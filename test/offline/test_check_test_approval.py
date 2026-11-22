"""Offline tests for the hardened (2nd pass) pre-code Test Approval Gate checker.

Deterministic: fixture GitHub API + reviewers mapping on the **base revision** +
real temp Git histories. Exercises actual main() exit behavior for each bypass.
"""

from __future__ import annotations

import hashlib
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


def _comment(fix, cid, author, at, body="Approved", updated_at=None, issue_pr=None):
    d = fix / "comments"
    d.mkdir(parents=True, exist_ok=True)
    rec = {"user": {"login": author}, "created_at": at, "body": body}
    if issue_pr is not None:
        rec["issue_url"] = f"https://api.github.com/repos/o/r/issues/{issue_pr}"
    if updated_at:
        rec["updated_at"] = updated_at
    (d / f"{cid}.json").write_text(json.dumps(rec))


def _marker(kind="test_plan", plan=FULL_SHA, ver="v0.3", scope="tradingagents/repro/manifest.py"):
    return f"TEST-APPROVAL: plan={plan} version={ver} kind={kind} scope={scope}"


def _markers_both(plan=FULL_SHA, ver="v0.3", scope="tradingagents/repro/manifest.py"):
    return _marker("test_plan", plan, ver, scope) + "\n" + _marker("execution_plan", plan, ver, scope)


def _orig_ref(ref_type="issue_comment", ref_id=111, pr=None):
    tail = f" pr={pr}" if pr is not None else ""
    return f"ORIGINAL-APPROVAL: type={ref_type} id={ref_id}{tail}"


def _clar_body(kind="test_plan", orig_id=111, pr=None, plan=FULL_SHA, ver="v0.3",
               scope="tradingagents/repro/manifest.py"):
    return _orig_ref("issue_comment", orig_id, pr) + "\n" + _marker(kind, plan, ver, scope)


PLAN_TEXT = ("# O2 plan v0.3\nrequirements: O2-FR-01\n"
             "tests: O2-TC-01\nfiles: tradingagents/repro/manifest.py\n")


def _plan(fix, sha, path, text=PLAN_TEXT):
    d = fix / "files"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sha}__{path.replace('/', '__')}").write_text(text)


def _commit_fixture(fix, sha, login):
    d = fix / "commits"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sha}.json").write_text(json.dumps({"sha": sha, "author": {"login": login}}))


def _record(root, name, **kw):
    d = root / "docs/test-approvals"
    d.mkdir(parents=True, exist_ok=True)
    base = {
        "batch_id": "batch-1", "feature": "O2",
        "approval_kinds": ["test_plan", "execution_plan"],
        "evidence": {"type": "issue_comment", "id": 111},
        "plan_sha": FULL_SHA, "plan_version": "v0.3",
        "plan_path": "test-plans/O2-plan.md",
        "requirement_ids": ["O2-FR-01"], "approved_test_ids": ["O2-TC-01"],
        "allowed_files": ["tradingagents/repro/manifest.py"],
        "implementers": ["fancx777"],
    }
    base.update(kw)
    (d / name).write_text(json.dumps(base))


def _dual_records(root, feature="O2", plan_sha=FULL_SHA, plan_ver="v0.3",
                  scope="tradingagents/repro/manifest.py", implementers=None):
    """Write two records for one batch: test_plan (by role) + execution_plan (by A),
    each with its OWN authenticated evidence carrying a marker for that kind."""
    im = implementers if implementers is not None else ["fancx777"]
    _record(root, "o2_test.json", feature=feature, approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=plan_sha, plan_version=plan_ver,
            allowed_files=scope.split(","),
            implementers=im)
    _record(root, "o2_exec.json", feature=feature, approval_kinds=["execution_plan"],
            evidence={"type": "issue_comment", "id": 112},
            plan_sha=plan_sha, plan_version=plan_ver,
            allowed_files=scope.split(","),
            implementers=im)


def _changed(tmp, paths):
    z = tmp / "changed.z"
    z.write_bytes(b"".join(p.encode() + b"\x00" for p in paths))
    return z


def _run(mod, root, z, fix, batch="batch-1", pr=0):
    return mod.main(["--changed-from-file", str(z), "--batch", batch, "--root", str(root),
                     "--pr", str(pr), "--api-fixture-dir", str(fix), "--base-ref", "main",
                     "--repo", "o/r"])


def _register_commits(r, fix, login="fancx777"):
    """Write commit fixtures mapping every commit in origin/main..HEAD to a login."""
    shas = _git(r, "rev-list", "origin/main..HEAD").split()
    for sha in shas:
        _commit_fixture(fix, sha, login)


def _valid(tmp):
    mod = _load()
    r = _repo(tmp)
    fix = tmp / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body=_marker("test_plan"))
    _comment(fix, 112, "Caicys297", "2026-11-16T15:02:48Z", body=_marker("execution_plan"))
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")
    _register_commits(r, fix)
    _dual_records(r)
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
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body=_marker("test_plan"))
    _comment(fix, 112, "Caicys297", "2026-11-16T15:02:48Z", body=_marker("execution_plan"))
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")
    _register_commits(r, fix)
    _dual_records(r)
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
    # rebind both records to a different batch -> none match batch-1
    for name in ("o2_test.json", "o2_exec.json"):
        d = json.loads((r / "docs/test-approvals" / name).read_text())
        d["batch_id"] = "other-batch"
        (r / "docs/test-approvals" / name).write_text(json.dumps(d))
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
    (r / "docs/test-approvals/o2_exec.json").unlink()  # remove the execution_plan record
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
                                               "state": "APPROVED", "body": _marker("test_plan")}))
    (rv / "9-334.json").write_text(json.dumps({"user": {"login": "Caicys297"},
                                               "submitted_at": "2026-11-16T15:00:01Z",
                                               "state": "APPROVED", "body": _marker("execution_plan")}))
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")
    _register_commits(r, fix)
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "review", "id": 333, "pr": 9},
            implementers=["fancx777"])
    _record(r, "o2_exec.json", feature="O2", approval_kinds=["execution_plan"],
            evidence={"type": "review", "id": 334, "pr": 9},
            implementers=["fancx777"])
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
    # A authorizes F (delegation marker) before F's approval; both carry markers.
    _comment(fix, 900, "Caicys297", "2026-11-16T14:00:00Z",
             body=f"TEST-DELEGATION: grantee=fancx777 plan={FULL_SHA} version=v0.4 "
                  "kind=test_plan until=batch-1")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z",
             body=_marker("test_plan", FULL_SHA, "v0.4"))
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z",
             body=_marker("execution_plan", FULL_SHA, "v0.4"))
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
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md",
          text="# O2 v0.4\nO2-FR-01 O2-TC-01 tradingagents/repro/manifest.py\n")
    # implementer is D (not Caicys297/fancx777)
    _register_commits(r, fix, login="D")
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
def test_authorized_clarification_confirms_scope_passes(tmp_path):
    """A later authorized clarification that confirms the plan/kind/scope passes."""
    mod, r, fix, z = _valid(tmp_path)
    # add a separate, later clarification comment (different id) with a marker
    _comment(fix, 777, "Caicys297", "2026-11-16T15:30:00Z", body=_clar_body("test_plan", orig_id=111))
    # attach clarification to the test_plan record
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=FULL_SHA, plan_version="v0.3",
            allowed_files=["tradingagents/repro/manifest.py"],
            implementers=["fancx777"],
            clarification={"evidence": {"type": "issue_comment", "id": 777},
                           "plan_sha": FULL_SHA, "plan_version": "v0.3"})
    assert _run(mod, r, z, fix) == 0


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


# ============================================================ correction-required negatives
@pytest.mark.unit
def test_forged_binding_unauthorized_author_fails(tmp_path):
    """Clarification authored by a non-authorized login cannot bind scope."""
    mod, r, fix, z = _valid(tmp_path)
    _comment(fix, 555, "randomuser", "2026-11-16T15:30:00Z",
             body=f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _record(r, "o2.json", clarification={
        "evidence": {"type": "issue_comment", "id": 555},
        "plan_sha": FULL_SHA, "plan_version": "v0.3",
        "allowed_files": ["tradingagents/repro/manifest.py"]})
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_clarification_cannot_predate_approval(tmp_path):
    """A clarification timestamp earlier than the original approval is rejected."""
    mod, r, fix, z = _valid(tmp_path)
    # original approval at 15:02; clarification claims 14:00 (predates)
    _comment(fix, 556, "Caicys297", "2026-11-16T14:00:00Z",
             body=f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _record(r, "o2.json", clarification={
        "evidence": {"type": "issue_comment", "id": 556},
        "plan_sha": FULL_SHA, "plan_version": "v0.3",
        "allowed_files": ["tradingagents/repro/manifest.py"]})
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_clarification_cannot_expand_scope(tmp_path):
    """Clarification cannot add files beyond the immutable plan's approved set."""
    mod, r, fix, z = _valid(tmp_path)
    # plan only names manifest.py; clarification tries to add rating.py
    _comment(fix, 557, "Caicys297", "2026-11-16T15:30:00Z",
             body=(f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py "
                   "and tradingagents/agents/rating.py"))
    _record(r, "o2.json", clarification={
        "evidence": {"type": "issue_comment", "id": 557},
        "plan_sha": FULL_SHA, "plan_version": "v0.3",
        "allowed_files": ["tradingagents/repro/manifest.py", "tradingagents/agents/rating.py"]})
    # a change touching rating.py is not in the plan scope
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")  # plan names only manifest.py
    _commit(r, "tradingagents/agents/rating.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py", "tradingagents/agents/rating.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_immutable_plan_missing_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    (fix / "files" / f"{FULL_SHA}__test-plans__O2-plan.md").unlink()  # remove plan
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_immutable_plan_version_mismatch_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md",
          text="# O2 plan v9.9\nO2-FR-01 O2-TC-01 tradingagents/repro/manifest.py\n")  # wrong version
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_immutable_plan_missing_test_id_fails(tmp_path):
    mod, r, fix, z = _valid(tmp_path)
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md",
          text="# O2 v0.3\nO2-FR-01 tradingagents/repro/manifest.py\n")  # no O2-TC-01
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_unknown_implementer_identity_fails(tmp_path):
    """Commit author not in commit fixtures and not in implementers.yaml -> fail."""
    mod, r, fix, z = _valid(tmp_path)
    # add a commit fixture-less commit (author t@t unresolved)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:05:00+00:00", content="z", msg="more")
    # do NOT register this new commit fixture
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_verifiable_self_approval_via_commit_fixture_fails(tmp_path):
    """Commit resolves to Caicys297 via commit fixture == approver -> self-approval."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=f"Approved {FULL_SHA} v0.3 for tradingagents/repro/manifest.py")
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")
    _register_commits(r, fix, login="Caicys297")  # implementer == approver
    _record(r, "o2.json", implementers=[])  # omitted; must still catch
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


# ============================================================ Phase-2 review findings
@pytest.mark.unit
def test_edited_after_creation_evidence_fails(tmp_path):
    """If the approval comment was edited after creation, content-at-time is not
    established -> fail for human verification."""
    mod, r, fix, z = _valid(tmp_path)
    # re-write comment 111 with updated_at != created_at, but valid markers
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body=_markers_both(),
             updated_at="2026-11-20T00:00:00Z")
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_delegation_without_marker_fails(tmp_path):
    """A delegation comment lacking TEST-DELEGATION cannot authorize."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 900, "Caicys297", "2026-11-16T14:00:00Z",
             body=f"Authorize fancx777 to approve {FULL_SHA} v0.4")  # prose, no marker
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z", body=_marker("test_plan", FULL_SHA, "v0.4"))
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z", body=_marker("execution_plan", FULL_SHA, "v0.4"))
    _record(r, "deleg.json", feature="O2", approval_kinds=[], implementers=["D"],
            evidence={"type": "issue_comment", "id": 900},
            delegation={"batch_id": "batch-1", "kind": "test_plan", "to_role": "F",
                        "to_login": "fancx777", "feature": "O2", "plan_sha": FULL_SHA,
                        "plan_version": "v0.4"}, plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "o2test.json", feature="O2", approval_kinds=["test_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 111}, plan_sha=FULL_SHA, plan_version="v0.4")
    _record(r, "exe.json", feature="O2", approval_kinds=["execution_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 112}, plan_sha=FULL_SHA, plan_version="v0.4")
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md",
          text="# O2 v0.4\nO2-FR-01 O2-TC-01 tradingagents/repro/manifest.py\n")
    _register_commits(r, fix, login="D")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


# ============================================================ Finding 1 (kind credit + clarification ref)
@pytest.mark.unit
def test_dual_kind_record_single_marker_does_not_credit_execution(tmp_path):
    """A record claiming BOTH kinds but with only a test_plan marker must NOT
    credit execution_plan."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=_marker("test_plan"))  # ONLY test_plan
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")
    _register_commits(r, fix)
    # one record claims both kinds, one evidence (test_plan marker)
    _record(r, "o2.json", approval_kinds=["test_plan", "execution_plan"],
            evidence={"type": "issue_comment", "id": 111})
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1  # execution_plan not credited


@pytest.mark.unit
def test_clarification_wrong_original_reference_fails(tmp_path):
    """A clarification must reference the exact original artifact; a wrong id fails."""
    mod, r, fix, z = _valid(tmp_path)
    # clarification points at a DIFFERENT (nonexistent) original artifact id
    _comment(fix, 999, "Caicys297", "2026-11-16T15:30:00Z", body=_clar_body("test_plan", orig_id=888))
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=FULL_SHA, plan_version="v0.3",
            allowed_files=["tradingagents/repro/manifest.py"], implementers=["fancx777"],
            clarification={"evidence": {"type": "issue_comment", "id": 999},
                           "plan_sha": FULL_SHA, "plan_version": "v0.3"})  # body names wrong id 888
    # the clarification evidence (999) marker exists, but it must bind the SAME
    # original artifact; the record asserts original_evidence_id=111 while evidence
    # is 999 -> mismatch must be rejected
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_clarification_missing_original_line_fails_despite_pr_json(tmp_path):
    """Body must contain ORIGINAL-APPROVAL even if PR JSON original_evidence_id is
    correct; a missing body line fails."""
    mod, r, fix, z = _valid(tmp_path)
    # body has a valid marker but NO ORIGINAL-APPROVAL line
    _comment(fix, 780, "Caicys297", "2026-11-16T15:30:00Z", body=_marker("test_plan"))
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=FULL_SHA, plan_version="v0.3",
            allowed_files=["tradingagents/repro/manifest.py"], implementers=["fancx777"],
            clarification={"evidence": {"type": "issue_comment", "id": 780},
                           "original_evidence_id": 111,  # correct PR JSON, but body lacks line
                           "plan_sha": FULL_SHA, "plan_version": "v0.3"})
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_clarification_body_original_line_must_match(tmp_path):
    """Correct body ORIGINAL-APPROVAL id passes; wrong id fails (body-dependent)."""
    mod, r, fix, z = _valid(tmp_path)
    _comment(fix, 781, "Caicys297", "2026-11-16T15:30:00Z", body=_clar_body("test_plan", orig_id=111))
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=FULL_SHA, plan_version="v0.3",
            allowed_files=["tradingagents/repro/manifest.py"], implementers=["fancx777"],
            clarification={"evidence": {"type": "issue_comment", "id": 781},
                           "plan_sha": FULL_SHA, "plan_version": "v0.3"})
    assert _run(mod, r, z, fix) == 0


@pytest.mark.unit
def test_clarification_marker_plan_mismatch_vs_original_fails(tmp_path):
    """Clarification marker plan must equal the ORIGINAL marker plan, not just the
    clarification's claimed PR metadata. A body whose marker names a different plan
    (even if PR JSON claims the right one) must fail."""
    mod, r, fix, z = _valid(tmp_path)
    wrong_plan = "aa9fda60" + "0" * 32  # 40-hex but different from FULL_SHA
    # body: ORIGINAL-APPROVAL id=111 (correct) + marker with WRONG plan
    _comment(fix, 782, "Caicys297", "2026-11-16T15:30:00Z",
             body=_orig_ref("issue_comment", 111) + "\n" + _marker("test_plan", wrong_plan, "v0.3"))
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=FULL_SHA, plan_version="v0.3",  # PR JSON claims correct plan
            allowed_files=["tradingagents/repro/manifest.py"], implementers=["fancx777"],
            clarification={"evidence": {"type": "issue_comment", "id": 782},
                           "plan_sha": FULL_SHA, "plan_version": "v0.3"})
    assert _run(mod, r, z, fix) == 1

# ============================================================ Historical compatibility route (A review 6005119233)
# Real source texts (verbatim short forms) — NOT rewritten into markers.
A8_POST = ("B，我复核了提交 `b0287da171cb77673bc7c03c4a6b13535d427730` 的 O2 测试计划 "
           "`v0.3-DRAFT` 和 OpenCode 执行计划 `v0.1-DRAFT`。**批准 B 的第一阶段编码前计划**")
A18_POST = ("我按 PR #18 当前 HEAD `aa9fda60bb34c126c65d05ac706fc000cdf8da05` 的 **v0.4-DRAFT** "
            "两份计划复核了范围 ... 以上是 A 对 EXEC v0.4 的编码前执行范围确认")
F18_REVIEW = ("F 已复核提交 `aa9fda60bb34c126c65d05ac706fc000cdf8da05` 的 O2 Stage 2 测试计划 "
              "v0.4-DRAFT，批准本版测试设计")

# Real plan identities (verbatim paths + full SHAs from the approved plans).
P1_SHA = "b0287da171cb77673bc7c03c4a6b13535d427730"
P1_TEST_PATH = "test-plans/O2-Test-Plan-v0.3-DRAFT.md"
P1_EXEC_PATH = "test-plans/O2-OpenCode-Execution-Plan-v0.1-DRAFT.md"
P1_SCOPE = ["tradingagents/repro/manifest.py", "test/offline/test_o2_manifest.py"]
S2_SHA = "aa9fda60bb34c126c65d05ac706fc000cdf8da05"
S2_TEST_PATH = "test-plans/O2-Stage-2-Test-Plan-v0.4-DRAFT.md"
S2_EXEC_PATH = "test-plans/O2-Stage-2-OpenCode-Execution-Plan-v0.4-DRAFT.md"
S2_SCOPE = ["tradingagents/cli/run.py", "test/offline/test_o2_cli_manifest.py"]


def _digest(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _hist_plan_body(path, scope, ver="v0.3", rid="O2-FR-01", tid="O2-TC-01"):
    lines = [f"# {path} {ver}", rid, tid]
    lines += [f"file: {f}" for f in scope]
    return "\n".join(lines) + "\n"


def _hist_entry(**kw):
    base = {"batch_id": "pr-16", "feature": "O2", "artifact_type": "issue_comment",
            "artifact_id": 6920115438, "pr": 8, "actor": "Caicys297", "kind": "test_plan",
            "plan_sha": P1_SHA, "plan_path": P1_TEST_PATH, "plan_version": "v0.3",
            "scope": list(P1_SCOPE), "body_sha256": "", "original_time": ""}
    base.update(kw)
    return base


def _base_with_historical(r, entries, reviewers=True):
    """Commit a base-trusted historical-approvals.yaml and point origin/main at it."""
    import yaml as _yaml
    d = r / "docs/test-approvals"
    d.mkdir(parents=True, exist_ok=True)
    if reviewers:
        (d / "reviewers.yaml").write_text("logins:\n  Caicys297: A\n  fancx777: F\n")
    (d / "historical-approvals.yaml").write_text(_yaml.safe_dump({"entries": entries}, allow_unicode=True))
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base-with-hist")
    base = _git(r, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", base], check=True)


def _write_review(fix, pr, rid, author, at, body, state="APPROVED", commit_id=None):
    d = fix / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    rec = {"user": {"login": author}, "submitted_at": at, "state": state, "body": body}
    if commit_id is not None:
        rec["commit_id"] = commit_id
    (d / f"{pr}-{rid}.json").write_text(json.dumps(rec))


def _hist_repo(tmp_path):
    r = tmp_path / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    return r


# ---------------------------------------------------------- valid historical cases
@pytest.mark.unit
def test_historical_a8_both_plans_accepted(tmp_path):
    """A #8 (6920115438) approves BOTH plans; mapping binds ONE kind per plan
    (v0.3 test, v0.1 exec) as SEPARATE entries; two records credited."""
    mod = _load()
    r = _hist_repo(tmp_path)
    b = _digest(A8_POST)
    _base_with_historical(r, [
        _hist_entry(kind="test_plan", plan_path=P1_TEST_PATH, plan_version="v0.3",
                    body_sha256=b, original_time="2026-11-16T15:02:47Z"),
        _hist_entry(kind="execution_plan", plan_path=P1_EXEC_PATH, plan_version="v0.1",
                    body_sha256=b, original_time="2026-11-16T15:02:47Z"),
    ])
    fix = tmp_path / "fix"
    _comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z", body=A8_POST, issue_pr=8)
    _plan(fix, P1_SHA, P1_TEST_PATH, text=_hist_plan_body(P1_TEST_PATH, P1_SCOPE, "v0.3"))
    _plan(fix, P1_SHA, P1_EXEC_PATH, text=_hist_plan_body(P1_EXEC_PATH, P1_SCOPE, "v0.1"))
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _commit(r, "test/offline/test_o2_manifest.py", "2026-11-16T16:01:00+00:00")
    _register_commits(r, fix)
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 6920115438, "pr": 8},
            plan_sha=P1_SHA, plan_version="v0.3", plan_path=P1_TEST_PATH,
            allowed_files=P1_SCOPE, implementers=["fancx777"], batch_id="pr-16")
    _record(r, "o2_exec.json", feature="O2", approval_kinds=["execution_plan"],
            evidence={"type": "issue_comment", "id": 6920115438, "pr": 8},
            plan_sha=P1_SHA, plan_version="v0.1", plan_path=P1_EXEC_PATH,
            allowed_files=P1_SCOPE, implementers=["fancx777"], batch_id="pr-16")
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 0


@pytest.mark.unit
def test_historical_a18_exec_and_f18_review_test(tmp_path):
    """A #18 7004478311 (exec) + F review 5972069186 (test) at aa9fda60 v0.4 S2
    plans; F's test approval is credited ONLY via A's verified delegation."""
    mod = _load()
    r = _hist_repo(tmp_path)
    a = _digest(A18_POST)
    _base_with_historical(r, [
        _hist_entry(batch_id="pr-23", artifact_id=7004478311, pr=18, kind="execution_plan",
                    plan_sha=S2_SHA, plan_path=S2_EXEC_PATH, plan_version="v0.4",
                    scope=list(S2_SCOPE), body_sha256=a, original_time="2026-11-19T08:58:16Z"),
        _hist_entry(batch_id="pr-23", artifact_type="review", artifact_id=5972069186, pr=18,
                    actor="fancx777", kind="test_plan",
                    plan_sha=S2_SHA, plan_path=S2_TEST_PATH, plan_version="v0.4",
                    scope=list(S2_SCOPE), body_sha256=_digest(F18_REVIEW),
                    original_time="2026-11-19T09:03:12Z",
                    delegation={"artifact_type": "issue_comment", "artifact_id": 7004478311,
                                "pr": 18, "grantee": "fancx777", "kind": "test_plan",
                                "body_sha256": a, "original_time": "2026-11-19T08:58:16Z"}),
    ])
    fix = tmp_path / "fix"
    _comment(fix, 7004478311, "Caicys297", "2026-11-19T08:58:16Z", body=A18_POST, issue_pr=18)
    _write_review(fix, 18, 5972069186, "fancx777", "2026-11-19T09:03:12Z", F18_REVIEW,
                  state="APPROVED", commit_id=S2_SHA)
    _plan(fix, S2_SHA, S2_TEST_PATH, text=_hist_plan_body(S2_TEST_PATH, S2_SCOPE, "v0.4"))
    _plan(fix, S2_SHA, S2_EXEC_PATH, text=_hist_plan_body(S2_EXEC_PATH, S2_SCOPE, "v0.4"))
    _commit(r, "tradingagents/cli/run.py", "2026-11-19T10:00:00+00:00")
    _commit(r, "test/offline/test_o2_cli_manifest.py", "2026-11-19T10:01:00+00:00")
    _register_commits(r, fix, login="D")
    _record(r, "o2_exec.json", feature="O2", approval_kinds=["execution_plan"],
            evidence={"type": "issue_comment", "id": 7004478311, "pr": 18},
            plan_sha=S2_SHA, plan_version="v0.4", plan_path=S2_EXEC_PATH,
            allowed_files=S2_SCOPE, implementers=["D"], batch_id="pr-23")
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "review", "id": 5972069186, "pr": 18},
            plan_sha=S2_SHA, plan_version="v0.4", plan_path=S2_TEST_PATH,
            allowed_files=S2_SCOPE, implementers=["D"], batch_id="pr-23")
    z = _changed(tmp_path, S2_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-23", pr=23) == 0


# ---------------------------------------------------------- helpers for negatives
def _a8_base(r, **entry_kw):
    kw = {"kind": "test_plan", "plan_path": P1_TEST_PATH, "plan_version": "v0.3",
          "body_sha256": _digest(A8_POST), "original_time": "2026-11-16T15:02:47Z"}
    kw.update(entry_kw)
    _base_with_historical(r, [_hist_entry(**kw)])


def _a8_fixture(tmp_path, body=A8_POST, plan_path=P1_TEST_PATH, ver="v0.3", issue_pr=8):
    fix = tmp_path / "fix"
    _comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z", body=body, issue_pr=issue_pr)
    _plan(fix, P1_SHA, plan_path, text=_hist_plan_body(plan_path, P1_SCOPE, ver))
    return fix


def _a8_record(r, **kw):
    base = {"feature": "O2", "approval_kinds": ["test_plan"],
            "evidence": {"type": "issue_comment", "id": 6920115438, "pr": 8},
            "plan_sha": P1_SHA, "plan_version": "v0.3", "plan_path": P1_TEST_PATH,
            "allowed_files": P1_SCOPE, "implementers": ["fancx777"], "batch_id": "pr-16"}
    base.update(kw)
    _record(r, "o2.json", **base)


# ---------------------------------------------------------- negative cases
@pytest.mark.unit
def test_historical_missing_original_fails(tmp_path):
    """Record references a comment id with no fixture (original missing) -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)
    fix = tmp_path / "fix"
    fix.mkdir()
    _plan(fix, P1_SHA, P1_TEST_PATH, text=_hist_plan_body(P1_TEST_PATH, P1_SCOPE))
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_late_approval_fails(tmp_path):
    """Implementation precedes the ORIGINAL approval time -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)
    fix = _a8_fixture(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T12:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_untrusted_mapping_from_pr_fails(tmp_path):
    """A mapping added only in the PR tree (not base) is not trusted."""
    mod = _load()
    r = _repo(tmp_path)
    import yaml as _yaml
    (r / "docs/test-approvals/historical-approvals.yaml").write_text(_yaml.safe_dump({"entries": [
        _hist_entry(body_sha256=_digest(A8_POST), original_time="2026-11-16T15:02:47Z")]}))
    fix = _a8_fixture(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_cross_batch_fails(tmp_path):
    """Entry bound to pr-8 cannot credit a pr-23 batch."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)
    fix = _a8_fixture(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r, batch_id="pr-23")
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-23", pr=23) == 1


@pytest.mark.unit
def test_historical_cross_plan_fails(tmp_path):
    """Entry bound to the test-plan path cannot credit a different plan path."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)
    other = "test-plans/O2-Other-Plan-v0.3.md"
    fix = _a8_fixture(tmp_path, plan_path=other)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r, plan_path=other)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_out_of_scope_fails(tmp_path):
    """Applicable file outside the binding scope -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r, scope=list(P1_SCOPE))
    fix = _a8_fixture(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _commit(r, "tradingagents/other.py", "2026-11-16T16:02:00+00:00")
    _register_commits(r, fix)
    _a8_record(r, allowed_files=list(P1_SCOPE) + ["tradingagents/other.py"])
    z = _changed(tmp_path, list(P1_SCOPE) + ["tradingagents/other.py"])
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_edited_original_fails(tmp_path):
    """Original comment edited after creation -> content-at-time unverified -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)
    fix = tmp_path / "fix"
    _comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z", body=A8_POST,
             updated_at="2026-11-16T15:30:00Z", issue_pr=8)
    _plan(fix, P1_SHA, P1_TEST_PATH, text=_hist_plan_body(P1_TEST_PATH, P1_SCOPE))
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_body_digest_mismatch_fails(tmp_path):
    """Base mapping body digest does not match the fetched original -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r, body_sha256="0" * 64)
    fix = _a8_fixture(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_review_not_approved_fails(tmp_path):
    """Review bound as test approval but fetched as CHANGES_REQUESTED -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _base_with_historical(r, [
        _hist_entry(batch_id="pr-23", artifact_type="review", artifact_id=5972069186, pr=18,
                    actor="fancx777", kind="test_plan",
                    plan_sha=S2_SHA, plan_path=S2_TEST_PATH, plan_version="v0.4",
                    scope=list(S2_SCOPE), body_sha256=_digest(F18_REVIEW),
                    original_time="2026-11-19T09:03:12Z",
                    delegation={"artifact_type": "issue_comment", "artifact_id": 7004478311,
                                "pr": 18, "grantee": "fancx777", "kind": "test_plan",
                                "body_sha256": _digest(A18_POST),
                                "original_time": "2026-11-19T08:58:16Z"})])
    fix = tmp_path / "fix"
    _comment(fix, 7004478311, "Caicys297", "2026-11-19T08:58:16Z", body=A18_POST, issue_pr=18)
    _write_review(fix, 18, 5972069186, "fancx777", "2026-11-19T09:03:12Z", F18_REVIEW,
                  state="CHANGES_REQUESTED", commit_id=S2_SHA)
    _plan(fix, S2_SHA, S2_TEST_PATH, text=_hist_plan_body(S2_TEST_PATH, S2_SCOPE, "v0.4"))
    _commit(r, "tradingagents/cli/run.py", "2026-11-19T10:00:00+00:00")
    _register_commits(r, fix, login="D")
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "review", "id": 5972069186, "pr": 18},
            plan_sha=S2_SHA, plan_version="v0.4", plan_path=S2_TEST_PATH,
            allowed_files=S2_SCOPE, implementers=["D"], batch_id="pr-23")
    z = _changed(tmp_path, S2_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-23", pr=23) == 1


@pytest.mark.unit
def test_historical_missing_delegation_fails(tmp_path):
    """F (O2 test reviewer is A) with NO delegation block -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _base_with_historical(r, [
        _hist_entry(batch_id="pr-23", artifact_type="review", artifact_id=5972069186, pr=18,
                    actor="fancx777", kind="test_plan",
                    plan_sha=S2_SHA, plan_path=S2_TEST_PATH, plan_version="v0.4",
                    scope=list(S2_SCOPE), body_sha256=_digest(F18_REVIEW),
                    original_time="2026-11-19T09:03:12Z")])
    fix = tmp_path / "fix"
    _comment(fix, 7004478311, "Caicys297", "2026-11-19T08:58:16Z", body=A18_POST, issue_pr=18)
    _write_review(fix, 18, 5972069186, "fancx777", "2026-11-19T09:03:12Z", F18_REVIEW,
                  state="APPROVED", commit_id=S2_SHA)
    _plan(fix, S2_SHA, S2_TEST_PATH, text=_hist_plan_body(S2_TEST_PATH, S2_SCOPE, "v0.4"))
    _commit(r, "tradingagents/cli/run.py", "2026-11-19T10:00:00+00:00")
    _register_commits(r, fix, login="D")
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "review", "id": 5972069186, "pr": 18},
            plan_sha=S2_SHA, plan_version="v0.4", plan_path=S2_TEST_PATH,
            allowed_files=S2_SCOPE, implementers=["D"], batch_id="pr-23")
    z = _changed(tmp_path, S2_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-23", pr=23) == 1


@pytest.mark.unit
def test_historical_delegation_by_B_fails(tmp_path):
    """Delegation granted by B (7004545668, role B), not A -> cannot authorize F."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _base_with_historical(r, [
        _hist_entry(batch_id="pr-23", artifact_type="review", artifact_id=5972069186, pr=18,
                    actor="fancx777", kind="test_plan",
                    plan_sha=S2_SHA, plan_path=S2_TEST_PATH, plan_version="v0.4",
                    scope=list(S2_SCOPE), body_sha256=_digest(F18_REVIEW),
                    original_time="2026-11-19T09:03:12Z",
                    delegation={"artifact_type": "issue_comment", "artifact_id": 7004545668,
                                "pr": 18, "grantee": "fancx777", "kind": "test_plan",
                                "body_sha256": _digest("B note"),
                                "original_time": "2026-11-19T08:30:00Z"})])
    fix = tmp_path / "fix"
    _comment(fix, 7004545668, "QinQilun", "2026-11-19T08:30:00Z", body="B note", issue_pr=18)
    _write_review(fix, 18, 5972069186, "fancx777", "2026-11-19T09:03:12Z", F18_REVIEW,
                  state="APPROVED", commit_id=S2_SHA)
    _plan(fix, S2_SHA, S2_TEST_PATH, text=_hist_plan_body(S2_TEST_PATH, S2_SCOPE, "v0.4"))
    _commit(r, "tradingagents/cli/run.py", "2026-11-19T10:00:00+00:00")
    _register_commits(r, fix, login="D")
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "review", "id": 5972069186, "pr": 18},
            plan_sha=S2_SHA, plan_version="v0.4", plan_path=S2_TEST_PATH,
            allowed_files=S2_SCOPE, implementers=["D"], batch_id="pr-23")
    z = _changed(tmp_path, S2_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-23", pr=23) == 1


@pytest.mark.unit
def test_historical_delegation_after_approval_fails(tmp_path):
    """A delegation timestamped at/after F's review cannot authorize it -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _base_with_historical(r, [
        _hist_entry(batch_id="pr-23", artifact_type="review", artifact_id=5972069186, pr=18,
                    actor="fancx777", kind="test_plan",
                    plan_sha=S2_SHA, plan_path=S2_TEST_PATH, plan_version="v0.4",
                    scope=list(S2_SCOPE), body_sha256=_digest(F18_REVIEW),
                    original_time="2026-11-19T09:03:12Z",
                    delegation={"artifact_type": "issue_comment", "artifact_id": 7004478311,
                                "pr": 18, "grantee": "fancx777", "kind": "test_plan",
                                "body_sha256": _digest(A18_POST),
                                "original_time": "2026-11-19T09:10:00Z"})])
    fix = tmp_path / "fix"
    _comment(fix, 7004478311, "Caicys297", "2026-11-19T09:10:00Z", body=A18_POST, issue_pr=18)
    _write_review(fix, 18, 5972069186, "fancx777", "2026-11-19T09:03:12Z", F18_REVIEW,
                  state="APPROVED", commit_id=S2_SHA)
    _plan(fix, S2_SHA, S2_TEST_PATH, text=_hist_plan_body(S2_TEST_PATH, S2_SCOPE, "v0.4"))
    _commit(r, "tradingagents/cli/run.py", "2026-11-19T10:00:00+00:00")
    _register_commits(r, fix, login="D")
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "review", "id": 5972069186, "pr": 18},
            plan_sha=S2_SHA, plan_version="v0.4", plan_path=S2_TEST_PATH,
            allowed_files=S2_SCOPE, implementers=["D"], batch_id="pr-23")
    z = _changed(tmp_path, S2_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-23", pr=23) == 1


@pytest.mark.unit
def test_historical_declared_kinds_beyond_binding_fails(tmp_path):
    """Record declares both kinds but only test_plan is bound -> exec unapproved."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)
    fix = _a8_fixture(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r, approval_kinds=["test_plan", "execution_plan"])
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_api_source_pr_mismatch_fails(tmp_path):
    """The approval's source PR is derived from GitHub's issue_url; if that PR
    differs from the bound original `pr`, the binding must not match -> fail."""
    mod = _load()
    r = _hist_repo(tmp_path)
    # Entry bound to source PR #8, but the fetched comment lives in issue/PR #99.
    _a8_base(r)  # pr=8
    fix = _a8_fixture(tmp_path, issue_pr=99)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    _a8_record(r)
    z = _changed(tmp_path, P1_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-16", pr=16) == 1


@pytest.mark.unit
def test_historical_record_declared_pr_ignored(tmp_path, capsys):
    """A matching API source PR (#8 via issue_url) still binds even if the record
    declares a different `pr`; the source PR comes from issue_url, not the record.
    The batch still fails overall only because no execution approval is bound."""
    mod = _load()
    r = _hist_repo(tmp_path)
    _a8_base(r)  # bound pr=8
    fix = _a8_fixture(tmp_path, issue_pr=8)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _register_commits(r, fix)
    # record lies about pr=777, but issue_url says 8 -> binding still matches
    _a8_record(r, evidence={"type": "issue_comment", "id": 6920115438, "pr": 777})
    z = _changed(tmp_path, P1_SCOPE)
    rc = _run(mod, r, z, fix, batch="pr-16", pr=16)
    err = capsys.readouterr().err
    assert "credited for ['test_plan']" in err
    assert "missing required execution-plan approval" in err
    assert rc == 1


# ============================================================ CI/governance authorization migration
# Separately authorized rule: for a GENUINE F-implemented CI/governance batch,
# a NON-implementer A reviews BOTH the Test Plan and the Execution Plan. These
# tests prove the positive path AND that every existing safeguard still rejects
# (self-approval, unauthorized author, unrelated batch, late approval, mismatched
# plan/scope) and that non-CI features keep their product-feature reviewer.
CI_SHA = "c0ffee0000000000000000000000000000000042"
CI_PLAN_PATH = "test-plans/ci-closure-v5/Test-Plan.md"
CI_SCOPE = ["scripts/check_test_approval.py"]


def _ci_plan_text(scope=None, ver="v1.0", rid="GOV-07", tid="GOV-T01"):
    scope = scope if scope is not None else CI_SCOPE
    lines = [f"# CI Closure Test Plan {ver}", rid, tid]
    lines += [f"file: {f}" for f in scope]
    return "\n".join(lines) + "\n"


def _ci_record(root, name, **kw):
    base = {
        "batch_id": "pr-40", "feature": "CI",
        "plan_sha": CI_SHA, "plan_version": "v1.0", "plan_path": CI_PLAN_PATH,
        "requirement_ids": ["GOV-07"], "approved_test_ids": ["GOV-T01"],
        "allowed_files": list(CI_SCOPE), "implementers": ["fancx777"],
    }
    base.update(kw)
    _record(root, name, **base)


def _ci_dual_records(root, **kw):
    """One test_plan record (A) + one execution_plan record (A), each own marker."""
    _ci_record(root, "ci_test.json", approval_kinds=["test_plan"],
               evidence={"type": "issue_comment", "id": 401}, **kw)
    _ci_record(root, "ci_exec.json", approval_kinds=["execution_plan"],
               evidence={"type": "issue_comment", "id": 402}, **kw)


def _ci_valid(tmp, impl_login="fancx777", feat="CI", scope=None, ver="v1.0",
              batch="pr-40"):
    """A genuine CI/governance batch: F implements, non-implementer A approves both."""
    mod = _load()
    r = _repo(tmp)
    fix = tmp / "fix"
    scope = scope if scope is not None else CI_SCOPE
    _commit(r, scope[0], "2026-11-16T16:00:00+00:00")
    _comment(fix, 401, "Caicys297", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, ver, ",".join(scope)))
    _comment(fix, 402, "Caicys297", "2026-11-16T15:02:48Z",
             body=_marker("execution_plan", CI_SHA, ver, ",".join(scope)))
    _plan(fix, CI_SHA, CI_PLAN_PATH, text=_ci_plan_text(scope, ver))
    _register_commits(r, fix, login=impl_login)
    _ci_dual_records(r, feature=feat, plan_version=ver, allowed_files=list(scope),
                     batch_id=batch, implementers=[impl_login])
    return mod, r, fix, _changed(tmp, scope)


# ---------------------------------------------------------- positive
@pytest.mark.unit
def test_ci_governance_A_approves_both_plans_passes(tmp_path):
    """Non-implementer A approves both plan kinds for a genuine F-implemented CI
    batch -> valid (the authorized migration path)."""
    mod, r, fix, z = _ci_valid(tmp_path)
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 0


# ---------------------------------------------------------- safeguards preserved
@pytest.mark.unit
def test_ci_governance_self_approval_rejected(tmp_path):
    """A both implements and approves the CI batch -> self-approval rejected."""
    mod, r, fix, z = _ci_valid(tmp_path, impl_login="Caicys297")
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_governance_unauthorized_author_rejected(tmp_path):
    """A non-A (here B) approving a CI test plan is rejected (narrow A rule only)."""
    mod, r, fix, z = _ci_valid(tmp_path)
    # reviewers.yaml in fixture base maps only Caicys297:A, fancx777:F; use an
    # unknown login to represent an unauthorized author.
    _comment(fix, 401, "attacker", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, "v1.0", ",".join(CI_SCOPE)))
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_governance_F_author_cannot_test_plan(tmp_path):
    """F (the implementer role) is NOT A; F cannot approve the CI test plan."""
    mod, r, fix, z = _ci_valid(tmp_path)
    _comment(fix, 401, "fancx777", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, "v1.0", ",".join(CI_SCOPE)))
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_governance_unrelated_batch_rejected(tmp_path):
    """Records bound to one CI batch cannot authorize a different batch."""
    mod, r, fix, z = _ci_valid(tmp_path)
    assert _run(mod, r, z, fix, batch="pr-999", pr=999) == 1


@pytest.mark.unit
def test_ci_governance_late_approval_rejected(tmp_path):
    """Implementation precedes A's approval -> not pre-code approval -> rejected."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, CI_SCOPE[0], "2026-11-16T14:00:00+00:00")  # before approval
    _comment(fix, 401, "Caicys297", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, "v1.0", ",".join(CI_SCOPE)))
    _comment(fix, 402, "Caicys297", "2026-11-16T15:02:48Z",
             body=_marker("execution_plan", CI_SHA, "v1.0", ",".join(CI_SCOPE)))
    _plan(fix, CI_SHA, CI_PLAN_PATH, text=_ci_plan_text())
    _register_commits(r, fix)
    _ci_dual_records(r)
    z = _changed(tmp_path, CI_SCOPE)
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_governance_scope_mismatch_rejected(tmp_path):
    """A file outside the immutable plan's approved scope is rejected."""
    mod, r, fix, z = _ci_valid(tmp_path)
    # change an extra implementation file not in the plan/records
    _commit(r, "tradingagents/other.py", "2026-11-16T16:00:00+00:00")
    z = _changed(tmp_path, CI_SCOPE + ["tradingagents/other.py"])
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_governance_plan_mismatch_rejected(tmp_path):
    """Plan version claimed by the record absent from the immutable plan -> fail."""
    mod, r, fix, z = _ci_valid(tmp_path, ver="v1.0")
    # immutable plan text says a different version than the record claims
    _plan(fix, CI_SHA, CI_PLAN_PATH, text=_ci_plan_text(ver="v9.9"))
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


# ---------------------------------------------------------- no blanket override
@pytest.mark.unit
def test_non_ci_feature_keeps_product_reviewer(tmp_path):
    """O4 (product feature) still requires F for the test plan: A cannot approve
    the O4 test plan just because A can approve CI. Proves the rule is scoped."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    # A tries to approve the O4 test plan (should require F) + exec (A)
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", FULL_SHA, "v0.3"))
    _comment(fix, 112, "Caicys297", "2026-11-16T15:02:48Z",
             body=_marker("execution_plan", FULL_SHA, "v0.3"))
    _plan(fix, FULL_SHA, "test-plans/O2-plan.md")
    _register_commits(r, fix)
    _dual_records(r, feature="O4")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1  # O4 test plan by A is not authorized


# ============================================================ CI/governance boundary completion
# The special A test-plan authority requires the batch to be GENUINELY
# F-implemented AND limited to CI/governance work. A product implementation
# merely relabelled "CI", or a non-F-implemented batch, must NOT qualify.
def _repo_with_reviewers(tmp, mapping_yaml):
    """Like _repo but with a custom base-committed reviewers.yaml mapping."""
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "docs/test-approvals").mkdir(parents=True, exist_ok=True)
    (r / "docs/test-approvals/reviewers.yaml").write_text(mapping_yaml)
    (r / "base.txt").write_text("b")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    base = _git(r, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", base], check=True)
    return r


@pytest.mark.unit
def test_ci_relabelled_product_implementation_rejected(tmp_path):
    """A product implementation (tradingagents/) merely relabelled feature=CI must
    NOT receive the A test-plan authority; the batch is not CI/governance work."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    prod_scope = ["tradingagents/repro/manifest.py"]
    _commit(r, prod_scope[0], "2026-11-16T16:00:00+00:00")
    _comment(fix, 401, "Caicys297", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, "v1.0", ",".join(prod_scope)))
    _comment(fix, 402, "Caicys297", "2026-11-16T15:02:48Z",
             body=_marker("execution_plan", CI_SHA, "v1.0", ",".join(prod_scope)))
    # immutable plan names the product file and plan lives under a CI path so the
    # plan-retrieval/version check passes; only the SCOPE qualification must fail.
    _plan(fix, CI_SHA, CI_PLAN_PATH, text=_ci_plan_text(prod_scope))
    _register_commits(r, fix, login="fancx777")
    _ci_dual_records(r, allowed_files=prod_scope, implementers=["fancx777"])
    z = _changed(tmp_path, prod_scope)
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_non_F_implementer_rejected(tmp_path):
    """Implemented by role A (non-F) but approved by a DIFFERENT A (no self-approval):
    still rejected because the batch is not F-implemented."""
    mod = _load()
    r = _repo_with_reviewers(
        tmp_path, "logins:\n  Caicys297: A\n  OtherA: A\n  fancx777: F\n")
    fix = tmp_path / "fix"
    scope = CI_SCOPE
    _commit(r, scope[0], "2026-11-16T16:00:00+00:00")
    # OtherA (role A) approves; Caicys297 (role A) is the implementer -> non-F, no self.
    _comment(fix, 401, "OtherA", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, "v1.0", ",".join(scope)))
    _comment(fix, 402, "OtherA", "2026-11-16T15:02:48Z",
             body=_marker("execution_plan", CI_SHA, "v1.0", ",".join(scope)))
    _plan(fix, CI_SHA, CI_PLAN_PATH, text=_ci_plan_text(scope))
    _register_commits(r, fix, login="Caicys297")  # implementer is role A, not F
    _ci_dual_records(r, allowed_files=list(scope), implementers=["Caicys297"])
    z = _changed(tmp_path, scope)
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_genuine_F_implemented_governance_scope_passes(tmp_path):
    """Positive control for the boundary: F implements multiple CI/governance files
    (scripts + docs/ci + test) and non-implementer A approves both -> passes."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    scope = ["scripts/check_test_approval.py", "docs/ci/Test-Approval-Status.md",
             "test/offline/test_check_test_approval.py"]
    for p in scope:
        _commit(r, p, "2026-11-16T16:00:00+00:00")
    _comment(fix, 401, "Caicys297", "2026-11-16T15:02:47Z",
             body=_marker("test_plan", CI_SHA, "v1.0", ",".join(scope)))
    _comment(fix, 402, "Caicys297", "2026-11-16T15:02:48Z",
             body=_marker("execution_plan", CI_SHA, "v1.0", ",".join(scope)))
    _plan(fix, CI_SHA, CI_PLAN_PATH, text=_ci_plan_text(scope))
    _register_commits(r, fix, login="fancx777")
    _ci_dual_records(r, allowed_files=list(scope), implementers=["fancx777"])
    z = _changed(tmp_path, scope)
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 0


@pytest.mark.unit
def test_ci_mixed_product_and_governance_changed_rejected(tmp_path):
    """Even if a CI/governance record scopes only governance files, a batch whose
    ACTUAL changed set includes a product file does not qualify."""
    mod, r, fix, z = _ci_valid(tmp_path)
    # add an unrelated product change to the batch's actual changed files
    _commit(r, "tradingagents/other.py", "2026-11-16T16:05:00+00:00")
    _register_commits(r, fix)
    z = _changed(tmp_path, CI_SCOPE + ["tradingagents/other.py"])
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1


@pytest.mark.unit
def test_ci_unknown_implementer_identity_rejected(tmp_path):
    """Commit author cannot be resolved to a trusted login -> CI qualification fails."""
    mod, r, fix, z = _ci_valid(tmp_path)
    # add a commit whose author is not registered in fixtures or implementers.yaml
    _commit(r, CI_SCOPE[0], "2026-11-16T16:10:00+00:00", content="z", msg="more")
    # do NOT register this new commit fixture -> unresolved identity
    assert _run(mod, r, z, fix, batch="pr-40", pr=40) == 1
