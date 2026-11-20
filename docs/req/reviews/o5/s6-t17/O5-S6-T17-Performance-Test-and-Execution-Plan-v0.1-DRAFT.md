# O5 S6 — T17 Performance Test and Execution Plan (DRAFT v0.2)

**Owner:** Member E (O5). **Status: DRAFT — F review is conditional (CHANGES_REQUESTED at v0.1, resolved by this v0.2 amendment pending F's re-review); A has confirmed implementation/file scope in principle on PR #31. Neither is a final approval of the test design, and T17 is not passed.**
**Historical plan baseline:** `main@99612ca` (`99612ca64445ec650b9a5f42203fa166783800b1`) — the S2–S4 merge this plan was originally written against. `main` has since advanced (O2 #23 merged), so `99612ca` is a **historical reference only, not a live implementation start point**. When coding begins, the implementation branch is cut from the then-current `main` and its full SHA is recorded in this document and the test manifest (§3, §9).
**Documentation only.** No fixture, harness, or CI job exists yet; nothing here is implemented.
**Measured:** nothing. T17 has **not** been run; no timing result is claimed.
**v0.2 change scope:** documentation corrections only, addressing F's four pre-coding findings on PR #31 (fixture self-consistency, oracle reconciliation adjudication, dual-hash integrity and warmup failure, plus the F1–F6 arithmetic). No code, fixture, or CI change is made by this amendment.

---

## 0. Scope and non-goals

- **In scope:** a fixed 1000-record fixture, an independently derived expected-result oracle, a measurement harness in `test/offline/`, and a proposed CI invocation for the `REQ-O5-10` runner.
- **Out of scope:** changing the selector, the adapter, any public API, retrieval behaviour, or S5 persistence. S5's O2 `run_dir` handoff **remains with C and does not block S6** — the harness calls the pure selector and writes no run-directory evidence.
- **No test-suite execution** is required to land this document.

## 1. Requirement values (fixed; not open for re-approval here)

These are the existing `REQ-O5-10` values and are quoted, not proposed:

| Value | Source |
|---|---|
| **1000 records**, **K=30** | `REQ-O5-10.statement` |
| **ubuntu-latest / Python 3.11** | `REQ-O5-10.fit_criterion` |
| **5 warmups**, **30 measured calls** | `fit_criterion` |
| **nearest-rank p95 = 29th smallest of 30** | `fit_criterion` |
| **p95 ≤ 100 ms** | `REQ-O5-10.threshold` |
| report **fixture hash and runner** | `fit_criterion` |
| any incorrect/exceptional measured call ⇒ T17 fails overall | approved v1.4 execution plan §9 |

The **runner and 100 ms gate apply only to ubuntu-latest/Python 3.11.** On any other interpreter or host the harness still verifies correctness and reports timings, but a p95 above 100 ms is informational, never a failure.

## 2. Proposed fixture (for F/A review)

**Not created.** Proposed path: `test/offline/fixtures/o5/O5-T17-Perf-Fixture-1000-v1.json`.

The six groups below are **mutually exclusive rows** — each record belongs to exactly one group, and the six counts sum to the total. F6 is **not** a subset of F5; the earlier v0.1 wording ("last 20 of F5", 80 irrelevant) double-counted and summed to 1020 and is withdrawn.

| Case | Count | Shape |
|---|---|---|
| F1 MP-only relevant | 280 | distinct titles, each R1-MP anchor+context |
| F2 IN-only relevant | 260 | R2-IN anchor+context |
| F3 EA-only relevant | 260 | R3-EA anchor+context |
| F4 multi-topic (MP+IN) | 120 | both rule pairs fire in one field |
| F5 ordinary irrelevant | 60 | no anchor; ordinary content, normal ID recipe |
| F6 duplicate-ID | 20 | **irrelevant** content (no anchor) whose `candidate_id` is deliberately copied from the first 20 F1 records |
| **Total** | **1000** | 280+260+260+120+60+20 = **1000** |

**Unique IDs and duplicate occurrences.** F1–F5 (280+260+260+120+60 = 980 records) each carry a `candidate_id` derived by the normal recipe, so they contribute **980 unique IDs**. F6's 20 records reuse 20 of those existing IDs (the first 20 F1 IDs) and therefore add **0 new IDs**: the fixture has **980 unique IDs** and **1000 input records**, i.e. **20 duplicate occurrences**. F6's content is irrelevant even under its reused ID, because relevance is computed from the record's own title/summary, not from its ID.

**Controlled exception to the ID recipe (explicit).** For all 980 non-F6 records, `candidate_id` is derived from that record's own fields (see recipe below), so the ID is a function of the content. F6 is a **deliberate, documented exception**: it overrides this contract to reuse 20 IDs from F1 in order to exercise the duplicate-occurrence path. The exception is confined to F6 and must be assertable — the fixture generator asserts that exactly the F6 rows deviate from the recipe and that every other row satisfies it.

**Input position, and preference of duplicate over irrelevant.** Each record carries its group tag for auditing only; the input array order is fixed as F1, F2, F3, F4, F5, F6 (deterministic order must not be left implicit). Because a duplicate is recognised by `candidate_id` before relevance is judged, an F6 record is counted in `counts.duplicate` and **not** also in `counts.irrelevant` — this is why the decision counts below show `duplicate 20` and `irrelevant 60`, never `irrelevant 80`.

**Fixed request (request topics + window + ordering).** `request.topics = ["MP","IN","EA"]` in that order (primary-topic precedence MP → IN → EA); `request.window` = `[min(published_at), max(published_at)]` over all 1000 records inclusive; `request.limit = 30`. The documented sort key `(-published_at, candidate_id)` is applied within each bucket, and the merged candidate order preserves the fixed input order for equal keys.

**Buckets (by primary topic of relevant records):** relevant total **920** = MP primary 400 (F1 280 + F4 120) · IN primary 260 (F2) · EA primary 260 (F3). F4's 120 records match both MP and IN, and take MP as primary under the MP → IN → EA precedence. F5 (60) and F6 (20) are irrelevant.

**Decision-count conservation** against the approved `REQ-O5` selector contract (`development_contract.o5`, selector status/count fields), for a 1000-record fixture with `limit = 30` and 920 relevant candidates:

| `counts` key | Value | Derivation |
|---|---|---|
| `input` | **1000** | all records considered |
| `selected` | **30** | `limit` reached, round-robin 10/10/10 |
| `not_selected_limit` | **890** | 920 relevant − 30 selected |
| `irrelevant` | **60** | F5 only (F6 is counted as duplicate, not irrelevant) |
| `invalid` | **0** | every record well-formed |
| `out_of_window` | **0** | window is the fixture's own min/max |
| `duplicate` | **20** | F6 duplicate occurrences dropped |
| `skipped_zero_limit` | **0** | `limit = 30` |

Conservation check: `selected 30 + not_selected_limit 890 + irrelevant 60 + invalid 0 + out_of_window 0 + duplicate 20 + skipped_zero_limit 0 = 1000 = input`. ✓ These exact counts are the frozen expectations in §3; retuning any group count requires recomputing every row of this table and the conservation identity.

**Determinism rules:** 1000 distinct UTC timestamps at +10-minute steps inside one fixed window; for the 980 non-F6 records `candidate_id = "o5:" + sha256(canon(title)+U+001F+canon(source)+U+001F+""+U+001F+iso)[:32]` (the recipe already used by the merged adapter); F6 copies the first 20 F1 IDs as stated above; synthetic sources; `url: null`; titles ≤ 300 chars, summaries ≤ 2000 chars. Each record also carries a `fixture_group` tag (F1–F6) for audit; the selector ignores unknown fields.

## 3. Expected-result oracle — derived independently of `select_macro_news`

**Not created.** Proposed path: `test/offline/fixtures/o5/O5-T17-Expected-Results-v1.json`.

The oracle must not be produced by the code under test:

1. Author the per-record primary topic by hand from the documented rule text (first requested topic among matched topics), reading the fixture titles/summaries — not by calling the selector.
2. Sort each bucket with the documented key `(-published_at, candidate_id)` using plain tuple sorting in a separate authoring script that does **not** import the selector.
3. Round-robin MP → IN → EA, one per bucket per pass, until 30.
4. **Freeze** the resulting ordered 30 IDs, `status`, per-topic counts and all eight `counts` keys into the expected file; record **its SHA-256 and the input fixture's SHA-256** in the manifest (§3a). Freezing happens **before the first performance measurement** and is traceable: the frozen file's hash, the fixture hash it was derived from, the rules version, and the adjudication log (§3a) are all written into the manifest.
5. **One-time reconciliation, with independent adjudication of every disagreement.** Run the merged selector against the frozen fixture **once** and compare field by field. Every disagreement — whether in `status`, ordered IDs, per-topic counts, or any `counts` key — is adjudicated individually against the fixed fixture content and the documented rules (`REQ-O5` selector contract and the `RULE_TABLE` rule text), **not** assumed in advance to be a fixture/oracle defect. Either outcome is permitted:
   - **Oracle wrong** — a genuine authoring error (wrong hand-assigned topic, wrong sort key, wrong round-robin). Corrected only after the adjudication reason is recorded; the corrected file is **re-frozen to a new SHA-256**, the old and new hashes and the reason are logged in the manifest, and the change is re-reviewed. Silent re-freezing is prohibited.
   - **Implementation wrong** — a selector defect the fixture exposes. The reconciliation is recorded as a **failing result** and escalated to the owner of the selector/adapter (with the exact record, rule text and observed vs expected values) instead of adjusting the oracle. **The expected file is never regenerated from selector output and expectations are never changed to make the test pass.** A reconciliation that ends in "both happened to differ" is resolved per field, not globally.
   - The adjudication log (each discrepancy: field, fixture record/ID, selector value, oracle value, documented rule, verdict, resolution, resulting expected-file SHA-256) is retained in the manifest as evidence.

**Expected values (to be frozen):** `status=OK`, `selected_count=30`, 10/10/10 per topic, counts `input 1000, selected 30, not_selected_limit 890, irrelevant 60, invalid 0, out_of_window 0, duplicate 20, skipped_zero_limit 0` (conserves as shown in §2). Reconciliation is evidence only; the values come from the independent derivation (§3.1–§3.4), never from the selector.

### 3a. Integrity manifest (dual hashes; proposed)

**Not created.** Proposed path: `test/offline/fixtures/o5/O5-T17-Manifest-v1.json`. **No hash value exists until the fixture and expected files are actually created** — this section fixes the *fields and procedure*, not values.

| Field | Meaning |
|---|---|
| `rules_version` | selector rules version the oracle assumes (e.g. `o5-rules-v1.1-draft`) |
| `record_count` | **1000** |
| `k` | **30** |
| `request_topics`, `request_window` | the fixed request (§2) |
| `fixture_sha256` | SHA-256 of `O5-T17-Perf-Fixture-1000-v1.json` |
| `expected_sha256` | SHA-256 of `O5-T17-Expected-Results-v1.json` |
| `implementation_main_sha` | full `main` SHA the implementation branch was cut from (§9) |
| `adjudication_log` | every reconciliation discrepancy + resolution (§3.5) |
| `runner` | ubuntu-latest / CPython 3.11.x |

**Verification order (both hashes, before any warmup):** compute the SHA-256 of the **input fixture** and of the **frozen expected file**, and assert **both** equal the manifest values, **and** assert `record_count=1000`, `k=30` and the fixed topics/window and `rules_version` match. If either hash or any invariant fails, T17 **fails immediately** — no warmup and no measurement run. This guards the fixture and the expectations independently, not just the expected file as v0.1 stated.

## 4. Timing boundary

| Phase | Inside timing? |
|---|---|
| Read + `json.load` fixture, RFC3339 parse, candidate/request construction | **No** |
| **One `select_macro_news(candidates, request)` call** | **Yes** |
| Result comparison, assertions, file I/O, report writing | **No** |

## 5. Measurement procedure

1. Load fixture and expected; verify **both** SHA-256 hashes against the manifest and the fixed `record_count`/`k`/topics/window/`rules_version` invariants (§3a) **before any warmup**. Any failure ⇒ T17 fails; do not proceed.
2. Build candidates and request once, outside the clock.
3. **5 warmup calls. Their timings are discarded, but they are not unchecked:** each warmup call must return a result equal to the oracle and must not raise. A warmup **exception or incorrect result fails T17 outright** — the run does **not** continue to the measured calls, and it must never be reported as "5 warmups completed". A failing warmup is recorded with the same first-mismatch detail as a measured failure.
4. 30 measured calls, each `perf_counter_ns` around exactly one selector call.
5. **Correctness gate on every measured call:** `status`, all counts, ordered selected IDs and per-topic counts must equal the oracle. Any mismatch or exception ⇒ **T17 fails overall**; the sample is not discarded.
6. p95 = `sorted(timings)[28]` (nearest-rank over 30 samples).

## 6. Report contents

```
runner          : ubuntu-latest / CPython 3.11.x
main_sha        : <40 hex — main the implementation branch was cut from>
fixture         : O5-T17-Perf-Fixture-1000-v1.json  sha256=<64 hex>  verified=true
expected        : O5-T17-Expected-Results-v1.json    sha256=<64 hex>  verified=true
samples         : 5 warmups (timings discarded, results verified) + 30 measured
correctness     : PASS (5/5 warmups + 30/30 measured equal to oracle)   # or FAIL + first mismatch (warmup or measured)
timings_ms      : min / median / p95 / max
p95 (29th)      : <value> ms   threshold <= 100 ms   => PASS/FAIL (REQ-O5-10 runner only)
raw             : [30 values in ms]
```

Both the fixture and the expected-file SHA-256 are reported (not only the expected file), along with the `main` SHA the implementation was built from. Variance is reported, not averaged away: min, median, p95, max and all 30 raw values.

## 7. Proposed harness file (for review)

**Not created.** `test/offline/test_o5_macro_news_perf.py`, marked `unit` (never `integration`), so the existing offline isolation in `test/offline/conftest.py` applies unchanged. The harness adds no network or LLM calls.

## 8. Proposed CI invocation (for A/F review)

Current state at `99612ca`: the `test` job runs plain `pytest -v` over `python-version: ["3.11","3.12","3.13","3.14"]` plus a 3.12 `America/New_York` include, on `ubuntu-latest`. There is no per-matrix selector today, so the gate must not be asserted there.

**Proposal (`.github/workflows/ci.yml` is F's shared CI file — A confirmed on PR #31 that E and F align and F lands it or a jointly-attributed PR carries it; E does not edit it): a dedicated job.**

```yaml
  o5-perf:
    name: o5 T17 performance (ubuntu-latest, py3.11)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - name: T17 gate
        env: { O5_T17_ENFORCE_THRESHOLD: "1" }
        run: pytest -q test/offline/test_o5_macro_news_perf.py
```

Harness contract: `O5_T17_ENFORCE_THRESHOLD` unset ⇒ correctness asserted, timings reported, threshold **not** enforced; `= 1` ⇒ additionally fail if p95 > 100 ms, and fail if the platform is not Linux or the interpreter is not 3.11. This keeps the gate on the `REQ-O5-10` runner while the other matrices only check correctness.

## 9. Files this batch would add (after approval)

| Path | Role |
|---|---|
| `test/offline/fixtures/o5/O5-T17-Perf-Fixture-1000-v1.json` | 1000 input records (980 unique IDs, 20 duplicate occurrences) |
| `test/offline/fixtures/o5/O5-T17-Expected-Results-v1.json` | frozen oracle, independent of selector |
| `test/offline/fixtures/o5/O5-T17-Manifest-v1.json` | rules version, dual SHA-256, request, `implementation_main_sha`, adjudication log |
| `test/offline/test_o5_macro_news_perf.py` | harness |
| `.github/workflows/ci.yml` (F-owned) | dedicated `o5-perf` job, landed by F or an explicitly attributed joint PR |

A confirmed the first four files on PR #31 (scope in principle). **Implementation branch is cut from the then-current `main` and records its full SHA** — `99612ca` is the historical plan baseline only, not the implementation start point. If the tests expose a need for a production change, that difference is reported before any production edit (A's request).

## 10. Review requests

**For F (test design) — conditional review at v0.1, re-review of v0.2 requested:**
1. F confirmed the timing boundary, 5 warmups + 30 measured calls, nearest-rank 29th, per-call correctness gate, raw-30/runner/hash reporting, and the threshold-on-separate-job split; F raised four pre-coding items now addressed:
   - **Composition arithmetic** — F1–F6 are now mutually exclusive 280/260/260/120/60/20 = 1000, F6 is no longer a subset of F5, duplicate-before-irrelevant and the ID-recipe exception are explicit (§2).
   - **Oracle reconciliation** — every disagreement is now independently adjudicated; either oracle or implementation may be found wrong; no regeneration from selector output, no silent re-freeze (§3.5).
   - **Dual-hash integrity + warmup failure** — both fixture and expected hashes recorded and verified before warmups; warmup exceptions/incorrect results fail T17 (§3a, §5, §6).
   - **Ordering/buckets/counts** — fixed request topics/window/order and conserved counts restated (920 relevant, 60 irrelevant, 20 duplicate, 30 selected / 890 not-selected) (§2).
2. Confirm `rules_version` pinned in the manifest is the version the oracle assumes.

**For A (implementation / file / CI scope) — confirmed in principle on PR #31:**
1. A confirmed the four test-side files and that no production file changes; independent `o5-perf` job enforces p95 only on ubuntu-latest/Python 3.11.
2. `ci.yml` remains F's shared file; E and F align and F lands the job (or an attributed joint PR).
3. A confirmed the implementation branch starts from the then-latest `main` with its SHA recorded — `99612ca` is historical only.

## 11. Status

| Item | Status |
|---|---|
| Fixture | **Proposal** — not created |
| Oracle | **Proposal** — not created |
| Manifest (dual hash) | **Proposal** — not created |
| Harness | **Proposal** — not created |
| CI job | **Proposal** — F-owned `ci.yml`, not landed |
| A scope confirmation | **Confirmed in principle** (PR #31) — not a test-design approval |
| F test-design review | **Conditional / CHANGES_REQUESTED at v0.1** — v0.2 addresses the four items, pending re-review; not a final approval |
| T17 measurement | **Not run** |
| S5 `run_dir` handoff | **C-owned, unresolved** — does not block S6 |
