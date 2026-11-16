# O1–O6 Test Case Catalogue — v2.0 Review Draft

**For:** Member F (test coordination and CI). **Status:** Consolidated draft. Cases are proposed unless their owner’s separate approval record says otherwise. Inclusion here does not mean a test was coded, run, passed, or approved.

## How to use it

This is a single reading copy of the owners’ cases. `requirements.yaml` records requirements and verification IDs; the sections below retain scenarios and expected results. Before implementation, compare the selected YAML with each owner’s current test-plan version, resolve the differences below, and record the actual pre-code approval. Later add real test paths, pytest node IDs and CI links. O5 also needs its adjacent `O5-Dev20-Fixtures-v0.5.3-DRAFT.json` fixture.

## Coverage inventory

| Feature | Preserved cases | Source and state |
|---|---|---|
| O1 | T-O1-01…10 | Separate O1 plan; draft; YAML-only 11/12 still need written cases |
| O2 | O2-TC-01…25 | v2.0 O2 requirements §7; proposed |
| O3 | T-N1…8, T-B1…9, T-E1…6, T-R1…3 | v2.0 O3 §5; proposed; YAML-only R4/E7/E8 need written cases |
| O4 | O4-T-01…25 | v2.0 O4 §5; proposed; separate O4 plan only covers 01…23 |
| O5 | T01…20, I1…I12, RT-1…RT-4 plus parameterized subcases | v2.0 O5 test plan; draft; full plan not approved |
| O6 | TC-O6-01…08 plus separate-plan 07b and 09…14 | v2.0 O6 §5 plus detailed draft; TC-07 differs between sources |

O5 parameterized invariant families expand into many individual cases; the table counts families, not pytest nodes. O4-T-22 is a manual scope review. O3 T-R3 is a manual live observation. Keep them out of the automatic offline pass count.

## Reconciliation queue for F and owners

| Feature | Gap | Required plan update |
|---|---|---|
| O1 | Selected YAML cites T-O1-11/12 for shuffled/duplicate dates; separate plan stops at 10 and assumes ordered unique dates. | A specifies fixture, entry point and exact result for 11/12; update the older proposed wording and tolerance status. |
| O2 | TC-13/14 still say “approved” error behavior; selected YAML chose visible fail-soft manifest write failure. | B writes the exact expected warning, no partial file/path claim and retained gated analysis result. |
| O3 | Selected YAML cites R4/E7/E8, absent from v2.0 §5. | C specifies idempotence, installed-tokenizer measurement and persisted-audit privacy cases, or removes the YAML links. |
| O4 | v2.0 contains T-24/25, but O4-TEST-v0.1 ends at T-23. | D adds T-24/25 to the versioned plan and confirms real Graph/CLI publication checks T-07/08/19/23. |
| O5 | Plan itself says not approved; DEV20 human labels, policy decisions and T17 threshold/runner are pending. Its header points to a corrected-r2 active copy. | E/F confirm the authoritative copy, approve labels and specify which cases and thresholds block CI. |
| O6 | v2.0 TC-07 tests Market ordinary plus News wrap_up; companion TC-07 tests ordinary plus wrap_up within one Analyst and 07b covers two Analysts. | F resolves distinct IDs/fixtures and verifies the latest FR-01 fit criterion, selected-Analyst identity, CLI disclosure and cross-Analyst isolation. |

## Proposed case text for YAML-only links

These five rows are **A's proposed reconciliation text**, derived from the selected `requirements.yaml`. They were **not** in the owners' supplied test plans and require owner/F review before approval. They are kept separate from the copied cases below so their origin stays clear.

| ID | Controlled input / action | Expected result | Maps to |
|---|---|---|---|
| T-O1-11 | Supply 260 unique dated, nonconstant closes to the Yahoo SMA calculation in deliberately shuffled row order. Query the 60th date in chronological order and the last date; compute reference means after sorting by date. | Values match the same chronological fixture: at chronological date 60, 50-SMA matches the latest 50 and 200-SMA reports insufficient history with `have 60`; at the last date both SMAs match their respective latest-window means. No future row contributes to an earlier date. | REQ-O1-03 |
| T-O1-12 | Supply a cleaned-looking frame with two rows for the same trading date to each O1 SMA entry point that accepts a frame; request 50/200 SMA separately. Keep a distinct non-SMA control. | Neither SMA returns a numeric value; the exact SMA result is `N/A: invalid price history (duplicate trading date)`. The non-SMA control retains its prior behavior. Confirm which public routed surface can expose this condition before fixing its test assertion. | REQ-O1-03, REQ-O1-06 |
| T-R4 (O3) | Run the condenser twice on the same deterministic multi-source fixture, feeding first output into the second pass. | Second-pass text is byte-identical to first-pass text; its `duplicates_removed`, `items_dropped` and `items_truncated` are all 0. | O3-NFR-01 / FC-9 |
| T-E7 (O3) | Use the approved offline tokenizer on the same 3× duplication fixture as T-N6; measure before and after with that tokenizer. | Estimated token count decreases strictly; the character-reduction figure remains labelled `chars`. Do not infer a universal token saving from one fixture. | O3-FR-07 / FC-11 |
| T-E8 (O3) | Put distinctive raw titles, URLs, payload text, endpoint strings and fake credentials in a controlled input; capture persisted audit output and INFO logs. | None of those distinctive values appear in either saved audit data or INFO logs; stable non-secret IDs and counts remain. | O3-NFR-05 / FC-7 |

For O2-TC-13/14, the selected YAML proposes a visible fail-soft result: keep the gated analysis result, issue a manifest-failed warning, publish no saved-manifest path and leave no partial JSON. B should put that exact expectation into the versioned O2 plan. For O6-TC-07, F should keep separate checks for one Analyst's ordinary-plus-`wrap_up` calls and for two selected Analysts' isolation; the conflicting source fixtures below should not share a single approved ID.

## Source snapshot

The six v2.0 requirement sources are also copied into `sources-v2.0/` so the registry source links work in the repository. The short SHA-256 prefixes identify the input files used to create this catalogue. They are not Git commits or approvals.

| Key | File | SHA-256 prefix |
|---|---|---|
| O1 | `O1-SMA-Guard-Test-Plan-Draft.md` | `03e47f591e5a70a4` |
| O2 | `O2-Reproducibility-Manifest-Requirements.md` | `a6e459a54453b917` |
| O3 | `O3-input-condensation.md` | `f8b9e3c1c385bfa5` |
| O4 | `O4-requirements.md` | `9e5eb76b729f06a5` |
| O5 | `O5-Test-Plan-v0.5.3-DRAFT.md` | `4b35c12cd60692a9` |
| O5 fixture | `O5-Dev20-Fixtures-v0.5.3-DRAFT.json` | `a6f65bf271d9c9ac` |
| O6 | `O6_Requirements_Review-组内审查后.md` | `cc543044c7adb202` |
| O6detail | `O6-Test-Plan-v0.1-DRAFT.md` | `e52515ece7680e2a` |
| O4detail | `O4-Test-Plan.md` | `971c6c8696728881` |

---

## O1 — SMA Validity Guard

Separate O1 draft plan; not in v2.0. Its ten cases are copied below. T-O1-11/12 are not yet specified there.

### 2. Cases and requirement trace

“Insufficient” below means the proposed labelled text, with no numeric SMA for that indicator; both the text and the `<= 1e-6` tolerance remain **proposed pending owner approval**. W−1 and W are the essential boundaries; 40, 60, and 220 are additional representative cases.

T-O1-10 covers only the **non-empty, all-`Close`-missing** case. It is deliberately **not** combined with a frame that becomes empty after the analysis-date cutoff (`ohlcv.py:230`); that route is separate and its current behavior must be observed before any assertion is written.

| Test ID | Controlled input and entry point | Expected result | Detects | Requirements |
|---|---|---|---|---|
| T-O1-01 | 40 and 49 cleaned closes; call the bulk indicator report separately for each SMA. | Both SMAs insufficient at 40; 50-SMA insufficient at 49. | Partial-window value and 49/50 off-by-one. | REQ-O1-01, -02 |
| T-O1-02 | 50 and 60 cleaned closes; separate bulk report calls. | 50-SMA equals the latest-50 mean; 200-SMA insufficient at both counts. | Incorrect 50 boundary or false 200-SMA. | REQ-O1-01, -02 |
| T-O1-03 | 199, 200, and 220 cleaned closes; separate bulk report calls. | 200-SMA insufficient at 199; at 200 and 220 both SMAs equal their respective latest-window means. | 199/200 off-by-one or wrong normal value. | REQ-O1-01, -02 |
| T-O1-04 | A 260-row cleaned frame; derive the 60th session's date from the frame (`target_date = frame["Date"].iloc[59]`, formatted `%Y-%m-%d`), then call `_get_stock_stats_bulk` separately for `close_50_sma` and `close_200_sma` and look up `target_date` as a **key** in each returned map. | At `bulk50[target_date]` the 50-SMA is valid (matches the latest-50 mean within 1e-6); at `bulk200[target_date]` the 200-SMA is insufficient with N=60. | Using whole-frame length for an early reported date, or a positional lookup that only works by insertion order. | REQ-O1-03 |
| T-O1-05 | Snapshot with 40, 50, 199, and 200 cleaned closes. | At 40 both SMA cells insufficient; at 50 only 50-SMA valid; at 199 only 50-SMA valid; at 200 both valid. Valid displayed values match independently computed means after display formatting. | Snapshot bypassing guard or boundary error. | REQ-O1-01, -02, -04 |
| T-O1-06 | Make `_get_stock_stats_bulk` raise `RuntimeError`; give the fallback cleaned frames of 49/50 and 199/200 rows. Call `get_stock_stats_indicators_window` separately for each SMA with `look_back_days=0` and the frame's last trading date. | The 49-row 50-SMA and 199-row 200-SMA return the insufficient-history line; the 50-row 50-SMA and 200-row 200-SMA return their correct means. | A bulk-only fix or a wrong fallback boundary. | REQ-O1-01, -02, -04 |
| T-O1-07 | For a controlled frame, request a non-SMA indicator present in `DEFAULT_SNAPSHOT_INDICATORS` (`snapshot.py:24-28`, e.g. `rsi`) through bulk, forced per-day fallback, and the verified snapshot; compute references from the same frame with stockstats directly. Note the snapshot builder also accepts a custom `indicators` argument, but O1 tests only use the default list to avoid depending on arbitrary names. Run all prior test suites after implementation. | Each tested non-SMA value matches its direct reference within 1e-6 or the existing display rule; all prior suites pass. | Guard accidentally applying to unrelated indicators in an edited path. | REQ-O1-05 |
| T-O1-08 | In one window output, include a trading date with insufficient SMA history and a nearby weekend/holiday date. | The two dates have distinct, exact messages: insufficient history versus not a trading day. | Ambiguous unavailable status. | REQ-O1-06 |
| T-O1-09 | Use a seeded local cache with 50 dated rows, one middle `Close` missing, and call an O1 entry point through the real `load_ohlcv`; repeat for 200 rows if the 50-case does not cover a separate branch. Keep vendor behavior controlled and offline. | The loader removes the missing-close row; the resulting 49/199 usable closes do not satisfy the 50/200 SMA window. Existing loader-cleaning tests may be referenced instead of duplicated. | Counting an invalid close as a valid session or failing to connect loader cleaning to the guard. | REQ-O1-01, -02 |
| T-O1-10 | One offline fixture: a **non-empty** seeded price frame (e.g. 50 dated rows) whose `Close` values are **all missing**, loaded through the real `load_ohlcv` via the `_run_load` seeded-cache pattern (`tests/test_ohlcv_latest_bar.py:98`). Exercise an O1 entry point (bulk report / snapshot). At the **direct** entry point `load_ohlcv` raises `NoMarketDataError` with detail `"no bar in range has a closing price"` (`ohlcv.py:238-241`); through the **routed tool** (`get_indicators` via `route_to_vendor`, or `get_verified_market_snapshot` which calls `no_data_available`, `tools.py:94-96`) the result is the `NO_DATA_AVAILABLE` sentinel (`router.py:185-197`). | The output never contains a numeric SMA and never contains `have 0` insufficient-history text; the existing no-data behavior is preserved. | Confusing absent market data with an available but short SMA history, or emitting a fabricated/zero-count SMA. | REQ-O1-01, -02, -04 |

The snapshot already has a test that removes a future price from its output (`tests/test_yahoo_snapshot.py::TestVerifiedSnapshot::test_excludes_future_rows`). That test does not by itself prove the SMA history count ignores future rows. This proposed O1 scope does not change `load_ohlcv`'s existing date cutoff; no new future-row test is claimed here. If the team makes future-row exclusion an O1 fit criterion, its test must exercise the real cutoff with controlled offline input rather than a mock that removes the future row before the code under test sees it.

---

## O2 — Reproducibility Manifest

v2.0 O2 requirements §7.

### 7. Proposed test cases

None of these tests are claimed implemented, executed, or approved. `test/offline/` and CI collection must be confirmed with F.

| Test ID | Scenario | Expected result | Requirement mapping |
|---|---|---|---|
| O2-TC-01 | Valid completed invocation | One parseable manifest with required fields and schema version | FR-01, FR-12, NFR-07 |
| O2-TC-02 | Same normalized fields/config with reordered dictionary keys | Identical fingerprint | FR-07/08, NFR-02 |
| O2-TC-03 | Change included fields individually | Corresponding fingerprint changes | FR-07 |
| O2-TC-04 | Two same-ticker/date invocations | Two distinct readable manifest paths; first is not overwritten | FR-02/03 |
| O2-TC-05 | Reference report/state/message artifacts | Correct stability labels; mutable artifacts not claimed immutable | FR-10 |
| O2-TC-06 | Fake secret and credential-bearing URL in supplied config | No secret key/value or credentials serialized | FR-05/11, NFR-03 |
| O2-TC-07 | No immutable market/news snapshot | `actual_input_data_provenance` is `not_captured`; no data hash | FR-09 |
| O2-TC-08 | Git unavailable | Explicit unavailable status; manifest creation continues | FR-06/14 |
| O2-TC-09 | Model/provider metadata missing | Explicit missing status; no invented values | FR-05/06 |
| O2-TC-10 | Empty optional fields, Unicode, reordered mappings | Valid JSON and deterministic equivalent fingerprint | FR-07, NFR-02/05 |
| O2-TC-11 | Two invocations start within same second | Distinct IDs and paths | FR-02/03 |
| O2-TC-12 | Raw ticker variants normalize identically | Same normalized identity/fingerprint if raw ticker excluded | FR-04/07 |
| O2-TC-13 | Non-serializable value | Approved error behavior; no partial/corrupt manifest | FR-13/14 |
| O2-TC-14 | Manifest destination unwritable | Approved fail-soft/closed behavior; no partial file | FR-14 |
| O2-TC-15 | Invalid/path-traversal ticker | Rejected without writing outside results boundary | FR-03, NFR-05 |
| O2-TC-16 | Nested secret or credential URL | Secret excluded/redacted | FR-11, NFR-03 |
| O2-TC-17 | Git lookup OS/timeout failure | Explicit unavailable/error status; no fabricated data | FR-06/14 |
| O2-TC-18 | Inspect runtime dependencies | No new third-party runtime dependency | NFR-01; proposed Static Analysis Gate check |
| O2-TC-19 | Run manifest tests with fakes and network disabled | No vendor/market-data/LLM/network access | NFR-04; proposed |
| O2-TC-20 | Regression-check agreed existing outputs/interfaces | Existing behavior is preserved | NFR-06; proposed |
| O2-TC-21 | Run path/serialization checks on approved CI platform matrix | Checks pass on every explicitly supported platform | NFR-05; proposed, platform matrix pending |
| O2-TC-22 | Inspect produced manifest identity fields | Normalized ticker, asset type, date, analysts are present | FR-04; proposed |
| O2-TC-23 | Supply allowlisted and unapproved config keys | Only allowlisted fields are serialized | FR-05; proposed |
| O2-TC-24 | Supply available package/Python/platform metadata | Those values are present; missing values are explicit | FR-06; proposed |
| O2-TC-25 | Inspect manifest schema-version field | Agreed field/value is present | FR-12; proposed |

---

## O3 — Input Condensation

v2.0 O3 §5.

### 5. Proposed Test Cases

New file: `test/offline/test_input_condensation.py` (pytest, no network, deterministic
fixtures in the file itself). Test FC-6a in T-N5 and FC-6b in T-E2.

#### Normal
| ID | Scenario | Expected |
| --- | --- | --- |
| T-N1 | 3 sources, 3 identical news articles among 8 | 1 copy kept, other items intact, `duplicates_removed == 2` |
| T-N2 | 10 real-shaped articles, budget generous | Nothing dropped; `chars_after == chars_before` modulo normalisation; audit note lists 0 removals |
| T-N3 | 10 articles, tight budget | Only top-ranked kept; ordering preserved; `<input_condensation>` footer present |
| T-N4 | News + StockTwits with the same headline | Both kept (FC-3) |
| T-N5 | Node-level test with fake LLM capturing messages | Captured prompt contains condensed blocks plus unchanged instrument identity, date and safety text |
| T-N6 | 3× duplication fixture | Length reduction ≥ 30 % (FC-10), figure labelled "chars" |
| T-N7 | Invalid allocation or a block over its cap while total input fits | Reject invalid cap allocation with `ValueError`; condense a valid oversized block to its source cap. |
| T-N8 | Three known source shapes and a changed formatter shape | Three fixtures parse as expected; the format contract test fails for the changed shape. |

#### Boundary
| ID | Scenario | Expected |
| --- | --- | --- |
| T-B1 | Empty input (`""`) | Returns input unchanged, all counts 0, no exception |
| T-B2 | Exactly at budget (`chars == budget`) | No truncation applied |
| T-B3 | Budget + 1 char | Output fits the cap including the marker, or the ordinary item is dropped |
| T-B4 | Protected placeholder longer than its source cap | Raise, fall back to original block, record exception and fail FC-5 |
| T-B5 | Single ordinary item longer than its source cap | Truncate if it fits including the marker, otherwise drop; preserve protected text |
| T-B6 | Two items, Jaccard exactly 0.8 | Treated as duplicates (inclusive threshold) |
| T-B7 | Two items, Jaccard 0.79 | Not merged |
| T-B8 | Article with no link and empty title | Not merged with another empty-title article; retained or dropped by rank only |
| T-B9 | Non-ASCII (Chinese headline set) | Same dedup/ranking behaviour; char counts are code-point counts |

#### Exception
| ID | Scenario | Expected |
| --- | --- | --- |
| T-E1 | `None` input | `CondensationError`; node falls back, logs warning, returns report |
| T-E2 | Fetcher returns `<Yahoo Finance news unavailable…>` placeholder | Placeholder retained verbatim, never counted as duplicate (FC-6) |
| T-E3 | Condenser raises | Node catches, uses uncondensed prompt, run still completes (FC-13) |
| T-E4 | Unknown/invalid config value (e.g. `input_budget_chars = -1`) | `ValueError` at config validation, not silent mid-run |
| T-E5 | Tokenizer absent | `tokens_after is None`; no token claim (FC-11) |
| T-E6 | Unknown block shape with sufficient budget | Preserve the whole block as one item and record `parse_fallbacks > 0`. |

#### Regression / integration
| ID | Scenario | Expected |
| --- | --- | --- |
| T-R1 | Explicit offline collection and execution | All pre-existing tests pass (FC-15) |
| T-R2 | `input_condensation_enabled=False` golden | Output byte-identical to baseline (FC-12) |
| T-R3 | `test/live/` (manual, recorded in `transcripts/`) | Record provider input-token usage where available as a diagnostic observation |

---

---

## O4 — Decision Evidence Gate

v2.0 O4 §5; this is newer than the separate 23-case O4 plan.

### 5. Proposed Test Cases

> **PROPOSED, not executed.** Deterministic and offline unless marked a benchmark or integration activity. Test directory placement pending Member F (Section 7); IDs `O4-T-*` are independent of file layout.

| Test ID | Requirement(s) | Initial state / input | Expected result | Category | Verification |
|---|---|---|---|---|---|
| O4-T-01 | FR-01, FR-02 | All four reports non-empty; original `Overweight`; all selected | Verdict `valid`; effective `Overweight` | Normal | Unit |
| O4-T-02 | FR-03, INV-01 | Parameterized: each of market/sentiment/news/fundamentals report is empty in turn; others present; original `Buy`; all selected | Effective `REVIEW`; failing set == that one report | Negative | Unit |
| O4-T-03 | FR-03 | Parameterized: each required report whitespace-only; plus multi-report-missing case | Those reports `missing`; downgrade; exact failing set | Boundary | Unit |
| O4-T-04 | FR-04 | Required report with approved sentinel; flag on vs off | On → `unavailable`+`REVIEW`; off → `present` | Boundary | Unit |
| O4-T-05 | FR-06, FR-11 | Selected `{market, news}`; sentiment/fundamentals empty | Those `not_required`; no false downgrade | Normal/Boundary | Unit |
| O4-T-06 | FR-05, INV-02 | All evidence present; original `REVIEW` | Remains `REVIEW` | Negative | Unit |
| O4-T-07 | FR-09, INV-04 | Unit: checker raises. Integration: recoverable failure in the wired call path | `REVIEW`, reason preserved, no ungated rating on any enabled surface | Checker failure | Unit + Integration |
| O4-T-08 | FR-07, FR-09, INV-01/03/04, NFR-08 | Downgraded and checker-failure states through real Graph/CLI publication path | Identical `REVIEW` across enabled surfaces only; disabled surfaces not assumed enabled | Integration | Integration (offline Graph/CLI) |
| O4-T-09 | FR-02 | All evidence present; original `Sell` | Effective `Sell`; no spurious downgrade | Normal | Unit |
| O4-T-10 | FR-12 | Downgraded run with a `Buy` body | Effective `REVIEW`; checker leaves `final_trade_decision` byte-identical (label rendering verified by T-19/T-23) | Negative | Unit |
| O4-T-11 | FR-08, NFR-01 | Same input ×100 | Identical verdicts; no I/O | Boundary | Unit |
| O4-T-12 | FR-10 | Any state, incl. non-pass | Complete per-item statuses; enumerated verdict; reason on non-pass | Normal | Unit |
| O4-T-13 | FR-06 | Selected `{market}` only; market present | Valid; others `not_required` | Boundary | Unit |
| O4-T-14 | FR-03, FR-06 | Parameterized: selected `{market}` only, market missing/empty; and multi-select with one required missing | Downgrade `REVIEW`; no false failure for unselected | Negative | Unit |
| O4-T-15 | NFR-02 | Import checker directly | Runs with no graph/LLM/network | Normal | Unit (collection) |
| O4-T-16 | NFR-03 | Benchmark WITH vs WITHOUT gate; complete and missing-evidence inputs | p50/p95 added latency recorded; < approved bound | Benchmark | Benchmark (Member F) |
| O4-T-17 | FR-03 | Parameterized: each required report key entirely absent from the state | Each classified `missing`; exact failing set; `REVIEW` | Negative | Unit |
| O4-T-18 | FR-11, FR-15 | Unit: unknown key raises. Integration: unknown key through wired path | `ValueError`; authoritative publication aborted; not presented as normal `REVIEW` | Negative | Unit + Integration |
| O4-T-19 | FR-07, FR-12, FR-13, INV-01 | Original body contains `Buy`; required evidence incomplete; real Graph/CLI path | Pre-gate no published Buy; post-gate `REVIEW` on enabled surfaces; body preserved and labelled unapproved | Negative | Unit + Integration |
| O4-T-20 | NFR-05 | Existing suite run with gate not wired into runtime | Current behavior unchanged; existing tests pass | Regression / Backward compatibility | Regression (Member F) |
| O4-T-21 | NFR-06 | Completed downgraded run; inspect existing artefacts | Runtime structured result available at capture point; effective rating reconstructable; durability documented pending | Auditability | Artefact inspection |
| O4-T-22 | NFR-07, FR-14 | Change-set and implementation review | One new module + approved integration points; no rating-logic change; no out-of-scope rules | Manual scope review (not an automated test) | Manual review |
| O4-T-23 | FR-07, FR-13, INV-01/03 | Fake CLI stream emits a PM `Buy` body before the gate sees a missing required report; real CLI entry point | Before gate, PM message/report text buffered; no published Buy; after gate, enabled surfaces `REVIEW`; preserved body non-authoritative | Negative integration | Integration (offline CLI) |
| O4-T-24 | FR-03, O5 boundary | Case A: O5 filtered-empty but selected News Analyst `news_report` non-empty. Case B: News Analyst selected and `news_report` missing/empty | A: no downgrade from filtered-empty (filtered-empty is a status, not a missing report). B: `REVIEW` with exact failing set == {`news_report`} | Boundary | Unit |
| O4-T-25 | FR-16, INV-02, INV-05 | (a) `final_rating` and parsed body agree; (b) `final_rating` absent, body supplies rating; (c) both clear but disagree; (d) original `REVIEW` | (a) agree preserved; (b) body rating used; (c) `REVIEW` with conflict reason; (d) stays `REVIEW` | Negative | Unit |

---

## O5 — Macro News Filter

v2.0 O5 plan: case matrix, detailed cases, invariant rows and regression. Send its DEV20 JSON fixture with this file.

### Case matrix

| Test | Layer | Req/Fit | Blocker |
|---|---|---|---|
| T01 | S | 01/04/07 FC-01 | labels (E+reviewer) |
| T02 | S | 02 FC-02 | labels |
| T03 | S/A | 03 | D5 for T03c |
| T04 | S/A | 03/05 | — |
| T05 | S | 02 | — |
| T06 | S | 02 | labels |
| T07 | S | 04 | — |
| T08 | S | 01/07 | rule approval |
| T09 | S | 01/04 | labels |
| T10 | S/A | 05 | E supported set |
| T11 | S/A | 05 | AM-01/25 |
| T12 | S | 04 | — |
| T13 | A/R/S | 03/05 | C7 hook, D5 |
| T14 | S | 06/08 | — |
| T15 | A | 09 FC-06 | C6 insertion; F1/F2 confirmed at `8c7eec3` only |
| T16 | S/A | 08 | F2 confirmed at `8c7eec3`; O5 testing pending |
| T17 | S | 10 | F4 runner |
| T18 | A | 07 | data,D |
| T19 | S | 02 | labels |
| T20 | S | 02/03 | — |
| I1–I12 | A | invariants | C/D6 |
| RT-1..RT-4 | R | 09 | C (RT-3) |

---

### T01 — DEV20 K=20

- Expected: selected ID set = `expected.k20_expected_selected_set` mapped via `fixture_key_to_id`; per-ID primary: M01/M02/M03/M04/I02/I03/I04 => MONETARY_POLICY; I01 => INFLATION; A01..A04 => ECONOMIC_ACTIVITY; matched_topics = labels (request-ordered); N01-N08 `REJECTED/NO_MACRO_EVIDENCE`; counts `{20,12,0,8,0,0,0,0}` (selected set 12; buckets 7/1/4).
- Status: Not run. Labels Pending.

### T02 — K=6 (actual IDs)

- Expected: `selected` actual IDs **equal `expected.k6_order_ids`** = `[o5:5bac9b8abe6d5ca1d080daddc17790be, o5:d55befa5f36ac3b155868409c5f899cf, o5:5c49d34495cd1dbf9c2eeb2e2ddc914d, o5:58f3c5dd5bc2f436c98fc012baf182f9, o5:561859c0dd24950172c101ba3de0418b, o5:44df14dcd79b73454a0aead746a40905]` (fixture keys **M01,I01,A01,M02,A02,M03**); counts `{20,6,6,8,0,0,0,0}`.
- Status: Not run. Labels.

### T03 — K=0 / all-irrelevant / all-invalid

- **T03a** DEV20 K=0 ⇒ `status=LIMIT_ZERO`; one `ZERO_LIMIT` decision per supplied position; classifier spy not called; **`input_count=20`, `skipped_zero_limit_count=20`, all other classification counts (selected/not_selected_limit/irrelevant/invalid/oow/duplicate) = 0**.
- **T03b** pool = the 8 N-records, K=3 ⇒ `NO_RELEVANT_NEWS`, `irrelevant_count=8`, others 0.
- **T03c** two records (JSON):
  ```json
  [{"candidate_id":"o5:aaaa0000000000000000000000000001","title":"","summary":"x","source":null,"url":null,"published_at":"2026-09-25T00:00:00Z"},
   {"candidate_id":"o5:aaaa0000000000000000000000000002","title":"No title","summary":"y","source":null,"url":null,"published_at":"2026-09-25T00:00:00Z"}]
  ```
  ⇒ `NO_RELEVANT_NEWS`, `invalid_count=2` (INVALID_TITLE), selected=0; adapter `empty_kind=ALL_INVALID`.
- Status: Not run. T03c wording blocked D5.

### T04 — Empty pool / upstream empty

T04a S `candidates=[]` ⇒ all-zero counts. T04b A `FakeSearch.news=[]` ⇒ "unavailable"/"not an absence". T04c A only out-of-window raw ⇒ baseline drops ⇒ coverage-gap.

### T05 — MP-only vs mixed MP/EA

- **T05a MP-only** (JSON):
  ```json
  [{"candidate_id":"o5:b00000000000000000000000000001","title":"Fed holds rates steady at 5.25 percent","summary":"","source":null,"url":null,"published_at":"2026-09-26T10:00:00Z"},
   {"candidate_id":"o5:b00000000000000000000000000002","title":"ECB cuts deposit rate by 25 basis points","summary":"","source":null,"url":null,"published_at":"2026-09-25T10:00:00Z"},
   {"candidate_id":"o5:b00000000000000000000000000003","title":"Bank of Japan keeps policy rate unchanged","summary":"","source":null,"url":null,"published_at":"2026-09-24T10:00:00Z"}]
  ```
  K=2 ⇒ `[o5:b…01,o5:b…02]`; counts `{3,2,1,0,0,0,0,0}`.
- **T05b mixed MP/EA** (JSON): MP `o5:c…01` "Fed holds rates unchanged" (2026-09-26T10:00:00Z), EA `o5:c…02` "US payrolls rise 187,000 as unemployment ticks up" (2026-09-27T10:00:00Z); K=2 ⇒ `[o5:c…01, o5:c…02]`; counts `{2,2,0,0,0,0,0,0}`.
- Status: Not run.

### T06 — K < topics (actual IDs)

- DEV20 K=2 ⇒ `selected` actual IDs **equal `expected.k2_order_ids`** = `[o5:5bac…, o5:d55b…]` (M01,I01); counts `{20,2,10,8,0,0,0,0}`.
- Status: Not run. Labels.

### T07 — Duplicate/invalid precedence

- T07a **same ID, wrong-type first**: A `{"candidate_id":"dup-1","title":123,"published_at":"2026-09-25T00:00:00Z"}` ⇒ INVALID_RECORD (no reservation); B `{"candidate_id":"dup-1","title":"Fed holds rates","published_at":"2026-09-26T00:00:00Z"}` ⇒ SELECTED.
- T07b valid-out-of-window first reserves (`dup-2`, `2026-09-10` OUT_OF_WINDOW) ⇒ in-window same ID ⇒ DUPLICATE_ID.
- T07c title-invalid reserving: A `{"candidate_id":"dup-3","title":""}` ⇒ INVALID_TITLE (reserved); B same ID valid ⇒ DUPLICATE_ID.
- T07d structurally valid duplicate with empty title: A `dup-4` valid reserves; B `dup-4`, `title=""` ⇒ DUPLICATE_ID (step 4 before step 6).
- T07e deepcopy mutation check.
- Status: Not run.

### T08 — Negative controls / multi-topic / summary-only

T08a FedEx REJECTED; T08b CPI Group REJECTED; T08c game inflation REJECTED; T08d `Fed holds rates at 5.25%, citing cooling CPI` ⇒ [MP,IN] primary MP; T08e tariffs+`inflation rose 4 percent` ⇒ IN; T08f S&P earnings ⇒ REJECTED; T08g summary-only `US CPI rose 3.0 percent year over year` ⇒ IN; T08h `Fed holds rates as CPI cools to 2.1 percent` ⇒ [MP,IN] primary MP. **T08i clause-crossing positive:** summary `Headline inflation eased toward the ECB target ... core inflation held steady` (I02 pattern) ⇒ R1 fires (ecb+held same field, cross-clause) ⇒ [MP,IN].

### T09 — DEV20 multi-topic

M01/M02/I02/I03/I04 matched per fixture labels; **M02 and I04 are MP+IN (primary MP)**; each selected once.

### T10 — Validation

T10a empty title→INVALID_TITLE; T10b "No title"→INVALID_TITLE; T10c direct selector string timestamp→INVALID_RECORD; T10c2 serialized invalid/naive via loader→INVALID_TIMESTAMP; T10d naive datetime→INVALID_TIMESTAMP; T10e missing candidate_id→INVALID_RECORD no reservation; T10f `limit=True`→INVALID_REQUEST; T10g `limit=-1`→INVALID_REQUEST; T10g2 `limit=2.5`→INVALID_REQUEST; T10i reversed window→INVALID_REQUEST; T10j unknown rules_version→INVALID_REQUEST; T10k2 summary/source/url absent/null→defaults; T10l non-dict candidate→INVALID_RECORD; conservation.

### T11 — Boundaries

T11a `2026-09-20T00:00:00Z` IN; T11b `2026-09-27T23:59:59.999999Z` IN; T11c `2026-09-28T00:00:00Z` OUT; T11d `2026-09-27T23:00:00-08:00` (=`2026-09-28T07:00:00Z`) OUT; T11e `2026-09-26T23:00:00+05:00` (=`2026-09-26T18:00:00Z`) IN; T11f raw `providerPublishTime` at midnight-after-end excluded.

### T12 — Decision completeness

Pool: SELECTED-eligible, INVALID_TITLE, OUT_OF_WINDOW, DUPLICATE, REJECTED ⇒ `len(decisions)=5`; `counts={5,1,0,1,1,1,1,0}`; conservation.

### T13 — Vendor / partial (complete)

**T13c** - two INDEPENDENT cases, each with fresh fakes, counters and its own evidence sink.

Shared scenario (per case, rebuilt from scratch):
- `limit=10`; `global_news_queries=["q1","q2","q3"]`; single-vendor `yfinance`; `common.time.sleep` patched to a **no-op**.
- Fake `yf.Search`: **q1 -> 1 in-window article**, **q2 -> 0**, **q3 -> raises `RuntimeError("boom")`**.
- Source path: `common.yf_retry` catches a non-`YFRateLimitError` and raises `VendorUnavailableError(f"Yahoo Finance request failed: {type(exc).__name__}")` (`common.py:88-91`); `router.route_to_vendor` catches `VendorUnavailableError` and, all-unavailable on a single-vendor chain, returns `vendor_unavailable(...)` (`router.py:237-242,265-266`). **The router does not emit O5 evidence.**
- Calls: 3 `yf.Search` invocations; **0 retries** (`RuntimeError` is not `YFRateLimitError`, `common.py:88-90`).
- Collector: pre-final-slice pool = **1** candidate (q1's article); q2 returns 0; q3 fails before adding. **No partial news published.**
- Selector never runs: `input_count`/`reason_counts`/`batch_id` are **not evaluated** (required-null, AM-44).

**Case T13c-D (direct vendor call):**
- Observation point: the private adapter's own evidence sink instance.
- Outcome: `get_global_news_yfinance(...)` **raises `VendorUnavailableError`** (message begins `Yahoo Finance request failed: RuntimeError`); no string returned.
- Assertions: 3 `yf.Search` calls; 0 retries; `pre_filter_candidate_count=1`; no article text reaches any caller output; sink holds **exactly one** event; that event `.variant == "V-PARTIAL"`; **no `V-VENDOR` event** in the sink.
- Per-event assertions split into presence and value:
  - presence: keys `batch_id`, `input_count`, `reason_counts`, `pre_filter_candidate_count`, `executed_query_count`, `queries_failed` each present;
  - value: `batch_id is None`; `input_count is None`; `reason_counts is None`; `pre_filter_candidate_count == 1`; `executed_query_count == 3`; `queries_failed == 1`.

**Case T13c-R (default single-vendor router call):**
- Fresh fakes/counters/sink; observation point: the adapter sink instance for this router invocation, plus the returned string.
- Outcome: `tools.get_global_news(...)` returns a **`str`** beginning `DATA_UNAVAILABLE: no configured vendor could serve get_global_news right now`; **no exception escapes**.
- Assertions: 3 `yf.Search` calls; 0 retries; pool = 1; no article text in the returned string; sink holds **exactly one** event; `.variant == "V-PARTIAL"`; **no `V-VENDOR` event** (router emits no O5 evidence and the adapter does not add one on this path).
- Same per-event presence/value assertions as T13c-D.

**Both cases assert:** the ordered event list is exactly `["V-PARTIAL"]`.

If C7 later decides the adapter must additionally emit `V-VENDOR` on re-raise, that is a **new schema/policy decision** requiring updates here and in Interface §4 - not assumed.

- **T13a** direct rate limit: `yf.Search` raises `YFRateLimitError`; sleep patched; expect `VendorUnavailableError` "rate limited".
- **T13b** routed rate limit: `str` begins `DATA_UNAVAILABLE`.
- **T13d** layered: public Yahoo path = coverage-gap for all-out-of-window; ALL_OUT_OF_WINDOW/ALL_INVALID only at direct seam. Malformed payload: non-dict `content` → flat branch (`news.py:38-53`) not a failure; non-dict **article** → `.get` failure (`news.py:22`).
- Status: Not run. C7 hook, D5.

### T14 — Determinism

100×; unique-ID permutation; no clock reads; conflicting duplicates not permutation-invariant.

### T15 — Real entry, filter-before-slice

- K=3; raw nested `content` records: q1 [N1 FedEx, N2 S&P]; q2 [N3 smartphone, **M1 Fed holds rates + summary "The Fed cited cooling inflation."**]; q3 never runs. All dates `2026-09-26T10:00..13:00Z` inside window. Pool after q2 = 4 ⇒ early stop (≥3).
- Expected `executed_query_count=2`, `pre_filter_candidate_count=4`, `selected_count=1` (M1), `irrelevant_count=3`, `not_selected_limit_count=0`; `yf.Search` called twice; baseline replay `[:3]`=[N1,N2,N3] excludes M1; slice-before-filter empty.
- Status: Not run. C6, F1/F2 confirmed for `8c7eec3` only; O5 collection/isolation untested.

### T16 — No network / no LLM / attempt recording

- Selector import boundary; isolation blocks sockets + `curl_cffi`; **harness records each attempted connect/DNS/HTTP call** (patch the connect/getaddrinfo/curl entry points to append to a list AND raise), and asserts the recorded attempt list is **empty** for passing tests, so business `try/except` cannot hide an attempt; config reset + temp `data_cache_dir`.
- Status: Not run. F2 confirmed for `8c7eec3` only; actual O5 collection/isolation untested.

### T17 — Performance (proposed)

1000 records, K=30, 5 warmups + 30 runs, nearest-rank p95 ≤ 100 ms (proposal). Runner Pending F4.

### T18 — Holdout

Handoff §4. Blocked data/labels/D.

### T19 — Requested-order/subset

Request `[INFLATION, MONETARY_POLICY]` on {M01,I01}: M01 matched [INFLATION,MONETARY_POLICY] primary INFLATION; I01 INFLATION; K=2 `[M01,I01]`.

### T20 — K > available

2 relevant (MP+EA), K=10 ⇒ both selected; `{2,2,0,0,0,0,0,0}`.

---

### Invariant / fault-injection

- **I1** stub ID∉input ⇒ V-INVARIANT INV-O5-02.
- **I2** stub returns an original out-of-window input (timestamp unchanged) ⇒ INV-O5-03; a stub that **changes** an in-window timestamp is INV-O5-01 (business-field modification), tested separately.
- **I3** duplicate output IDs ⇒ INV-O5-02. Multi-violation precedence INV-O5-04>INV-O5-02>INV-O5-03>INV-O5-01.
- **I4** import boundary; harness blocks network.
- **I5** sink emit raises ⇒ public string unchanged; `SINK_FAILED` via independent logger. **I5b** construction failure branch (Interface §7).
- **I6 required-field deletion (parameter table).** Start from a valid example per variant; remove ONE required key; expect rejection.
  Required keys = common required (`variant`,`action`,`trigger`,`disposition`,`rules_version`,`occurred_at`) plus variant-specific required, INCLUDING required-null keys. Only the mutated variant fails.

  | Case | Variant | Removed key | Expected |
  |---|---|---|---|
  | I6-VS-1 | V-SELECTED | `batch_id` | reject |
  | I6-VS-2 | V-SELECTED | `input_count` | reject |
  | I6-VS-3 | V-SELECTED | `selected_count` | reject |
  | I6-VS-4 | V-SELECTED | `reason_counts` | reject |
  | I6-VS-5 | V-SELECTED | `executed_query_count` | reject |
  | I6-VS-6 | V-SELECTED | `pre_filter_candidate_count` | reject |
  | I6-FE-1 | V-FILTERED-EMPTY | `batch_id` | reject |
  | I6-FE-2 | V-FILTERED-EMPTY | `input_count` | reject |
  | I6-FE-3 | V-FILTERED-EMPTY | `selected_count` | reject |
  | I6-FE-4 | V-FILTERED-EMPTY | `reason_counts` | reject |
  | I6-FE-5 | V-FILTERED-EMPTY | `executed_query_count` | reject |
  | I6-FE-6 | V-FILTERED-EMPTY | `pre_filter_candidate_count` | reject |
  | I6-FE-7 | V-FILTERED-EMPTY | `empty_kind` | reject |
  | I6-LZ-1 | V-LIMIT-ZERO | `batch_id` (required-null key) | reject |
  | I6-LZ-2 | V-LIMIT-ZERO | `input_count` | reject |
  | I6-LZ-3 | V-LIMIT-ZERO | `executed_query_count` | reject |
  | I6-LZ-4 | V-LIMIT-ZERO | `pre_filter_candidate_count` | reject |
  | I6-UE-1 | V-UPSTREAM-EMPTY | `batch_id` (required-null) | reject |
  | I6-UE-2 | V-UPSTREAM-EMPTY | `input_count` (required-null) | reject |
  | I6-UE-3 | V-UPSTREAM-EMPTY | `selected_count` (required-null) | reject |
  | I6-UE-4 | V-UPSTREAM-EMPTY | `reason_counts` (required-null) | reject |
  | I6-UE-5 | V-UPSTREAM-EMPTY | `executed_query_count` | reject |
  | I6-UE-6 | V-UPSTREAM-EMPTY | `pre_filter_candidate_count` | reject |
  | I6-VV-1 | V-VENDOR | `vendor` | reject |
  | I6-VV-2 | V-VENDOR | `method` | reject |
  | I6-VV-3 | V-VENDOR | `batch_id` (required-null) | reject |
  | I6-VV-4 | V-VENDOR | `input_count` (required-null) | reject |
  | I6-VV-5 | V-VENDOR | `selected_count` (required-null) | reject |
  | I6-VV-6 | V-VENDOR | `reason_counts` (required-null) | reject |
  | I6-VV-7 | V-VENDOR | `pre_filter_candidate_count` (required-null) | reject |
  | I6-PA-A1 | V-PARTIAL branch A | `queries_failed` | reject |
  | I6-PA-A2 | V-PARTIAL branch A | `executed_query_count` | reject |
  | I6-PA-A3 | V-PARTIAL branch A | `pre_filter_candidate_count` | reject |
  | I6-PA-A4 | V-PARTIAL branch A | `input_count` (required-null) | reject |
  | I6-PA-A5 | V-PARTIAL branch A | `reason_counts` (required-null) | reject |
  | I6-PA-A6 | V-PARTIAL branch A | `batch_id` (required-null) | reject |
  | I6-PA-B1 | V-PARTIAL branch B | `queries_failed` | reject |
  | I6-PA-B2 | V-PARTIAL branch B | `pre_filter_candidate_count` | reject |
  | I6-IV-1 | V-INVARIANT | `violated_invariant` | reject |
  | I6-IV-2 | V-INVARIANT | `batch_id` | reject |
  | I6-IV-3 | V-INVARIANT | `pre_suppression_selected_count` | reject |
  | I6-IV-4 | V-INVARIANT | `published_selected_count` | reject |
  | I6-IR-1 | V-INVALID-REQUEST | `field` | reject |
  | I6-IR-2 | V-INVALID-REQUEST | `reason` | reject |
  | I6-IR-3 | V-INVALID-REQUEST | `rules_version` (required-null) | reject |
  | I6-RV-1 | V-SELECTED | `rules_version` (missing) | reject |
  | I6-RV-2 | V-FILTERED-EMPTY | `rules_version` (missing) | reject |
  | I6-RV-3 | V-LIMIT-ZERO | `rules_version` (missing; null allowed, absent not) | reject |
  | I6-RV-4 | V-UPSTREAM-EMPTY | `rules_version` (missing) | reject |
  | I6-RV-5 | V-VENDOR | `rules_version` (missing) | reject |
  | I6-RV-6 | V-PARTIAL | `rules_version` (missing) | reject |
  | I6-RV-7 | V-INVARIANT | `rules_version` (missing) | reject |
  | I6-RV-8 | V-INVALID-REQUEST | `rules_version` (missing; null allowed) | reject |
  | I6-COM-1..5 | any variant | remove one of `variant`,`action`,`trigger`,`disposition`,`occurred_at` | reject |

  New across v0.5.3: complete V-LIMIT-ZERO, V-UPSTREAM-EMPTY and V-VENDOR coverage, and required-null keys are included as required.

- **I7 extra-key rejection.** (F confirmed this TEST DESIGN.) Add a key not listed for the variant (e.g. `vendor` on V-SELECTED; `input_count` on V-INVALID-REQUEST; `selected_count` on V-PARTIAL): reject.

- **I8 legal/illegal triples.** (F confirmed this TEST DESIGN.) Interface §4.3: M1-M11 pass; X1-X6 fail; includes one passing V-VENDOR case for each closed trigger `VENDOR_TIMEOUT`, `VENDOR_RATE_LIMIT`, `VENDOR_PAYLOAD_INVALID`, `VENDOR_UNAVAILABLE`.

- **I9 `rules_version`: schema vs emission behavior.** The schema cannot distinguish stages by itself (no stage field on the event); the TEST SETUP supplies the stage.
  - **I9-a (BUILDER-ONLY unit scenario, not an integration scenario):** the test **directly constructs** a V-VENDOR evidence object for a stage where rules have not yet been resolved. It does **not** manufacture a production vendor failure and is **not** an invalid-request integration scenario. Expected: `rules_version` key **present and `None`**; missing key fails; any non-null value fails. Invalid/missing *request* `rules_version` follows the separate **V-INVALID-REQUEST** contract (Interface §4.1), not I9-a.
  - **I9-b (failure AFTER successful rule resolution):** setup - valid `rules_version` resolved, then `yf.Search` raises `RuntimeError`; fault location - retrieval loop; observation - adapter sink. Expected: `rules_version` **present and equal to the resolved string** (e.g. `o5-rules-v1.1-draft`); **missing key fails**; `None` fails.
  - Generated for the V-VENDOR builder. **Reachability:** the production Yahoo path always resolves rules from config before retrieval, so **I9-a is an evidence-builder/unit-seam case**; I9-b is the reachable integration case. This is stated, not an invented production path.
  - Non-V-VENDOR `rules_version` nullability follows Interface §4.1 (present-null only for V-INVALID-REQUEST); present-null on V-SELECTED fails; absent always fails.

- **I10 V-PARTIAL branch/field/state matrix + count constraints.**
  - Branch discriminator: **branch A iff `pre_filter_candidate_count >= 1`; branch B iff `pre_filter_candidate_count == 0`.**
  - 18 explicit cases over {branch A, branch B} x {`batch_id`, `input_count`, `reason_counts`} x {present-null, missing, present-non-null}:

    | Case | Branch | Field | State | Expected |
    |---|---|---|---|---|
    | I10-A-bi-1 | A | batch_id | present null | accept |
    | I10-A-bi-2 | A | batch_id | missing | reject |
    | I10-A-bi-3 | A | batch_id | present non-null | reject |
    | I10-A-ic-1 | A | input_count | present null | accept |
    | I10-A-ic-2 | A | input_count | missing | reject |
    | I10-A-ic-3 | A | input_count | present non-null | reject |
    | I10-A-rc-1 | A | reason_counts | present null | accept |
    | I10-A-rc-2 | A | reason_counts | missing | reject |
    | I10-A-rc-3 | A | reason_counts | present non-null | reject |
    | I10-B-bi-1 | B | batch_id | present null | accept |
    | I10-B-bi-2 | B | batch_id | missing | reject |
    | I10-B-bi-3 | B | batch_id | present non-null | reject |
    | I10-B-ic-1 | B | input_count | present null | accept |
    | I10-B-ic-2 | B | input_count | missing | reject |
    | I10-B-ic-3 | B | input_count | present non-null | reject |
    | I10-B-rc-1 | B | reason_counts | present null | accept |
    | I10-B-rc-2 | B | reason_counts | missing | reject |
    | I10-B-rc-3 | B | reason_counts | present non-null | reject |

  - **Four complete valid examples** (schema/builder cases; `queries_failed/executed_query_count` pairs below):

    | Case | Branch | queries_failed/executed_query_count | pre_filter_candidate_count | required-null fields | Expected |
    |---|---|---|---|---|---|
    | I10-A-11 | A | 1/1 | 1 | batch_id, input_count, reason_counts | accept |
    | I10-A-33 | A | 3/3 | 2 | batch_id, input_count, reason_counts | accept |
    | I10-B-11 | B | 1/1 | 0 | batch_id, input_count, reason_counts | accept |
    | I10-B-33 | B | 3/3 | 0 | batch_id, input_count, reason_counts | accept |

  - Count constraints (both branches):
    - `executed_query_count` and `queries_failed` are **integers excluding booleans**.
    - `1 <= queries_failed <= executed_query_count`.
    - `pre_filter_candidate_count` is a **nonnegative integer excluding booleans**; **Branch A requires >= 1**, **Branch B requires 0**.
    - Rejections retained: `queries_failed=0`; `queries_failed>executed_query_count`; negative counts; floats (`3.0`); strings (`"3"`); booleans (`True`).
    - Prohibited keys on both branches: `empty_kind`,`violated_invariant`,`vendor`,`method`,`field`,`reason`,`selected_count`; adding any -> reject (I7).
  - **Reachability caveat:** these are **schema/builder** cases. The current fail-fast retrieval loop cannot produce some schema-valid combinations (e.g. it stops at the first failing query), so **not every schema-valid example is claimed reachable** through production retrieval.

  - Preserved: **V-SELECTED requires `executed_query_count`** (missing -> reject).
  - Status: **AM-44** (branch A `input_count`/`reason_counts` required-null) confirmed by F as a design.

- **I11** correct ID, modified title/summary ⇒ INV-O5-01 business-field guard.
- **I12** summary changed, same IDs ⇒ `batch_id` differs.

---

### Regression

RT-1 `get_global_news` schema; RT-2 `get_news_yfinance` unchanged; RT-3 inherited macro-news tests (verified names, `tests/test_news_lookahead.py` + `tests/test_alpha_vantage_hardening.py::test_global_news_omitted_optionals_use_the_configured_defaults`) with owner-reviewed adaptation; RT-4 `get_news` schema + ticker header.

- **F status (v0.5.3-corrected-r2):** F has **closed** T13c-D/T13c-R independent sinks and the single `V-PARTIAL` assertions; the **I10 18 field-state cases**; and the **reviewed version-reference corrections**. This round's remaining corrections (I6 `rules_version` deletion rows, I9-a builder-only definition, I10 count constraints/valid examples, Interface §4.2 sync, M02 vocabulary paragraph) are **awaiting F verification**. The **whole test plan is NOT approved**. Still pending: C/D interface/runtime-policy decisions, **DEV20 human label sign-off**, and **performance runner/threshold confirmation**.

---

---

## O6 — Per-Agent Usage Tracker

v2.0 O6 §5. Its TC-O6-07 differs from the supplemental plan below.

### 5. Proposed Test Cases

| Test | Type | Input or action | Expected result | Requirement |
|---|---|---|---|---|
| TC-O6-01 | Normal | Feed the three calls in the FR-01 fixture. | Both analyst rows match the exact expected values. | FR-01 |
| TC-O6-02 | Boundary | Compare a completed call with missing usage to one reporting `0/0`. | The first has two unknown fields. The second has two complete zero totals. | FR-02 |
| TC-O6-03 | Negative | Feed `100/20` and `50/missing` for one analyst. | Input is `150`, complete. Output is `20`, partial. | FR-02 |
| TC-O6-04 | Concurrency | Start Market at `0.0 s` and News at `0.2 s`. Finish News at `1.0 s` with `80/15`, then Market at `1.5 s` with `100/20`. | Each analyst has one call. Market has `100/20` and `1.5 s`. News has `80/15` and `0.8 s`. | FR-01, NFR-01 |
| TC-O6-05 | Negative | Replay the start and completion notifications for one invocation. Separately, send a call that ends with an error and one that has only a start event. | Replays leave totals unchanged. Both other calls count once. An invocation that errors at 1.75 s after starting at 1.0 s contributes 0.75 s. A start-only invocation contributes 0 s while no terminal event is present. Both have unknown usage if no usage was reported. | FR-01, FR-02 |
| TC-O6-06 | Regression | Run the NFR-02 baseline fixture, then start a new analysis with events from News only. | The first run preserves all four baseline values. The second run has no Market row or prior-run totals. | NFR-01, NFR-02 |
| TC-O6-07 | Integration | Use the approved CLI path with a deterministic test model. Through the real Analyst subgraph, Market makes one ordinary call with `100/20` and News makes one `wrap_up` call with `80/15`. | The CLI shows exactly one call per Analyst with the expected tokens and discloses that first structured-call attribution is deferred. | FR-01, NFR-01 |
| TC-O6-08 | Boundary | Add one model call with no verified analyst identifier alongside known Market and News calls. | The named rows stay unchanged and `unattributed_calls=1` is visible; the summary does not claim full attribution. | FR-01 |

---

## O6 supplemental detailed specifications

Separate O6 draft: more precise setup and additional 07b, 09…14. Resolve TC-07 before approval.

### 3. Per-case specification

**TC-O6-01 (O6-FR-01) — normal rows**
- Setup: per-Analyst tracker + handler; inject invocations with `scope="analyst"`/`agent_key`; usage as `{"input_tokens":100,"output_tokens":20,"total_tokens":120}` etc.; controlled clock.
- Assert: Market = 2 calls, 150/30, 1.5 s; News = 1, 80/15, 0.8 s; each counted once.

**TC-O6-02 (O6-FR-02) — missing vs explicit zero**
- Setup: one call with no `usage_metadata`; one with `{"input_tokens":0,"output_tokens":0,"total_tokens":0}`.
- Assert: first → both `Unknown`; second → complete zero totals.

**TC-O6-03 (O6-FR-02) — partial completeness**
- Setup: calls `100/20` and `50/missing` (`output_tokens` absent).
- Assert: input 150 complete; output 20 partial.

**TC-O6-04 (O6-FR-01, O6-NFR-01) — synthetic out-of-order (handler unit test)**
- Setup: **pure handler unit test with synthetic events** (not real subgraph); controlled clock; Market start@0.0/end@1.5; News start@0.2/end@1.0.
- Assert: Market 100/20/1.5 s; News 80/15/0.8 s. **Each invocation contributes only to the row matching its trusted `agent_key`, with zero contribution to the other row** (no cross-attribution).

**TC-O6-05 (O6-FR-01, O6-FR-02) — duplicate / error / start-only**
- Setup: replay start+end for one invocation; one errored call; one start-only call.
- Assertions (exact, observable): **duplicate-event replay leaves totals unchanged** (exact equality on call count, tokens, and duration after replay); an errored call counts once; a start-only call counts once.
- Duration rules (exact): **an invocation that starts at 1.0 s and errors at 1.75 s contributes 0.75 s**; **a start-only invocation contributes 0 s while no terminal event is present**; missing usage reads as `Unknown`.
- **Dedup key is TBD** (implementation detail — not asserted).

**TC-O6-06 (O6-NFR-01, O6-NFR-02) — baseline + cross-run isolation (handler level)**
- Setup: baseline fixture (`llm_calls=1,tool_calls=1,tokens_in=100,tokens_out=20`); then a new tracker/run with News-only events.
- Assert: baseline preserved; second run has no Market row or prior totals.

**TC-O6-07 (O6-FR-01, O6-NFR-01) — real subgraph: ordinary + wrap_up for same Analyst**
- Setup: `ScriptedModel`-style controlled model via `_graph` (fake vendor deps). For **one Analyst**: an ordinary call (100/20) with a controlled duration of **1.0 s**, and a `wrap_up` call (80/15) with a controlled duration of **0.5 s**.
- Assert at the **actual model callback**: `scope="analyst"` and the expected `agent_key` present for **both** the ordinary and the `wrap_up` call; then assert the resulting row totals: **2 calls, 180 input tokens, 35 output tokens, and 1.5 s cumulative duration**.
- **Ordinary and `wrap_up` calls use the same rules for counts, tokens, and duration** (no special-casing of wrap_up in attribution or accumulation).
- **Subcase TC-O6-07b (proposed) — two selected Analysts in the same analysis run**
  - Setup: real Analyst subgraphs for **two** selected Analysts (e.g. Market and News) in one run, controlled model + fake vendor deps.
  - Assert at the **actual model callback**: each call carries the **expected `spec.key`** of its Analyst; then assert **exact per-Analyst call and token totals**. **Each invocation contributes only to the row matching its trusted `agent_key`, with zero contribution to the other row** (no cross-attribution).
- Depends: **A's `setup.py` binding point**; metadata propagation (planned).

**TC-O6-08 (O6-FR-01) — unattributed surface**
- Setup: known Market+News plus one in-scope call with no verified identity.
- Assert: named rows unchanged; `unattributed_calls=1` visible.

**TC-O6-09 [proposed] (O6-NFR-02) — `get_stats()` compatibility**
- Setup: one completed call (100/20) + one tool call.
- Assert: exactly `{llm_calls:1, tool_calls:1, tokens_in:100, tokens_out:20}`; new interface separate.

**TC-O6-10 [proposed] (O6-FR-01) — invalid identity (kept separate from out-of-scope)**
- Setup: in-scope `scope="analyst"` with `agent_key=""` / unknown value.
- Assert: `unattributed_calls` increments; no named row.

**TC-O6-11 [proposed] (O6-FR-01) — real-subgraph out-of-scope exclusion**
- Setup: real subgraph; a **demonstrably out-of-scope** call (e.g. Research Manager/Trader/risk/PM, carrying no analyst scope).
- Assert: the call changes **neither any named Analyst row nor `unattributed_calls`**. Compare both before and after the call.
- Status: **Proposed**. The Analyst binding boundary and the meaning of the scope label still require A's confirmation before this case is approved.

**TC-O6-12 [proposed] (O6-FR-01) — CLI disclosure**
- Setup: CLI path with controlled model.
- Assert: **the CLI explicitly discloses both (a) that attribution of the first structured call is deferred and (b) that named rows include only calls from selected Analysts whose call identity has been verified.**

**TC-O6-13 [proposed] (O6-FR-01, O6-NFR-01) — wrap_up attribution**
- Setup: force `max_tool_rounds` low → `wrap_up` (`setup.py:83` → `turn.py:20-25`).
- Assert: wrap_up call carries same `agent_key` as its Analyst and is attributed once. (Complements 07 by isolating wrap_up.)

**TC-O6-14 [proposed] (O6-NFR-01, O6-NFR-02) — same-entrypoint two-run CLI isolation**
- Setup: run **two analyses through the same CLI entrypoint in the same process** with the controlled model; run 2 emits News-only events.
- Assert: **run 2 contains only its own events** — no Market row, no residual call/token totals from run 1; the first run is unaffected.

---

## F handoff checklist

- [ ] Resolve the six reconciliation rows with the owners and record the new test-plan versions.
- [ ] Keep O5 DEV20 fixture with the catalogue; confirm label sign-off and which plan copy is authoritative.
- [ ] Separate offline unit, offline integration, benchmark, manual/live and manual-review cases.
- [ ] Confirm real collection and offline isolation for actual test paths; then add pytest node IDs.
- [ ] Record actual pre-code test-plan and OpenCode execution-plan approvals with reviewer, scope, version and timestamp.
- [ ] Attach actual CI run links/results later; this catalogue asserts none.
