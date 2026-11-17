# O4 — Pre-Implementation Test Plan

| Field | Value |
|---|---|
| Plan ID | O4-TEST-v0.4 |
| Status | Draft / Approval Pending |
| Owner | Member D (Safety and Reliability Lead) |
| Prepared for | Member F (test coordination, CI integration, verification) |
| Approval | Pending — Member F has **NOT** formally approved this version |
| Approval history | Member A (PR #7, commit `60f1496…`) approved **only the O4-EXEC-v0.1 Stage 1 execution scope**; Member A did **not** approve this revised test plan as a whole. Member F test-plan approval is **pending**. Shared Stage 2 integration is **unapproved**. |
| **Authoritative requirements baseline** | `docs/req/requirements.yaml` — Caicys297/TradingAgents-CS5351, PR #2 merged into `main`; current `main` commit **`5afb24cf1b48e15e5000ee1365826eebb30d01ae`**; PR #2 merge commit `4f87e29f7a52842dba8272071d2a4a1b527def10` |
| O4 Draft PR | PR #7 (`feature/o4-evidence-gate`, base `main` @ `5afb24cf…`) — Member A reviewed; Member F test-plan approval pending |
| **CI provenance** | Unified pytest collection + `test/offline/` network-blocking fixture originate from **CI PR #1** (`pyproject.toml`, `test/offline/conftest.py`), NOT PR #2 |
| Superseded draft reference | `O4-requirements.md` (workspace draft revision **O4-REQ-r3**) — a working draft, NOT the approved baseline |
| Source CI plan | `F_CI_Gate_Plan_for_Team_Review_Revised.md` |
| Performance methodology (T-16) | `O4_T16_Performance_Verification_Plan.md`, v0.1 (Proposed) — supplementary diagnostics only |
| Registry | Requirements Registry / Schema 1.0.0 (Member B confirmed; O4 IDs preserved) |
| Supersedes | O4-TEST-v0.3, O4-TEST-v0.2, O4-TEST-v0.1 |

> **Status of this document.** This is a *pre-implementation* test plan. No test in this plan has been written, executed, or approved. The O4 checker module (`tradingagents/agents/evidence_gate.py`) and the O4 test files do **not** exist in the workspace. Every test ID below is a **proposed identifier**, not a passing test. No approval, benchmark measurement, or result is fabricated here.
>
> **Two-stage scope (Member A, PR #7).** Member A has approved **only** Member D's **Stage 1** scope: the pure Evidence Gate checker and its deterministic offline unit tests. **Stage 2** — shared Graph/CLI/reporting/state/persistence integration — is coordinated by Member C and requires separate A/C approval. Partial Stage 1 safety coverage is **NOT** complete O4 safety approval. See §2.4.
>
> **Confirmed performance target.** O4-NFR-03 (`Should`) has a confirmed registry target: nearest-rank **p95 added latency <= 10 ms** (fixed four-report fixture, 5 warmups, 30 measured calls, `ubuntu-latest`/Python 3.11). Formal acceptance uses the registry procedure; F's paired A/B plan is supplementary diagnostics only. No benchmark has been executed; no passing result is claimed.

---

## 1. Document metadata and conventions

- **Plan ID:** O4-TEST-v0.4 (versioned; increments on each reviewed revision). Prior reviewed version was O4-TEST-v0.3; this revision changes reviewed scope and acceptance details, so earlier approvals do **not** automatically cover it.
- **Owner:** Member D.
- **Status:** Draft.
- **Approval:** Pending. Approval record completed in Section 11 only by the authorised reviewer(s).
- **Authoritative requirements baseline:** `docs/req/requirements.yaml` at `main` `5afb24cf1b48e15e5000ee1365826eebb30d01ae` (PR #2 merged at `4f87e29f…`). FR-04 = `Won't`; NFR-03 = `Should`, p95 `<= 10 ms`; INV-05 maps to O4-T-25.
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
- Durable persistence of the complete structured Gate verdict — **not required for O4 v1** (Member A decision). Enabled authoritative rating outputs must still remain consistent (O4-NFR-06 runtime + consistency contract, see §3.2 and T-21).
- O1 single-SMA insufficient-history text alone triggering `REVIEW`.
- O5 filtered-empty news alone automatically implying O4 `REVIEW`.

### 2.3 O4/O5 boundary
- O4 checks report **presence and non-emptiness**, not factual content.
- An **O5 filtered-empty** result alone does **not** force O4 `REVIEW` (used when no usable items remain after O5's own filtering, not a missing report).
- If News Analyst is selected and `news_report` is absent/empty, O4 **MUST** downgrade to `REVIEW`.
- A single insufficient-history SMA from O1 does not imply the whole market report is missing.

### 2.4 Two-stage implementation scope (Member A, PR #7)

**Stage 1 — approved for Member D's own files (pure checker + offline unit tests):**
- Files D may create/modify: `tradingagents/agents/evidence_gate.py`, `test/offline/test_evidence_gate.py`.
- Stage 1 test IDs: **O4-T-01…T-07, T-09…T-15, T-17…T-19, T-24, T-25**.
- For **O4-T-07, T-18, T-19**, Stage 1 covers **only their unit-test portions**; their integration portions are Stage 2.
- Stage 1 **must NOT** modify shared Graph, CLI, reporting, logging, state, or runtime integration files.
- Stage 1 approved-in-scope tests are **NOT yet implemented** and **NOT** a complete O4 safety approval.

**Stage 2 — shared integration (Member C coordinates; separate A/C approval):**
- Files: `tradingagents/graph/trading_graph.py`, `tradingagents/agents/state.py`, `cli/run.py`, `tradingagents/reporting.py`, `tradingagents/report_html.py`, `tradingagents/memory/log.py` (as approved).
- Integration portions of T-07, T-18, T-19; plus **T-08, T-16, T-20, T-21, T-23** and the cross-surface parts of T-02/T-06/T-14/T-17/T-25.
- **Adopted integration policy (Member A, PR #7):** **G1** — the same Gate is invoked on both the Graph completion path and the CLI path before `record_decision` / external publication; **B1** — CLI buffers PM text and only displays it after the Gate. (Exact insertion points/line scope still confirmed by A/C in Stage 2.)

**Full O4 safety CI obligation:** the canonical mandatory set (§6.6) plus all parameterized subcases must eventually be collected, executed, and passed before **final O4 merge**. Partial Stage 1 coverage does not discharge this obligation.

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
| O4-FR-10 | Must | O4-T-12 | Unit | — |
| O4-FR-11 | Must | O4-T-05, O4-T-18 | Unit + Integration (unit in Stage 1) | Integration portion Stage 2 (Q4) |
| O4-FR-12 | Must | O4-T-10, O4-T-19 | Unit | — |
| O4-FR-13 | Must | O4-T-10, O4-T-19, O4-T-23 | Unit + Integration | Integration point (Q4) PENDING |
| O4-FR-14 | Won't (v1) | O4-T-22 | Manual | — |
| O4-FR-15 | Must | O4-T-18 | Unit + Integration | Integration point (Q4) PENDING |
| O4-FR-16 | Must | O4-T-25 | Unit | — |

### 3.2 Non-functional Requirements

| Requirement | Priority (registry) | Test IDs | Test type | Pending dependency |
|---|---|---|---|---|
| O4-NFR-01 | Must | O4-T-11 | Unit | — |
| O4-NFR-02 | Must | O4-T-15 | Unit (collection) | — |
| O4-NFR-03 | Should | O4-T-16 | Benchmark | p95 `<= 10 ms` (fixed four-report fixture, 5 warmups, 30 measured calls, ubuntu-latest/Py3.11); non-blocking Should — see §9 |
| O4-NFR-04 | Must | O4-T-07 | Unit + dependency review | — |
| O4-NFR-05 | Should | O4-T-20 | Regression + signature review | Stage 2 (integration) |
| O4-NFR-06 | Should | O4-T-08, O4-T-21 | Integration + artefact inspection | Stage 2; full-verdict durability **not required in v1**; enabled-rating consistency required |
| O4-NFR-07 | Should | O4-T-22 | Manual | — |
| O4-NFR-08 | Must | O4-T-08 | Integration | Stage 2 |

### 3.3 Safety invariants

| Invariant | Test IDs | Test type | Pending dependency |
|---|---|---|---|
| O4-INV-01 | O4-T-02, O4-T-08, O4-T-19, O4-T-23 | Unit + Integration | Q4 for integration cases |
| O4-INV-02 | O4-T-06, O4-T-25 | Unit | — |
| O4-INV-03 | O4-T-08, O4-T-23 | Integration | Q4 |
| O4-INV-04 | O4-T-07, O4-T-08 | Unit + Integration | Q4 |
| O4-INV-05 | O4-T-25 | Unit | — (registry verified: `verification: ["O4-T-25"]` at `main` `5afb24cf…`; earlier apparent mismatch resolved) |

---

## 4. Test case catalogue (O4-T-01 … O4-T-25)

Each entry gives objective, input/setup, execution approach, expected outcome, pass/fail assertion, test type, and dependencies. All are **PROPOSED / NOT YET IMPLEMENTED**. Parameterized tests retain their original identity while expanding across the four report fields.

**Stage tags** (per §2.4): **[S1]** = Stage 1, D-owned pure checker + offline unit (approved in scope by Member A, not yet implemented). **[S2]** = Stage 2, shared integration (Member C, separate A/C approval). **[S1/S2]** = Stage 1 unit portion plus a Stage 2 integration portion. The tag appears in each entry's **Type** line.

### O4-T-01 — Complete evidence preserves rating
- **Covers:** O4-FR-01, O4-FR-02
- **Objective:** A complete, valid state yields `valid` and preserves the original rating.
- **Input/setup:** Plain `dict` state; all four reports non-empty; `final_rating="Overweight"`; all four selected.
- **Execution:** Call the checker directly (offline).
- **Expected outcome:** `verdict="valid"`; `effective_rating="Overweight"`.
- **Pass/fail assertion:** `result.verdict == "valid" and result.effective_rating == "Overweight"`.
- **Type:** Offline unit. **[S1]**
- **Dependencies:** Checker module exists.

### O4-T-02 — Single empty required report forces REVIEW (parameterized)
- **Covers:** O4-FR-03, O4-INV-01
- **Objective:** Any one empty required report downgrades to `REVIEW` and is named.
- **Input/setup:** Parameterized over `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`: set the chosen report to `""`, other required reports non-empty, `final_rating="Buy"`, all four selected. Plus a multi-missing case (two required reports empty simultaneously).
- **Execution:** Checker call per parameter set.
- **Expected outcome:** `verdict="review"`; failing set == exactly the empty report(s); effective `REVIEW`.
- **Pass/fail assertion:** `verdict=="review" and set(failing)==expected_failing and effective=="REVIEW"`.
- **Type:** Offline unit (negative/safety-critical). **[S1]**
- **Dependencies:** Checker module.

### O4-T-03 — Whitespace-only, whitespace variants, multi-missing (parameterized)
- **Covers:** O4-FR-03
- **Objective:** Whitespace-only counts as empty; multiple missing reports all reported.
- **Input/setup:** Parameterized: each required report whitespace-only (`"   \n\t "`); plus a multi-missing case combining an empty and a whitespace-only report.
- **Execution:** Checker call per parameter set.
- **Expected outcome:** each whitespace-only report classified `missing`; exact failing set; downgrade.
- **Pass/fail assertion:** `set(failing)==expected_failing and verdict=="review"`.
- **Type:** Offline unit (boundary). **[S1]**
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
- **Type:** Offline unit (negative/boundary) — **executable**, not deferred. **[S1]**
- **Dependencies:** Checker module only. No approved sentinel convention is required to run this test; sentinel recognition is out of v1 scope (`Won't`).

### O4-T-05 — Unselected analysts are not_required
- **Covers:** O4-FR-06, O4-FR-11
- **Objective:** Unselected analysts are `not_required` and cannot downgrade.
- **Input/setup:** Selected `{market, news}`; sentiment/fundamentals empty; market/news non-empty.
- **Execution:** Checker call.
- **Expected outcome:** sentiment/fundamentals `not_required`; `valid`; required set `{market_report, news_report}`.
- **Pass/fail assertion:** `statuses["sentiment_report"]==statuses["fundamentals_report"]=="not_required" and verdict=="valid" and required=={"market_report","news_report"}`.
- **Type:** Offline unit (normal/boundary). **[S1]**
- **Dependencies:** Checker module; `ANALYST_NODE_SPECS`.

### O4-T-06 — Pre-existing REVIEW not upgraded
- **Covers:** O4-FR-05, O4-INV-02
- **Objective:** Never upgrade an existing `REVIEW`.
- **Input/setup:** All evidence present; `final_rating="REVIEW"`.
- **Execution:** Checker call.
- **Expected outcome:** effective `REVIEW`.
- **Pass/fail assertion:** `effective=="REVIEW"`.
- **Type:** Offline unit (negative/safety-critical). **[S1]**
- **Dependencies:** Checker module.

### O4-T-07 — Recoverable checker failure fails closed (Stage 1 unit / Stage 2 integration)
- **Covers:** O4-FR-09, O4-INV-04, O4-NFR-04
- **Objective:** A recoverable checker failure yields `REVIEW` with a diagnostic reason and never publishes an ungated rating.
- **Stage 1 (offline unit / pure module):**
  - **Input/setup:** A pure-checker input that triggers an internal (recoverable) failure, or a test-local wrapper around the pure checker that converts an exception into a fail-closed result.
  - **Expected outcome:** the pure module (or its approved thin wrapper) produces `verdict="review"`, `effective_rating="REVIEW"`, and a non-empty `reason`.
  - **Pass/fail assertion:** `verdict=="review" and effective=="REVIEW" and reason`.
  - **Interface ambiguity (flagged, not assumed solved):** the current proposed pure-checker interface (`check_evidence → GateResult`) does not by itself define exception handling. If a failing internal exception cannot be observed at the pure-module boundary without a wrapper, this must be **resolved by A/C in Stage 2**; Stage 1 must not claim the shared fail-closed wiring is verified, and must not introduce a shared-integration dependency.
- **Stage 2 (Graph/CLI integration):**
  - **Input/setup:** the same recoverable failure injected in the offline Graph/CLI publication path with fixtures.
  - **Expected outcome:** no ungated rating published; all enabled surfaces show `REVIEW`, `reason` preserved, publication safety held.
  - **Pass/fail assertion:** `effective=="REVIEW" and reason and not ungated_published and all(enabled_surfaces=="REVIEW")`.
- **Type:** Stage 1 offline unit **[S1]**; Stage 2 offline integration **[S2]** (checker failure / safety-critical).
- **Dependencies:** Stage 2 half depends on the integration point (Q4) and A/C confirmation.

### O4-T-08 — Cross-surface consistency (unit + real-path integration)
- **Covers:** O4-FR-07, O4-FR-09, O4-INV-01, O4-INV-03, O4-INV-04, O4-NFR-08
- **Objective:** All **expected enabled** output surfaces carry the same authoritative `effective_rating`, including under checker failure; disabled surfaces are not assumed enabled; an empty or partial observed set fails.
- **Input/setup:** Downgraded states (missing evidence, checker failure) driven through the real publication path. Conditional surfaces to consider (exact set from the verified publication contract and enabled options): Graph/programmatic return; CLI final display when CLI is enabled; markdown report when enabled; HTML report when `html=True`; state log; memory log when `memory_log_path` enables it.
- **Execution:** Offline integration through the real Graph/CLI entry point with LLM/network replaced by deterministic fixtures; inspect actual output artefacts and messages, not only isolated helper return values.
- **Expected enabled-surface set:** computed from the test configuration (`expected_enabled_surface_set`), reflecting the actual verified contract.
- **Pass/fail assertion (ordered):**
  1. `actual_observed_surface_set == expected_enabled_surface_set` (an empty observed set or a missing enabled surface **fails**; a vacuous universal assertion is not allowed).
  2. Every expected enabled surface contains an authoritative rating equal to `REVIEW`; `set(values) == {"REVIEW"}` alone is insufficient and must not be used as the sole check.
- **Type:** Offline integration. **[S2]**
- **Dependencies:** Integration point (Q4) PENDING; offline deterministic network-blocked fixtures; verified publication contract (A/C).

### O4-T-09 — Complete evidence keeps Sell
- **Covers:** O4-FR-02
- **Objective:** No spurious downgrade on a valid bearish rating.
- **Input/setup:** All evidence present; `final_rating="Sell"`.
- **Execution:** Checker call.
- **Expected outcome:** effective `Sell`.
- **Pass/fail assertion:** `effective=="Sell"`.
- **Type:** Offline unit (normal). **[S1]**
- **Dependencies:** Checker module.

### O4-T-10 — Original decision text preserved (unit)
- **Covers:** O4-FR-12
- **Objective:** The checker does not mutate `final_trade_decision`.
- **Input/setup:** Downgraded run with a `Buy` body.
- **Execution:** Compare checker output state to input decision (pure checker unit; no rendering).
- **Expected outcome:** effective `REVIEW`; body byte-identical.
- **Pass/fail assertion:** `effective=="REVIEW" and out_decision==in_decision`.
- **Type:** Offline unit (negative). **[S1]**
- **Dependencies:** Checker module.
- **Note:** The unit test proves text preservation only. The actual rendered non-authoritative label on CLI/report surfaces is verified by offline integration tests **O4-T-19** and **O4-T-23**, not by this unit test.

### O4-T-11 — Determinism (100 repetitions)
- **Covers:** O4-FR-08, O4-NFR-01
- **Objective:** Repeated identical input yields identical verdicts, no I/O.
- **Input/setup:** Same state ×100.
- **Execution:** Loop checker calls; no network/LLM.
- **Expected outcome:** 100/100 identical.
- **Pass/fail assertion:** `len(set(verdicts))==1`.
- **Type:** Offline unit (boundary). **[S1]**
- **Dependencies:** Checker module; no I/O.

### O4-T-12 — Structured result completeness
- **Covers:** O4-FR-10
- **Objective:** Every required key has a status; verdict enumerated; reason on non-pass.
- **Input/setup:** Any state, including a non-pass (missing-evidence or conflict) state.
- **Execution:** Inspect return value.
- **Expected outcome:** statuses cover required keys; verdict ∈ {`valid`,`review`}; `reason` set on non-pass, empty on pass.
- **Pass/fail assertion:** `required ⊆ statuses.keys() and verdict in {"valid","review"} and (verdict=="valid" or reason)`.
- **Type:** Offline unit (normal). **[S1]**
- **Dependencies:** Checker module; output schema.

### O4-T-13 — Single selected analyst valid
- **Covers:** O4-FR-06
- **Objective:** Single-analyst config is valid when that report is present.
- **Input/setup:** Selected `{market}` only; market present.
- **Execution:** Checker call.
- **Expected outcome:** `valid`; others `not_required`.
- **Pass/fail assertion:** `verdict=="valid" and others all "not_required"`.
- **Type:** Offline unit (boundary). **[S1]**
- **Dependencies:** Checker module.

### O4-T-14 — Single-analyst missing and multi-select partial (parameterized)
- **Covers:** O4-FR-03, O4-FR-06
- **Objective:** Downgrade when a selected analyst's required report is empty; no false failure for unselected analysts.
- **Input/setup:** Parameterized: (a) selected `{market}` only, `market_report=""`; (b) selected `{market, news, fundamentals}`, `news_report=""`.
- **Execution:** Checker call per parameter set.
- **Expected outcome:** `REVIEW`; exact failing set; unselected absent reports not flagged.
- **Pass/fail assertion:** `effective=="REVIEW" and set(failing)==expected_failing and unselected_not_flagged`.
- **Type:** Offline unit (negative). **[S1]**
- **Dependencies:** Checker module.

### O4-T-15 — Offline importability
- **Covers:** O4-NFR-02
- **Objective:** Checker imports and runs with no graph/LLM/network.
- **Input/setup:** Import test; call once with minimal state.
- **Execution:** Unit test (collection + single call), offline.
- **Expected outcome:** succeeds under network-blocking fixture.
- **Pass/fail assertion:** test passes with sockets blocked.
- **Type:** Offline unit (collection). **[S1]**
- **Dependencies:** Checker module; offline fixture; `test/offline/` placement (§7).

### O4-T-16 — Latency benchmark WITH vs WITHOUT gate
- **Covers:** O4-NFR-03
- **Formal acceptance source:** the Requirements Registry procedure (ubuntu-latest / Python 3.11, fixed four-report fixture, 5 warm-up calls, 30 measured calls, nearest-rank p95 added latency <= 10 ms inclusive; priority `Should`). `O4_T16_Performance_Verification_Plan.md` v0.1 (Proposed, Member F) is **supplementary diagnostic methodology only** — it may investigate stability but does not replace the Registry acceptance procedure.
- **Objective:** Measure the incremental **offline wall time** O4 introduces into rating processing. Formal acceptance uses the Registry procedure; F's paired A/B design is used as supplementary diagnostics.
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
- **Type:** Benchmark (Member F). Non-blocking `Should` target. **[S2]**
- **Dependencies:** `O4_T16_Performance_Verification_Plan.md` v0.1 (Proposed); A/C confirmation of the actual invocation point; sampling-protocol reconciliation with F (see below). Pure-checker microbenchmark results are diagnostic only.
- **Formal acceptance vs. supplemental diagnostics (resolved):** the **registry procedure is the formal acceptance** — fixed four-report fixture, 5 warm-up calls, 30 measured calls, single process, `ubuntu-latest`/Python 3.11, nearest-rank p95 added latency `<= 10 ms` (inclusive). Member F's extended paired A/B protocol (100 warm-up pairs, 3 processes × 1,000 paired samples, alternating order, per-round p50/p95) is retained **only as supplementary diagnostic measurement** to characterize stability; it does **not** replace the registry acceptance procedure. The real Gate invocation point and timing boundaries remain pending A/C in Stage 2.

### O4-T-17 — Absent report keys (parameterized)
- **Covers:** O4-FR-03
- **Objective:** A required key absent from the mapping is `missing`.
- **Input/setup:** Parameterized over each required report key removed entirely from the state.
- **Execution:** Checker call per parameter set.
- **Expected outcome:** that key classified `missing`; exact failing set; `REVIEW`.
- **Pass/fail assertion:** `statuses[missing_key]=="missing" and set(failing)=={missing_key} and effective=="REVIEW"`.
- **Type:** Offline unit (negative). **[S1]**
- **Dependencies:** Checker module; `.get`-style handling.

### O4-T-18 — Unknown analyst configuration aborts publication (Stage 1 unit / Stage 2 integration)
- **Covers:** O4-FR-11, O4-FR-15
- **Objective:** An unknown analyst key / unrecognizable configuration is a contract error that aborts publication; it is never silently `not_required` and never a normal `REVIEW`.
- **Stage 1 (offline unit / pure module):**
  - **Input/setup:** `selected_analysts` includes an unknown key (e.g. `"options"`).
  - **Expected outcome:** raises the required `ValueError` (or documented contract error); never returns a normal `GateResult` with the unknown analyst classified `not_required`.
  - **Pass/fail assertion:** `pytest.raises(ValueError)` and no normal result is produced.
- **Stage 2 (Graph/CLI integration):**
  - **Input/setup:** the same unknown configuration through the wired publication path.
  - **Expected outcome:** authoritative publication is aborted; the run is not reported as a normal `REVIEW`.
  - **Pass/fail assertion:** `not authoritative_published and not reported_as_normal_review`.
- **Type:** Stage 1 offline unit **[S1]**; Stage 2 offline integration **[S2]** (negative).
- **Dependencies:** `analyst_execution.py:55–56` precedent; integration point (Q4) for Stage 2.

### O4-T-19 — Buy body not presented as approved (Stage 1 unit / Stage 2 integration)
- **Covers:** O4-FR-07, O4-FR-12, O4-FR-13, O4-INV-01
- **Objective:** Missing evidence yields effective `REVIEW`; the original decision body is preserved; on enabled surfaces the Buy is never presented as approved.
- **Stage 1 (offline unit / pure module):**
  - **Input/setup:** original body contains `Buy`; a required report is missing/empty.
  - **Expected outcome:** `effective=="REVIEW"`; the original decision body is unchanged (byte-identical).
  - **Pass/fail assertion:** `effective=="REVIEW" and body_unchanged`.
  - **Note:** Stage 1 does not observe Graph/CLI rendering; it must not pretend to.
- **Stage 2 (Graph/CLI integration):**
  - **Input/setup:** the same state through the real Graph/CLI path with fixtures.
  - **Expected outcome:** post-Gate CLI/report rendering shows `REVIEW`; any preserved Buy body is labelled unapproved original content; no approved Buy/Sell publication.
  - **Pass/fail assertion:** `all(enabled_surfaces=="REVIEW") and body_labeled_unapproved and not approved_buy`.
- **Type:** Stage 1 offline unit **[S1]**; Stage 2 offline integration **[S2]** (negative/safety-critical).
- **Dependencies:** integration point (Q4) and labelling decision for Stage 2.

### O4-T-20 — Backward compatibility
- **Covers:** O4-NFR-05
- **Objective:** Baseline behaviour unchanged when the gate is not wired; public signatures additive only.
- **Input/setup:** Existing regression suite; signature diff of `run_rating`, `record_decision`, `store_decision`, `write_report_tree`.
- **Execution:** Run the existing suite; manual signature diff.
- **Expected outcome:** existing tests pass; additive-only signature diff.
- **Pass/fail assertion:** suite green; diff additive-only.
- **Type:** Regression (Member F) + manual signature review. **[S2]**
- **Dependencies:** Gate not wired into runtime for this run.

### O4-T-21 — Auditability of artefacts (runtime/audit + enabled-rating consistency)
- **Covers:** O4-NFR-06
- **Objective:** Verify the approved v1 contract: the Gate returns a structured runtime result (verdict, effective rating, per-item statuses, diagnostic reason) and every enabled authoritative rating output remains consistent with the effective rating. Full structured-verdict **durable persistence is NOT required in v1** (Member A decision).
- **Input/setup:** A completed downgraded run; inspect state log and memory log and the return/heir surfaces.
- **Execution:** Artefact inspection (Stage 2, requires shared integration).
- **Expected outcome:** the effective rating is recoverable from the enabled authoritative outputs; the runtime structured result is available at the Gate's capture point; enabled rating outputs agree.
- **Pass/fail assertion:** `effective_rating recoverable from enabled artefacts` **and** `all enabled authoritative rating outputs == effective_rating`.
- **Type:** Artefact inspection (integration). **[S2]** — Stage 2 because actual runtime artefact verification requires shared integration.
- **Dependencies:** Stage 2 shared integration. **Not** conditional on full-verdict durability (which v1 does not require).

### O4-T-22 — Scope review
- **Covers:** O4-NFR-07, O4-FR-14
- **Objective:** Change set is one module plus approved integration points; no out-of-scope rules.
- **Input/setup:** Diff and implementation review.
- **Execution:** MANUAL review (not automated).
- **Expected outcome:** scope matches §7; no rating-logic change; no length/verification/debate rules.
- **Pass/fail assertion:** reviewer confirms scope.
- **Type:** Manual scope review. **[S2]/manual**
- **Dependencies:** Human reviewer (F/C).

### O4-T-23 — CLI buffering before gate (real CLI)
- **Covers:** O4-FR-07, O4-FR-13, O4-INV-01, O4-INV-03
- **Objective:** PM Buy is buffered before the gate; after gate, effective `REVIEW`; preserved Buy non-authoritative.
- **Input/setup:** Fake CLI stream emits a PM `Buy` body before the gate sees a missing required report; exercise the real CLI entry point with fixtures (message area and report section, verifying both `cli/run.py` write paths).
- **Execution:** Offline CLI integration (LLM/network replaced by fixtures; network blocked).
- **Expected outcome:** before gate, PM message/report text buffered (not published as approved); after gate, enabled surfaces `REVIEW`; preserved body non-authoritative.
- **Pass/fail assertion:** `not pre_gate_published and post_gate=="REVIEW" and body_non_authoritative`.
- **Type:** Offline integration (negative/safety-critical). **[S2]**
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
- **Type:** Offline unit (boundary). **[S1]**
- **Dependencies:** Checker module; O5 status representation (§4 boundary).

### O4-T-25 — Rating precedence and conflict
- **Covers:** O4-FR-16, O4-INV-02, O4-INV-05
- **Objective:** Precedence and conflict handling.
- **Input/setup:** (a) `final_rating` and parsed body agree; (b) `final_rating` absent, body supplies rating; (c) both clear but disagree; (d) original `REVIEW`.
- **Execution:** Checker call per case.
- **Expected outcome:** (a) agree preserved; (b) body rating used; (c) `REVIEW` with conflict reason; (d) stays `REVIEW`.
- **Pass/fail assertion:** `a: effective==agreed; b: effective==body; c: effective=="REVIEW" and reason; d: effective=="REVIEW"`.
- **Type:** Offline unit (negative/safety-critical). **[S1]**
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

### 6.1 Offline unit tests (deterministic, no network/LLM) — Stage 1 scope
O4-T-01, T-02, T-03, T-04, T-05, T-06, **T-07 (unit portion)**, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-17, **T-18 (unit portion)**, **T-19 (unit portion)**, T-24, T-25. (O4-T-04 is an executable v1 negative test — unavailable-source text in a non-empty report stays structurally `present`; no sentinel convention is required. The unit portions of T-07/T-18/T-19 are pure-module tests and do not observe Graph/CLI behaviour.)

### 6.2 Offline integration tests (real Graph/CLI publication path, fixtures, network blocked) — Stage 2 scope
**T-07 (integration portion)**, T-08, **T-18 (integration portion)**, **T-19 (integration portion)**, T-23. Only the integration portions of the mixed-stage tests appear here.

### 6.3 Regression
O4-T-20.

### 6.4 Benchmark
O4-T-16 (formal acceptance = registry procedure: fixed four-report fixture, 5 warmups, 30 measured calls, `ubuntu-latest`/Py3.11, nearest-rank p95 `<= 10 ms` inclusive, non-blocking `Should`; `O4_T16_Performance_Verification_Plan.md` v0.1 paired A/B is supplementary diagnostics only).

### 6.5 Manual verification (NOT automated)
O4-T-22; signature-diff portion of O4-T-20; artefact inspection in O4-T-21.

### 6.6 Mandatory vs deferred

Each test keeps its unique ID; mandatory status is applied per **parameterized subcase**. A whole-test label is used only where no subcase is excluded.

**Canonical mandatory safety test set (single source of truth for the plan):** O4-T-02, O4-T-03, O4-T-06, O4-T-07, O4-T-08, O4-T-14, O4-T-17, O4-T-18, O4-T-19, O4-T-23, O4-T-25.

| Status | Tests / subcases |
|---|---|
| Mandatory (every subcase must execute + pass) | O4-T-02 (all four reports + multi-missing), O4-T-03 (all four whitespace variants + multi-missing), O4-T-14 (all subcases), O4-T-17 (all four absent-key subcases), O4-T-06, O4-T-07, O4-T-08, O4-T-18, O4-T-19, O4-T-23, O4-T-25 |
| Conditional (blocked on unapproved decisions) | O4-T-21 (Stage 2 shared integration — not blocked on durability, which v1 does not require); O4-T-16 (benchmark runnable, but target is non-blocking `Should` and the Gate invocation wrapper is pending A/C) |
| Standard executable (not in the mandatory safety set) | O4-T-01, O4-T-04, O4-T-05, O4-T-09, O4-T-10, O4-T-11, O4-T-12, O4-T-13, O4-T-15, O4-T-24 |
| Manual | O4-T-22 |
| Regression | O4-T-20 |

**Mandatory parameterized subcases (explicit):**
- **O4-T-02:** `market_report=""`, `sentiment_report=""`, `news_report=""`, `fundamentals_report=""`, and the two-required-reports-empty subcase.
- **O4-T-03:** `market_report` whitespace-only, `sentiment_report` whitespace-only, `news_report` whitespace-only, `fundamentals_report` whitespace-only, and the empty+whitespace multi-missing subcase.
- **O4-T-14:** single-select `{market}` with `market_report=""`; multi-select `{market, news, fundamentals}` with `news_report=""`.
- **O4-T-17:** each of the four required report keys removed entirely from the state.

**Stage 1 execution scope (Member A approved in PR #7 — tests only, not yet implemented):** Stage 1 IDs are O4-T-01…T-07, T-09…T-15, T-17…T-19, T-24, T-25. For **T-07, T-18, T-19 only their unit portions** are Stage 1. Stage 1 mandatory-cases (unit portions only): T-02, T-03, T-06, T-07 (unit), T-14, T-17, T-18 (unit), T-19 (unit), T-25, with all their parameterized subcases. Passing Stage 1 alone does **NOT** constitute full O4 safety approval — T-08, T-23, T-16, T-20, T-21 and the integration portions of T-07/T-18/T-19 are Stage 2 and still required before final merge.

**Full-O4 mandatory pass rule (final merge gate):** the canonical set above, plus all parameterized subcases, must be **collected**, **actually executed**, **passed**, **not skipped**, **not xfailed**, **not errored**, and **not missing from the collection manifest**. Stage 1 satisfies only the Stage 1 subset; the full set is discharged only after Stage 2. Any violation blocks merge under the proposed Safety CI Gate.

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

### 7.2 CI provenance — unified collection and offline fixture come from CI PR #1

| Source | Change | Provenance |
|---|---|---|
| `pyproject.toml:59` | `testpaths = ["tests", "test/offline"]` | **CI PR #1** ("Regression Phase 1 — collect test/offline via default pytest"), merged into `main` |
| `test/offline/conftest.py` | `autouse` `_no_network` fixture, **directory-scoped to `test/offline/`** | **CI PR #1** (new file) |

- The unified default collection of `test/offline/` and the `test/offline/` network-blocking fixture are **attributed to CI PR #1**, **not** PR #2. (PR #1's changed files were verified via the GitHub API: `pyproject.toml`, `test/offline/conftest.py`.)
- `addopts = '-ra --strict-markers -m "not integration"'` — default run **excludes** `integration`-marked tests; `pytest -q` in `.github/workflows/ci.yml`.
- The `test/offline/conftest.py` fixture returns early **only** for `integration`-marked tests; because O4 offline unit/Graph/CLI tests are **not** integration-marked under the unified policy, the fixture **is** active for them.

> **Evidence caveat:** config and fixture facts are established from read-only API inspection of merged `main` / CI PR #1. Actual collection, execution, and network isolation on CI have **not** been verified; no O4 run has occurred. The current local workspace is a pre-merge snapshot and lacks `test/`.

### 7.3 Required commands (documented proposals — NOT executed, NOT verified for O4)

Under the unified policy the default run is the primary evidence source; a separate integration-marker run is **not** the O4 path for offline Graph/CLI tests (they are default-collected).

1. Default collection (root): `pytest --collect-only -q`
2. Default execution (root): `pytest -q`
3. (Only if a future test genuinely needs real external services) integration-marker execution: `pytest -q -m integration` — not used by O4 offline tests.
4. Manifest comparison: compare expected mandatory node IDs (Section 6.6, incl. parameterized subcase IDs) against the node IDs actually collected and executed by Steps 1–2.

> `pytest --collect-only -q test/offline` alone does **NOT** prove default collection. Since O4 tests live in `test/offline/` and `testpaths` includes it (CI PR #1), they appear in the root default collection; the root `--collect-only -q` is the correct comparison source.

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
- **Performance (non-blocking `Should`):** formal acceptance is the Registry procedure (ubuntu-latest/Py3.11, fixed four-report fixture, 5 warmups, 30 measured calls, nearest-rank p95 `<= 10 ms` inclusive); F's paired A/B plan is supplementary diagnostics only. Authoritative target `p95 <= 10 ms` (registry). `p95 <= 10 ms` meets the target; `p95 > 10 ms` does not. Because O4-NFR-03 is `Should`, an unmet target is **recorded and reported** but does **not** automatically block merge; it only blocks if the approved CI policy explicitly makes it blocking. Failure to meet a performance target never overrides Safety Escape Count or any mandatory safety rule. No measurement has been executed; no passing result is claimed.
- **Manual findings** (O4-T-22) recorded as a review outcome, not an automated pass.

Immediate mandatory safety checks are separate from the confirmed-target performance check and other pending activities. No gate in this section is implemented or configured in CI yet. Outstanding items are: F's sampling-protocol reconciliation (compact registry procedure vs F's extended A/B plan) and A/C confirmation of the actual Gate invocation point and timing wrapper; until those are settled, no acceptance benchmark is run and the 10 ms target remains the confirmed requirement value, not a measured result.

---

## 10. Pending decisions and approval dependencies

| Topic | Requirement | PENDING — decision owner |
|---|---|---|
| **Stage 1 test-plan approval (Member F)** | O4-T-01…07,09…15,17…19,24,25 (unit) | **F** — D's Stage 1 scope is approved by A in PR #7; F has **not** formally approved this O4-TEST-v0.4 plan. Tests may not be written before F's approval is recorded. |
| **Stage 2 shared integration plan (A + C)** | Integration portions of T-07/18/19; T-08/16/20/21/23 | **A + C** — shared files coordinated by C; separate approval required |
| G1/S2/B1 confirmed; exact insertion points & original-rating storage field | O4-FR-07/09/12/16, state policy | Adopted: G1, S2, B1 (Member A, PR #7). Exact line-level insertion scope and the original-rating storage field name remain **A/C** confirmation |
| Durable verdict persistence (v1 not required) | O4-NFR-06, O4-T-21 | A + C — v1 does not require full verdict persistence; enabled rating outputs must still be consistent |
| Integration location / shared-file scope (Decisions A–D give direction only) | O4-FR-07/09/13/15, O4-T-07/08/18/19/23 | A + C (Q4) |
| T-16 performance protocol | O4-NFR-03, O4-T-16 | **Resolved:** registry procedure is formal acceptance (p95 <= 10 ms, 5 warmups/30 calls, ubuntu-latest/Py3.11); F's extended A/B is supplemental diagnostics only. Gate invocation point still A/C (Stage 2). |
| Actual Gate invocation point and timing wrapper for T-16 | O4-T-16 | A + C (source-code call-chain confirmation) |
| Test discovery / CI default collection (unified policy) | All O4 offline tests | F — `testpaths`/fixture sourced from **CI PR #1**; confirm on target branch |
| Reviewer eligibility / approval evidence | Test Approval Gate | A + B |
| Whole-report unavailable sentinel | O4-FR-04, O4-T-04 | **Resolved for v1:** FR-04 is `Won't`; sentinel recognition not implemented. T-04 is an executable negative test (no Q3 blocker). Any future sentinel remains a separate requirement-change review (C + D + B). |
| Invariant representation in Schema 1.0.0 | O4-INV-01…05 | B (requirements §9 Q8) |
| SE-06 interpretation and its CI enforcement | O4-T-18, Section 8 | F (confirm) + team (approve) |
| Network-blocking guard for O4 offline tests | O4-T-15, O4-T-07/08/18/19/23 offline halves | Sourced from **CI PR #1** (`test/offline/conftest.py` `_no_network`, directory-scoped, active for non-integration tests); F confirms on target branch |

**Resolved by A/C architecture direction** (no longer open as policy; still not formal requirements approval): CLI buffering for v1 (B1); checker-failure fail-closed; unknown-analyst configuration abort; rating precedence and conflict-to-`REVIEW`. **G1/S2/B1 adopted by Member A (PR #7):** the same Gate is invoked on Graph and CLI completion paths before `record_decision`/publication; CLI buffers PM text until after the Gate; finalized state sets **both** `final_rating` and `effective_rating` to the Gate-adjusted value while preserving the original rating separately and leaving `final_trade_decision` unchanged.

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
Plan version: O4-TEST-v0.4
Authoritative requirements baseline: docs/req/requirements.yaml @ main 5afb24cf1b48e15e5000ee1365826eebb30d01ae (PR #2 merged)
Superseded draft reference: O4-requirements.md O4-REQ-r3 (working draft, not the approved baseline)
