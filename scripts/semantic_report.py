#!/usr/bin/env python3
"""Deterministic semantic evaluation report for the approved O5 case set.

Runs the *real* approved O5 tests (through the real production entry
``get_global_news_yfinance``) for a versioned, fixed case set, and emits a
machine-readable report with per-case IDs and results against a 100% safety
threshold. Fails nonzero if any required case is missing, errored, skipped, or
failed.

Scope honesty:
- Covers only the deterministic O5 safety cases defined here. It does NOT
  validate arbitrary prompt/model changes, and is not a general text-quality
  evaluator.
- Prompt/model paths *not* covered are reported explicitly (``UNCOVERED``).
- The report is produced only from actual pytest outcomes (no pre-filled scores).

Usage:
    python scripts/semantic_report.py [--json PATH]

Exit codes:
    0  all required cases passed (100% safety threshold met)
    1  a required case failed / missing / errored / skipped
    2  execution/internal error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CASESET_VERSION = "o5-deterministic-v1"
THRESHOLD_PASS_RATE = 1.0  # 100% of required cases

TEST_FILE = "test/offline/test_o5_macro_news_integration.py"

# case_id -> (test function name, description, covered prompt/model path)
CASES: dict[str, tuple[str, str, str]] = {
    "O5-REL-01": (
        "test_s4_selected_path_filters_before_slice_and_keeps_fields",
        "relevant macro news selected via real get_global_news_yfinance (filter-before-slice)",
        "tradingagents/dataflows/vendors/yahoo/news.py:get_global_news_yfinance (selector path)",
    ),
    "O5-EMPTY-01": (
        "test_s4_t04d_filtered_to_zero_is_not_upstream_empty",
        "irrelevant candidates filtered to zero (distinct from upstream-empty)",
        "get_global_news_yfinance (filtered-empty path)",
    ),
    "O5-EMPTY-02": (
        "test_s4_t04d_all_irrelevant_uses_the_all_irrelevant_enum_member",
        "all-irrelevant -> ALL_IRRELEVANT exact enum member",
        "get_global_news_yfinance (ALL_IRRELEVANT path)",
    ),
    "O5-UNAVAIL-01": (
        "test_s4_filter_unavailable_text_is_distinct_from_filtered_empty",
        "filter unavailable -> suppression, no unvalidated publication",
        "get_global_news_yfinance (FILTER_UNAVAILABLE path)",
    ),
    "O5-LIMIT0-01": (
        "test_s3_zero_limit_skips_vendor",
        "limit=0 -> zero vendor calls",
        "get_global_news_yfinance (LIMIT_ZERO short-circuit)",
    ),
}

UNCOVERED = [
    "Arbitrary prompt edits (analyst/PM system prompts) — no fixed quality case in this set",
    "Model/provider swaps — not exercised by the deterministic O5 cases",
    "Non-deterministic text-quality scoring — no calibrated evaluator/threshold in this set",
    "LLM tier routing / reasoning-effort changes — out of scope for this set",
]

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cases(junit_path: Path) -> int:
    node_ids = [f"{TEST_FILE}::{c[0]}" for c in CASES.values()]
    cmd = [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
        f"--junitxml={junit_path}", *node_ids,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT).returncode


def parse_junit(junit_path: Path) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    if not junit_path.is_file():
        return outcomes
    tree = ET.parse(junit_path)
    for tc in tree.iter("testcase"):
        name = tc.get("name", "")
        outcome = "passed"
        for child in tc:
            if child.tag == "failure":
                outcome = "failed"
            elif child.tag == "error":
                outcome = "error"
            elif child.tag == "skipped":
                outcome = "skipped"
        outcomes[name] = outcome
    return outcomes


def evaluate(junit_outcomes: dict[str, str]) -> dict:
    results = []
    required_failed = []
    for case_id, (fn, desc, path) in CASES.items():
        outcome = junit_outcomes.get(fn, "missing")
        ok = outcome == "passed"
        results.append({
            "case_id": case_id, "node_id": f"{TEST_FILE}::{fn}",
            "covered_path": path, "description": desc,
            "outcome": outcome, "pass": ok,
        })
        if not ok:
            required_failed.append(case_id)
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    rate = passed / total if total else 0.0
    threshold_met = (rate >= THRESHOLD_PASS_RATE) and not required_failed
    return {
        "caseset_version": CASESET_VERSION,
        "threshold_pass_rate": THRESHOLD_PASS_RATE,
        "results": results,
        "passed": passed,
        "total": total,
        "pass_rate": rate,
        "required_failed": required_failed,
        "threshold_met": threshold_met,
        "covered_paths": [c[2] for c in CASES.values()],
        "uncovered_changes": UNCOVERED,
        "note": "Deterministic O5 safety cases only; not a general prompt/model quality evaluator.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=Path("semantic-report.json"))
    args = parser.parse_args(argv)

    if not (REPO_ROOT / TEST_FILE).is_file():
        print("ERROR: O5 integration test file not present; cannot run authorized cases.", file=sys.stderr)
        return 2

    junit = REPO_ROOT / "semantic-junit.xml"
    rc = run_cases(junit)
    report = evaluate(parse_junit(junit))
    args.json.write_text(json.dumps(report, indent=2) + "\n")

    print(f"semantic case set {CASESET_VERSION}: {report['passed']}/{report['total']} passed "
          f"(threshold {THRESHOLD_PASS_RATE:.0%})")
    for r in report["results"]:
        print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['case_id']} {r['node_id']} -> {r['outcome']}")
    for u in UNCOVERED:
        print(f"  [UNCOVERED] {u}")

    if not report["threshold_met"]:
        print(f"SEMANTIC FAILED: required cases failed/missing: {report['required_failed']}", file=sys.stderr)
        return 1
    if rc != 0:
        print(f"SEMANTIC FAILED: pytest exit {rc} despite threshold check", file=sys.stderr)
        return 1
    print("SEMANTIC OK: all required deterministic O5 cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
