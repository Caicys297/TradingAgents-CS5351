# O1 — SMA Validity Guard: Requirements Draft

**Owner:** Member A  
**Status:** Revised discussion draft, 12 November 2026. Proposed by Member A for owner review; scope and tests are not approved. No O1 code has been changed or tested.  
**Proposed scope:** Guard the 50-session and 200-session SMA outputs on the Yahoo/stockstats path.

## 1. Problem and goal

A simple moving average (SMA) for a window of 50 or 200 sessions should only be presented as that window's average when enough usable closing prices exist up to the reported date. The current Yahoo indicator path asks stockstats for the SMA and reports its value without checking the history length. The verified market snapshot also reports the latest stockstats value without this check. The official [TradingAgents issue #1679](https://github.com/TauricResearch/TradingAgents/issues/1679) reports a very short-history case in which both SMAs were shown as the same partial-history average.

Relevant baseline code: [`market.py`](TradingAgents-CS5351/tradingagents/dataflows/vendors/yahoo/market.py) (`_get_stock_stats_bulk`, `get_stock_stats`, and `get_stock_stats_indicators_window`); [`snapshot.py`](TradingAgents-CS5351/tradingagents/dataflows/vendors/yahoo/snapshot.py) (`build_verified_market_snapshot`); and [`ohlcv.py`](TradingAgents-CS5351/tradingagents/dataflows/vendors/yahoo/ohlcv.py) (`load_ohlcv`). The current loader removes rows without a closing price and excludes rows after the analysis date.

O1's goal is to prevent a partial-history SMA from being presented as a valid 50-session or 200-session value. It covers the normal indicator report, its per-day fallback, and the verified snapshot. An unavailable SMA must be distinguishable from a non-trading day.

**Scope limit:** This proposal does not change the historical download window or cache. For an old analysis date, the current loader may still have too little history even when earlier prices exist at the vendor. O1 would then honestly report insufficient history, but it would not recover the correct historical SMA values. O1 must not be described as a complete fix for every part of issue #1679. Alpha Vantage behavior is outside this proposed change and has not been verified by these tests.

## 2. Requirements for discussion

The IDs below are provisional entries for the eventual D1 YAML requirements registry. A test ID is separate from a requirement ID. “Must” means O1 cannot be accepted without the criterion; the tradeoff column states what is lost if it is omitted.

| ID | Type | Statement | Priority and tradeoff | Machine-checkable fit criterion |
|---|---|---|---|---|
| REQ-O1-01 | Functional behavior | For each reported trading date with at least one usable close, show a numeric `close_50_sma` only when at least 50 usable dated closes exist through that date. For 1–49 closes, show the approved insufficient-history text. Zero usable closes retain the existing no-market-data behavior. | **Must.** Without it, a short-history value can be labelled a 50-session SMA. | At the target date with 49 closes, the exact insufficient-history value is returned; with 50, the parsed numeric value matches the latest-50 mean within an approved tolerance. |
| REQ-O1-02 | Functional behavior | Apply the same rule to `close_200_sma` with a 200-session window; zero usable closes retain the existing no-market-data behavior. | **Must.** Without it, a short-history value can be labelled a 200-session SMA. | At the target date with 199 closes, the exact insufficient-history value is returned; with 200, the parsed numeric value matches the latest-200 mean within an approved tolerance. |
| REQ-O1-03 | Invariant | Determine validity separately for each reported date, counting only usable closes up to and including that date. | **Must.** A whole-frame count could make an early date look valid because later rows exist. | In a 260-row series, at row 60 the 50-SMA is valid and the 200-SMA is unavailable, even though the full series has 260 rows. Zero early-date 200-SMA values are reported as valid. |
| REQ-O1-04 | Functional behavior | When the yfinance/stockstats vendor serves the indicator (the shipped technical-indicators default, `default_config.py:160`), apply REQ-O1-01 and REQ-O1-02 on the bulk indicator path, the per-day fallback, and the verified snapshot. Alpha Vantage and any other configured indicator vendor remain outside O1. | **Must.** An unguarded Yahoo path would still send a misleading value to the analyst. | On the Yahoo path, each of the bulk, fallback, and snapshot entry points reports insufficient history for 49/199 sessions and a valid value at the corresponding 50/200 boundary. |
| REQ-O1-05 | Invariant | Leave non-SMA indicators' behavior unchanged. | **Must.** A broad guard could suppress unrelated indicators. | For a controlled frame, each selected non-SMA output equals the same-run direct stockstats reference; the prior regression suite has zero new failures. |
| REQ-O1-06 | Quality attribute: clear output | Use a labelled insufficient-history result that is distinct from the existing non-trading-day result. The exact text remains a review decision. | **Must.** A generic `N/A` would hide the reason from the analyst. | Metric: ambiguous statuses in the O1 output tests. Threshold: **0**. Verification: tests assert distinct exact text for insufficient history and a non-trading day. |

**Proposed text (not current behavior; requires owner approval):** `N/A: insufficient history (needs W sessions, have N)`, where W is 50 or 200 and N is the number of usable closes through the reported date.

**Proposed numeric comparison (requires owner approval):** for a valid SMA, compare parsed numeric values against an independently computed mean as `abs(actual - expected) <= 1e-6` **before** any display formatting. For the snapshot, format the expected mean with the existing `price_text` rule and compare the displayed text exactly.

**Input and output contract:** The existing public tool inputs and function signatures remain unchanged. The Yahoo path receives a symbol, indicator name, analysis date, and (for the report) look-back period. Valid results retain the current numeric rendering; insufficient results use the approved text. The guard counts one cleaned, dated closing-price row per session through the date being reported. **Pending confirmation with C:** the owner and C must confirm that the cleaned input is chronologically ordered with unique dates (or assign that guarantee to a specific component) before approval, because the per-date counting and the by-date map lookup assume it. A missing close is not counted. A date absent from the cleaned loader output retains the existing non-trading-day message; this wording does not prove whether the date was actually a holiday or a missing-data day. The snapshot uses its latest trading row on or before the requested analysis date.

## 3. Proposed change boundary and integration risks

| Area | Proposed work | Shared-file concern |
|---|---|---|
| `market.py` | Guard `_get_stock_stats_bulk` per row and `get_stock_stats` for the fallback. A shared SMA-window rule may live here. | Other Yahoo indicators use this file. |
| `snapshot.py` | Guard the latest reported SMA values with the same rule. | The market analyst treats this snapshot as a source for exact claims. |
| `ohlcv.py`, router, tools, Alpha Vantage | No proposed O1 change. | Historical download behavior remains a documented limitation. The shipped technical-indicators default is `yfinance` (`default_config.py:160`), so the Yahoo guard is active by default; if a user configures `alpha_vantage` (or another vendor) that vendor's own warm-up behavior applies and O1 does not cover it. The only configuration that selects every vendor is the explicit `"default"` sentinel, which for `get_indicators` orders `alpha_vantage` before `yfinance` (`router.py:216,225`, `router.py:104-106`). On the yfinance path a returned insufficient-history string is a successful router result and does not fall through to another vendor (`router.py:235-237`); C must record this authority and fallback contract. |

Member C should check whether another feature plans to edit `market.py` or `snapshot.py`, and whether the proposed helper has an appropriate home. Member F should resolve the offline-test location and CI collection issue described in the companion test plan. Member B can incorporate the approved requirements into the course's machine-readable YAML registry; this Markdown draft is not the final D1 deliverable.

## 4. Review decisions and record

| Decision | Current state |
|---|---|
| O1 scope: guard only, or also historical data retrieval | Guard only is proposed; Member A decision pending. |
| Exact insufficient-history text | Proposed above; decision pending. |
| Numeric comparison tolerance (`<= 1e-6`, pre-format) | Proposed above; decision pending. |
| Chronological, unique-date input guarantee | Pending confirmation with Member C. |
| File/interface conflict check with Member C | Pending. |
| Test location and CI collection with Member F | Pending. |
| Requirements and test-plan approval before implementation | Pending; record approver, date, version, and evidence after the actual decision. |

The full OpenCode session and Member A's real corrections should be retained for D5. No approval, implementation, or test result is claimed in this draft.
