"""Shared CI event -> commit-range resolution (PR/push) for gate scripts.

Defines the trusted comparison base and the per-commit range for the workflow's
supported events, failing closed on missing/zero/ambiguous history (never a
silent skip or working-tree fallback).

- pull_request: range = merge-base(origin/<base>, HEAD) .. HEAD
- push:         range = github.event.before .. github.event.after (all pushed
                commits); new-branch/tag (zero before) or unavailable commits ->
                explicit failure.
- other events: unsupported -> explicit failure (caller decides; not green).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

ZERO = "0" * 40


class EventError(RuntimeError):
    """Applicability/history could not be determined for the event."""


@dataclass
class Range:
    kind: str          # "pull_request" | "push"
    base_sha: str      # comparison base (merge-base for PR; before for push)
    head_sha: str
    commits: list[str]  # per-commit SHAs in the range (oldest first)


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise EventError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout.strip()


def resolve_range(root: Path, env: dict[str, str]) -> Range:
    event = (env.get("GITHUB_EVENT_NAME") or "").strip()

    if event == "pull_request":
        base_ref = (env.get("GITHUB_BASE_REF") or "").strip()
        if not base_ref:
            raise EventError("pull_request event without GITHUB_BASE_REF")
        try:
            mb = _git(root, "merge-base", f"origin/{base_ref}", "HEAD")
        except EventError as exc:
            raise EventError(f"cannot compute merge-base with origin/{base_ref}: {exc}") from exc
        head = _git(root, "rev-parse", "HEAD")
        commits = _commit_list(root, f"{mb}..HEAD")
        return Range("pull_request", mb, head, commits)

    if event == "push":
        before = (env.get("GITHUB_BEFORE") or "").strip()
        after = (env.get("GITHUB_AFTER") or "").strip()
        if not before or before == ZERO or not after or after == ZERO:
            raise EventError(
                f"push has no usable before/after (before={before!r} after={after!r}); "
                "new-branch/tag push has no trusted comparison base"
            )
        # Both commits must exist locally.
        for rev in (before, after):
            try:
                _git(root, "cat-file", "-e", f"{rev}^{{commit}}")
            except EventError as exc:
                raise EventError(f"push commit {rev} not available in history") from exc
        commits = _commit_list(root, f"{before}..{after}")
        return Range("push", before, after, commits)

    raise EventError(f"unsupported/unknown event {event!r} for gate applicability")


def _commit_list(root: Path, rev_range: str) -> list[str]:
    out = _git(root, "rev-list", "--reverse", rev_range)
    return [ln for ln in out.splitlines() if ln.strip()]
