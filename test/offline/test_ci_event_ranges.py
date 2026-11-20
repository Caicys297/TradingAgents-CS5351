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
