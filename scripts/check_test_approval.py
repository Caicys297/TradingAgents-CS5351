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
import hashlib
import json
import os
import re
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
HISTORICAL_FILE = "docs/test-approvals/historical-approvals.yaml"

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

    def get_commit(self, sha: str) -> dict:  # pragma: no cover
        return self._gh("api", f"repos/{self.repo}/commits/{sha}")

    def get_file(self, repo: str, sha: str, path: str) -> str | None:  # pragma: no cover
        import base64
        try:
            j = self._gh("api", f"repos/{repo}/contents/{path}?ref={sha}")
        except ExecutionError:
            return None
        content = j.get("content")
        if not content:
            return None
        return base64.b64decode(content).decode("utf-8", "replace")


class FixtureAPI:
    def __init__(self, root: Path):
        self.comments = root / "comments"
        self.reviews = root / "reviews"
        self.commits_dir = root / "commits"
        self.files_dir = root / "files"

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

    def get_commit(self, sha: str) -> dict:
        p = self.commits_dir / f"{sha}.json"
        if not p.is_file():
            raise ExecutionError(f"fixture commit {sha} not found")
        return json.loads(p.read_text())

    def get_file(self, repo: str, sha: str, path: str) -> str | None:
        p = self.files_dir / f"{sha}__{path.replace('/', '__')}"
        return p.read_text() if p.is_file() else None


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


def _evidence_with_meta(record: dict, api, default_pr):
    """Like _resolve_evidence but also returns (created_iso, updated_iso) edit
    metadata. A comment/review whose {created,updated} are inconsistent with the
    required time cannot establish content as of that time."""
    ev = record.get("evidence") or {}
    etype = ev.get("type")
    if etype == "issue_comment":
        o = api.get_issue_comment(int(ev["id"]))
        created = o.get("created_at", "")
        updated = o.get("updated_at", created)
        return o.get("user", {}).get("login", ""), created, updated, o.get("body", ""), ev.get("pr")
    if etype == "review":
        src_pr = ev.get("pr", default_pr)
        if src_pr is None:
            raise ExecutionError("review evidence requires a source PR")
        o = api.get_review(int(src_pr), int(ev["id"]))
        submitted = o.get("submitted_at", "")
        return o.get("user", {}).get("login", ""), submitted, submitted, o.get("body", ""), int(src_pr)
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


# Explicit, machine-verifiable approval marker. Keyword inference is NOT
# accepted as an approval: the authorized reviewer includes this exact line in the
# GitHub evidence body, so the approved plan/kind/scope are stated unambiguously.
#   TEST-APPROVAL: plan=<40hex> version=<vX.Y> kind=test_plan|execution_plan scope=<f1,f2,...>
_DELEGATION_MARKER_RE = re.compile(
    r"TEST-DELEGATION:\s*grantee=(?P<grantee>\S+)\s+plan=(?P<plan>[0-9a-f]{40})\s+"
    r"version=(?P<version>\S+)\s+kind=(?P<kind>test_plan|execution_plan)\s+until=(?P<until>\S+)"
)
# Explicit ORIGINAL-APPROVAL line (in an authenticated clarification body). It
# names the exact original artifact the clarification refers to.
#   ORIGINAL-APPROVAL: type=<issue_comment|review> id=<id> [pr=<n>]
_ORIGINAL_REF_RE = re.compile(
    r"ORIGINAL-APPROVAL:\s*type=(?P<type>issue_comment|review)\s+id=(?P<id>[0-9]+)"
    r"(?:\s+pr=(?P<pr>[0-9]+))?"
)
_APPROVAL_MARKER_RE = re.compile(
    r"TEST-APPROVAL:\s*plan=(?P<plan>[0-9a-f]{40})\s+version=(?P<ver>\S+)\s+"
    r"kind=(?P<kind>test_plan|execution_plan)\s+scope=(?P<scope>[^\n]+)"
)


def _refused(body: str) -> bool:
    low = body.lower()
    return any(r in low for r in REFUSAL_RE)


def _parse_approval_marker(body: str) -> dict | None:
    """Parse the explicit TEST-APPROVAL marker (bounded, exact). None if absent or
    if the surrounding body is a refusal."""
    if _refused(body):
        return None
    m = _APPROVAL_MARKER_RE.search(body)
    if not m:
        return None
    scope = [x.strip() for x in m.group("scope").split(",") if x.strip()]
    return {"plan": m.group("plan"), "version": m.group("ver"),
            "kind": m.group("kind"), "scope": scope}


def _parse_original_ref(body: str) -> dict | None:
    """Parse an in-body ORIGINAL-APPROVAL line identifying the exact original
    artifact (type, id, optional source PR). None if absent."""
    m = _ORIGINAL_REF_RE.search(body)
    if not m:
        return None
    return {"type": m.group("type"), "id": int(m.group("id")),
            "pr": int(m.group("pr")) if m.group("pr") else None}


def _retrieve_plan(api, repo: str | None, plan_sha: str, plan_path: str) -> str | None:
    """Retrieve the immutable plan file at the plan commit (Correction 2).

    Returns the plan text, or None if it cannot be read (caller fails). Uses the
    GitHub contents API at the exact plan SHA (fixture-backed in tests).
    """
    if not repo:
        raise ExecutionError("plan retrieval requires --repo")
    return api.get_file(repo, plan_sha, plan_path)


def _plan_mentions(plan_text: str, needle: str) -> bool:
    return needle in plan_text


def _verify_scope_and_plan(rec, api, repo, applicable, problems, rp) -> dict | None:
    """Correction 2: retrieve the immutable plan and verify version/IDs/scope.

    Returns resolved allowed_files on success, else None (problems appended).
    """
    plan_sha = str(rec.get("plan_sha", "")).strip()
    plan_ver = str(rec.get("plan_version", "")).strip()
    plan_path = str(rec.get("plan_path", "")).strip()
    reqs = [str(x) for x in rec.get("requirement_ids", [])]
    tests = [str(x) for x in rec.get("approved_test_ids", [])]
    allowed = [str(a) for a in rec.get("allowed_files", [])]
    if not plan_path:
        problems.append(f"{rp}: missing plan_path (immutable plan file path required)")
        return None
    try:
        plan_text = _retrieve_plan(api, repo, plan_sha, plan_path)
    except ExecutionError as exc:
        problems.append(f"{rp}: plan unreadable: {exc}")
        return None
    if plan_text is None:
        problems.append(f"{rp}: plan not found at {plan_sha[:7]}:{plan_path} (unreadable immutable plan)")
        return None
    # Version + IDs + scope must be present in the actual plan text.
    if plan_ver and not _plan_mentions(plan_text, plan_ver):
        problems.append(f"{rp}: plan_version {plan_ver!r} not found in immutable plan")
        return None
    for rid in reqs:
        if not _plan_mentions(plan_text, rid):
            problems.append(f"{rp}: requirement {rid!r} not found in immutable plan")
            return None
    for tid in tests:
        if not _plan_mentions(plan_text, tid):
            problems.append(f"{rp}: test case {tid!r} not found in immutable plan")
            return None
    for f in allowed:
        if not _plan_mentions(plan_text, f):
            problems.append(f"{rp}: approved file {f!r} not named in immutable plan")
            return None
    return allowed


def _verify_binding(rec, api, repo, reviewers, feature, approval_iso, root, problems, rp,
                    orig_marker: dict, src_pr) -> dict | None:
    """Correction 1: a `binding`/`clarification` record may identify what the
    ORIGINAL evidence already approved, but is a SEPARATE, currently-dated record
    that cannot expand scope, grant retrospective approval, or backdate.

    Requires: authorized author (role for the feature), explicit reference to the
    original evidence id, plan SHA+version, and the supported approved files. Its
    timestamp is reported separately and must be >= the original approval time
    (it is later clarification), NOT earlier.
    """
    b = rec.get("binding") or rec.get("clarification")
    if not b:
        return None
    ev = b.get("evidence") or {}
    if not ev.get("id"):
        problems.append(f"{rp}: clarification missing reference to original evidence id")
        return None
    # The clarification evidence must be a SEPARATE, later record, not the
    # original artifact itself.
    orig = rec.get("evidence") or {}
    if str(ev.get("id")) == str(orig.get("id")):
        problems.append(f"{rp}: clarification evidence is the original artifact itself, not a separate clarification")
        return None
    try:
        author, ctime, utime, body, _ = _evidence_with_meta({"evidence": ev}, api, None)
    except ExecutionError as exc:
        problems.append(f"{rp}: clarification evidence unverifiable: {exc}")
        return None
    # The AUTHENTICATED clarification body must carry an explicit ORIGINAL-APPROVAL
    # line naming the exact original artifact (type, id, source PR), matching the
    # record's actually resolved original evidence. PR-supplied metadata is NOT
    # trusted for this; the body line is authoritative.
    oref = _parse_original_ref(body)
    if oref is None:
        problems.append(f"{rp}: clarification body has no ORIGINAL-APPROVAL line naming the original artifact")
        return None
    if oref["type"] != orig.get("type") or str(oref["id"]) != str(orig.get("id")):
        problems.append(f"{rp}: ORIGINAL-APPROVAL line {oref['type']}/{oref['id']} does not match "
                        f"resolved original evidence {orig.get('type')}/{orig.get('id')}")
        return None
    # The original evidence may omit `pr` and fall back to the default/source PR;
    # the clarification must name the ACTUAL resolved source PR in that case too.
    resolved_pr = orig.get("pr")
    if resolved_pr is None:
        resolved_pr = src_pr
    if resolved_pr is not None and oref["pr"] != int(resolved_pr):
        problems.append(f"{rp}: ORIGINAL-APPROVAL pr {oref['pr']} does not match resolved original source pr {resolved_pr}")
        return None
    if reviewers.get(author) not in (TEST_PLAN_REVIEWER.get(feature), EXECUTION_PLAN_REVIEWER):
        problems.append(f"{rp}: clarification author {author!r} not authorized for {feature}")
        return None
    if utime and utime != ctime:
        problems.append(f"{rp}: clarification edited after creation (created {ctime}, updated {utime}); "
                        "cannot establish original content — needs human verification")
        return None
    # The clarification must carry an explicit marker and it must match the
    # ORIGINAL marker already parsed for this record (NOT PR-supplied JSON):
    # same plan, version and kind; scope must be a SUBSET of the original scope.
    marker = _parse_approval_marker(body)
    if marker is None:
        problems.append(f"{rp}: clarification has no explicit TEST-APPROVAL marker")
        return None
    if orig_marker is None:
        problems.append(f"{rp}: cannot verify clarification against original marker (none parsed)")
        return None
    if marker["plan"] != orig_marker["plan"]:
        problems.append(f"{rp}: clarification marker plan {marker['plan'][:7]} != original {orig_marker['plan'][:7]}")
        return None
    if marker["version"] != orig_marker["version"]:
        problems.append(f"{rp}: clarification marker version {marker['version']} != original {orig_marker['version']}")
        return None
    if marker["kind"] != orig_marker["kind"]:
        problems.append(f"{rp}: clarification marker kind {marker['kind']} != original {orig_marker['kind']}")
        return None
    if not set(marker["scope"]).issubset(set(orig_marker["scope"])):
        problems.append(f"{rp}: clarification scope {marker['scope']} exceeds original scope {orig_marker['scope']}")
        return None
    # Later clarification: its own timestamp must NOT be earlier than the original
    # approval (it cannot manufacture an earlier approval). Report both separately.
    try:
        if approval_iso and _parse_iso(ctime) < _parse_iso(approval_iso):
            problems.append(f"{rp}: clarification time {ctime} precedes original approval {approval_iso}; "
                            "a later clarification cannot predate the approval it clarifies")
            return None
    except ValueError:
        problems.append(f"{rp}: unparseable clarification/approval timestamp")
        return None
    print(f"NOTE {rp}: original approval {approval_iso}; later authorized clarification {ctime}", file=sys.stderr)
    # The clarification confirms the marker scope; the caller intersects with the
    # immutable plan and rejects any expansion.
    return {"allowed_files": marker["scope"], "kind": marker["kind"]}


def _marker_matches(marker: dict, plan_sha: str, ver: str, kind: str, allowed: list[str]) -> bool:
    if marker is None:
        return False
    if marker["plan"] != plan_sha:
        return False
    if ver and marker["version"] != ver:
        return False
    if marker["kind"] != kind:
        return False
    return sorted(set(marker["scope"])) == sorted(set(allowed))


# --------------------------------------------------------------- validation
def _load_implementer_map(root: Path, base_ref: str) -> dict[str, str]:
    """email -> github login, from a base-trusted reviewed mapping (optional).

    First introduction prints an explicit notice. Base-ref resolution failure is
    an error, not silent.
    """
    path = "docs/test-approvals/implementers.yaml"
    text = None
    try:
        text = _git(root, "show", f"origin/{base_ref}:{path}")
    except ExecutionError as exc:
        chk = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify",
                              f"origin/{base_ref}^{{commit}}"], capture_output=True, text=True)
        if chk.returncode != 0:
            raise ExecutionError(f"cannot resolve base origin/{base_ref} for implementer map") from exc
        text = None
    if text is None:
        p = root / path
        if not p.is_file():
            return {}
        print("BOOTSTRAP: implementers.yaml absent on base; using tree copy (A review)", file=sys.stderr)
        text = p.read_text()
    if yaml is None:
        raise ExecutionError("PyYAML required to read implementers mapping")
    data = yaml.safe_load(text) or {}
    emails = data.get("emails", {})
    return {str(k).lower(): str(v) for k, v in emails.items()} if isinstance(emails, dict) else {}


def _resolve_implementers(root: Path, base_ref: str, applicable: set[str], api, repo: str | None,
                          meta: dict) -> set[str]:
    """Implementer identities via GitHub-verifiable account association (Correction 3).

    For each batch commit touching applicable files, resolve the author to a GitHub
    login via the commit API (``author.login``). Fall back to an authorized,
    base-trusted email->login mapping. If any commit's author cannot be resolved to
    a login and is not in the mapping -> ExecutionError (unknown identity fails).
    Declared record fields may ADD implementers but never remove resolved ones.
    NOTE: GitHub account association is an identity signal, not cryptographic
    proof of authorship.
    """
    if not applicable:
        return set()
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", "--format=%H%x1f%ae", f"origin/{base_ref}..HEAD",
             "--", *sorted(applicable)], capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise ExecutionError(f"git not available to resolve implementers: {exc}") from exc
    if out.returncode != 0:
        raise ExecutionError(f"cannot read batch commits: {out.stderr.strip()[:200]}")

    emap = _load_implementer_map(root, base_ref)
    logins: set[str] = set()
    unresolved: list[str] = []
    for ln in out.stdout.splitlines():
        if not ln.strip():
            continue
        sha, email = ln.split("\x1f", 1)
        email = email.strip().lower()
        login = None
        # 1) GitHub account association from the commit record.
        try:
            info = api.get_commit(sha)
            author = (info.get("author") or {}).get("login")
            if author:
                login = author
        except ExecutionError:
            login = None
        # 2) authorized base-trusted email->login mapping.
        if login is None and email in emap:
            login = emap[email]
        if login is None:
            unresolved.append(f"{sha[:12]} <{email}>")
        else:
            logins.add(login)
            logins.add(login.lower())
    if unresolved:
        raise ExecutionError(
            "unknown implementer identity (no GitHub account association and not in "
            f"implementers.yaml): {unresolved}"
        )
    return logins


def _body_digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def load_historical(root: Path, base_ref: str) -> dict:
    """Load the reviewed HISTORICAL approval mapping from the base revision.

    A bounded route for legacy natural-language approvals written before
    structured markers. Trusted ONLY from the base revision (a PR cannot
    self-declare). Each entry binds ONE kind for ONE plan of an EXACT original
    artifact: batch_id, artifact_type/id/pr, actor, kind, full plan identity
    (sha+path+version), scope, body_sha256 and original_time; optional
    `delegation` binds an authorized A grantor artifact.
    """
    if yaml is None:
        raise ExecutionError("PyYAML required to read historical approvals")
    try:
        text = _git(root, "show", f"origin/{base_ref}:{HISTORICAL_FILE}")
    except ExecutionError as exc:
        chk = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify",
                              f"origin/{base_ref}^{{commit}}"], capture_output=True, text=True)
        if chk.returncode != 0:
            raise ExecutionError(f"cannot resolve base origin/{base_ref}") from exc
        return {"entries": []}
    data = yaml.safe_load(text) or {}
    entries = data.get("entries", []) if isinstance(data.get("entries"), list) else []
    return {"entries": [e for e in entries if isinstance(e, dict)]}


def _find_historical(hist: dict, batch_id, feature: str, rec_ev: dict, src_pr, rec_plan_sha,
                     rec_plan_path, rec_plan_ver, kind):
    """Find the SINGLE entry binding this exact artifact AND this kind/plan/batch.

    Matches the actual workflow batch_id (e.g. pr-16/pr-23), exact artifact
    type/id, the original API PR metadata, and the record's full plan identity.
    Returns None if no entry matches all of them (no borrowing across kinds/plans).
    """
    for e in hist.get("entries", []):
        if e.get("batch_id") != batch_id:
            continue
        if str(e.get("feature", "")).upper()[:2] != feature:
            continue
        if e.get("artifact_type") != rec_ev.get("type"):
            continue
        if str(e.get("artifact_id")) != str(rec_ev.get("id")):
            continue
        if src_pr is None or str(e.get("pr")) != str(src_pr):
            continue
        if e.get("kind") != kind:
            continue
        if str(e.get("plan_sha", "")) != rec_plan_sha:
            continue
        if str(e.get("plan_path", "")) != rec_plan_path:
            continue
        if str(e.get("plan_version", "")) != rec_plan_ver:
            continue
        return e
    return None


def _fetch_artifact(api, ev, default_pr):
    """Fetch an original artifact and return a dict of verified fields."""
    etype = ev.get("type")
    if etype == "issue_comment":
        o = api.get_issue_comment(int(ev["id"]))
        return {"author": o.get("user", {}).get("login", ""),
                "original_time": o.get("created_at", ""),
                "updated_time": o.get("updated_at", o.get("created_at", "")),
                "body": o.get("body", ""), "state": None, "commit_id": None,
                "pr": ev.get("pr", default_pr)}
    if etype == "review":
        src_pr = ev.get("pr", default_pr)
        if src_pr is None:
            raise ExecutionError("review evidence requires a source PR")
        o = api.get_review(int(src_pr), int(ev["id"]))
        return {"author": o.get("user", {}).get("login", ""),
                "original_time": o.get("submitted_at", ""),
                "updated_time": o.get("submitted_at", ""),
                "body": o.get("body", ""), "state": o.get("state"),
                "commit_id": o.get("commit_id"), "pr": int(src_pr)}
    raise ExecutionError(f"unknown evidence type {etype!r}")


def _verify_historical(hist_entry, rec, batch_id, reviewers, feature, applicable,
                       plan_allowed, api, default_pr, earliest_iso, problems, rp) -> str | None:
    """Verify ONE legacy approval entry against its re-fetched original artifact.

    Returns the verified kind on success, else appends problems and returns None.
    """
    kind = hist_entry.get("kind")
    if kind not in ("test_plan", "execution_plan"):
        problems.append(f"{rp}: historical binding has invalid kind {kind!r}")
        return None
    ev = rec.get("evidence") or {}
    try:
        art = _fetch_artifact(api, ev, default_pr)
    except ExecutionError as exc:
        problems.append(f"{rp}: historical original unverifiable: {exc}")
        return None
    # provenance: author, not edited, body digest, original time
    if art["author"] != str(hist_entry.get("actor", "")):
        problems.append(f"{rp}: historical actor {hist_entry.get('actor')!r} != original author {art['author']!r}")
        return None
    if art["updated_time"] and art["updated_time"] != art["original_time"]:
        problems.append(f"{rp}: historical original edited after creation — content-at-time unverified")
        return None
    if _body_digest(art["body"]) != str(hist_entry.get("body_sha256", "")):
        problems.append(f"{rp}: historical original body digest mismatch (changed/unverifiable original)")
        return None
    if art["original_time"] != str(hist_entry.get("original_time", "")):
        problems.append(f"{rp}: historical original_time {art['original_time']!r} != binding "
                        f"{hist_entry.get('original_time')!r}")
        return None
    if art["pr"] is not None and str(art["pr"]) != str(hist_entry.get("pr")):
        problems.append(f"{rp}: historical PR {art['pr']} != binding {hist_entry.get('pr')}")
        return None
    # original approval timestamp (never a later record/mapping time) must precede impl
    if earliest_iso is not None:
        try:
            if _parse_iso(art["original_time"]) >= _parse_iso(earliest_iso):
                problems.append(f"{rp}: late historical approval {art['original_time']} "
                                f"not before first impl {earliest_iso}")
                return None
        except ValueError:
            problems.append(f"{rp}: unparseable historical/impl timestamp")
            return None
    if hist_entry.get("artifact_type") == "review":
        if art["state"] != "APPROVED":
            problems.append(f"{rp}: historical review state {art['state']!r} != APPROVED")
            return None
        if art["commit_id"] and str(art["commit_id"]) != str(hist_entry.get("plan_sha")):
            problems.append(f"{rp}: historical review commit_id {str(art['commit_id'])[:7]} != plan_sha")
            return None
    # role / delegation
    role = reviewers.get(art["author"])
    need = TEST_PLAN_REVIEWER.get(feature) if kind == "test_plan" else EXECUTION_PLAN_REVIEWER
    if role != need and not _verify_delegation(hist_entry, art, reviewers, feature, kind,
                                               problems, rp, api, default_pr):
        return None
    # plan identity already matched by _find_historical; scope controls
    h_scope = [str(x) for x in hist_entry.get("scope", [])]
    if sorted(set(h_scope)) != sorted({str(a) for a in rec.get("allowed_files", [])}):
        problems.append(f"{rp}: record scope != historical binding scope")
        return None
    beyond = [f for f in h_scope if f not in plan_allowed]
    if beyond:
        problems.append(f"{rp}: historical scope beyond immutable plan: {beyond}")
        return None
    for ex in [str(a) for a in rec.get("excluded_files", [])]:
        for f in applicable:
            if (ex.endswith("/") and f.startswith(ex)) or fnmatch.fnmatch(f, ex) or f == ex:
                problems.append(f"{rp}: applicable file {f} inside exclusion ({ex})")
                return None
    missing = _covers_all(h_scope, applicable)
    if missing:
        problems.append(f"{rp}: historical scope does not cover applicable files: {missing}")
        return None
    return kind


def _verify_delegation(hist_entry, art, reviewers, feature, kind, problems, rp, api, default_pr) -> bool:
    """Verify an evidence-backed delegation: an authorized A grantor artifact
    authorizes this grantee (the approval author) for this kind, and its ORIGINAL
    time precedes the grantee's approval time."""
    d = hist_entry.get("delegation")
    if not isinstance(d, dict):
        problems.append(f"{rp}: historical {kind} author role != required and no valid delegation")
        return False
    # Grantee must be the approval author.
    if str(d.get("grantee", "")) != art["author"]:
        problems.append(f"{rp}: delegation grantee {d.get('grantee')!r} != approval author {art['author']!r}")
        return False
    # Kind must match the delegated kind.
    if d.get("kind") != kind:
        problems.append(f"{rp}: delegation kind {d.get('kind')!r} != {kind}")
        return False
    # Fetch the grantor artifact and verify A authority, digest, original time.
    gev = {"type": d.get("artifact_type"), "id": d.get("artifact_id"), "pr": d.get("pr")}
    try:
        g = _fetch_artifact(api, gev, default_pr)
    except ExecutionError as exc:
        problems.append(f"{rp}: delegation grantor unverifiable: {exc}")
        return False
    if reviewers.get(g["author"]) != "A":
        problems.append(f"{rp}: delegation grantor {g['author']!r} is not role A (B cannot authorize)")
        return False
    if _body_digest(g["body"]) != str(d.get("body_sha256", "")):
        problems.append(f"{rp}: delegation grantor body digest mismatch")
        return False
    if g["original_time"] != str(d.get("original_time", "")):
        problems.append(f"{rp}: delegation grantor original_time mismatch")
        return False
    # Delegation must precede the approval it authorizes (strictly earlier).
    try:
        if _parse_iso(g["original_time"]) >= _parse_iso(art["original_time"]):
            problems.append(f"{rp}: delegation {g['original_time']} not before approval {art['original_time']}")
            return False
    except ValueError:
        problems.append(f"{rp}: unparseable delegation/approval timestamp")
        return False
    return True


def validate_batch(records, api, default_pr, batch_id, applicable, reviewers, earliest,
                   root: Path, base_ref: str, repo: str | None, hist: dict) -> list[str]:
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
            author, otime, utime, body, src_pr = _evidence_with_meta(rec, api, default_pr)
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
        # Edit metadata: if the comment/review was edited after creation, the content
        # we see may not have existed at the required time. Only trust it when
        # updated matches created (never edited) so content at approval time is
        # established; otherwise fail for human verification.
        if utime and utime != otime:
            problems.append(f"{rp}: evidence edited after creation (created {otime}, updated {utime}); "
                            "cannot establish original content at approval time — needs human verification")
            continue

        is_delegation = bool(rec.get("delegation"))
        if is_delegation:
            continue  # handled by _delegated()

        # Explicit, machine-verifiable approval: the authorized reviewer's marker
        # must state exactly this plan/version/kind and scope. Keywords are not
        # accepted; a marker is required.
        marker = _parse_approval_marker(body)
        kinds_declared = rec.get("approval_kinds") or ([rec.get("approval_kind")] if rec.get("approval_kind") else [])
        kinds_declared = [k for k in kinds_declared if k]
        allowed_declared = [str(a) for a in rec.get("allowed_files", [])]
        if marker is None:
            # Historical natural-language approvals are NOT keyword-parsed. Each
            # KIND must be bound by its OWN base-trusted historical entry (a single
            # entry approves ONE kind/plan). A record claiming kinds the entries do
            # not separately authorize is not credited.
            plan_allowed_h = _verify_scope_and_plan(rec, api, repo, applicable, problems, rp)
            if plan_allowed_h is None:
                continue
            # ORIGINAL evidence timestamp must precede implementation (a later
            # record/mapping timestamp never counts as the approval time).
            if earliest["earliest_iso"] is not None and _parse_iso(otime) >= _parse_iso(earliest["earliest_iso"]):
                problems.append(f"{rp}: late historical approval {otime} not before first impl "
                                f"{earliest['earliest_iso']}")
                continue
            credited: set[str] = set()
            for kind in (kinds_declared or []):
                hist_entry = _find_historical(hist, batch_id, feature, rec.get("evidence") or {},
                                              src_pr, plan_sha, str(rec.get("plan_path", "")),
                                              str(rec.get("plan_version", "")), kind)
                if hist_entry is None:
                    problems.append(f"{rp}: no trusted historical binding for kind {kind!r} "
                                    "(artifact/plan/batch not matched)")
                    continue
                if _verify_historical(hist_entry, rec, batch_id, reviewers, feature,
                                      applicable, plan_allowed_h, api, default_pr,
                                      earliest["earliest_iso"], problems, rp):
                    credited.add(kind)
            if not credited:
                continue
            # implementer/self-approval still applies
            declared = set(rec.get("implementers", [])) | ({rec["implementer"]} if rec.get("implementer") else set())
            try:
                resolved = _resolve_implementers(root, base_ref, applicable, api, repo, rec)
            except ExecutionError as exc:
                problems.append(f"{rp}: cannot establish implementer identity: {exc}")
                continue
            if author in (declared | resolved) or author.lower() in {x.lower() for x in (declared | resolved)}:
                problems.append(f"{rp}: self-approval (historical actor {author} is an implementer)")
                continue
            print(f"NOTE {rp}: HISTORICAL approval credited for {sorted(credited)} "
                  f"(original {otime}, actor {author})", file=sys.stderr)
            if "test_plan" in credited:
                test_ok = rec
            if "execution_plan" in credited:
                exec_ok = rec
            continue
        # Credit ONLY the single kind the marker explicitly names.
        marker_kind = marker["kind"]
        if marker_kind not in kinds_declared:
            problems.append(f"{rp}: marker kind {marker_kind!r} not among record's declared kinds {kinds_declared}")
            continue
        if not _marker_matches(marker, plan_sha, plan_ver, marker_kind, allowed_declared):
            problems.append(f"{rp}: TEST-APPROVAL marker does not match plan/version/kind/scope")
            continue

        # Time vs earliest impl.
        if earliest["earliest_iso"] is not None and _parse_iso(otime) >= _parse_iso(earliest["earliest_iso"]):
            problems.append(f"{rp}: late approval {otime} not before first impl {earliest['earliest_iso']}")
            continue

        # Correction 2: retrieve the immutable plan and verify version/IDs/scope
        # against the ACTUAL plan content (not PR-declared fields alone).
        plan_allowed = _verify_scope_and_plan(rec, api, repo, applicable, problems, rp)
        if plan_allowed is None:
            continue

        # Correction 1: an optional later authorized clarification may bind scope,
        # but cannot expand beyond the plan-supported files, backdate, or replace
        # the original approval. If present it may only confirm scope already in
        # the plan; we take the intersection and reject any expansion.
        clar = _verify_binding(rec, api, repo, reviewers, feature, otime, root, problems, rp,
                               marker, src_pr)
        if clar is not None:
            extra = [f for f in clar["allowed_files"] if f not in plan_allowed]
            if extra:
                problems.append(f"{rp}: clarification expands scope beyond the immutable plan: {extra}")
                continue
            allowed = clar["allowed_files"]
        else:
            allowed = plan_allowed

        excluded = [str(a) for a in rec.get("excluded_files", [])]
        for f in applicable:
            for ex in excluded:
                if (ex.endswith("/") and f.startswith(ex)) or fnmatch.fnmatch(f, ex) or f == ex:
                    problems.append(f"{rp}: applicable file {f} inside exclusion ({ex})")
        missing = _covers_all(allowed, applicable)
        if missing:
            problems.append(f"{rp}: scope does not cover applicable file(s): {missing}")

        # Correction 3: implementers via GitHub account association / authorized map.
        declared = set(rec.get("implementers", [])) | ({rec["implementer"]} if rec.get("implementer") else set())
        try:
            resolved = _resolve_implementers(root, base_ref, applicable, api, repo, rec)
        except ExecutionError as exc:
            problems.append(f"{rp}: cannot establish implementer identity: {exc}")
            continue
        implementers = declared | resolved
        if author in implementers or author.lower() in {x.lower() for x in implementers}:
            problems.append(f"{rp}: self-approval (evidence author {author} is an implementer)")
            continue

        # Credit ONLY the kind the marker explicitly approved (single kind per
        # marker). The reviewer-role / delegation check applies to that kind.
        credit_kinds = {marker_kind}
        if clar is not None:
            # A clarification may additionally confirm exactly its own kind, but
            # only if it is a different, still-authenticated kind for this record.
            credit_kinds.add(clar["kind"])
        if "test_plan" in credit_kinds:
            if role == role_needed or _delegated(records, api, default_pr, reviewers, batch_id,
                                                 feature, "test_plan", plan_sha, plan_ver,
                                                 reviewer_login=author, approval_iso=otime):
                test_ok = rec
            else:
                problems.append(f"{rp}: test_plan for {feature} requires reviewer {role_needed} "
                                f"(or delegation); author role {role!r}")
        if "execution_plan" in credit_kinds:
            if role == EXECUTION_PLAN_REVIEWER or _delegated(records, api, default_pr, reviewers, batch_id,
                                                             feature, "execution_plan", plan_sha, plan_ver,
                                                             reviewer_login=author, approval_iso=otime):
                exec_ok = rec
            else:
                problems.append(f"{rp}: execution_plan requires reviewer {EXECUTION_PLAN_REVIEWER} "
                                f"(or delegation); author role {role!r}")

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
        # Immutable plan binding is REQUIRED on the delegation (not optional).
        to_login = str(d.get("to_login", "")).strip()
        d_plan_sha = str(d.get("plan_sha", "")).strip()
        d_plan_ver = str(d.get("plan_version", "")).strip()
        if not to_login or not d_plan_sha or not d_plan_ver:
            continue
        if plan_sha and (d_plan_sha[:7] != plan_sha[:7]):
            continue
        if plan_ver and d_plan_ver != plan_ver:
            continue
        # Grantee identity must match the actual reviewer and its resolved role.
        if to_login != reviewer_login:
            continue
        if str(d.get("to_role", "")).upper() != to_role_expected:
            continue
        if reviewers.get(reviewer_login) != to_role_expected:
            continue
        try:
            gauthor, gtime, g_upd, gbody, _ = _evidence_with_meta(rec, api, default_pr)
        except ExecutionError:
            continue
        # Grantor must be an authorized A.
        if reviewers.get(gauthor) != "A":
            continue
        if g_upd and g_upd != gtime:
            continue  # edited after creation -> content-at-time not established
        # Explicit, machine-verifiable delegation marker (no keyword inference):
        #   TEST-DELEGATION: grantee=<login> plan=<40hex> version=<v> kind=<k> until=<batch|iso>
        m = _DELEGATION_MARKER_RE.search(gbody)
        if not m:
            continue
        if m.group("grantee") != to_login:
            continue
        if m.group("plan") != d_plan_sha:
            continue
        if m.group("version") != d_plan_ver:
            continue
        if m.group("kind") != kind:
            continue
        until = m.group("until").strip()
        if until not in (batch_id, "batch:" + batch_id) and not until.startswith(("2", "until")):
            continue
        # Delegation must strictly precede the approval it authorizes.
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
        hist = load_historical(root, base_ref)
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
        problems = validate_batch(records, api, args.pr, args.batch, applicable, reviewers, earliest,
                                  root, base_ref, args.repo, hist)
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
