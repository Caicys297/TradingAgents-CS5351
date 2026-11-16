# O1 — SMA Validity Guard: Test Plan v1.0 (Draft)

**Owner:** Member A

**Reviewers:** Member F (test plan); Member B (requirement–case mapping)

**Status:** Prepared for review on 16 November 2026. No pre-implementation approval, execution, or result is claimed.

**Requirement baseline:** `docs/req/requirements.yaml`, REQ-O1-01 through REQ-O1-06, merged in requirements PR #2. Check the exact version before approval. The root `O1-SMA-Guard-Requirements-Draft.md` is an earlier discussion record; it does not override the selected YAML where they differ.

## 1. Scope and method

Test the Yahoo/stockstats `close_50_sma` and `close_200_sma` paths only: the bulk indicator report, the per-day fallback, and the verified snapshot. The guard does not change the history download window, cache, other indicators, or other vendors.

Use deterministic non-constant OHLCV frames with dated closes and no external network. For boundary cases, replace the Yahoo module's `load_ohlcv` with a frame representing cleaned loader output. For loader cases, exercise the real `load_ohlcv` using a seeded local cache and block downloads. Calculate expected SMA values independently from the latest 50 or 200 valid closes on or before the target date. Compare the unformatted value with absolute error at most `1e-6`; compare snapshot text using the existing `price_text` display rule. Check the value for the **target date**, not a matching value elsewhere in the report.

The required insufficient-history value is exactly `N/A: insufficient history (needs W sessions, have N)` after replacing W and N with integer counts. A duplicate trading date gives exactly `N/A: invalid price history (duplicate trading date)` for the requested SMA. The existing non-trading-day and no-market-data results stay distinct. The cases below are planned outcomes, not observed results.

## 2. Cases and requirement mapping

| ID | Controlled input and entry point | Expected assertion | Requirements |
|---|---|---|---|
| T-O1-01 | 40 and 49 cleaned dated closes; call `_get_stock_stats_bulk` separately for each SMA. | At 40, both SMA values are exact insufficient-history strings with `have 40`; at 49, 50-SMA says `have 49`. No partial-window number. | REQ-O1-01, REQ-O1-02 |
| T-O1-02 | 50 and 60 cleaned closes; separate bulk calls for each fixture and indicator. | 50-SMA equals the latest-50 mean within tolerance at both counts; 200-SMA says `have 50` on the 50-row fixture and `have 60` on the 60-row fixture. | REQ-O1-01, REQ-O1-02 |
| T-O1-03 | 199, 200, and 220 cleaned closes; separate bulk calls. | At 199, 200-SMA says `have 199`; at 200 and 220, both SMAs equal their latest-window means. | REQ-O1-01, REQ-O1-02 |
| T-O1-04 | 260 ordered dates; request the 60th chronological date from `_get_stock_stats_bulk` for each SMA and look it up by date key. | On that date, 50-SMA equals the mean of dates 11–60; 200-SMA says `have 60`, despite 260 rows being present. | REQ-O1-03 |
| T-O1-05 | Call `build_verified_market_snapshot` with 40, 50, 199, and 200 cleaned closes, using the default indicators. | Its 50/200 SMA cells have the same boundary outcomes; valid cells match `price_text` of the independently computed mean. | REQ-O1-01, REQ-O1-02, REQ-O1-04 |
| T-O1-06 | Force `_get_stock_stats_bulk` to raise `RuntimeError`; spy on `get_stockstats_indicator`; call `get_stock_stats_indicators_window` for each SMA with `look_back_days=0` and frames of 49/50 or 199/200 rows. | The spy confirms the per-day fallback ran. The target-date report line has the exact insufficient string at W−1 and a correct mean at W. | REQ-O1-01, REQ-O1-02, REQ-O1-04 |
| T-O1-07 | On a controlled frame, request one default non-SMA indicator, such as `rsi`, through bulk, forced fallback, and snapshot; compute a same-frame stockstats reference. | Non-SMA values retain their prior numerical/display behavior; the existing regression suite has no new failures. | REQ-O1-05 |
| T-O1-08 | In one `get_stock_stats_indicators_window` output, include a dated row with insufficient history and a nearby absent weekend date. | The first line has the exact insufficient-history value; the absent date has the existing `N/A: Not a trading day (weekend or holiday)` value. | REQ-O1-06 |
| T-O1-09 | Seed the real `load_ohlcv` cache with 50 dated rows and one middle missing `Close`; repeat with 200 rows if needed to cover both windows. Follow the frozen-`today`, fresh-cache, blocked-download pattern in `tests/test_ohlcv_latest_bar.py::_run_load`. | Loader removes the missing-close row. The O1 entry point counts 49/199 valid closes and does not return a numeric 50/200 SMA. Reuse existing loader tests where they prove the cleaning step. | REQ-O1-01, REQ-O1-02 |
| T-O1-10 | Seed a **non-empty** cache frame whose `Close` column is entirely missing; exercise real `load_ohlcv` and one routed O1 tool. | Direct loader raises `NoMarketDataError` with detail `no bar in range has a closing price`; the routed output has `NO_DATA_AVAILABLE`, with no numeric SMA or `have 0` message. | REQ-O1-01, REQ-O1-02, REQ-O1-04 |
| T-O1-11 | Supply 260 unique dated, non-constant closes in shuffled order and the same frame sorted as a control. Call `_get_stock_stats_bulk` for each SMA with `as_of_date` set first to the 60th chronological date and then to the final date; the mocked loader deliberately returns all 260 rows in both calls. Put an extreme price after the earlier analysis date. | **After the guard is implemented**, shuffled and sorted frames give the same dated SMA results. At date 60, 50-SMA is the mean of chronological dates 11–60 and 200-SMA says `have 60`; at the final date, both SMAs match their latest-window means. The later extreme price does not affect date 60. | REQ-O1-03 |
| T-O1-12 | Supply a cleaned-looking frame with two rows sharing a trading date. Inject it at `load_ohlcv` for `_get_stock_stats_bulk`, `get_stock_stats` (per-day path), and `build_verified_market_snapshot`; request both SMAs separately. Use a separate non-SMA control. | **After the guard is implemented**, no SMA entry point publishes a numeric result for invalid history; the requested SMA result is the exact duplicate-date message. The non-SMA control retains its prior behavior. No routed-tool duplicate-message assertion is made. | REQ-O1-03, REQ-O1-06 |

T-O1-11 tests the **new O1 calculation's** ordering and date cutoff, even when the controlled frame includes later rows. It does **not** prove the real loader's cutoff; existing loader and snapshot tests provide that separate evidence. T-O1-12 tests the **new O1 duplicate-date behavior** at the three direct entry points. Current code has no such message and must change for this planned case to pass. The public routed tool is outside this assertion because the current real loader does not reject duplicates.

## 3. Execution and evidence plan

Place deterministic O1 tests under `test/offline/`, subject to F's final CI review. Current `main` (after CI PR #1) collects both `tests/` and `test/offline/` by default and excludes tests marked `integration`; the older local `feature/o1-sma-guard` checkout still has `testpaths = ["tests"]`. Bring that feature branch up to the approved main baseline safely before relying on default collection, and confirm its local configuration. Keep these offline cases in the default run; use `pytest -q test/offline/<O1_test_file>.py` for the O1 file and `pytest -q` for the regression run after implementation. F will record the actual pytest node IDs, default collection, network-block result, CI run links, and any separately run inherited suite. Do not mark a deterministic offline case `integration` merely because it crosses a loader or router boundary.

Before implementation, seek F's approval of this exact plan version and case range T-O1-01 through T-O1-12. B checks the requirement–case mapping. Keep a dated approval record in `docs/test-approvals/` or the team's agreed record location, with the plan link, reviewer, decision, scope, and timestamp; preserve the original message/PR evidence. A then approves the read-only OpenCode execution plan as a separate decision. Only after these approvals should implementation or test code be written. Record actual first-code time, baseline failure if feasible, passing result, PR review, CI links, and raw OpenCode transcript later; do not fill these fields in advance.

## 4. Read-only feasibility checks before approval

- Confirm the exact function seam and report-line parser for each case, especially T-O1-06 and T-O1-12. `get_stock_stats_indicators_window` handles one indicator per call.
- Check whether T-O1-11's earlier-date assertion can be exercised through the bulk function with a controlled frame, and whether the source itself enforces the analysis-date cutoff or relies on `load_ohlcv`.
- Confirm T-O1-12's expected duplicate-date behavior at bulk, per-day, and snapshot entry points and define the smallest production change needed to make them agree. Keep the non-SMA control independent.
- Confirm T-O1-09/10's seeded-cache fixtures remain recent enough for the loader's stale-data rule and cannot reach the network.
- Check the feature branch against current main's pytest collection and offline network fixtures before recording exact CI commands.

If a check shows a case is infeasible or changes an approved requirement, revise this draft and obtain approval of the new version before coding.
