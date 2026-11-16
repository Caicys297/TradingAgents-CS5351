# O5 Macro News Filter — Test Plan (pre-code upload, v1.1-DRAFT)

**Owner:** Member E (O5). **Test-plan reviewer:** Member F (registry `development_contract.approval_roles.O5_test_plan` → "F reviews").
**Execution-plan reviewer:** Member A ("A reviews each scoped plan before first code edit").
**Status:** DRAFT for review. **NOT approved. No software test has been run. No project test code exists.**
**Development authority for this review:** `docs/req/requirements.yaml` and `docs/req/A-Requirements-Decisions.md` at `3cb83f3ff8fddb780b9c9c7fb2a6fd930b3395cf` (PR #2, reported **not merged**). Neither that registry nor this document is a test-plan or execution-plan approval.

---

## 0. Package contents and how to read them

| File | Role |
|---|---|
| `O5-Test-Plan-precode-v1.1-DRAFT.md` | **This plan (normative for review).** |
| `O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md` | Companion execution plan (A's review). |
| [`O5-Detailed-Test-Cases-Reference-r2.md`](./O5-Detailed-Test-Cases-Reference-r2.md) | **Historical supporting reference**: full T01–T20, I1–I12, RT-1..RT-4, I6–I10 parameter tables. |
| [`O5-Interface-Reference-r2.md`](./O5-Interface-Reference-r2.md) | **Historical supporting reference**: evidence schema (Interface §4, 4.1, 4.2, 4.3), hooks, sink. |
| [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](./O5-T17-Perf-Fixture-1000-v1-DRAFT.json) | T17 input fixture (byte-identical copy). |
| [`O5-T17-Expected-Results-v1-DRAFT.json`](./O5-T17-Expected-Results-v1-DRAFT.json) | T17 expected results (byte-identical copy). |
| [`O5-T17-Manifest-v1-DRAFT.json`](./O5-T17-Manifest-v1-DRAFT.json) | T17 manifest (byte-identical copy). |
| [`O5-T17-F-Handoff-v1-DRAFT.md`](./O5-T17-F-Handoff-v1-DRAFT.md) | T17 handoff (byte-identical copy). |

**Reading rule:** the two `*-r2.md` files are the detailed case sources. This plan **amends** them only in §5. Where this plan and an r2 reference disagree **outside** §5, treat it as an error in this plan to be reported, not as license to pick either — there is exactly one contract, amended once, in §5.

---

## 1. What was actually inspected

| Item | Method | Result |
|---|---|---|
| Local HEAD / status | `git rev-parse HEAD`, `git status --short --branch` | `970a9ea…` on `main`, working tree clean |
| Registry revision present | `git cat-file -t 3cb83f3…` | `commit` (already present locally) |
| Registry files read | `git cat-file blob 3cb83f3:docs/req/...` | `requirements.yaml`, `product-requirements.yaml`, `req-schema.json`, `A-Requirements-Decisions.md`, `Team-O1-O6-Test-Case-Catalog-v2.0-DRAFT.md`, `O5-Dev20-Fixtures-v0.5.3-DRAFT.json`, `docs/test-approvals/TEMPLATE.md` |
| Team DEV20 fixture identity | blob bytes; SHA-256 | `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6`, 24,291 bytes — **identical** to the local r2 fixture and equal to the registry's `development_contract.o5.dev20_fixture_sha256` |
| Selector implementation | filesystem check | `tradingagents/dataflows/macro_news_filter.py` **absent**; `src/` and `test/offline/` contain only `.gitkeep` |
| Repository instructions | filesystem check | no `AGENTS.md`; `.agent/` only `.gitkeep`; `.opencode/` tooling only. Sole repository instruction is `docs/PROJECT_WORKSPACE.md` |

### 1.1 Git-state note (corrected wording)

An earlier draft called the requirements fetch "read-only". **Correction:** the fetch *did* populate Git objects and `.git/FETCH_HEAD`, i.e. **Git metadata changed**. What is guaranteed is narrower and accurate: `main`, `origin/main`, `HEAD`, the index and every tracked working-tree file are **unchanged**. No pull, merge, checkout or branch creation occurred.

---

## 2. Authority model for this review

The registry is the **proposed development authority** for review purposes. Its statements are of two kinds, and this plan separates them:

- **Selected policy direction (treated as decided for review):** scope (already-fetched Yahoo global news only), selector module path, `rules_version`, topic order, same-field clause-crossing matching, negation selectable-with-flag, evidence path in the O2 run dir, `SINK_FAILED` behaviour, "filter-unavailable" on invariant failure, K=0 returning `LIMIT_ZERO` without vendor fetch, the three rule tables, `config_allowlist` O5 keys, and `REQ-O5-10`'s acceptance condition. This plan does **not** reopen these merely because the older r2 drafts said "Pending".
- **Unresolved implementation seams (still genuinely open):** how the O2 run-directory context reaches the adapter, whether `o5_*` config keys are added to `default_config.py`, the exact "filter-unavailable" string, the negation-flag field name, and the CI wiring for `test/offline/`. These are listed in §9 and are **C/D/A/F** questions, not E policy choices.
- **Author's checkout context:** `A-Requirements-Decisions.md` records the authoring checkout as `feature/o1-sma-guard`. That is **A's recorded context**, not a required branch for E and **not** a registry contradiction. Implementation-base verification is a separate **pre-code check** owned by A (§9 Q1). The local checkout here is `main` @ `970a9ea`.

---

## 3. Traceability (registry → cases)

| Requirement | Registry statement focus | `verification` | Cases |
|---|---|---|---|
| REQ-O5-01 | Classify with `o5-rules-v1.1` + rule catalog; query text never evidence | T01, T08e, RT-3 | T01, T08a–i, RT-3 |
| REQ-O5-02 | Primary bucket, round-robin, `published_at desc, candidate_id asc`, ≤K | T01,T02,T05,T06,T19,T20 | T01,T02,T05,T06,T19,T20 |
| REQ-O5-03 | Honest empty; no padding; K=0 ≠ failure | T03,T04,T13 | T03,T04,T13 |
| REQ-O5-04 | One decision per input position; verbatim business fields | T12, I11 | T12, I11 |
| REQ-O5-05 | Request/record validation; window; isolate damaged; adapter failure | T10,T11 | T10,T11 |
| REQ-O5-06 (invariant) | 100× equal; unique-ID permutation; no wall clock | T14 | T14 |
| REQ-O5-07 (quality) | precision ≥0.90, pre-limit recall ≥0.75, coverage ==1.0 | T01, T18 | T01, T18 |
| REQ-O5-08 (cost) | 0 added requests, 0 LLM calls, 0 mutations | T10,T14,T16 | T10,T14,T16 |
| REQ-O5-09 (invariant) | Public `str`; ticker path unchanged; prior tests | T15, RT-1, RT-4 | T15, RT-1..RT-4 |
| REQ-O5-10 (performance) | 1000 records, K=30, p95 ≤ 100 ms on ubuntu-latest/Py3.11 | T17 | T17 |
| INV-O5-01 | No fabrication / irrelevant padding | "O5 invariant tests I1-I12" | I1, I3, I11 |
| INV-O5-02 | No out-of-input / duplicate / mutation | "O5 invariant tests I1-I12" | I1, I2, I3 |
| INV-O5-03 | Window containment | "O5 invariant tests I1-I12" | I2 |
| INV-O5-04 | No network / LLM | "O5 invariant tests I1-I12" | I4, T16 |

The registry gives INV-O5-01..04 one shared `verification` string; the per-invariant split above is **E's mapping, Pending F** (see §9 Q2).

---

## 4. Layers, files and offline isolation

| Layer | Meaning | Planned file |
|---|---|---|
| `S` | Pure selector, in-memory inputs, no clock | `test/offline/test_o5_macro_news_filter.py` |
| `B` | Evidence-builder unit tests (construct evidence directly; no selector under test) | `test/offline/test_o5_evidence_builder.py` |
| `A` | Adapter over the real `get_global_news_yfinance` entry | `test/offline/test_o5_macro_news_integration.py` |
| `I` | Invariant / fault injection | `test/offline/test_o5_invariants.py` |
| `R` | Public interface / inherited regression | `test/offline/test_o5_regression.py` |
| `P` | T17 measurement harness | `test/offline/test_o5_macro_news_perf.py` |

**Schema vs builder vs integration (requirement 5).**
- **Schema tests** validate an evidence dict against Interface §4 alone: I6, I7, I8, I9-a, I9-b (nullability), I10 field/state and count constraints.
- **Builder tests** exercise the code that *produces* V-PARTIAL / V-VENDOR / V-INVALID-REQUEST evidence at a stage that production retrieval cannot reach (I9-a). They construct the evidence directly and assert the emitted object.
- **Reachable integration tests** go through `get_global_news_yfinance` / `tools.get_global_news`: T13a, T13b, T13c-D, T13c-R, T13d, T15.

**Offline isolation (unchanged requirement, F owns):** `test/offline/` must run under default `pytest -q`; sockets and `curl_cffi` blocked; `integration` marker reserved for live services; per-test config reset and temp `data_cache_dir`; T16 records every attempted connect/DNS/HTTP call and asserts the list is empty. Member F reported that `8c7eec3` collects both trees and has isolation; that is **F-reported for that revision** and **O5's own collection/isolation remains untested**.

---

## 5. Explicit v1.1 amendments (the ONLY changes to the r2 references)

### A-1. T03c — complete, well-formed input (fixes the malformed/abbreviated r2 input)

The r2 T03c input is replaced by this complete record set. Note `title` must be a string for the record to be structurally valid; the r2 example's `title:""` and `"No title"` are both kept, and the two IDs are real fixture-style IDs.

```json
[
  {"candidate_id": "o5:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01", "title": "", "summary": "x",
   "source": null, "url": null, "published_at": "2026-09-25T00:00:00Z"},
  {"candidate_id": "o5:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02", "title": "No title", "summary": "y",
   "source": null, "url": null, "published_at": "2026-09-25T00:00:00Z"}
]
```

Request: topics `[MONETARY_POLICY, INFLATION, ECONOMIC_ACTIVITY]`, `start_at=2026-09-20T00:00:00Z`, `end_at=2026-09-27T23:59:59.999999Z`, `limit=3`, `rules_version=o5-rules-v1.1-draft`.
Expected: `status=NO_RELEVANT_NEWS`; `counts = {input_count 2, selected_count 0, not_selected_limit_count 0, irrelevant_count 0, invalid_count 2, out_of_window_count 0, duplicate_count 0, skipped_zero_limit_count 0}` (conserves: 2 = 0+0+0+2+0+0+0); decisions are two `INVALID` / `reason_code=INVALID_TITLE`; adapter layer `empty_kind=ALL_INVALID`.
(Any error in `published_at` string syntax would make the record structurally invalid — the strings above are valid RFC3339, so both records reach the title check.)

### A-2. T12 — corrected count conservation

r2 asserted `len(decisions)=5` with `counts={5,1,0,1,1,1,1,0}`, which does **not** conserve (sums to 5 only if `input_count` is 5, but the ordering of keys is ambiguous and the r2 line is abbreviated). v1.1 restates it canonically:

Pool (5 records, in input order): one valid relevant (SELECTED-eligible), one `INVALID_TITLE`, one `OUT_OF_WINDOW`, one `DUPLICATE_ID` (repeat of the selected ID), one `REJECTED` (irrelevant).
Request: K=10, default window/topics.

Expected `counts` (canonical keys, conserving):
`input_count 5, selected_count 1, not_selected_limit_count 0, irrelevant_count 1, invalid_count 1, out_of_window_count 1, duplicate_count 1, skipped_zero_limit_count 0` → 1+0+1+1+1+1+0 = **5**.
`len(decisions) == 5`, one disposition per index: `SELECTED`(0), `INVALID`(1), `OUT_OF_WINDOW`(2), `DUPLICATE_ID`(3), `REJECTED`(4).

### A-3. Adapter case T03a-A — K=0 must not fetch (registry `o5.zero_limit`)

New adapter case (this was not in r2): `tools.get_global_news(curr_date, limit=0)` with `yf.Search` patched to a counter that records calls.
Expected: **`yf.Search` call count = 0**; returns a short `str` stating limit=0 / nothing analyzed; evidence variant `V-LIMIT-ZERO` with `input_count=0`, `executed_query_count=0`, `pre_filter_candidate_count=0`, `batch_id=null`. This is the registry's zero-fetch path and is a **deliberate change from baseline** (baseline would fetch then format). It does **not** reopen any V-PARTIAL count constraint.

### A-4. Evidence path (registry `o5.evidence_path`)

Evidence is written to `o5_evidence.jsonl` in the **same O2 run directory** when a CLI run context exists. Where no CLI context exists, `SINK_FAILED` is logged and the honest result is still served (registry `o5.sink_failure`). The exact handoff is a **C seam** (§9 Q3), not an E policy choice.

### A-5. Invariant-failure wording (registry `o5.invariant_failure`)

On selector invariant failure the adapter suppresses selected articles and returns an explicit **"filter-unavailable"** message, never "no news". The exact string is a **D** confirmation (§9 Q4).

### A-6. Negation flag (registry `o5.negation`)

A negated match remains **selectable as context** and carries a negation flag. The evidence/selected record must expose that flag; the exact field name is a **D** confirmation (§9 Q5). Add case: a record whose only anchor is negated (`no sign of rising inflation`) is selectable, flagged `negated=true`.

### A-7. Rule-vocabulary strings (registry rule tables)

Use the registry's literal strings, including `basis points`, `price pressures`, `hike`, `cut` (no singular variants). This is a **Pending** difference from r2 (which listed `basis point`, `price pressure`) and is tracked in §8 D-03; **DEV20 labels have not been re-derived under the registry list** and remain provisional.

### A-8. T17 acceptance condition wording

`REQ-O5-10` **specifies** ubuntu-latest / Python 3.11, 5 warmups, 30 measured runs, nearest-rank p95 ≤ 100 ms. This is the **specified acceptance condition**, distinct from (a) F/E reviewer approval of the plan, (b) runner realization, and (c) actual measurements — none of which have occurred. A relaxation would require an explicit registry decision.

Everything not listed A-1..A-8 stands as written in the two r2 references.

---

## 6. Case index (IDs checked for consistency)

`T01–T20` (T13 has sub-cases T13a, T13b, T13c-D, T13c-R, T13d; T03 has T03a, T03a-A, T03b, T03c; T05 T05a/T05b; T07 T07a–e; T08 T08a–i; T10 T10a–l incl. T10c2/T10g2/T10k2; T11 T11a–f; T14 T14a–d).
`I1–I12` (I6 groups I6-VS-1..6, I6-FE-1..7, I6-LZ-1..4, I6-UE-1..6, I6-VV-1..7, I6-PA-A1..6, I6-PA-B1..2, I6-IV-1..4, I6-IR-1..3, I6-RV-1..8, I6-COM-1..5; I9-a, I9-b; I10-A/B × bi/ic/rc × 1..3 plus I10-A-11, I10-A-33, I10-B-11, I10-B-33).
`RT-1..RT-4`. New in v1.1: `T03a-A`.

Case IDs above are defined once, in the r2 detailed reference, and referenced — not redefined — here.

## 7. T17 measurement conditions (registry-specified)

- Fixture: [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](./O5-T17-Perf-Fixture-1000-v1-DRAFT.json), SHA-256 `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0`, 1000 records, K=30.
- Expected: [`O5-T17-Expected-Results-v1-DRAFT.json`](./O5-T17-Expected-Results-v1-DRAFT.json), SHA-256 `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6`; `status=OK`, selected 30 (10/10/10), counts `{1000,30,890,60,0,0,20,0}`.
- Manifest: [`O5-T17-Manifest-v1-DRAFT.json`](./O5-T17-Manifest-v1-DRAFT.json), SHA-256 `1ed6d0a4674afe74b856fc5b1430074370c7bb100aec6454d76eebbb5bd07959`.
- Handoff: [`O5-T17-F-Handoff-v1-DRAFT.md`](./O5-T17-F-Handoff-v1-DRAFT.md), SHA-256 `97a36c5124d37d53fe28384a53a3a9dd1f72c8d002e8e0868adb08f6b411de5a`.
- Boundary: load/deserialize/RFC3339 parse/defaults **outside**; validation, classification, sort, allocation, result construction **inside**; assertions and persistence **outside**. Input mutation is a correctness failure.
- Correctness gate before timing; any mismatch or error ⇒ **invalid measurement**.
- The T17 artifacts contain the old note "runner pending F". **Superseded only here** by A-8: the registry names ubuntu-latest/Py3.11 as the specified condition. 100 ms remains unverified.

## 8. Registry contradictions kept visible

| ID | Contradiction | Status |
|---|---|---|
| D-02 | `REQ-O5-01` says `o5-rules-v1.1`; `development_contract.o5.rules_version` says `o5-rules-v1.1-draft` | **Open** — flagged to B; this plan uses the `development_contract` value |
| D-03 | Registry rule strings (`basis points`, `price pressures`, `hike`, `cut`) differ from r2's singular variants | **Open** — A-7 adopts the registry list; DEV20 labels not re-derived |
| D-04 | INV-O5-01..04 share one `verification` string | **Open** — E's per-invariant mapping Pending F |
| D-06 | REQ-O5-07 needs a human holdout; DEV20 is provisional | **Open** — DEV20 labels **not** human-approved; no quality acceptance claimed |

## 9. Review questions (genuinely open seams)

1. **A:** confirm the implementation base branch (the `feature/o1-sma-guard` line in A's document is the authoring context, not E's target) — a pre-code check, not a registry contradiction.
2. **F:** confirm the per-invariant case mapping (D-04) and whether I-cases may be approved under one `verification` string.
3. **C:** confirm the O2 run-directory handoff for `o5_evidence.jsonl`, and whether `o5_*` keys go into `default_config.py` or stay module constants.
4. **D:** confirm the exact "filter-unavailable" string.
5. **D:** confirm the negation-flag field name.
6. **F/E:** confirm T17 runner realization and whether 100 ms stands after measurement (relaxation requires a registry decision).
7. **B/A:** normalize the rules-version naming (D-02) and the rule strings (D-03).

## 10. Approval status

- **F reviews this O5 test plan.** **A reviews the execution plan.**
- Implementation and test coding may begin only after both scoped approvals and project governance readiness; an approval comment must name the reviewed version, requirement IDs, case IDs, allowed files and exclusions; an empty `docs/test-approvals/TEMPLATE.md` is **not** approval.
- **All software tests: Not run.**

## 11. Preserved F closures (r2 document-review scope)

Preserved unchanged: T13c-D/T13c-R independent sinks + single `V-PARTIAL`; the I10 18 field-state cases; I6-RV-1..8; I9-a builder-only boundary; Interface §4.2 count constraints + the four A/B examples; M02 vocabulary wording. **Not reopened** by A-3 (the K=0 zero-fetch path is a separate adapter case and does not touch V-PARTIAL counts). Renewed-review flags: A-7 may affect the QC list wording; A-8 supersedes only the runner note inside the T17 artifacts.
