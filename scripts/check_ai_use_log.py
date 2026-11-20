#!/usr/bin/env python3
"""Structural check for CS5351 AI-use evidence in ``transcripts/``.

This is a *structural and reference-association* check only. It verifies that a
PR adds a meaningful, PR-specific AI-use record that references a real session /
export and associates it with task, usage scope, and implementation commits. It
does **not** and cannot establish that a record is truthful; humans review
authenticity and access.

Design notes (per A/C approval):
- Existing log locations and formats are preserved; nothing is migrated.
- The accepted evidence forms are a reviewer-accessible real session link
  (https URL) OR an exported transcript file that resolves inside the repo
  (``transcripts/``). A bare PR URL is not, by itself, session evidence.
- Machine-specific absolute paths (``/Users/``, ``C:\\``, ``/home/``) are not
  accepted as references because reviewers cannot access them.
- The check does not require a log commit to contain its own final SHA, and it
  tolerates implementation commits landing after the log entry.
- No remote fetch is performed; link reachability is left to human review. The
  checker flags references that are structurally invalid or point inside the repo
  but do not resolve.

Usage:
    python scripts/check_ai_use_log.py --changed-file <path> [--changed-file ...]
                                       [--root .]

Exit codes:
    0  at least one valid, PR-specific AI-use entry is present in the change set
    1  code/prompt change without a valid AI-use entry (or malformed entries)
    2  usage / internal error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A log file is any Markdown under transcripts/ whose name mentions "ai-use".
LOG_NAME_RE = re.compile(r"ai[-_ ]?use", re.IGNORECASE)
# Required association markers (case-insensitive) in a log's content, anywhere.
REQUIRED_MARKERS = ("task", "scope", "commit")
# A real session/export reference: an https URL, or a repo-relative transcript path.
HTTPS_URL_RE = re.compile(r"https://\S+")
TRANSCRIPT_REF_RE = re.compile(r"transcripts/[A-Za-z0-9._/\-]+\.(?:md|json|jsonl|txt)")
ABS_PATH_RE = re.compile(r"(?:^|[\s(\"'`])(?:/Users/|/home/|[A-Za-z]:\\)")


def is_ai_use_log(path: Path) -> bool:
    parts = path.parts
    return "transcripts" in parts and LOG_NAME_RE.search(path.name) is not None


def references(path_str: str, root: Path) -> tuple[bool, list[str]]:
    """Return (has_valid_ref, problems) for one log file's content."""
    text = path_str
    problems: list[str] = []

    if ABS_PATH_RE.search(text):
        problems.append("contains a machine-specific absolute path (reviewers cannot access it)")

    https = HTTPS_URL_RE.findall(text)
    transcript_refs = TRANSCRIPT_REF_RE.findall(text)

    # A https URL that is *only* a github PR URL and nothing else is not enough.
    session_urls = [u for u in https if not re.search(r"github\.com/[^/]+/[^/]+/pull/\d+/?$", u)]

    resolvable_export = [
        ref for ref in transcript_refs if (root / ref).is_file()
    ]

    has_ref = bool(session_urls) or bool(resolvable_export)
    if not has_ref:
        problems.append(
            "no real session/export reference (need an https session link or a resolvable transcripts/ export)"
        )
    return has_ref, problems


def check(changed_files: list[str], root: Path) -> list[str]:
    errors: list[str] = []
    log_changes = [f for f in changed_files if is_ai_use_log(Path(f))]

    if not log_changes:
        return [
            "code/prompt change with no AI-use log change under transcripts/ "
            "(add a PR-specific entry; existing logs are not migrated)"
        ]

    any_valid = False
    for rel in log_changes:
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: listed as changed but not found")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [m for m in REQUIRED_MARKERS if m not in text.lower()]
        if missing:
            errors.append(f"{rel}: missing association marker(s): {', '.join(missing)}")
            continue
        has_ref, problems = references(text, root)
        if problems:
            errors.extend(f"{rel}: {p}" for p in problems)
            continue
        if has_ref:
            any_valid = True

    if errors:
        return errors
    if not any_valid:
        return ["no valid AI-use entry found in the change set"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check AI-use evidence in the change set.")
    parser.add_argument("--changed-file", action="append", default=[], dest="changed")
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args(argv)

    if not args.changed:
        print("ERROR: no --changed-file provided", file=sys.stderr)
        return 2

    try:
        errors = check(args.changed, args.root)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(f"AI-use evidence INVALID: {len(errors)} problem(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("OK: valid PR-specific AI-use evidence found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
