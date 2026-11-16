# O1 SMA Validity Guard — OpenCode Execution Plan v1.0 (Draft)

**Owner and execution-plan reviewer:** Member A

**Test-plan reviewer:** Member F; Member B checks the requirement–case mapping

**Status:** Pre-code draft, 16 November 2026. No approval, implementation, O1 test execution, or CI result is claimed.

## 1. Basis and scope

Use `docs/req/requirements.yaml` REQ-O1-01 through REQ-O1-06 from the merged requirements PR #2 as the requirement baseline. The companion test plan is `O1-SMA-Guard-Test-Plan-v1.0-DRAFT.md`, cases T-O1-01 through T-O1-12. The older `O1-SMA-Guard-Requirements-Draft.md` is discussion history where it differs from the YAML.

O1 changes only the Yahoo/stockstats `close_50_sma` and `close_200_sma` results. The bulk report, per-day fallback, and verified snapshot must agree. Other indicators, Alpha Vantage, public tool signatures, the Yahoo history download window, and cache policy stay outside this change.

This plan summarizes OpenCode's read-only analysis in session `ses_e34f21c97ffevLFn0o9TxQa9zG` and A's review corrections. The raw session must be preserved separately for D5; this summary is not a substitute for that transcript.

## 2. Pre-code checks and approvals

1. **Confirm the implementation base.** The local `feature/o1-sma-guard` checkout is still at `970a9ea`, before CI PR #1 and requirements PR #2. It also contains untracked local documents under `docs/req/`. Record those files and update the feature branch safely from current `main` before writing code; do not use a blind pull or discard the untracked files. Confirm the resulting commit, YAML version, `test/offline/` collection, and offline network fixture.
2. **Confirm governance files.** Check the project-root `AGENTS.md` and `Prompt.md` and follow the approved reading order and permissions before asking OpenCode to write code. They are absent from the current local O1 checkout; their creation is a project-level task, not an O1 code change in this plan.
3. **Approve the test plan first.** F records approval of the exact O1 test-plan version and T-O1-01 through T-O1-12 before any O1 test or implementation code is written. B checks the YAML-to-case mapping. Use `docs/test-approvals/TEMPLATE.md` or the agreed record location with the reviewer, actual time, version, case range, and original GitHub/message evidence.
4. **Approve this execution plan separately.** A records the reviewed plan version, implementation-base commit, allowed files, scope, and actual approval time before the first OpenCode code edit. If the file list or behavior changes materially, revise the plan and obtain approval of that revision.

## 3. Allowed changes after both approvals

| File | Planned change |
|---|---|
| `tradingagents/dataflows/vendors/yahoo/market.py` | Add an internal rule for the two named SMA windows. Use it in `_get_stock_stats_bulk` and `get_stock_stats`; keep `get_stock_stats_indicators_window`'s public signature and fallback behavior. |
| `tradingagents/dataflows/vendors/yahoo/snapshot.py` | Use the same SMA rule for the two SMA cells in `build_verified_market_snapshot`. Keep the existing formatting and other indicator cells. |
| `test/offline/test_o1_sma_guard.py` | Add deterministic, network-free cases T-O1-01 through T-O1-12, including controlled real-loader fixtures for T-O1-09/10. F confirms this exact path when approving the test plan. |

No change is planned to `ohlcv.py`, `router.py`, `agents/tools.py`, Alpha Vantage, `pyproject.toml`, CI workflows, or `test/offline/conftest.py`. A new production file, dependency, public API change, or changed download/cache policy requires a revised plan before editing.

## 4. Function-level implementation plan

1. In `market.py`, keep one internal mapping for `close_50_sma → 50` and `close_200_sma → 200` and one shared SMA calculation rule. Apply this path only when the requested indicator is one of those two names. The non-SMA path keeps its existing stockstats behavior.
2. For an O1 SMA request, work from cleaned dated closes. Exclude rows later than the request's `as_of_date`, reject duplicate trading dates among the remaining rows with the exact invalid-history text, and sort the eligible rows by date. For each reported date, count and use only closes through that date. Produce a numeric latest-W mean only when at least W usable closes exist; otherwise return the exact insufficient-history text for counts 1 through W−1. Do not silently deduplicate or produce a partial-window SMA.
3. `_get_stock_stats_bulk` returns its existing date-keyed map. The value for an early date must depend on that date's eligible history, not the whole frame length. `get_stock_stats` applies the same rule for one target date so the per-day fallback cannot bypass the guard. A date absent from the cleaned frame retains the existing non-trading-day message.
4. The snapshot already selects and sorts rows on or before the analysis date. Use the shared SMA rule for its 50/200 SMA cells, including duplicate-date rejection; retain the current `price_text` display rule for valid values. Do not apply O1's guard to `rsi`, EMA, Bollinger, MACD, ATR, or any other indicator.
5. Keep the current no-data path. In particular, T-O1-10's non-empty, all-`Close`-missing loader fixture must yield `NoMarketDataError` directly and `NO_DATA_AVAILABLE` through the routed tool, never `have 0`. This plan does not claim that every possible empty-frame route has the same direct exception without separate source verification.

## 5. Existing test-case map

| Cases | Path and purpose |
|---|---|
| T-O1-01–04 | `_get_stock_stats_bulk`: 40/49, 50/60, 199/200/220, and early date in a 260-date frame. |
| T-O1-05 | `build_verified_market_snapshot`: both SMA boundaries and display formatting. |
| T-O1-06 | Force bulk `RuntimeError`; spy on `get_stockstats_indicator`; verify the per-day path reaches `get_stock_stats` and applies the guard. |
| T-O1-07 | Bulk, fallback, and snapshot non-SMA control; inherited regression tests. |
| T-O1-08 | Indicator-window text distinguishes insufficient history from an absent trading date. |
| T-O1-09 | Real `load_ohlcv` with a controlled fresh cache and one missing middle close; guard counts 49/199 usable closes. |
| T-O1-10 | Real loader and routed tool on a non-empty frame with all closes missing; preserve no-data behavior. |
| T-O1-11 | Bulk with shuffled unique dates and deliberate future rows from a mocked loader; guard sorts and excludes later rows before computing. |
| T-O1-12 | Bulk, `get_stock_stats`, and snapshot with an eligible duplicate trading date; exact invalid-history text and no numeric SMA. |

The expected strings and valid-value tolerance are those in the YAML: `N/A: insufficient history (needs W sessions, have N)`, `N/A: invalid price history (duplicate trading date)`, and absolute numeric error at most `1e-6` before display formatting. The test plan gives the exact fixture and assertion for each ID; this execution plan does not add cases or acceptance criteria.

## 6. Runtime actions already specified by O1

| Trigger | Action | Result |
|---|---|---|
| At least W eligible closes through the reported date | Compute the latest-W mean. | Numeric O1 SMA. |
| 1 through W−1 eligible closes | Suppress the partial-window number. | Exact insufficient-history text with W and N. |
| A row later than the analysis date | Exclude it from O1 SMA calculation. | Earlier dated result is unaffected. |
| Duplicate date among rows eligible for this request | Reject the O1 SMA input; do not silently deduplicate. | Exact invalid-history text; no numeric O1 SMA. |
| T-O1-10's all-missing-close loader input | Preserve existing no-data routing. | Direct loader error; routed `NO_DATA_AVAILABLE`. |
| Requested date absent from cleaned rows | Preserve the existing date lookup behavior. | Existing non-trading-day text. |

## 7. Build and verification sequence after approval

1. Add the approved offline tests and record which cases fail on the unguarded baseline, if a baseline run is feasible. Do not change expected results just to make the baseline pass.
2. Make the minimal `market.py` and `snapshot.py` changes above. Keep the shared rule confined to the two O1 indicators.
3. Run the O1 file directly, then the default regression suite after confirming that the updated branch collects both `tests/` and `test/offline/`. F checks default collection, network blocking, pytest node IDs, and the applicable CI results. Planned commands (not run now):

   ```text
   pytest --collect-only -q test/offline/test_o1_sma_guard.py
   pytest -q test/offline/test_o1_sma_guard.py
   pytest -q
   ruff check tradingagents/dataflows/vendors/yahoo/market.py tradingagents/dataflows/vendors/yahoo/snapshot.py test/offline/test_o1_sma_guard.py
   ```

4. Open the O1 code PR. Preserve the actual test output, CI links, approval records, first-code time, code review, and raw OpenCode transcript. No result is recorded in advance.

**Stop condition:** If a case needs a different public behavior, a new file, a change to another indicator/vendor, or a new test case, stop and return the proposed change for requirement/test-plan review before coding it.
