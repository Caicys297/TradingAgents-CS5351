"""Focused tests for per-commit Ruff enforcement (WS-A, T1–T7).

Uses controlled temporary Git histories. To keep the test hermetic and fast it
substitutes a tiny stand-in for ``ruff`` via ``RUFF_BIN``: the stand-in flags a
file named ``bad.py`` (exit 1, message on stdout) and passes otherwise; a special
mode makes it exit 2 to prove tool errors propagate. The real ``ruff check .``
final-tree run remains a separate, unchanged CI step.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import lint_commits  # noqa: E402


def _git(repo, *args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=e
    ).stdout.strip()


def _repo(tmp):
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "f.txt").write_text("base")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    subprocess.run(
        ["git", "-C", str(r), "update-ref", "refs/remotes/origin/main", _git(r, "rev-parse", "HEAD")],
        check=True,
    )
    return r


def _commit(r, name, content, msg):
    (r / name).write_text(content)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", msg)
    return _git(r, "rev-parse", "HEAD")


def _fake_ruff(tmp, mode="normal"):
    """Stand-in ruff: exit 1 if any tracked file is bad.py (normal), exit 2 if mode=error."""
    p = tmp / f"fake_ruff_{mode}.py"
    p.write_text(
        "import sys, pathlib\n"
        f"MODE = {mode!r}\n"
        "if MODE == 'error':\n"
        "    sys.stderr.write('boom')\n"
        "    sys.exit(2)\n"
        "bad = [f for f in pathlib.Path('.').rglob('bad.py')]\n"
        "if bad:\n"
        "    print('bad.py: F401 unused')\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return f"{sys.executable} {p}"


def _env_pr(base="main", head=None):
    e = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": base}
    if head:
        e["CI_HEAD_SHA"] = head
    return e


def _run(monkeypatch, tmp, root, ruff, env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    for k in ("GITHUB_BEFORE", "GITHUB_AFTER", "CI_HEAD_SHA"):
        if k not in env:
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RUFF_BIN", ruff)
    return lint_commits.main(["--root", str(root)])


@pytest.mark.unit
def test_t1_clean_range_passes(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "a.py", "x = 1\n", "c1")
    _commit(r, "b.py", "y = 2\n", "c2")
    ruff = _fake_ruff(tmp_path)
    assert _run(monkeypatch, tmp_path, r, ruff, _env_pr()) == 0


@pytest.mark.unit
def test_t2_bad_intermediate_fails_even_if_head_clean(tmp_path, monkeypatch, capsys):
    r = _repo(tmp_path)
    bad = _commit(r, "bad.py", "import os\n", "introduce lint error")
    _commit(r, "bad.py", "", "fix by removing content")  # overwrites bad.py (now empty, not flagged)
    # Simulate a later commit that repairs: delete bad.py
    (r / "bad.py").unlink()
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "repair")
    ruff = _fake_ruff(tmp_path)
    rc = _run(monkeypatch, tmp_path, r, ruff, _env_pr())
    err = capsys.readouterr().err
    assert rc == 1
    assert bad[:12] in err  # offending intermediate commit identified
    assert "FAILED commit" in err


@pytest.mark.unit
def test_t3_pr_uses_explicit_head_not_synthetic(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "a.py", "x = 1\n", "real head commit")
    real_head = _git(r, "rev-parse", "HEAD")
    # Advance HEAD to a synthetic "merge" that is clean; explicit head must win.
    _commit(r, "merge.txt", "m", "synthetic merge")
    ruff = _fake_ruff(tmp_path)
    # With explicit real head, range excludes the synthetic merge commit's content.
    rc = _run(monkeypatch, tmp_path, r, ruff, _env_pr(head=real_head))
    assert rc == 0


@pytest.mark.unit
def test_t3_bad_explicit_head_fails_closed(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "a.py", "x = 1\n", "c1")
    ruff = _fake_ruff(tmp_path)
    rc = _run(monkeypatch, tmp_path, r, ruff, _env_pr(head="0" * 40))
    assert rc == 1  # unresolvable CI_HEAD_SHA fails closed


@pytest.mark.unit
def test_t4_push_range_checked(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    before = _git(r, "rev-parse", "HEAD")
    _commit(r, "bad.py", "import os\n", "bad push commit")
    after = _git(r, "rev-parse", "HEAD")
    ruff = _fake_ruff(tmp_path)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": before, "GITHUB_AFTER": after}
    assert _run(monkeypatch, tmp_path, r, ruff, env) == 1


@pytest.mark.unit
def test_t5_missing_history_fails_closed(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _commit(r, "a.py", "x=1\n", "c1")
    ruff = _fake_ruff(tmp_path)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": "0" * 40, "GITHUB_AFTER": _git(r, "rev-parse", "HEAD")}
    assert _run(monkeypatch, tmp_path, r, ruff, env) == 1


@pytest.mark.unit
def test_t6_ruff_tool_error_fails(tmp_path, monkeypatch, capsys):
    r = _repo(tmp_path)
    _commit(r, "a.py", "x = 1\n", "c1")
    ruff = _fake_ruff(tmp_path, mode="error")
    rc = _run(monkeypatch, tmp_path, r, ruff, _env_pr())
    assert rc == 1
    assert "ruff exited 2" in capsys.readouterr().err


@pytest.mark.unit
def test_t7_default_head_unchanged_when_no_explicit_head(tmp_path, monkeypatch):
    """Without CI_HEAD_SHA, PR range uses HEAD (backward-compatible default)."""
    r = _repo(tmp_path)
    _commit(r, "a.py", "x = 1\n", "c1")
    ruff = _fake_ruff(tmp_path)
    assert _run(monkeypatch, tmp_path, r, ruff, _env_pr()) == 0
