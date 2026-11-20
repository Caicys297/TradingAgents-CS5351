"""Offline tests for the hardened pre-code Test Approval Gate checker.

Deterministic: fixture GitHub API + the trusted reviewers mapping + real temp Git
histories. Exercises actual main() exit behavior for each bypass.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


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


def _repo(tmp):
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "base.txt").write_text("b")
    _git(r, "add", "base.txt")
    _git(r, "commit", "-qm", "base")
    base = _git(r, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", base], check=True)
    # trusted reviewers mapping + records dir
    (r / "docs/test-approvals").mkdir(parents=True, exist_ok=True)
    (r / "docs/test-approvals/reviewers.yaml").write_text("logins:\n  Caicys297: A\n  fancx777: F\n")
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
    base = {
        "batch_id": "batch-1", "feature": "O2",
        "approval_kinds": ["test_plan", "execution_plan"],
        "evidence": {"type": "issue_comment", "id": 111},
        "plan_sha": "b0287da", "plan_version": "v0.3",
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


def _valid_setup(tmp):
    mod = _load()
    r = _repo(tmp)
    fix = tmp / "fix"
    # impl after approval; body references plan sha+version
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z",
             body="Approved plan b0287da v0.3 for implementation")
    # A approves both test_plan (O2 needs A) and execution_plan (A) in one record
    _record(r, "o2.json")
    z = _changed(tmp, ["tradingagents/repro/manifest.py"])
    return mod, r, fix, z


# ------------------------------------------------------------ positive
@pytest.mark.unit
def test_valid_batch_passes(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    assert _run(mod, r, z, fix) == 0


# ------------------------------------------------------------ trusted identity
@pytest.mark.unit
def test_impostor_login_claiming_role_A_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    # Evidence author is fancx777 (F) but claims to approve O2 test plan (needs A)
    _comment(fix, 111, "fancx777", "2026-11-16T15:02:47Z", body="Approved b0287da v0.3")
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_unauthorized_login_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    _comment(fix, 111, "randomuser", "2026-11-16T15:02:47Z", body="Approved b0287da v0.3")
    assert _run(mod, r, z, fix) == 1


# ------------------------------------------------------------ batch binding
@pytest.mark.unit
def test_unrelated_old_approval_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    # record bound to a DIFFERENT batch -> not found for batch-1
    _record(r, "o2.json", batch_id="other-batch")
    assert _run(mod, r, z, fix, batch="batch-1") == 1


@pytest.mark.unit
def test_file_outside_scope_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    _commit(r, "tradingagents/other.py", "2026-11-16T16:00:00+00:00")  # outside allowed
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py", "tradingagents/other.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_file_inside_exclusion_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    _record(r, "o2.json", excluded_files=["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


# ------------------------------------------------------------ meaning/immutable
@pytest.mark.unit
def test_plan_sha_mismatch_in_body_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body="Approved some other plan")
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_late_approval_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T14:00:00+00:00")  # before approval
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body="Approved b0287da v0.3")
    _record(r, "o2.json")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_self_approval_via_evidence_author_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    _record(r, "o2.json", implementers=["Caicys297"])  # approver is implementer
    assert _run(mod, r, z, fix) == 1


# ------------------------------------------------------------ both kinds
@pytest.mark.unit
def test_only_test_plan_kind_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    _record(r, "o2.json", approval_kinds=["test_plan"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_later_code_review_not_precode(tmp_path):
    """A review APPROVED on a *later* PR (post-impl) is not pre-code approval."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    # review submitted AFTER impl
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T14:00:00+00:00")
    rv = fix / "reviews"
    rv.mkdir(parents=True, exist_ok=True)
    (rv / "7-222.json").write_text(json.dumps({"user": {"login": "Caicys297"},
                                               "submitted_at": "2026-11-16T16:00:00Z",
                                               "state": "APPROVED", "body": "Approved b0287da v0.3"}))
    _record(r, "o2.json", evidence={"type": "review", "id": 222})
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix, pr=7) == 1  # late (after impl)


# ------------------------------------------------------------ delegation
@pytest.mark.unit
def test_valid_delegation_A_to_F_for_o2(tmp_path):
    """A authorizes F to approve the O2 test plan for this batch/scope."""
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    # A delegation comment references plan; F approves test plan; A approves exec
    _comment(fix, 900, "Caicys297", "2026-11-16T14:00:00Z", body="Authorize F to approve aa9fda60")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z", body="Approved aa9fda60 v0.4")
    _record(r, "deleg.json", batch_id="batch-1", feature="O2", implementers=["D"], delegation={
        "batch_id": "batch-1", "kind": "test_plan", "to_role": "F", "plan_sha": "aa9fda60"},
        evidence={"type": "issue_comment", "id": 900}, plan_sha="aa9fda60", plan_version="v0.4")
    _record(r, "o2test.json", batch_id="batch-1", feature="O2", approval_kinds=["test_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 111}, plan_sha="aa9fda60", plan_version="v0.4")
    # execution plan by A
    _comment(fix, 112, "Caicys297", "2026-11-16T15:10:00Z", body="Approved exec aa9fda60 v0.4")
    _record(r, "exe.json", batch_id="batch-1", feature="O2", approval_kinds=["execution_plan"], implementers=["D"],
            evidence={"type": "issue_comment", "id": 112}, plan_sha="aa9fda60", plan_version="v0.4")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 0


@pytest.mark.unit
def test_missing_delegation_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    _comment(fix, 111, "fancx777", "2026-11-16T15:00:00Z", body="Approved b0287da v0.3")
    _record(r, "o2test.json", approval_kinds=["test_plan"],
            evidence={"type": "issue_comment", "id": 111})
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1  # F approving O2 test plan without delegation


# ------------------------------------------------------------ history
@pytest.mark.unit
def test_incomplete_history_fails(tmp_path):
    mod, r, fix, z = _valid_setup(tmp_path)
    rc = mod.main(["--changed-from-file", str(z), "--batch", "batch-1", "--root", str(r),
                   "--pr", "0", "--api-fixture-dir", str(fix), "--base-ref", "doesnotexist"])
    assert rc == 2


@pytest.mark.unit
def test_docs_only_not_applicable(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    fix.mkdir()
    z = _changed(tmp_path, ["docs/x.md", "transcripts/y.md"])
    assert _run(mod, r, z, fix) == 0


# ------------------------------------------------------------ cherry-pick provenance
@pytest.mark.unit
def test_cherry_pick_preserves_author_date_late(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T12:00:00+00:00", msg="orig")
    _comment(fix, 111, "Caicys297", "2026-11-16T15:02:47Z", body="Approved b0287da v0.3")
    _record(r, "o2.json")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1  # 12:00 < approval -> late
