"""Offline tests for the hardened (2nd pass) pre-code Test Approval Gate checker.

Deterministic: fixture GitHub API + reviewers mapping on the **base revision** +
real temp Git histories. Exercises actual main() exit behavior for each bypass.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
FULL_SHA = "b0287da171cb77673bc7c03c4a6b13535d427730"


def _load():
    spec = importlib.util.spec_from_file_location("cta", SCRIPTS / "check_test_approval.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _git(repo, *args, env=None):
    import os
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=e).stdout.strip()


def _repo(tmp, reviewers_in_base=True):
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "docs/test-approvals").mkdir(parents=True, exist_ok=True)
    if reviewers_in_base:
        (r / "docs/test-approvals/reviewers.yaml").write_text("logins:\n  Caicys297: A\n  fancx777: F\n")
    (r / "base.txt").write_text("b")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    base = _git(r, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", base], check=True)
    return r


def _commit(r, rel, when, content="x", msg="impl"):
    f = r / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", msg, env={"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})
    return _git(r, "rev-parse", "HEAD")


def _comment(fix, cid, author, at, body="Approved"):
    d = fix / "comments"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{cid}.json").write_text(json.dumps({"user": {"login": author}, "created_at": at, "body": body}))


def _record(root, name, **kw):
    d = root / "docs/test-approvals"
    d.mkdir(parents=True, exist_ok=True)
    base = {
        "batch_id": "batch-1", "feature": "O2",
        "approval_kinds": ["test_plan", "execution_plan"],
        "evidence": {"type": "issue_comment", "id": 111},
        "plan_sha": FULL_SHA, "plan_version": "v0.3",
        "requirement_ids": ["O2-FR-01"], "approved_test_ids": ["O2-TC-01"],
        "allowed_files": ["tradingagents/repro/manifest.py"],
        "implementers": ["fancx777"],
    }
    base.update(kw)
    (d / name).write_text(json.dumps(base))


def _changed(tmp, paths):
    z = tmp / "changed.z"
    z.write_bytes(b"".join(p.encode() + b"\x00" for p in paths))
    return z


def _run(mod, root, z, fix, batch="batch-1", pr=0):
    return mod.main(["--changed-from-file", str(z), "--batch", batch, "--root", str(root),
                     "--pr", str(pr), "--api-fixture-dir", str(fix), "--base-ref", "main"])


def _valid(tmp):
    mod = _load()
    r = _repo(tmp)
    fix = tmp / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Approved plan {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _record(r, "o2.json")
    return mod, r, fix, _changed(tmp, ["tradingagents/repro/manifest.py"])


# ---------------------------------------------------------- positive
@pytest.mark.unit
def test_valid_batch_passes(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    assert _run(mod, r, z, fix) == 0


# ---------------------------------------------------------- trusted identity from base
@pytest.mark.unit
def test_pr_self_grant_role_A_rejected(tmp_path):
    """A PR that edits reviewers.yaml to grant itself A cannot self-authorize."""
    mod = _load()
    r = _repo(tmp_path)  # base has Caicys297:A, fancx777:F
    fix = tmp_path / "fix"
    # PR adds a malicious identity ATTEST as A in the working tree
    (r / "docs/test-approvals/reviewers.yaml").write_text(
        "logins:\n  Caicys297: A\n  fancx777: F\n  attacker: A\n")
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "attacker", "2026-11-16T15:02:47Z", body=f"Approved {FULL_SHA} v0.3")
    _record(r, "o2.json")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1  # base mapping wins; attacker not authorized


@pytest.mark.unit
def test_bootstrap_when_mapping_absent_on_base(tmp_path):
    mod = _load()
    r = _repo(tmp_path, reviewers_in_base=False)  # no mapping on base
    # add mapping only in working tree (first introduction)
    (r / "docs/test-approvals/reviewers.yaml").write_text("logins:\n  Caicys297: A\n")
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _record(r, "o2.json", approval_kinds=["test_plan", "execution_plan"])
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    # bootstrap allowed (A-review), passes structurally
    assert _run(mod, r, z, fix) == 0


@pytest.mark.unit
def test_impostor_login_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _comment(fix, 111, "impostor", "2026-11-16T15:02:47Z", body=f"Approved {FULL_SHA} v0.3")
    assert _run(mod, r, z, fix) == 1


# ---------------------------------------------------------- plan binding
@pytest.mark.unit
def test_empty_plan_sha_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _record(r, "o2.json", plan_sha="")
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_short_sha_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _record(r, "o2.json", plan_sha="b0287da")
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_body_mention_without_approval_or_refusal_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Discussing {FULL_SHA} v0.3 but not approved")  # refuses
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_unrelated_comment_mentioning_sha_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body="unrelated note about something else")  # no plan ref/approval
    assert _run(mod, r, z, fix) == 1


# ---------------------------------------------------------- batch/scope
@pytest.mark.unit
def test_unrelated_old_approval_batch_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _record(r, "o2.json", batch_id="other-batch")
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_out_of_scope_file_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _commit(r, "tradingagents/other.py", "2026-11-16T16:00:00+00:00")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py", "tradingagents/other.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_excluded_file_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _record(r, "o2.json", excluded_files=["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


# ---------------------------------------------------------- late/self
@pytest.mark.unit
def test_late_approval_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T14:00:00+00:00")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body=f"Approved {FULL_SHA} v0.3")
    _record(r, "o2.json")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_self_approval_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _record(r, "o2.json", implementers=["Caicys297"])
    assert _run(mod, r, z, fix) == 1


# ---------------------------------------------------------- both kinds / review
@pytest.mark.unit
def test_only_test_plan_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _record(r, "o2.json", approval_kinds=["test_plan"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_later_review_not_precode(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T14:00:00+00:00")
    rv = fix / "reviews"
    rv.mkdir(parents=True, exist_ok=True)
    (rv / "7-222.json").write_text(json.dumps({"user": {"login": "Caicys297"},
                                               "submitted_at": "2026-11-16T16:00:00Z",
                                               "state": "APPROVED", "body": f"Approved {FULL_SHA} v0.3"}))
    _record(r, "o2.json", evidence={"type": "review", "id": 222, "pr": 7})
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix, pr=7) == 1


@pytest.mark.unit
def test_review_from_another_pr_uses_source_pr(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    rv = fix / "reviews"
    rv.mkdir(parents=True, exist_ok=True)
    (rv / "9-333.json").write_text(json.dumps({"user": {"login": "Caicys297"},
                                               "submitted_at": "2026-11-16T15:00:00Z",
                                               "state": "APPROVED",
                                               "body": f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py"}))
    _record(r, "o2.json", evidence={"type": "review", "id": 333, "pr": 9})
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    # current PR is 0 but evidence source pr=9 is used
    assert _run(mod, r, z, fix, pr=0) == 0


# ---------------------------------------------------------- delegation
@pytest.mark.unit
def test_missing_delegation_f_fails_o2(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z", body=f"Approved {FULL_SHA} v0.3")
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z", body=f"Approved exec {FULL_SHA} v0.3")
    _record(r, "o2test.json", approval_kinds=["test_plan"], evidence={"type": "issue_comment", "id": 111},
            implementers=["D"])
    _record(r, "exe.json", approval_kinds=["execution_plan"], evidence={"type": "issue_comment", "id": 112},
            implementers=["D"])
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_valid_delegation_A_to_F(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    # A authorizes F before F's approval; both reference full sha+version.
    _comment(fix, 900, "Caicys297", "2026-11-16T14:00:00Z",
             body=f"Authorize fancx777 to approve {FULL_SHA} v0.4 for this batch")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z",
             body=f"Approved {FULL_SHA} v0.4 for tradingagents/repro/manifest.py")
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z",
             body=f"Approved exec {FULL_SHA} v0.4 for tradingagents/repro/manifest.py")
    _record(r, "deleg.json", feature="O2", approval_kinds=[], implementers=["D"],
            evidence={"type": "issue_comment", "id": 900},
            delegation={"batch_id": "batch-1", "kind": "test_plan", "to_role": "F",
                        "to_login": "fancx777", "feature": "O2", "plan_sha": FULL_SHA,
                        "plan_version": "v0.4"},
            plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "o2test.json", feature="O2", approval_kinds=["test_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 111}, plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "exe.json", feature="O2", approval_kinds=["execution_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 112}, plan_sha=FULL_SHA, plan_version="v0.4")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 0


@pytest.mark.unit
def test_delegation_after_approval_fails(tmp_path):
    """Delegation must precede the approval it authorizes."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 900, "Caicys297", "2026-11-16T15:30:00Z", body=f"Authorize fancx777 {FULL_SHA} v0.4")  # AFTER F
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z", body=f"Approved {FULL_SHA} v0.4")
    _comment(fix, 112, "Caicys297", "2026-11-16T15:40:00Z", body=f"Approved exec {FULL_SHA} v0.4")
    _record(r, "deleg.json", feature="O2", approval_kinds=[], implementers=["D"],
            evidence={"type": "issue_comment", "id": 900},
            delegation={"batch_id": "batch-1", "kind": "test_plan", "to_role": "F",
                        "to_login": "fancx777", "feature": "O2", "plan_sha": FULL_SHA,
                        "plan_version": "v0.4"},
            plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "o2test.json", feature="O2", approval_kinds=["test_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 111}, plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "exe.json", feature="O2", approval_kinds=["execution_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 112}, plan_sha=FULL_SHA, plan_version="v0.4")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


# ---------------------------------------------------------- history
@pytest.mark.unit
def test_incomplete_history_exit2(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    rc = mod.main(["--changed-from-file", str(z), "--batch", "batch-1", "--root", str(r),
                   "--pr", "0", "--api-fixture-dir", str(fix), "--base-ref", "doesnotexist"])
    assert rc == 2


@pytest.mark.unit
def test_nonmonotonic_author_dates_ambiguous(tmp_path):
    """Out-of-order author dates across the batch -> ambiguous -> fail."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T18:00:00+00:00", content="a", msg="later")
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T12:00:00+00:00", content="b", msg="earlier")
    _comment(fix, 111, "Caicys297", "2026-11-16T10:00:00Z", body=f"Approved {FULL_SHA} v0.3")
    _record(r, "o2.json")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_docs_only_not_applicable(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    fix.mkdir()
    z = _changed(tmp_path, ["docs/x.md", "transcripts/y.md"])
    assert _run(mod, r, z, fix) == 0


# ============================================================ new defect tests (A/B/C)
@pytest.mark.unit
def test_neutral_mention_not_approval(tmp_path):
    """A neutral SHA/version mention (no approving verb) must not pass."""
    mod, r, fix, z = _valid(tmp_path)
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Ref: {FULL_SHA} v0.3 tradingagents/repro/manifest.py")  # mention, no approval
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_scope_beyond_source_fails(tmp_path):
    """Declared allowed_files not named in the source body and no binding -> fail."""
    mod, r, fix, z = _valid(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    # allow an extra file the body never names
    _record(r, "o2.json", allowed_files=["tradingagents/repro/manifest.py",
                                         "tradingagents/agents/rating.py"])
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py", "tradingagents/agents/rating.py"])
    rc = _run(mod, r, z, fix)
    assert rc == 1


@pytest.mark.unit
def test_authorized_binding_supports_scope(tmp_path):
    """An authorized binding record supports declared scope beyond body text."""
    mod, r, fix, z = _valid(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _record(r, "o2.json", allowed_files=["tradingagents/repro/manifest.py"],
            binding={"evidence": {"type": "issue_comment", "id": 111},
                     "allowed_files": ["tradingagents/repro/manifest.py"],
                     "requirement_ids": ["O2-FR-01"], "approved_test_ids": ["O2-TC-01"]})
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 0


@pytest.mark.unit
def test_delegation_incomplete_missing_login_fails(tmp_path):
    """Delegation without to_login/plan fields is not valid."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 900, "Caicys297", "2026-11-16T14:00:00Z", body=f"Authorize {FULL_SHA} v0.4")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z",
             body=f"Approved {FULL_SHA} v0.4 for tradingagents/repro/manifest.py")
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z",
             body=f"Approved exec {FULL_SHA} v0.4 tradingagents/repro/manifest.py")
    _record(r, "deleg.json", feature="O2", approval_kinds=[], implementers=["D"],
            evidence={"type": "issue_comment", "id": 900},
            delegation={"batch_id": "batch-1", "kind": "test_plan", "to_role": "F",
                        "feature": "O2", "plan_sha": FULL_SHA, "plan_version": "v0.4"},
            plan_sha=FULL_SHA, plan_version="v0.4")  # no to_login
    _record(r, "o2test.json", feature="O2", approval_kinds=["test_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 111}, plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "exe.json", feature="O2", approval_kinds=["execution_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 112}, plan_sha=FULL_SHA, plan_version="v0.4")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_delegation_unrelated_grantor_fails(tmp_path):
    """Delegation by a non-A (F) cannot authorize F."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 900, "fancx777", "2026-11-16T14:00:00Z",
             body=f"Authorize fancx777 {FULL_SHA} v0.4")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z",
             body=f"Approved {FULL_SHA} v0.4 for tradingagents/repro/manifest.py")
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z",
             body=f"Approved exec {FULL_SHA} v0.4 tradingagents/repro/manifest.py")
    _record(r, "deleg.json", feature="O2", approval_kinds=[], implementers=["D"],
            evidence={"type": "issue_comment", "id": 900},
            delegation={"batch_id": "batch-1", "kind": "test_plan", "to_role": "F",
                        "to_login": "fancx777", "feature": "O2", "plan_sha": FULL_SHA,
                        "plan_version": "v0.4"},
            plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "o2test.json", feature="O2", approval_kinds=["test_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 111}, plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "exe.json", feature="O2", approval_kinds=["execution_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 112}, plan_sha=FULL_SHA, plan_version="v0.4")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_self_approval_when_implementer_omitted_fails(tmp_path):
    """Implementer omitted from record, but git author == evidence author -> self-approval."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    # commit authored by Caicys297 (login-ish name) then Caicys297 approves
    f = r / "tradingagents/repro/manifest.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "impl", env={"GIT_AUTHOR_NAME": "Caicys297",
                                          "GIT_AUTHOR_EMAIL": "Caicys297@users.noreply.github.com",
                                          "GIT_AUTHOR_DATE": "2026-11-16T16:00:00+00:00",
                                          "GIT_COMMITTER_DATE": "2026-11-16T16:00:00+00:00"})
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _record(r, "o2.json")  # no implementers field
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1  # git author resolves to Caicys297 == approver


@pytest.mark.unit
def test_self_approval_false_declared_implementer_still_caught(tmp_path):
    """Record falsely declares implementer=D, but git author is the approver."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    f = r / "tradingagents/repro/manifest.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "impl", env={"GIT_AUTHOR_NAME": "Caicys297",
                                          "GIT_AUTHOR_EMAIL": "Caicys297@users.noreply.github.com",
                                          "GIT_AUTHOR_DATE": "2026-11-16T16:00:00+00:00",
                                          "GIT_COMMITTER_DATE": "2026-11-16T16:00:00+00:00"})
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _record(r, "o2.json", implementers=["D"])  # false declaration
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1
