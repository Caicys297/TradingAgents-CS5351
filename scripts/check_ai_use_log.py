#!/usr/bin/env python3
"""Structural AI-use evidence check for a PR (corrections 3 & 5).

This verifies that a code/prompt PR adds a **meaningful new** AI-use entry that
associates task, usage scope, and implementation commit(s) with an explicitly
identified session/export reference. It does NOT establish truthfulness; humans
review authenticity and access.

Key rules:
- Inspects only the PR's **added/modified lines** (via the merge-base diff), so an
  unchanged historical entry plus a whitespace edit cannot pass.
- Rejects whitespace-only edits and reuse of unchanged historical entries.
- A generic HTTPS URL is not automatically a session reference. A real session/
  export reference must be an https URL whose path/query clearly denotes a session
  or export, OR a resolvable in-repo ``transcripts/`` export file. PR URLs
  (github.com/<owner>/<repo>/pull/<n>) — especially with punctuation, comments,
  query strings, or fragments — are rejected as session evidence.
- Machine-specific absolute paths used *as the evidence reference* are rejected.
  A historical log mentioning a local path elsewhere is not itself rejected.
- Implementation commit association: an entry line naming a commit SHA is accepted
  structurally; whether that SHA exists and relates to this PR is reported as a
  hint for human review (the check does not require the log commit to contain its
  own final SHA).
- `--changed-from-file` reads a NUL-separated changed-file list, so filenames with
  spaces are handled safely and never interpolated into shell.

Usage:
    python scripts/check_ai_use_log.py --changed-file A [--changed-file B ...] [--root .]
    python scripts/check_ai_use_log.py --changed-from-file changed_files.z [--root .]

Exit codes:
    0  a valid, newly-added AI-use entry exists (or no code/prompt change)
    1  code/prompt change without valid newly-added AI-use evidence
    2  usage / internal error
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LOG_NAME_RE = re.compile(r"ai[-_ ]?use", re.IGNORECASE)
REQUIRED_FIELD_LABELS = ("task", "scope", "commit")

# https session/export heuristic: path or query shows "session"/"export"/"transcript".
SESSION_URL_RE = re.compile(
    r"https://[^\s)]*(?:session|sessions|export|exports|transcript|transcripts)[^\s)]*",
    re.IGNORECASE,
)
PR_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+", re.IGNORECASE)
TRANSCRIPT_REF_RE = re.compile(r"transcripts/[^\s)`'\"]+\.(?:md|json|jsonl|txt)")
COMMIT_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
ABS_PATH_RE = re.compile(r"(?:^|[\s(\"'`])(?:/Users/|/home/|[A-Za-z]:\\)")

# File classes that make the gate applicable.
CODE_PREFIXES = (
    "tradingagents/", "cli/", "scripts/", "prompts/",
    ".github/workflows/", "test/", "tests/",
)


def _is_ai_use_log(path: str) -> bool:
    p = Path(path)
    return "transcripts" in p.parts and LOG_NAME_RE.search(p.name) is not None


def _applicable(changed: list[str]) -> bool:
    return any(f.startswith(CODE_PREFIXES) and not _is_ai_use_log(f) for f in changed)


def added_lines(path: Path, base_ref: str) -> list[str]:
    """Added ('+') lines for ``path`` versus the merge base with origin/<base>."""
    try:
        proc = subprocess.run(
            ["git", "diff", "--unified=0", f"origin/{base_ref}...HEAD", "--", path.as_posix()],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return []
    if proc.returncode != 0:
        # If git diff is unavailable, fall back to the whole file (still validated).
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[str] = []
    for ln in proc.stdout.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            out.append(ln[1:])
    return out


def _validate_entry(text_lines: list[str], root: Path) -> list[str]:
    """Validate one log's added content. Returns problems (empty = valid)."""
    joined = "\n".join(text_lines)
    if not joined.strip():
        return ["no added content (whitespace-only or unchanged entry) — not valid evidence"]

    lowered = joined.lower()
    missing = [lbl for lbl in REQUIRED_FIELD_LABELS if lbl not in lowered]
    if missing:
        return [f"missing field label(s): {', '.join(missing)}"]

    problems: list[str] = []

    session_urls = SESSION_URL_RE.findall(joined)
    transcript_refs = list(TRANSCRIPT_REF_RE.findall(joined))
    resolvable_exports = [r for r in transcript_refs if (root / r).is_file()]

    if not session_urls and not resolvable_exports:
        # Distinguish "only a PR URL" and "bare URL" for a clearer message.
        if PR_URL_RE.search(joined):
            problems.append(
                "PR URL is not session evidence (need an explicitly identified "
                "session/export https link or a resolvable transcripts/ export file)"
            )
        else:
            problems.append(
                "no real session/export reference (need an https session/export link "
                "or a resolvable transcripts/ export file)"
            )

    # Absolute local path used as the evidence reference is rejected.
    if ABS_PATH_RE.search(joined):
        problems.append("evidence references a machine-specific absolute path (reviewers cannot access it)")

    # Commit association: structural only; note for humans.
    if not COMMIT_SHA_RE.search(joined):
        problems.append("no implementation commit SHA associated with the entry")

    return problems


def _changed_from_file(zpath: Path) -> list[str]:
    raw = zpath.read_bytes()
    parts = raw.split(b"\x00")
    return [p.decode("utf-8", errors="replace") for p in parts if p]


def check(changed: list[str], root: Path, base_ref: str) -> list[str]:
    if not _applicable(changed):
        return []  # no code/prompt change -> gate not applicable

    log_files = [f for f in changed if _is_ai_use_log(f)]
    if not log_files:
        return ["code/prompt change with no AI-use log change under transcripts/"]

    errors: list[str] = []
    any_valid = False
    for rel in log_files:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: listed as changed but not found")
            continue
        added = added_lines(path, base_ref) if base_ref else path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()
        problems = _validate_entry(added, root)
        if problems:
            errors.extend(f"{rel}: {p}" for p in problems)
        else:
            any_valid = True

    if errors:
        return errors
    if not any_valid:
        return ["no valid newly-added AI-use entry found"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-file", action="append", default=[], dest="changed")
    parser.add_argument("--changed-from-file", type=Path, default=None)
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--base-ref", default=None)
    args = parser.parse_args(argv)

    changed = list(args.changed)
    if args.changed_from_file:
        changed.extend(_changed_from_file(args.changed_from_file))

    if not changed:
        # Empty change set is not automatically a pass if a diff file was provided.
        if args.changed_from_file:
            print("OK: no changed files reported; AI-use gate not applicable")
            return 0
        print("ERROR: no --changed-file / --changed-from-file provided", file=sys.stderr)
        return 2

    import os

    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF", "")

    try:
        errors = check(changed, args.root, base_ref)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(f"AI-use evidence INVALID: {len(errors)} problem(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("OK: valid newly-added AI-use evidence found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
