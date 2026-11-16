# O4 — Pre-Implementation Test Plan

| Field | Value |
|---|---|
| Plan ID | O4-TEST-v0.3 |
| Status | Draft / Approval Pending |
| Owner | Member D (Safety and Reliability Lead) |
| Prepared for | Member F (test coordination, CI integration, verification) |
| Approval | Pending |
| **Authoritative requirements baseline** | `docs/req/requirements.yaml` — Caicys297/TradingAgents-CS5351 PR #2 merged baseline (main commit **`4f87e29f7a52842dba8272071d2a4a1b527def10`**, 2026-11-16); PR #2 commit snapshot `f411763c3d080bddde425c60a7a06d1797913328`; prose `docs/req/sources-v2.0/O4-requirements.md` |
| Superseded draft reference | `O4-requirements.md` (workspace draft revision **O4-REQ-r3**) — a working draft, NOT the approved baseline; its FR-04 `Should` and NFR-03 `TBD` values are superseded by the authoritative registry |
| Source CI plan | `F_CI_Gate_Plan_for_Team_Review_Revised.md` |
| Performance methodology (T-16) | `O4_T16_Performance_Verification_Plan.md`, v0.1 (Proposed) |
| Registry | Requirements Registry / Schema 1.0.0 (Member B confirmed; O4 IDs preserved) |
| Supersedes | O4-TEST-v0.2, O4-TEST-v0.1 |

> **Status of this document.** This is a *pre-implementation* test plan. No test in this plan has been written, executed, or approved. The O4 checker module (`tradingagents/agents/evidence_gate.py`) and the O4 test files do **not** exist in the workspace. Every test ID below is a **proposed identifier**, not a passing test. No approval, benchmark measurement, or result is fabricated here. The A/C architecture directions (buffering; checker-failure fail-closed; configuration-error abort; rating precedence/conflict) are **architecture directions only** — they are not pre-coding test-plan approval.
>
> **Confirmed performance target vs. unmeasured results.** O4-NFR-03 (`Should`) has a **confirmed numeric target** from the authoritative registry: nearest-rank **p95 added latency <= 10 ms** (fixed four-report fixture, 5 warmups, 30 measured calls, `ubuntu-latest`/Python 3.11). This target is approved requirements direction; it is distinct from (a) this test plan, which remains **Draft / Approval Pending**, and (b) the benchmark results, which have **not been measured** — no passing performance result is claimed. The sampling protocol and Gate invocation point remain subject to F and A/C confirmation (see §4 T-16 and §9).

---

## 1. Document metadata and conventions

- **Plan ID:** O4-TEST-v0.3 (versioned; increments on each reviewed revision).
- **Owner:** Member D.
- **Status:** Draft.
- **Approval:** Pending. Approval record completed in Section 11 only by the authorised reviewer(s).
- **Authoritative requirements baseline:** `docs/req/requirements.yaml` at main commit `4f87e29f7a52842dba8272071d2a4a1b527def10` (PR #2 merged). FR-04 = `Won't`; NFR-03 = `Should`, p95 `<= 10 ms`; INV-05 maps to O4-T-25.
- **Superseded draft:** `O4-requirements.md` O4-REQ-r3 (working draft; its FR-04/NFR-03 values are not the approved baseline).
- **Requirement IDs** (`O4-FR-01…16`, `O4-NFR-01…08`, `O4-INV-01…05`) and **test IDs** (`O4-T-01`…`O4-T-25`) are preserved/extended as in `O4-requirements.md`.

**Traceability rule (course Test Approval Gate, F plan §2.1):** tests must be approved before implementation begins. This plan requests approval; it does not grant it.

**Status labels:** **PROPOSED** (specified, not written); **NOT YET IMPLEMENTED** (module/test absent); **PENDING TEAM APPROVAL** (decision unresolved); **UNVERIFIED** (path/command not confirmed); **MANUAL** (review activity, not an automated test).

---

## 2. Testing scope and O4 v1 boundaries

### 2.1 In scope (v1)
- Deterministic check that **required analyst reports are present and non-empty**.
- Classification per required evidence item: `present` / `missing` / `unavailable` / `not_required`.
- Producing `effective_rating`: original PM rating when evidence complete, else `REVIEW`.
- **Original-rating precedence** (`final_rating` first, else parsed body) and conflict-to-`REVIEW`.
- **CLI buffering**: no raw PM Buy/Sell published as authoritative before the gate.
- Consistency of `effective_rating` across enabled surfaces.
- Fail-closed on recoverable checker failure; abort on configuration error.
- Preserving `final_trade_decision` unchanged; labelling it unapproved when `REVIEW`.

### 2.2 Out of scope (v1) — from O4-FR-14 and the v1 boundary statement
- Semantic truthfulness/completeness of data inside a non-empty report.
- Minimum content-length, cross-verification, or requiring debate histories.
- Whole-report explicit-unavailable detection — **not implemented in v1** (O4-FR-04 is `Won't`). O4-T-04 verifies the negative: unavailable-source text inside a non-empty report is still structurally `present` and does not trigger `REVIEW`.
- Durable persistence of the evidence verdict (O4-NFR-06 durable half, PENDING).
- O1 single-SMA insufficient-history text alone triggering `REVIEW`.
- O5 filtered-empty news alone automatically implying O4 `REVIEW`.

### 2.3 O4/O5 boundary
- O4 checks report **presence and non-emptiness**, not factual content.
- An **O5 filtered-empty** result alone does **not** force O4 `REVIEW` (used when no usable items remain after O5's own filtering, not a missing report).
- If News Analyst is selected and `news_report` is absent/empty, O4 **MUST** downgrade to `REVIEW`.
- A single insufficient-history SMA from O1 does not imply the whole market report is missing.

---

## 3. Requirement-to-test traceability matrix

Executable = automated offline test. Manual = scope review. Pending = depends on an unapproved decision (§10).

### 3.1 Functional Requirements

| Requirement | Priority | Test IDs | Test type | Pending dependency |
|---|---|---|---|---|
| O4-FR-01 | Must | O4-T-01 | Unit | — |
| O4-FR-02 | Must | O4-T-01, O4-T-09 | Unit | — |
| O4-FR-03 | Must | O4-T-02, O4-T-03, O4-T-14, O4-T-17, O4-T-24 (Case B) | Unit (parameterized) | — |
| O4-FR-04 | Won't (v1) | O4-T-04 | Unit (negative/boundary, executable) | — (no sentinel in v1; registry verification `["O4-T-04"]`) |
| O4-FR-05 | Must | O4-T-06 | Unit | — |
| O4-FR-06 | Must | O4-T-05, O4-T-13 | Unit | — |
| O4-FR-07 | Must | O4-T-08, O4-T-19, O4-T-23 | Unit + Integration | Integration point (Q4) PENDING |
| O4-FR-08 | Must | O4-T-11 | Unit | — |
| O4-FR-09 | Must | O4-T-07, O4-T-08 | Unit + Integration | Integration point (Q4) PENDING |
| O4-FR-10 | Should | O4-T-12 | Unit | — |
| O4-FR-11 | Should | O4-T-05, O4-T-18 | Unit | — |
| O4-FR-12 | Must | O4-T-10, O4-T-19 | Unit | — |
| O4-FR-13 | Must | O4-T-10, O4-T-19, O4-T-23 | Unit + Integration | Integration point (Q4) PENDING |
| O4-FR-14 | Won't (v1) | O4-T-22 | Manual | — |
| O4-FR-15 | Must | O4-T-18 | Unit + Integration | Integration point (Q4) PENDING |
| O4-FR-16 | Must | O4-T-25 | Unit | — |

### 3.2 Non-functional Requirements

| Requirement | Priority (proposed) | Test IDs | Test type | Pending dependency |
|---|---|---|---|---|
| O4-NFR-01 | Must (proposed) | O4-T-11 | Unit | — |
| O4-NFR-02 | Must (proposed) | O4-T-15 | Unit (collection) | — |
| O4-NFR-03 | Should | O4-T-16 | Benchmark | p95 `<= 10 ms` (fixed four-report fixture, 5 warmups, 30 measured calls, ubuntu-latest/Py3.11); non-blocking Should — see §9 |
| O4-NFR-04 | Must (proposed) | O4-T-07 | Unit + dependency review | — |
| O4-NFR-05 | Should (proposed) | O4-T-20 | Regression + signature review | Gate not wired (Q4) |
| O4-NFR-06 | Should (proposed) | O4-T-08, O4-T-21 | Integration + artefact inspection | Durability TBD (Q5) |
| O4-NFR-07 | Should (proposed) | O4-T-22 | Manual | — |
| O4-NFR-08 | Must (proposed) | O4-T-08 | Integration | — |

### 3.3 Safety invariants

| Invariant | Test IDs | Test type | Pending dependency |
|---|---|---|---|
| O4-INV-01 | O4-T-02, O4-T-08, O4-T-19, O4-T-23 | Unit + Integration | Q4 for integration cases |
| O4-INV-02 | O4-T-06, O4-T-25 | Unit | — |
| O4-INV-03 | O4-T-08, O4-T-23 | Integration | Q4 |
| O4-INV-04 | O4-T-07, O4-T-08 | Unit + Integration | Q4 |
| O4-INV-05 | O4-T-25 | Unit | — (registry verified: `verification: ["O4-T-25"]` at main commit `4f87e29f`; earlier apparent mismatch resolved) |

---

## 4. Test case catalogue (O4-T-01 … O4-T-25)

Each entry gives objective, input/setup, execution approach, expected outcome, pass/fail assertion, test type, and dependencies. All are **PROPOSED / NOT YET IMPLEMENTED**. Parameterized tests retain their original identity while expanding across the four report fields.

### O4-T-01 — Complete evidence preserves rating
- **Covers:** O4-FR-01, O4-FR-02
- **Objective:** A complete, valid state yields `valid` and preserves the original rating.
- **Input/setup:** Plain `dict` state; all four reports non-empty; `final_rating="Overweight"`; all four selected.
- **Execution:** Call the checker directly (offline).
- **Expected outcome:** `verdict="valid"`; `effective_rating="Overweight"`.
- **Pass/fail assertion:** `result.verdict == "valid" and result.effective_rating == "Overweight"`.
- **Type:** Offline unit.
- **Dependencies:** Checker module exists.

### O4-T-02 — Single empty required report forces REVIEW (parameterized)
- **Covers:** O4-FR-03, O4-INV-01
- **Objective:** Any one empty required report downgrades to `REVIEW` and is named.
- **Input/setup:** Parameterized over `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`: set the chosen report to `""`, other required reports non-empty, `final_rating="Buy"`, all four selected. Plus a multi-missing case (two required reports empty simultaneously).
- **Execution:** Checker call per parameter set.
- **Expected outcome:** `verdict="review"`; failing set == exactly the empty report(s); effective `REVIEW`.
- **Pass/fail assertion:** `verdict=="review" and set(failing)==expected_failing and effective=="REVIEW"`.
- **Type:** Offline unit (negative/safety-critical).
- **Dependencies:** Checker module.

### O4-T-03 — Whitespace-only, whitespace variants, multi-missing (parameterized)
- **Covers:** O4-FR-03
- **Objective:** Whitespace-only counts as empty; multiple missing reports all reported.
- **Input/setup:** Parameterized: each required report whitespace-only (`"   \n\t "`); plus a multi-missing case combining an empty and a whitespace-only report.
- **Execution:** Checker call per parameter set.
- **Expected outcome:** each whitespace-only report classified `missing`; exact failing set; downgrade.
- **Pass/fail assertion:** `set(failing)==expected_failing and verdict=="review"`.
- **Type:** Offline unit (boundary).
- **Dependencies:** Checker module; whitespace rule.

### O4-T-04 — Unavailable-source text is structurally present (negative/boundary)
- **Covers:** O4-FR-04 (priority `Won't` for v1 — no whole-report sentinel recognition)
- **Objective:** Non-empty text containing `N/A`, an unavailable-source note, or similar text is still structurally `present`; it is **not** classified `unavailable` and does **not** cause a downgrade solely because of that text.
- **Input/setup:**
  1. A selected analyst produces a **non-empty** report containing `N/A`, an unavailable-source note, or similar text (e.g. a `NO_DATA_AVAILABLE` / "unavailable" note inside an otherwise non-empty body).
  2. All other required analyst reports are present and non-empty.
  3. The original rating (`final_rating`) is clearly specified (e.g. `Buy`).
  4. Any parseable decision-body rating **agrees** with `final_rating` (to avoid an unrelated O4-T-25 conflict).
- **Execution:** Checker call (no sentinel convention; v1 structural rule only).
- **Expected outcome / assertions:**
  - The report's status is `present` (structurally non-empty).
  - It is **not** `unavailable` solely because it contains such text.
  - `verdict == "valid"`.
  - `effective_rating == original_rating`.
  - No downgrade to `REVIEW` is caused solely by the unavailable-source note.
- **Pass/fail assertion:** `status[report]=="present" and verdict=="valid" and effective_rating==original_rating and "REVIEW" not caused by the note`.
- **Type:** Offline unit (negative/boundary) — **executable**, not deferred.
- **Dependencies:** Checker module only. No approved sentinel convention is required to run this test; sentinel recognition is out of v1 scope (`Won't`).

### O4-T-05 — Unselected analysts are not_required
- **Covers:** O4-FR-06, O4-FR-11
- **Objective:** Unselected analysts are `not_required` and cannot downgrade.
- **Input/setup:** Selected `{market, news}`; sentiment/fundamentals empty; market/news non-empty.
- **Execution:** Checker call.
- **Expected outcome:** sentiment/fundamentals `not_required`; `valid`; required set `{market_report, news_report}`.
- **Pass/fail assertion:** `statuses["sentiment_report"]==statuses["fundamentals_report"]=="not_required" and verdict=="valid" and required=={"market_report","news_report"}`.
- **Type:** Offline unit (normal/boundary).
- **Dependencies:** Checker module; `ANALYST_NODE_SPECS`.

### O4-T-06 — Pre-existing REVIEW not upgraded
- **Covers:** O4-FR-05, O4-INV-02
- **Objective:** Never upgrade an existing `REVIEW`.
- **Input/setup:** All evidence present; `final_rating="REVIEW"`.
- **Execution:** Checker call.
- **Expected outcome:** effective `REVIEW`.
- **Pass/fail assertion:** `effective=="REVIEW"`.
- **Type:** Offline unit (negative/safety-critical).
- **Dependencies:** Checker module.

### O4-T-07 — Recoverable checker failure fails closed (unit + integration)
- **Covers:** O4-FR-09, O4-INV-04, O4-NFR-04
- **Objective:** A raising checker yields `REVIEW`, preserves reason, never publishes an ungated rating, across the wired path.
- **Input/setup:** Unit: checker functions monkeypatched to raise. Integration: same failure injected in the offline Graph/CLI publication path with fixtures.
- **Execution:** Checker call (unit) and wired-path run (integration), offline.
- **Expected outcome:** `effective=="REVIEW"`; `reason` non-empty; no ungated rating on any enabled surface; enabled surfaces agree.
- **Pass/fail assertion:** `effective=="REVIEW" and reason and not ungated_published and all(enabled_surfaces=="REVIEW")`.
- **Type:** Offline unit + offline integration (checker failure / safety-critical).
- **Dependencies:** Integration point (Q4) PENDING for the integration half.

### O4-T-08 — Cross-surface consistency (unit + real-path integration)
- **Covers:** O4-FR-07, O4-FR-09, O4-INV-01, O4-INV-03, O4-INV-04, O4-NFR-08
- **Objective:** All **expected enabled** output surfaces carry the same authoritative `effective_rating`, including under checker failure; disabled surfaces are not assumed enabled; an empty or partial observed set fails.
- **Input/setup:** Downgraded states (missing evidence, checker failure) driven through the real publication path. Conditional surfaces to consider (exact set from the verified publication contract and enabled options): Graph/programmatic return; CLI final display when CLI is enabled; markdown report when enabled; HTML report when `html=True`; state log; memory log when `memory_log_path` enables it.
- **Execution:** Offline integration through the real Graph/CLI entry point with LLM/network replaced by deterministic fixtures; inspect actual output artefacts and messages, not only isolated helper return values.
- **Expected enabled-surface set:** computed from the test configuration (`expected_enabled_surface_set`), reflecting the actual verified contract.
- **Pass/fail assertion (ordered):**
  1. `actual_observed_surface_set == expected_enabled_surface_set` (an empty observed set or a missing enabled surface **fails**; a vacuous universal assertion is not allowed).
  2. Every expected enabled surface contains an authoritative rating equal to `REVIEW`; `set(values) == {"REVIEW"}` alone is insufficient and must not be used as the sole check.
- **Type:** Offline integration.
- **Dependencies:** Integration point (Q4) PENDING; offline deterministic network-blocked fixtures; verified publication contract (A/C).

### O4-T-09 — Complete evidence keeps Sell
- **Covers:** O4-FR-02
- **Objective:** No spurious downgrade on a valid bearish rating.
- **Input/setup:** All evidence present; `final_rating="Sell"`.
- **Execution:** Checker call.
- **Expected outcome:** effective `Sell`.
- **Pass/fail assertion:** `effective=="Sell"`.
- **Type:** Offline unit (normal).
- **Dependencies:** Checker module.

### O4-T-10 — Original decision text preserved (unit)
- **Covers:** O4-FR-12
- **Objective:** The checker does not mutate `final_trade_decision`.
- **Input/setup:** Downgraded run with a `Buy` body.
- **Execution:** Compare checker output state to input decision (pure checker unit; no rendering).
- **Expected outcome:** effective `REVIEW`; body byte-identical.
- **Pass/fail assertion:** `effective=="REVIEW" and out_decision==in_decision`.
- **Type:** Offline unit (negative).
- **Dependencies:** Checker module.
- **Note:** The unit test proves text preservation only. The actual rendered non-authoritative label on CLI/report surfaces is verified by offline integration tests **O4-T-19** and **O4-T-23**, not by this unit test.

### O4-T-11 — Determinism (100 repetitions)
- **Covers:** O4-FR-08, O4-NFR-01
- **Objective:** Repeated identical input yields identical verdicts, no I/O.
- **Input/setup:** Same state ×100.
- **Execution:** Loop checker calls; no network/LLM.
- **Expected outcome:** 100/100 identical.
- **Pass/fail assertion:** `len(set(verdicts))==1`.
- **Type:** Offline unit (boundary).
- **Dependencies:** Checker module; no I/O.

### O4-T-12 — Structured result completeness
- **Covers:** O4-FR-10
- **Objective:** Every required key has a status; verdict enumerated; reason on non-pass.
- **Input/setup:** Any state, including a non-pass (missing-evidence or conflict) state.
- **Execution:** Inspect return value.
- **Expected outcome:** statuses cover required keys; verdict ∈ {`valid`,`review`}; `reason` set on non-pass, empty on pass.
- **Pass/fail assertion:** `required ⊆ statuses.keys() and verdict in {"valid","review"} and (verdict=="valid" or reason)`.
- **Type:** Offline unit (normal).
- **Dependencies:** Checker module; output schema.

### O4-T-13 — Single selected analyst valid
- **Covers:** O4-FR-06
- **Objective:** Single-analyst config is valid when that report is present.
- **Input/setup:** Selected `{market}` only; market present.
- **Execution:** Checker call.
- **Expected outcome:** `valid`; others `not_required`.
- **Pass/fail assertion:** `verdict=="valid" and others all "not_required"`.
- **Type:** Offline unit (boundary).
- **Dependencies:** Checker module.

### O4-T-14 — Single-analyst missing and multi-select partial (parameterized)
- **Covers:** O4-FR-03, O4-FR-06
- **Objective:** Downgrade when a selected analyst's required report is empty; no false failure for unselected analysts.
- **Input/setup:** Parameterized: (a) selected `{market}` only, `market_report=""`; (b) selected `{market, news, fundamentals}`, `news_report=""`.
- **Execution:** Checker call per parameter set.
- **Expected outcome:** `REVIEW`; exact failing set; unselected absent reports not flagged.
- **Pass/fail assertion:** `effective=="REVIEW" and set(failing)==expected_failing and unselected_not_flagged`.
- **Type:** Offline unit (negative).
- **Dependencies:** Checker module.

### O4-T-15 — Offline importability
- **Covers:** O4-NFR-02
- **Objective:** Checker imports and runs with no graph/LLM/network.
- **Input/setup:** Import test; call once with minimal state.
- **Execution:** Unit test (collection + single call), offline.
- **Expected outcome:** succeeds under network-blocking fixture.
- **Pass/fail assertion:** test passes with sockets blocked.
- **Type:** Offline unit (collection).
- **Dependencies:** Checker module; offline fixture; `test/offline/` placement (§7).

### O4-T-16 — Latency benchmark WITH vs WITHOUT gate
- **Covers:** O4-NFR-03
- **Methodology source:** `O4_T16_Performance_Verification_Plan.md`, version **v0.1 (Proposed)** (Member F). This entry summarises that plan; the attachment is the authoritative measurement methodology.
- **Objective:** Measure the incremental **offline wall time** O4 introduces into rating processing, by paired A/B measurement on a fixed runner with equivalent synthetic inputs.
- **Measurement design:**
  - Same candidate commit, fixed runner, and equivalent synthetic inputs across both paths.
  - **Path A** bypasses the O4 checker and its added result processing **within the test harness only** (test substitution); existing rating-processing logic is preserved.
  - **Path B** executes the real O4 checker and the actual integration-point result handling (including producing the structured evidence and selecting the effective rating).
  - All other rating-processing logic is identical in both paths.
  - **No production configuration toggle** is introduced; the bypass exists only in the test harness.
- **Timing boundary:** Start = entry into the actual rating-processing section; End = `effective_rating` is ready for downstream publication. **Excluded** from timing: graph execution, LLM/vendor calls, logging to disk, CLI rendering, and report writing. Use `time.perf_counter_ns()` and retain raw nanosecond values. Inputs are pre-built outside the timed window.
- **Actual Gate invocation point and timing wrapper: Pending A/C source-code call-chain confirmation.** No function name, line number, or integration point is asserted here. A pure-checker microbenchmark may be used **diagnostically** but is **not** a substitute for the real invocation-point acceptance measurement.
- **Scenarios:**
  - **Complete evidence:** four selected analysts, four non-empty synthetic reports, original rating `Buy`; B path preserves the rating, all four items `present`.
  - **Missing evidence:** the same input except the required `news_report` key is absent; B path yields `REVIEW` with failing set == {`news_report`}.
  - **Optional long-report boundary:** only if actual report sizes justify it, a fixed long-report fixture run in both complete and missing variants; verified under the same contract.
- **Sampling methodology:**
  - 100 warm-up pairs per scenario (not counted in statistics).
  - Three independent processes per scenario.
  - 1,000 paired measurements per process.
  - Alternate order A→B and B→A for adjacent samples to reduce order/cache effects.
  - `Delta = B duration − A duration`; **preserve negative values and outliers**.
  - Compute p50 and p95 using **nearest-rank** (sorted, take the `ceil(q × n)`-th item).
  - Report each measurement round independently; assert output correctness and confirm exactly one Gate execution per B run, outside the timed window.
- **Required evidence:**
  - Runner CPU, OS, Python and dependency versions (or lockfile).
  - Candidate commit SHA.
  - Fixture version and per-report lengths.
  - Exact benchmark command.
  - Raw paired A/B timings.
  - Per-scenario and per-round p50/p95/max and sample count.
  - Network-blocking verification and zero external calls.
  - Performance threshold approval evidence, when available.
- **Authoritative target (registry):** **p95 added latency `<= 10 ms`** — nearest-rank p95 on a fixed four-report fixture in the same process, after 5 warmups and 30 measured calls on `ubuntu-latest`/Python 3.11 (registry metric "Nearest-rank p95 added checker latency"). Target applies per measured scenario/round; no measurement has been executed and no passing result is claimed.
- **Acceptance rule (inclusive):** `p95(Delta) <= 10 ms` **meets** the target; `p95(Delta) > 10 ms` **does not meet** the target. This requirement is `Should` (non-mandatory): an unmet target is recorded and does not by itself block merge unless the approved CI policy explicitly makes it blocking (see §9). It never overrides safety-blocking rules.
- **Unstable-target handling:** if reproducible measurements show the 10 ms target is unstable, record the evidence for a future requirement-change review; do not change the 10 ms target independently.
- **Type:** Benchmark (Member F). Non-blocking `Should` target.
- **Dependencies:** `O4_T16_Performance_Verification_Plan.md` v0.1 (Proposed); A/C confirmation of the actual invocation point; sampling-protocol reconciliation with F (see below). Pure-checker microbenchmark results are diagnostic only.
- **Sampling protocol note (requires F's confirmation):** the registry specifies a compact protocol (5 warmups, 30 measured calls, single process, `ubuntu-latest`/Py3.11, nearest-rank p95), while F's v0.1 plan proposes an extended protocol (100 warmup pairs, 3 processes × 1,000 paired A/B samples, alternating order, per-round p50/p95). The extended protocol is a stricter superset used to establish a reproducible baseline; the **acceptance target remains `p95 <= 10 ms`** from the registry. F must confirm whether the compact registry procedure or the extended procedure is authoritative for the formal acceptance measurement. Do not silently replace either specification.

### O4-T-17 — Absent report keys (parameterized)
- **Covers:** O4-FR-03
- **Objective:** A required key absent from the mapping is `missing`.
- **Input/setup:** Parameterized over each required report key removed entirely from the state.
- **Execution:** Checker call per parameter set.
- **Expected outcome:** that key classified `missing`; exact failing set; `REVIEW`.
- **Pass/fail assertion:** `statuses[missing_key]=="missing" and set(failing)=={missing_key} and effective=="REVIEW"`.
- **Type:** Offline unit (negative).
- **Dependencies:** Checker module; `.get`-style handling.

### O4-T-18 — Unknown analyst configuration aborts publication (unit + integration)
- **Covers:** O4-FR-11, O4-FR-15
- **Objective:** Unknown key / unrecognizable configuration is a contract error that aborts publication; not silently `not_required`; not a normal `REVIEW`.
- **Input/setup:** Unit: selected includes `"options"` (unknown). Integration: same through the wired path.
- **Execution:** Call expecting exception (unit); run wired path (integration).
- **Expected outcome:** `ValueError`; authoritative publication aborted; run not presented as normal `REVIEW`.
- **Pass/fail assertion:** `pytest.raises(ValueError) and not authoritative_published and not reported_as_normal_review`.
- **Type:** Offline unit + offline integration (negative).
- **Dependencies:** `analyst_execution.py:55–56` precedent; integration point (Q4).

### O4-T-19 — Buy body not presented as approved (unit + integration)
- **Covers:** O4-FR-07, O4-FR-12, O4-FR-13, O4-INV-01
- **Objective:** Effective `REVIEW` everywhere; Buy not framed as approved; body preserved and labelled unapproved.
- **Input/setup:** Original body contains `Buy`; required evidence incomplete; real Graph/CLI path with fixtures.
- **Execution:** Unit + integration through the wired path.
- **Expected outcome:** `REVIEW` on all enabled surfaces; body unchanged and labelled unapproved; no approved Buy.
- **Pass/fail assertion:** `all(enabled_surfaces=="REVIEW") and body_unchanged and body_labeled_unapproved and not approved_buy`.
- **Type:** Offline unit + offline integration (negative/safety-critical).
- **Dependencies:** Integration point (Q4); labelling decision.

### O4-T-20 — Backward compatibility
- **Covers:** O4-NFR-05
- **Objective:** Baseline behaviour unchanged when the gate is not wired; public signatures additive only.
- **Input/setup:** Existing regression suite; signature diff of `run_rating`, `record_decision`, `store_decision`, `write_report_tree`.
- **Execution:** Run the existing suite; manual signature diff.
- **Expected outcome:** existing tests pass; additive-only signature diff.
- **Pass/fail assertion:** suite green; diff additive-only.
- **Type:** Regression (Member F) + manual signature review.
- **Dependencies:** Gate not wired into runtime for this run.

### O4-T-21 — Auditability of artefacts
- **Covers:** O4-NFR-06
- **Objective:** Runtime structured result exists; effective rating reconstructable; durability documented pending.
- **Input/setup:** Completed downgraded run; inspect state log and memory log.
- **Execution:** Artefact inspection.
- **Expected outcome:** effective rating recoverable; runtime result at capture point; durability pending.
- **Pass/fail assertion:** rating recoverable; durability status recorded pending.
- **Type:** Artefact inspection (integration).
- **Dependencies:** Q5 durability PENDING — durable half cannot pass until decided.

### O4-T-22 — Scope review
- **Covers:** O4-NFR-07, O4-FR-14
- **Objective:** Change set is one module plus approved integration points; no out-of-scope rules.
- **Input/setup:** Diff and implementation review.
- **Execution:** MANUAL review (not automated).
- **Expected outcome:** scope matches §7; no rating-logic change; no length/verification/debate rules.
- **Pass/fail assertion:** reviewer confirms scope.
- **Type:** Manual scope review.
- **Dependencies:** Human reviewer (F/C).

### O4-T-23 — CLI buffering before gate (real CLI)
- **Covers:** O4-FR-07, O4-FR-13, O4-INV-01, O4-INV-03
- **Objective:** PM Buy is buffered before the gate; after gate, effective `REVIEW`; preserved Buy non-authoritative.
- **Input/setup:** Fake CLI stream emits a PM `Buy` body before the gate sees a missing required report; exercise the real CLI entry point with fixtures (message area and report section, verifying both `cli/run.py` write paths).
- **Execution:** Offline CLI integration (LLM/network replaced by fixtures; network blocked).
- **Expected outcome:** before gate, PM message/report text buffered (not published as approved); after gate, enabled surfaces `REVIEW`; preserved body non-authoritative.
- **Pass/fail assertion:** `not pre_gate_published and post_gate=="REVIEW" and body_non_authoritative`.
- **Type:** Offline integration (negative/safety-critical).
- **Dependencies:** Integration point (Q4) PENDING.

### O4-T-24 — O5 boundary
- **Covers:** O4-FR-03, O5 boundary
- **Objective:** An upstream O5 filtered-empty status alone does not downgrade an otherwise complete valid run; a missing/empty selected `news_report` does.
- **Case A — filtered-empty does not downgrade:**
  - News Analyst is selected; every other selected analyst's required report is also non-empty; all required report fields are present and non-empty.
  - An O5 filtered-empty status exists upstream (a status, not a missing report).
  - `original_rating` is explicit (e.g. `Buy`); if the decision body contains a parseable rating, it is made to **agree** with `original_rating` to avoid an unrelated rating conflict (O4-T-25).
  - **Assert:** `verdict == "valid"` **and** `effective_rating == original_rating`.
  - **Demonstrates:** O5 filtered-empty alone does not downgrade a complete valid run.
- **Case B — missing news report downgrades:**
  - News Analyst selected; `news_report` missing or empty (two subcases: absent key and empty string); all other required evidence present; original rating explicit.
  - **Assert:** `verdict == "review"` **and** `effective_rating == "REVIEW"` **and** `exact_failing_items == {"news_report"}`.
  - **Note:** a weaker check such as "news_report is contained in the failing-item set" is **not** sufficient; the exact set must be asserted.
- **Execution:** Checker call per case.
- **Type:** Offline unit (boundary).
- **Dependencies:** Checker module; O5 status representation (§4 boundary).

### O4-T-25 — Rating precedence and conflict
- **Covers:** O4-FR-16, O4-INV-02, O4-INV-05
- **Objective:** Precedence and conflict handling.
- **Input/setup:** (a) `final_rating` and parsed body agree; (b) `final_rating` absent, body supplies rating; (c) both clear but disagree; (d) original `REVIEW`.
- **Execution:** Checker call per case.
- **Expected outcome:** (a) agree preserved; (b) body rating used; (c) `REVIEW` with conflict reason; (d) stays `REVIEW`.
- **Pass/fail assertion:** `a: effective==agreed; b: effective==body; c: effective=="REVIEW" and reason; d: effective=="REVIEW"`.
- **Type:** Offline unit (negative/safety-critical).
- **Dependencies:** Checker module; precedence rule.

---

## 5. Negative and safety-critical coverage summary

| Concern | Tests | Category |
|---|---|---|
| Missing/empty/absent evidence (all four reports) → REVIEW | O4-T-02, O4-T-03, O4-T-14, O4-T-17 | Negative (parameterized) |
| REVIEW never upgraded | O4-T-06, O4-T-25 | Safety-critical |
| Recoverable checker failure fails closed | O4-T-07, O4-T-08 | Safety-critical |
| No published Buy/Sell before gate / on downgrade | O4-T-19, O4-T-23 | Safety-critical |
| Unknown analyst configuration aborts publication | O4-T-18 | Negative |
| Rating conflict → REVIEW | O4-T-25 | Safety-critical |
| O5 filtered-empty does not force REVIEW | O4-T-24 | Boundary |
| Determinism / no I/O | O4-T-11 | Boundary |

**Mandatory safety-critical set (canonical):** defined in **Section 6.6**. This section does not maintain a separate list. The canonical set is O4-T-02, O4-T-03, O4-T-06, O4-T-07, O4-T-08, O4-T-14, O4-T-17, O4-T-18, O4-T-19, O4-T-23, O4-T-25, including all applicable mandatory parameterized subcases enumerated in Section 6.6. Sections 8 (Safety Escape Count) and 9 (Gate interaction) reference the same canonical set.

---

## 6. Test separation by category

### 6.1 Offline unit tests (deterministic, no network/LLM)
O4-T-01, T-02, T-03, T-04, T-05, T-06, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-17, T-24, T-25. (O4-T-04 is an executable v1 negative test — unavailable-source text in a non-empty report stays structurally `present`; no sentinel convention is required.)

### 6.2 Offline integration tests (real Graph/CLI publication path, fixtures, network blocked)
O4-T-07 (integration half), T-08, T-18 (integration half), T-19, T-23.

### 6.3 Regression
O4-T-20.

### 6.4 Benchmark
O4-T-16 (methodology: `O4_T16_Performance_Verification_Plan.md` v0.1, Proposed; fixed runner, paired A/B incremental offline wall time; authoritative target `p95 <= 10 ms` per registry; non-blocking `Should`).

### 6.5 Manual verification (NOT automated)
O4-T-22; signature-diff portion of O4-T-20; artefact inspection in O4-T-21.

### 6.6 Mandatory vs deferred

Each test keeps its unique ID; mandatory status is applied per **parameterized subcase**. A whole-test label is used only where no subcase is excluded.

**Canonical mandatory safety test set (single source of truth for the plan):** O4-T-02, O4-T-03, O4-T-06, O4-T-07, O4-T-08, O4-T-14, O4-T-17, O4-T-18, O4-T-19, O4-T-23, O4-T-25.

| Status | Tests / subcases |
|---|---|
| Mandatory (every subcase must execute + pass) | O4-T-02 (all four reports + multi-missing), O4-T-03 (all four whitespace variants + multi-missing), O4-T-14 (all subcases), O4-T-17 (all four absent-key subcases), O4-T-06, O4-T-07, O4-T-08, O4-T-18, O4-T-19, O4-T-23, O4-T-25 |
| Conditional (blocked on unapproved decisions) | O4-T-21 (Q5 durability); O4-T-16 (benchmark runnable, but target is non-blocking `Should` and the Gate invocation wrapper is pending A/C) |
| Standard executable (not in the mandatory safety set) | O4-T-01, O4-T-04, O4-T-05, O4-T-09, O4-T-10, O4-T-11, O4-T-12, O4-T-13, O4-T-15, O4-T-24 |
| Manual | O4-T-22 |
| Regression | O4-T-20 |

**Mandatory parameterized subcases (explicit):**
- **O4-T-02:** `market_report=""`, `sentiment_report=""`, `news_report=""`, `fundamentals_report=""`, and the two-required-reports-empty subcase.
- **O4-T-03:** `market_report` whitespace-only, `sentiment_report` whitespace-only, `news_report` whitespace-only, `fundamentals_report` whitespace-only, and the empty+whitespace multi-missing subcase.
- **O4-T-14:** single-select `{market}` with `market_report=""`; multi-select `{market, news, fundamentals}` with `news_report=""`.
- **O4-T-17:** each of the four required report keys removed entirely from the state.

**Mandatory pass rule (per node ID and per required parameterized subcase):** each must be **collected**, **actually executed**, **passed**, **not skipped**, **not xfailed**, **not errored**, and **not missing from the collection manifest**. Any violation blocks merge under the proposed Safety CI Gate.

This agrees with Section 8 (SE-01 covers every missing/empty-evidence subcase; SE-04/SE-05 cover the surfaces; **SE-06 covers O4-T-18 unknown-configuration publication**) and Section 9 (any skip/xfail/error/missing mandatory subcase blocks merge).

---

## 7. Proposed test file locations and CI discovery (UNVERIFIED until files/CI exist)

Member F has confirmed new O4 offline tests should live under `test/offline/`.

| Item | Proposal | Status |
|---|---|---|
| Unit tests | `test/offline/test_evidence_gate.py` | PROPOSED (path confirmed by F; `test/` does not exist yet) |
| Offline Graph/CLI integration tests | `test/offline/test_evidence_gate_integration.py` | PROPOSED |
| Lint | `ruff check .` | Verified in `ci.yml:66` |
| Benchmark | Member F harness per `O4_T16_Performance_Verification_Plan.md` v0.1 | NOT YET DEFINED |

### 7.1 Team unified pytest collection policy (Member A)

Member A has established the team rule for this project:

- **Deterministic offline unit tests and offline Graph/CLI tests MUST be included in the default `pytest -q` run.**
- The `integration` marker is **reserved for tests that require real external services**.
- Exercising a real Graph/CLI code path with **mocked external dependencies does not by itself require** the `integration` marker.

Consequence for O4: the offline Graph/CLI tests (O4-T-07/T-08/T-18/T-19/T-23 integration halves) are **deterministic offline tests** and must be collected and executed by the **default** `pytest -q` run. They must **not** be marked `integration`.

### 7.2 Current configuration — workspace vs PR #2 target commit

| Source | `testpaths` | Status |
|---|---|---|
| Workspace `pyproject.toml:59` | `testpaths = ["tests"]` | CONFIRMED — current workspace does **not** yet include `test/offline` |
| PR #2 target commit `f411763` `pyproject.toml:59` | `testpaths = ["tests", "test/offline"]` | CONFIRMED from PR snapshot — default collection **will include** `test/offline/` |

- `addopts = "-ra --strict-markers -m \"not integration\""` — CONFIRMED identical in workspace and PR (excludes `integration`-marked tests from the default run).
- CI runs `pytest -q` (`.github/workflows/ci.yml:36`) — CONFIRMED identical in workspace and PR; `application` unaffected.
- PR #2 adds `test/offline/conftest.py` with an `autouse` `_no_network` fixture that is **directory-scoped to `test/offline/`** (CONFIRMED from PR snapshot). It returns early only for `integration`-marked tests; because O4 offline Graph/CLI tests are **not** integration-marked under the unified policy, the fixture **is** active for them.
- `test/` does **not** exist in the current workspace; the target branch introduces it.

> **Evidence caveat:** the PR-snapshot `testpaths`/conftest facts are established from the fetched commit files (read-only). Actual collection, execution, and network isolation on CI have **not** been verified; no run has occurred for O4.

### 7.3 Required commands (documented proposals — NOT executed, NOT verified for O4)

Under the unified policy the default run is the primary evidence source; a separate integration-marker run is **not** the O4 path for offline Graph/CLI tests (they are default-collected).

1. Default collection (root): `pytest --collect-only -q`
2. Default execution (root): `pytest -q`
3. (Only if a future test genuinely needs real external services) integration-marker execution: `pytest -q -m integration` — not used by O4 offline tests.
4. Manifest comparison: compare expected mandatory node IDs (Section 6.6, incl. parameterized subcase IDs) against the node IDs actually collected and executed by Steps 1–2.

> `pytest --collect-only -q test/offline` alone does **NOT** prove default collection. Since O4 tests live in `test/offline/` and `testpaths` includes it (PR #2), they appear in the root default collection; the root `--collect-only -q` is the correct comparison source.

### 7.4 Evidence requirements (unified policy)

Retain:
- actual pytest node IDs, **including parameterized subcase IDs**;
- default collection and default execution results;
- an expected-versus-actual mandatory-test manifest;
- per-case outcomes;
- skip / xfail / error detection;
- the network-blocking guard configuration (`test/offline/conftest.py`) and proof it is active for the non-integration-marked offline tests;
- evidence that live external calls cannot escape the offline environment;
- CI job name, command, and saved result location, once implemented.

**Member F confirmation required:** confirm the target-branch root pytest configuration (`testpaths` including `test/offline`) and the CI `pytest -q` job after the O4 target branch is established.

**Never fabricate:** no collected node IDs, pytest output, or CI evidence is invented here. None exists today.

---

## 8. Safety Escape Count (SEC)

**Safety-escape categories:**
- **SE-01:** Required evidence missing/empty but a tradeable rating published.
- **SE-02:** Existing `REVIEW` incorrectly upgraded.
- **SE-03:** Recoverable checker failure releases an ungated rating.
- **SE-04:** Enabled authoritative output surfaces disagree, or endorse an ungated Buy/Sell.
- **SE-05:** CLI presents a raw final rating as an approved result before the gate completes.
- **SE-06 (PROPOSED — requires Member F confirmation):** An unknown analyst configuration or unrecognizable required configuration is detected, yet the system nevertheless publishes any authoritative rating — including a `REVIEW` rating. A recognized unknown configuration must abort publication with a reported configuration/contract error and must **not** produce a tradeable rating or a normally completed `REVIEW`. If any authoritative rating is published in this condition, the affected mandatory case (O4-T-18) counts as one safety escape.

**Counting (PROPOSED):** SEC is counted **per mandatory evaluated case**, not per number of erroneous output surfaces. A case containing one or more escapes counts as **one escaping case**; SEC = number of escaping cases among those actually executed.

**Canonical mandatory set:** Section 6.6 (O4-T-02, O4-T-03, O4-T-06, O4-T-07, O4-T-08, O4-T-14, O4-T-17, O4-T-18, O4-T-19, O4-T-23, O4-T-25, with all mandatory parameterized subcases).

**Proposed merge condition (all required):**
- Safety Escape Count == 0;
- complete mandatory **collection**;
- complete mandatory **execution**;
- all mandatory node IDs and required parameterized subcases **passed**;
- no skips, xfails, errors, or missing required parameterized subcases.

**O4-T-18 note:** a mandatory T-18 **execution failure also blocks merge** even if it does not produce a countable SE-06 escape (for example, the case errors before publication can be observed).

**Mandatory-case collection/execution evidence is required.** A zero count without complete required execution is **NOT** a pass.

**This CI policy — including SE-06 and its interpretation — is a proposal awaiting Member F confirmation and formal approval/implementation.**

---

## 9. Gate interaction (proposed)

- **Immediate mandatory safety checks:** SEC == 0 with complete execution evidence (**SE-01…SE-06**, per Section 8) against the canonical mandatory set in Section 6.6; all mandatory node IDs and required parameterized subcases collected, executed, and passed. Any escape, skip, xfail, error, or missing mandatory case/subcase blocks merge. This includes an O4-T-18 execution failure even when it yields no countable SE-06 escape.
- **Regression:** O4-T-20 failure blocks merge.
- **Performance (non-blocking `Should`):** methodology is `O4_T16_Performance_Verification_Plan.md` v0.1; authoritative target `p95 <= 10 ms` (registry). `p95 <= 10 ms` meets the target; `p95 > 10 ms` does not. Because O4-NFR-03 is `Should`, an unmet target is **recorded and reported** but does **not** automatically block merge; it only blocks if the approved CI policy explicitly makes it blocking. Failure to meet a performance target never overrides Safety Escape Count or any mandatory safety rule. No measurement has been executed; no passing result is claimed.
- **Manual findings** (O4-T-22) recorded as a review outcome, not an automated pass.

Immediate mandatory safety checks are separate from the confirmed-target performance check and other pending activities. No gate in this section is implemented or configured in CI yet. Outstanding items are: F's sampling-protocol reconciliation (compact registry procedure vs F's extended A/B plan) and A/C confirmation of the actual Gate invocation point and timing wrapper; until those are settled, no acceptance benchmark is run and the 10 ms target remains the confirmed requirement value, not a measured result.

---

## 10. Pending decisions and approval dependencies

| Topic | Requirement | PENDING — decision owner |
|---|---|---|
| Integration location / shared-file scope (Decisions A–D give direction only) | O4-FR-07/09/13/15, O4-T-07/08/18/19/23 | A + C (Q4) |
| Performance sampling protocol for O4-NFR-03 | O4-NFR-03, O4-T-16 | Target adopted from registry (`p95 <= 10 ms`, 5 warmups/30 calls, ubuntu-latest/Py3.11). F confirms whether the compact registry procedure or F's extended A/B procedure is authoritative for acceptance (`O4_T16_Performance_Verification_Plan.md` v0.1) |
| Actual Gate invocation point and timing wrapper for T-16 | O4-T-16 | A + C (source-code call-chain confirmation) |
| Test discovery / CI default collection (unified policy) | All O4 offline tests | F (confirm target-branch `testpaths = ["tests", "test/offline"]` and `pytest -q` job on the target branch) |
| Reviewer eligibility / approval evidence | Test Approval Gate | A + B |
| Whole-report unavailable sentinel | O4-FR-04, O4-T-04 | **Resolved for v1:** FR-04 is `Won't`; sentinel recognition not implemented. T-04 is an executable negative test (no Q3 blocker). Any future sentinel remains a separate requirement-change review (C + D + B). |
| Durable verdict persistence | O4-NFR-06, O4-T-21 | A + C (Q5 in requirements §9) |
| Invariant representation in Schema 1.0.0 | O4-INV-01…05 | B (requirements §9 Q8) |
| SE-06 interpretation and its CI enforcement | O4-T-18, Section 8 | F (confirm) + team (approve) |
| Network-blocking guard for O4 offline tests | O4-T-15, O4-T-07/08/18/19/23 offline halves | F (PR #2 adds `test/offline/conftest.py` `_no_network`, directory-scoped; active for non-integration-marked tests — confirm on target branch) |

**Resolved by A/C architecture direction** (no longer open as policy; still not formal requirements approval): CLI buffering for v1; recoverable checker-failure fail-closed; unknown-analyst configuration abort; rating precedence and conflict-to-`REVIEW`.

---

## 11. Human approval record

> Empty until a human reviewer records approval. Do not pre-fill. A code change may begin only after this record is completed, and implementation start must not precede approval timestamp.

| Field | Value |
|---|---|
| Approver identity and role | |
| Approval timestamp (with timezone) | |
| Exact approved test-plan version | |
| Exact approved requirements revision | |
| Approved test scope | |
| Original full approval message and timestamp, or reliable reference | |
| Actual implementation start timestamp | |
| PR / review / CI evidence (later) | |

**Proposed approver:** Member F (subject to the team's final approval-authority confirmation). **Members A/C** confirm architecture and integration decisions; **Member B** checks registry and test traceability. The current A/C replies confirm architecture direction only and do **not** constitute pre-coding test-plan approval. Any substantial subsequent change to safety policy, acceptance criteria, or mandatory test scope requires re-versioning and re-approval of the affected scope.

---

## 12. Review status

Status: Draft
Owner: Member D
Reviewer: Pending
Review date: Pending
Approval evidence: Not yet available
Plan version: O4-TEST-v0.3
Authoritative requirements baseline: docs/req/requirements.yaml @ main 4f87e29f7a52842dba8272071d2a4a1b527def10 (PR #2 merged)
Superseded draft reference: O4-requirements.md O4-REQ-r3 (working draft, not the approved baseline)
