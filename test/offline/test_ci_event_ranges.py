"""Focused tests for type/dependency event execution (Correction 3, cases H/I).

Deterministic: uses real temp Git histories and the actual gate scripts'
range-resolution/main() exit codes. No real mypy/pip-audit network scan needed for
the applicability/failure-propagation logic (the scripts short-circuit before a
scan when the range is unresolvable).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import ci_event  # noqa: E402


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
    (r / "f.txt").write_text("b")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", _git(r, "rev-parse", "HEAD")], check=True)
    return r


@pytest.mark.unit
def test_pr_range_uses_merge_base(tmp_path):
    r = _repo(tmp_path)
    (r / "g.txt").write_text("x")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "impl")
    rng = ci_event.resolve_range(r, {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main"})
    assert rng.kind == "pull_request"
    assert rng.commits  # at least the impl commit
    assert rng.base_sha == _git(r, "rev-parse", "origin/main")


@pytest.mark.unit
def test_push_range_uses_before_after(tmp_path):
    r = _repo(tmp_path)
    before = _git(r, "rev-parse", "HEAD")
    (r / "g.txt").write_text("x")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "one")
    (r / "h.txt").write_text("y")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "two")
    after = _git(r, "rev-parse", "HEAD")
    rng = ci_event.resolve_range(r, {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": before, "GITHUB_AFTER": after})
    assert rng.kind == "push"
    assert len(rng.commits) == 2  # multi-commit push covered


@pytest.mark.unit
def test_push_zero_before_fails_closed(tmp_path):
    r = _repo(tmp_path)
    with pytest.raises(ci_event.EventError):
        ci_event.resolve_range(r, {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": "0" * 40, "GITHUB_AFTER": "HEAD"})


@pytest.mark.unit
def test_push_unavailable_before_fails_closed(tmp_path):
    r = _repo(tmp_path)
    after = _git(r, "rev-parse", "HEAD")
    with pytest.raises(ci_event.EventError):
        ci_event.resolve_range(r, {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": "deadbeef" * 5, "GITHUB_AFTER": after})


@pytest.mark.unit
def test_unknown_event_fails_closed(tmp_path):
    r = _repo(tmp_path)
    with pytest.raises(ci_event.EventError):
        ci_event.resolve_range(r, {"GITHUB_EVENT_NAME": "schedule"})


@pytest.mark.unit
def test_typecheck_push_zero_base_exit2(tmp_path):
    """Actual script: push with zero base -> exit 2 (not success)."""
    r = _repo(tmp_path)
    rc = subprocess.run(
        [sys.executable, str(SCRIPTS / "typecheck.py"), "--event", "push",
         "--before", "0" * 40, "--after", "HEAD"],
        capture_output=True, text=True, cwd=r,
    ).returncode
    assert rc == 2


@pytest.mark.unit
def test_dep_audit_push_zero_base_exit2(tmp_path):
    r = _repo(tmp_path)
    rc = subprocess.run(
        [sys.executable, str(SCRIPTS / "dep_audit.py"), "--event", "push",
         "--before", "0" * 40, "--after", "HEAD"],
        capture_output=True, text=True, cwd=r,
    ).returncode
    assert rc == 2


# ============================================================ Phase-2 findings 2 & 3
def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


class _FakeRange:
    def __init__(self, commits):
        self.kind = "pull_request"
        self.base_sha = "base"
        self.head_sha = "head"
        self.commits = commits


@pytest.mark.unit
def test_typecheck_tool_error_fails(monkeypatch):
    """mypy nonzero exit with no usable diagnostics must fail (not clean)."""
    tc = _load("typecheck")
    monkeypatch.setattr(tc.ci_event, "resolve_range", lambda root, env: _FakeRange(["c1"]))
    monkeypatch.setattr(tc, "load_baseline", lambda sha: (tc.Counter(), "test"))
    monkeypatch.setattr(tc, "run_mypy", lambda: [])  # HEAD clean
    monkeypatch.setattr(tc, "_mypy_at_rev", lambda rev: ([], 2, "internal mypy error"))
    assert tc.main([]) == 1


@pytest.mark.unit
def test_typecheck_intermediate_commit_new_diag_fails_head_clean(monkeypatch):
    tc = _load("typecheck")
    diag = ["cli/run.py: note: In function \"f\":",
            "cli/run.py:1: error: NEW  [return-value]"]
    monkeypatch.setattr(tc.ci_event, "resolve_range", lambda root, env: _FakeRange(["c1", "c2"]))
    monkeypatch.setattr(tc, "load_baseline", lambda sha: (tc.Counter(), "test"))
    monkeypatch.setattr(tc, "run_mypy", lambda: [])  # HEAD clean
    # commit c1 introduces a new diagnostic (rc=1), c2 clean
    monkeypatch.setattr(tc, "_mypy_at_rev", lambda rev: (diag, 1, "") if rev == "c1" else ([], 0, ""))
    assert tc.main([]) == 1


@pytest.mark.unit
def test_dep_intermediate_commit_new_finding_fails_head_clean(monkeypatch):
    da = _load("dep_audit")
    head_report = {"dependencies": [{"name": "ok", "version": "1", "vulns": []}]}
    commit_report = {"dependencies": [{"name": "foo", "version": "1.0",
                                       "vulns": [{"id": "GHSA-x", "fix_versions": ["1.2"]}]}]}
    monkeypatch.setattr(da.ci_event, "resolve_range", lambda root, env: _FakeRange(["c1", "c2"]))
    monkeypatch.setattr(da, "run_pip_audit", lambda: head_report)  # HEAD clean
    monkeypatch.setattr(da, "_load_baseline", lambda sha: ({"findings": []}, "test"))
    monkeypatch.setattr(da, "_depfiles_changed_per_commit", lambda root, commits: ["c1"])
    monkeypatch.setattr(da, "_audit_requirements_at_rev", lambda root, rev: commit_report)
    assert da.main([]) == 1


@pytest.mark.unit
def test_dep_scanner_failure_on_commit_is_not_clean(monkeypatch):
    da = _load("dep_audit")
    monkeypatch.setattr(da.ci_event, "resolve_range", lambda root, env: _FakeRange(["c1"]))
    monkeypatch.setattr(da, "run_pip_audit", lambda: {"dependencies": []})
    monkeypatch.setattr(da, "_load_baseline", lambda sha: ({"findings": []}, "test"))
    monkeypatch.setattr(da, "_depfiles_changed_per_commit", lambda root, commits: ["c1"])

    def boom(root, rev):
        raise da.ScannerError("resolver unavailable")

    monkeypatch.setattr(da, "_audit_requirements_at_rev", boom)
    assert da.main([]) == 2  # not clean
