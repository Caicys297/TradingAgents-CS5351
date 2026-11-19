# O4 — Stage 2 Integration Test Plan

| Field | Value |
|---|---|
| Plan ID | O4-TEST-S2-v0.6-DRAFT |
| Approved at | **`6275725796e618f15d4794ddc61526963bb41c35`** (F test-design `5974514410`; A execution-scope `5973684411`) — approvals cover design/scope only; no code/test/CI/merge. |
| Status | **DRAFT — NOT APPROVED** |
| Owner | Member D |
| Prepared for | Member F (test coordination, CI integration, verification); Member A/C (integration scope) |
| Companion execution plan | `docs/req/O4-Execution-Plan-Stage2-DRAFT.md` (O4-EXEC-S2-v0.6-DRAFT) |
| Verified baseline | **Integration baseline:** current `origin/main` `102511dd44ad8779a46e09cbefe50edb8a995b45` (includes PR #9 `d36a677`, O2 PR #16 `808df04`, O6 identity-binding PR #19 `6a561ab`, O6 CLI PR #20 merge `e4b6f9a`). **PR #17 base:** `d36a677`. **Historical O4 Stage 1 baseline:** `185d18b483ce1e04a9ac649923cbec14707fd9e3`. C must re-verify the O6/C-integrated baseline before O4 CLI edits. |
| Stage 1 checker under test | `tradingagents/agents/evidence_gate.py` — `check_evidence()`, `GateResult` (merged, unchanged by Stage 2) |
| Authoritative requirements | `docs/req/requirements.yaml` (PR #2 `4f87e29f…`); `development_contract.o4` |
| Approval | **Member F pre-implementation test-design approval** — review `5974514410` (`2026-11-19T11:55:11Z`, bound to `6275725`; supplements `5971672933`/`5972448586`). This approves the **test design**; **no Stage 2 test is written/executed, no CI/acceptance/merge** is approved. DRAFT — NOT APPROVED as implemented code. |

> **Status labels:** **PROPOSED** (specified, not written); **NOT YET IMPLEMENTED** (file/fixture absent); **UNVERIFIED** (path/command not yet executed for Stage 2). No CI result, benchmark measurement, or passing test is claimed here.

> **Coverage scope:** this plan covers only the Stage 2 test IDs — **O4-T-08, T-16, T-20, T-21, T-23** and the **integration portions** of **T-07, T-18, T-19** — plus the cross-surface requirement parts of the existing catalogue (T-02/T-06/T-14/T-17/T-25 cross-surface). Unit-level Stage 1 tests already merged are not re-specified here.

> **Unified collection policy [CONFIRMED, CI PR #1 + Member A]:** deterministic offline Graph/CLI tests with mocked dependencies are **not** `integration`-marked and must run under the default `pytest -q`. The `integration` marker is reserved for real external services. `test/offline/conftest.py` provides the autouse `_no_network` guard for non-integration tests.

---

## 0. Shared fixtures & harness [PROPOSED]

Proposed location: `test/offline/` (default-collected). Candidate files:
- `test/offline/test_evidence_gate_integration.py` — T-08, T-19, T-23, display-order, §10e PM temporal/complete-snapshot.
- `test/offline/test_evidence_gate_graph.py` — T-07/T-18 integration, §10a Gate-count, §10b retry/persistence-failure.
- `test/offline/test_evidence_gate_audit.py` — T-21, T-20 signature diff helper.
- `test/offline/test_evidence_gate_benchmark.py` — T-16 (non-blocking `Should`).
- `test/offline/test_evidence_gate_lifecycle.py` — §10 checkpoint/resume + repeated-completion + §10c two-lifecycle isolation.

**Fixtures (all offline, network-blocked):**
- `complete_state` — four non-empty selected reports + clear rating (e.g. `Buy`).
- `missing_evidence_state` — a required report empty/absent (parameterized over the four fields).
- `whitespace_state`, `na_note_state` — whitespace-only / `N/A`-in-body.
- `conflict_state` — `final_rating` vs body disagree; `preexisting_review_state`.
- `fake_graph_stream` / `fake_cli_stream` — deterministic stand-ins for `stream_run` chunks (PM `Buy` body + report fields), so the **real** `record_decision`/publication path runs without LLM/network.
- `tmp_results_dir` — isolated `results_dir` for state log / report tree / HTML.
- `expected_enabled_surface_set(entrypoint, save, show, html, memory_config)` — **grounded in the actual execution entrypoint + output selections + memory configuration, not config alone**. Expected surfaces (computed independently **before** the run):
  - **entrypoint:** programmatic Graph completion vs CLI completion (CLI display only on the CLI path; programmatic return only on the programmatic path);
  - **save** on/off → full Markdown report + standalone `decision.md` present/absent;
  - **show** on/off → terminal/`show` report view present/absent;
  - **html** on/off → HTML report present/absent;
  - **memory** enabled/disabled ← driven by the relevant memory configuration (`memory_log_path`/equivalent) → memory log present/absent;
  - **always where applicable:** state log (via `record_decision`/`_log_state`).
  The **observed** set is collected **after** the run from real artefacts; compared as sets (§T-08). Hardcoded/assumed lists are not acceptable; **Memory is NOT assumed always enabled**, and **save/show/html do not have identical effects** — each combination yields its own expected set.
- **`memory_config` fixture (isolation) [PROPOSED]:**
  - **Memory-disabled cases:** pass an **empty/disabled Memory configuration appropriate to the actual implementation** (e.g. `memory_log_path` unset/`None`, or the implementation's explicit "no memory" setting) — **not** merely omitting a field that defaults to a real path.
  - **Memory-enabled cases:** use an **isolated temporary Memory path** (per-test `tmp_path`), never the default user directory.
  - Regardless of config, tests must assert whether memory persistence occurred and **where**.
- Reuse `test/offline/conftest.py::_no_network` (already active).

**Common execution rule:** drive the **real** Graph/CLI entry points with the fake stream/fixtures; inspect actual artefacts/messages, not only helper returns. Never mark these `integration`.

---

## 1. O4-T-07 (integration portion) — Recoverable checker failure fails closed via real path
- **Covers:** O4-FR-09, O4-INV-04, O4-NFR-04.
- **Fixtures:** `complete_state` + monkeypatched production helper (`_classify_report` or `_resolve_original_rating`) raising `RuntimeError`; `fake_graph_stream`.
- **Execution:** run real Graph completion path (and CLI path) with the failing helper injected.
- **Assertions:** no ungated authoritative Buy/Sell output; every enabled surface shows `REVIEW`; `reason` preserved at the runtime result; cross-surface rating consistent.
- **Expected:** `effective == "REVIEW" and reason and not ungated_published and all(enabled_surfaces == "REVIEW")`.
- **Owner:** D (test author), F (collection/CI).
- **Note:** checker-level T-07 already merged; this is the integration half only.

---

## 2. O4-T-08 — Cross-surface consistency (real path) — **includes explicit test-case matrix**
- **Covers:** O4-FR-07, FR-09, INV-01, INV-03, INV-04, NFR-08.
- **Fixtures:** `missing_evidence_state` + `conflict_state` + checker-failure; `expected_enabled_surface_set(entrypoint, save, show, html, memory_config)`; memory config (enabled/disabled).
- **Execution:** offline integration through the real Graph/CLI publication path; inspect return value, CLI display text, full Markdown report, standalone `decision.md`, HTML report, state log, memory log. Capture **actual output BEFORE the Gate** where the assertion is about pre-gate suppression (see §T-23/display-order), and **after** publication for consistency.
- **Parameterized test-case matrix (each enabled surface checked for presence AND authoritative `effective_rating`):**

  | Axis | Values |
  |---|---|
  | Entrypoint | programmatic Graph completion; CLI completion |
  | save | on / off (full Markdown report + standalone `decision.md`) |
  | show | on / off (terminal/`show` report view) |
  | html | enabled / disabled (HTML report) |
  | memory | enabled / disabled (memory log via memory configuration) |
  | Downgrade variant | missing evidence; rating conflict; checker failure |
  | Persistence paths | state log (always); memory log (only when memory enabled); return value (programmatic path only) |

  Sub-scenarios are enumerated as the cross-product of the applicable axes; **not every surface is enabled for every scenario**, and save/show/html have **distinct** effects (do not collapse them). Each scenario computes its own `expected_enabled_surface_set(entrypoint, save, show, html, memory_config)` and must match the observed set.

- **Assertions (ordered, independent expected-vs-observed; [CONFIRMED §4]):**
  1. `expected = expected_enabled_surface_set(entrypoint, save, show, html, memory_config)` computed **before** the run; `observed` collected **after** the run from real artefacts; assert `observed == expected` (both non-empty). A missing enabled surface, or an empty observed set, **fails** — a vacuous `set(vals)=={...}` equality is explicitly disallowed.
  2. Independently, every expected enabled surface carries the authoritative `effective_rating` (`REVIEW` for all three variants) — asserted **per surface** on the actual artefact content (Markdown header rating, standalone `decision.md`, HTML rating, CLI text, state-log `final_rating`/`effective_rating`, memory tag) — not by collapsing to one set comparison.
  3. **Memory isolation (independent checks):** for **Memory-disabled** cases → assert **no** memory persistence occurred (no entry written anywhere) using an explicit disabled Memory config; for **Memory-enabled** cases → assert the effective rating is persisted to the **expected isolated temporary location**, and assert **no default user directory** (e.g. `~/.tradingagents` or the implementation default) was written.
- **Expected:** both independent assertions pass for the expected enabled set; disabled surfaces (incl. memory when disabled) are not assumed enabled and are not counted in `expected`; memory isolations hold (disabled→no write; enabled→temp-only, no default dir).
- **Owner:** D; F collection/CI.
- **Dependencies:** integration point (Q4) A/C-confirmed; mandatory sub-scenarios confirmed by F (§13).

---

## 3. O4-T-16 — Pure `check_evidence()` incremental latency (registry procedure)
- **Covers:** O4-NFR-03 (`Should`, non-blocking).
- **What is measured [Member A decision]:** the incremental latency of the **pure `check_evidence()` checker** only — **not** a Graph/CLI integration wrapper. Path A = the same fixture with the checker call omitted/bypassed **within the harness only**; Path B = one direct `check_evidence()` call. Graph/CLI wiring, logging, I/O, rendering are **outside** the timed window.
- **Formal acceptance [CONFIRMED, registry — preserved verbatim]:** `ubuntu-latest`, Python 3.11, fixed four-report fixture, **five (5) warm-up calls, thirty (30) measured calls**, single process, **nearest-rank p95 added latency ≤ 10 ms (inclusive)**.
- **Policy [CONFIRMED, preserved]:** this requirement is `Should` / **non-blocking**. An unmet target (p95 > 10 ms) is **recorded** and does **not by itself block merge** unless Member **A and F separately approve** making it CI-blocking. This plan does **not** assume CI enforcement; default remains non-blocking.
- **Fixtures:** fixed four-report fixture (complete + missing-`news` variants as diagnostics); `time.perf_counter_ns()`.
- **Execution:** `Δ = (pure check_evidence() call) − (harness baseline without the call)`; 5 warm-ups then 30 measured calls, single process. Record raw ns; nearest-rank p95.
- **Assertions — split measurement/reporting from blocking checks:**
  - **Blocking (pytest) assertions [safety/behaviour, must pass]:** the pure checker returns the correct, deterministic result on the fixture; exactly one direct checker invocation per measured sample; **no external/network calls**; harness determinism (fixed warm-up/measured counts).
  - **Measurement / reporting (non-blocking) [the `Should` latency target]:** record raw ns samples and compute nearest-rank **p95(Δ)**; report runner/OS/Python/commit/fixture lengths/command + compliance status (`within ≤10 ms` / `over`). It is **not** wired as a blocking pytest assertion by default. Enforcement (making `p95 > 10 ms` fail CI) requires Members **A and F explicitly approving** it; this plan does not assume that.
- **Expected:** correctness + no-network blocking checks pass; latency p95 reported against the ≤10 ms target as a non-blocking diagnostic/acceptance record; **no passing latency result claimed now**.
- **Owner:** F (harness), D (fixtures).
- **Note:** Member F’s extended paired A/B design (100 warm-up pairs, 3 processes × 1000 samples) is **supplementary diagnostics only**, never a replacement for the registry acceptance procedure.

---

## 4. O4-T-18 (integration portion) — Unknown config aborts publication
- **Covers:** O4-FR-11, O4-FR-15.
- **Fixtures:** `complete_state` with an unknown analyst key in the graph’s selection (e.g. `"options"`); `fake_graph_stream`.
- **Execution:** drive the real publication path with unknown configuration.
- **Assertions:** the publication path aborts **without** producing an authoritative rating; the run is **not** reported as a normal `REVIEW`; `ValueError` is not swallowed by the recoverable handler.
- **Expected:** `not authoritative_published and not reported_as_normal_review`.
- **Owner:** D; F collection/CI.
- **Note:** checker-level T-18 already merged; integration half only.

---

## 5. O4-T-19 (integration portion) — Buy body not presented as approved
- **Covers:** O4-FR-07, FR-12, FR-13, INV-01.
- **Fixtures:** `missing_evidence_state` whose `final_trade_decision` body contains `Buy`; `fake_cli_stream`; configs enabling markdown report and HTML (`html=True`).
- **Execution:** real CLI/Graph path; inspect post-gate rendering on **each enabled surface** — CLI text, markdown report, HTML report.
- **Assertions (observable, per enabled rendered surface):**
  - enabled surfaces show `REVIEW` as the authoritative rating;
  - no rendered surface presents the raw Buy as the run's approved rating (e.g. must not show "Rating: Buy" for a REVIEW run);
  - any preserved Buy body is accompanied by the non-authoritative/unapproved label (label wording pending A/C);
  - `final_trade_decision` in state is byte-identical to input (preserved).
- **Expected:** `all(enabled_surfaces=="REVIEW") and body_labeled_unapproved and not approved_buy and out_decision==in_decision`.
- **Owner:** D; F collection/CI.
- **Note:** checker-level T-19 already merged; integration half only.

---

## 6. O4-T-20 — Backward compatibility (extended)
- **Covers:** O4-NFR-05.
- **Fixtures:** existing regression suite; signature snapshot of `run_rating`, `record_decision`, `store_decision`, `write_report_tree`; **legacy states** (no `effective_rating`, older-checkpoint states); a **checkpoint/resume-to-completion** state; gated-path fixtures.
- **Execution:**
  1. Run the full existing suite (including the **actual gated paths** where applicable after Stage 2 wiring lands) — must stay green.
  2. Automated/manual **signature diff**: additive-only (no removed/renamed params; new params optional/back-compatible).
  3. **Legacy/checkpoint behaviour:** a finalized state without `effective_rating` (pre-Stage-2 or restored from an older checkpoint) still yields a usable rating via `run_rating` semantics without raising; default behaviour for consumers unchanged. Checkpoint/resume-to-completion still produces a gated, consistent rating (see execution plan §K.2).
  4. **Existing-caller compatibility:** the merged tests asserting the current `record_decision()` behaviour/signature (`tests/test_cli_memory_log.py` `:29/:37/:190`, `tests/test_memory_log.py` `:966`) must remain green — any signature change must be additive/back-compatible (pending C).
  5. **Repeated-completion & stale-field read-compat:** a repeat within one completed execution does not double-publish/persist; a legacy state carrying stale `effective_rating`/`original_rating` is readable for history but does **not** authorize an ungated new publication (see execution plan §K.2 and §10 above).
- **Assertions:** suite green; diff additive-only; legacy state path does not raise and preserves prior semantics; resumed-to-completion run consistent; existing-caller tests green; repeat→single publish; stale-fields→re-evaluated.
- **Expected:** `suite green; diff additive-only; legacy/checkpoint back-compat holds`.
- **Owner:** F (regression + signature review), D (diff/legacy fixtures).
- **Type:** Regression + manual signature review + legacy/checkpoint behaviour.

---

## 7. O4-T-21 — Auditability of artefacts (runtime/audit + enabled-rating consistency)
- **Covers:** O4-NFR-06.
- **Fixtures:** a completed downgraded run (`tmp_results_dir`, memory enabled).
- **Execution:** artefact inspection (state log, memory log, and the return value / consumer surfaces).
- **Runtime `GateResult` observation [PROPOSED, no unapproved persistence]:** the runtime `GateResult` (verdict, effective rating, per-item statuses, diagnostic `reason`) is observed **in-memory via the proposed per-run observation mechanism** (a lightweight observer/hook or per-run accessor — concrete interface **pending C**) **without** changing `record_decision()`'s signature/`None` return and **without** requiring the full structured verdict to be durably persisted (not required in v1). **The generic CLI REVIEW warning does not consume `GateResult`** — it reads `final_state["effective_rating"]` directly; this test verifies the diagnostic observation seam, not CLI display.
- **Assertions:** `effective_rating` recoverable from enabled authoritative outputs **and** all enabled authoritative rating outputs == `effective_rating`; the runtime `GateResult.verdict`/`effective_rating`/`reason` observed **in-memory** match the published effective rating; the observation does **not** require durable verdict persistence; the CLI REVIEW warning (when `REVIEW`) is derivable from `final_state["effective_rating"]` alone.
- **Expected:** recoverable + consistent; in-memory observation available; CLI warning independent of `GateResult`. Full structured-verdict durability **not** required (v1).
- **Owner:** D; F collection/CI.
- **Dependencies:** Stage 2 shared integration; C confirms the concrete in-memory observation interface.

---

## 8. O4-T-23 — CLI buffering before gate (real CLI, incl. real-time Markdown)
- **Covers:** O4-FR-07, FR-13, INV-01, INV-03.
- **Fixtures:** `fake_cli_stream` emits a PM `Buy` body **and** a PM message before the Gate sees a missing required report; isolated `report_dir` (`tmp_path`) so real-time Markdown writes are observable; exercise **BOTH** CLI display areas — the PM **message/display area** and the PM **decision/report section** — **and the real-time sectional Markdown** (`final_trade_decision.md` via `save_report_section_decorator`, `cli/run.py:173–190`).
- **Execution:** offline CLI integration (LLM/network replaced by fixtures; network blocked). Capture output **BEFORE the Gate executes**, **after authorized release**, and **on failure paths** — real emitted output / file contents at those moments, not only the final screenshot.
- **Assertions:**
  - **before Gate:** neither CLI area shows an approved Buy/Sell, AND `final_trade_decision.md` does **not** contain an authorized PM Buy/Sell (PM Markdown withheld pre-Gate);
  - **ordinary Analyst `.md` sections** still stream normally (unchanged behaviour);
  - **after authorized release:** PM content published with effective rating; `REVIEW` → preserved body labelled non-authoritative on all enabled outputs;
  - **failure paths** (invalid config / interrupted stream / persistence failure): no authoritative PM decision published — no leftover `final_trade_decision.md` containing an authorized recommendation.
- **Expected:** `not pre_gate_published_in(message_area AND report_section AND final_trade_decision.md)`, `ordinary_analyst_stream_unchanged`, `post_gate=="REVIEW" → body_non_authoritative`, failure → `no authorized PM publication`.
- **Owner:** D; F collection/CI.
- **Dependencies:** integration point (Q4) A/C-confirmed; real-time Markdown buffer/release point confirmed by C (§D.1).

---

## 9. CLI display-order test (new — relative order) [PROPOSED]
- **Covers:** O4-FR-07, FR-13, INV-03 (completion must not imply an approved trade). **Display-order provenance:** the proposed order is a **D/C coordination proposal — NOT verified A/F approval**; final integration placement/wording pending A/C (see companion execution plan §E).
- **Fixtures:** `fake_cli_stream` for a complete-valid run **and** a REVIEW (missing-evidence) run; capture the post-analysis output sequence (ordered list of emitted lines/items) rather than a screenshot.
- **Execution:** real CLI path; record the ordered post-analysis messages after the Live display ends.
- **Assertions (relative order):** for the REVIEW run, the observed order is **completion notice → O4 REVIEW warning (if applicable) → elapsed time → O6 statistics summary → report options**, and these elements appear exactly once each in that relative order (other unrelated lines may interleave). For the complete-valid run, the O4 REVIEW warning is **absent** but the other elements retain their relative order. The **completion notice text must not contain an approved Buy/Sell recommendation** (it states completion only).
- **Expected:** `index(completion) < index(review_warning?) < index(elapsed) < index(o6_stats) < index(report_options)`; `"Buy"/"Sell" not presented as approved in completion notice`.
- **Owner:** D; F collection/CI.
- **Note:** exact wording/placement pending A/C (§J); this asserts *relative order and non-implying completion*, not exact strings.

---

## 10. Checkpoint / resume & repeated-completion coverage — [PROPOSED]
- **Covers:** O4-FR-07, FR-09, INV-01/03 (publication integrity across resume + repeated-completion paths).
- **Fixtures:** a checkpointed run **resumed to completion** (`checkpoint_thread_id` + `checkpoint_input`) with a downgraded state; an **interrupted** run that does not reach publication; a **repeated `record_decision()`** fixture (same completed execution invoked twice); a **legacy/stale-field checkpoint** state carrying stale `final_rating`/`effective_rating`/`original_rating`.
- **Execution:** offline; drive the real Graph/CLI resume/repeat path with fixtures; do not assume fresh and resumed paths are identical.
- **Assertions (observable):**
  - **authoritative evaluation count:** resumed-to-completion and repeated-call paths each perform **exactly one** authoritative Gate evaluation (direct count assertion, see §10a);
  - **rating propagation:** after a resumed/complete run, `effective_rating`/`final_rating` reflect the gated result and `original_rating` holds the pre-gate value;
  - **`original_rating` not overwritten** by a previously downgraded `REVIEW` on a repeat;
  - **persistence count:** state log and memory persist **exactly once** per completed execution (no duplicates on repeat);
  - **checkpoint cleanup ordering:** checkpoint cleanup (`clear_checkpoint_on_success`) occurs **only after** successful gated completion (restore → Gate → S2 → log → cleanup), not before;
  - **complete restored state evaluated:** the resumed Gate evaluates the **full restored reports** (all four report fields restored), not a partial state — a resumed run whose restored reports satisfy presence yields a non-downgraded gated result, and one with a missing restored report downgrades;
  - **interrupted** run that never reaches authoritative publication publishes **no** authoritative rating (existing skip-`record_decision` behaviour preserved);
  - **legacy/stale-field checkpoint** state with stale `final_rating`/`effective_rating`/`original_rating` → **re-evaluated** on completion (presence of stale `effective_rating` does **not** authorize publication); historical-state read still works via `run_rating` semantics;
  - **legacy/checkpointed state without `effective_rating`** still yields a usable rating (see T-20).
- **Expected:** `eval-count==1`, `rating-propagated`, `original_rating-preserved`, `persist-count==1`, `cleanup-after-gated-completion`, `stale-fields→re-evaluated`, `interrupted→no authoritative rating`.
- **Owner:** D; F collection/CI.
- **Note:** exact resume/repeat/legacy interaction with the Gate (and execution-identity mechanism) is **pending C**.

---

## 10a. Gate-invocation-count & ordering (mandatory) — [PROPOSED]
- **Covers:** O4-FR-07, FR-09, INV-01/03 (one authoritative evaluation, before publication).
- **Fixtures:** instrument `check_evidence` via a counting seam (wrap/spy) around the **authoritative** call; fixtures for: duplicate completion callbacks (same execution), **new CLI run after a persistence failure**, **Resume-to-completion**, and **sequential executions on one Graph instance**; interrupted/error fixture.
- **Execution:** run each entrypoint offline; count authoritative `check_evidence()` evaluations and record the order relative to `record_decision`/publication.
- **Assertions:**
  - normal programmatic completion → **exactly one** authoritative evaluation;
  - CLI completion → **exactly one** authoritative evaluation (must **not** re-invoke authoritatively after `record_decision`);
  - resume-to-completion → **exactly one** authoritative evaluation **before** publication;
  - **duplicate completion callbacks (same execution)** → exactly one authoritative evaluation (deduplicated);
  - **new CLI run after persistence failure** → a **new** authoritative evaluation (NOT deduplicated with the prior execution);
  - **Resume-to-completion** → a **new** authoritative evaluation on the complete restored state (never reuses checkpoint authorization);
  - **sequential executions on one Graph instance** → each new execution has its **own** single authoritative evaluation (thread reuse ≠ execution identity);
  - the evaluation precedes any authoritative publication in every case; interrupted/error cases publish **no** authoritative rating;
  - S2 state per case: `original_rating` captured pre-gate (never the downgraded effective), `final_rating == effective_rating`, `final_trade_decision` byte-preserved.
  - **Per-execution completion-guard lifecycle [PROPOSED; mechanism pending C]:** the guard is created for the current completion, blocks duplicate authoritative work while the same execution can fire again, is released when the execution terminates (after successful gated logging + checkpoint cleanup, or clean abort), and is **never reused** for a new execution. Test: a **new** execution after a completed one performs its **own** single authoritative evaluation (guard not reused); a duplicate callback within the **same** execution performs none.
  - **CLI final-state completeness [PROPOSED; completeness pending C]:** the state passed to `record_decision` from the CLI stream-merge path contains **all four report fields** (incl. those restored from a checkpoint on resume) — not an incomplete stream delta; a resumed run whose restored reports are complete is not spuriously downgraded for "missing" evidence.
- **Expected:** `count == 1` per completed execution; `gate_before_publication == True`; interrupted → `no_authoritative_publication`; guard-not-reused across executions; CLI final_state complete.
- **Owner:** D; F collection/CI.
- **Dependencies:** the observation seam / counting mechanism to C (§J). This is a **mandatory** test (enumerated in §13).

---

## 10b. Gate-success / logging-persistence failure & retry — [PROPOSED; mandatory]
- **Covers:** O4-FR-07, FR-09, INV-01/03 (fail-closed publication; no ungated release; no duplicate persistence).
- **Fixtures:** a completed run whose Gate succeeds and updates `final_state` (`effective_rating`/`final_rating`), then a **state-log write failure** (monkeypatched `_log_state`) and a **memory-write failure** (monkeypatched `store_decision`) separately; the **same logical completion** retried; counting spy on `check_evidence`; pre-Gate snapshot spy.
- **Execution:** offline; run → force persistence failure → retry the same completion.
- **Assertions:**
  - **state-log failure + retry:** retry does **not** produce a second authoritative Gate evaluation when the guard confirms the same finalized input; `original_rating` preserved across the retry; no ungated Buy/Sell released; missing persistence completed on retry.
  - **memory-write failure + retry:** same guarantees for the memory path.
  - **`original_rating` preservation:** not re-captured from the already Gate-downgraded `final_rating`.
  - **original-rating provenance:** capture happens **before** the Gate mutates `final_rating`; the pre-Gate `final_rating` field is distinguished from the rating parsed from the original `final_trade_decision`; provenance is preserved for same-execution reuse; `final_trade_decision` bytes unchanged.
  - **no unintended second authoritative evaluation** for a valid same-execution retry (count == 1);
  - **no duplicate authoritative publication** (state log / memory entries not duplicated);
  - **partial persistence** (only one of state-log/memory written) handled safely — the retry completes the missing one without releasing an ungated rating; if no trustworthy original input is available → **fail closed** (no authoritative publication).
  - retry handling must **not** bypass a required Gate for a **new** completion.
- **Expected:** `retry→reuse-valid-gate (count==1)`, `original_rating preserved`, `no ungated release`, `no duplicate persistence`, incomplete-and-unrecoverable → `no authoritative publication`.
- **Owner:** D; F collection/CI.
- **Dependencies:** pre-Gate snapshot / persistence-idempotency mechanism **PENDING C**. Mandatory (§13).

---

## 10c. Two distinct lifecycles (guard vs GateResult record) — [PROPOSED; mandatory]
- **Covers:** O4-FR-07, FR-09, INV-01/03; isolation on the SAME Graph instance.
- **Fixtures:** **one Graph instance** executing **sequential separate** completions; repeated-completion callbacks; failed-persistence retry; resume; cleanup observation.
- **Execution:** offline; drive multiple executions on the same Graph instance.
- **Assertions:**
  - **Guard lifecycle (A):** initialized per execution; blocks repeat within the same execution; tracks Gate-completed and publication/persistence-completed; **not released prematurely** after the first successful Gate (so a post-Gate persistence retry reuses the result); released at safe cleanup; **never reused** as authorization for a new execution or a resumed-to-completion execution needing fresh evaluation.
  - **GateResult record lifecycle (B):** created when a Gate evaluation produces a result; associated with its execution; exposes verdict/effective/reason/statuses to diagnostics/tests; no durable persistence; explicit availability/cleanup; **must not leak** one execution's result into another execution on the same Graph instance.
  - **Isolation test:** two sequential executions on the **same** Graph instance each get their **own** guard/record; a duplicate callback in the **same** execution triggers no second authoritative eval; a new execution after cleanup performs a fresh single eval.
- **Expected:** `guard isolated per execution`, `record not leaked across executions`, `post-Gate retry reuses result`, `cleanup at safe boundary`.
- **Owner:** D; F collection/CI.
- **Dependencies:** concrete representation/cleanup **PENDING C** (§B.4). Mandatory (§13).

---

## 10d. REVIEW display & legacy-state compatibility — [PROPOSED; mandatory]
- **Covers:** O4-FR-07, FR-12, FR-13, FR-16, INV-01/02.
- **Fixtures:** newly gated REVIEW state; newly gated valid (Buy/Sell/Hold) state; **legacy state lacking `effective_rating`**; legacy checkpoint state **resumed into a new completed execution**.
- **Execution:** offline; render/read via the real `is_review(run_rating(final_state))` path (`rating.py:106`/`:115`).
- **Assertions:**
  - newly gated REVIEW → warning shown; `final_rating == effective_rating`; body labelled non-authoritative;
  - newly gated valid rating → preserved, no spurious REVIEW;
  - legacy state lacking `effective_rating` → readable via `run_rating` (no raise), but **reading a legacy state never authorizes a new ungated publication**;
  - legacy checkpoint resumed into a **new completed execution** → **fresh Gate evaluation** required; not published unggated;
  - **no fallback to an ungated Buy/Sell** when a new publication requires a Gate result.
- **Expected:** `REVIEW→warning`, `valid→preserved`, `legacy→readable but not publishing`, `no ungated fallback`.
- **Owner:** D; F collection/CI.
- **Dependencies:** none beyond integration; mandatory (§13).

---

## 10e. PM buffering temporal window & complete-snapshot — [PROPOSED; mandatory]
- **Covers:** O4-FR-07, FR-13, INV-01/03.
- **Fixtures:** `fake_cli_stream` emitting PM Buy text; capture of **both** CLI areas (message/display area + decision/report section) **BEFORE** Gate completion; forced failure paths (invalid config; interrupted stream; state-log/memory failure); a resumed `values`-snapshot run with restored reports.
- **Execution:** offline; capture real emitted output at the **pre-Gate** moment and **during each failure path** (not only final rendering).
- **Assertions:**
  - **PM buffering covers the entire interval** from streaming PM output until Gate evaluation + publication authorization completes — **both** areas show no approved Buy/Sell before the Gate;
  - Gate REVIEW → preserved PM text shown **only** with non-authoritative label;
  - invalid config → **no** authoritative decision publication;
  - interrupted/failed stream → **no** authoritative decision publication;
  - state-log/memory failure → publication follows failure policy; buffered Buy/Sell **not** silently released;
  - **complete `values` snapshot** (incl. restored reports) is the Gated input, not an incomplete chunk.
- **Expected:** `no pre-gate release in either area`, `failure paths → no authoritative publication`, `REVIEW→non-authoritative label`, `snapshot complete`.
- **Owner:** D; F collection/CI.
- **Dependencies:** exact buffering boundary pending C/A; mandatory (§13).

---

## 11. Cross-surface requirement parts (from existing catalogue)
For T-02, T-06, T-14, T-17, T-25 the **cross-surface** portions (already validated unit-level in Stage 1) are re-exercised through the real publication path as part of T-08’s surface-consistency matrix (same fixtures, downgraded variants). No new IDs; the unit assertions remain Stage 1.

---

## 12. Traceability matrix (Stage 2)

| Test | Requirement(s) | Type | Owner | Key assertion |
|---|---|---|---|---|
| T-07 (integration) | FR-09, INV-04, NFR-04 | integration | D/F | fail-closed, no ungated output |
| T-08 | FR-07, FR-09, INV-01/03/04, NFR-08 | integration | D/F | expected-vs-observed enabled set + per-surface `REVIEW` |
| T-16 | NFR-03 (`Should`) | benchmark | F/D | p95 Δ ≤ 10 ms (non-blocking) |
| T-18 (integration) | FR-11, FR-15 | integration | D/F | abort, not normal REVIEW |
| T-19 (integration) | FR-07, FR-12, FR-13, INV-01 | integration | D/F | body unapproved (CLI/MD/HTML), no approved Buy |
| T-20 | NFR-05 | regression + manual + legacy/checkpoint | F/D | suite green; additive-only; legacy/checkpoint back-compat |
| T-21 | NFR-06 | artefact inspection | D/F | recoverable + consistent effective; runtime GateResult in-memory |
| T-23 | FR-07, FR-13, INV-01, INV-03 | CLI integration | D/F | no pre-gate publish (message area **and** report section **and** real-time `final_trade_decision.md`); ordinary Analyst streaming unchanged |
| Display-order (new) | FR-07, FR-13, INV-03 | CLI integration | D/F | completion→REVIEW→elapsed→O6→reports; completion not implying trade |
| Checkpoint/resume (new) | FR-07, FR-09, INV-01/03 | integration | D/F | resumed→gated-consistent; interrupted→no authoritative rating |
| Repeated-completion (new) | FR-07, FR-09, INV-01/03 | integration | D/F | repeat→single authoritative publish/persist; `original_rating` not overwritten; stale-fields→re-evaluated |
| Gate-invocation-count (new) | FR-07, FR-09, INV-01/03 | integration | D/F | exactly one authoritative eval, before publication |
| Gate-success/log-failure retry (10b) | FR-07, FR-09, INV-01/03 | integration | D/F | retry reuses valid gate, original_rating preserved, no duplicate publish |
| Two-lifecycle isolation (10c) | FR-07, FR-09, INV-01/03 | integration | D/F | guard per-execution; GateResult record not leaked across executions |
| REVIEW/legacy display (10d) | FR-07, FR-12, FR-13, FR-16, INV-01/02 | integration | D/F | REVIEW warning; legacy readable but no ungated new publication |
| PM buffering temporal (10e) | FR-07, FR-13, INV-01/03 | integration | D/F | no pre-gate release in either area; complete values snapshot |

---

## 13. Mandatory collection & safety acceptance — **[mandatory set approved by F at `6275725` (`5974514410`)]**

All **mandatory** Stage 2 tests and their **parameterized subcases / sub-scenarios** must be **collected, actually executed, and passed** for final safety acceptance. None may be **skipped, xfailed, errored, or missing from the collection manifest**; a missing mandatory node blocks acceptance (and merge, under the proposed Safety CI Gate).

**Mandatory Stage 2 set (enumerated; F confirms final classification against plan §6.6):**
- **T-07 (integration portion) — RESTORED to mandatory.** Recoverable checker failure fails closed through the real completion/publication path.
- **T-08 — all parameterized cross-surface sub-scenarios** (entrypoint × save × show × html × downgrade-variant matrix in §2), each asserting presence **and** per-surface `effective_rating` for the **actual enabled channels**: Markdown report, standalone `decision.md`, HTML report, CLI display, state log, memory log, programmatic return.
- **T-18 (integration)** — unknown analyst configuration `ValueError` propagates and publication aborts.
- **T-19 (integration)** — preserved Buy/Sell body marked unapproved across enabled rendered outputs.
- **T-23** — pre-Gate observation of **BOTH** the CLI message area **and** the decision/report section (no authoritative publication before the Gate).
- **Display-order (new)** — completion notice → REVIEW warning (if applicable) → elapsed → O6 stats → report options; completion not implying an approved trade.
- **Checkpoint/resume (new)** — **completed** (resumed→gated-consistent) and **interrupted** (no authoritative rating) cases.
- **Gate-success/log-failure retry (§10b, new)** — state-log failure + retry, memory-write failure + retry, `original_rating` preservation, no second authoritative eval on valid retry, no duplicate publication, partial-persistence safe handling; unrecoverable → fail closed.
- **Two-lifecycle isolation (§10c, new)** — guard vs GateResult record; sequential executions on the SAME Graph instance; no cross-execution leak; post-Gate retry reuses result; cleanup.
- **REVIEW/legacy display (§10d, new)** — newly gated REVIEW/valid; legacy lacking `effective_rating` readable but no ungated new publication; resumed legacy → fresh Gate; no ungated Buy/Sell fallback.
- **PM buffering temporal & complete snapshot (§10e, new)** — both CLI areas captured BEFORE Gate; failure paths publish nothing; complete `values` snapshot (incl. restored reports) is the Gated input.
- **Repeated-completion (new, mandatory)** — repeated `record_decision()` within one completed execution → single authoritative publish/persist; `original_rating` not overwritten by a prior REVIEW; legacy/stale-field checkpoint → re-evaluated, stale `effective_rating` does **not** authorize publication.
- **Gate-invocation-count** — see below.
- **T-20 (regression gate)** — historical-state read compatibility **without** allowing an ungated **new** publication; gated-path suite green; additive-only signatures.
- **T-21 (auditability)** — effective rating recoverable from enabled outputs and consistent; runtime `GateResult` observed at the **observation-point contract pending confirmation** (no mandatory durable persistence of full verdict).

**Direct Gate-invocation-count assertions (mandatory):**
- normal programmatic Graph completion → **exactly one** authoritative `check_evidence()` evaluation;
- CLI completion → **exactly one** authoritative evaluation (reused from the shared boundary, not a second authoritative call);
- resume-to-completion → **exactly one** authoritative evaluation before publication;
- **all** cases: the evaluation occurs **before** any authoritative publication; interrupted/error cases perform **no** authoritative publication;
- **S2 state assertions** in each: `original_rating` captured pre-gate (never overwritten by a downgraded effective), `final_rating == effective_rating`, `final_trade_decision` byte-preserved.

**F’s test-design approval recorded:** the mandatory set + parameterized boundaries were approved by F at `6275725` (`5974514410`). F authorized administrative updates to outdated approval text without a renewed approval. T-16 remains non-blocking `Should` (measurement/reporting only). No Stage 2 test is written/executed; no CI/acceptance/merge approved.

---

## 14. Unresolved items blocking finalization
**Approvals recorded at `6275725`:** F test-design (`5974514410`) and A execution-scope (`5973684411`); C interface confirmed (link awaiting traceability). **Resolved (do not re-open):** `original_rating` field name; S2 capture→set order + conflict in `gate.reason` (no full durable `GateResult`); single authoritative Gate at the `record_decision` shared boundary (no Graph/CLI second authoritative call); **C's backward-compatible `record_decision` contract** (signature + `None` return preserved, in-place mutation); T-16 measures the **pure** checker; `Should` non-blocking by default; T-07 integration **mandatory**. **PR #9: merged (merge commit `d36a677` = PR #17 base) — not a live dependency.**
- **C (interface confirmed at `6275725`; original evidence link awaiting traceability — internal mechanism is C's choice):** **retry/idempotency** mechanism for Gate-success-then-persistence-failure (§C) incl. pre-Gate snapshot + partial-persistence idempotency; **two distinct lifecycles** representation/cleanup — guard (A) vs GateResult record (B), Graph-instance-scoped execution-isolated (§B.4); same-vs-new **execution-identity** mechanism + **per-execution guard lifecycle** (§B.1 — lifecycle create/use/preserve/release/never-reuse; do not invent an approved identity field, permanent state field, or cache); inline vs shared helper; `selected_analysts` reaching the boundary; **concrete per-run in-memory `GateResult` observation interface** (CLI REVIEW warning reads `final_state["effective_rating"]` directly, not full `GateResult`); **complete `values` snapshot** final-state source (§B.3 — merged stream chunks + checkpoint-restored reports; residual if a resumed snapshot omits a field); `original_rating` conflict/absent encoding; effective-rating persistence shape (with B); B1 two-area insertion points; **real-time sectional Markdown buffer/release point** (PM `final_trade_decision.md` withheld until Gate + authorization; ordinary Analyst streaming unchanged — §D.1); **trusted pre-Gate original-rating provenance representation** (pre-Gate `final_rating` field vs parsed original body; fail-closed if none); duplicate-vs-new execution rules; repeated-completion/checkpoint/resume/legacy-stale-field rules + cleanup ordering.
- **C — O6 prerequisite:** O6 identity-binding **merged** (`6a561ab`/PR #19) **and O6 CLI PR #20 merged** (`e4b6f9a`, ancestor of `origin/main` `102511d`) → traceable commit exists; **C must still record CLI joint-verification evidence**; re-verify O6/O2/PR#9-integrated `main` before O4 CLI edits. *(Verified via Git/API; not claiming C's joint verification done; O6 prerequisite ≠ O4 coding approval.)*
- **A/C:** enabled-surface contract confirmation; non-authoritative label wording (CLI/MD/`decision.md`/HTML) + cause-neutral REVIEW message + display-order placement; unknown-config abort UX; T-21 observation-point contract.
- **A:** confirm the **exact six shared-file modification scope** at final Execution Plan approval.
- **A/F:** whether the `Should` (≤10 ms) target may ever be CI-blocking (default non-blocking).
- **F:** test-design approval **recorded** (`5974514410`, bound to `6275725`); F authorized administrative updates to outdated approval text without a renewed approval.

**Test design approved by Member F at `6275725` (`5974514410`). No Stage 2 test is written or executed; no CI/acceptance/merge is approved. DRAFT.**
