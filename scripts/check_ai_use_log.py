"""Structural AI-use evidence check for a PR (hardened per review).

Goals:
- Inspect only the PR's **added lines** vs the merge base; if the merge base /
  git diff cannot be resolved, return a distinct EXECUTION FAILURE (exit 3),
  never fall back to validating the whole file.
- Require a genuine new entry associating task, usage scope, and an actual
  implementation commit that exists in the repo, with an explicitly identified
  session/export reference. A baseline main SHA alone is not this PR's
  implementation association.
- Reject PR URLs even when their query/fragment contains "session"/"export".
- Reject machine-absolute-path evidence; a *summary* file is not a raw export and
  does not by itself satisfy the genuine-export requirement (see notes).
- Truthfulness/authenticity is a human responsibility; this only checks structure.

Usage:
    python scripts/check_ai_use_log.py --changed-from-file changed.z [--root .]
    python scripts/check_ai_use_log.py --changed-file A --changed-file B [--root .]

Exit codes:
    0  valid newly-added AI-use evidence (or gate not applicable)
    1  evidence invalid (missing/weak entry)
    2  usage / internal error
    3  execution failure: could not resolve merge base / git diff
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

LOG_NAME_RE = re.compile(r"ai[-_ ]?use", re.IGNORECASE)
REQUIRED_FIELD_LABELS = ("task", "scope", "commit")

# A PR URL — regardless of trailing query/fragment.
PR_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+(?:[?#][^\s]*)?", re.IGNORECASE)
# A genuine session/export https reference: the URL *path/authority* must denote a
# session/export; query/fragment alone does NOT count (see validation logic).
HTTPS_URL_RE = re.compile(r"https://[^\s)>\]]+", re.IGNORECASE)
TRANSCRIPT_REF_RE = re.compile(r"transcripts/[^\s)`'\"]+\.(?:md|json|jsonl|txt)")
COMMIT_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
ABS_PATH_RE = re.compile(r"(?:^|[\s(\"'`])(?:/Users/|/home/|[A-Za-z]:\\)")

CODE_PREFIXES = (
    "tradingagents/", "cli/", "scripts/", "prompts/",
    ".github/workflows/", "test/", "tests/",
)


class DiffError(RuntimeError):
    """Raised when the merge base / git diff cannot be resolved."""


def _is_ai_use_log(path: str) -> bool:
    p = Path(path)
    return "transcripts" in p.parts and LOG_NAME_RE.search(p.name) is not None


def _applicable(changed: list[str]) -> bool:
    return any(f.startswith(CODE_PREFIXES) and not _is_ai_use_log(f) for f in changed)


def added_lines(path: Path, base_ref: str) -> list[str]:
    """Added ('+') lines for ``path`` vs the merge base with origin/<base>.

    Raises DiffError if git/diff/base cannot be resolved — the caller turns that
    into a distinct execution failure (no whole-file fallback).
    """
    if not base_ref:
        raise DiffError("no base ref available to compute the PR diff")
    try:
        proc = subprocess.run(
            ["git", "diff", "--unified=0", f"origin/{base_ref}...HEAD", "--", path.as_posix()],
            capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise DiffError("git is not available to compute the PR diff") from exc
    if proc.returncode != 0:
        raise DiffError(
            f"git diff failed for origin/{base_ref}...HEAD (exit {proc.returncode}): "
            f"{proc.stderr.strip()[:300]}"
        )
    out: list[str] = []
    for ln in proc.stdout.splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            out.append(ln[1:])
    return out


def _is_session_url(url: str) -> bool:
    """True only if the URL's path/authority (not just query/fragment) is a session/export."""
    if PR_URL_RE.match(url):
        return False  # a PR URL is never session evidence, even with ?session=...
    # Strip query and fragment; only the pre-'?'/'#' part counts.
    core = re.split(r"[?#]", url, maxsplit=1)[0]
    return re.search(r"(?:session|sessions|export|exports|transcript|transcripts)", core, re.IGNORECASE) is not None


def _commit_exists(sha: str, root: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0


def _commit_in_range(sha: str, base_ref: str, root: Path) -> bool:
    """Whether ``sha`` is reachable in the PR range origin/<base>..HEAD."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0


def _is_genuine_export(path: Path) -> bool:
    """A resolvable transcript reference counts as export evidence only if it is a
    real machine export (JSON/JSONL) or does not self-identify as an authored
    summary. A hand-written 'NOT a raw export' summary is rejected as evidence."""
    if not path.is_file():
        return False
    if path.suffix.lower() in (".json", ".jsonl"):
        return True
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:2000].lower()
    except OSError:
        return False
    is_summary = ("not a raw" in head) or ("authored" in head and "summary" in head)
    return not is_summary


def _validate_entry(text_lines: list[str], root: Path, base_ref: str, check_commits: bool = True) -> list[str]:
    joined = "\n".join(text_lines)
    if not joined.strip():
        return ["no added content (whitespace-only or unchanged entry) — not valid evidence"]

    lowered = joined.lower()
    missing = [lbl for lbl in REQUIRED_FIELD_LABELS if lbl not in lowered]
    if missing:
        return [f"missing field label(s): {', '.join(missing)}"]

    problems: list[str] = []

    # Genuine session/export reference: a non-PR https URL whose path denotes a
    # session/export, or a resolvable transcripts/ export file.
    session_urls = [u for u in HTTPS_URL_RE.findall(joined) if _is_session_url(u)]
    transcript_refs = list(TRANSCRIPT_REF_RE.findall(joined))
    resolvable_exports = [r for r in transcript_refs if _is_genuine_export(root / r)]

    if not session_urls and not resolvable_exports:
        if PR_URL_RE.search(joined):
            problems.append(
                "PR URL is not session evidence (query/fragment containing 'session' does "
                "not count; need a genuine session/export URL path or a resolvable export file)"
            )
        else:
            problems.append(
                "no genuine session/export reference (need an https session/export URL or a "
                "resolvable transcripts/ export file)"
            )

    if ABS_PATH_RE.search(joined):
        problems.append("evidence references a machine-specific absolute path (reviewers cannot access it)")

    # Implementation-commit association must be a REAL commit in this PR's range.
    if base_ref and check_commits:
        shas = COMMIT_SHA_RE.findall(joined)
        real = [s for s in shas if _commit_exists(s, root)]
        in_range = [s for s in real if _commit_in_range(s, base_ref, root)]
        if not shas:
            problems.append("no implementation commit SHA associated with the entry")
        elif not real:
            problems.append(
                "commit SHA(s) in the entry do not exist in the repository "
                "(a baseline main SHA alone is not this PR's implementation association)"
            )
        elif not in_range:
            problems.append(
                "commit SHA(s) exist but are not part of this PR's implementation range "
                "(origin/base..HEAD)"
            )

    return problems


def _changed_from_file(zpath: Path) -> list[str]:
    raw = zpath.read_bytes()
    return [p.decode("utf-8", errors="replace") for p in raw.split(b"\x00") if p]


def check(changed: list[str], root: Path, base_ref: str) -> list[str]:
    if not _applicable(changed):
        return []
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
        added = added_lines(path, base_ref)  # raises DiffError (no fallback)
        problems = _validate_entry(added, root, base_ref)
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
        if args.changed_from_file:
            print("OK: no changed files reported; AI-use gate not applicable")
            return 0
        print("ERROR: no --changed-file / --changed-from-file provided", file=sys.stderr)
        return 2

    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF", "")

    # If the gate applies to a code/prompt change, a resolvable base is mandatory.
    if _applicable(changed) and not base_ref:
        print(
            "ERROR: code/prompt change but no base ref to compute the PR diff "
            "(GITHUB_BASE_REF / --base-ref); refusing to validate the whole file.",
            file=sys.stderr,
        )
        return 3

    try:
        errors = check(changed, args.root, base_ref)
    except DiffError as exc:
        print(f"ERROR: cannot obtain PR diff: {exc}", file=sys.stderr)
        return 3
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
