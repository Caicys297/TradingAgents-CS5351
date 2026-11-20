"""Offline tests for the pre-code Test Approval Gate checker.

Deterministic: fixture-backed GitHub API + genuine temporary Git histories.
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


def _git(repo: Path, *args: str, env: dict | None = None):
    import os
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=e).stdout.strip()


def _repo(tmp: Path) -> Path:
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "base.txt").write_text("b")
    _git(r, "add", "base.txt")
    _git(r, "commit", "-qm", "base")
    base = _git(r, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", base], check=True)
    return r


def _commit(r: Path, rel: str, when: str, msg: str = "impl") -> str:
    f = r / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x")
    _git(r, "add", "-A")
    env = {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    _git(r, "commit", "-qm", msg, env=env)
    return _git(r, "rev-parse", "HEAD")


def _write_comment(fix: Path, cid: int, author: str, at: str):
    d = fix / "comments"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{cid}.json").write_text(json.dumps({"user": {"login": author}, "created_at": at, "body": "Approved"}))


def _record(root: Path, **kw):
    d = root / "docs/test-approvals"
    d.mkdir(parents=True, exist_ok=True)
    base = {
        "feature": "O2", "approval_kind": "test_plan",
        "evidence": {"type": "issue_comment", "id": 6920115438,
                     "reviewer_role": "A", "author": "Caicys297"},
        "plan_sha": "b0287da", "plan_version": "v0.3/v0.1",
        "requirement_ids": ["O2-FR-01"], "approved_test_ids": ["O2-TC-01"],
        "allowed_files": ["tradingagents/repro/manifest.py"],
        "approval_time": "2026-11-16T15:02:47+00:00",
    }
    base.update(kw)
    (d / "o2.json").write_text(json.dumps(base))


def _changed(tmp: Path, paths: list[str]) -> Path:
    z = tmp / "changed.z"
    z.write_bytes(b"".join(p.encode() + b"\x00" for p in paths))
    return z


def _run(mod, root, changed_z, fixture, pr=None):
    return mod.main(["--changed-from-file", str(changed_z), "--root", str(root),
                     "--pr", str(pr) if pr else "0", "--api-fixture-dir", str(fixture),
                     "--base-ref", "main"])


# ---------------------------------------------------------------- not applicable
@pytest.mark.unit
def test_docs_only_not_applicable(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    fix.mkdir()
    z = _changed(tmp_path, ["docs/readme.md", "transcripts/x.md"])
    assert _run(mod, r, z, fix) == 0


# ---------------------------------------------------------------- positive
@pytest.mark.unit
def test_valid_precode_approval_passes(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")  # after approval
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 0


# ---------------------------------------------------------------- negatives
@pytest.mark.unit
def test_missing_record_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    fix = tmp_path / "fix"
    fix.mkdir()
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_late_approval_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T14:00:00+00:00")  # BEFORE approval
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_self_approval_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r, implementer="A")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_unauthorized_reviewer_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r, evidence={"type": "issue_comment", "id": 6920115438,
                         "reviewer_role": "D", "author": "Caicys297"})  # O2 must be A
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_scope_version_mismatch_missing_field_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r, plan_version="")
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_approval_time_backdating_mismatch_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r, approval_time="2026-11-16T10:00:00+00:00")  # claims earlier than real
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_api_failure_fails_not_green(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    fix.mkdir()  # empty: evidence unverifiable
    _record(r)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    # unverifiable evidence -> failure, not green (exit 1 for unverifiable per policy)
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_incomplete_history_fails(tmp_path):
    mod = _load()
    r = _repo(tmp_path)
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    # bad base ref -> execution error (exit 2)
    rc = mod.main(["--changed-from-file", str(z), "--root", str(r), "--pr", "0",
                   "--api-fixture-dir", str(fix), "--base-ref", "doesnotexist"])
    assert rc == 2


# ---------------------------------------------------------------- provenance
@pytest.mark.unit
def test_cherry_picked_preserves_author_date(tmp_path):
    """A cherry-pick keeps the original author date; approval before it stays valid."""
    mod = _load()
    r = _repo(tmp_path)
    # Original impl commit authored BEFORE approval, then approval, then cherry-pick forward
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T12:00:00+00:00", "orig")
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _record(r)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    # author date 12:00 < approval 15:02 -> late approval -> fail
    assert _run(mod, r, z, fix) == 1


@pytest.mark.unit
def test_in_scope_followup_covered_by_existing_approval(tmp_path):
    """A small in-scope follow-up (after approval) reuses the approval -> passes."""
    mod = _load()
    r = _repo(tmp_path)
    # Only a doc-plan commit before impl; approval precedes impl.
    fix = tmp_path / "fix"
    _write_comment(fix, 6920115438, "Caicys297", "2026-11-16T15:02:47Z")
    _commit(r, "tradingagents/repro/manifest.py", "2026-11-16T16:00:00+00:00")
    # follow-up: a different in-scope CHANGE (new file content) after approval
    (r / "tradingagents/repro/manifest.py").write_text("y")
    _git(r, "add", "-A")
    env = {"GIT_AUTHOR_DATE": "2026-11-16T16:10:00+00:00", "GIT_COMMITTER_DATE": "2026-11-16T16:10:00+00:00"}
    _git(r, "commit", "-qm", "followup", env=env)
    _record(r)
    z = _changed(tmp_path, ["tradingagents/repro/manifest.py"])
    assert _run(mod, r, z, fix) == 0
