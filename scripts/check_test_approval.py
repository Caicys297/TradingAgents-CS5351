#!/usr/bin/env python3
"""Pre-code Test Approval Gate checker (REQ-GOV-01/02) — hardened.

Enforces the A-confirmed rules:
- Trusted reviewer identity: GitHub logins are bound to roles by a reviewed
  source (``docs/test-approvals/reviewers.yaml``); the record's declared role is
  NOT trusted. The original evidence author must map to the authorized role.
- Implementers are identified from actual batch evidence (evidence author /
  recorded implementers) — self-approval is rejected.
- Batch binding: a historical record does not authorize an unrelated PR. The
  record declares a ``batch_id``; it must match the requested batch, and the
  record's allowed files must cover **every** applicable implementation file in
  the batch.
- Both a test-plan approval AND an execution-plan approval are required (one
  original record may approve both), unless an evidence-backed delegation covers
  one.
- Approval meaning: the original evidence body must actually reference the plan
  SHA/version (or an authorized human binding record explicitly references the
  original evidence + approved fields). Non-empty JSON fields are insufficient.
  A later PR code review (even APPROVED) is not pre-code approval.
- Time/history: compares approval time to the earliest implementation commit
  touching applicable files (author date), not merely the first topological log
  entry; rejects unavailable/ambiguous history; fails if no implementation commit
  is found despite applicable changes.

Trust/bootstrap honesty (workflow): the CI job runs this checker from the PR
checkout with a read-only GitHub token. Minimal privilege is kept (no write
creds, no pull_request_target). This DOES mean a PR could modify the checker in
its own tree; the trust anchor is the protected ``main`` reviewers mapping + the
original GitHub evidence. The job's description must not claim the PR cannot
change the checker.

Usage:
    python scripts/check_test_approval.py --changed-from-file F --batch ID \
        [--repo R] [--pr N] [--root .] [--api-fixture-dir DIR] [--base-ref B]

Exit codes: 0 valid; 1 evidence invalid; 2 execution/API/format error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

TEST_PLAN_REVIEWER = {"O1": "F", "O2": "A", "O3": "F", "O4": "F", "O5": "F", "O6": "A"}
EXECUTION_PLAN_REVIEWER = "A"
OWNER_ROLES = {"A", "B", "C", "D", "E", "F"}
RECORDS_DIR = "docs/test-approvals"
REVIEWERS_FILE = "docs/test-approvals/reviewers.yaml"

CODE_PREFIXES = ("tradingagents/", "cli/", "scripts/", "src/",
                 ".github/workflows/", "test/", "tests/", "prompts/")
DOC_PREFIXES = ("docs/", "transcripts/")
DOC_EXACT = {"README.md", "AGENTS.md", "Prompt.md", "Report.md"}


class ExecutionError(RuntimeError):
    pass


# --------------------------------------------------------------- trusted identity
def load_reviewers(root: Path) -> dict[str, str]:
    """login -> role, from the reviewed mapping file. Missing/empty -> error."""
    p = root / REVIEWERS_FILE
    if not p.is_file():
        raise ExecutionError(f"trusted reviewers mapping not found: {REVIEWERS_FILE}")
    if yaml is None:
        raise ExecutionError("PyYAML required to read reviewers mapping")
    data = yaml.safe_load(p.read_text()) or {}
    logins = data.get("logins", {})
    if not isinstance(logins, dict) or not logins:
        raise ExecutionError("reviewers mapping has no logins")
    mapping: dict[str, str] = {}
    for login, role in logins.items():
        role = str(role).upper()
        if role not in OWNER_ROLES:
            raise ExecutionError(f"reviewers mapping has invalid role {role!r} for {login}")
        mapping[str(login)] = role
    return mapping


# --------------------------------------------------------------- API abstraction
class GitHubAPI:
    def __init__(self, repo: str | None):
        self.repo = repo

    def _gh(self, *args: str) -> dict:  # pragma: no cover - network
        proc = subprocess.run(["gh", *args], capture_output=True, text=True)
        if proc.returncode != 0:
            raise ExecutionError(f"gh api failed: {proc.stderr.strip()[:300]}")
        return json.loads(proc.stdout)

    def get_issue_comment(self, number: int) -> dict:  # pragma: no cover
        return self._gh("api", f"repos/{self.repo}/issues/comments/{number}")

    def get_review(self, pr: int, review_id: int) -> dict:  # pragma: no cover
        return self._gh("api", f"repos/{self.repo}/pulls/{pr}/reviews/{review_id}")


class FixtureAPI:
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


def make_api(repo, fixture_dir):
    return FixtureAPI(fixture_dir) if fixture_dir is not None else GitHubAPI(repo)


# --------------------------------------------------------------- git helpers
def _parse_iso(ts: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise ExecutionError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout.strip()


def _is_implementation(p: str) -> bool:
    if p in DOC_EXACT or p.startswith(DOC_PREFIXES):
        return False
    return p.startswith(CODE_PREFIXES)


def earliest_impl_for_files(root: Path, base_ref: str, applicable: set[str]) -> tuple[str, str] | None:
    """Earliest (author-iso, sha) among commits touching any applicable file.

    Uses ``git log --format=%H %aI -- <paths>`` so we get the earliest commit that
    touched the *batch's* files (not merely the first topological entry). Raises on
    unavailable history.
    """
    if not applicable:
        return None
    try:
        out = _git(root, "log", "--reverse", "--format=%H%x1f%aI", f"origin/{base_ref}..HEAD",
                   "--", *sorted(applicable))
    except ExecutionError as exc:
        raise ExecutionError(f"cannot read history for origin/{base_ref}..HEAD: {exc}") from exc
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines:
        return None
    sha, iso = lines[0].split("\x1f", 1)
    return iso, sha


# --------------------------------------------------------------- records
def load_records(root: Path) -> list[dict]:
    d = root / RECORDS_DIR
    out: list[dict] = []
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        try:
            out.append({"__path": str(p.relative_to(root)), **json.loads(p.read_text())})
        except json.JSONDecodeError as exc:
            raise ExecutionError(f"malformed approval record {p}: {exc}") from exc
    return out


def _applicable(changed: list[str]) -> set[str]:
    return {p for p in changed if _is_implementation(p)}


def _feature(record: dict) -> str:
    f = str(record.get("feature", "")).strip()
    return f[:2].upper() if f else ""


# --------------------------------------------------------------- validation
def _resolve_evidence(record: dict, api, pr: int | None) -> tuple[str, str, str]:
    """Return (author_login, original_iso, body) for the record's evidence."""
    ev = record.get("evidence") or {}
    etype = ev.get("type")
    if etype == "issue_comment":
        o = api.get_issue_comment(int(ev["id"]))
        return o.get("user", {}).get("login", ""), o.get("created_at", ""), o.get("body", "")
    if etype == "review":
        if pr is None:
            raise ExecutionError("review evidence requires --pr")
        o = api.get_review(pr, int(ev["id"]))
        # A review's state APPROVED alone is not pre-code approval; caller checks body.
        return o.get("user", {}).get("login", ""), o.get("submitted_at", ""), o.get("body", "")
    raise ExecutionError(f"unknown evidence type {etype!r}")


def _covers_all(allowed: list[str], applicable: set[str]) -> list[str]:
    """Return applicable files NOT covered by any allowed glob/prefix/exact."""
    missing = []
    for f in applicable:
        ok = False
        for a in allowed:
            if a.endswith("/") and f.startswith(a):
                ok = True
            elif "*" in a:
                import fnmatch
                if fnmatch.fnmatch(f, a):
                    ok = True
            elif f == a:
                ok = True
        if not ok:
            missing.append(f)
    return missing


def validate_batch(records, api, pr, batch_id, applicable, reviewers, earliest) -> list[str]:
    """Validate the whole batch: require BOTH kinds, batch/scope binding, meaning."""
    problems: list[str] = []

    # Collect valid-ish records for this batch, per kind.
    test_ok = None
    exec_ok = None
    for rec in records:
        rp = rec.get("__path", "<record>")
        if rec.get("batch_id") != batch_id:
            continue
        feature = _feature(rec)
        role_needed = TEST_PLAN_REVIEWER.get(feature)
        if role_needed is None:
            problems.append(f"{rp}: unknown feature {rec.get('feature')!r}")
            continue
        try:
            author, otime, body = _resolve_evidence(rec, api, pr)
        except ExecutionError as exc:
            problems.append(f"{rp}: evidence unverifiable: {exc}")
            continue
        role = reviewers.get(author)
        if role is None:
            problems.append(f"{rp}: evidence author {author!r} is not an authorized reviewer")
            continue
        if not otime:
            problems.append(f"{rp}: evidence has no original timestamp")
            continue

        kinds = rec.get("approval_kinds") or ([rec.get("approval_kind")] if rec.get("approval_kind") else [])
        kinds = [k for k in kinds if k]

        # Meaning: evidence body must reference plan sha AND version.
        plan_sha = str(rec.get("plan_sha", ""))
        plan_ver = str(rec.get("plan_version", ""))
        is_delegation = bool(rec.get("delegation"))
        if plan_sha and plan_sha[:7] not in body and plan_sha not in body:
            problems.append(f"{rp}: evidence body does not reference approved plan_sha {plan_sha!r}")
            continue
        if (not is_delegation) and plan_ver and plan_ver not in body:
            problems.append(f"{rp}: evidence body does not reference approved plan_version {plan_ver!r}")
            continue
        if is_delegation:
            # delegation records are only used by _delegated(); skip kind handling
            continue

        # Time: original approval must precede earliest impl for applicable files.
        if earliest is not None and _parse_iso(otime) >= _parse_iso(earliest[0]):
            problems.append(f"{rp}: late approval {otime} not before first impl {earliest[0]}")
            continue

        # Scope: allowed files must cover every applicable file; no exclusion hit.
        allowed = [str(a) for a in rec.get("allowed_files", [])]
        excluded = [str(a) for a in rec.get("excluded_files", [])]
        import fnmatch
        for f in applicable:
            for ex in excluded:
                if (ex.endswith("/") and f.startswith(ex)) or fnmatch.fnmatch(f, ex) or f == ex:
                    problems.append(f"{rp}: applicable file {f} is inside approved exclusions ({ex})")
        missing = _covers_all(allowed, applicable)
        if missing:
            problems.append(f"{rp}: approved scope does not cover applicable file(s): {missing}")

        # Authorization per kind + self-approval + delegation.
        implementers = set(rec.get("implementers", [])) | {x for x in [rec.get("implementer")] if x}
        if author in implementers:
            problems.append(f"{rp}: self-approval (evidence author {author} is an implementer)")
            continue

        for kind in kinds:
            if kind == "test_plan":
                ok = (role == role_needed) or _delegated(
                    records, api, pr, reviewers, batch_id, feature, "test_plan", plan_sha)
                if ok:
                    test_ok = rec
                else:
                    problems.append(f"{rp}: test_plan for {feature} must be reviewed by {role_needed} (or a recorded delegation); author role {role!r}")
            elif kind == "execution_plan":
                ok = (role == EXECUTION_PLAN_REVIEWER) or _delegated(
                    records, api, pr, reviewers, batch_id, feature, "execution_plan", plan_sha)
                if ok:
                    exec_ok = rec
                else:
                    problems.append(f"{rp}: execution_plan must be reviewed by {EXECUTION_PLAN_REVIEWER} (or a recorded delegation); author role {role!r}")
            else:
                problems.append(f"{rp}: unknown approval kind {kind!r}")

    if test_ok is None:
        problems.append("missing required test-plan approval for this batch")
    if exec_ok is None:
        problems.append("missing required execution-plan approval for this batch")
    return problems


def _delegated(records, api, pr, reviewers, batch_id, feature, kind, plan_sha) -> bool:
    """True if a separate delegation record authorizes this kind for this batch."""
    for rec in records:
        d = rec.get("delegation")
        if not d:
            continue
        if d.get("batch_id") != batch_id or d.get("kind") != kind:
            continue
        if d.get("plan_sha") and plan_sha and d["plan_sha"][:7] != plan_sha[:7]:
            continue
        try:
            author, otime, body = _resolve_evidence(rec, api, pr)
        except ExecutionError:
            return False
        role = reviewers.get(author)
        # A delegation must be granted by an authorized A (or the role that owns it).
        if role != "A":
            return False
        if d.get("to_role") != ("F" if kind == "test_plan" else EXECUTION_PLAN_REVIEWER):
            return False
        # The delegation evidence must reference the grantee/scope.
        return not (d.get("plan_sha") and d["plan_sha"][:7] not in body and d["plan_sha"] not in body)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-from-file", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--pr", type=int, default=None)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--api-fixture-dir", type=Path, default=None)
    parser.add_argument("--base-ref", default=None)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    changed = [p.decode("utf-8", "replace") for p in args.changed_from_file.read_bytes().split(b"\x00") if p]
    applicable = _applicable(changed)
    if not applicable:
        print("OK: no implementation change; Test Approval gate not applicable")
        return 0

    try:
        reviewers = load_reviewers(root)
        records = load_records(root)
    except ExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not records:
        print("TEST APPROVAL FAILED: implementation change but no approval records", file=sys.stderr)
        return 1

    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF", "")
    if not base_ref:
        print("ERROR: no base ref for history comparison", file=sys.stderr)
        return 2
    try:
        earliest = earliest_impl_for_files(root, base_ref, applicable)
    except ExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if earliest is None:
        # applicable files changed but no impl commit found -> do not silently pass
        print("TEST APPROVAL FAILED: applicable files changed but no implementation "
              "commit found in origin/base..HEAD (ambiguous history)", file=sys.stderr)
        return 1

    api = make_api(args.repo, args.api_fixture_dir)
    try:
        problems = validate_batch(records, api, args.pr, args.batch, applicable, reviewers, earliest)
    except ExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if problems:
        print("TEST APPROVAL FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: batch {args.batch} has valid pre-code test-plan + execution-plan approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
