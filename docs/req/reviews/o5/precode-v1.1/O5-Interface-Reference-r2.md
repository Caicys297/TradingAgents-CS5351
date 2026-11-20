# O5 Interface and Runtime Policy - r2 Reference (historical)

**Status: HISTORICAL SUPPORTING REFERENCE (r2), subordinate to `O5-Test-Plan-precode-v1.1-DRAFT.md` and `O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md`.**

It preserves the authoritative evidence-variant schema (section 4, 4.1, 4.2, 4.3), hooks A/B/D/E/G and the sink proposal. The v1.1 plans do not redefine the schema.

This file is a verbatim copy of `O5-Interface-and-Runtime-Policy-v0.5.3-DRAFT.md` from `E-O5-review-drafts\v0.5.3-corrected-r2\`. It is **not** a second, competing contract:
where the v1.1 plans state an amendment, the v1.1 plan wins; everywhere else this reference is the detailed source.
Any "pending", "awaiting F verification" or old local-path note inside the body below is historical and superseded only where the v1.1 plans say so.
No human approval is recorded by this file; all software tests remain Not run.

---

# O5 Macro News Filter - Interface and Runtime-Policy v0.5.3-draft (Member F latest review) - DRAFT

**Revision note (v0.5.3-corrected-r2):** active copy in `v0.5.3-corrected-r2\`; supersedes the same-named file in `v0.5.3-corrected\` (unmodified history). Active delivery references point here.

**Correction revision (v0.5.3-corrected):** this file lives in `v0.5.3-corrected\`; it supersedes the same-named file in `v0.5.3-F-review\`, which remains unmodified history. Active references point here.

**Owner:** Member E (O5). **Status:** DRAFT — decisions Pending. **Baseline checkout:** `970a9ea`; Member F reports `8c7eec3` (not verified here).
**Supersedes:** `v0.5.2-F-review/O5-Interface-and-Runtime-Policy-v0.5.2-DRAFT.md` (retained).
**v0.5.3 changes:** `rules_version` nullability defined by variant and processing stage (§4.1); V-PARTIAL branch A/B schema made explicit and **not-evaluated** contract added (§4.2); M02 witness anchor corrected to `central bank` in Requirements/fixture. Trigger enum and vocabulary unchanged.
**Single source of truth for the evidence contract.**

---

## 1. Module/adapter boundary

Selector preferred at `tradingagents/dataflows/macro_news_filter.py` (C1); `src/` only with packaging plan C4 (`pyproject.toml:51-52` includes only `tradingagents*`,`cli*`). Private adapter inside `get_global_news_yfinance`; public signature unchanged; sink/config via run-scoped context (C5). Insertion between `news.py:189` and `:191` [FACT].

---

## 2. Call-flow (hooks A,B,D,E,G)

```
get_global_news_yfinance (news.py:137-201)                      [str | raise]
  (A) request validation + K=0 shortcut     [C6]
  (B) try/except/finally around retrieval   [C7 — NEW]
        unchanged loop (news.py:169-189)
  (C) pre-final-slice list (news.py:190)
  (D) normalize + select
  (E) invariant validation
  (F) format + return
  (G) evidence emit                          [C5]
```

Vendor error mapping: `VendorUnavailableError` (`errors.py:46-50`). Trigger enum closed: `VENDOR_TIMEOUT`, `VENDOR_RATE_LIMIT`, `VENDOR_PAYLOAD_INVALID`, **`VENDOR_UNAVAILABLE`** (generic connection failure — not mislabelled). Mapping by typed evidence only.

---

## 3. Record contract

Serialized: `candidate_id,title,summary?,source?,url?,published_at(RFC3339|null),fixture_key`. Selector: aware `datetime`; `title_norm` derived internally (AM-37). Loader: RFC3339→aware; per-record invalid/naive→INVALID_TIMESTAMP; direct-string→INVALID_RECORD. `raw` removed.

---

## 4. Evidence schema (authoritative) + concrete examples for I6–I10

**Global rule:** only common keys + the variant's listed keys are permitted; any other key is prohibited (absent). Types given.

### Common keys (all variants)
`variant`(str enum), `action`(str enum), `trigger`(str enum), `disposition`(str enum), `rules_version`(str|null), `occurred_at`(str RFC3339 UTC seconds).

### 4.1 `rules_version` nullability (by variant and processing stage)

Request validation runs **before** any rule resolution. If the request itself is rejected, no rule set applies.
If the request validated, the rule version is resolved from the O5 registry and is a non-null string for the rest of the run.

| Variant | Stage reached | `rules_version` |
|---|---|---|
| V-INVALID-REQUEST | request validation failed **before** rule resolution | **null** (present-and-null) |
| V-VENDOR | retrieval failed; rules may or may not have been resolved | **str if resolved before the failure, else null**; never absent |
| V-PARTIAL | retrieval loop started (request validated) | **str** (request validation implies rule resolution) |
| V-LIMIT-ZERO | request validated; K=0 short-circuit | **str** |
| V-UPSTREAM-EMPTY | request validated; empty pool | **str** |
| V-SELECTED | classified | **str** |
| V-FILTERED-EMPTY | classified | **str** |
| V-INVARIANT | classified, invariant failed | **str** |

**Rule:** the key is always **present**; it is `null` only where the table says so; any other `null` fails. Absent always fails.

### 4.2 V-PARTIAL branch contract (authoritative)

The selector **has not executed** when retrieval fails. There are therefore **no classification decisions** to report. The two branches are distinguished by whether any candidate survived the collector's window/title-dedup before the failure.

**Branch A -- candidates exist** (`pre_filter_candidate_count >= 1`; selector still not run):
- required non-null: `executed_query_count`(int), `queries_failed`(int≥1), `pre_filter_candidate_count`(int≥1)
- required-null: `batch_id`(null), `input_count`(null), `reason_counts`(null) -- **not evaluated**; the schema **amendment AM-44** replaces the earlier "`input_count`/`reason_counts` required" wording with **required-null** because no classification ran
- prohibited: `empty_kind`,`violated_invariant`,`vendor`,`method`,`field`,`reason`,`selected_count`

**Branch B -- no candidates** (`pre_filter_candidate_count == 0`):
- required non-null: `executed_query_count`(int), `queries_failed`(int≥1), `pre_filter_candidate_count`(int, =0)
- required-null: `batch_id`,`input_count`,`reason_counts`
- prohibited: same as Branch A

**Field types and count constraints (synchronized with Test Plan I10):**
- `executed_query_count`, `queries_failed`: **integers excluding booleans**.
- `1 <= queries_failed <= executed_query_count`.
- `pre_filter_candidate_count`: **nonnegative integer excluding booleans**; **Branch A requires >= 1**, **Branch B requires 0**.
- These are **schema constraints**; a schema-valid combination need not be reachable through the fail-fast retrieval loop.

**Rationale source for AM-44:** a partial failure means the selector was never invoked, so `reason_counts` cannot be populated without fabricating classification. The honest contract is `null` (not evaluated). This is recorded as a schema amendment and every previous assertion is synchronized.

### 4.3 Action/trigger/disposition acceptance matrix

| # | variant | action | trigger | disposition | expected |
|---|---|---|---|---|---|
| M1 | V-SELECTED | SERVE_SELECTED | OK | OK | accept |
| M2 | V-FILTERED-EMPTY | SERVE_FILTERED_EMPTY | NO_RELEVANT_NEWS | FILTERED_TO_EMPTY | accept |
| M3 | V-LIMIT-ZERO | SKIP_CLASSIFICATION | LIMIT_ZERO | LIMIT_ZERO | accept |
| M4 | V-UPSTREAM-EMPTY | SERVE_UPSTREAM_EMPTY | UPSTREAM_EMPTY | UPSTREAM_UNAVAILABLE | accept |
| M5 | V-VENDOR | VENDOR_UNAVAILABLE | VENDOR_TIMEOUT | UPSTREAM_UNAVAILABLE | accept |
| M6 | V-VENDOR | VENDOR_UNAVAILABLE | VENDOR_RATE_LIMIT | UPSTREAM_UNAVAILABLE | accept |
| M7 | V-VENDOR | VENDOR_UNAVAILABLE | VENDOR_PAYLOAD_INVALID | UPSTREAM_UNAVAILABLE | accept |
| M8 | V-VENDOR | VENDOR_UNAVAILABLE | VENDOR_UNAVAILABLE | UPSTREAM_UNAVAILABLE | accept |
| M9 | V-PARTIAL | PARTIAL_UPSTREAM | PARTIAL_QUERY_FAILURE | PARTIAL_UPSTREAM | accept |
| M10 | V-INVARIANT | SUPPRESS_BATCH | INVARIANT_VIOLATION | INVARIANT_VIOLATION | accept |
| M11 | V-INVALID-REQUEST | REJECT_REQUEST | INVALID_REQUEST | INVALID_REQUEST | accept |
| X1 | V-VENDOR | VENDOR_UNAVAILABLE | VENDOR_OTHER | UPSTREAM_UNAVAILABLE | reject (trigger not in closed enum) |
| X2 | V-VENDOR | SERVE_SELECTED | VENDOR_TIMEOUT | UPSTREAM_UNAVAILABLE | reject (action mismatch) |
| X3 | V-SELECTED | SERVE_SELECTED | OK | FILTERED_TO_EMPTY | reject (disposition mismatch) |
| X4 | V-PARTIAL | PARTIAL_UPSTREAM | PARTIAL_QUERY_FAILURE | OK | reject (disposition mismatch) |
| X5 | V-INVALID-REQUEST | REJECT_REQUEST | INVALID_REQUEST | INVARIANT_VIOLATION | reject (disposition mismatch) |
| X6 | V-LIMIT-ZERO | SKIP_CLASSIFICATION | LIMIT_ZERO | UPSTREAM_UNAVAILABLE | reject (disposition mismatch) |

### V-SELECTED — SERVE_SELECTED / OK / OK
Required: `batch_id`(str), `input_count`(int), `selected_count`(int≥1), `reason_counts`(map[str,int]), `executed_query_count`(int≥0), `pre_filter_candidate_count`(int≥1). Optional: `matched_topic_counts`(map). Prohibited: all other variant keys.

**I6 valid example:**
```json
{"variant":"V-SELECTED","action":"SERVE_SELECTED","trigger":"OK","disposition":"OK",
 "rules_version":"o5-rules-v1.1-draft","occurred_at":"2026-09-28T00:00:00Z",
 "batch_id":"b:…","input_count":4,"selected_count":1,
 "reason_counts":{"SELECTED":1,"NO_MACRO_EVIDENCE":3},
 "executed_query_count":2,"pre_filter_candidate_count":4}
```
**I6 invalid mutations:** delete `executed_query_count` ⇒ fail; delete `batch_id` ⇒ fail; set `selected_count=0` ⇒ fail.

### V-FILTERED-EMPTY — SERVE_FILTERED_EMPTY / NO_RELEVANT_NEWS / FILTERED_TO_EMPTY
Required: `batch_id`, `input_count`(≥1), `selected_count`(=0), `reason_counts`, `executed_query_count`, `pre_filter_candidate_count`, `empty_kind`(enum). Optional: `matched_topic_counts`.
**I6 valid:** example with `empty_kind:"ALL_INVALID"`. **Invalid:** `empty_kind:"ALL_INVALID"` missing ⇒ fail; `selected_count=1` ⇒ fail.

### V-LIMIT-ZERO — SKIP_CLASSIFICATION / LIMIT_ZERO / LIMIT_ZERO
Required: `input_count`(≥0), `executed_query_count`(≥0), `pre_filter_candidate_count`(≥0). Nullable-required: `batch_id`. Prohibited: `reason_counts`,`empty_kind`,`violated_invariant`,`vendor`,`method`,`field`,`reason`.
**I9:** `batch_id:null` passes; `batch_id` absent fails; `reason_counts` present fails.

### V-UPSTREAM-EMPTY — SERVE_UPSTREAM_EMPTY / UPSTREAM_EMPTY / UPSTREAM_UNAVAILABLE
Required: `executed_query_count`(≥0), `pre_filter_candidate_count`(=0). **Present-and-null:** `batch_id`,`input_count`,`selected_count`,`reason_counts`. Prohibited: `empty_kind`,`violated_invariant`,`vendor`,`method`,`field`,`reason`.
**I9:** all-present-null passes; any absent ⇒ fail; a non-null `input_count` ⇒ fail (no pool).

### V-VENDOR — VENDOR_UNAVAILABLE / trigger ∈ {VENDOR_TIMEOUT,VENDOR_RATE_LIMIT,VENDOR_PAYLOAD_INVALID,VENDOR_UNAVAILABLE} / UPSTREAM_UNAVAILABLE
Required: `vendor`(str), `method`(str). Optional: `executed_query_count`(int). Present-and-null: `batch_id`,`input_count`,`selected_count`,`reason_counts`,`pre_filter_candidate_count`. Prohibited: `empty_kind`,`violated_invariant`,`field`,`reason`.
**I8:** `trigger:"VENDOR_TIMEOUT"` with `action:"VENDOR_UNAVAILABLE"` passes; `trigger:"VENDOR_OTHER"` fails.

### V-PARTIAL - PARTIAL_UPSTREAM / PARTIAL_QUERY_FAILURE / PARTIAL_UPSTREAM
See Section 4.2 (authoritative branch contract; AM-44 makes `input_count`/`reason_counts` required-null, not required).

### V-INVARIANT — SUPPRESS_BATCH / INVARIANT_VIOLATION / INVARIANT_VIOLATION
Required: `violated_invariant`(∈INV-01..04), `batch_id`, `pre_suppression_selected_count`(≥0), `published_selected_count`(=0). Optional: `input_count`,`reason_counts`. Prohibited: `empty_kind`,`vendor`,`method`,`field`,`reason`.

### V-INVALID-REQUEST — REJECT_REQUEST / INVALID_REQUEST / INVALID_REQUEST
Required: `field`(str), `reason`(str). Nullable-required: `rules_version`. **Prohibited:** `batch_id` and **all** candidate/query counts, `reason_counts`, `violated_invariant`, `vendor`, `method`, `empty_kind`.
**I8:** counts present ⇒ fail (no fabricated batch).

### Legal triples
Only the eight variants; each row's action/trigger/disposition is the only legal triple. **I8** iterates all illegal combos ⇒ fail.

### Invariant precedence (multi-violation stubs)
`INV-O5-04 > INV-O5-02 > INV-O5-03 > INV-O5-01`.

### batch_id
Canonical JSON (`sort_keys`, compact separators, `ensure_ascii=False`), second-precision UTC; **original title**+summary+source+url+published_at; invalid records `{type_tag, repr_sha256}` or `repr_unavailable:true`; inputs `{rules_version,limit,topics(request-ordered),start_at_iso,end_at_iso,records}`. (I12 verifies a summary change alters `batch_id`.)

---

## 5. Caller-facing wording (exact) vs router text

**Direct exceptions (no wrapper text):**  A direct `get_global_news_yfinance` vendor failure **raises** `VendorUnavailableError` (no `DATA_UNAVAILABLE` string). A direct call never returns the router sentinel.

**Router-generated text (returned `str`):**
```
DATA_UNAVAILABLE: no configured vendor could serve get_global_news right now (<error>). This says nothing about the instrument; report the data as unavailable and do not estimate or fabricate values.
```
(`router.vendor_unavailable`, `router.py:176-182`.)

**Yahoo empty-after-filter (returned `str`):**
- coverage gap: `<Yahoo Finance global news unavailable for <start>..<end>: <reason>, so this is not an absence of market news>` (`coverage_gap`, `date_window.py:45-69`).
- fully covered but empty: `No global news found between <start> and <end>` (`news.py:199`).

**O5 adapter wordings (proposed, D approves):**

| Case | Text |
|---|---|
| selected ≥1 | baseline `## Global Market News, from <start> to <end>:\n\n` + articles |
| all irrelevant | `Fetched N candidate(s); none carry the requested macro evidence. This is a filter result, not a statement that no macro news exists.` |
| all invalid | `Fetched N malformed candidate(s); none were usable. This is a data-quality result, not an absence of news.` |
| all out-of-window | `Fetched N candidate(s), all outside the requested window.` |
| mixed none relevant | `Fetched N candidate(s); none qualified after window, validity and relevance checks.` |
| no candidates | baseline coverage-gap phrase |
| K=0 | `limit=0 requested; nothing was analyzed.` |
| vendor unavailable | router `DATA_UNAVAILABLE` text (routed) / raised (direct) |

Invalid ≠ irrelevant everywhere.

---

## 6. Policy table

P1 selected→format(V-SELECTED); P2 0 relevant→text(V-FILTERED-EMPTY,D); P3 K=0→skip(V-LIMIT-ZERO,C); P4 empty→baseline(V-UPSTREAM-EMPTY); P5 transport→baseline(V-VENDOR); P6 INV→suppress(V-INVARIANT,D); P7 invalid request→raise(V-INVALID-REQUEST); P8 partial→baseline(V-PARTIAL).

---

## 7. Persistence (sink)

`O5EvidenceSink.emit`; production `JsonlEvidenceSink(<results_dir>/<run-id>/o5_evidence.jsonl)` appending under `files.locked` (`files.py:36-88`); `InMemorySink` tests only. Injection via run-scoped context (C5), public signature unchanged. **Branch A construction failure** vs **Branch B emit failure** (Interface prior text): A = warning + continue (or fail-closed, D/C choose); B = independent logger `tradingagents.o5.evidence` + `SINK_FAILED`, string served. Logger is diagnostic, not guaranteed persisted audit.

---

## 8. Enforcement vs semantic

Unchanged: runtime checks structural; truth human-validated; INV-O5-04 test-time block with attempt recording (T16).

---

## 9. Authoritative owner-decision list

| ID | Question | Proposed | Owner | Pending |
|---|---|---|---|---|
| C1 | selector location | `tradingagents/dataflows/macro_news_filter.py` | C | yes |
| C2 | shared-file edits | hooks A/D/E/G only | C | yes |
| C3 | O3 shares | No | C | yes |
| C4 | packaging | include+clean-install if `src/` | C | yes |
| C5 | sink config/injection/run-id/path | run-scoped context | C | yes |
| C6 | pre-fetch validation + K=0 | adapter pre-check | C | yes |
| C7 | retrieval-loop B wrapper | try/except/finally, behavior unchanged | C | yes |
| D1 | O4 consumption | none auto | D | yes |
| D2 | wording | §5 | D | yes |
| D3 | invariant/sink action | §7 | D | yes |
| D4 | negation | selectable context | D | yes |
| D5 | ALL_INVALID | empty_kind | D | yes |
| D6 | hook placement | with C6/C7 | C/D | yes |
| F1 | discovery | **reported satisfied at `8c7eec3`** (default config collects `tests/`+`test/offline/`); confirm | F | yes |
| F2 | isolation | **reported satisfied at `8c7eec3`** (`test/offline/` blocks socket+curl_cffi); confirm | F | yes |
| F3 | marker | `unit` for offline tests; `integration` reserved for live services | F | yes |
| F4 | perf runner | fixed runner; 5/30/nearest-rank; 100 ms proposed | F | yes |

---

## 10. Non-goals

Unchanged.

---

## 11. Status

Approvals Pending; software tests Not run; implementation Not started.
