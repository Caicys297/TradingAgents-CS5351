# O5 S1 case inventory — v1.6 - formal S1 review request (approval pending)

Owner: E. Reviewer: F. Revised 2026-11-18. Previous v1.5/v1.5-r2 preparations retained unchanged. Stable filename retained. All cases **Not run**. No implementation or executable test code has been produced.

## 1. Exact authority and readiness

- Approved execution plan: [v1.4 at b5891ac534bf686989d0b670dca1d3e5b76b33e1](https://github.com/Caicys297/TradingAgents-CS5351/blob/b5891ac534bf686989d0b670dca1d3e5b76b33e1/docs/req/reviews/o5/precode-v1.1/O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md), section 5a S1. Its bytes are preserved in this package.
- [A's explicit execution approval and rules-version decision](https://github.com/Caicys297/TradingAgents-CS5351/pull/3#issuecomment-6917171487): `o5-rules-v1.1-draft` is selected by A; the choice is no longer pending, but its Registry reconciliation is still pending.
- [A's S1 clarification](https://github.com/Caicys297/TradingAgents-CS5351/pull/3#issuecomment-6943145906): S1 does not wait for C/D interfaces or unpublished project AGENTS.md/Prompt.md. Read the merged Registry, approved execution plan, F-approved applicable test plan and actual code; record baseline, approval links, allowed files and session evidence.
- [F's v1.4 document closure](https://github.com/Caicys297/TradingAgents-CS5351/pull/3#pullrequestreview-5920289874) closes mapping, I9-b/I13 and T17 document issues; it is not formal test-plan approval.
- **Registry correction merge SHA and inspected main:** `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`, verified merged through GitHub PR #9 and present on origin/main. Statement, contract and DEV20 all use `o5-rules-v1.1-draft`.
- **PR #3 document commit:** to be recorded in the submission note after committing; never use a file's own commit SHA as self-referential content.
- **F formal S1 approval: PENDING.** This v1.6 requests review of the exact cases/parameters below. A's approved execution-plan bytes remain unchanged.

The S1 row lists T01-T12, T14, T19, T20 and I6-I10 **schema cases**. It is not permission to pull adapter, builder or emission assertions into S1 merely because they share a parent ID. The case-by-case projection below is proposed to F, not an already-approved test scope.


### 1a. Verified baseline and source precedence (2026-11-18)

PR #9 is merged at `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`; PR #3 was inspected at b5891ac534bf686989d0b670dca1d3e5b76b33e1 before this update. Branch-only e4161e3 is historical, not the merge baseline.

Compared with `c861d0307238a3b763a35446f7da1245b1e8322a`, O5 requirements differ only in REQ-O5-01.statement's version literal. The entire O5 development contract, all other O5 requirement fields, rule catalog, mappings and DEV20 bytes are unchanged. O2 adds input_condensation_audit_note and narrows O2-FR-14.verification to TC-13/14; neither changes S1 expectations.

Merged Registry plus A's decision govern development; the approved execution plan defines the file/stage boundary; F must approve this S1 projection. R2-IN numeric-context/game exclusions in T08b/c come from source Requirements section 5.3 via Registry source_review, not additional anchor/context-array entries. Ask A/B if a contract conflict emerges; do not silently discard inherited exclusions.

B's manual Schema validation has a record according to A's supplied message. That record was not independently rerun here; Schema CI Gate remains unconnected. O5 evidence-schema tests cannot stand in for Registry Schema validation. See [course evidence matrix](./O5-S1-Course-Requirements-and-Evidence-v1.5-r2.md).

## 2. Proposed S1 file and behavior boundary

Proposed production file: `tradingagents/dataflows/macro_news_filter.py` only, containing the pure selector (validation, classification, allocation and result construction). Proposed test files: `test/offline/test_o5_macro_news_filter.py` for the selector rows, and `test/offline/test_o5_invariants.py` for static schema rows. A byte-identical DEV20 fixture copy may live under the already-approved `test/offline/fixtures/o5/` directory. No executable files are created by this document preparation.

No news.py edits, vendor/router entry, sink construction/emission, JSONL persistence, O2 run_dir, public output wording, shared configuration, CLI/Graph, CI, pyproject.toml or conftest.py changes are requested for S1. No evidence builder is introduced under the label of schema validation. Static schema checks use fixed dictionaries and the preserved Interface section 4 contract; passing them would not prove runtime emission or a production validator. F must approve the validation seam: controls and mutations must be evaluated against one explicit contract oracle independent of selector output, not a predicate invented merely to make its own test pass. This does not authorize adding a production builder/validator or another production file in S1.

No D-owned output-field spelling or negation-flag publication assertion is requested in S1. The Registry's negated-context policy is not repealed; its field-level integration acceptance remains outside this request, as A's stage clarification directs.

## 3. Common input definitions

`MP`, `IN`, `EA` mean MONETARY_POLICY, INFLATION, ECONOMIC_ACTIVITY. Default request: topics [MP,IN,EA], start_at 2026-09-20T00:00:00Z, end_at 2026-09-27T23:59:59.999999Z (inclusive), K=20, rules_version `o5-rules-v1.1-draft` **verified at `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`**. Both boundaries are aware datetimes.

`P(id, title=..., summary=..., at=...)` is a complete test-record recipe, not executable code. It means candidate_id=id, title="Fed holds rates", summary="", source=null, url=null, published_at=aware datetime 2026-09-25T00:00:00Z, with only the explicitly named overrides. This fills missing nonessential fields in older shorthand without changing validation precedence. Candidate IDs supplied to direct selector cases are opaque nonempty IDs; generated-ID recipes are not being substituted for duplicate tests.

For DEV20 load the exact [Registry fixture at the inspected baseline](https://github.com/Caicys297/TradingAgents-CS5351/blob/d36a677d4738efd365b6bbcf6f69f993acf8fd3c/docs/req/O5-Dev20-Fixtures-v0.5.3-DRAFT.json). SHA-256 `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6`. Parse valid RFC3339 values to aware datetimes and strip fixture_key in test setup; retain original business fields. Direct string/naive tests deliberately bypass that conversion. This setup does not create or test a production loader.

Counts are always ordered `(input_count, selected_count, not_selected_limit_count, irrelevant_count, invalid_count, out_of_window_count, duplicate_count, skipped_zero_limit_count)`. For a valid request, input_count equals the sum of the other seven, with one decision per input position. Invalid requests are rejected; do not fabricate normal classification counts for them.

DEV20 is a fixed **provisional development oracle**. Its current labels/orders are expectations, not independently verified human truth or proof of REQ-O5-07 quality thresholds. This preparation checks fixture identity and mapping, not classifier performance or human relevance.

## 4. Selector cases proposed for S1

Requirement numbers below abbreviate REQ-O5-NN. All expected values are specifications for review, not executed results. No row asserts adapter evidence emission.

| Case | Requirement / coverage | Complete input or exact fixture reference | Expected selector assertion |
|---|---|---|---|
| T01 | 01,04; 07 development oracle only | DEV20, K=20. | Selected actual-ID set equals mapped expected.k20_expected_selected_set; counts (20,12,0,8,0,0,0,0); matched topics/primary equal provisional labels; N01-N08 rejected. No human-quality acceptance claimed. |
| T02 | 02 | DEV20, K=6. | Actual IDs equal expected.k6_order_ids, keys M01,I01,A01,M02,A02,M03; counts (20,6,6,8,0,0,0,0). |
| T03a | 03 | DEV20, K=0. | LIMIT_ZERO; 20 ZERO_LIMIT decisions; input_count=20, skipped_zero_limit_count=20, all other categories zero; classifier not called. No vendor/event assertions. |
| T03b | 03 | DEV20 N01-N08 only, K=3. | NO_RELEVANT_NEWS; counts (8,0,0,8,0,0,0,0). |
| T03c | 03,05 | The two complete serialized records in active plan section 5 A-1; parse their valid timestamps in test setup; K=3. | NO_RELEVANT_NEWS; counts (2,0,0,0,2,0,0,0); both INVALID_TITLE. ALL_INVALID adapter wording is excluded. |
| T04a | 03,05 | Empty candidates, K=20, otherwise valid request. | Empty selection; all eight counts zero. No V-UPSTREAM-EMPTY or public-string assertion. |
| T05a | 02 | Parameter recent: the three complete MP records in r2 T05a, converted to aware timestamps; K=2. Parameter tie (new review detail): [P(c),P(a),P(b)] at the same default instant, K=2. | Recent: select first and second source records (Sep 26, Sep 25), comparing literal full IDs. Tie: select [a,b], decision for c is NOT_SELECTED_LIMIT; both counts (3,2,1,0,0,0,0,0). The tie parameter requires F approval; it is not previously executed coverage. |
| T05b | 02 | P(mp, title="Fed holds rates unchanged", at=2026-09-26T10:00:00Z), P(ea, title="US payrolls rise 187,000 as unemployment ticks up", at=2026-09-27T10:00:00Z); K=2. | IDs [mp,ea] despite newer EA; counts (2,2,0,0,0,0,0,0). |
| T06 | 02 | DEV20, K=2. | Actual IDs equal expected.k2_order_ids (M01,I01); counts (20,2,10,8,0,0,0,0). |
| T07a | 04,08 | Two P(dup-1) records: first title=123, second default valid title; K=2. | INVALID_RECORD then SELECTED; invalid structure must not reserve the ID; counts (2,1,0,0,1,0,0,0). |
| T07b | 04,08 | Two P(dup-2): first at=2026-09-10T00:00:00Z, second default in-window; K=2. | OUT_OF_WINDOW then DUPLICATE_ID; counts (2,0,0,0,0,1,1,0). |
| T07c | 04,08 | Two P(dup-3): first title="", second valid; both structurally complete with aware timestamps. | INVALID_TITLE then DUPLICATE_ID; counts (2,0,0,0,1,0,1,0). |
| T07d | 04,08 | Two P(dup-4): first valid, second title="" with all other fields structurally valid. | SELECTED then DUPLICATE_ID; counts (2,1,0,0,0,0,1,0). |
| T07e | 04,08 | Deep-copy DEV20 selector inputs/request before a K=6 call. | Input/request deep-equal to snapshot; no business-field rewrite. This does not claim runtime fault-injection I11 has run. |
| T08a | 01; 07 development controls only | One P(T08a, title="FedEx expands parcel delivery service", summary=""), K=1. | REJECTED; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08b | 01; 07 development controls only | One P(T08b, title="CPI Group reports quarterly earnings", summary=""), K=1. | REJECTED; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08c | 01; 07 development controls only | One P(T08c, title="Game inflation rises in a virtual economy", summary=""), K=1. | REJECTED; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08d | 01; 07 development controls only | One P(T08d, title="Fed holds rates at 5.25%, citing cooling CPI", summary=""), K=1. | [MP,IN], primary MP; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08e | 01; 07 development controls only | One P(T08e, title="Tariffs spark debate", summary="Inflation rose 4 percent."), K=1. | [IN], primary IN; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08f | 01; 07 development controls only | One P(T08f, title="S&P companies report earnings", summary=""), K=1. | REJECTED; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08g | 01; 07 development controls only | One P(T08g, title="Economic release", summary="US CPI rose 3.0 percent year over year"), K=1. | [IN], primary IN; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08h | 01; 07 development controls only | One P(T08h, title="Fed holds rates as CPI cools to 2.1 percent", summary=""), K=1. | [MP,IN], primary MP; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T08i | 01; 07 development controls only | One P(T08i, title="Economic release", summary="Headline inflation eased toward the ECB target; core inflation held steady."), K=1. | [MP,IN], primary MP; same-field matching only. Concrete control text instantiates the r2 shorthand and requires F review; it is not measured classifier output. |
| T09 | 01,04 | DEV20 M01,M02,I02,I03,I04, K=20. | Each matched [MP,IN], primary MP, selected once; compare fixture labels, without treating them as independently human-labelled truth. |
| T10a | 05; 08 input integrity where applicable | P(v) with title="" | INVALID_TITLE; invalid_count=1; no V-INVALID-REQUEST emission or public wording assertion. |
| T10b | 05; 08 input integrity where applicable | P(v) with title="No title" | INVALID_TITLE; invalid_count=1; no V-INVALID-REQUEST emission or public wording assertion. |
| T10c | 05; 08 input integrity where applicable | P(v) with published_at left as the STRING "2026-09-25T00:00:00Z" at the selector entry | INVALID_RECORD; no loader invoked; no V-INVALID-REQUEST emission or public wording assertion. |
| T10d | 05; 08 input integrity where applicable | P(v) with naive datetime 2026-09-25 00:00:00 (no timezone) | INVALID_TIMESTAMP; no V-INVALID-REQUEST emission or public wording assertion. |
| T10e | 05; 08 input integrity where applicable | P(v) with candidate_id key removed | INVALID_RECORD; ID not reserved; no V-INVALID-REQUEST emission or public wording assertion. |
| T10f | 05; 08 input integrity where applicable | [P(v)], request limit=True | INVALID_REQUEST; no normal selected result; no V-INVALID-REQUEST emission or public wording assertion. |
| T10g | 05; 08 input integrity where applicable | [P(v)], request limit=-1 | INVALID_REQUEST; no normal selected result; no V-INVALID-REQUEST emission or public wording assertion. |
| T10g2 | 05; 08 input integrity where applicable | [P(v)], request limit=2.5 | INVALID_REQUEST; no normal selected result; no V-INVALID-REQUEST emission or public wording assertion. |
| T10i | 05; 08 input integrity where applicable | [P(v)], start_at/end_at exchanged | INVALID_REQUEST; no normal selected result; no V-INVALID-REQUEST emission or public wording assertion. |
| T10j | 05; 08 input integrity where applicable | [P(v)], rules_version="unsupported-o5-version" | INVALID_REQUEST; unknown version not silently accepted; no V-INVALID-REQUEST emission or public wording assertion. |
| T10k2 | 05; 08 input integrity where applicable | P(v) in two runs: summary/source/url all absent, then all explicitly null | Apply contract defaults; same classification/order/counts; do not mutate input; no V-INVALID-REQUEST emission or public wording assertion. |
| T10l | 05; 08 input integrity where applicable | Candidates=[123] | INVALID_RECORD; counts (1,0,0,0,1,0,0,0); no V-INVALID-REQUEST emission or public wording assertion. |
| T11a | 05; INV-O5-03 containment | One P(T11a, at=2026-09-20T00:00:00Z); parse to an aware datetime retaining the offset; K=1. | SELECTED; input_count=1 and exactly one corresponding classification count. |
| T11b | 05; INV-O5-03 containment | One P(T11b, at=2026-09-27T23:59:59.999999Z); parse to an aware datetime retaining the offset; K=1. | SELECTED; input_count=1 and exactly one corresponding classification count. |
| T11c | 05; INV-O5-03 containment | One P(T11c, at=2026-09-28T00:00:00Z); parse to an aware datetime retaining the offset; K=1. | OUT_OF_WINDOW; input_count=1 and exactly one corresponding classification count. |
| T11d | 05; INV-O5-03 containment | One P(T11d, at=2026-09-27T23:00:00-08:00); parse to an aware datetime retaining the offset; K=1. | OUT_OF_WINDOW (2026-09-28T07:00:00Z); input_count=1 and exactly one corresponding classification count. |
| T11e | 05; INV-O5-03 containment | One P(T11e, at=2026-09-26T23:00:00+05:00); parse to an aware datetime retaining the offset; K=1. | SELECTED (2026-09-26T18:00:00Z); input_count=1 and exactly one corresponding classification count. |
| T12 | 04 | [P(keep), P(bad,title=""), P(old,at=2026-09-10T00:00:00Z), exact copy of P(keep), P(irrelevant,title="Local bookstore opens")], K=10. | One decision per input index: SELECTED, INVALID_TITLE, OUT_OF_WINDOW, DUPLICATE_ID, REJECTED; counts (5,1,0,1,1,1,1,0). |
| T14a | 06,08 | DEV20, identical request K=6, invoke 100 times. | Full deterministic selector result equality; no event timestamps or sink objects involved. |
| T14b | 06,08 | DEV20 unique-ID pool in original, reversed, and the fixed zero-based permutation [19,0,18,1,17,2,16,3,15,4,14,5,13,6,12,7,11,8,10,9], K=6. | Same selected ID order, classification by ID and counts; decisions.input_index follows the actual permutation, not a false full-list equality requirement. |
| T14c | 06,08 | DEV20 K=6; test-local trap on wall-clock reads reachable from selector. | No wall-clock read; result equals the deterministic reference result. No shared conftest edit. |
| T14d | 04,06 | Pair [P(conflict), P(conflict,title="Local bookstore opens")] then reverse order; K=1. | First structurally valid occurrence owns ID: first order SELECTED then duplicate; reverse order REJECTED then duplicate. Conflicting duplicates are intentionally not permutation-invariant. |
| T19 | 02 | DEV20 M01,I01; requested topics [INFLATION,MONETARY_POLICY], K=2. | M01 primary INFLATION; I01 primary INFLATION; selected IDs mapped from [M01,I01]; M01 matched topics follow requested order. Additional subset parameter (for F review): same pool, topics [INFLATION], K=2; both match only requested INFLATION, primary INFLATION, selected order [M01,I01]. |
| T20 | 02,03 | The T05b pool, K=10. | Both selected once in [mp,ea] order; counts (2,2,0,0,0,0,0,0); no padding. |

**Exact selector selection (48 rows):** T01, T02, T03a, T03b, T03c, T04a, T05a, T05b, T06, T07a, T07b, T07c, T07d, T07e, T08a, T08b, T08c, T08d, T08e, T08f, T08g, T08h, T08i, T09, T10a, T10b, T10c, T10d, T10e, T10f, T10g, T10g2, T10i, T10j, T10k2, T10l, T11a, T11b, T11c, T11d, T11e, T12, T14a, T14b, T14c, T14d, T19, T20.

The concrete T05b/T07/T08/T12/T14 inputs expand existing shorthand; F must approve these instantiations. T10h/T10k are not invented to fill naming gaps in the legacy reference.

## 5. Static schema cases proposed for S1

Sources: [detailed reference](./O5-Detailed-Test-Cases-Reference-r2.md), its I6/I7/I8/I10 definitions and parameter tables; [Interface](./O5-Interface-Reference-r2.md) section 4, 4.1, 4.2, 4.3. Exact fields and variant matrices remain there, not a second schema. Relates to REQ-O5-03/04/05 evidence structure only; these checks do not complete the runtime acceptance of those requirements or prove INV-O5-01..04 enforcement.

| Family | Exact requested parameter selection / input | Expected assertion |
|---|---|---|
| I6 | I6-VS-1..6; FE-1..7; LZ-1..4; UE-1..6; VV-1..7; PA-A1..6; PA-B1..2; IV-1..4; IR-1..3; RV-1..8; COM-1..5. Each prefix is I6-. Start from the corresponding complete valid Interface example; delete the named field only. COM rows apply across all eight variants; V-PARTIAL required-key checks cover both A and B. | Reject each deletion, including nullable-but-required keys. A valid control must first pass. Missing rules_version fails for all variants; null is legal only under Interface 4.1. The historical I6-LZ-3 parenthesis suggesting null is allowed does not override 4.1: LIMIT_ZERO has a non-null resolved version. |
| I7 | Starting from each valid variant, add an unlisted key; explicitly include vendor on V-SELECTED, input_count on V-INVALID-REQUEST, selected_count on V-PARTIAL. Apply all prohibited keys from Interface 4, one mutation at a time. | Reject; permitted-key set is closed. No event emitted. |
| I8 | Interface 4.3 M1-M11 valid objects and X1-X6 invalid mutations; include V-VENDOR controls for VENDOR_TIMEOUT, VENDOR_RATE_LIMIT, VENDOR_PAYLOAD_INVALID, VENDOR_UNAVAILABLE. | M1-M11 accept; X1-X6 reject. This validates combinations, not their production reachability. |
| I10 | All 18 I10-{A,B}-{bi,ic,rc}-{1,2,3} rows in r2: branch A/B × batch_id/input_count/reason_counts × present-null/missing/present-non-null. Plus I10-A-11,A-33,B-11,B-33 full controls and existing invalid-count mutations. | Present-null accepts, missing/non-null rejects for these three fields. A requires candidate_count>=1; B requires 0. 1<=queries_failed<=executed_query_count, integer counts excluding bool, candidate count nonnegative. Reject zero failed count, excess, negative, float, string, bool. Four controls accept; some combinations are schema-valid but not reachable through fail-fast retrieval. |

**No I9-a or I9-b is silently included by the range I6-I10.** I9-a is a builder invocation (S2); I9-b is reachable adapter integration (S3). Missing-version checks remain covered by I6-RV-1..8 and static nullability in the controls. Builder stage semantics and runtime resolved-version assertions are deferred, not dropped. I13 also stays outside S1.

## 6. Explicit exclusions and retained later coverage

| Excluded from this S1 approval request | Reason / retained stage |
|---|---|
| T03a-A | Zero-fetch adapter/event assertions: S3; T03a selector K=0 stays included. |
| T03c adapter ALL_INVALID wording; T04b/c | Public empty/failure messages and vendor retrieval: S3/S4; T03c selector result and T04a empty input stay included. |
| T10c2 | Serialized malformed/naive timestamps through the production loader are not direct selector inputs; defer loader coverage to adapter normalization. T10c/d test the direct selector boundary. |
| T10 request-failure emission | T10f/g/g2/i/j direct request rejection stays included; V-INVALID-REQUEST emission and vendor call count belong to S3. |
| T11f | providerPublishTime/half-open vendor mapping is adapter coverage; retain S3/S4, not replace it with a direct datetime test. |
| T13a-d including T13c-D/R; T15; I9-b; I13 | Retrieval/router/adapter entry: S3/S4. Single V-PARTIAL and no extra V-VENDOR on T13c paths remain unchanged. |
| I9-a; any evidence builder call | S2, not this independent S1 request. |
| I1-I5/I5b, I11, I12 runtime fault injection, suppression, sink or batch_id evidence | Later invariant/evidence stages. T07e does not claim to replace I11. |
| T16 as a standalone network-attempt integration case | Not in the approved S1 row. Reuse existing offline isolation for S1 without claiming full T16 acceptance or editing shared fixtures. |
| T17 | S6 performance runner; preserved artifacts, no measurement or timing gate requested now. |
| T18, human label sign-off; RT-1..RT-4 | Holdout/public regression stages, not S1. DEV20 does not satisfy human-quality acceptance. |
| D-owned flag spelling and caller wording; C-owned run_dir/configuration | Later interface/integration stages. They do not block the selected independent S1 scope. |

### 6a. Negative coverage and partial acceptance

Every selected row remains Not run. The following are assertions to implement only after F approval. Negative inputs are accompanied by positive controls; expected values must come from the approved contract/fixture, never from the implementation under test.

| S1 behavior / requirement | Positive control | Negative or boundary assertion |
|---|---|---|
| Classification / REQ-O5-01 | T01, T08d/e/g/h/i | T08a/b/c/f must not select irrelevant controls; whole-token and exclusion provenance retained |
| Allocation / REQ-O5-02 | T02, T05a/b, T19 | T06 must not exceed K; T05a tie must not depend on input order; T20 must not pad or duplicate |
| Empty/zero / REQ-O5-03 (selector part) | T01 normal nonempty | T03a does not classify; T03b/c and T04a do not fabricate articles; upstream failure remains later-stage coverage |
| Decisions and input / REQ-O5-04 | T01/T12 | T07a-d duplicate/invalid precedence; T07e rejects mutation; T12 disallows missing/double-counted decisions |
| Validation / REQ-O5-05 (selector part) | T11a/b/e | T10 invalid inputs; T11c/d outside UTC window; T12 shows invalid rows do not discard valid rows |
| Determinism / REQ-O5-06 | T14a repeat equality | T14b permutation, T14c wall-clock trap, T14d conflicting duplicates; wrong dependence/equality fails |
| Cost / REQ-O5-08 (partial) | Existing offline environment | T07e input-mutation check and existing network block; do not claim T16 attempt-recording or zero LLM-call integration coverage from these alone |
| Evidence schema shape only | I6/I7/I8/I10 valid controls | Delete required nullable keys, add prohibited keys, invalid enum combinations and non-integer/bool/count mutations reject |

For all valid selector calls, check output IDs are unique, belong to the supplied input, and selected business fields equal their source fields; all eight counts conserve; decisions cover each input index exactly once with matched topics and specific reason_code. These are selector-result assertions, not the adapter's injected invariant-failure/emission tests. I1/I3 -> INV-O5-02; I2 -> INV-O5-03; I11 -> INV-O5-01; I4/T16 -> INV-O5-04 remain later coverage. Do not mark these four operational invariant acceptance groups complete at S1 exit.

REQ-O5-07 human quality acceptance (T18), REQ-O5-09 public regression acceptance, REQ-O5-10 T17 performance acceptance, and adapter portions of REQ-O5-03/05/08 remain pending. Running all previous suites is still required for an S1 code change; deferring new RT integration cases is not a waiver of regression.

## 7. Assertion delta and unchanged evidence

| Item | Prior state | v1.6 verified action |
|---|---|---|
| Canonical value decision | v1.4 file called it a proposal | A has selected `o5-rules-v1.1-draft`; Registry reconciliation verified at d36a677. No assertion is changed to the non-draft value. |
| Valid request value | DEV20 and current cases already use -draft | Retain exactly; cite corrected Registry SHA d36a677d4738efd365b6bbcf6f69f993acf8fd3c. T01/T02/T03/T05/T06/T07/T08/T09/T10/T11/T12/T14/T19/T20 inherit that request value. |
| Unknown version | T10j rejects unsupported literal | Unchanged; do not invent acceptance of the non-draft alias. |
| Schema version fields | Required presence and stage/variant nullability | Unchanged for I6/I7/I8/I10. Static controls use selected -draft where a resolved value is required. I9 runtime/builder behavior remains deferred. |
| Topic labels, orders, counts, tokenizer, invariant mapping | v1.4 + Registry table | No rule, label, ordering or count-policy changes. Concrete input instantiation and S1-only projection are explicitly presented for F review. |
| Runtime evidence timing | v1.4 | Unchanged and outside S1; no success, failure, sink or public-message assertions are smuggled into selector cases. |
| T17 four files and both r2 references | F closed v1.4 document findings | Byte-identical in this preparation. Historical proposal notes inside them are not active version decisions; no new benchmark claims. |
| Execution plan | A approved v1.4 at b5891ac | Byte-identical; approval recorded externally here and in README. No scope expansion or re-approval request for the same execution plan. |

### 7a. Changes retained for v1.6 review

- T05a adds an explicit equal-timestamp/id tie parameter; T19 makes the subset parameter explicit; T14b fixes a deterministic permutation. The 48 row IDs are unchanged, but row count is not executable parameter count.
- All valid selector cases gain explicit subset, uniqueness, business-field equality, per-position decision and conservation assertions. No fault-injection/emission stage is moved into S1.
- Sections 1a/6a distinguish inherited rule exclusions, partial requirement acceptance and negative controls. Four schema families are requested as schema-only; I9 builder/stage behavior remains excluded.
- Add course evidence/verification obligations without widening E's product-code files or claiming team governance has already passed.

## 8. Formal review and implementation handoff

1. Baseline verification completed: d36a677d4738efd365b6bbcf6f69f993acf8fd3c is the PR #9 merge and inspected main. Registry O5 diff and unchanged fixture bytes verified; no rule/label/order/count change is introduced.
2. Submit v1.6 to existing PR #3 and record resulting full document commit SHA in the review request. F is asked to approve section 4's 48 selector rows (including parameters), section 5's four schema families and sections 6a/7a's assertions and file exclusions.
3. F approval is still pending. Do not implement S1 functional/test code until it is recorded. No S2-S6 approval is requested.
4. Before implementation, verify actual implementation-branch baseline, read approved materials and actual code/applicable instructions, record links and whitelist, and preserve the raw OpenCode session. C/D later integration and unpublished project agent files are not extra S1 gates under A's clarification; final course deliverables remain required.

**All software tests and benchmarks: Not run. Registry mismatch is resolved; formal F S1 approval remains pending.**
