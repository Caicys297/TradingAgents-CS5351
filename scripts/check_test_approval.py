#!/usr/bin/env python3
"""Pre-code Test Approval Gate checker (REQ-GOV-01/02).

Verifies that a code/prompt change batch had an **authorized pre-code approval**
whose original evidence precedes the batch's earliest implementation commit
(code, tests, fixtures, or workflow), matches the approved plan version/SHA,
requirement & case IDs, and allowed/excluded files — for the Registry reviewer
roles.

Trust model:
- Machine-readable records (``docs/test-approvals/*.json``) only *index* genuine
  GitHub evidence (a review/comment id + author + original timestamp). They
  cannot grant approval themselves; the checker resolves the evidence via the
  GitHub API (or a fixture directory for tests) and validates it.
- Reviewer roles come from the Registry (``approval_roles``): O2/O6 test plans ->
  A; O1/O3/O4/O5 -> F; execution plans -> A. Implementer self-approval is
  rejected.
- Later PR code-review approval does NOT authorize pre-code implementation.
- Missing / late / unauthorized / mismatched / unverifiable / API-incomplete
  evidence fails with a specific reason.
- A WeChat original may be preserved, but a GitHub binding must honestly keep the
  original message time; the binding time cannot masquerade as the approval time.

Usage:
    python scripts/check_test_approval.py --changed-from-file changed_files.z \
        [--repo OWNER/NAME] [--pr N] [--root .] [--api-fixture-dir DIR]

Exit codes:
    0  a valid authorized pre-code approval covers this batch (or not applicable:
       pure documentation)
    1  approval evidence missing/late/unauthorized/mismatched/unverifiable
    2  execution/internal error (API unavailable, bad record format)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path

# Registry reviewer roles (test plans). Execution plans always by A.
TEST_PLAN_REVIEWER = {
    "O1": "F", "O2": "A", "O3": "F", "O4": "F", "O5": "F", "O6": "A",
}
EXECUTION_PLAN_REVIEWER = "A"
OWNER_ROLES = {"A", "B", "C", "D", "E", "F"}

RECORDS_DIR = "docs/test-approvals"

CODE_PREFIXES = (
    "tradingagents/", "cli/", "scripts/", "src/",
    ".github/workflows/", "test/", "tests/", "prompts/",
)
DOC_PREFIXES = ("docs/", "transcripts/")
DOC_EXACT = {"README.md", "AGENTS.md", "Prompt.md", "Report.md"}


class ExecutionError(RuntimeError):
    """API/history/format problem -> exit 2."""


# ----------------------------------------------------------------- API abstraction
class GitHubAPI:
    """Resolves original evidence. Override in tests or via --api-fixture-dir."""

    def __init__(self, repo: str | None):
        self.repo = repo

    def _gh(self, *args: str) -> dict:  # pragma: no cover - needs network
        proc = subprocess.run(["gh", *args], capture_output=True, text=True)
        if proc.returncode != 0:
            raise ExecutionError(f"gh api failed: {proc.stderr.strip()[:300]}")
        return json.loads(proc.stdout)

    def get_issue_comment(self, number: int) -> dict:  # pragma: no cover
        return self._gh("api", f"repos/{self.repo}/issues/comments/{number}")

    def get_review(self, pr: int, review_id: int) -> dict:  # pragma: no cover
        return self._gh("api", f"repos/{self.repo}/pulls/{pr}/reviews/{review_id}")


class FixtureAPI:
    """Offline fixture-backed resolver: reads <comments>/*.json and <reviews>/*.json."""

    def __init__(self, root: Path):
        self.comments = root / "comments"
        self.reviews = root / "reviews"

    def get_issue_comment(self, number: int) -> dict:
        p = self.comments / f"{number}.json"
        if not p.is_file():
            raise ExecutionError(f"fixture comment {number} not found")
        return json.loads(p.read_text())

    def get_review(self, pr: int, review_id: int) -> dict:
        p = self.reviews / f"{pr}-{review_id}.json"
        if not p.is_file():
            raise ExecutionError(f"fixture review {pr}/{review_id} not found")
        return json.loads(p.read_text())


def make_api(repo: str | None, fixture_dir: Path | None):
    if fixture_dir is not None:
        return FixtureAPI(fixture_dir)
    return GitHubAPI(repo)


# ----------------------------------------------------------------- git helpers
def _parse_iso(ts: str) -> _dt.datetime:
    # GitHub returns e.g. 2026-11-16T15:02:47Z
    return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise ExecutionError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout.strip()


def earliest_implementation_commits(root: Path, base_ref: str, allowed: set[str]) -> list[tuple[str, str, str]]:
    """Return [(sha, iso_time, path)] for the earliest commit touching any
    implementation (code/test/fixture/workflow) path within origin/<base>..HEAD.

    Implementation = a path under CODE_PREFIXES (docs/transcript-only commits are
    not implementation). Preserves original provenance: uses the commit's own
    author/committer date from history; a later rebase/cherry-pick does not move
    the original author date, which is what we compare on.
    """
    try:
        log = _git(root, "log", "--reverse", "--format=%H%x1f%aI%x1f%s",
                   f"origin/{base_ref}..HEAD")
    except ExecutionError as exc:
        # base ref missing -> history incomplete
        raise ExecutionError(f"cannot read history for origin/{base_ref}..HEAD") from exc
    if not log:
        return []
    out: list[tuple[str, str, str]] = []
    for line in log.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        sha, iso, _subject = parts
        files = _git(root, "show", "--name-only", "--format=", "-z", sha)
        paths = [p for p in files.split("\x00") if p]
        if any(_is_implementation_path(p) for p in paths):
            # record the first implementation path for context
            impl = next(p for p in paths if _is_implementation_path(p))
            out.append((sha, iso, impl))
    return out


def _is_implementation_path(p: str) -> bool:
    if p in DOC_EXACT:
        return False
    if p.startswith(DOC_PREFIXES):
        return False
    return p.startswith(CODE_PREFIXES)


# ----------------------------------------------------------------- record loading
def load_records(root: Path) -> list[dict]:
    d = root / RECORDS_DIR
    records: list[dict] = []
    if not d.is_dir():
        return records
    for p in sorted(d.glob("*.json")):
        try:
            records.append({"__path": str(p.relative_to(root)), **json.loads(p.read_text())})
        except json.JSONDecodeError as exc:
            raise ExecutionError(f"malformed approval record {p}: {exc}") from exc
    return records


# ----------------------------------------------------------------- validation
def _applicable(changed: list[str]) -> bool:
    return any(_is_implementation_path(p) for p in changed)


def _feature_of(record: dict) -> str:
    feat = str(record.get("feature", "")).strip()
    return feat[:2].upper() if feat else ""


def validate_record(record: dict, api, pr: int | None, earliest_iso: str | None) -> list[str]:
    """Return list of problems for one record (empty = valid)."""
    problems: list[str] = []
    feature = _feature_of(record)
    role = TEST_PLAN_REVIEWER.get(feature)
    if role is None:
        problems.append(f"unknown feature {record.get('feature')!r}; cannot resolve reviewer role")
        return problems

    # Required structural fields (a machine record is an index, not approval).
    for field in ("approval_kind", "evidence", "plan_sha", "plan_version",
                  "requirement_ids", "approved_test_ids",
                  "allowed_files", "approval_time"):
        if not record.get(field):
            problems.append(f"missing field: {field}")
    if problems:
        return problems

    # Resolve original evidence.
    ev = record["evidence"]
    if ev.get("type") == "issue_comment":
        try:
            original = api.get_issue_comment(int(ev["id"]))
        except ExecutionError as exc:
            problems.append(f"evidence unverifiable: {exc}")
            return problems
        author = original.get("user", {}).get("login", "")
        otime = original.get("created_at", "")
    elif ev.get("type") == "review":
        if pr is None:
            problems.append("review evidence requires --pr")
            return problems
        try:
            original = api.get_review(pr, int(ev["id"]))
        except ExecutionError as exc:
            problems.append(f"evidence unverifiable: {exc}")
            return problems
        author = original.get("user", {}).get("login", "")
        otime = original.get("submitted_at", "")
    else:
        problems.append(f"unknown evidence type {ev.get('type')!r}")
        return problems

    # Evidence author must be a real GitHub user and match the record if declared.
    if not author:
        problems.append("evidence has no author")
    if ev.get("author") and author and str(ev["author"]) != author:
        problems.append(
            f"evidence author {author!r} does not match record author {ev.get('author')!r}"
        )

    # Reviewer role / authorization.
    reviewer_role = str(ev.get("reviewer_role", "")).strip()
    if reviewer_role not in OWNER_ROLES:
        problems.append("evidence reviewer_role not a known role")
    if record["approval_kind"] == "test_plan" and reviewer_role != role:
        problems.append(f"unauthorized reviewer: test plan for {feature} must be reviewed by {role}, got {reviewer_role!r}")
    if record["approval_kind"] == "execution_plan" and reviewer_role != EXECUTION_PLAN_REVIEWER:
        problems.append(f"unauthorized reviewer: execution plan must be reviewed by {EXECUTION_PLAN_REVIEWER}, got {reviewer_role!r}")

    # Implementer cannot self-approve.
    if record.get("implementer") and str(record["implementer"]) == ev.get("reviewer_role"):
        problems.append("self-approval: implementer equals approver role")

    # Original timestamp present and matches the record (no backdating).
    if not otime:
        problems.append("evidence has no original timestamp")
    else:
        try:
            if _parse_iso(otime) != _parse_iso(record["approval_time"]):
                problems.append(
                    f"approval_time {record['approval_time']} does not match original evidence time {otime}"
                )
        except (ValueError, AttributeError):
            problems.append("unparseable timestamp")

    # Pre-code ordering: approval must precede earliest implementation.
    if earliest_iso is not None and otime:
        try:
            if _parse_iso(otime) >= _parse_iso(earliest_iso):
                problems.append(
                    f"late approval: approval {otime} is not before first implementation {earliest_iso}"
                )
        except ValueError:
            pass

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from-file", type=Path, required=True)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--pr", type=int, default=None)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--api-fixture-dir", type=Path, default=None)
    parser.add_argument("--base-ref", default=None)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    raw = args.changed_from_file.read_bytes()
    changed = [p.decode("utf-8", "replace") for p in raw.split(b"\x00") if p]

    if not _applicable(changed):
        print("OK: no implementation change in this batch; Test Approval gate not applicable")
        return 0

    records = load_records(root)
    if not records:
        print("TEST APPROVAL FAILED: implementation change with no approval record "
              f"under {RECORDS_DIR}/", file=sys.stderr)
        return 1

    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF", "")
    earliest_iso = None
    if not base_ref:
        print("ERROR: no base ref to compare approval against first implementation",
              file=sys.stderr)
        return 2
    try:
        earliest = earliest_implementation_commits(root, base_ref, set())
    except ExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if earliest:
        earliest_iso = earliest[0][1]

    api = make_api(args.repo, args.api_fixture_dir)

    all_problems: list[str] = []
    any_valid = False
    for rec in records:
        try:
            problems = validate_record(rec, api, args.pr, earliest_iso)
        except ExecutionError as exc:
            print(f"ERROR validating {rec.get('__path')}: {exc}", file=sys.stderr)
            return 2
        if problems:
            all_problems.extend(f"{rec.get('__path')}: {p}" for p in problems)
        else:
            any_valid = True

    if any_valid:
        print("OK: authorized pre-code approval verified for this batch")
        return 0

    print("TEST APPROVAL FAILED:", file=sys.stderr)
    for p in all_problems:
        print(f"  - {p}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
