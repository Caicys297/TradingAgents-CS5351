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


def _comment(fix, cid, author, at, body="Approved", updated_at=None):
    d = fix / "comments"
    d.mkdir(parents=True, exist_ok=True)
    rec = {"user": {"login": author}, "created_at": at, "body": body}
    if updated_at:
        rec["updated_at"] = updated_at
    (d / f"{cid}.json").write_text(json.dumps(rec))


def _marker(kind="test_plan", plan=FULL_SHA, ver="v0.3", scope="tradingagents/repro/manifest.py"):
    return f"TEST-APPROVAL: plan={plan} version={ver} kind={kind} scope={scope}"


def _markers_both(plan=FULL_SHA, ver="v0.3", scope="tradingagents/repro/manifest.py"):
    return _marker("test_plan", plan, ver, scope) + "\n" + _marker("execution_plan", plan, ver, scope)


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
    _comment(fix, 777, "Caicys297", "2026-11-16T15:30:00Z", body=_marker("test_plan"))
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
    _comment(fix, 999, "Caicys297", "2026-11-16T15:30:00Z", body=_marker("test_plan"))
    _record(r, "o2_test.json", feature="O2", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111},
            plan_sha=FULL_SHA, plan_version="v0.3",
            allowed_files=["tradingagents/repro/manifest.py"], implementers=["fancx777"],
            clarification={"evidence": {"type": "issue_comment", "id": 999},
                           "original_evidence_id": 888,  # WRONG original (record evidence is 111)
                           "plan_sha": FULL_SHA, "plan_version": "v0.3"})
    # the clarification evidence (999) marker exists, but it must bind the SAME
    # original artifact; the record asserts original_evidence_id=111 while evidence
    # is 999 -> mismatch must be rejected
    assert _run(mod, r, z, fix) == 1
