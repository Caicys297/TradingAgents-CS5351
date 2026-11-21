#!/usr/bin/env python3
"""Deterministic semantic evaluation report for the approved O5 case set.

Runs the *real* approved O5 tests (through the real production entry
``get_global_news_yfinance``) for a versioned, fixed case set, and emits a
machine-readable report with per-case IDs and results against a 100% safety
threshold. Fails nonzero if any required case is missing, errored, skipped, or
failed, or if a prompt/model change is not covered by an approved case.

Evidence scope (honesty):
- This is **actual offline O5 production-path execution with fake vendor inputs**
  (the tests inject fake Yahoo search responses + an in-memory sink). It is NOT
  live-provider evaluation and NOT a general text-quality scorer.
- It covers only the deterministic O5 safety cases here. It does NOT validate
  arbitrary prompt/model changes. A prompt/model change with no approved
  applicable case is reported as a nonzero *applicability* failure, not green.
- O4 semantic coverage is mapped-only until its production/tests are integrated.

Usage:
    python scripts/semantic_report.py [--json PATH] [--base-ref main]
                                       [--changed-from-file FILE]

Exit codes:
    0  required cases passed AND no uncovered prompt/model change in the diff
    1  a required case failed / missing / errored / skipped, OR an uncovered
       prompt/model change was detected, OR pytest failed
    2  execution/internal error (bad/missing JUnit, missing test file, bad input)
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CASESET_VERSION = "o5-deterministic-v2"
THRESHOLD_PASS_RATE = 1.0  # 100% of required cases
TEST_FILE = "test/offline/test_o5_macro_news_integration.py"

# case_id -> (test function name, description, covered prompt/model path)
# Six nodes = the six selected by the approved PR #30 job (upstream-empty kept as
# additional coverage, not removed).
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
    "O5-UPSTREAM_EMPTY-01": (
        "test_s3_empty_vendor_pool_is_distinct_from_filtered_pool",
        "upstream empty pool distinct from filtered-empty (additional coverage)",
        "get_global_news_yfinance (upstream-empty path)",
    ),
}

# Documented scope of prompt/model-related paths and whether an approved case
# covers them. A change under a prompt/model path NOT listed as covered below is
# an applicability failure (nonzero).
PROMPT_MODEL_PATH_PREFIXES = (
    "prompts/",
    "tradingagents/agents/",
    "tradingagents/memory/reflection.py",
    "tradingagents/default_config.py",
    "tradingagents/llm_clients/",
)
# Paths under the above prefixes that the O5 deterministic set DOES cover.
COVERED_PATH_PREFIXES = (
    # the O5 selector/entry that the deterministic cases exercise
    "tradingagents/dataflows/vendors/yahoo/news.py",
    "tradingagents/dataflows/macro_news_filter.py",
)
# Always informational (out of scope for any semantic evaluation here).
INFORMATIONAL = [
    "Arbitrary prompt edits (analyst/PM system prompts) — no approved quality case",
    "Model/provider swaps — not exercised by the deterministic O5 cases",
    "Non-deterministic text-quality scoring — no calibrated evaluator/threshold",
    "LLM tier routing / reasoning-effort changes — out of scope",
]

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_prompt_model_path(path: str) -> bool:
    return any(path.startswith(p) for p in PROMPT_MODEL_PATH_PREFIXES)


def _is_covered(path: str) -> bool:
    return any(path.startswith(p) for p in COVERED_PATH_PREFIXES)


def classify_changes(changed_paths: list[str]) -> dict:
    """Split changes into covered / informational-unrelated / uncovered prompt-model."""
    uncovered = []
    covered = []
    unrelated = []
    for p in changed_paths:
        if _is_covered(p):
            covered.append(p)
        elif _is_prompt_model_path(p):
            uncovered.append(p)
        else:
            unrelated.append(p)
    return {"covered": covered, "uncovered_prompt_model": uncovered, "unrelated": unrelated}


def run_cases(junit_path: Path) -> tuple[int, str]:
    node_ids = [f"{TEST_FILE}::{c[0]}" for c in CASES.values()]
    cmd = [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
        f"--junitxml={junit_path}", *node_ids,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def parse_junit(junit_path: Path, required_names: set[str]) -> dict[str, str]:
    """Parse a fresh JUnit file. Raises ValueError if missing/malformed or if a
    required case name is duplicated (which could mask a required-case failure)."""
    if not junit_path.is_file():
        raise ValueError(f"JUnit report not found: {junit_path}")
    try:
        tree = ET.parse(junit_path)
    except ET.ParseError as exc:
        raise ValueError(f"malformed JUnit report: {exc}") from exc
    seen: dict[str, int] = {}
    outcomes: dict[str, str] = {}
    for tc in tree.iter("testcase"):
        name = tc.get("name", "")
        seen[name] = seen.get(name, 0) + 1
        outcome = "passed"
        for child in tc:
            if child.tag == "failure":
                outcome = "failed"
            elif child.tag == "error":
                outcome = "error"
            elif child.tag == "skipped":
                outcome = "skipped"
        # last wins, but we also detect duplicates below
        outcomes[name] = outcome
    dup = sorted(n for n, c in seen.items() if c > 1 and n in required_names)
    if dup:
        raise ValueError(f"duplicate required testcase name(s) in JUnit: {dup}")
    return outcomes


def evaluate(junit_outcomes: dict[str, str], changes: dict | None = None) -> dict:
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
    cases_ok = (rate >= THRESHOLD_PASS_RATE) and not required_failed

    uncovered = (changes or {}).get("uncovered_prompt_model", [])
    applicability_ok = not uncovered
    threshold_met = cases_ok and applicability_ok
    return {
        "caseset_version": CASESET_VERSION,
        "threshold_pass_rate": THRESHOLD_PASS_RATE,
        "results": results,
        "passed": passed,
        "total": total,
        "pass_rate": rate,
        "required_failed": required_failed,
        "cases_ok": cases_ok,
        "uncovered_prompt_model_changes": uncovered,
        "applicability_ok": applicability_ok,
        "threshold_met": threshold_met,
        "covered_paths": [c[2] for c in CASES.values()],
        "informational": INFORMATIONAL,
        "note": "Offline O5 production-path execution with fake vendor inputs; not a general prompt/model quality evaluator.",
    }


class ApplicabilityError(RuntimeError):
    """Could not determine changed paths from the event (unknown applicability)."""


def _git_diff_names(*revs: str) -> list[str]:
    """NUL-separated `git diff --name-only -z` for the given rev range.

    Raises ApplicabilityError if git fails (e.g. unknown revisions). Uses -z so
    filenames with spaces/newlines are not split.
    """
    proc = subprocess.run(
        ["git", "diff", "--name-only", "-z", *revs],
        capture_output=True, cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        raise ApplicabilityError(
            f"git diff failed for {' '.join(revs)}: {proc.stderr.decode('utf-8', 'replace').strip()[:300]}"
        )
    return [p.decode("utf-8", "replace") for p in proc.stdout.split(b"\x00") if p]


def _pr_changed_files(base_ref: str) -> list[str]:
    """PR event: merge-base three-dot diff against origin/<base>."""
    return _git_diff_names(f"origin/{base_ref}...HEAD")


def _push_changed_files(before: str, after: str) -> list[str]:
    """Push event: all paths changed in the before..after commit range.

    Handles edge cases explicitly rather than treating unknown as clean:
      - new branch / zero before SHA (all zeros): no meaningful prior state ->
        ApplicabilityError (unknown applicability, must not green-pass).
      - after not present / before not present: ApplicabilityError.
    """
    zero = "0" * 40
    if not before or before == zero or not after or after == zero:
        raise ApplicabilityError(
            f"push event has no usable before/after commit range (before={before!r} after={after!r}); "
            "new-branch/tag push applicability is unknown"
        )
    # Verify both commits exist locally.
    for rev in (before, after):
        chk = subprocess.run(
            ["git", "cat-file", "-e", f"{rev}^{{commit}}"], capture_output=True, cwd=REPO_ROOT
        )
        if chk.returncode != 0:
            raise ApplicabilityError(f"push commit {rev} not available in history")
    return _git_diff_names(before, after)


def resolve_changed_files(
    *, changed_from_file: Path | None, base_ref: str | None, env: dict[str, str]
) -> list[str]:
    """Determine changed paths from an explicit file or the CI event, or raise."""
    if changed_from_file is not None:
        raw = changed_from_file.read_bytes()
        return [p.decode("utf-8", "replace") for p in raw.split(b"\x00") if p]

    event = env.get("GITHUB_EVENT_NAME", "").strip()
    if event == "pull_request":
        ref = base_ref or env.get("GITHUB_BASE_REF", "").strip()
        if not ref:
            raise ApplicabilityError("pull_request event without a base ref")
        return _pr_changed_files(ref)
    if event == "push":
        return _push_changed_files(env.get("GITHUB_BEFORE", "").strip(), env.get("GITHUB_AFTER", "").strip())

    raise ApplicabilityError(
        f"unsupported/unknown event ({event!r}); cannot determine applicability "
        "(need --changed-from-file, PR or push history)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=Path("semantic-report.json"))
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--changed-from-file", type=Path, default=None)
    parser.add_argument("--push-before", default=None)
    parser.add_argument("--push-after", default=None)
    args = parser.parse_args(argv)

    if not (REPO_ROOT / TEST_FILE).is_file():
        print("ERROR: O5 integration test file not present; cannot run authorized cases.", file=sys.stderr)
        return 2

    # --- applicability: inspect actual changed paths from the event ---
    import os
    env = dict(os.environ)
    if args.push_before is not None:
        env["GITHUB_EVENT_NAME"] = "push"
        env["GITHUB_BEFORE"] = args.push_before
        env["GITHUB_AFTER"] = args.push_after or ""
    try:
        changed = resolve_changed_files(
            changed_from_file=args.changed_from_file, base_ref=args.base_ref, env=env
        )
    except ApplicabilityError as exc:
        print(f"ERROR: cannot determine prompt/model applicability: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # diff failure is an execution error, not green
        print(f"ERROR: cannot determine changed files: {exc}", file=sys.stderr)
        return 2

    changes = classify_changes(changed)

    # --- fresh JUnit per invocation ---
    junit = REPO_ROOT / "semantic-junit.xml"
    with contextlib.suppress(FileNotFoundError):
        junit.unlink()
    rc, diag = run_cases(junit)
    try:
        outcomes = parse_junit(junit, {fn for (fn, _d, _p) in CASES.values()})
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if diag.strip():
            print("--- pytest diagnostics ---", file=sys.stderr)
            print(diag[-4000:], file=sys.stderr)
        return 2

    report = evaluate(outcomes, changes)
    args.json.write_text(json.dumps(report, indent=2) + "\n")

    print(f"semantic case set {CASESET_VERSION}: {report['passed']}/{report['total']} passed "
          f"(threshold {THRESHOLD_PASS_RATE:.0%})")
    for r in report["results"]:
        print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['case_id']} {r['node_id']} -> {r['outcome']}")
    for u in report["informational"]:
        print(f"  [INFO out-of-scope] {u}")

    failed = False
    if not report["cases_ok"]:
        print(f"SEMANTIC FAILED: required cases failed/missing: {report['required_failed']}", file=sys.stderr)
        failed = True
    if rc != 0:
        print(f"SEMANTIC FAILED: pytest exited {rc}", file=sys.stderr)
        print(diag[-4000:], file=sys.stderr)
        failed = True
    if report["uncovered_prompt_model_changes"]:
        print("SEMANTIC APPLICABILITY FAILED: prompt/model change without an approved "
              "applicable case:", file=sys.stderr)
        for p in report["uncovered_prompt_model_changes"]:
            print(f"  - {p}: no mapping to an approved deterministic O5 case", file=sys.stderr)
        failed = True

    if failed:
        return 1
    print("SEMANTIC OK: required cases passed; no uncovered prompt/model change in the diff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
