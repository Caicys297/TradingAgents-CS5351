#!/usr/bin/env python3
"""Per-commit Ruff enforcement (REQ-GOV-07).

Fails if ANY commit in the event's trusted range does not pass ``ruff check .``,
even when the final checked-out tree is clean. Resolution is delegated to the
shared ``ci_event.resolve_range`` helper (PR: merge-base .. real PR head; push:
before .. after), which itself fails closed on missing/zero/ambiguous history.

Each historical revision is materialised in an isolated ``git worktree`` so the
working tree is never disturbed; the worktree is always removed in ``finally``.

Usage:
    python scripts/lint_commits.py [--root .] [--ruff ruff]

Environment (supplied by the workflow, mirroring the other gate jobs):
    GITHUB_EVENT_NAME, GITHUB_BASE_REF, GITHUB_BEFORE, GITHUB_AFTER,
    CI_HEAD_SHA  (optional explicit real PR head; not the synthetic merge commit)

Exit codes: 0 all commits clean; 1 a commit (or range/tool failure) is not clean;
2 execution/usage error.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_event  # noqa: E402


class LintError(RuntimeError):
    """Per-commit lint could not be established (range/tool/worktree failure)."""


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def _lint_tree(root: Path, sha: str, ruff: str) -> str | None:
    """Return Ruff output if the revision fails, else None. Raises LintError on
    tool/worktree failures (never silently clean)."""
    wt = Path(tempfile.mkdtemp(prefix="lint-commit-"))
    try:
        add = _run(["git", "-C", str(root), "worktree", "add", "--detach", str(wt), sha], root)
        if add.returncode != 0:
            raise LintError(f"git worktree add failed for {sha[:12]}: {add.stderr.strip()[:300]}")
        cmd = [*shlex.split(ruff), "check", "."]
        res = _run(cmd, wt)
        if res.returncode == 0:
            return None
        if res.returncode == 1:
            return (res.stdout or "") + (res.stderr or "")
        # Any non-0/1 exit means ruff itself could not run (tool error).
        raise LintError(f"ruff exited {res.returncode} at {sha[:12]}: {res.stderr.strip()[:300]}")
    finally:
        _run(["git", "-C", str(root), "worktree", "remove", "--force", str(wt)], root)
        shutil.rmtree(wt, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Per-commit Ruff enforcement")
    ap.add_argument("--root", default=".")
    ap.add_argument("--ruff", default=os.environ.get("RUFF_BIN", "ruff"))
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        rng = ci_event.resolve_range(root, dict(os.environ))
    except ci_event.EventError as exc:
        print(f"LINT FAILED: cannot resolve commit range: {exc}", file=sys.stderr)
        return 1

    failures: list[tuple[str, str]] = []
    for sha in rng.commits:
        try:
            out = _lint_tree(root, sha, args.ruff)
        except LintError as exc:
            print(f"LINT FAILED: {exc}", file=sys.stderr)
            return 1
        if out is not None:
            failures.append((sha, out))

    if failures:
        print(f"LINT FAILED: {len(failures)} of {len(rng.commits)} commit(s) are not clean", file=sys.stderr)
        for sha, out in failures:
            print(f"\nFAILED commit {sha[:12]}:", file=sys.stderr)
            print(out.rstrip(), file=sys.stderr)
        return 1

    print(f"OK: all {len(rng.commits)} commit(s) in the {rng.kind} range pass ruff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
