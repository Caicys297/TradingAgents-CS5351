# O5 Detailed Test Cases - r2 Reference (historical)

**Status: HISTORICAL SUPPORTING REFERENCE (r2), subordinate to `O5-Test-Plan-precode-v1.1-DRAFT.md` and `O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md`.**

It preserves the detailed T01-T20, I1-I12, RT-1..RT-4 and I6-I10 parameter tables. The v1.1 Test Plan amends specific items (see its section 5 'Explicit v1.1 amendments').

This file is a verbatim copy of `O5-Test-Plan-v0.5.3-DRAFT.md` from `E-O5-review-drafts\v0.5.3-corrected-r2\`. It is **not** a second, competing contract:
where the v1.1 plans state an amendment, the v1.1 plan wins; everywhere else this reference is the detailed source.
Any "pending", "awaiting F verification" or old local-path note inside the body below is historical and superseded only where the v1.1 plans say so.
No human approval is recorded by this file; all software tests remain Not run.

---

# O5 Macro News Filter - Test Plan v0.5.3-draft (Member F latest review) - DRAFT

**Revision note (v0.5.3-corrected-r2):** active copy in `v0.5.3-corrected-r2\`; supersedes the same-named file in `v0.5.3-corrected\` (unmodified history). Active delivery references point here.

**Correction revision (v0.5.3-corrected):** this file lives in `v0.5.3-corrected\`; it supersedes the same-named file in `v0.5.3-F-review\`, which remains unmodified history. Active references point here.

**Owner:** Member E (O5). **Status:** DRAFT. All tests **Not run**. No test code written/executed.
**Baseline checkout:** `970a9ea` (older). Member F reports `8c7eec3` collects `tests/` + `test/offline/` with isolation; **not verified here** (see Requirements §0.3).
**Supersedes:** `v0.5.2-F-review/O5-Test-Plan-v0.5.2-DRAFT.md` (retained).
**Fixture:** `O5-Dev20-Fixtures-v0.5.3-DRAFT.json` (this corrected directory) (`rules_version=o5-rules-v1.1-draft`; orders carry both key and actual-ID arrays).
**Evidence schema:** single source = Interface v0.5.3 §4, including §4.1 `rules_version` nullability, §4.2 V-PARTIAL branches (AM-44), §4.3 action/trigger/disposition matrix.

---

## 0. Conventions

Layers **S/A/R/I**; namespaces: rules R1-MP/R2-IN/R3-EA/R4/R5/R6, R12-ORD; regression RT-1..RT-4; invariant I1–I12; owner decisions C1–C7, D1–D6, F1–F4 (Interface §9). Loader parses RFC3339; direct-selector string timestamp → INVALID_RECORD; serialized invalid/naive → INVALID_TIMESTAMP (per record). Clock freeze via `date_window.datetime` attribute proxy. All Not run.

### 0.1 Discovery/isolation status

- **At `970a9ea`** [FACT]: `testpaths=["tests"]`; isolation lives in `tests/conftest.py`.
- **Member F reports at `8c7eec3`** [F-REPORTED]: default config collects `tests/` + `test/offline/`; `test/offline/` already has socket + `curl_cffi` blocking.
- **This pass does not verify or change CI/isolation.** Tests below are planned. F confirmed discovery and socket/`curl_cffi` isolation **for `8c7eec3` only**; **O5 collection and isolation remain untested**.
- **T16** must record attempted network access at the harness level so business code catching the blocked exception cannot hide a violation.

### 0.2 Canonical contract

Validation algorithm (Requirements §6.2): request → K=0 → structure → DUPLICATE_ID → reserve → title/timestamp/window → classify/allocate. Counts: `input_count = selected_count + not_selected_limit_count + irrelevant_count + invalid_count + out_of_window_count + duplicate_count + skipped_zero_limit_count`.

---

## Case matrix

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

## T01 — DEV20 K=20

- Expected: selected ID set = `expected.k20_expected_selected_set` mapped via `fixture_key_to_id`; per-ID primary: M01/M02/M03/M04/I02/I03/I04 => MONETARY_POLICY; I01 => INFLATION; A01..A04 => ECONOMIC_ACTIVITY; matched_topics = labels (request-ordered); N01-N08 `REJECTED/NO_MACRO_EVIDENCE`; counts `{20,12,0,8,0,0,0,0}` (selected set 12; buckets 7/1/4).
- Status: Not run. Labels Pending.

## T02 — K=6 (actual IDs)

- Expected: `selected` actual IDs **equal `expected.k6_order_ids`** = `[o5:5bac9b8abe6d5ca1d080daddc17790be, o5:d55befa5f36ac3b155868409c5f899cf, o5:5c49d34495cd1dbf9c2eeb2e2ddc914d, o5:58f3c5dd5bc2f436c98fc012baf182f9, o5:561859c0dd24950172c101ba3de0418b, o5:44df14dcd79b73454a0aead746a40905]` (fixture keys **M01,I01,A01,M02,A02,M03**); counts `{20,6,6,8,0,0,0,0}`.
- Status: Not run. Labels.

## T03 — K=0 / all-irrelevant / all-invalid

- **T03a** DEV20 K=0 ⇒ `status=LIMIT_ZERO`; one `ZERO_LIMIT` decision per supplied position; classifier spy not called; **`input_count=20`, `skipped_zero_limit_count=20`, all other classification counts (selected/not_selected_limit/irrelevant/invalid/oow/duplicate) = 0**.
- **T03b** pool = the 8 N-records, K=3 ⇒ `NO_RELEVANT_NEWS`, `irrelevant_count=8`, others 0.
- **T03c** two records (JSON):
  ```json
  [{"candidate_id":"o5:aaaa0000000000000000000000000001","title":"","summary":"x","source":null,"url":null,"published_at":"2026-09-25T00:00:00Z"},
   {"candidate_id":"o5:aaaa0000000000000000000000000002","title":"No title","summary":"y","source":null,"url":null,"published_at":"2026-09-25T00:00:00Z"}]
  ```
  ⇒ `NO_RELEVANT_NEWS`, `invalid_count=2` (INVALID_TITLE), selected=0; adapter `empty_kind=ALL_INVALID`.
- Status: Not run. T03c wording blocked D5.

## T04 — Empty pool / upstream empty

T04a S `candidates=[]` ⇒ all-zero counts. T04b A `FakeSearch.news=[]` ⇒ "unavailable"/"not an absence". T04c A only out-of-window raw ⇒ baseline drops ⇒ coverage-gap.

## T05 — MP-only vs mixed MP/EA

- **T05a MP-only** (JSON):
  ```json
  [{"candidate_id":"o5:b00000000000000000000000000001","title":"Fed holds rates steady at 5.25 percent","summary":"","source":null,"url":null,"published_at":"2026-09-26T10:00:00Z"},
   {"candidate_id":"o5:b00000000000000000000000000002","title":"ECB cuts deposit rate by 25 basis points","summary":"","source":null,"url":null,"published_at":"2026-09-25T10:00:00Z"},
   {"candidate_id":"o5:b00000000000000000000000000003","title":"Bank of Japan keeps policy rate unchanged","summary":"","source":null,"url":null,"published_at":"2026-09-24T10:00:00Z"}]
  ```
  K=2 ⇒ `[o5:b…01,o5:b…02]`; counts `{3,2,1,0,0,0,0,0}`.
- **T05b mixed MP/EA** (JSON): MP `o5:c…01` "Fed holds rates unchanged" (2026-09-26T10:00:00Z), EA `o5:c…02` "US payrolls rise 187,000 as unemployment ticks up" (2026-09-27T10:00:00Z); K=2 ⇒ `[o5:c…01, o5:c…02]`; counts `{2,2,0,0,0,0,0,0}`.
- Status: Not run.

## T06 — K < topics (actual IDs)

- DEV20 K=2 ⇒ `selected` actual IDs **equal `expected.k2_order_ids`** = `[o5:5bac…, o5:d55b…]` (M01,I01); counts `{20,2,10,8,0,0,0,0}`.
- Status: Not run. Labels.

## T07 — Duplicate/invalid precedence

- T07a **same ID, wrong-type first**: A `{"candidate_id":"dup-1","title":123,"published_at":"2026-09-25T00:00:00Z"}` ⇒ INVALID_RECORD (no reservation); B `{"candidate_id":"dup-1","title":"Fed holds rates","published_at":"2026-09-26T00:00:00Z"}` ⇒ SELECTED.
- T07b valid-out-of-window first reserves (`dup-2`, `2026-09-10` OUT_OF_WINDOW) ⇒ in-window same ID ⇒ DUPLICATE_ID.
- T07c title-invalid reserving: A `{"candidate_id":"dup-3","title":""}` ⇒ INVALID_TITLE (reserved); B same ID valid ⇒ DUPLICATE_ID.
- T07d structurally valid duplicate with empty title: A `dup-4` valid reserves; B `dup-4`, `title=""` ⇒ DUPLICATE_ID (step 4 before step 6).
- T07e deepcopy mutation check.
- Status: Not run.

## T08 — Negative controls / multi-topic / summary-only

T08a FedEx REJECTED; T08b CPI Group REJECTED; T08c game inflation REJECTED; T08d `Fed holds rates at 5.25%, citing cooling CPI` ⇒ [MP,IN] primary MP; T08e tariffs+`inflation rose 4 percent` ⇒ IN; T08f S&P earnings ⇒ REJECTED; T08g summary-only `US CPI rose 3.0 percent year over year` ⇒ IN; T08h `Fed holds rates as CPI cools to 2.1 percent` ⇒ [MP,IN] primary MP. **T08i clause-crossing positive:** summary `Headline inflation eased toward the ECB target ... core inflation held steady` (I02 pattern) ⇒ R1 fires (ecb+held same field, cross-clause) ⇒ [MP,IN].

## T09 — DEV20 multi-topic

M01/M02/I02/I03/I04 matched per fixture labels; **M02 and I04 are MP+IN (primary MP)**; each selected once.

## T10 — Validation

T10a empty title→INVALID_TITLE; T10b "No title"→INVALID_TITLE; T10c direct selector string timestamp→INVALID_RECORD; T10c2 serialized invalid/naive via loader→INVALID_TIMESTAMP; T10d naive datetime→INVALID_TIMESTAMP; T10e missing candidate_id→INVALID_RECORD no reservation; T10f `limit=True`→INVALID_REQUEST; T10g `limit=-1`→INVALID_REQUEST; T10g2 `limit=2.5`→INVALID_REQUEST; T10i reversed window→INVALID_REQUEST; T10j unknown rules_version→INVALID_REQUEST; T10k2 summary/source/url absent/null→defaults; T10l non-dict candidate→INVALID_RECORD; conservation.

## T11 — Boundaries

T11a `2026-09-20T00:00:00Z` IN; T11b `2026-09-27T23:59:59.999999Z` IN; T11c `2026-09-28T00:00:00Z` OUT; T11d `2026-09-27T23:00:00-08:00` (=`2026-09-28T07:00:00Z`) OUT; T11e `2026-09-26T23:00:00+05:00` (=`2026-09-26T18:00:00Z`) IN; T11f raw `providerPublishTime` at midnight-after-end excluded.

## T12 — Decision completeness

Pool: SELECTED-eligible, INVALID_TITLE, OUT_OF_WINDOW, DUPLICATE, REJECTED ⇒ `len(decisions)=5`; `counts={5,1,0,1,1,1,1,0}`; conservation.

## T13 — Vendor / partial (complete)

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

## T14 — Determinism

100×; unique-ID permutation; no clock reads; conflicting duplicates not permutation-invariant.

## T15 — Real entry, filter-before-slice

- K=3; raw nested `content` records: q1 [N1 FedEx, N2 S&P]; q2 [N3 smartphone, **M1 Fed holds rates + summary "The Fed cited cooling inflation."**]; q3 never runs. All dates `2026-09-26T10:00..13:00Z` inside window. Pool after q2 = 4 ⇒ early stop (≥3).
- Expected `executed_query_count=2`, `pre_filter_candidate_count=4`, `selected_count=1` (M1), `irrelevant_count=3`, `not_selected_limit_count=0`; `yf.Search` called twice; baseline replay `[:3]`=[N1,N2,N3] excludes M1; slice-before-filter empty.
- Status: Not run. C6, F1/F2 confirmed for `8c7eec3` only; O5 collection/isolation untested.

## T16 — No network / no LLM / attempt recording

- Selector import boundary; isolation blocks sockets + `curl_cffi`; **harness records each attempted connect/DNS/HTTP call** (patch the connect/getaddrinfo/curl entry points to append to a list AND raise), and asserts the recorded attempt list is **empty** for passing tests, so business `try/except` cannot hide an attempt; config reset + temp `data_cache_dir`.
- Status: Not run. F2 confirmed for `8c7eec3` only; actual O5 collection/isolation untested.

## T17 — Performance (proposed)

1000 records, K=30, 5 warmups + 30 runs, nearest-rank p95 ≤ 100 ms (proposal). Runner Pending F4.

## T18 — Holdout

Handoff §4. Blocked data/labels/D.

## T19 — Requested-order/subset

Request `[INFLATION, MONETARY_POLICY]` on {M01,I01}: M01 matched [INFLATION,MONETARY_POLICY] primary INFLATION; I01 INFLATION; K=2 `[M01,I01]`.

## T20 — K > available

2 relevant (MP+EA), K=10 ⇒ both selected; `{2,2,0,0,0,0,0,0}`.

---

## Invariant / fault-injection

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

## Regression

RT-1 `get_global_news` schema; RT-2 `get_news_yfinance` unchanged; RT-3 inherited macro-news tests (verified names, `tests/test_news_lookahead.py` + `tests/test_alpha_vantage_hardening.py::test_global_news_omitted_optionals_use_the_configured_defaults`) with owner-reviewed adaptation; RT-4 `get_news` schema + ticker header.

- **F status (v0.5.3-corrected-r2):** F has **closed** T13c-D/T13c-R independent sinks and the single `V-PARTIAL` assertions; the **I10 18 field-state cases**; and the **reviewed version-reference corrections** (earlier closed items, preserved).
- **r2 corrections now CLOSED (basis: the supplied Member F review):**
  1. missing `rules_version` deletion cases for all eight variants (I6-RV-1..8) - closed;
  2. I9-a evidence-builder unit-test boundary - closed;
  3. Interface section 4.2 count constraints and the four A/B passing examples (I10-A-11, I10-A-33, I10-B-11, I10-B-33) - closed;
  4. M02 vocabulary wording (`central bank`) - closed.
- **Explicitly:** this is **document-review closure**, NOT software-test execution and NOT approval of the entire test plan. All software tests remain **Not run**.
- Still pending: C/D **interface/runtime-policy** confirmation, **DEV20 human label sign-off**, and **performance runner/threshold** confirmation.

---

## Planned commands (not run)

```
pytest -q tests test/offline
pytest -q test/offline/test_o5_macro_news_filter.py
pytest -q test/offline/test_o5_macro_news_integration.py
pytest --collect-only -q tests test/offline
ruff check test/offline
```

No project test code exists; no test run; no label human-approved.
