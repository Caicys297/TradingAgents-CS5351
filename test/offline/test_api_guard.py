"""Focused tests for the API governance guard (WS-C).

Hermetic: temporary Git histories + the real guard's decision logic. Applicability
and failure propagation are proven by pointing the guard's config at (a) a passing
and (b) a deliberately failing temporary pytest node, so the guard's own subprocess
invocation is exercised end to end without running the full O2/O4 suites.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_api  # noqa: E402


def _git(repo, *a):
    return subprocess.run(
        ["git", "-C", str(repo), *a], capture_output=True, text=True, check=True
    ).stdout.strip()


def _repo(tmp, node, nodepath_rel, nodepath_src):
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "docs/ci").mkdir(parents=True)
    (r / "docs/ci/governance-guards.yaml").write_text(
        "api:\n  protected_paths:\n    - cli/run.py\n  nodes:\n    - " + node + "\n"
    )
    np = r / nodepath_rel
    np.parent.mkdir(parents=True, exist_ok=True)
    np.write_text(nodepath_src)
    (r / "base.txt").write_text("b")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    subprocess.run(
        ["git", "-C", str(r), "update-ref", "refs/remotes/origin/main",
         _git(r, "rev-parse", "HEAD")],
        check=True,
    )
    return r


def _commit(r, path, msg="c"):
    f = r / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", msg)


def _env(monkeypatch, **e):
    for k, v in {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main", **e}.items():
        monkeypatch.setenv(k, v)
    for k in ("GITHUB_BEFORE", "GITHUB_AFTER", "CI_HEAD_SHA"):
        if k not in e:
            monkeypatch.delenv(k, raising=False)


@pytest.mark.unit
def test_non_applicable_skips(tmp_path, monkeypatch, capsys):
    r = _repo(tmp_path, "tmp_node.py::test_ok", "tmp_node.py", "def test_ok():\n    assert True\n")
    _commit(r, "docs/readme.md", "docs only")
    _env(monkeypatch)
    assert check_api.main(["--root", str(r)]) == 0
    assert "skipped" in capsys.readouterr().out


@pytest.mark.unit
def test_protected_change_passing_node_ok(tmp_path, monkeypatch):
    r = _repo(tmp_path, "tmp_node.py::test_ok", "tmp_node.py", "def test_ok():\n    assert True\n")
    _commit(r, "cli/run.py", "touch protected")
    _env(monkeypatch)
    assert check_api.main(["--root", str(r)]) == 0


@pytest.mark.unit
def test_protected_change_failing_node_blocks(tmp_path, monkeypatch):
    r = _repo(tmp_path, "tmp_node.py::test_bad", "tmp_node.py", "def test_bad():\n    assert False\n")
    _commit(r, "cli/run.py", "touch protected")
    _env(monkeypatch)
    assert check_api.main(["--root", str(r)]) == 1


@pytest.mark.unit
def test_resolution_error_fails(tmp_path, monkeypatch):
    r = _repo(tmp_path, "tmp_node.py::test_ok", "tmp_node.py", "def test_ok():\n    assert True\n")
    _env(monkeypatch, GITHUB_EVENT_NAME="push", GITHUB_BEFORE="0" * 40, GITHUB_AFTER="0" * 40)
    assert check_api.main(["--root", str(r)]) == 1
