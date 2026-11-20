# O5 S6 — T17 Performance Test and Execution Plan (DRAFT v0.1)

**Owner:** Member E (O5). **Status: DRAFT — PENDING F's test-design review and A's implementation/file/CI-scope approval.**
**Baseline:** `main@99612ca` (`99612ca64445ec650b9a5f42203fa166783800b1`) — the S2–S4 merge that this plan builds on.
**Documentation only.** No fixture, harness, or CI job exists yet; nothing here is approved or implemented.
**Measured:** nothing. T17 has **not** been run; no timing result is claimed.

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

| Case | Count | Shape |
|---|---|---|
| F1 MP-only relevant | 280 | distinct titles, each R1-MP anchor+context |
| F2 IN-only relevant | 260 | R2-IN anchor+context |
| F3 EA-only relevant | 260 | R3-EA anchor+context |
| F4 multi-topic (MP+IN) | 120 | both rule pairs fire in one field |
| F5 irrelevant | 80 | no anchor |
| F6 duplicate-ID | 20 | last 20 of F5 reuse F1's first 20 `candidate_id`s |

Totals: 1000 records, **980 unique IDs**, 20 duplicate occurrences.
Buckets: MP primary 400 · IN 260 · EA 260 · relevant total 920.

**Determinism rules:** 1000 distinct UTC timestamps at +10-minute steps inside one fixed window; `candidate_id = "o5:" + sha256(canon(title)+U+001F+canon(source)+U+001F+""+U+001F+iso)[:32]` (the recipe already used by the merged adapter); synthetic sources; `url: null`; titles ≤ 300 chars, summaries ≤ 2000 chars.

## 3. Expected-result oracle — derived independently of `select_macro_news`

**Not created.** Proposed path: `test/offline/fixtures/o5/O5-T17-Expected-Results-v1.json`.

The oracle must not be produced by the code under test:

1. Author the per-record primary topic by hand from the documented rule text (first requested topic among matched topics), reading the fixture titles/summaries — not by calling the selector.
2. Sort each bucket with the documented key `(-published_at, candidate_id)` using plain tuple sorting in a separate authoring script that does **not** import the selector.
3. Round-robin MP → IN → EA, one per bucket per pass, until 30.
4. **Freeze** the resulting ordered 30 IDs, `status`, per-topic counts and all eight `counts` keys into the expected file; record its SHA-256 in the manifest.
5. **One-time reconciliation:** run the merged selector against the frozen fixture once and compare. Any disagreement is investigated as a fixture/oracle defect; the frozen oracle is **never** overwritten from selector output, and the reconciliation result is recorded as evidence, not as the values' source.

Expected values (to be frozen): `status=OK`, `selected_count=30`, 10/10/10 per topic, counts `input 1000, selected 30, not_selected_limit 890, irrelevant 60, invalid 0, out_of_window 0, duplicate 20, skipped_zero_limit 0` (conserves).

## 4. Timing boundary

| Phase | Inside timing? |
|---|---|
| Read + `json.load` fixture, RFC3339 parse, candidate/request construction | **No** |
| **One `select_macro_news(candidates, request)` call** | **Yes** |
| Result comparison, assertions, file I/O, report writing | **No** |

## 5. Measurement procedure

1. Load fixture and expected; assert the fixture SHA-256 matches the manifest.
2. Build candidates and request once, outside the clock.
3. 5 warmup calls, discarded.
4. 30 measured calls, each `perf_counter_ns` around exactly one selector call.
5. **Correctness gate on every measured call:** `status`, all counts, ordered selected IDs and per-topic counts must equal the oracle. Any mismatch or exception ⇒ **T17 fails overall**; the sample is not discarded.
6. p95 = `sorted(timings)[28]` (nearest-rank over 30 samples).

## 6. Report contents

```
runner        : ubuntu-latest / CPython 3.11.x
fixture       : O5-T17-Perf-Fixture-1000-v1.json  sha256=<64 hex>
expected      : O5-T17-Expected-Results-v1.json    sha256=<64 hex>
samples       : 5 warmups (discarded) + 30 measured
correctness   : PASS (30/30 equal to oracle)   # or FAIL + first mismatch
timings_ms    : min / median / p95 / max
p95 (29th)    : <value> ms   threshold <= 100 ms   => PASS/FAIL (REQ-O5-10 runner only)
raw           : [30 values in ms]
```

Variance is reported, not averaged away: min, median, p95, max and all 30 raw values.

## 7. Proposed harness file (for review)

**Not created.** `test/offline/test_o5_macro_news_perf.py`, marked `unit` (never `integration`), so the existing offline isolation in `test/offline/conftest.py` applies unchanged. The harness adds no network or LLM calls.

## 8. Proposed CI invocation (for A/F review)

Current state at `99612ca`: the `test` job runs plain `pytest -v` over `python-version: ["3.11","3.12","3.13","3.14"]` plus a 3.12 `America/New_York` include, on `ubuntu-latest`. There is no per-matrix selector today, so the gate must not be asserted there.

**Proposal (A to approve — CI is outside E's file rights): a dedicated job.**

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
| `test/offline/fixtures/o5/O5-T17-Perf-Fixture-1000-v1.json` | 1000 input records |
| `test/offline/fixtures/o5/O5-T17-Expected-Results-v1.json` | frozen oracle |
| `test/offline/fixtures/o5/O5-T17-Manifest-v1.json` | version, hashes, recipe, runner |
| `test/offline/test_o5_macro_news_perf.py` | harness |
| `.github/workflows/ci.yml` (pending A) | dedicated `o5-perf` job |

## 10. Review requests

**For F (test design):**
1. Approve the F1–F6 composition and the frozen expected counts.
2. Approve the **independent oracle derivation** (§3), including the one-time reconciliation being evidence rather than source.
3. Approve the timing boundary, per-call correctness gate, and report format.

**For A (implementation / file / CI scope):**
1. Approve the four new files and that no production file changes.
2. Approve the dedicated `o5-perf` CI job and the env-var split (§8).
3. Confirm implementation begins on a named branch from `99612ca`, not on a detached HEAD.

## 11. Status

| Item | Status |
|---|---|
| Fixture | **Proposal** — not created |
| Oracle | **Proposal** — not created |
| Harness | **Proposal** — not created |
| CI job | **Proposal** — pending A |
| T17 measurement | **Not run** |
| S5 `run_dir` handoff | **C-owned, unresolved** — does not block S6 |
