# Requirements Trace Matrix — Evidence-Limited Draft

Owner: C. Prepared 2026-11-22. Intended repository path: `docs/architecture/trace-matrix.md`.

## Baseline and interpretation

- Source/Registry snapshot: `252fe311d8d1483b5713de69b04ce2769c33f1dd`. All 97 Registry entries are retained below without changing IDs, fit criteria or approval status.
- [Registry](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml). Statement and fit criterion are copied separately under each entry; source-code lists from Registry are explicitly distinguished from actual implementation observations.
- [Existing CI run](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013): Python 3.11/3.12/3.13/3.14 test jobs were independently observed as success. This is suite-level evidence, not a per-node pass transcript or proof that every requirement is satisfied. Detailed anonymous log download returned403. No tests or collection were executed for this document.
- Full node references identify source-declared test functions; parametrized suffixes are intentionally not invented. Presence is not a new execution result. Non-O3 matches are cross-references recovered from explicit case IDs in names/docstrings and need B/F assertion-level review.
- The old Team-O1-O6 catalogue is a review draft, not execution or approval evidence. It is used as historical context only.
- **S6 development is stopped. REQ-O5-10/T17 is not accepted as satisfied.** Do not erase this requirement or count ordinary selector correctness as performance evidence.
- No repository files, approvals, CI, tests, or business code were modified. This artifact is prepared outside the source checkout; no commit/push/PR was created.

## O3 overview — all15 requirements

| Requirement | Actual component/functions | Declared automated node references | Evidence boundary / remaining item |
|---|---|---|---|
| O3-FR-01 | parse_source; _parse_news; _parse_stocktwits; _parse_reddit; condense_source; create_sentiment_analyst | `test/offline/test_input_condensation.py::test_T_E6_unknown_shape_becomes_one_item`<br>`test/offline/test_input_condensation.py::test_T_N8_real_formatter_contract_and_source_structure`<br>`test/offline/test_input_condensation.py::test_T_N8_reddit_groups_keep_headers_and_omission_marker`<br>`test/offline/test_input_condensation.py::test_T_N8_stocktwits_summary_is_prologue_and_reports_trims` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-02 | _dedupe; _matchable_title; _jaccard; condense_source | `test/offline/test_input_condensation.py::test_T_B6_T_B7_near_duplicate_threshold`<br>`test/offline/test_input_condensation.py::test_T_B7_jaccard_below_threshold_is_not_merged`<br>`test/offline/test_input_condensation.py::test_T_B8_empty_link_and_title_do_not_match`<br>`test/offline/test_input_condensation.py::test_T_N1_exact_duplicates_collapse_with_counts`<br>`test/offline/test_input_condensation.py::test_T_N4_cross_source_duplicates_are_preserved` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-03 | _rank; condense_source | `test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-04 | validate_caps; condense_source; _truncate_news; _fit_flat; _fit_reddit | `test/offline/test_input_condensation.py::test_PR14_2_node_rejects_caps_summing_over_total`<br>`test/offline/test_input_condensation.py::test_T_B2_exactly_at_cap_is_not_truncated`<br>`test/offline/test_input_condensation.py::test_T_B3_one_char_over_cap_still_fits`<br>`test/offline/test_input_condensation.py::test_T_B5_single_oversized_item_is_truncated_or_dropped`<br>`test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order`<br>`test/offline/test_input_condensation.py::test_T_N7_invalid_caps_raise_and_oversized_block_is_condensed` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-05 | create_sentiment_analyst; _build_system_message; _is_placeholder; condense_source | `test/offline/test_input_condensation.py::test_T_E2_unavailable_placeholder_is_kept_verbatim`<br>`test/offline/test_input_condensation.py::test_T_N5_node_prompt_keeps_identity_date_and_safety_text` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-06 | CondensationReport; safe_id; report_as_dict; render_audit_footer | `test/offline/test_input_condensation.py::test_T_E6_unknown_shape_becomes_one_item`<br>`test/offline/test_input_condensation.py::test_T_N1_exact_duplicates_collapse_with_counts`<br>`test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-07 | condense_source(count_tokens=…); render_audit_footer | `test/offline/test_input_condensation.py::test_T_E5_absent_tokenizer_reports_none`<br>`test/offline/test_input_condensation.py::test_T_E7_optional_tokenizer_estimates_decrease`<br>`test/offline/test_input_condensation.py::test_T_N6_character_reduction_is_reported_as_chars` | Character claims supported by code/tests; T-R3 provider-usage evidence not linked. Token estimates are not provider usage. |
| O3-FR-08 | DEFAULT_CONFIG; get_config; validate_caps; create_sentiment_analyst | `test/offline/test_input_condensation.py::test_T_E4_invalid_config_raises_value_error`<br>`test/offline/test_input_condensation.py::test_T_R2_disabled_condensation_is_byte_identical` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-FR-09 | condense_source(count_tokens=None) | `test/offline/test_input_condensation.py::test_T_E5_absent_tokenizer_reports_none` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-NFR-01 | _rank; _dedupe; condense_source | `test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order`<br>`test/offline/test_input_condensation.py::test_T_R2_disabled_condensation_is_byte_identical`<br>`test/offline/test_input_condensation.py::test_T_R4_repeat_and_recondense_are_stable` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-NFR-02 | condense_source (measurement target; no production performance threshold) | No automated node: manual record required. | Manual diagnostic FC-14: elapsed time, peak memory, fixed200000-character fixture hash and runner ID. No verified record linked here; not an automated PASS. |
| O3-NFR-03 | condense_source; create_sentiment_analyst (fake fetchers in offline tests) | `test/offline/test_input_condensation.py::test_R5_T_R5_direct_condenser_makes_no_network_calls`<br>`test/offline/test_input_condensation.py::test_R5_T_R5_node_makes_no_network_calls`<br>`test/offline/test_input_condensation.py::test_T_R1_collected_cases_are_present` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-NFR-04 | CondensationError; condense_source; create_sentiment_analyst fallback | `test/offline/test_input_condensation.py::test_FC5_node_keeps_original_news_block_when_protected_text_over_cap`<br>`test/offline/test_input_condensation.py::test_T_B4_protected_content_over_cap_falls_back`<br>`test/offline/test_input_condensation.py::test_T_E3_node_survives_a_condenser_fault` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-NFR-05 | safe_id; RemovalRecord; report_as_dict; counts-only audit logging | `test/offline/test_input_condensation.py::test_T_E8_audit_and_logs_hold_no_raw_content` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |
| O3-NFR-06 | create_sentiment_analyst; disabled input path; existing fetcher call pattern | `test/offline/test_input_condensation.py::test_PR14_1_disabled_matches_pre_o3_golden_byte_for_byte`<br>`test/offline/test_input_condensation.py::test_PR14_1_fetchers_keep_pre_o3_calls`<br>`test/offline/test_input_condensation.py::test_T_R1_collected_cases_are_present`<br>`test/offline/test_input_condensation.py::test_T_R2_disabled_condensation_is_byte_identical` | Source nodes located; suite-level CI evidence only. B/F to confirm full assertion coverage. |

### O3 runtime monitoring and fallback

Per-source `CondensationReport` provides input/output item counts, duplicate/drop/truncation counts, before/after characters, parse fallbacks and budget exception; `render_audit_footer` provides bounded human-readable context. Token fields are optional. Protected-content overflow falls back to the original affected source and must not count as a budget pass. Other parse/input failures are distinguished from budget overflow. No automatic performance or financial-quality monitor is claimed.

### Known Registry implementation-location discrepancy

O3 Registry `source_code` points to sentiment_analyst.py and yahoo/news.py. The pure implementation actually lives in `tradingagents/agents/analysts/condensation.py`, with defaults in `tradingagents/default_config.py`. O2 Registry similarly includes Graph paths but actual manifest implementation is `tradingagents/repro/manifest.py` plus CLI. This draft records both without editing B's Registry.

## Full Registry inventory and recovered mappings

Each entry contains the original statement/fit criterion, enforcing-component locations, declared node references, unresolved verification labels, runtime observation and coverage boundaries. Other-module locations below are module-level, not newly asserted exact function contracts.


## O1

### REQ-O1-01

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** On the Yahoo SMA path, a 50-session SMA is numeric only with at least 50 cleaned, non-missing dated closes through the reported date; with 1–49 usable closes return the exact insufficient-history text. An empty/no-close frame retains the existing no-market-data outcome.

**Fit criterion:** 49 usable closes -> N/A: insufficient history (needs 50 sessions, have 49); 50 -> latest-50 dated-close mean with absolute error <= 1e-6 before display formatting; an all-missing-close frame yields NO_DATA_AVAILABLE through the routed tool.

**Registry verification labels:** `T-O1-01`, `T-O1-02`, `T-O1-03`, `T-O1-05`, `T-O1-06`, `T-O1-09`, `T-O1-10`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o1_sma_guard.py::test_t_o1_01_bulk_40_and_49`

- `test/offline/test_o1_sma_guard.py::test_t_o1_02_bulk_50_and_60`

- `test/offline/test_o1_sma_guard.py::test_t_o1_03_bulk_199_200_220`

- `test/offline/test_o1_sma_guard.py::test_t_o1_05_snapshot_boundaries`

- `test/offline/test_o1_sma_guard.py::test_t_o1_06_fallback_guard`

- `test/offline/test_o1_sma_guard.py::test_t_o1_09_real_loader_missing_close`

- `test/offline/test_o1_sma_guard.py::test_t_o1_10_all_closes_missing`

**Runtime monitor/fallback:** Unavailable/invalid-history indicator output. No separate continuous monitor established here.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O1-02

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** On the Yahoo SMA path, a 200-session SMA is numeric only with at least 200 cleaned, non-missing dated closes through the reported date; with 1–199 usable closes return the exact insufficient-history text. An empty/no-close frame retains the existing no-market-data outcome.

**Fit criterion:** 199 usable closes -> N/A: insufficient history (needs 200 sessions, have 199); 200 -> latest-200 dated-close mean with absolute error <= 1e-6 before display formatting; an all-missing-close frame yields NO_DATA_AVAILABLE through the routed tool.

**Registry verification labels:** `T-O1-01`, `T-O1-02`, `T-O1-03`, `T-O1-05`, `T-O1-06`, `T-O1-09`, `T-O1-10`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o1_sma_guard.py::test_t_o1_01_bulk_40_and_49`

- `test/offline/test_o1_sma_guard.py::test_t_o1_02_bulk_50_and_60`

- `test/offline/test_o1_sma_guard.py::test_t_o1_03_bulk_199_200_220`

- `test/offline/test_o1_sma_guard.py::test_t_o1_05_snapshot_boundaries`

- `test/offline/test_o1_sma_guard.py::test_t_o1_06_fallback_guard`

- `test/offline/test_o1_sma_guard.py::test_t_o1_09_real_loader_missing_close`

- `test/offline/test_o1_sma_guard.py::test_t_o1_10_all_closes_missing`

**Runtime monitor/fallback:** Unavailable/invalid-history indicator output. No separate continuous monitor established here.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O1-03

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** Count cleaned, non-missing closes separately for each reported date. Sort dated closes chronologically for the SMA-only calculation; exclude rows after the analysis date. A duplicate trading date is an invalid SMA input and must never produce a numeric SMA.

**Fit criterion:** At row/date 60 of a 260-date frame, 50-SMA is the latest-50 mean and 200-SMA is insufficient with count 60; shuffled unique-date input produces the same dated SMA values; duplicate-date input returns N/A: invalid price history (duplicate trading date).

**Registry verification labels:** `T-O1-04`, `T-O1-11`, `T-O1-12`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o1_sma_guard.py::test_t_o1_04_early_date_uses_its_own_history`

- `test/offline/test_o1_sma_guard.py::test_t_o1_11_shuffled_and_future_rows`

- `test/offline/test_o1_sma_guard.py::test_t_o1_12_duplicate_date_rejected`

**Runtime monitor/fallback:** Unavailable/invalid-history indicator output. No separate continuous monitor established here.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O1-04

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** When the yfinance/stockstats vendor serves the indicator (the shipped technical-indicators default, default_config.py:160), apply REQ-O1-01 and REQ-O1-02 on the bulk indicator path, the per-day fallback, and the verified snapshot. Alpha Vantage and any other configured indicator vendor remain outside O1.

**Fit criterion:** On the Yahoo path, each of the bulk, fallback, and snapshot entry points reports insufficient history for 49/199 sessions and a valid value at the corresponding 50/200 boundary.

**Registry verification labels:** `T-O1-01`, `T-O1-02`, `T-O1-03`, `T-O1-05`, `T-O1-06`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o1_sma_guard.py::test_t_o1_01_bulk_40_and_49`

- `test/offline/test_o1_sma_guard.py::test_t_o1_02_bulk_50_and_60`

- `test/offline/test_o1_sma_guard.py::test_t_o1_03_bulk_199_200_220`

- `test/offline/test_o1_sma_guard.py::test_t_o1_05_snapshot_boundaries`

- `test/offline/test_o1_sma_guard.py::test_t_o1_06_fallback_guard`

**Runtime monitor/fallback:** Unavailable/invalid-history indicator output. No separate continuous monitor established here.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O1-05

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** Leave non-SMA indicators' behavior unchanged.

**Fit criterion:** For a controlled frame, each selected non-SMA output equals the same-run direct stockstats reference; the prior regression suite has zero new failures.

**Registry verification labels:** `T-O1-07`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o1_sma_guard.py::test_t_o1_07_non_sma_unchanged`

**Runtime monitor/fallback:** Unavailable/invalid-history indicator output. No separate continuous monitor established here.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O1-06

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Use an exact insufficient-history message distinct from the existing non-trading-day and no-market-data outcomes; duplicate dates use a separate invalid-history message.

**Fit criterion:** Exact insufficient-history text is N/A: insufficient history (needs W sessions, have N), with W and N replaced by integers. Duplicate dates yield N/A: invalid price history (duplicate trading date). A date absent from the cleaned loader output retains the existing non-trading-day text. No output test confuses these states.

**Registry verification labels:** `T-O1-08`, `T-O1-10`, `T-O1-12`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/market.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/market.py), [tradingagents/dataflows/vendors/yahoo/snapshot.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/snapshot.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o1_sma_guard.py::test_t_o1_08_distinct_messages`

- `test/offline/test_o1_sma_guard.py::test_t_o1_10_all_closes_missing`

- `test/offline/test_o1_sma_guard.py::test_t_o1_12_duplicate_date_rejected`

**Runtime monitor/fallback:** Unavailable/invalid-history indicator output. No separate continuous monitor established here.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).


## O2

### O2-FR-01

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** For every completed CLI invocation, attempt one JSON provenance manifest. On success show its unique path; on write failure keep the analysis result but show a manifest-failed warning and do not claim saved provenance.

**Fit criterion:** Two successful same-ticker/date runs retain two readable manifests; an injected write failure leaves the gated analysis rating unchanged, visibly reports provenance unavailable and publishes no manifest path.

**Registry verification labels:** `O2-TC-01`, `O2-TC-04`, `O2-TC-13`, `O2-TC-14`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_01_manifest_has_required_fields_and_is_writable`

- `test/offline/test_o2_manifest.py::test_o2_tc_13_serialization_failure_leaves_no_partial_manifest`

- `test/offline/test_o2_manifest.py::test_o2_tc_14_promotion_failure_leaves_no_partial_manifest`

**Unresolved labels / manual references:** `O2-TC-04`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-02

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Generate one collision-resistant invocation ID per run, distinguishing same-ticker/date and same-second invocations.

**Fit criterion:** Two same-ticker/date invocations retain two independently readable manifests. Two invocations in the same second have distinct IDs.

**Registry verification labels:** `O2-TC-04`, `O2-TC-11`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O2-TC-04`, `O2-TC-11`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-03

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Reserve a unique run directory at <config[results_dir]>/<safe_ticker>/<analysis_date>/runs/<uuid4>/ and write manifest.json there without replacing a prior run directory or manifest.

**Fit criterion:** Two invocations with identical ticker/date and frozen second reserve distinct directories and retain byte-readable manifest.json files; an existing UUID collision is retried, never overwritten.

**Registry verification labels:** `O2-TC-04`, `O2-TC-11`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O2-TC-04`, `O2-TC-11`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-04

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Record normalized ticker, asset type, ISO analysis date and selected Analyst keys. Do not store the raw ticker separately.

**Fit criterion:** Manifest identity contains exactly the normalized four fields and no raw-ticker field.

**Registry verification labels:** `O2-TC-22`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_22_identity_contains_only_approved_fields`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-05

**Registry type / priority / status:** security / Must / selected_for_development

**Statement:** Serialize only the consolidated effective-configuration allowlist named in development_contract.o2_config_allowlist; omit absent values explicitly and never serialize a full config or environment.

**Fit criterion:** For a fixture containing every allowlisted field plus secrets and unknown fields, JSON contains the allowed non-secret fields with correct values and excludes every unlisted field and credential.

**Registry verification labels:** `O2-TC-06`, `O2-TC-23`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_06_secret_fields_and_unapproved_keys_are_excluded`

- `test/offline/test_o2_manifest.py::test_o2_tc_23_only_merged_allowlist_is_serialized`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-06

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Record package/runtime identity and Git commit/dirty state when available. Represent missing values explicitly; never fabricate them.

**Fit criterion:** Missing Git/model metadata is explicit, and available package/runtime values are recorded.; Package version, Python version, and platform are recorded when available.

**Registry verification labels:** `O2-TC-08`, `O2-TC-09`, `O2-TC-17`, `O2-TC-24`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_08_git_unavailable_is_explicit`

- `test/offline/test_o2_manifest.py::test_o2_tc_09_missing_model_and_provider_are_explicit`

- `test/offline/test_o2_manifest.py::test_o2_tc_17_git_lookup_error_is_explicit`

- `test/offline/test_o2_manifest.py::test_o2_tc_24_runtime_metadata_is_recorded_or_explicitly_missing`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-07

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Compute SHA-256 over canonical UTF-8 JSON of normalized identity fields and the consolidated effective-configuration allowlist. Use sorted keys, no ASCII escaping, comma/colon separators, finite JSON numbers only, ISO analysis date and fixed Analyst order.

**Fit criterion:** Reordered mapping keys yield an identical 64-hex fingerprint; changing any included field changes it; excluded run ID/timestamp/artifact/output/payload fields do not; NaN/Infinity input is rejected.

**Registry verification labels:** `O2-TC-02`, `O2-TC-03`, `O2-TC-12`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_02_nan_and_infinity_are_rejected`

- `test/offline/test_o2_manifest.py::test_o2_tc_02_reordered_config_has_identical_fingerprint`

- `test/offline/test_o2_manifest.py::test_o2_tc_03_included_fields_change_fingerprint_but_excluded_fields_do_not`

- `test/offline/test_o2_manifest.py::test_o2_tc_12_raw_ticker_variants_normalize_identically`

- `test/offline/test_o2_manifest.py::test_o2_tc_12_selected_analysts_use_canonical_order_for_identity_and_config`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-08

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Exclude run ID, timestamps, duration, artifact paths, secrets, and market/news payloads from the deterministic fingerprint.

**Fit criterion:** Changing an included field changes the fingerprint; excluded fields do not.; Run ID and volatile timestamps do not affect deterministic fingerprint.

**Registry verification labels:** `O2-TC-03`, `O2-TC-12`, `O2-TC-02`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_02_nan_and_infinity_are_rejected`

- `test/offline/test_o2_manifest.py::test_o2_tc_02_reordered_config_has_identical_fingerprint`

- `test/offline/test_o2_manifest.py::test_o2_tc_03_included_fields_change_fingerprint_but_excluded_fields_do_not`

- `test/offline/test_o2_manifest.py::test_o2_tc_12_raw_ticker_variants_normalize_identically`

- `test/offline/test_o2_manifest.py::test_o2_tc_12_selected_analysts_use_canonical_order_for_identity_and_config`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-09

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** If no immutable per-run market/news snapshot exists, record actual_input_data_provenance: not_captured; do not call the fingerprint a data hash.

**Fit criterion:** Without immutable snapshot, provenance is exactly not_captured; no data-hash/full-reproducibility claim.

**Registry verification labels:** `O2-TC-07`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_07_data_provenance_is_not_captured_and_fingerprint_is_not_data`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-10

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Reference agreed artifacts using relative paths where possible and label each run_unique, shared_mutable, or not_persisted.

**Fit criterion:** Every artifact reference has the correct stability label.

**Registry verification labels:** `O2-TC-05`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_05_artifact_stability_labels_and_relative_paths`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-11

**Registry type / priority / status:** security / Must / selected_for_development

**Statement:** Exclude API keys, tokens, passwords, credential-bearing URLs, unrelated environment variables, and other secrets.

**Fit criterion:** No unapproved config fields or secret values appear in manifest.

**Registry verification labels:** `O2-TC-06`, `O2-TC-16`, `O2-TC-23`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_06_secret_fields_and_unapproved_keys_are_excluded`

- `test/offline/test_o2_manifest.py::test_o2_tc_16_credential_in_url_query_is_redacted_from_manifest_and_fingerprint`

- `test/offline/test_o2_manifest.py::test_o2_tc_16_nested_secret_and_credential_url_are_redacted`

- `test/offline/test_o2_manifest.py::test_o2_tc_23_only_merged_allowlist_is_serialized`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-12

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Include an agreed schema version and stable field names.

**Fit criterion:** In-scope completed invocation creates one valid manifest with required fields/schema version.; Manifest contains the agreed schema-version field and value.

**Registry verification labels:** `O2-TC-01`, `O2-TC-25`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_01_manifest_has_required_fields_and_is_writable`

- `test/offline/test_o2_manifest.py::test_o2_tc_25_schema_version_is_1_0_0`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-13

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Write valid JSON atomically, leaving no partial manifest after interruption/failure.

**Fit criterion:** Manifest JSON is first written to a temporary file inside its reserved run directory and atomically promoted to manifest.json; injected write/promotion failure leaves no partial manifest.json and a visible provenance-failed status.

**Registry verification labels:** `O2-TC-13`, `O2-TC-14`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_13_serialization_failure_leaves_no_partial_manifest`

- `test/offline/test_o2_manifest.py::test_o2_tc_14_promotion_failure_leaves_no_partial_manifest`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-FR-14

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** A manifest-write failure is fail-soft for the gated analysis result but fail-closed for provenance claims: show a visible warning, leave no partial JSON, and do not publish a manifest path.

**Fit criterion:** On injected write failure, the O4 effective rating remains unchanged, CLI shows manifest failed, no partial manifest.json exists and no success path or full-provenance claim is shown.

**Registry verification labels:** `O2-TC-13`, `O2-TC-14`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_13_serialization_failure_leaves_no_partial_manifest`

- `test/offline/test_o2_manifest.py::test_o2_tc_14_promotion_failure_leaves_no_partial_manifest`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-01

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Use only the Python standard library for the manifest writer and fingerprint.

**Fit criterion:** Dependency diff for the O2 change contains zero new third-party runtime packages.

**Registry verification labels:** `O2-TC-18`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O2-TC-18`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-02

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Canonicalization is deterministic: sorted keys, stable separators, UTF-8, documented normalization.

**Fit criterion:** Same normalized included inputs/config yield identical fingerprint independent of key order.

**Registry verification labels:** `O2-TC-02`, `O2-TC-10`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_02_nan_and_infinity_are_rejected`

- `test/offline/test_o2_manifest.py::test_o2_tc_02_reordered_config_has_identical_fingerprint`

- `test/offline/test_o2_manifest.py::test_o2_tc_10_empty_optional_fields_unicode_and_nan_rejection`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-03

**Registry type / priority / status:** security / Must / selected_for_development

**Statement:** Use an allowlist; serialized output contains no secrets.

**Fit criterion:** No unapproved config fields or secret values appear in manifest.

**Registry verification labels:** `O2-TC-06`, `O2-TC-16`, `O2-TC-23`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_06_secret_fields_and_unapproved_keys_are_excluded`

- `test/offline/test_o2_manifest.py::test_o2_tc_16_credential_in_url_query_is_redacted_from_manifest_and_fingerprint`

- `test/offline/test_o2_manifest.py::test_o2_tc_16_nested_secret_and_credential_url_are_redacted`

- `test/offline/test_o2_manifest.py::test_o2_tc_23_only_merged_allowlist_is_serialized`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-04

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Tests run offline without live vendors, market data, or LLM calls.

**Fit criterion:** Manifest tests use fakes and run without network/vendor/market-data/LLM access.

**Registry verification labels:** `O2-TC-19`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_19_manifest_writer_runs_offline`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-05

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Path reservation, atomic promotion and JSON serialization work on Ubuntu, macOS and Windows using the same public behavior.

**Fit criterion:** O2 offline path/JSON test job passes on ubuntu-latest, macos-latest and windows-latest.

**Registry verification labels:** `O2-TC-21`, `O2-TC-10`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_10_empty_optional_fields_unicode_and_nan_rejection`

**Unresolved labels / manual references:** `O2-TC-21`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-06

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Manifest integration is additive: report, memory-log, checkpoint and public API behavior remain unchanged, apart from the explicit visible manifest status.

**Fit criterion:** All prior suites pass; no public signature is removed or renamed; shared-mutable artifacts are never labelled run-unique without proof.

**Registry verification labels:** `O2-TC-20`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O2-TC-20`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O2-NFR-07

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Manifest is human-readable JSON with documented stable keys.

**Fit criterion:** JSON parses, required keys exist, and keys match documented schema.

**Registry verification labels:** `O2-TC-01`

**Registry source_code:** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py), [tradingagents/repro/manifest.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/repro/manifest.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o2_manifest.py::test_o2_tc_01_manifest_has_required_fields_and_is_writable`

**Runtime monitor/fallback:** Manifest success/failure output and artifact references; run reservation. Failure contract must preserve honest analysis and avoid false provenance claims.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).


## O3

### O3-FR-01

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** The feature applies to exactly one point in the pipeline: the inputs of the Sentiment Analyst (sentiment_analyst.py::create_sentiment_analyst). It must be a pure function callable without network access, so it is testable and reusable. Other agents are out of scope for O3. Maintain one text-shape fixture per source and a contract test that fails if the shared news formatter changes shape.

**Fit criterion:** Verify all three known source shapes. A formatter shape change fails the contract test. At runtime an unknown block enters budgeting as one item, with parse_fallbacks > 0.

**Registry verification labels:** `T-N8`, `T-E6`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** parse_source; _parse_news; _parse_stocktwits; _parse_reddit; condense_source; create_sentiment_analyst

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E6_unknown_shape_becomes_one_item`

- `test/offline/test_input_condensation.py::test_T_N8_real_formatter_contract_and_source_structure`

- `test/offline/test_input_condensation.py::test_T_N8_reddit_groups_keep_headers_and_omission_marker`

- `test/offline/test_input_condensation.py::test_T_N8_stocktwits_summary_is_prologue_and_reports_trims`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-02

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Before the prompt is built, exact and near-duplicate items within a source are collapsed to one representative: - exact duplicate = same link (non-empty), or same normalised title; - near duplicate = same publisher and title token Jaccard similarity ≥ 0.8. Keep the first occurrence in the source block. Preserve duplicates across sources. Empty links and empty normalized titles do not establish a match.

**Fit criterion:** An input where the identical article appears 3× yields exactly 1 copy; duplicates_removed == 2; the kept item's link is in the output.; Same-publisher titles at Jaccard 0.85 retain the first occurrence.; The same headline in news and StockTwits is not merged; both survive.

**Registry verification labels:** `T-N1`, `T-N4`, `T-B6`, `T-B7`, `T-B8`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** _dedupe; _matchable_title; _jaccard; condense_source

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_B6_T_B7_near_duplicate_threshold`

- `test/offline/test_input_condensation.py::test_T_B7_jaccard_below_threshold_is_not_merged`

- `test/offline/test_input_condensation.py::test_T_B8_empty_link_and_title_do_not_match`

- `test/offline/test_input_condensation.py::test_T_N1_exact_duplicates_collapse_with_counts`

- `test/offline/test_input_condensation.py::test_T_N4_cross_source_duplicates_are_preserved`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-03

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Rank items mentioning the ticker or a resolved identity term first. Preserve original block order within each rank. Retain a prefix of the ranked items. The formatted v1 interface carries no reliable publication date.

**Fit criterion:** Retain ticker/identity matches first and break ties in original block order.

**Registry verification labels:** `T-N3`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** _rank; condense_source

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-04

**Registry type / priority / status:** cost / Must / selected_for_development

**Statement:** Apply one total character budget and three explicit source caps. Defaults are 24,000 total and 12,000 / 6,000 / 6,000 for news / StockTwits / Reddit. Reject invalid caps or a sum exceeding the total with ValueError. Unused capacity stays with its source. Count rendered separators and any truncation marker. Drop lower-ranked whole items first, then truncate at most one ordinary summary at a word boundary if it fits with …[truncated]. Otherwise drop that item. Reserve space for protected placeholders. Measure static prompt text and the audit footer separately.

**Fit criterion:** Each source fits its cap and the three rendered blocks fit the total. Footer is ≤ 240 characters separately. A budget exception cannot pass FC-5. Defaults are total 24000, news 12000, StockTwits 6000, Reddit 6000 characters; all rendered blocks respect their caps except an explicitly recorded budget-exception fallback.

**Registry verification labels:** `T-N3`, `T-N7`, `T-B2`, `T-B3`, `T-B5`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** validate_caps; condense_source; _truncate_news; _fit_flat; _fit_reddit

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_PR14_2_node_rejects_caps_summing_over_total`

- `test/offline/test_input_condensation.py::test_T_B2_exactly_at_cap_is_not_truncated`

- `test/offline/test_input_condensation.py::test_T_B3_one_char_over_cap_still_fits`

- `test/offline/test_input_condensation.py::test_T_B5_single_oversized_item_is_truncated_or_dropped`

- `test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order`

- `test/offline/test_input_condensation.py::test_T_N7_invalid_caps_raise_and_oversized_block_is_condensed`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-05

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** The following must be present in the final prompt unchanged, and the condensation step must fail closed if it would remove them: - the exact-ticker identity sentence produced by build_instrument_context (context.py:107-169), i.e. the current instrument_context string, injected at sentiment_analyst.py:97,107; - the analysis date (trade_date) as injected by the prompt template (Today's date is {current_date}, sentiment_analyst.py:97,106); - the safety/scope constraints that are already part of the system message: the NO_EXTERNAL_TOOLS block (structured.py:36-39), the "Report what your tools support; another agent decides the trade." sentence (sentiment_analyst.py:93), and the prompt template text itself — O3 condenses only the three interpolated data blocks ({news_block}, {stocktwits_block}, {reddit_block}), never the system message; - any <unavailable> / "not an absence of news" placeholder from a fetcher — an absence marker is never condensed away or counted as a duplicate.

**Fit criterion:** FC-6a checks unchanged identity, date and safety text in the captured node prompt. FC-6b checks verbatim placeholder preservation at function level.

**Registry verification labels:** `T-N5`, `T-E2`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** create_sentiment_analyst; _build_system_message; _is_placeholder; condense_source

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E2_unavailable_placeholder_is_kept_verbatim`

- `test/offline/test_input_condensation.py::test_T_N5_node_prompt_keeps_identity_date_and_safety_text`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-06

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Return per-source counts for items in/out, duplicates, drops, truncations, characters before/after, and parser fallbacks. Record each affected item with a stable non-secret identifier and reason. INFO logs contain counts only. When enabled, append an audit footer of at most 240 characters, measured separately from the source budget. Unknown block shapes enter budgeting as a single item and increment parse_fallbacks.

**Fit criterion:** items_in - items_out == duplicates_removed + items_dropped; len(removals) == duplicates_removed + items_dropped + items_truncated. Every affected item has a stable safe ID and INFO logs contain counts only.

**Registry verification labels:** `T-N1`, `T-N3`, `T-E6`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** CondensationReport; safe_id; report_as_dict; render_audit_footer

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E6_unknown_shape_becomes_one_item`

- `test/offline/test_input_condensation.py::test_T_N1_exact_duplicates_collapse_with_counts`

- `test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-07

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** We may claim input length reduction measured in characters (deterministic, offline). We may claim token reduction only when measured by one of: (a) an offline tokenizer whose encode(text) length is recorded and labelled as an estimate; (b) real provider usage data from a test/live/ run, recorded in the transcript. Character counts must never be labelled "tokens" in code, logs or the report.

**Fit criterion:** A fixture with 3× duplication reports a character reduction ≥ 30 %; the report never emits the word "token" for that figure.; With the offline tokenizer, the estimated token count strictly decreases on the same fixture; without it, tokens_after is None and no token claim is made.

**Registry verification labels:** `T-N6`, `T-E5`, `T-E7`, `T-R3`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** condense_source(count_tokens=…); render_audit_footer

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E5_absent_tokenizer_reports_none`

- `test/offline/test_input_condensation.py::test_T_E7_optional_tokenizer_estimates_decrease`

- `test/offline/test_input_condensation.py::test_T_N6_character_reduction_is_reported_as_chars`

**Unresolved labels / manual references:** `T-R3`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-08

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** All knobs live in DEFAULT_CONFIG and are read through dataflows.config.get_config() so run_config/TRADINGAGENTS_* overrides work: input_condensation_enabled (True), input_budget_chars (total), three explicit source caps, input_near_dup_jaccard (0.8), input_condensation_audit_note (True). When input_condensation_enabled is False the prompt is byte-identical to the baseline.

**Fit criterion:** input_condensation_enabled=False → output equals baseline string exactly (golden test). Default enabled=True and audit_note=True; disabling reproduces the baseline prompt byte-for-byte.

**Registry verification labels:** `T-R2`, `T-E4`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** DEFAULT_CONFIG; get_config; validate_caps; create_sentiment_analyst

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E4_invalid_config_raises_value_error`

- `test/offline/test_input_condensation.py::test_T_R2_disabled_condensation_is_byte_identical`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-FR-09

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Token counting is behind an optional interface count_tokens(text) -> int \| None. With no tokenizer installed it returns None and the run still works, reporting characters only. We do not add tiktoken to core dependencies; if used, it goes in a dev/optional extra (see Open Questions).

**Fit criterion:** With the offline tokenizer, the estimated token count strictly decreases on the same fixture; without it, tokens_after is None and no token claim is made.

**Registry verification labels:** `T-E5`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** condense_source(count_tokens=None)

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E5_absent_tokenizer_reports_none`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-NFR-01

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Same input + same config → identical output bytes. condense(condense(x)) == condense(x).

**Fit criterion:** Two runs on the same fixture produce byte-identical output and equal reports.; Second pass reports duplicates_removed == items_dropped == items_truncated == 0.

**Registry verification labels:** `T-N3`, `T-R2`, `T-R4`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** _rank; _dedupe; condense_source

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_N3_tight_budget_keeps_top_ranked_in_order`

- `test/offline/test_input_condensation.py::test_T_R2_disabled_condensation_is_byte_identical`

- `test/offline/test_input_condensation.py::test_T_R4_repeat_and_recondense_are_stable`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-NFR-02

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Measure and record elapsed time and peak memory on the fixed 200000-character fixture, with SHA-256 fixture fingerprint and runner identifier; this is diagnostic only.

**Fit criterion:** For the 200000-character fixture, record non-negative elapsed time and peak memory, fixture fingerprint, and machine identifier for every measurement; no speed threshold is claimed.

**Registry verification labels:** `FC-14 performance record`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** condense_source (measurement target; no production performance threshold)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `FC-14 performance record`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** MANUAL DIAGNOSTIC EVIDENCE PENDING; ordinary CI cannot substitute. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-NFR-03

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Zero network calls in the condenser and its tests (tests/conftest.py::_no_network already blocks sockets; the condenser must not need an exception). Identity is passed in, not looked up.

**Fit criterion:** Collect and run the offline tests explicitly with pytest -q tests test/offline -m "not integration".

**Registry verification labels:** `T-R1`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** condense_source; create_sentiment_analyst (fake fetchers in offline tests)

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_R5_T_R5_direct_condenser_makes_no_network_calls`

- `test/offline/test_input_condensation.py::test_R5_T_R5_node_makes_no_network_calls`

- `test/offline/test_input_condensation.py::test_T_R1_collected_cases_are_present`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-NFR-04

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** If a protected placeholder exceeds its source cap, raise CondensationError. The node uses the original source block and records budget_exception=True. Exclude that run from budget-pass results. Malformed inputs follow the baseline fallback path and emit a diagnostic. Verify outer prompt integrity at node level.

**Fit criterion:** A protected placeholder longer than its source cap raises CondensationError. The node uses the original source block, records the budget exception and excludes the run from FC-5.

**Registry verification labels:** `T-B4`, `T-E3`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** CondensationError; condense_source; create_sentiment_analyst fallback

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_FC5_node_keeps_original_news_block_when_protected_text_over_cap`

- `test/offline/test_input_condensation.py::test_T_B4_protected_content_over_cap_falls_back`

- `test/offline/test_input_condensation.py::test_T_E3_node_survives_a_condenser_fault`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-NFR-05

**Registry type / priority / status:** security / Must / selected_for_development

**Statement:** Use stable non-secret item identifiers and counts-only INFO logs. Keep raw titles, links, payloads, endpoints and credentials out of persisted audit records.

**Fit criterion:** A fixture containing raw titles, URLs, payload text, endpoints and credentials produces persisted audit and INFO logs containing none of those values; only stable non-secret IDs and counts remain.

**Registry verification labels:** `T-E8`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** safe_id; RemovalRecord; report_as_dict; counts-only audit logging

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_T_E8_audit_and_logs_hold_no_raw_content`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O3-NFR-06

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** No public signature of existing functions changes. Public names of news.py, sentiment_analyst.py's fetcher call pattern, and graph/* are preserved.

**Fit criterion:** input_condensation_enabled=False → output equals baseline string exactly (golden test).; Collect and run the offline tests explicitly with pytest -q tests test/offline -m "not integration".

**Registry verification labels:** `T-R1`, `T-R2`

**Registry source_code:** [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/agents/analysts/condensation.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/condensation.py), [tradingagents/agents/analysts/sentiment_analyst.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/analysts/sentiment_analyst.py), [tradingagents/default_config.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/default_config.py)

**Functions/types:** create_sentiment_analyst; disabled input path; existing fetcher call pattern

**Source-declared nodes linked by case ID:**

- `test/offline/test_input_condensation.py::test_PR14_1_disabled_matches_pre_o3_golden_byte_for_byte`

- `test/offline/test_input_condensation.py::test_PR14_1_fetchers_keep_pre_o3_calls`

- `test/offline/test_input_condensation.py::test_T_R1_collected_cases_are_present`

- `test/offline/test_input_condensation.py::test_T_R2_disabled_condensation_is_byte_identical`

**Runtime monitor/fallback:** CondensationReport / audit footer; see O3 fallback section.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).


## O4

### O4-FR-01

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** The system MUST run a deterministic evidence-completeness check before the rating is treated as a valid result.

**Fit criterion:** Verdict ∈ {valid, review}.

**Registry verification labels:** `O4-T-01`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t01_complete_evidence_preserves_rating`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-02

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** When every selected Analyst report is non-empty under the structural v1 rule, preserve the original Portfolio Manager rating as effective rating; report contents are not certified as factually valid.

**Fit criterion:** For selected Market+News with both reports non-empty, original Overweight remains effective Overweight, even if a report describes limited input; unselected reports do not affect the result.

**Registry verification labels:** `O4-T-01`, `O4-T-09`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t01_complete_evidence_preserves_rating`

- `test/offline/test_evidence_gate.py::test_t09_complete_evidence_keeps_sell`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-03

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** When any required evidence item is missing (field absent) or empty (zero-length or whitespace-only), the effective rating MUST become REVIEW, with an explanation naming each failing item.

**Fit criterion:** Exact failing set; effective REVIEW.

**Registry verification labels:** `O4-T-02`, `O4-T-03`, `O4-T-14`, `O4-T-17`, `O4-T-24`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t02_single_empty_report_forces_review`

- `test/offline/test_evidence_gate.py::test_t02_two_required_reports_empty`

- `test/offline/test_evidence_gate.py::test_t03_empty_plus_whitespace_multi_missing`

- `test/offline/test_evidence_gate.py::test_t03_whitespace_only_is_missing`

- `test/offline/test_evidence_gate.py::test_t14_multi_select_news_missing_unselected_not_flagged`

- `test/offline/test_evidence_gate.py::test_t14_single_select_market_missing`

- `test/offline/test_evidence_gate.py::test_t17_absent_key_is_missing`

- `test/offline/test_evidence_gate.py::test_t24a_filtered_empty_status_does_not_downgrade`

- `test/offline/test_evidence_gate.py::test_t24b_missing_news_report_downgrades`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-05

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** If the original Portfolio Manager rating is already REVIEW, the gate MUST NOT convert it to any tradeable rating.

**Fit criterion:** Effective == REVIEW.

**Registry verification labels:** `O4-T-06`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t06_preexisting_review_not_upgraded`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-06

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Reports from analysts not selected for the run MUST be classified not_required and MUST NOT count as missing evidence.

**Fit criterion:** Statuses == not_required.

**Registry verification labels:** `O4-T-05`, `O4-T-13`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t05_unselected_analysts_not_required`

- `test/offline/test_evidence_gate.py::test_t13_single_analyst_valid`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-07

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Before any rating surface publishes a final recommendation, apply the evidence gate. Buffer Portfolio Manager Buy/Sell report text and message-stream text in CLI until the gate completes. The effective rating is the only authoritative rating on enabled surfaces.

**Fit criterion:** An offline CLI stream containing a pre-gate Buy and a missing selected report publishes no pre-gate Buy; final CLI/report/state/memory surfaces that are enabled show REVIEW and label preserved original text unapproved.

**Registry verification labels:** `O4-T-08`, `O4-T-19`, `O4-T-23`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t19_missing_evidence_review_and_body_preserved`

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Unresolved labels / manual references:** `O4-T-23`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-08

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Evidence classification MUST be deterministic for the same state and selected-analyst set; it MUST NOT depend on network, LLM, clock, or randomness.

**Fit criterion:** 100/100 identical.

**Registry verification labels:** `O4-T-11`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t11_determinism`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-09

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** If the checker experiences a recoverable internal failure (an exception or inability to complete its own computation), the system MUST fail closed to effective_rating = REVIEW, preserve a diagnostic reason, and MUST NOT publish the ungated original tradeable rating. Every enabled final output surface MUST use the same effective_rating. This MUST be distinguished from invalid configuration (O4-FR-15), which aborts publication instead of producing a normal REVIEW.

**Fit criterion:** Fail-closed observed.

**Registry verification labels:** `O4-T-07`, `O4-T-08`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t07_rating_parse_failure_fails_closed`

- `test/offline/test_evidence_gate.py::test_t07_recoverable_failure_fails_closed`

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-10

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** The checker MUST return structured results: per-item status (present/missing/unavailable/not_required), an overall verdict (valid/review), an effective rating, and a diagnostic reason when the outcome is not a clean pass.

**Fit criterion:** Complete statuses; enumerated verdict; reason on non-pass.

**Registry verification labels:** `O4-T-12`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t12_non_pass_has_reason`

- `test/offline/test_evidence_gate.py::test_t12_structured_result_completeness`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-11

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** The required evidence set MUST be derived from the selected-analyst configuration via ANALYST_NODE_SPECS.

**Fit criterion:** Exact set match.

**Registry verification labels:** `O4-T-05`, `O4-T-18`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t05_unselected_analysts_not_required`

- `test/offline/test_evidence_gate.py::test_t18_config_error_beats_rating_failure`

- `test/offline/test_evidence_gate.py::test_t18_empty_selection_raises`

- `test/offline/test_evidence_gate.py::test_t18_unknown_analyst_raises_value_error`

- `test/offline/test_evidence_gate.py::test_t18_unknown_config_not_converted_to_review`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-12

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** The checker MUST NOT mutate final_trade_decision. When the effective rating is REVIEW but the decision body still states a direction (e.g. a Buy/Sell line), only the authoritative rating label is REVIEW; the original body is preserved byte-for-byte, and any surface that shows it MUST label it clearly as unapproved original content (see FR-13).

**Fit criterion:** Byte equality.

**Registry verification labels:** `O4-T-10`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t10_decision_text_preserved`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-13

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** When the effective rating is REVIEW and the original decision body contains a tradeable direction, enabled rating surfaces MUST present the authoritative rating as REVIEW and MUST identify any preserved original Buy/Sell body as unapproved original content, never as an approved recommendation. Under v1 buffering, the original body MUST NOT be published as an authoritative result before the gate (per FR-07). The CLI's current review message (cli/run.py:378–385) describes only an unreadable rating; it MUST be replaced with a cause-neutral review message so an evidence downgrade or rating conflict is not misreported. Any new display element requires interface approval.

**Fit criterion:** Surface rating == REVIEW; body labelled non-authoritative.

**Registry verification labels:** `O4-T-19`, `O4-T-23`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t19_missing_evidence_review_and_body_preserved`

**Unresolved labels / manual references:** `O4-T-23`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-15

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** An unknown analyst key, or an unrecognizable required configuration, is a configuration/contract error. The system MUST abort authoritative rating publication, report the error, and MUST NOT (a) silently classify unknown analysts as not_required, or (b) present the aborted run as a normally completed REVIEW run. If a safe authoritative result cannot be reliably constructed, none is published.

**Fit criterion:** Error raised; no authoritative rating; not reported as normal REVIEW.

**Registry verification labels:** `O4-T-18`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t18_config_error_beats_rating_failure`

- `test/offline/test_evidence_gate.py::test_t18_empty_selection_raises`

- `test/offline/test_evidence_gate.py::test_t18_unknown_analyst_raises_value_error`

- `test/offline/test_evidence_gate.py::test_t18_unknown_config_not_converted_to_review`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-16

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Original-rating precedence and conflict handling: the original rating is final_rating when present; only when it is absent does the system fall back to parsing final_trade_decision. If both sources clearly provide a rating and disagree, this is a rating-consistency error: the gate MUST downgrade effective_rating to REVIEW and preserve the conflict reason. An original REVIEW is never upgraded. After the gate, effective_rating is the single authoritative rating for final return, reporting, persistence, and CLI publication.

**Fit criterion:** Precedence and conflict rules hold.

**Registry verification labels:** `O4-T-25`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t25a_sources_agree_preserved`

- `test/offline/test_evidence_gate.py::test_t25b_body_supplies_rating_when_final_absent`

- `test/offline/test_evidence_gate.py::test_t25c_conflict_downgrades_with_reason`

- `test/offline/test_evidence_gate.py::test_t25d_original_review_stays_review`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-01

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Checker is a pure function of its inputs (no I/O, no LLM, no clock).

**Fit criterion:** Zero such calls; deterministic.

**Registry verification labels:** `O4-T-11`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t11_determinism`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-02

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Checker unit-testable from a plain dict state and a selected-analyst set, with no graph/LLM/network.

**Fit criterion:** Offline execution succeeds.

**Registry verification labels:** `O4-T-15`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t15_offline_import_and_call`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-04

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** The gate fails closed (O4-INV-03/04) and adds no new runtime dependency.

**Fit criterion:** Empty dependency diff; O4-T-07 passes.

**Registry verification labels:** `O4-T-07`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t07_rating_parse_failure_fails_closed`

- `test/offline/test_evidence_gate.py::test_t07_recoverable_failure_fails_closed`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-05

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Backward compatible: with the gate not wired into runtime, existing functions behave unchanged; enabled APIs accept only additive parameters.

**Fit criterion:** Existing tests pass unchanged; no removed/renamed public parameter.

**Registry verification labels:** `O4-T-20`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate_audit.py::test_t20_historical_state_readable_without_effective_rating`

- `test/offline/test_evidence_gate_audit.py::test_t20_pre_gate_provenance_readable_and_unmutated`

- `test/offline/test_evidence_gate_audit.py::test_t20_record_decision_signature_unchanged`

- `test/offline/test_evidence_gate_audit.py::test_t20_stage1_gate_behaviour_preserved`

- `test/offline/test_evidence_gate_audit.py::test_t20_unselected_analysts_not_required_and_unavailable_present`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-06

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** The checker returns structured evidence results to its caller at runtime; durable verdict persistence is deferred.

**Fit criterion:** Every completed checker call returns verdict, effective rating, per-item statuses and a reason on non-pass. Durable verdict persistence is not required in v1.

**Registry verification labels:** `O4-T-08`, `O4-T-21`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_graph_integration.py::test_t21_last_completion_cleared_after_end_checkpoint`

- `test/offline/test_evidence_gate_graph_integration.py::test_t21_last_completion_none_before_gate`

- `test/offline/test_evidence_gate_graph_integration.py::test_t21_last_completion_populated_after_gate`

- `test/offline/test_evidence_gate_graph_integration.py::test_t21_review_verdict_and_reason_observed`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-07

**Registry type / priority / status:** quality_attribute / Should / selected_for_development

**Statement:** Implement one evidence-checker module and the approved graph finalization and CLI buffering integration points, without redesigning LangGraph or changing rating generation.

**Fit criterion:** Change review shows one checker module and only graph finalization, CLI buffering and necessary state/report wiring; no rating-generation rule change.

**Registry verification labels:** `O4-T-22`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O4-T-22`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-08

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Output-surface applicability: consistency applies only to enabled surfaces — HTML only when html=True (reporting.py:92, :116–123), CLI message only on CLI path (cli/run.py:380), state log always via record_decision (trading_graph.py:362, :438–476), memory log only when memory_log_path set (memory/log.py:44–45).

**Fit criterion:** Compared set == enabled set.

**Registry verification labels:** `O4-T-08`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-INV-01

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** No run whose required evidence is incomplete may publish a tradeable rating on any enabled surface; the published rating MUST be the effective rating.

**Fit criterion:** Pre-gate PM text buffered; final enabled ratings all REVIEW.

**Registry verification labels:** `O4-T-02`, `O4-T-08`, `O4-T-19`, `O4-T-23`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t02_single_empty_report_forces_review`

- `test/offline/test_evidence_gate.py::test_t02_two_required_reports_empty`

- `test/offline/test_evidence_gate.py::test_t19_missing_evidence_review_and_body_preserved`

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Unresolved labels / manual references:** `O4-T-23`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-INV-02

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** A pre-existing original REVIEW is never upgraded to a tradeable rating.

**Fit criterion:** Effective == REVIEW.

**Registry verification labels:** `O4-T-06`, `O4-T-25`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t06_preexisting_review_not_upgraded`

- `test/offline/test_evidence_gate.py::test_t25a_sources_agree_preserved`

- `test/offline/test_evidence_gate.py::test_t25b_body_supplies_rating_when_final_absent`

- `test/offline/test_evidence_gate.py::test_t25c_conflict_downgrades_with_reason`

- `test/offline/test_evidence_gate.py::test_t25d_original_review_stays_review`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-INV-03

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** Every enabled rating surface observes the same effective rating; none reads the ungated original rating independently. No raw Portfolio Manager Buy/Sell is published as an approved result before the gate completes.

**Fit criterion:** Equality across enabled surfaces.

**Registry verification labels:** `O4-T-08`, `O4-T-23`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Unresolved labels / manual references:** `O4-T-23`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-INV-04

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** On a recoverable internal checker failure, the effective rating MUST be REVIEW, a diagnostic reason is preserved, every enabled surface uses that effective_rating, and the ungated original rating is never published. This is distinct from a configuration error (O4-FR-15), which aborts publication rather than producing a normal REVIEW.

**Fit criterion:** Matches fail-closed policy.

**Registry verification labels:** `O4-T-07`, `O4-T-08`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t07_rating_parse_failure_fails_closed`

- `test/offline/test_evidence_gate.py::test_t07_recoverable_failure_fails_closed`

- `test/offline/test_evidence_gate_graph_integration.py::test_t08_graph_entrypoint_return_value_is_gated`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_cli_show_renders_gated_state`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_recoverable_checker_failure_real_cli`

- `test/offline/test_evidence_gate_t08_surface_matrix.py::test_t08_surface_matrix`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-INV-05

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** When final_rating and a clearly parsed final_trade_decision rating disagree, the effective rating MUST be REVIEW with a preserved conflict reason; an original REVIEW is never upgraded.

**Fit criterion:** Conflict downgrade observed.

**Registry verification labels:** `O4-T-25`

**Registry source_code:** [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t25a_sources_agree_preserved`

- `test/offline/test_evidence_gate.py::test_t25b_body_supplies_rating_when_final_absent`

- `test/offline/test_evidence_gate.py::test_t25c_conflict_downgrades_with_reason`

- `test/offline/test_evidence_gate.py::test_t25d_original_review_stays_review`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-04

**Registry type / priority / status:** functional_behavior / Won't / selected_for_development

**Statement:** Do not infer whole-report unavailability from non-empty text or single unavailable data items in v1; no whole-report sentinel recognition is implemented.

**Fit criterion:** A non-empty selected report containing N/A or an unavailable-source note is structurally present; O4-T-04 with sentinel recognition disabled does not downgrade solely for that text.

**Registry verification labels:** `O4-T-04`

**Registry source_code:** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate.py::test_t04_unavailable_text_stays_present`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-FR-14

**Registry type / priority / status:** functional_behavior / Won't / selected_for_development

**Statement:** Do not add report-length, content-truth, cross-verification or debate-history rules to the O4 v1 evidence gate.

**Fit criterion:** Manual scope review finds zero such rules; only selected-report presence and rating consistency are checked.

**Registry verification labels:** `O4-T-22`

**Registry source_code:** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O4-T-22`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O4-NFR-03

**Registry type / priority / status:** performance / Should / selected_for_development

**Statement:** The pure evidence checker adds bounded latency without external calls.

**Fit criterion:** On a fixed four-report fixture in the same process, after 5 warmups and 30 measured calls on ubuntu-latest/Python 3.11, nearest-rank p95 added latency is <= 10 ms; report the runner and samples.

**Registry verification labels:** `O4-T-16`

**Registry source_code:** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py)

**Actual implementation locations (files present):** [tradingagents/graph/trading_graph.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/trading_graph.py), [tradingagents/agents/rating.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/agents/rating.py), [tradingagents/reporting.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/reporting.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_evidence_gate_benchmark.py::test_t16_checker_is_pure_no_state_mutation`

- `test/offline/test_evidence_gate_benchmark.py::test_t16_pure_checker_correctness_and_fixed_counts`

- `test/offline/test_evidence_gate_benchmark.py::test_t16_pure_checker_p95_diagnostic`

**Runtime monitor/fallback:** Effective rating/REVIEW and completion-boundary diagnostics. Detailed policies require D/F assertion review.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).


## O5

### REQ-O5-01

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Classify fetched English global-news candidates using O5 rules version o5-rules-v1.1-draft and the versioned rule catalog in development_contract; retrieval query text is context only and never classification evidence.

**Fit criterion:** DEV20 fixed rule fixture yields the selected/rejected IDs and matched rule IDs in the v0.5.3 expected arrays; ticker/company focus alone never excludes a candidate with same-field anchor+context evidence.

**Registry verification labels:** `T01`, `T08e`, `RT-3`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t01_dev20_k20`

**Unresolved labels / manual references:** `T08e`, `RT-3`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-02

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** From qualified fetched candidates, allocate by primary bucket (first requested matched topic), round-robin over request topic order, bucket sort published_at desc, candidate_id asc, each candidate at most once, output ≤ K, fill available slots.

**Fit criterion:** Scheduling deterministic given approved buckets (T01/T02/T05/T06/T19/T20).

**Registry verification labels:** `T01`, `T02`, `T05`, `T06`, `T19`, `T20`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t01_dev20_k20`

- `test/offline/test_o5_macro_news_filter.py::test_t02_dev20_k6`

- `test/offline/test_o5_macro_news_filter.py::test_t05a_mp_only_recent`

- `test/offline/test_o5_macro_news_filter.py::test_t05a_tie_order_by_id`

- `test/offline/test_o5_macro_news_filter.py::test_t05b_mixed_mp_ea_keeps_topic_order`

- `test/offline/test_o5_macro_news_filter.py::test_t06_dev20_k2`

- `test/offline/test_o5_macro_news_filter.py::test_t19_requested_topic_subset_reorders_primary`

- `test/offline/test_o5_macro_news_filter.py::test_t19_single_topic_subset_filters_matched_topics`

- `test/offline/test_o5_macro_news_filter.py::test_t20_no_padding_beyond_available`

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-03

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Explicit honest empty status; no irrelevant padding; K=0 distinct from upstream failure; failure never disguised as success.

**Fit criterion:** T03/T04/T13 distinct.

**Registry verification labels:** `T03`, `T04`, `T13`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t03a_dev20_k0`

- `test/offline/test_o5_macro_news_filter.py::test_t03b_irrelevant_only`

- `test/offline/test_o5_macro_news_filter.py::test_t03c_invalid_titles`

- `test/offline/test_o5_macro_news_filter.py::test_t04a_empty_pool`

- `test/offline/test_o5_macro_news_integration.py::test_s4_t04d_all_irrelevant_uses_the_all_irrelevant_enum_member`

- `test/offline/test_o5_macro_news_integration.py::test_s4_t04d_filtered_to_zero_is_not_upstream_empty`

**Unresolved labels / manual references:** `T13`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-04

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Exactly one decision per input position with matched topics, rule reason, specific reason_code; selected records keep supplied business fields verbatim.

**Fit criterion:** The number of decisions equals the number of supplied input positions, with exactly one decision per position and a matched-topics list, rule reason and specific reason_code for each. Every selected record retains its supplied business fields unchanged.

**Registry verification labels:** `T12`, `I11`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t12_one_decision_per_position`

**Unresolved labels / manual references:** `I11`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-05

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Validate request; validate records per §6.2; map time window per R9; isolate/count damaged records; express upstream failure at adapter boundary.

**Fit criterion:** Invalid requests produce INVALID_REQUEST without selected news. Each damaged candidate receives its specified invalid-record, invalid-title or invalid-timestamp decision and is counted without discarding valid candidates. UTC start and end boundary records are included, later records are OUT_OF_WINDOW, and upstream vendor failure is reported as unavailable rather than selected news.

**Registry verification labels:** `T10`, `T11`, `T13`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t10_request_rejections`

- `test/offline/test_o5_macro_news_filter.py::test_t10a_empty_title`

- `test/offline/test_o5_macro_news_filter.py::test_t10b_no_title_sentinel`

- `test/offline/test_o5_macro_news_filter.py::test_t10c_string_timestamp_is_structural`

- `test/offline/test_o5_macro_news_filter.py::test_t10d_naive_datetime_is_invalid_timestamp`

- `test/offline/test_o5_macro_news_filter.py::test_t10e_missing_candidate_id`

- `test/offline/test_o5_macro_news_filter.py::test_t10k2_absent_and_null_optionals_agree`

- `test/offline/test_o5_macro_news_filter.py::test_t10l_non_mapping_candidate`

- `test/offline/test_o5_macro_news_filter.py::test_t11_window_containment`

**Unresolved labels / manual references:** `T13`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-06

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** 100× identical ⇒ full equality; unique-ID permutations equal (input_index differs); conflicting duplicate IDs not permutation-invariant; no wall-clock in selector.

**Fit criterion:** Running the same fixture 100 times produces identical decisions, selected IDs and audit output. Permuting records with unique IDs preserves the selected ID set and rule results apart from input_index; conflicting duplicate-ID inputs are excluded from that permutation assertion. The selector reads no wall clock.

**Registry verification labels:** `T14`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t14a_hundred_identical_runs`

- `test/offline/test_o5_macro_news_filter.py::test_t14b_permutation_invariance`

- `test/offline/test_o5_macro_news_filter.py::test_t14c_no_wall_clock_read`

- `test/offline/test_o5_macro_news_filter.py::test_t14d_conflicting_duplicates_first_occurrence_wins`

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-07

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** On the fixed human-review candidate set, require macro relevance precision >=90%, pre-limit recall >=75%, and primary-topic coverage 100% when K covers all relevant primary topics; the development fixture is a provisional oracle until a human checks its labels.

**Fit criterion:** T18 computes precision >=0.90, pre-limit recall >=0.75 and eligible primary-topic coverage ==1.0 against the fixed labelled set; report N/A only for zero-denominator cases under the specified rules.

**Registry verification labels:** `T01`, `T18`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t01_dev20_k20`

**Unresolved labels / manual references:** `T18`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-08

**Registry type / priority / status:** cost / Must / selected_for_development

**Statement:** 0 added requests, 0 LLM calls, 0 input mutations; offline no keys.

**Fit criterion:** The selector adds zero vendor or network requests and zero LLM calls, leaves caller input deeply unchanged, and its offline tests complete without credentials or recorded network attempts.

**Registry verification labels:** `T07`, `T10`, `T14`, `T16`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_macro_news_filter.py::test_t07a_structural_invalid_first_does_not_reserve_id`

- `test/offline/test_o5_macro_news_filter.py::test_t07b_out_of_window_first_reserves_id`

- `test/offline/test_o5_macro_news_filter.py::test_t07c_title_invalid_reserves_id`

- `test/offline/test_o5_macro_news_filter.py::test_t07d_duplicate_after_valid_selection`

- `test/offline/test_o5_macro_news_filter.py::test_t07e_selector_does_not_mutate_inputs`

- `test/offline/test_o5_macro_news_filter.py::test_t10_request_rejections`

- `test/offline/test_o5_macro_news_filter.py::test_t10a_empty_title`

- `test/offline/test_o5_macro_news_filter.py::test_t10b_no_title_sentinel`

- `test/offline/test_o5_macro_news_filter.py::test_t10c_string_timestamp_is_structural`

- `test/offline/test_o5_macro_news_filter.py::test_t10d_naive_datetime_is_invalid_timestamp`

- `test/offline/test_o5_macro_news_filter.py::test_t10e_missing_candidate_id`

- `test/offline/test_o5_macro_news_filter.py::test_t10k2_absent_and_null_optionals_agree`

- `test/offline/test_o5_macro_news_filter.py::test_t10l_non_mapping_candidate`

- `test/offline/test_o5_macro_news_filter.py::test_t14a_hundred_identical_runs`

- `test/offline/test_o5_macro_news_filter.py::test_t14b_permutation_invariance`

- `test/offline/test_o5_macro_news_filter.py::test_t14c_no_wall_clock_read`

- `test/offline/test_o5_macro_news_filter.py::test_t14d_conflicting_duplicates_first_occurrence_wins`

- `test/offline/test_o5_regression.py::test_t16_o5_path_adds_no_network_or_llm`

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-09

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** Keep public news API signatures and return type str unchanged; leave ticker-news behavior unchanged and run all prior applicable news tests.

**Fit criterion:** RT-1 through RT-4 and the inherited news tests pass; public signatures and ticker-news golden output are unchanged.

**Registry verification labels:** `T15`, `RT-1`, `RT-4`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o5_regression.py::test_rt1_global_news_tool_schema_unchanged`

- `test/offline/test_o5_regression.py::test_rt4_ticker_news_path_untouched`

- `test/offline/test_o5_regression.py::test_rt4b_ticker_news_signature_unchanged`

**Unresolved labels / manual references:** `T15`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### INV-O5-01

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** No fabrication / irrelevant padding

**Fit criterion:** output ⊆ input; SELECTED-only publication; business-field equality (I11)

**Registry verification labels:** `O5 invariant tests I1-I12`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O5 invariant tests I1-I12`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### INV-O5-02

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** No out-of-input/duplicate/mutation

**Fit criterion:** subset, uniqueness, deep-equality

**Registry verification labels:** `O5 invariant tests I1-I12`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O5 invariant tests I1-I12`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### INV-O5-03

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** Window containment

**Fit criterion:** adapter recompute on original published_at

**Registry verification labels:** `O5 invariant tests I1-I12`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O5 invariant tests I1-I12`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### INV-O5-04

**Registry type / priority / status:** invariant / Must / selected_for_development

**Statement:** No network/LLM

**Fit criterion:** import boundary + test-time block + attempt recording (T16)

**Registry verification labels:** `O5 invariant tests I1-I12`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `O5 invariant tests I1-I12`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** Needs explicit node/manual-evidence mapping; no individual acceptance claimed. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-O5-10

**Registry type / priority / status:** performance / Should / selected_for_development

**Statement:** The deterministic selector has bounded local processing time on a fixed 1000-record, K=30 fixture.

**Fit criterion:** On ubuntu-latest/Python 3.11, after 5 warmups and 30 measured runs, nearest-rank p95 selector time is <= 100 ms; report fixture hash and runner.

**Registry verification labels:** `T17`

**Registry source_code:** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py)

**Actual implementation locations (files present):** [tradingagents/dataflows/vendors/yahoo/news.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/vendors/yahoo/news.py), [tradingagents/dataflows/macro_news_filter.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/dataflows/macro_news_filter.py)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `T17`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** Evidence decision events and SINK_FAILED diagnostic; S5 run-scoped JSONL. Runtime sink failure is soft, regression violations are not waived.

**Evidence / status:** STOPPED / NOT ACCEPTED: S6/T17 performance gate not met per team decision; no implementation restart planned. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).


## O6

### O6-FR-01

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Report per-selected-Analyst ordinary and wrap_up model-call counts, input/output usage, cumulative model-call duration and unattributed in-scope calls; count each invocation once, exclude known out-of-scope calls from both named rows and unattributed_calls, and disclose deferred first structured-call attribution.

**Fit criterion:** Two Market calls (one ordinary call and one wrap_up) with 100/20 and 50/10 input/output tokens and durations of 1.0 s and 0.5 s yield 2 calls, 150/30 tokens, 1.5 s. One News call with 80/15 tokens and a duration of 0.8 s yields 1 call, 80/15 tokens, 0.8 s. Repeating a notification for an existing invocation leaves these values unchanged. One in-scope call without a verified analyst ID increments unattributed_calls by 1 and changes no named row. A known out-of-scope call changes neither named Analyst rows nor unattributed_calls. An offline test through the real Analyst subgraph verifies that ordinary and wrap_up calls reach the callback with the expected selected Analyst key. The CLI integration test verifies exact counts, token attribution, and a visible statement that first structured-call attribution is deferred and named rows cover only verified in-scope calls. Real-subgraph ordinary and wrap_up callbacks must carry spec.key, and two simultaneous selected Analysts must have no cross-attribution; handler-only synthetic events do not satisfy this criterion.

**Registry verification labels:** `TC-O6-01`, `TC-O6-04`, `TC-O6-07`, `TC-O6-07b`, `TC-O6-08`, `TC-O6-10`, `TC-O6-11`, `TC-O6-12`, `TC-O6-13`

**Registry source_code:** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py)

**Actual implementation locations (files present):** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py), [cli/display.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/display.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o6_analyst_subgraph.py::test_tc_o6_07_market_ordinary_and_wrap_up`

- `test/offline/test_o6_analyst_subgraph.py::test_tc_o6_07b_swapped_graph_keys_fail_attribution`

- `test/offline/test_o6_analyst_subgraph.py::test_tc_o6_07b_two_analysts_overlap_no_crossover`

- `test/offline/test_o6_analyst_subgraph.py::test_tc_o6_11_out_of_scope_call_excluded`

- `test/offline/test_o6_analyst_subgraph.py::test_tc_o6_13_wrap_up_attributed_once`

- `test/offline/test_o6_cli_wiring.py::test_tc_o6_12_cli_disclosure_rows_and_wording`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_01_market_two_calls_news_one`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_04_interleaved_reverse_completion`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_08_in_scope_missing_identity`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_10_empty_and_unknown_keys`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_10b_duplicate_start_before_terminal_unattributed`

**Runtime monitor/fallback:** Named statistics and unattributed count; token unknown/partial presentation. No claim of model-quality monitoring.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O6-FR-02

**Registry type / priority / status:** functional_behavior / Must / selected_for_development

**Statement:** Report input and output token completeness independently. If every counted call reported a value for a field, show the total. If some did, show the known subtotal marked partial. If none did, show Unknown. Treat an explicitly reported zero as a known value.

**Fit criterion:** No reported token data yields Unknown for both fields. A reported 0/0 yields two complete zero totals. For calls reporting 100/20 and 50/missing, input is 150 and complete, and output is 20 and partial.

**Registry verification labels:** `TC-O6-02`, `TC-O6-03`

**Registry source_code:** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py)

**Actual implementation locations (files present):** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py), [cli/display.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/display.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_02_missing_usage_vs_explicit_zero`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_03_partial_output_metadata_omits_field`

**Runtime monitor/fallback:** Named statistics and unattributed count; token unknown/partial presentation. No claim of model-quality monitoring.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O6-NFR-01

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Attribute model calls correctly when invocations overlap or complete out of order. Keep statistics isolated across CLI analysis runs.

**Fit criterion:** Interleave ordinary and wrap_up calls for Market and News and complete them out of order. Assert that each invocation contributes only to the named row matching its trusted agent_key. Verify exact counts, tokens, and durations in each row, with zero contribution to the other Analyst's row. A new run contains only its own events.

**Registry verification labels:** `TC-O6-04`, `TC-O6-06`

**Registry source_code:** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py)

**Actual implementation locations (files present):** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py), [cli/display.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/display.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_04_interleaved_reverse_completion`

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_06_fresh_handler_isolated`

**Runtime monitor/fallback:** Named statistics and unattributed count; token unknown/partial presentation. No claim of model-quality monitoring.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### O6-NFR-02

**Registry type / priority / status:** quality_attribute / Must / selected_for_development

**Statement:** Preserve the baseline get_stats() interface, output and run-level counter semantics. The O6 offline tests must be repeatable with simulated model events and a controlled clock, without API credentials or network access.

**Fit criterion:** For one completed call with 100/20 tokens and one tool call, the baseline interface still reports llm_calls=1, tool_calls=1, tokens_in=100, and tokens_out=20. The CI log shows both the baseline suite and the new O6 offline tests running successfully.

**Registry verification labels:** `TC-O6-09`

**Registry source_code:** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py)

**Actual implementation locations (files present):** [cli/stats_handler.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/stats_handler.py), [tradingagents/graph/setup.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/tradingagents/graph/setup.py), [cli/display.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/display.py), [cli/run.py](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py)

**Source-declared nodes linked by case ID:**

- `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_09_legacy_get_stats_preserved`

**Runtime monitor/fallback:** Named statistics and unattributed count; token unknown/partial presentation. No claim of model-quality monitoring.

**Evidence / status:** Cross-reference located; partial/fit-criterion coverage not certified; suite-level CI only. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).


## GOV

### REQ-GOV-01

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** No code change merges unless its tests were approved before implementation began.

**Fit criterion:** Every merged code PR has an approval record with approver, timestamp, test-plan version and scope earlier than its first implementation commit.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-02

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** Before a coding agent generates code, it produces an execution plan covering traceability, interface, scope and tests, and waits for human approval.

**Fit criterion:** Every agent implementation session has a dated plan and approval before its first code edit.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-03

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** CI validates the requirements registry against its checked-in JSON Schema.

**Fit criterion:** A valid registry passes and a malformed or missing required-field fixture fails the schema job.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-04

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** Every change runs the full prior regression suite; any regression blocks merge.

**Fit criterion:** CI executes all applicable prior suites and a deliberately failing test blocks merge.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-05

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** Prompt or model changes run a fixed semantic evaluation set against approved quality thresholds.

**Fit criterion:** A below-threshold fixture blocks merge and the CI log records case-level scores.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-06

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** Code or prompt PRs update the AI-use log and preserve links to genuine agent-session evidence.

**Fit criterion:** A code/prompt PR without an AI-use-log update is rejected by CI; the log points to real transcripts.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-07

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** Every commit runs lint, type and dependency checks; safety-relevant PRs also run contract, security, API-surface and permission checks.

**Fit criterion:** CI runs required jobs on the stated triggers and an injected violation blocks merge.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

### REQ-GOV-08

**Registry type / priority / status:** governance / Must / selected_for_development

**Statement:** Branch protection requires passing CI and human review with an architecture decision for safety-critical path changes.

**Fit criterion:** A failing required check or missing qualifying review prevents merge in a protected-branch trial.

**Registry verification labels:** `course D7/D9 gate evidence`

**Registry source_code:** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml), [docs/req/requirements.yaml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)

**Actual implementation locations (files present):** [.github/workflows/ci.yml](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml)

**Source-declared nodes linked by case ID:**

No exact case-ID match recovered. This is a mapping gap, not a finding that no relevant tests exist.

**Unresolved labels / manual references:** `course D7/D9 gate evidence`. Review source and owner evidence; do not invent matches.

**Runtime monitor/fallback:** CI job conclusions; branch-protection settings are external and require their own evidence.

**Evidence / status:** CI configuration is present; specific checker negative-test mapping and actual merge-blocking evidence still need F/A evidence. Job success alone does not establish required-check enforcement. [Existing suite CI](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013).

## Handoff and validation

C: maintain this document, fill exact O3 mapping and integrate existing owner material. B: check97 Registry IDs, wording, fit criteria and stale source_code references. F: inspect assertions and attach exact case results/manual artifacts where required. A: provide authoritative final freezeSHA and branch-protection enforcement evidence. This is factual closeout review, not a new requirement or test-plan approval round.

Outstanding: manual O3 FC-14 record, provider-usage diagnostic if token claims are desired, unmatched case labels below, full other-module assertion review, governance merge-blocking evidence. No raw secrets/transcripts were copied into this document.

| Requirement | Unresolved labels |
|---|---|
| O2-FR-01 | O2-TC-04 |
| O2-FR-02 | O2-TC-04, O2-TC-11 |
| O2-FR-03 | O2-TC-04, O2-TC-11 |
| O2-NFR-01 | O2-TC-18 |
| O2-NFR-05 | O2-TC-21 |
| O2-NFR-06 | O2-TC-20 |
| O3-FR-07 | T-R3 |
| O3-NFR-02 | FC-14 performance record |
| O4-FR-07 | O4-T-23 |
| O4-FR-13 | O4-T-23 |
| O4-NFR-07 | O4-T-22 |
| O4-INV-01 | O4-T-23 |
| O4-INV-03 | O4-T-23 |
| REQ-O5-01 | T08e, RT-3 |
| REQ-O5-03 | T13 |
| REQ-O5-04 | I11 |
| REQ-O5-05 | T13 |
| REQ-O5-07 | T18 |
| REQ-O5-09 | T15 |
| INV-O5-01 | O5 invariant tests I1-I12 |
| INV-O5-02 | O5 invariant tests I1-I12 |
| INV-O5-03 | O5 invariant tests I1-I12 |
| INV-O5-04 | O5 invariant tests I1-I12 |
| REQ-GOV-01 | course D7/D9 gate evidence |
| REQ-GOV-02 | course D7/D9 gate evidence |
| REQ-GOV-03 | course D7/D9 gate evidence |
| REQ-GOV-04 | course D7/D9 gate evidence |
| REQ-GOV-05 | course D7/D9 gate evidence |
| REQ-GOV-06 | course D7/D9 gate evidence |
| REQ-GOV-07 | course D7/D9 gate evidence |
| REQ-GOV-08 | course D7/D9 gate evidence |
| O4-FR-14 | O4-T-22 |
| REQ-O5-10 | T17 |