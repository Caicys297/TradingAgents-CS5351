# O5 Macro News Filter - Requirements v0.5.3-draft (Member F latest review) - DRAFT

**Revision note (v0.5.3-corrected-r2):** active copy in `v0.5.3-corrected-r2\`; supersedes the same-named file in `v0.5.3-corrected\` (unmodified history). Active delivery references point here.

**Correction revision (v0.5.3-corrected):** this file lives in `v0.5.3-corrected\`; it supersedes the same-named file in `v0.5.3-F-review\`, which remains unmodified history. Active references point here.

**Owner:** Member E (O5). **Status:** DRAFT — all approvals Pending; all software tests Not run.
**Baseline in working checkout:** `970a9ea` (branch `main`, clean). **Member F reports** a later revision `8c7eec3` collects `tests/` and `test/offline/` — that revision is **not present in this checkout** (verified, §0.3).
**Supersedes:** `v0.5.2-F-review/O5-Requirements-v0.5.2-DRAFT.md` (retained).
**Change log:** `O5-v0.5.3-F-Review-Response.md`.
**Review artifact outside the repository; no implementation.**

---

## 0. Conventions and F-review status

### 0.1 Tags

**[FACT]** verified in this checkout; **[F-REPORTED]** asserted by Member F, not independently verified here; **[PROPOSAL]** E recommendation Pending; **[AMENDED-PROPOSAL]** changed from a previous draft and logged.

### 0.2 What changed for Member F's four points (summary)

- **F1 (I02 / matching scope):** anchor/context pairing may cross **clauses within the same field**; this had not been stated. It **does** apply to I02's summary (`ecb` ... `held`), so **I02 is MONETARY_POLICY + INFLATION**, primary MONETARY_POLICY. All 20 records rechecked; see §5.5. **Correction (v0.5.2):** v0.5.1's follow-on claim that I04 is INFLATION-only was **FALSE and is withdrawn** — I04's summary contains `Fed's` (tokenizes to `fed`,`s`) and `tightening`, so **I04 is MONETARY_POLICY + INFLATION, primary MONETARY_POLICY**. Buckets are MP=7, IN=1, EA=4; K=6 is `M01,I01,A01,M02,A02,M03`.
- **F2 (tokenization/IDs):** one percent-tokenization rule with `3.1%`, `%`, `percent` examples. FC-O5-02 → `expected.k6_order_ids`; T06 → `expected.k2_order_ids`. T03a clarification retained.
- **F3 (oracles):** T13c completed with fake responses/K/query/retry counts/evidence; I6–I10 schema examples in the Interface doc; exact caller wording vs router text distinguished.
- **F4 (CI evidence):** F3/F4 aligned to Interface §9; `8c7eec3` **not available** here; F's report recorded as F-REPORTED, not independently verified.

### 0.3 F confirmations recorded (v0.5.3)

- F **confirmed** the topic conclusions and the K=2/K=6/K=20 scheduling **given the DEV20 fixture labels**. DEV20 still needs **human label sign-off**; F's confirmation is not human label approval.
- F's **CI discovery** and **socket/curl_cffi** confirmation applies specifically to revision `8c7eec3`. Actual O5 collection and isolation remain **untested** (not executed in this pass or any prior pass).
- **F3:** `unit` accepted for offline tests. **F4:** the measurement procedure is accepted; runner and the 100 ms threshold remain **pending empirical confirmation**.
- No C/D decision, implementation or software test is approved.
- **F's latest targeted confirmations (v0.5.3-corrected):** F confirmed (a) the M02/I04 label corrections, (b) T13c's intended behavior, (c) **AM-44** (V-PARTIAL `input_count`/`reason_counts` required-null), and (d) the **I7/I8 TEST DESIGNS**. These are scoped confirmations only — not implementation approval, not software-test results, and not full human label sign-off. DEV20 labels still need human sign-off.

### 0.4 Revision availability check actually performed

`git cat-file -t 8c7eec3` ⇒ `fatal: Not a valid object name 8c7eec3`; refs are only `refs/heads/main` and `origin/main` at `970a9ea`. **I did not inspect 8c7eec3's files and do not claim its collection/isolation.** The local `970a9ea` checkout is an **older baseline**, not the current team revision.

---

## 1. Problem, verified baseline, scope

### 1.1 Verified baseline facts (at `970a9ea`)

| # | Fact | Location |
|---|---|---|
| B1 | Tool forwards clamped date + optional look_back/limit to router. | `agents/tools.py:194-215` |
| B2 | Router resolves `news_data`, walks chain. | `router.py:67-74,133-136,200-297` |
| B3 | Default `news_data` = single `yfinance`. | `default_config.py:158-167` |
| B4 | Query loop, `news_count=limit`, fuzzy, window, exact-title dedup, early stop, `[:limit]`. | `vendors/yahoo/news.py:155-201` |
| B5 | Extraction fields; no ID; null≈missing. | `news.py:16-54` |
| B6 | Formatter hides `pub_date`. | `news.py:75-84` |
| B7 | Window UTC `[start, midnight-after-end)`. | `date_window.py:24-32` |
| B8 | Empty-after-filter → coverage gap / "No global news found". | `news.py:193-199` |
| B9 | `yf_retry` retries rate limits; router tries next vendor. | `common.py:64-91`, `router.py:231-297` |
| B10 | Pytest collects only `tests/` at this checkout; isolation in `tests/conftest.py`. | `pyproject.toml:58-65`, `tests/conftest.py:59-75` |
| B11 | Policy: offline tests → `test/offline/`; team code → `src/`. | `docs/PROJECT_WORKSPACE.md:5-15` |
| B12 | Alpha Vantage payload differs. | `vendors/alpha_vantage/news.py:36-70` |
| B13 | Packaging includes only `tradingagents*`, `cli*`. | `pyproject.toml:51-52` |
| B14 | Non-dict `content` → flat branch; non-dict **article** → `.get` failure. | `news.py:22-53` |
| B15 | Error taxonomy/derivation. | `errors.py:1-58` |

**[F-REPORTED, F1/§4]** At `8c7eec3`, default configuration collects `tests/` and `test/offline/`, and `test/offline/` has socket + `curl_cffi` blocking. Not verified in this checkout; no CI/isolation change duplicated.

### 1.2 Scope [PROPOSAL]

Unchanged: Yahoo global-news filtering/allocation of already-fetched candidates before final truncation; no retrieval/LLM additions; Alpha Vantage out; public `str` preserved; no O3/O4 change.

### 1.3 Candidate-supply limitation [FACT]

Per-query `news_count` and early stop prevent O5 from recovering unfetched topics.

---

## 2. Functional requirements (full)

| ID | Pri | Statement | Acceptance target (proposed) |
|---|---|---|---|
| REQ-O5-01 | Must | For each candidate in the requested window, classify English macro relevance against the frozen, versioned rule text in §5. Query strings are context-only retrieval hints, not topics or evidence. Company-focused articles with genuine anchor+context evidence must not be excluded for being company-focused. | Determinism-stable per-record decisions with matched rule IDs; T08e selected; queries never enter classification. |
| REQ-O5-02 | Must | From qualified fetched candidates, allocate by **primary bucket** (first requested matched topic), round-robin over request topic order, bucket sort `published_at desc, candidate_id asc`, each candidate at most once, output ≤ K, fill available slots. | Scheduling deterministic given approved buckets (T01/T02/T05/T06/T19/T20). |
| REQ-O5-03 | Must | Explicit honest empty status; no irrelevant padding; K=0 distinct from upstream failure; failure never disguised as success. | T03/T04/T13 distinct. |
| REQ-O5-04 | Must | Exactly one decision per input position with matched topics, rule reason, specific reason_code; selected records keep supplied business fields verbatim. | T12; I11. |
| REQ-O5-05 | Must | Validate request; validate records per §6.2; map time window per R9; isolate/count damaged records; express upstream failure at adapter boundary. | T10/T11. |

---

## 3. NFR and invariants (full)

| ID | Pri | Statement | Acceptance target |
|---|---|---|---|
| REQ-O5-06 | Must | 100× identical ⇒ full equality; unique-ID permutations equal (input_index differs); conflicting duplicate IDs not permutation-invariant; no wall-clock in selector. | T14 |
| REQ-O5-07 | Must | Holdout precision ≥ 90 %, pre-limit recall ≥ 75 %, primary coverage 100 % when K covers human primary topics; DEV20 expected set satisfied. | T01/T18 |
| REQ-O5-08 | Must | 0 added requests, 0 LLM calls, 0 input mutations; offline no keys. | T10/T14/T16 |
| REQ-O5-09 | Must | Public signatures/types preserved; ticker path unchanged; prior applicable tests pass (owner-reviewed adaptation only). | T15/RT-1..RT-4 |
| REQ-O5-10 | Should | Proposed 1000 records, K=30, 5 warmups + 30 runs, nearest-rank p95 ≤ 100 ms on an approved runner. *(Threshold is a proposal.)* | T17 |

| Invariant | Full requirement | Runtime check | Human validation |
|---|---|---|---|
| INV-O5-01 | No fabrication / irrelevant padding | output ⊆ input; SELECTED-only publication; business-field equality (I11) | precision |
| INV-O5-02 | No out-of-input/duplicate/mutation | subset, uniqueness, deep-equality | — |
| INV-O5-03 | Window containment | adapter recompute on original `published_at` | — |
| INV-O5-04 | No network/LLM | import boundary + test-time block + **attempt recording** (T16) | — |

---

## 4. Fit criteria

| Fit ID | Pass condition | Tests |
|---|---|---|
| FC-O5-01 | DEV20 K=20 selected set = 12 proposed-relevant IDs; N rejected | T01,RT-3 |
| FC-O5-02 | `selected` actual IDs **are `expected.k6_order_ids`** (not fixture keys) | T02–T07 |
| FC-O5-03 | Empty/K=0/upstream/invalid distinct | T03,T04,T10,T12,T13 |
| FC-O5-04 | Endpoint inclusion, out-of-window rejection, per-item reasons | T10,T11 |
| FC-O5-05 | 100×; unchanged input; zero added network/LLM | T14,T16 |
| FC-O5-06 | Real entry filters before slice; query/candidate counts recorded | T15,T18 |
| FC-O5-07 | Holdout metrics + same-pool baseline delta | T18 |
| FC-O5-08 | Runner p95 ≤ 100 ms | T17 |

---

## 5. Frozen proposed rules

### 5.1 Request order / primary

`TOPIC_ORDER = [MONETARY_POLICY, INFLATION, ECONOMIC_ACTIVITY]` (default request). `primary_topic` = first **requested** topic among matched topics; request subsets reorder/filter. `matched_topics` request-ordered.

### 5.2 Tokenizer and percent rule (single, synchronized)

Order: NFKC → casefold → **percent split**: every `%` is separated to a token boundary (a `%` becomes its own token `%`), so `3.1%` tokenizes to `3.1`, `%`. Then whitespace collapse; token = maximal run of `[letters, digits, +, ., -, %]`? **No** — `%` is always its own token after the split step. Boundary characters are any non-alphanumeric except `+`, `.`, `-` (kept word-internal). Decimal point kept inside numbers.

**Normative examples:**

| Input | Tokens |
|---|---|
| `3.1%` | `3.1`, `%` |
| `%` | `%` |
| `percent` | `percent` |
| `CPI.` | `cpi` |
| `FedEx` | `fedex` |
| `Fed's` | `fed`, `s` |
| `input-cost` | `input-cost` |

Consequence: QC lists contain **both** `percent` and `%` as distinct tokens; a record with `3.1%` satisfies the `%` QC; `31 percent` satisfies `percent`.

### 5.3 Term sets ([AMENDED-PROPOSAL] from v0.4; see changelog)

| Rule | Topic | Anchors | QC | Exclusions |
|---|---|---|---|---|
| R1-MP | MONETARY_POLICY | federal reserve, fed, ecb, bank of england, boe, bank of japan, boj, central bank, monetary policy | rate, rates, policy, basis point(s), hike(s), cut(s), unchanged, holds, held, easing, tightening, normalization, quantitative easing, qe, minutes | whole-token equality (fedex≠fed, boeing≠boe, federation≠fed) |
| R2-IN | INFLATION | inflation, cpi, consumer price index, pce, core pce, disinflation, deflation, price pressure(s) | percent, %, year over year, yoy, falls, fall, rise, rises, rose, holds, held, cools, eases, eased, easing, target, sticky, pressures | `inflation` in game/virtual economy/expansion-pack field; `cpi` with no numeric/`%` token in that field |
| R3-EA | ECONOMIC_ACTIVITY | gdp, payrolls, nonfarm payrolls, unemployment, jobless, pmi, recession, retail sales, industrial production, manufacturing, consumer spending | percent, %, growth, grows, contract, contraction, expansion, rose, fell, ticks up, ticked up, beats, beating, forecasts, worries, signals, resilient, slips | `manufacturing` without R3 QC in that field |

- **Matching scope (explicit — F1):** anchor and QC must be in the **same field** (`title` or `summary`); pairing **may cross clause/sentence boundaries within that field**. It may **not** cross fields (title anchor + summary QC is not a pair).
- R4-SRCCTX: publisher alone no evidence. R5-COMPANY: company articles match only via anchor+QC. R6-NEG: proposal — negated match selectable-as-context, flagged (D review).

### 5.4 v0.4 delta and rationale

v0.4 R2 QC did not contain `easing`/`holds`/`held`/`fall`/`rose`/`eased`/`cools`; this list adds explicit inflections (no stemming). Proposed `rules_version = o5-rules-v1.1-draft`. This is an **amended proposal**, not a correction of the prior reviewer.

### 5.5 Per-record witness table (same-field, clause-crossing allowed)

| Key | Rule | Field | Anchor | QC | Field-crossing violation? | Matched (request-ordered) | Primary |
|---|---|---|---|---|---|---|---|
| M01 | R1-MP | title | fed | holds | no | [MP, IN] | MP |
| M01 | R2-IN | summary | inflation | easing | no | — | — |
| M02 | R1-MP | title | ecb | cuts | no | [MP, IN] | MP |
| M02 | R1-MP | summary | **central bank** (vocabulary entry; inside `The European Central Bank`) | rate | no | -- | -- |
| M02 | R2-IN | summary | inflation | easing | no | -- | -- |
| M03 | R1-MP | title/summary | bank of japan | rate | no | [MP] | MP |
| M04 | R1-MP | title | federal reserve | minutes | no | [MP] | MP |
| I01 | R2-IN | title | cpi | percent | no | [IN] | IN |
| **I02** | R2-IN | title | inflation | percent | no | **[MP, IN]** | **MP** |
| **I02** | R1-MP | **summary** | ecb | held (cross-clause, same field) | **allowed** | — | — |
| I03 | R2-IN | title | inflation | percent | no | [MP, IN] | MP |
| I03 | R1-MP | summary | bank of england | rate | no | — | — |
| **I04** | R2-IN | title | core pce | percent | no | **[MP, IN]** | **MP** |
| **I04** | R1-MP | **summary** | fed (from `Fed's`) | tightening | no | -- | -- |
| A01 | R3-EA | title | payrolls | percent | no | [EA] | EA |
| A02 | R3-EA | title | gdp | percent | no | [EA] | EA |
| A03 | R3-EA | title | pmi | contraction | no | [EA] | EA |
| A04 | R3-EA | title | retail sales | percent | no | [EA] | EA |
| N01 | — | title | fedex | — | — | [] | null |
| N02 | — | title | cpi | no numeric | exclusion | [] | null |
| N03 | — | title+summary | inflation | game context | exclusion | [] | null |
| N04–N08 | — | — | none | — | — | [] | null |

**Corrections found by recheck:** I02 was previously labelled INFLATION-only; its summary has `ecb` and `held` in the same field, so under clause-crossing scope it is **MP+IN, primary MP**. **I04 (v0.5.2 withdrawal):** v0.5.1 claimed I04's summary has no Fed anchor. That is **false**. The summary is "The Fed's preferred inflation gauge continued to moderate, supporting expectations of slower tightening." — the tokenizer maps `Fed's` to `fed`,`s`, and `fed` is an R1 anchor with `tightening` as an R1 QC in the same field. Therefore **I04 matches MONETARY_POLICY and INFLATION, primary MONETARY_POLICY**. **M02:** its summary is "The European Central Bank lowered its deposit facility rate, pointing to soft growth and easing inflation." — the vocabulary anchor **`central bank`** + `rate` fires R1, and `inflation` + `easing` fires R2, so **M02 is MP+IN, primary MP** (previous v0.5.1 label MP-only was wrong under the same-field rule).

### 5.6 Buckets and K expectations (recomputed)

Buckets (MP/IN/EA): **MP = {M01,M02,M03,M04,I02,I03,I04}**, **IN = {I01}**, **EA = {A01,A02,A03,A04}** => **7/1/4**.

- **K=2:** `M01, I01` (unchanged).
- **K=6:** `M01, I01, A01, M02, A02, M03` (changed).
- **K=20 round-robin:** `M01, I01, A01, M02, A02, M03, A03, M04, A04, I02, I03, I04` (changed).

**Consequence:** K=6/K=20 are **not** preserved — forced by the literal rule under clause-crossing scope. This is a label correction, not a rule change to preserve old examples.

---

## 6. Result and validation contract

### 6.1 Selector input

`candidate_id:str, title:str, summary:str→"", published_at:datetime(UTC-aware)|None, source|None, url|None`; `topics`; `start_at,end_at`; `limit int≥0 not bool`; `rules_version`. **`title_norm` derived internally** (AM-37). Loader parses valid RFC3339; per-record invalid/naive → `INVALID_TIMESTAMP`; direct-string → `INVALID_RECORD`.

### 6.2 Authoritative validation algorithm

1. Validate request (topics/window/limit/rules_version) ⇒ INVALID_REQUEST.
2. If `limit==0`: one ZERO_LIMIT per supplied position; `input_count=20`, `skipped_zero_limit_count=20`, all other classification counts = 0; stop.
3. Structure/types + non-empty `candidate_id` ⇒ INVALID_RECORD, no reservation.
4. ID already reserved ⇒ DUPLICATE_ID.
5. Else reserve ID.
6. Title (INVALID_TITLE) → timestamp (INVALID_TIMESTAMP) → window (OUT_OF_WINDOW) first applicable.
7. Classify → allocate.

### 6.3 Counts

`input_count = selected_count + not_selected_limit_count + irrelevant_count + invalid_count + out_of_window_count + duplicate_count + skipped_zero_limit_count`; `invalid_count = #INVALID_RECORD + #INVALID_TITLE + #INVALID_TIMESTAMP`.

### 6.4 Adapter K=0

Proposed skip-fetch shortcut (C6); else fetch then step 2.

### 6.5 Result object

`{selected[], decisions[], counts{8 keys}, status, metadata}` + adapter extras.

---

## 7. Identity / timestamps / ordering

R7: ID as U+001F recipe; `batch_id` content digest (Interface §4). R8 missing fields; R9 time mapping; R10 duplicates; R12-ORD round-robin.

---

## 8. Statuses

`OK`, `NO_RELEVANT_NEWS`, `LIMIT_ZERO`, `FILTERED_TO_EMPTY`, `UPSTREAM_UNAVAILABLE`. Invalid ≠ irrelevant.

---

## 9. Ownership and IDs

A coordinates; B registry; C architecture/interfaces/shared/packaging/CI-integration; D O4 safety; E rules/data/tests; F test/CI/isolation/runner. Owner IDs: C1–C7, D1–D6, F1–F4 (Interface §9). Regression RT-1..RT-4; invariant I1–I12; rules R1-MP/R2-IN/R3-EA/R4/R5/R6; ordering R12-ORD.

---

## 10. Amendments log

AM-27 separator; AM-28 synthetic sources + ID recompute; AM-29 primary contract; AM-30 QC inflections; AM-31 counts; AM-32 timestamp mapping; AM-33 K=0; AM-34 batch_id; AM-35 namespaces; AM-36 business-field guard; AM-37 internal title_norm; AM-38 tokenizer; AM-39 rules_version; **AM-40 matching scope: same-field, clause-crossing allowed**; **AM-41 I02 → MP+IN; AM-43 I04 → MP+IN, M02 → MP+IN; K=2/K=6/K=20 recomputed; buckets 7/1/4**; **AM-42 (new) FC-O5-02/T06 reference actual-ID arrays**.

---

## 11. Open decisions

E+reviewer: AM-30/39 (keep `easing`), AM-40/41 (matching scope + labels), R6 negation, AM-01/25. C1–C7; D1–D6; F1–F4 (F1/F2/F3 partly covered by F's reported revision, §0.3). Issue #1678/B3.1 unverified.

---

## 12. Review status

DRAFT. All approvals Pending. Software tests Not run. Implementation/O5-CI integration Not started.
