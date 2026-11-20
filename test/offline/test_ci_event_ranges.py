"""Focused tests for type/dependency event execution (Correction 3, cases H/I).

Deterministic: uses real temp Git histories and the actual gate scripts'
range-resolution/main() exit codes. No real mypy/pip-audit network scan needed for
the applicability/failure-propagation logic (the scripts short-circuit before a
scan when the range is unresolvable).
"""

from __future__ import annotations

import json
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


@pytest.mark.unit
def test_historical_dep_audit_runs_production_path(tmp_path, monkeypatch):
    """No scanner hook: exercise the REAL production scan path, intercepting only
    the subprocess commands (venv create, install, scan) while GIT creates a real
    historical worktree. Verifies:
      - install runs '. [dev]' with cwd == the historical worktree,
      - scan runs sys.executable -m pip_audit --path <that rev's site-packages>,
      - the worktree HEAD is the requested historical revision,
      - an earlier finding is returned while HEAD would be clean.
    """

    r = tmp_path / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "requirements.txt").write_text(".\n")
    (r / "pyproject.toml").write_text(
        "[project]\nname='x'\ndependencies=['safe-pkg>=1']\n"
        "[project.optional-dependencies]\ndev=['pytest']\n")
    (r / "a.py").write_text("a")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "rev1")
    rev1 = _git(r, "rev-parse", "HEAD")
    subprocess.run(["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", rev1], check=True)

    da = _load("dep_audit")
    calls = {}
    real_run = da.subprocess.run

    class _P:
        def __init__(self, rc=0, out=""):
            self.returncode = rc
            self.stdout = out
            self.stderr = ""

    def fake_run(cmd, *a, **k):
        joined = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "worktree" in joined:  # let git create the real worktree
            return real_run(cmd, *a, **k)
        if "-m" in cmd and "venv" in cmd:
            # create the venv dir + bin/python so path exists
            vpath = Path(cmd[-1])
            (vpath / "bin").mkdir(parents=True, exist_ok=True)
            (vpath / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages").mkdir(
                parents=True, exist_ok=True)
            calls["venv"] = True
            return _P(0)
        if "pip" in cmd and "install" in cmd:
            calls["install_cmd"] = cmd
            calls["install_cwd"] = k.get("cwd")
            # capture the worktree HEAD while it still exists
            calls["install_head"] = real_run(
                ["git", "-C", str(k.get("cwd")), "rev-parse", "HEAD"],
                capture_output=True, text=True).stdout.strip()
            return _P(0)
        if "pip_audit" in joined:
            calls["scan_cmd"] = cmd
            calls["scan_cwd"] = k.get("cwd")
            return _P(0, json.dumps({"dependencies": [{"name": "bad-pkg", "version": "1.0",
                     "vulns": [{"id": "GHSA-bad", "fix_versions": ["2.0"]}]}]}))
        return real_run(cmd, *a, **k)

    monkeypatch.setattr(da.subprocess, "run", fake_run)
    # a revision whose pyproject changes; worktree checkout is real
    (r / "pyproject.toml").write_text(
        "[project]\nname='x'\ndependencies=['bad-pkg>=1']\n"
        "[project.optional-dependencies]\ndev=['pytest']\n")
    (r / "c.py").write_text("c")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "rev2-bad")
    rev2 = _git(r, "rev-parse", "HEAD")

    rep = da._audit_requirements_at_rev(r, rev2)  # NO scanner hook

    # install used '.[dev]' with cwd == the historical worktree
    assert calls["install_cmd"][-1] == ".[dev]"
    assert calls["install_cwd"] and Path(calls["install_cwd"]).name.startswith("deprev-wt-")
    assert calls["install_head"] == rev2  # worktree was the historical revision
    # scan ran via sys.executable -m pip_audit --path <rev site-packages>
    assert calls["scan_cmd"][0] == sys.executable
    assert "pip_audit" in calls["scan_cmd"] and "--path" in calls["scan_cmd"]
    # historical finding returned
    assert rep["dependencies"][0]["name"] == "bad-pkg"

