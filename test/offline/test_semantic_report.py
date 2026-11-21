"""Offline tests for the deterministic semantic report runner (scripts/semantic_report.py).

Deterministic: no LLM. Covers the aggregation/threshold logic and the
execution/exit behavior (pytest nonzero, malformed JUnit, missing/skipped cases,
applicability blocking, covered success).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load():
    spec = importlib.util.spec_from_file_location("semantic_report", SCRIPTS / "semantic_report.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _all_pass(mod):
    return {fn: "passed" for (fn, _d, _p) in mod.CASES.values()}


# ---------------------------------------------------------------- evaluate()
@pytest.mark.unit
def test_all_pass_meets_threshold():
    mod = _load()
    rep = mod.evaluate(_all_pass(mod))
    assert rep["threshold_met"] is True and rep["pass_rate"] == 1.0
    assert rep["required_failed"] == []


@pytest.mark.unit
def test_one_failure_blocks():
    mod = _load()
    outcomes = _all_pass(mod)
    first = next(iter(mod.CASES.values()))[0]
    outcomes[first] = "failed"
    assert mod.evaluate(outcomes)["threshold_met"] is False


@pytest.mark.unit
def test_missing_case_blocks():
    mod = _load()
    only = {next(iter(mod.CASES.values()))[0]: "passed"}
    rep = mod.evaluate(only)
    assert rep["threshold_met"] is False
    assert len(rep["required_failed"]) == len(mod.CASES) - 1


@pytest.mark.unit
def test_skipped_counts_as_not_passed():
    mod = _load()
    outcomes = _all_pass(mod)
    outcomes[next(iter(mod.CASES.values()))[0]] = "skipped"
    assert mod.evaluate(outcomes)["threshold_met"] is False


@pytest.mark.unit
def test_six_cases_including_upstream_empty():
    mod = _load()
    assert len(mod.CASES) == 6  # not silently reduced from the approved 6 nodes
    names = {fn for (fn, _d, _p) in mod.CASES.values()}
    assert "test_s3_empty_vendor_pool_is_distinct_from_filtered_pool" in names


# ---------------------------------------------------------------- applicability
@pytest.mark.unit
def test_covered_path_is_not_uncovered():
    mod = _load()
    ch = mod.classify_changes(["tradingagents/dataflows/vendors/yahoo/news.py"])
    assert ch["uncovered_prompt_model"] == []
    assert ch["covered"]


@pytest.mark.unit
def test_prompt_change_without_case_is_uncovered():
    mod = _load()
    ch = mod.classify_changes(["tradingagents/agents/managers/portfolio_manager.py"])
    assert ch["uncovered_prompt_model"] == ["tradingagents/agents/managers/portfolio_manager.py"]


@pytest.mark.unit
def test_unrelated_path_is_not_uncovered():
    mod = _load()
    ch = mod.classify_changes(["README.md", "docs/x.md"])
    assert ch["uncovered_prompt_model"] == []


@pytest.mark.unit
def test_evaluate_blocks_on_uncovered_prompt_model():
    mod = _load()
    rep = mod.evaluate(_all_pass(mod), {"uncovered_prompt_model": ["prompts/foo.yaml"]})
    assert rep["applicability_ok"] is False
    assert rep["threshold_met"] is False


# ---------------------------------------------------------------- execution/exit
def _write_junit(path: Path, cases: dict[str, str]):
    body = "".join(
        f'<testcase classname="c" name="{n}">{ "<failure/>" if o=="failed" else "<skipped/>" if o=="skipped" else "" }</testcase>'
        for n, o in cases.items()
    )
    path.write_text(f'<testsuite tests="{len(cases)}">{body}</testsuite>')


@pytest.mark.unit
def test_main_fails_on_pytest_nonzero(monkeypatch, tmp_path):
    mod = _load()

    def fake_run(junit):
        _write_junit(junit, _all_pass(mod))
        return 1, "pytest failed: boom"  # nonzero

    monkeypatch.setattr(mod, "run_cases", fake_run)
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"tradingagents/dataflows/vendors/yahoo/news.py\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 1


@pytest.mark.unit
def test_main_missing_junit_is_execution_error(monkeypatch, tmp_path):
    mod = _load()
    monkeypatch.setattr(mod, "run_cases", lambda junit: (2, "collection error"))
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"news.py\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 2


@pytest.mark.unit
def test_main_malformed_junit_is_execution_error(monkeypatch, tmp_path):
    mod = _load()

    def fake_run(junit):
        junit.write_text("<testsuite><testcase ")  # malformed
        return 0, ""

    monkeypatch.setattr(mod, "run_cases", fake_run)
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"x\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 2


@pytest.mark.unit
def test_main_required_skipped_produces_failing_exit(monkeypatch, tmp_path):
    mod = _load()
    outcomes = _all_pass(mod)
    outcomes[next(iter(mod.CASES.values()))[0]] = "skipped"

    def fake_run(junit):
        _write_junit(junit, outcomes)
        return 0, ""  # pytest may still exit 0 for skipped-only in some configs

    monkeypatch.setattr(mod, "run_cases", fake_run)
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"news.py\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 1  # skipped required case -> failing main exit


@pytest.mark.unit
def test_main_uncovered_prompt_change_blocks(monkeypatch, tmp_path):
    mod = _load()
    monkeypatch.setattr(mod, "run_cases", lambda junit: (_write_junit(junit, _all_pass(mod)) or 0, ""))
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"tradingagents/agents/analysts/market_analyst.py\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 1


@pytest.mark.unit
def test_main_covered_all_pass_succeeds(monkeypatch, tmp_path):
    mod = _load()
    monkeypatch.setattr(mod, "run_cases", lambda junit: (_write_junit(junit, _all_pass(mod)) or 0, ""))
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"tradingagents/dataflows/macro_news_filter.py\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 0


@pytest.mark.unit
def test_main_duplicate_required_name_is_execution_error(monkeypatch, tmp_path):
    mod = _load()
    fn = next(iter(mod.CASES.values()))[0]

    def fake_run(junit):
        junit.write_text(
            f'<testsuite><testcase name="{fn}"/><testcase name="{fn}"/></testsuite>'
        )
        return 0, ""

    monkeypatch.setattr(mod, "run_cases", fake_run)
    zf = tmp_path / "changed.z"
    zf.write_bytes(b"news.py\x00")
    rc = mod.main(["--json", str(tmp_path / "r.json"), "--changed-from-file", str(zf)])
    assert rc == 2


# ---------------------------------------------------------------- event handling
def _git(repo: Path, *args: str) -> str:
    import subprocess as _sp
    return _sp.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def _init_repo(tmp: Path) -> Path:
    import subprocess as _sp
    repo = tmp / "r"
    _sp.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "base.txt").write_text("b")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-qm", "base")
    return repo


def test_pr_event_uses_merge_base(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    base = _git(repo, "rev-parse", "HEAD")
    # origin/main ref pointing at base
    import subprocess as _sp
    _sp.run(["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", base], check=True)
    (repo / "prompt.py").write_text("x")
    _git(repo, "add", "prompt.py")
    _git(repo, "commit", "-qm", "change prompt")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main"}
    files = mod.resolve_changed_files(changed_from_file=None, base_ref=None, env=env)
    assert "prompt.py" in files


def test_push_event_empty_base_ref_uses_range(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    before = _git(repo, "rev-parse", "HEAD")
    (repo / "z.txt").write_text("z")
    _git(repo, "add", "z.txt")
    _git(repo, "commit", "-qm", "z")
    after = _git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BASE_REF": "", "GITHUB_BEFORE": before, "GITHUB_AFTER": after}
    files = mod.resolve_changed_files(changed_from_file=None, base_ref=None, env=env)
    assert files == ["z.txt"]


def test_push_multicommit_uncovered_prompt_change_detected(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    before = _git(repo, "rev-parse", "HEAD")
    (repo / "tradingagents/agents/analysts").mkdir(parents=True)
    (repo / "tradingagents/agents/analysts/market_analyst.py").write_text("p")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "prompt change")
    (repo / "other.txt").write_text("o")
    _git(repo, "add", "other.txt")
    _git(repo, "commit", "-qm", "second commit")
    after = _git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": before, "GITHUB_AFTER": after}
    files = mod.resolve_changed_files(changed_from_file=None, base_ref=None, env=env)
    ch = mod.classify_changes(files)
    assert "tradingagents/agents/analysts/market_analyst.py" in ch["uncovered_prompt_model"]


def test_push_new_branch_zero_before_fails_closed(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    after = _git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": "0" * 40, "GITHUB_AFTER": after}
    with pytest.raises(mod.ApplicabilityError):
        mod.resolve_changed_files(changed_from_file=None, base_ref=None, env=env)


def test_push_unavailable_history_fails_closed(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    after = _git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": "deadbeef" * 5, "GITHUB_AFTER": after}
    with pytest.raises(mod.ApplicabilityError):
        mod.resolve_changed_files(changed_from_file=None, base_ref=None, env=env)


def test_unknown_event_fails_closed(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    with pytest.raises(mod.ApplicabilityError):
        mod.resolve_changed_files(changed_from_file=None, base_ref=None, env={"GITHUB_EVENT_NAME": "schedule"})


def test_filenames_with_spaces_and_newlines_are_preserved(monkeypatch, tmp_path):
    mod = _load()
    repo = _init_repo(tmp_path)
    before = _git(repo, "rev-parse", "HEAD")
    weird = repo / "weird name\nwith newline.txt"
    weird.write_text("w")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "weird")
    after = _git(repo, "rev-parse", "HEAD")
    monkeypatch.setattr(mod, "REPO_ROOT", repo)
    env = {"GITHUB_EVENT_NAME": "push", "GITHUB_BEFORE": before, "GITHUB_AFTER": after}
    files = mod.resolve_changed_files(changed_from_file=None, base_ref=None, env=env)
    assert files == ["weird name\nwith newline.txt"]
