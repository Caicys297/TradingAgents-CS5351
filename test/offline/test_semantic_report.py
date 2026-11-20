"""Offline tests for the deterministic semantic report runner (scripts/semantic_report.py).

These test the aggregation/threshold logic deterministically (no LLM). Real
execution is exercised separately in CI via the workflow job.
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


@pytest.mark.unit
def test_all_pass_meets_threshold():
    mod = _load()
    rep = mod.evaluate(_all_pass(mod))
    assert rep["threshold_met"] is True
    assert rep["pass_rate"] == 1.0
    assert rep["required_failed"] == []


@pytest.mark.unit
def test_one_failure_blocks():
    mod = _load()
    outcomes = _all_pass(mod)
    first_fn = next(iter(mod.CASES.values()))[0]
    outcomes[first_fn] = "failed"
    rep = mod.evaluate(outcomes)
    assert rep["threshold_met"] is False
    assert rep["required_failed"]


@pytest.mark.unit
def test_missing_case_blocks():
    mod = _load()
    only_one = {next(iter(mod.CASES.values()))[0]: "passed"}
    rep = mod.evaluate(only_one)
    assert rep["threshold_met"] is False
    assert len(rep["required_failed"]) == len(mod.CASES) - 1


@pytest.mark.unit
def test_skipped_counts_as_not_passed():
    mod = _load()
    outcomes = _all_pass(mod)
    first_fn = next(iter(mod.CASES.values()))[0]
    outcomes[first_fn] = "skipped"
    assert mod.evaluate(outcomes)["threshold_met"] is False


@pytest.mark.unit
def test_report_declares_uncovered_paths():
    mod = _load()
    rep = mod.evaluate(_all_pass(mod))
    assert rep["uncovered_changes"]  # must explicitly list uncovered prompt/model paths
    assert rep["caseset_version"] == "o5-deterministic-v1"
