"""O5 S6 T17 offline performance and correctness test.

Implements the approved S6 plan (docs/req/reviews/o5/s6-t17, v0.2):

* verifies the SHA-256 of **both** the fixed fixture and the frozen oracle
  against the manifest, plus the count/k/topics/window/rules invariants,
  before any warmup;
* runs 5 warmups (timings discarded, results and exceptions still gated) and
  30 measured calls, timing **only** the ``select_macro_news`` call;
* fails on any incorrect or exceptional warmup or measured call;
* keeps all 30 measured timings and applies nearest-rank p95.

The ``<= 100 ms`` threshold and the platform/interpreter check apply **only**
when ``O5_T17_ENFORCE_THRESHOLD`` is set (the dedicated ubuntu-latest/Python
3.11 CI job). On every other interpreter or host the harness still checks
correctness and reports timings, but a p95 above 100 ms is informational.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

from tradingagents.dataflows import macro_news_filter as o5

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "o5"
FIXTURE_PATH = FIXTURE_DIR / "O5-T17-Perf-Fixture-1000-v1.json"
EXPECTED_PATH = FIXTURE_DIR / "O5-T17-Expected-Results-v1.json"
MANIFEST_PATH = FIXTURE_DIR / "O5-T17-Manifest-v1.json"
BUILDER_PATH = FIXTURE_DIR / "build_o5_t17_fixture.py"

RECORD_COUNT = 1000
K = 30
WARMUPS = 5
MEASURED = 30
THRESHOLD_MS = 100.0
ENFORCE_ENV = "O5_T17_ENFORCE_THRESHOLD"

COUNT_KEYS = (
    "input_count",
    "selected_count",
    "not_selected_limit_count",
    "irrelevant_count",
    "invalid_count",
    "out_of_window_count",
    "duplicate_count",
    "skipped_zero_limit_count",
)

pytestmark = pytest.mark.unit


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load() -> tuple[dict, dict, dict]:
    return (
        json.loads(FIXTURE_PATH.read_text(encoding="utf-8")),
        json.loads(EXPECTED_PATH.read_text(encoding="utf-8")),
        json.loads(MANIFEST_PATH.read_text(encoding="utf-8")),
    )


def _o5_window(expected: dict) -> tuple[datetime, datetime]:
    return (
        datetime.fromisoformat(expected["request"]["start_at"].replace("Z", "+00:00")),
        datetime.fromisoformat(expected["request"]["end_at"].replace("Z", "+00:00")),
    )


def _candidates(fixture: dict) -> list[o5.MacroNewsCandidate]:
    out = []
    for record in fixture["candidates"]:
        out.append(
            o5.MacroNewsCandidate(
                candidate_id=record["candidate_id"],
                title=record["title"],
                summary=record["summary"],
                published_at=datetime.fromisoformat(
                    record["published_at"].replace("Z", "+00:00")
                ),
                source=record["source"],
                url=record["url"],
            )
        )
    return out


def _request(expected: dict) -> o5.MacroNewsRequest:
    start, end = _o5_window(expected)
    return o5.MacroNewsRequest(
        topics=tuple(expected["request"]["topics"]),
        start_at=start,
        end_at=end,
        limit=expected["request"]["limit"],
    )


def _mismatch(result, expected: dict) -> str | None:
    """Return a short description of the first disagreement, or None."""

    if result.status != expected["status"]:
        return f"status {result.status!r} != {expected['status']!r}"
    counts = result.counts()
    for key in COUNT_KEYS:
        if counts[key] != expected["counts"][key]:
            return f"counts[{key}] {counts[key]} != {expected['counts'][key]}"
    got_ids = [item.candidate_id for item in result.selected]
    if got_ids != expected["selected_ids"]:
        for index, (got, want) in enumerate(zip(got_ids, expected["selected_ids"], strict=False)):
            if got != want:
                return f"selected_ids[{index}] {got!r} != {want!r}"
        return f"selected_ids length {len(got_ids)} != {len(expected['selected_ids'])}"
    per_topic = dict.fromkeys(expected["selected_per_topic"], 0)
    for item in result.selected:
        per_topic[item.primary_topic] += 1
    if per_topic != expected["selected_per_topic"]:
        return f"per_topic {per_topic} != {expected['selected_per_topic']}"
    return None


# ------------------------------------------------------------- integrity checks


def test_both_hashes_match_manifest_before_any_warmup():
    """Both fixture and expected SHA-256, plus the fixed invariants (§3a)."""

    _, _, manifest = _load()

    fixture_sha = _sha256(FIXTURE_PATH)
    expected_sha = _sha256(EXPECTED_PATH)
    assert fixture_sha == manifest["fixture_sha256"], "fixture hash drift"
    assert expected_sha == manifest["expected_sha256"], "expected hash drift"

    fixture, expected, _ = _load()
    assert manifest["record_count"] == RECORD_COUNT
    assert manifest["k"] == K
    assert len(fixture["candidates"]) == RECORD_COUNT
    assert fixture["unique_ids"] == 980
    assert expected["request"]["limit"] == K
    assert manifest["request_topics"] == expected["request"]["topics"]
    assert manifest["request_window"] == [
        expected["request"]["start_at"],
        expected["request"]["end_at"],
    ]
    assert manifest["rules_version"] == expected["rules_version"] == o5.RULES_VERSION


def test_fixture_group_and_id_contract():
    """980 unique ids, 20 duplicate occurrences, F6 the only recipe deviation."""

    fixture, expected, _ = _load()
    records = fixture["candidates"]
    assert len(records) == 1000
    assert len({record["candidate_id"] for record in records}) == 980
    assert fixture["group_counts"] == {
        "F1": 280, "F2": 260, "F3": 260, "F4": 120, "F5": 60, "F6": 20,
    }
    f1_ids = {
        record["candidate_id"]
        for record in records
        if record["fixture_group"] == "F1"
    }
    f6_ids = {
        record["candidate_id"]
        for record in records
        if record["fixture_group"] == "F6"
    }
    assert f6_ids <= f1_ids and len(f6_ids) == 20
    # The oracle conserves and matches the approved counts.
    counts = expected["counts"]
    assert counts["input_count"] == 1000
    assert counts["selected_count"] == 30
    assert counts["not_selected_limit_count"] == 890
    assert counts["irrelevant_count"] == 60
    assert counts["duplicate_count"] == 20
    assert (
        counts["selected_count"] + counts["not_selected_limit_count"]
        + counts["irrelevant_count"] + counts["invalid_count"]
        + counts["out_of_window_count"] + counts["duplicate_count"]
        + counts["skipped_zero_limit_count"]
    ) == counts["input_count"]


def test_expected_file_is_not_generated_by_the_selector():
    """The oracle builder must not import or call the selector under test."""

    import ast

    tree = ast.parse(BUILDER_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any("macro_news_filter" in name for name in imported), imported

    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)
    assert "select_macro_news" not in called


# --------------------------------------------------------- warmups and measure


def _run_t17() -> dict:
    fixture, expected, manifest = _load()
    assert _sha256(FIXTURE_PATH) == manifest["fixture_sha256"]
    assert _sha256(EXPECTED_PATH) == manifest["expected_sha256"]

    candidates = _candidates(fixture)
    request = _request(expected)

    for index in range(WARMUPS):
        try:
            result = o5.select_macro_news(candidates, request)
        except Exception as exc:  # noqa: BLE001 - a warmup failure fails T17
            pytest.fail(f"warmup[{index}] raised {type(exc).__name__}: {exc}")
        problem = _mismatch(result, expected)
        if problem is not None:
            pytest.fail(f"warmup[{index}] incorrect: {problem}")

    timings: list[float] = []
    for index in range(MEASURED):
        try:
            started = time.perf_counter_ns()
            result = o5.select_macro_news(candidates, request)
            elapsed = time.perf_counter_ns() - started
        except Exception as exc:  # noqa: BLE001 - a measured failure fails T17
            pytest.fail(f"measured[{index}] raised {type(exc).__name__}: {exc}")
        problem = _mismatch(result, expected)
        if problem is not None:
            pytest.fail(f"measured[{index}] incorrect: {problem}")
        timings.append(elapsed / 1_000_000.0)

    ordered = sorted(timings)
    p95 = ordered[28]  # nearest-rank: ceil(0.95 * 30) = 29 -> 29th smallest
    return {
        "runner": f"{platform.platform()} / CPython {platform.python_version()}",
        "fixture_sha256": manifest["fixture_sha256"],
        "expected_sha256": manifest["expected_sha256"],
        "implementation_main_sha": manifest["implementation_main_sha"],
        "warmups": WARMUPS,
        "measured": MEASURED,
        "correctness": f"{WARMUPS}/{WARMUPS} warmups + {MEASURED}/{MEASURED} measured",
        "min_ms": ordered[0],
        "median_ms": (ordered[14] + ordered[15]) / 2.0,
        "p95_ms": p95,
        "max_ms": ordered[-1],
        "raw_ms": timings,
        "enforced": os.environ.get(ENFORCE_ENV) == "1",
    }


def _report(report: dict) -> str:
    raw = ", ".join(f"{value:.3f}" for value in report["raw_ms"])
    return "\n".join(
        (
            f"runner        : {report['runner']}",
            f"main_sha      : {report['implementation_main_sha']}",
            f"fixture       : sha256={report['fixture_sha256']} verified=true",
            f"expected      : sha256={report['expected_sha256']} verified=true",
            f"samples       : {report['warmups']} warmups (discarded) + {report['measured']} measured",
            f"correctness   : PASS ({report['correctness']} equal to oracle)",
            f"timings_ms    : min {report['min_ms']:.3f} / median {report['median_ms']:.3f}"
            f" / p95 {report['p95_ms']:.3f} / max {report['max_ms']:.3f}",
            f"threshold     : enforced={report['enforced']} (<= {THRESHOLD_MS:.0f} ms on ubuntu-latest/py3.11)",
            f"raw_ms        : [{raw}]",
        )
    )


def test_t17_measurement(capsys):
    report = _run_t17()
    with capsys.disabled():
        print("\n--- O5 T17 report ---")
        print(_report(report))
        print("--- end report ---\n")

    assert len(report["raw_ms"]) == MEASURED

    if report["enforced"]:
        assert sys.platform.startswith("linux"), (
            f"{ENFORCE_ENV}=1 requires Linux (got {sys.platform})"
        )
        assert sys.version_info[:2] == (3, 11), (
            f"{ENFORCE_ENV}=1 requires CPython 3.11 (got {sys.version_info[:2]})"
        )
        assert report["p95_ms"] <= THRESHOLD_MS, (
            f"p95 {report['p95_ms']:.3f} ms exceeds {THRESHOLD_MS:.0f} ms"
        )
