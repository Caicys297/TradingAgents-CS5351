# S2–S4 Execution Plan — FINAL DRAFT (for A)
Status: DRAFT for A review — not approved. Baseline: 5cdd7589cc73817133a7ca73cf768fc02d0cd19a. S2–S4 implementation and tests: Not run.

## 1. Files (closed whitelist)
| Path | Change |
| --- | --- |
| tradingagents/dataflows/vendors/yahoo/news.py | E-owned private integration (regions 1–4) |
| test/offline/test_o5_evidence_builder.py | new (S2) |
| test/offline/test_o5_macro_news_integration.py | new (S3/S4) |
| test/offline/test_o5_regression.py | new (RT-1..RT-4, T16) |
| test/offline/test_o5_invariants.py | append runtime-invariant cases |
Untouched: macro_news_filter.py (consumed, not edited), router.py, common.py, date_window.py, agents/tools.py, default_config.py, cli/run.py, graph files, pyproject.toml, CI, test/offline/conftest.py.

## 2. Private helpers (names Pending A)
_build_o5_request, _validate_o5_request_for_retrieval (thin wrapper over existing request validation — no second policy), _map_news_dict_to_candidate, _map_selected_to_article_dict, _check_o5_invariants, _build_o5_evidence, _emit_o5_evidence, _exit_o5_with_evidence.

## 3. Call order
validate → invalid exit (V-INVALID-REQUEST) → K=0 exit (V-LIMIT-ZERO) → existing collector loop (query text, news_count, enable_fuzzy_query, window filter, title dedupe, early stop unchanged) → empty-pool exit (V-UPSTREAM-EMPTY) → convert → select_macro_news → zero-selected exit (V-FILTERED-EMPTY) → invariant check → terminal exit (V-SELECTED only after invariants pass) → existing formatted output. finally never emits.

## 4. Conversion — exact rule
(a) candidate_id. Fixed by the DEV20 fixture metadata; the article shape supplies every input:

o5: + first 32 hex of sha256(canon(title) + U+001F + canon(source) + U+001F + canonical_url + U+001F + timestamp_iso), with canon = NFKC → casefold → whitespace-collapse → strip; canonical_url lowercases the scheme and host, removes only default ports, the trailing slash, query and fragment, and uses "" when the URL is absent; timestamp_iso = YYYY-MM-DDTHH:MM:SSZ at second precision.

Inputs come straight from _extract_article_data: title→title, publisher→source, link→URL, pub_date→timestamp. Presented as a design for A to review; it is reproducible from the current shape and needs no fallback.

(b) Article-dictionary round-trip for _format_articles:

| Formatter key | SelectedRecord field |
| --- | --- |
| title | title |
| publisher | source |
| summary | summary |
| link | url |
| pub_date | published_at (retained for audit; not printed) |
Original business fields pass through unchanged, including extraction's existing "Unknown"/"" defaults, so the formatted output is unchanged.

## 5. Behaviour preserved
Query strings from global_news_queries, news_count=limit, enable_fuzzy_query=True, window filtering, exact-title dedupe, early stop at len >= limit, _extract_article_data/_format_articles unchanged, get_news_yfinance untouched, public get_global_news signature and str return.

## 6. Requirement status after S2–S4
S2–S4 do not complete O5. Still open: S5 real persistence, REQ-O5-07 human holdout, REQ-O5-10 (S6 T17).

## Case table
| Case | Expected | File | Stage |
| --- | --- | --- | --- |
| I9-a-1/2/3 | V-VENDOR control accepts; missing / non-null reject | test/offline/test_o5_evidence_builder.py | S2 |
| T03a-A | 0 fetches; V-LIMIT-ZERO | test/offline/test_o5_macro_news_integration.py | S3 |
| T10f/g/g2/i/j | V-INVALID-REQUEST, 0 fetches | integration | S3 |
| T13a / T13b | raise / DATA_UNAVAILABLE | integration | S3 |
| T13c-D / T13c-R | one V-PARTIAL, zero V-VENDOR | integration | S3 |
| I9-b | V-VENDOR, one event, non-null version | integration | S3 (after seam) |
| I13 | V-PARTIAL, one event, no V-VENDOR | integration | S3 (after seam) |
| T13d | coverage-gap vs seam empty_kind | integration | S3 |
| T04b | V-UPSTREAM-EMPTY, empty-feed phrasing | integration | S3 |
| T04c | all-out-of-window ⇒ coverage-gap | integration | S3 |
| T04d (proposed ID) | non-empty pool, zero selected ⇒ V-FILTERED-EMPTY | integration | S4 |
| Success path | V-SELECTED after invariant pass | integration | S4 |
| I1, I3, I2, I11, time-tamper | INV-O5-02 / 02 / 03 / 01 / 01 | test/offline/test_o5_invariants.py | S4 |
| T01/T02/T05/T06/T19/T20 | S1 IDs/order/counts via entry | integration | S4 |
| T15 | filter-before-slice, pool 4, K=3 | integration | S4 |
| T16, RT-1..RT-4 | zero adds; schemas/ticker unchanged | test/offline/test_o5_regression.py | S4 |
| I5 / I5b (proposed scope) | no V-SELECTED on raise; diagnostic only | test/offline/test_o5_evidence_builder.py | S2/S3 simulated |
| T04a | selector candidates=[] ⇒ all-zero counts | test/offline/test_o5_macro_news_filter.py | S1 — complete, unchanged |
| Real JSONL persistence + filesystem failure | deferred | S5 sink | S5 |
| T17 | p95 ≤ 100 ms | perf harness | S6 |
## Genuine remaining decisions
F — approve the new case ID T04d (filtered-to-zero adapter case); no existing ID covers it.
A — review the candidate-ID hash design in Execution §4(a). It is reproducible from the current article shape and the DEV20 metadata; only if A requires preferring a vendor-supplied id would a different rule be needed.
D — exact filter-unavailable wording (blocks the invariant path and T04d's filtered-empty text).
D — negation contract: registry says only "a negation flag"; S1's negated is internal; the external field name/type is undecided.
A + F — simulated I5/I5b scope: adding in-memory construction/emit failure checks to this batch, real persistence deferred to S5. Not approved.
Awaiting F's test-plan review and A's execution-plan review before implementation. No implementation or test code has been edited or run.
