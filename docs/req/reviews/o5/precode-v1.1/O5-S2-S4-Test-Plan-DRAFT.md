# S2–S4 Test Plan — FINAL DRAFT (for F)
Status: DRAFT for F review — not approved. S2–S4: Not run. No implementation or test code has been edited.

## 0. Verified baseline
| Item | Value |
| --- | --- |
| Baseline | 5cdd7589cc73817133a7ca73cf768fc02d0cd19a (= origin/main; S1 merged via PR #22) |
| Interface reference | docs/req/reviews/o5/precode-v1.1/O5-Interface-Reference-r2.md, read from origin/docs/o5-precode-review-v1.1 @ fc4498f4ece42923ffb6e10c342bf3aebd5a1709 |
| Detailed cases | O5-Detailed-Test-Cases-Reference-r2.md (same SHA) |
| AGENTS.md / Prompt.md | Not read; not present in the repository |
| S1 status | Complete and unchanged — macro_news_filter.py, test_o5_macro_news_filter.py, test_o5_invariants.py, DEV20 fixture |
| Test tree | test/offline/ (there is no tests/o5/) |
## 1. Requirement mapping
1.1 REQ-O5-08 is cost/isolation only: zero added vendor/network requests, zero LLM calls, zero input mutation, offline with no credentials. Not a persistence requirement.

1.2 Evidence sink policy comes from development_contract.o5.evidence_path, development_contract.o5.sink_failure and Interface §7. Persisting to the O2 run directory is S5.

1.3 REQ-O5-01/02 at S4 verify the integration relation — request → validation → conversion → invariant check → private evidence exit — with public API and selector behaviour unchanged. Classification/allocation logic is verified at S1.

1.4 Batch classification

| Class | Items |
| --- | --- |
| Planned complete | request-validation ordering; K=0; zero vendor/LLM/network/credential/mutation checks; production evidence builder (in memory); test InMemorySink; private evidence exit; I1/I3/I11/I2; conversion; T04b/T04c; new T04d; I9-a |
| Conditional / proposed | I5 simulated sink emit failure and a separately named evidence-builder failure diagnostic (§6; approval requested, not assumed); I9-b/I13 execute only after E lands the private seam |
| S5 | real JsonlEvidenceSink honouring evidence_path/sink_failure; run_dir handoff; JSONL persistence; I5b sink construction failure and filesystem I5 |
| S6 | T17 performance measurement only |
## 2. T04 correction (from the detailed reference)
The reference defines T04 as "Empty pool / upstream empty", and the three sub-cases are:

| ID | Layer | Definition | Stage |
| --- | --- | --- | --- |
| T04a | S | pure selector, candidates=[] ⇒ all-zero counts | S1 — already implemented and passing; not an S3/S4 test |
| T04b | A | FakeSearch.news=[] ⇒ "unavailable"/"not an absence" | S3 |
| T04c | A | only out-of-window raw items ⇒ existing collector drops them ⇒ coverage-gap | S3 |
New S4 case — batch-local ID T04d (accepted by F, not a new Registry ID). Call the public entry with `as_of_date="2026-09-28"`, `look_back_days=2`, `limit=1`; the first `FakeSearch.news` response contains exactly one nested Yahoo article: `content.title="Company reports quarterly earnings"`, `content.summary=""`, `content.provider.displayName="FixtureWire"`, `content.canonicalUrl.url="https://example.test/earnings"`, `content.pubDate="2026-09-27T10:00:00Z"`. It is valid, in-window, and has no macro anchor/context. The collector stops after this first query. Expect `V-FILTERED-EMPTY`, `input_count=1`, `pre_filter_candidate_count=1`, `executed_query_count=1`, `selected_count=0`, `reason_counts={"NO_MACRO_EVIDENCE":1}`, and one `IRRELEVANT` decision. The `empty_kind` must denote all valid input as irrelevant (`ALL_IRRELEVANT` proposed; D must confirm the literal before its exact assertion). This is separate from T04a empty selector input, T04b empty vendor feed, T04c window-empty feed, and T03c all-invalid records.

## 3. Evidence variants — the eight from Interface §4
V-INVALID-REQUEST, V-LIMIT-ZERO, V-UPSTREAM-EMPTY, V-FILTERED-EMPTY, V-VENDOR, V-PARTIAL, V-INVARIANT, V-SELECTED. Sink construction/emit failures are Interface §7 diagnostics, not evidence variants.

## 4. Cases and independent expectations
| Case | Expected | File |
| --- | --- | --- |
| I9-a-1 | V-VENDOR control: rules_version present-and-None accepted | test/offline/test_o5_evidence_builder.py |
| I9-a-2 | rules_version missing ⇒ rejected | same |
| I9-a-3 | rules_version present non-None at pre-resolution ⇒ rejected | same |
| T03a-A | limit=0 ⇒ 0 yf.Search calls; V-LIMIT-ZERO, input_count=0, executed_query_count=0, pre_filter_candidate_count=0, batch_id=null | test/offline/test_o5_macro_news_integration.py |
| T10f/g/g2/i/j | V-INVALID-REQUEST; 0 retrieval calls; raises before fetch | same |
| T13a | direct: raises VendorUnavailableError "rate limited" | same |
| T13b | routed: str begins DATA_UNAVAILABLE | same |
| T13c-D | exactly one V-PARTIAL, zero V-VENDOR; 3 calls, 0 retries, pool 1 | same |
| T13c-R | exactly one V-PARTIAL, zero V-VENDOR; routed DATA_UNAVAILABLE | same |
| T13d | public path all-out-of-window ⇒ coverage-gap; empty_kind at the seam only | same |
| I9-b | post-resolution V-VENDOR; rules_version present non-None; one event; S3, after the seam | same |
| I13 | post-resolution V-PARTIAL; one event; no V-VENDOR; S3, after the seam | same |
| T04b | FakeSearch.news=[] ⇒ V-UPSTREAM-EMPTY; "unavailable"/"not an absence" phrasing | same |
| T04c | only out-of-window raw ⇒ collector drops ⇒ V-UPSTREAM-EMPTY; coverage-gap | same |
| T04d (batch-local) | fixed 2026-09-27 Yahoo article under 2026-09-28 / 2-day / K=1 request ⇒ V-FILTERED-EMPTY; input_count=1, pre_filter_candidate_count=1, executed_query_count=1, selected_count=0, reason_counts={"NO_MACRO_EVIDENCE":1}; irrelevant empty_kind literal and filtered-empty wording await D | same |
| I1 | out-of-input ID ⇒ V-INVARIANT, INV-O5-02 | test/offline/test_o5_invariants.py |
| I3 | duplicate output IDs ⇒ V-INVARIANT, INV-O5-02 | same |
| I2 | original out-of-window input ⇒ INV-O5-03 | same |
| I11 | business-field modification ⇒ INV-O5-01 | same |
| time-tamper | stub that changes a timestamp ⇒ INV-O5-01, judged separately from I2 | same |
| I5 (proposed scope) | Inject sink `emit` failure after a successful selection; return the same public string and selected result as the working-sink control, log `SINK_FAILED` through the independent logger, and do not claim persisted evidence. The failed sink retains no `V-SELECTED` event; the user still receives the normal result. | test/offline/test_o5_macro_news_integration.py |
| Builder-failure diagnostic (proposed, not I5b) | Inject `_build_o5_evidence` failure separately; preserve the same honest business result as the control, log `SINK_FAILED`, and claim no stored event. Do not count this as I5b coverage. | test/offline/test_o5_macro_news_integration.py |
| I5b (S5) | Sink construction failure at the real sink factory; separately verify the Registry `SINK_FAILED` policy and unchanged honest result. No builder exception is used as its surrogate. | deferred to S5 |
| T01/T02/T05/T06/T19/T20 via entry | same IDs/order/counts as the S1 selector | integration |
| T15 | filter-before-slice: pool 4, K=3, executed_query_count=2 | same |
| T16 | zero added requests/LLM; harness-level attempt recording | test/offline/test_o5_regression.py |
| RT-1..RT-4 | schemas, ticker path, str API unchanged | same |
Empty-pool (T04a, S1), vendor-empty (T04b), window-empty (T04c) and filtered-empty (T04d) remain four separate cases. Adapter expectations are fixed literals, never generated by calling the selector under test.

## 5. Offline isolation and regression
test/offline/conftest.py blocks sockets and curl_cffi; unchanged; new files must not carry the integration marker. RT-1..RT-4 plus inherited tests/test_news_lookahead.py and tests/test_alpha_vantage_hardening.py::test_global_news_omitted_optionals_use_the_configured_defaults must pass.

## 6. Evidence failure boundaries (approval requested, not assumed)
I5 is a sink `emit` failure, observed through the real adapter with a failing in-memory sink. Compare its public string and selected records with a working-sink control for identical input: they must match. The independent `tradingagents.o5.evidence` logger records `SINK_FAILED`; no JSONL persistence or successfully retained `V-SELECTED` is claimed. A separate proposed builder-failure diagnostic injects `_build_o5_evidence` failure and checks the same honest-result, diagnostic, and no-false-retention policy. It has no I5b label. I5b remains S5 because it is specifically failure to construct the production sink; this batch does not introduce a public sink/factory interface. F and A must approve the two proposed in-memory failure checks for this batch; otherwise they remain deferred.
