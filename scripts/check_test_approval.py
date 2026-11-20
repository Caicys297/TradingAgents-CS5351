#!/usr/bin/env python3
"""Pre-code Test Approval Gate checker (REQ-GOV-01/02) — hardened (2nd pass).

Enforced rules (A-confirmed):
- Trusted identity from the **verified base revision** (``origin/<base>``), not
  the PR working tree. First-introduction bootstrap is explicit (not silent); a
  PR that adds/changes reviewers.yaml cannot grant itself a role until the change
  is on the base.
- Records declare a ``batch_id``; the batch is bound and every applicable file
  must be covered; exclusions rejected.
- Both test-plan and execution-plan approval are required (one record may cover
  both) unless an evidence-backed delegation covers one.
- The original evidence must actually approve the plan: full valid plan SHA,
  non-empty version, requirement/case IDs, explicit scope; the body must approve
  (not merely mention, and not refuse) and reference SHA+version. A later
  APPROVED code review is not pre-code approval.
- Delegation must name the grantee login/role, feature, batch, plan SHA+version,
  scope, and its original time must precede the approval/use it authorizes.
- Evidence carries its own source PR (reviews may belong to another PR).
- Earliest implementation is computed across all batch commits with a defensible
  comparison; non-monotonic/ambiguous/rewritten provenance is reported, not
  silently accepted; incomplete history never becomes success.

Workflow trust model (accurate): the job runs this from the PR checkout with a
read-only token; a PR can edit the checker. Trust anchors: the base-revision
reviewers mapping (protected main) + read-only-resolved original evidence.

Usage:
    python scripts/check_test_approval.py --changed-from-file F --batch ID \
        [--repo R] [--pr N] [--root .] [--api-fixture-dir DIR] [--base-ref B]

Exit codes: 0 valid; 1 evidence invalid; 2 execution/API/format error.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
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

# Phrases that indicate refusal / non-approval in an evidence body.
REFUSAL_RE = ("not approved", "cannot approve", "reject", "decline", "no approval",
              "does not approve", "不予批准", "不批准", "拒绝", "不同意")


class ExecutionError(RuntimeError):
    pass


# --------------------------------------------------------------- git
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


# --------------------------------------------------------------- trusted identity
def load_reviewers(root: Path, base_ref: str) -> tuple[dict[str, str], bool]:
    """login->role from the verified base revision.

    Returns (mapping, bootstrapped). If the file is absent on base (genuine first
    introduction), falls back to the working tree and returns bootstrapped=True so
    the caller prints an explicit A-review notice. Base-ref resolution failure ->
    ExecutionError (not silent).
    """
    if yaml is None:
        raise ExecutionError("PyYAML required to read reviewers mapping")
    text = None
    try:
        text = _git(root, "show", f"origin/{base_ref}:{REVIEWERS_FILE}")
    except ExecutionError as exc:
        # Distinguish "file absent on base" (bootstrap) from "git/ref failed".
        chk = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify",
                              f"origin/{base_ref}^{{commit}}"], capture_output=True, text=True)
        if chk.returncode != 0:
            raise ExecutionError(f"cannot resolve base origin/{base_ref}: {chk.stderr.strip()[:200]}") from exc
        text = None  # base resolves, file genuinely absent -> bootstrap

    bootstrapped = False
    if text is None:
        p = root / REVIEWERS_FILE
        if not p.is_file():
            raise ExecutionError(f"trusted reviewers mapping absent on base and in tree: {REVIEWERS_FILE}")
        text = p.read_text()
        bootstrapped = True

    data = yaml.safe_load(text) or {}
    logins = data.get("logins", {})
    if not isinstance(logins, dict) or not logins:
        raise ExecutionError("reviewers mapping has no logins")
    mapping: dict[str, str] = {}
    for login, role in logins.items():
        role = str(role).upper()
        if role not in OWNER_ROLES:
            raise ExecutionError(f"invalid role {role!r} for {login}")
        mapping[str(login)] = role
    return mapping, bootstrapped


# --------------------------------------------------------------- API
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


# --------------------------------------------------------------- earliest impl
def earliest_impl_for_files(root: Path, base_ref: str, applicable: set[str]) -> dict:
    """Return {earliest_iso, sha, ambiguous, reason} for the batch's applicable files.

    Inspects ALL commits in origin/<base>..HEAD touching any applicable path and
    compares their *author* dates. Author dates alone are not proof of preserved
    provenance, so:
      - if the commit order by history topology disagrees with author-date order,
        or a merge is present, or a commit has both author/committer dates far
        apart (possible rewrite), we flag ``ambiguous`` and the caller fails.
    Raises ExecutionError on unavailable history.
    """
    if not applicable:
        return {"earliest_iso": None, "sha": None, "ambiguous": False, "reason": "no applicable files"}
    # Include parents to spot merges; %aI=author, %cI=committer.
    try:
        out = _git(root, "log", "--reverse", "--format=%H%x1f%aI%x1f%cI%x1f%P",
                   f"origin/{base_ref}..HEAD", "--", *sorted(applicable))
    except ExecutionError as exc:
        raise ExecutionError(f"cannot read history for origin/{base_ref}..HEAD: {exc}") from exc
    rows = []
    for ln in out.splitlines():
        if not ln.strip():
            continue
        sha, ai, ci, parents = ln.split("\x1f")
        rows.append({"sha": sha, "author": ai, "committer": ci, "parents": parents.split()})
    if not rows:
        return {"earliest_iso": None, "sha": None, "ambiguous": False, "reason": "no implementing commit"}

    # Defensible earliest = minimum author date across the batch's commits.
    try:
        earliest = min(rows, key=lambda r: _parse_iso(r["author"]))
    except ValueError as exc:
        raise ExecutionError(f"unparseable commit date: {exc}") from exc

    ambiguous_reason = None
    # Merges touching applicable files -> parenthood ambiguity for "first impl".
    if any(len(r["parents"]) > 1 for r in rows):
        ambiguous_reason = "merge commit(s) touch applicable files; earliest is ambiguous"
    # Non-monotonic author vs history order (rebase/rewrite signal).
    try:
        author_seq = [_parse_iso(r["author"]) for r in rows]
        if author_seq != sorted(author_seq):
            ambiguous_reason = ambiguous_reason or "author dates are non-monotonic across the batch history (rebase/rewrite?)"
    except ValueError:
        ambiguous_reason = ambiguous_reason or "unparseable dates in history"
    return {"earliest_iso": earliest["author"], "sha": earliest["sha"],
            "ambiguous": ambiguous_reason is not None, "reason": ambiguous_reason or "ok"}


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


def _resolve_evidence(record: dict, api, default_pr: int | None) -> tuple[str, str, str, int | None]:
    """Return (author, original_iso, body, source_pr). Evidence may carry its own
    ``pr`` (reviews may belong to another PR than the implementing one)."""
    ev = record.get("evidence") or {}
    etype = ev.get("type")
    if etype == "issue_comment":
        o = api.get_issue_comment(int(ev["id"]))
        return o.get("user", {}).get("login", ""), o.get("created_at", ""), o.get("body", ""), ev.get("pr")
    if etype == "review":
        src_pr = ev.get("pr", default_pr)
        if src_pr is None:
            raise ExecutionError("review evidence requires a source PR (evidence.pr or --pr)")
        o = api.get_review(int(src_pr), int(ev["id"]))
        return o.get("user", {}).get("login", ""), o.get("submitted_at", ""), o.get("body", ""), int(src_pr)
    raise ExecutionError(f"unknown evidence type {etype!r}")


def _covers_all(allowed: list[str], applicable: set[str]) -> list[str]:
    missing = []
    for f in applicable:
        if not any((a.endswith("/") and f.startswith(a)) or
                   ("*" in a and fnmatch.fnmatch(f, a)) or f == a for a in allowed):
            missing.append(f)
    return missing


def _invalid_sha(sha: str) -> bool:
    """A record's plan_sha must be a full 40-hex commit SHA (immutable plan id)."""
    return len(sha) != 40 or not all(c in "0123456789abcdef" for c in sha.lower())


def _refused(body: str) -> bool:
    low = body.lower()
    return any(r in low for r in REFUSAL_RE)


def _approves_plan(body: str, plan_sha: str, plan_ver: str) -> bool:
    """Body must reference full(ish) SHA and version AND not be a refusal."""
    if _refused(body):
        return False
    return (plan_sha[:7] in body or plan_sha in body) and (plan_ver in body)


# --------------------------------------------------------------- validation
def validate_batch(records, api, default_pr, batch_id, applicable, reviewers, earliest) -> list[str]:
    problems: list[str] = []
    test_ok = exec_ok = None

    for rec in records:
        rp = rec.get("__path", "<record>")
        if rec.get("batch_id") != batch_id:
            continue
        feature = _feature(rec)
        role_needed = TEST_PLAN_REVIEWER.get(feature)
        if role_needed is None:
            problems.append(f"{rp}: unknown feature {rec.get('feature')!r}")
            continue

        # Full valid plan binding.
        plan_sha = str(rec.get("plan_sha", "")).strip()
        plan_ver = str(rec.get("plan_version", "")).strip()
        if _invalid_sha(plan_sha):
            problems.append(f"{rp}: invalid/empty plan_sha {plan_sha!r} (full commit SHA required)")
            continue
        if not plan_ver:
            problems.append(f"{rp}: empty plan_version")
            continue
        if not rec.get("requirement_ids") or not rec.get("approved_test_ids"):
            problems.append(f"{rp}: missing requirement_ids or approved_test_ids")
            continue

        try:
            author, otime, body, src_pr = _resolve_evidence(rec, api, default_pr)
        except ExecutionError as exc:
            problems.append(f"{rp}: evidence unverifiable: {exc}")
            continue
        role = reviewers.get(author)
        if role is None:
            problems.append(f"{rp}: evidence author {author!r} not an authorized reviewer (base mapping)")
            continue
        if not otime:
            problems.append(f"{rp}: evidence has no original timestamp")
            continue

        is_delegation = bool(rec.get("delegation"))
        if not is_delegation and not _approves_plan(body, plan_sha, plan_ver):
            problems.append(f"{rp}: evidence does not approve plan {plan_sha[:7]} / {plan_ver} "
                            "(missing reference or refusal)")
            continue
        if is_delegation:
            continue  # handled by _delegated()

        # Time vs earliest impl.
        if earliest["earliest_iso"] is not None and _parse_iso(otime) >= _parse_iso(earliest["earliest_iso"]):
            problems.append(f"{rp}: late approval {otime} not before first impl {earliest['earliest_iso']}")
            continue

        # Scope coverage + exclusions.
        allowed = [str(a) for a in rec.get("allowed_files", [])]
        excluded = [str(a) for a in rec.get("excluded_files", [])]
        for f in applicable:
            for ex in excluded:
                if (ex.endswith("/") and f.startswith(ex)) or fnmatch.fnmatch(f, ex) or f == ex:
                    problems.append(f"{rp}: applicable file {f} inside exclusion ({ex})")
        missing = _covers_all(allowed, applicable)
        if missing:
            problems.append(f"{rp}: scope does not cover applicable file(s): {missing}")

        # Self-approval from batch evidence.
        implementers = set(rec.get("implementers", [])) | ({rec["implementer"]} if rec.get("implementer") else set())
        if author in implementers:
            problems.append(f"{rp}: self-approval (author {author} is an implementer)")
            continue

        kinds = rec.get("approval_kinds") or ([rec.get("approval_kind")] if rec.get("approval_kind") else [])
        kinds = [k for k in kinds if k]
        for kind in kinds:
            if kind == "test_plan":
                if role == role_needed or _delegated(records, api, default_pr, reviewers, batch_id,
                                                     feature, "test_plan", plan_sha, plan_ver,
                                                     reviewer_login=author, approval_iso=otime):
                    test_ok = rec
                else:
                    problems.append(f"{rp}: test_plan for {feature} requires reviewer {role_needed} "
                                    f"(or delegation); author role {role!r}")
            elif kind == "execution_plan":
                if role == EXECUTION_PLAN_REVIEWER or _delegated(records, api, default_pr, reviewers, batch_id,
                                                                 feature, "execution_plan", plan_sha, plan_ver,
                                                                 reviewer_login=author, approval_iso=otime):
                    exec_ok = rec
                else:
                    problems.append(f"{rp}: execution_plan requires reviewer {EXECUTION_PLAN_REVIEWER} "
                                    f"(or delegation); author role {role!r}")
            else:
                problems.append(f"{rp}: unknown approval kind {kind!r}")

    if test_ok is None:
        problems.append("missing required test-plan approval for this batch")
    if exec_ok is None:
        problems.append("missing required execution-plan approval for this batch")
    return problems


def _delegated(records, api, default_pr, reviewers, batch_id, feature, kind, plan_sha, plan_ver,
               reviewer_login: str, approval_iso: str) -> bool:
    """True if a valid delegation authorizes ``reviewer_login`` to give ``kind`` for
    this batch/feature/plan. Verifies grantor is A; grantee login/role; scope; and
    that the delegation's original time precedes the approval it authorizes."""
    to_role_expected = "F" if kind == "test_plan" else EXECUTION_PLAN_REVIEWER
    for rec in records:
        d = rec.get("delegation")
        if not d:
            continue
        if d.get("batch_id") != batch_id:
            continue
        if d.get("kind") != kind:
            continue
        if str(d.get("feature", "")).strip()[:2].upper() != feature:
            continue
        if d.get("plan_sha") and plan_sha and d["plan_sha"][:7] != plan_sha[:7]:
            continue
        if d.get("plan_version") and plan_ver and d["plan_version"] != plan_ver:
            continue
        # Grantee identity must match the actual reviewer.
        if d.get("to_login") and d["to_login"] != reviewer_login:
            continue
        if str(d.get("to_role", "")).upper() != to_role_expected:
            continue
        if reviewers.get(reviewer_login) != to_role_expected:
            continue
        try:
            gauthor, gtime, gbody, _ = _resolve_evidence(rec, api, default_pr)
        except ExecutionError:
            continue
        if reviewers.get(gauthor) != "A":
            continue
        # Delegation evidence must reference the plan and grantee.
        if plan_sha and plan_sha[:7] not in gbody and plan_sha not in gbody:
            continue
        if d.get("to_login") and d["to_login"] not in gbody:
            continue
        # Delegation must precede the approval it authorizes.
        try:
            if _parse_iso(gtime) >= _parse_iso(approval_iso):
                continue
        except (ValueError, AttributeError):
            continue
        return True
    return False




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

    base_ref = args.base_ref or os.environ.get("GITHUB_BASE_REF", "")
    if not base_ref:
        print("ERROR: no base ref for trusted mapping + history", file=sys.stderr)
        return 2

    try:
        reviewers, bootstrapped = load_reviewers(root, base_ref)
        records = load_records(root)
    except ExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if bootstrapped:
        print("BOOTSTRAP: reviewers mapping absent on base revision; using this PR's "
              "reviewers.yaml — A must review this first-introduction mapping.", file=sys.stderr)

    if not records:
        print("TEST APPROVAL FAILED: implementation change but no approval records", file=sys.stderr)
        return 1

    try:
        earliest = earliest_impl_for_files(root, base_ref, applicable)
    except ExecutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if earliest["sha"] is None:
        print("TEST APPROVAL FAILED: applicable files changed but no implementation commit "
              "found in origin/base..HEAD (ambiguous history)", file=sys.stderr)
        return 1
    if earliest["ambiguous"]:
        print(f"TEST APPROVAL FAILED: ambiguous implementation provenance: {earliest['reason']}", file=sys.stderr)
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
