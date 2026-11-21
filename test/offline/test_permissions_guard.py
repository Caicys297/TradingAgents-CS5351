"""Focused tests for the workflow-permission guard (WS-C).

Hermetic: temporary Git histories with small workflow YAML files. Proves the
guard's positive path, each prohibited pattern, fail-closed on unparseable YAML,
and range-resolution failure.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_permissions  # noqa: E402

GOOD_WF = """name: CI
on:
  pull_request:
permissions:
  contents: read
  pull-requests: read
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
"""


def _git(repo, *a):
    return subprocess.run(
        ["git", "-C", str(repo), *a], capture_output=True, text=True, check=True
    ).stdout.strip()


def _repo(tmp, wf=GOOD_WF):
    r = tmp / "r"
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / ".github/workflows").mkdir(parents=True)
    (r / ".github/workflows/ci.yml").write_text(wf)
    (r / "docs/ci").mkdir(parents=True)
    (r / "docs/ci/governance-guards.yaml").write_text(
        "permission:\n  protected_paths:\n    - .github/workflows/\n"
    )
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "base")
    subprocess.run(
        ["git", "-C", str(r), "update-ref", "refs/remotes/origin/main",
         _git(r, "rev-parse", "HEAD")],
        check=True,
    )
    return r


def _commit(r, path):
    f = r / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "change")


def _change_wf(r, wf):
    (r / ".github/workflows/ci.yml").write_text(wf)
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "wf change")


def _env(monkeypatch):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    for k in ("GITHUB_BEFORE", "GITHUB_AFTER", "CI_HEAD_SHA"):
        monkeypatch.delenv(k, raising=False)


def _run(monkeypatch, r):
    _env(monkeypatch)
    return check_permissions.main(["--root", str(r)])


@pytest.mark.unit
def test_good_workflow_passes(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _change_wf(r, GOOD_WF + "# trigger\n")
    assert _run(monkeypatch, r) == 0


@pytest.mark.unit
def test_non_applicable_skips(tmp_path, monkeypatch, capsys):
    r = _repo(tmp_path)
    _commit(r, "docs/x.md")
    assert _run(monkeypatch, r) == 0
    assert "skipped" in capsys.readouterr().out


@pytest.mark.unit
def test_pr_reachable_write_scope_blocks(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    bad = GOOD_WF.replace("  contents: read\n", "  contents: write\n")
    _change_wf(r, bad)
    assert _run(monkeypatch, r) == 1


@pytest.mark.unit
def test_write_all_blocks(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    bad = GOOD_WF.replace(
        "permissions:\n  contents: read\n  pull-requests: read\n", "permissions: write-all\n"
    )
    _change_wf(r, bad)
    assert _run(monkeypatch, r) == 1


@pytest.mark.unit
def test_persist_credentials_default_blocks(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    bad = GOOD_WF.replace(
        "        with:\n          persist-credentials: false\n", ""
    )
    _change_wf(r, bad)
    assert _run(monkeypatch, r) == 1


@pytest.mark.unit
def test_restriction_removal_blocks(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    bad = GOOD_WF.replace(
        "permissions:\n  contents: read\n  pull-requests: read\n", ""
    )
    _change_wf(r, bad)
    assert _run(monkeypatch, r) == 1


@pytest.mark.unit
def test_pull_request_target_with_secrets_blocks(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    bad = GOOD_WF.replace("  pull_request:\n", "  pull_request_target:\n").replace(
        "      - uses: actions/checkout@v7",
        "      - run: echo ${{ secrets.X }}\n      - uses: actions/checkout@v7",
    )
    _change_wf(r, bad)
    assert _run(monkeypatch, r) == 1


@pytest.mark.unit
def test_unparseable_yaml_fails_closed(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    _change_wf(r, "on: [pull_request\n  bad: : :")
    assert _run(monkeypatch, r) == 1


@pytest.mark.unit
def test_resolution_error_fails(tmp_path, monkeypatch):
    r = _repo(tmp_path)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_BEFORE", "0" * 40)
    monkeypatch.setenv("GITHUB_AFTER", "0" * 40)
    assert check_permissions.main(["--root", str(r)]) == 1
