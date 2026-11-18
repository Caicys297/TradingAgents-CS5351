# O4 — Evidence Gate: Stage 2 Execution Plan

| Field | Value |
|---|---|
| Plan ID | O4-EXEC-S2-v0.4-DRAFT |
| Status | **DRAFT — NOT APPROVED** |
| Prepared by | Member D |
| Prepared for | Member A (scope/integration review), Member C (shared-file integration owner), Member F (test/CI) |
| Companion test plan | `docs/req/O4-Test-Plan-Stage2-DRAFT.md` (O4-TEST-S2-v0.4-DRAFT) |
| Verified baseline | `origin/main` `d36a677d4738efd365b6bbcf6f69f993acf8fd3c` (this review branch's base; includes O2 PR #16 `808df04`, PR #9). Historical Stage 1 merge: `185d18b483ce1e04a9ac649923cbec14707fd9e3`. |
| Stage 1 checker | `tradingagents/agents/evidence_gate.py` (`check_evidence`, `GateResult`) — merged |
| Authoritative requirements | `docs/req/requirements.yaml` (PR #2 merged at `4f87e29f…`); `development_contract.o4` |
| Approval | **NONE.** Stage 2 is NOT approved. Shared-file ownership for Stage 2 has NOT been newly granted by this document. This is a proposal for A/C/F review. |

> **Document intent.** This is a *planning* document only. It proposes how to wire the already-merged Stage 1 checker into the runtime. It does **not** implement Stage 2, does **not** modify code, and does **not** claim any new approval. Every line number was re-verified against `main` `185d18b`; numbers may drift as other PRs merge and must be re-confirmed at implementation time.

> **Confirmed vs proposed.** Statements marked **[CONFIRMED]** are fixed by the requirements registry or already-merged code. Statements marked **[PROPOSED]** are this plan's suggested implementation and require A/C/F sign-off.

---

## 0. Objectives and scope

**Objective.** Enforce a single Evidence Gate evaluation on both completion paths (Graph and CLI) before any authoritative rating is published, so that missing evidence, checker failure, or rating conflict cannot leak an ungated Buy/Sell — per `development_contract.o4.publication` and FR-07/09/13/16, INV-01/03/04.

**One evaluation per completed execution [CONFIRMED intent, FR-07/INV-03; placement decided by A].** "One Gate evaluation per completed execution" is a *behavioural* invariant: for a single logical run (including a checkpoint/resume that completes), exactly one authoritative evaluation determines the published rating. Member A's decision places that single authoritative evaluation at the shared completion boundary (`record_decision`), covering both the Graph and CLI completion paths; the Graph and CLI must not independently re-invoke the checker authoritatively. The exact implementation mechanism (inline in `record_decision` vs a shared helper) remains **subject to C's verification** (§B.0, §J).

**In scope (Stage 2):** wiring `check_evidence()` into the shared completion boundary (`record_decision`) so it covers the Graph and CLI completion paths; propagating `effective_rating`; buffering PM text in the CLI; reading the effective rating in reporting/HTML/memory; adding `effective_rating` + `original_rating` state fields; the Stage 2 tests (T-08, T-16, T-20, T-21, T-23 and the integration halves of T-07/T-18/T-19).

**Out of scope (v1 boundary):** whole-report sentinel recognition (FR-04 `Won't`), report-length/content-truth/cross-verification/debate-history rules (FR-14 `Won't`), durable persistence of the *complete* structured verdict (not required in v1 — Member A), and any change to the Stage 1 checker's pure contract.

---

## A. Current call chain (verified on `origin/main` `d36a677`) — **[CONFIRMED by code]**

> **Baseline note.** This review branch is based on `origin/main` `d36a677` (includes O2 PR #16, PR #9). Verified facts below are read from `d36a677`. **C must still re-verify the O6/O2-integrated baseline after O6 F identity-binding lands and after any further main merges** before line-level O4 CLI scope is fixed (see §I). O2 PR #16 added `tradingagents/repro/manifest.py` (isolated writer; **not yet wired** into `cli/run.py`/`trading_graph.py` on `d36a677`).

**Graph completion path** — `tradingagents/graph/trading_graph.py`:
- `_run_graph()` (`:373`): after graph invoke/stream → `self.record_decision(...)` (`:400`) → `clear_checkpoint_on_success(...)` → `return final_state, run_rating(final_state)` (`:405`).
- `record_decision()` (`:359`): `self._log_state(...)` (`:362`) then `memory_log.store_decision(..., rating=run_rating(final_state))` (`:368–371`).
- `_log_state()` (`:438`): serializes state incl. `"final_rating": run_rating(final_state)` (`:464`) and raw `final_trade_decision` (`:463`). No `effective_rating` field today.
- Selection: `self.selected_analysts` (`:109`) — **not on `AgentState`**.

**CLI path** — `cli/run.py`:
- `run_analysis()` (`:99`) streams via `graph.stream_run(...)` (`:241`).
- **Pre-gate publication** of PM text: report section `"final_trade_decision"` written from streamed chunks at `:310–334` (incl. `"### Portfolio Manager Decision\n{judge}"` at `:333`); messages buffered at `:249–251` — all **before** `record_decision` (`:353`).
- Post-stream copy of `final_state[section]` into sections at `:369–371`.
- Rating display: `is_review(run_rating(final_state))` at `:380` (ungated). Reports offered at `:388` (`_offer_reports`, `:426`).

**Other readers (ungated `run_rating`):**
- `tradingagents/reporting.py` `_header()` `:26` (`- Rating: {run_rating(...)}`), `write_report_tree()` `:92`.
- `tradingagents/report_html.py` `:251`.
- `tradingagents/memory/log.py` `store_decision()` `:32`, fallback `parse_rating` `:56`.

**AgentState** — `tradingagents/agents/state.py`: has `final_trade_decision` (`:69`), `final_rating` (`:70`); **no** `effective_rating`, **no** `original_rating`.

---

## B. G1 — Gate enforcement points — **[PROPOSED]**

**G1 policy [CONFIRMED direction, A PR #7]:** the same Gate is invoked on **both** the Graph completion path and the CLI path, before `record_decision` / external publication.

### B.0 Authoritative Gate placement — one shared completion boundary — **[PROPOSED architecture direction (Member A); NOT code authorization; mechanism subject to C's verification]**

**Invariant [CONFIRMED intent, FR-07/INV-03]:** for each **completed execution** exactly **one authoritative** Gate evaluation determines the published rating, and no path can publish a rating that bypasses it.

**Verified call-path fact [CONFIRMED by code, `origin/main` `d36a677`]:** both completion paths converge on `record_decision()`:
- **Programmatic:** `propagate()` (`trading_graph.py:167`) → `_run_graph()` (`:373`) → `self.record_decision(...)` (`:400`) → `return ..., run_rating(...)` (`:405`).
- **CLI:** `cli/run.py` does **not** call `_run_graph`; after `graph.stream_run(...)` (`:241`) it calls `graph.record_decision(...)` (`:353`) directly.
- **Current signature [CONFIRMED]:** `record_decision(self, company_name, trade_date, final_state)` — it has **no `selected_analysts` parameter**; the selection is available as `self.selected_analysts` (`trading_graph.py:109`), not on `final_state`.
- **Callers [CONFIRMED by code]:** `trading_graph.py:400` (programmatic) and `cli/run.py:353` (CLI) — plus **existing tests** (`tests/test_cli_memory_log.py` `:29/:37/:190`, `tests/test_memory_log.py` `:966`) that assert current behaviour and the current signature; backward compatibility (T-20) must preserve these.

**Member A's architecture decision (direction only, not coding approval) [CONFIRMED direction]:** `record_decision()` is the **shared completion boundary** at which the single authoritative Gate evaluation must occur — **before** state logging, persistence, rating return, or final publication. There must be **exactly one** authoritative evaluation per completed execution, and the Graph and CLI **must not independently invoke the checker again**. A shared completion helper (called by/from `record_decision()`) may be proposed if necessary.

**Consequences to be verified by C [pending C confirmation]:** all current callers of `record_decision()` (incl. tests), its function signature and return-value compatibility, whether/how `selected_analysts` reaches the boundary, the exact implementation mechanism (inline vs a shared helper), and whether the CLI’s post-stream `final_state` is complete/identical to the programmatic path’s at `record_decision()`.

> **Baseline note:** facts above are from `origin/main` `d36a677` (this branch's base). The O6/O2-integrated baseline must be re-verified by C after O6 F identity-binding lands and after later merges, before O4 CLI line-level scope is fixed (see §I).

**Required properties of the single authoritative design:**
- **One designated authority:** exactly one evaluation is authoritative per completed execution; every published surface derives its rating from that same `effective_rating`; no consumer recomputes from raw `final_rating`/`final_trade_decision`.
- **No second authoritative evaluation:** Graph and CLI must not each call `check_evidence()` authoritatively; any incidental `check_evidence()` call elsewhere is diagnostic-only and must not drive publication.
- **Order:** the Gate runs **before** `_log_state`/persistence, before the rating return value is fixed, and before any authoritative CLI display/report publication.
- **No publication bypass:** every authoritative publication point (Graph return `:405`; `record_decision` `:360`; CLI display/reports `:380`/`:388`; reporting/HTML/memory readers) observes only the gated effective rating. Any new publication path must route through the same boundary (fail-closed if it cannot).
- **Checkpoint/resume:** a resumed run that reaches completion must perform the single authoritative gated evaluation on its finalized state before publication (see §K.2). A partial/interrupted run that does **not** reach authoritative publication must publish no authoritative rating (existing behaviour — it skips `record_decision` on mid-stream failure).

### B.1 Proposed `record_decision()` contract — **[PROPOSED; EXACT INTERFACE PENDING C CONFIRMATION]**

The current signature `record_decision(self, company_name, trade_date, final_state)` is **not** proposed to change in a way that breaks the two production callers or the existing tests; any change is **pending C confirmation**. The proposed **behavioural contract** at this boundary:

1. **Inputs:** receives `final_state` (complete finalized run state). `selected_analysts` is available on the graph instance (`self.selected_analysts`, `trading_graph.py:109`) — whether the Gate reads it from `self`, from an argument C adds, or from a shared helper is **pending C**.
2. **Exactly one authoritative evaluation per completed execution:** one `check_evidence(final_state, selected_analysts)` call determines the published rating; Graph/CLI do not re-invoke authoritatively.
3. **Capture `original_rating` before any Gate-driven overwrite:** read the pre-gate rating (Stage 1 precedence: `final_rating` else parsed body) into `original_rating` **before** step 4.
4. **Set `final_rating = gate.effective_rating` and `effective_rating = gate.effective_rating`.**
5. **Preserve `final_trade_decision` unchanged** (bytes; FR-12).
6. **`GateResult` runtime availability:** `gate` (verdict, effective rating, per-item statuses, `reason`) is available at the boundary in-memory for diagnostics and integration tests — **no full durable persistence required**; exact availability/return shape pending C.
7. **State logging + memory persistence only after Gate evaluation:** `_log_state(...)` (`:362`) and `memory_log.store_decision(...)` (`:368–371`) run **after** the Gate and persist the **effective** rating; they must not run before, nor use the ungated original.
8. **Return value & backward compatibility:** the boundary returns so the Graph return (`_run_graph` `:405`) and CLI post-`record_decision` display read the gated effective rating. If `record_decision` currently returns `None` (it does — no return), any new return value must be **additive/back-compatible** for the CLI caller and tests — **pending C**.
9. **Error propagation:** invalid Analyst configuration raises `ValueError` from `check_evidence` and **propagates** (aborts publication) — not converted to `REVIEW` (see §G).

- Then the Graph return path (`_run_graph` `:405`) and the CLI post-`record_decision` display read the gated effective rating; they must **not** re-invoke the checker.
- **Whether this lives inline in `record_decision` or in a shared completion helper, and the exact interface/signature change (if any), is PENDING C CONFIRMATION.** Signature/return compatibility (T-20) must be preserved; existing callers/tests must not break.

### B.2 CLI path (`cli/run.py`) — **[PROPOSED; C-owned shared edit]**
- **Verified:** the CLI reaches publication via `stream_run` (`:241`) + `record_decision` (`:353`); since `record_decision` now carries the single authoritative Gate (§B.1), the CLI **consumes** the gated result from there and does **not** call `check_evidence()` again.
- The CLI must not display PM rating/text as approved before the Gate. Buffer PM text (B1, §D) and publish the effective rating **after** `record_decision` returns the gated state.
- Result drives the final rating display (`:380` region), report sections, and reports.

**Invariant [CONFIRMED, FR-07/INV-03]:** one authoritative Gate evaluation per completed execution at the `record_decision` boundary; no Graph/CLI second authoritative call; no raw PM Buy/Sell published as approved before the Gate completes; no publication path bypasses the gate.

---

## C. S2 — Rating propagation & `original_rating` field — **[approved field name; batch behaviour PROPOSED]**

**Contract [CONFIRMED, `development_contract.o4.state_rule`]:** *preserve `final_trade_decision` bytes; set `final_rating` and `effective_rating` to the effective value on finalized state; retain the original rating separately for diagnosis.*

**Approved field name [CONFIRMED, Member A decision]:** the separate diagnostic field is **`original_rating`**.

**New-execution rating contract [APPROVED behaviour, Member A]:**
For a newly completed execution, at the shared completion boundary (§B.1), in this order:
1. **Capture the pre-gate original rating into `original_rating` BEFORE modifying `final_rating`.**
2. `final_rating = gate.effective_rating`.
3. `effective_rating = gate.effective_rating`.
4. `final_trade_decision` **unchanged** (byte-preserved; FR-12).
5. Rating-conflict diagnostics stay in the runtime **`gate.reason`** (not a separate durable field).
6. **Full durable persistence of the full `GateResult` is NOT required for this batch.**

**Safeguards against repeated completion processing [APPROVED intent; exact mechanism to C]:**
- **Never overwrite `original_rating` with an already-downgraded `effective_rating`.** If `original_rating` is already set for this execution, do not re-capture from a `final_rating` that has been set to the effective value (that would record `REVIEW` as "original"). Capture must happen exactly once, before `final_rating` is mutated.
- **Never treat stale Gate fields from a prior checkpoint as authorization for a new completed publication.** A resumed/restored state may carry `effective_rating`/`original_rating`/`final_rating` from a previous partial run; these must not be interpreted as a valid gate decision for a new completed publication. Re-evaluation at the completion boundary determines the new authoritative rating. **Merely finding `effective_rating` in state does NOT prove the Gate ran for the current completion.**
- **Legacy historical-state read compatibility preserved** (consumers can still read old states lacking `effective_rating`/`original_rating` via `run_rating` semantics) **without allowing an ungated *new* publication** — reading history is fine; publishing a new run without the Gate is not.

*(Full repeated-completion / checkpoint / resume rules: see §K.2.)*

**Capture when sources conflict or are absent [PROPOSED; representation to A/C/C]:**
- **Precedence (from Stage 1):** pre-gate rating = `final_rating` if present, else rating parsed from `final_trade_decision` (`_resolve_original_rating`).
- **Conflict** (`final_rating` and parsed body both present and disagree): Stage 1 yields `error_kind="rating_conflict"` → effective `REVIEW`; conflict detail is preserved in `gate.reason`. Whether `original_rating` records the primary source, both sources, or a conflict marker is **pending A/C/C** (do not invent a representation).
- **Absent** (neither source parses): pre-gate is the `REVIEW` sentinel; `original_rating` must distinguish "absent/REVIEW sentinel" from "downgraded from a real rating" — **encoding pending A/C/C**.

**Consumer rule [CONFIRMED, FR-16/INV-01]:** after the Gate, `effective_rating` is the single authoritative rating for final return, reporting, persistence, and CLI publication (S2 keeps `final_rating == effective_rating`). Reporting/HTML/memory/CLI read the effective rating, not the ungated original. `original_rating` is diagnostic only. Stage 1's pure checker is unchanged.

---

## D. B1 — CLI pre-publication buffering — **[PROPOSED / CONFIRMED mechanism]**

**Policy [CONFIRMED, `o4.publication`]:** buffer PM text in the CLI; display only after the Gate; if `REVIEW`, any preserved body is labelled **unapproved original content**, never an approved recommendation.

**Proposed CLI changes [PROPOSED], `cli/run.py` — BOTH pre-gate areas must buffer/suppress:**
- **Area 1 — Portfolio Manager message / display area:** messages streamed at `:249–251` that carry PM decision text (and any PM status/message) must not imply an approved rating pre-gate.
- **Area 2 — Portfolio Manager decision / report section:** the `"final_trade_decision"` report section written from streamed chunks at `:310–334` (incl. `"### Portfolio Manager Decision\n{judge}"` at `:333`) must not be committed as an approved section pre-gate.
- **Both areas** buffer or suppress authoritative decision content **before** the Gate executes; after `record_decision` returns the gated state, publish with the effective rating. When `REVIEW`, the preserved body is labelled **non-authoritative**.
- Replace the current `is_review(run_rating(final_state))` check at `:380` with an effective-rating–based, **cause-neutral** REVIEW message (do not leak internal `reason` verbatim to end users unless A/C decide otherwise).
- **Exact insertion points pending A/C / C verification.**

**Cross-surface non-authoritative labelling — ALL enabled rendered outputs [CONFIRMED intent, FR-13]:**
When the effective rating is `REVIEW`, any preserved Buy/Sell text from `final_trade_decision` must **not** appear as an approved recommendation on any enabled rendered output:
- **CLI:** preserved body, if shown, carries an explicit unapproved/non-authoritative label; no approved Buy/Sell headline.
- **Full Markdown report** (`reporting.write_report_tree`): decision component labelled non-authoritative; the "Rating:" header shows `REVIEW`, not the raw Buy/Sell.
- **Standalone `decision.md`** (the PM decision artifact emitted by `write_report_tree`/report parts): same non-authoritative labelling; must not present the raw Buy/Sell as the approved rating.
- **HTML report** (`report_html.render_report`, when `html=True`): rating shown as `REVIEW`; preserved body labelled non-authoritative.

**Observable assertions [PROPOSED] (per rendered output, when enabled):**
- `"REVIEW"` appears as the authoritative rating for the run;
- the raw `final_trade_decision` Buy/Sell token is **not** presented as the run's approved rating (no e.g. "Rating: Buy" for a REVIEW run);
- if the preserved body is rendered, its text is accompanied by the non-authoritative label (label string pending A/C, §J);
- `final_trade_decision` bytes in state are unchanged (byte-identical), independent of rendering.

---

## E. REVIEW & non-authoritative output rules — **[CONFIRMED intent]**

- Missing required evidence → `effective_rating = REVIEW`; every enabled surface shows `REVIEW`.
- Checker recoverable failure → `REVIEW` + diagnostic reason preserved at the runtime result (not necessarily user-facing verbatim).
- Rating conflict (FR-16/INV-05) → `REVIEW` + conflict reason.
- Pre-existing `REVIEW` never upgraded.
- Preserved `final_trade_decision` body on `REVIEW` is clearly labelled unapproved original content (FR-13) on **every** enabled rendered surface (CLI, Markdown, HTML) — see §D observable assertions.

**CLI display order [PROPOSED by D/C coordination — NOT an approved A/F agreement; final placement/wording pending A/C]:** the proposed relative order of post-analysis output is:
1. **completion notice** (e.g. "Analysis Complete!");
2. **O4 REVIEW warning if applicable** (when effective rating is `REVIEW`);
3. **elapsed time** summary;
4. **O6 statistics summary**;
5. **report options** (save/show/HTML prompts).

The **completion notice must never imply an approved trade recommendation** — it states only that the analysis completed. The O4 REVIEW warning (step 2), when applicable, is the first place a rating status is communicated, and it should precede elapsed/O6/report-options. This ordering is a **D/C proposal for coordination**, not verified A/F approval evidence; exact integration placement and wording are **pending A/C** (§J). A CLI relative-order test is specified in the companion test plan.

**Runtime `GateResult` availability [PROPOSED, no unapproved persistence]:** integration tests need to observe the runtime `GateResult` (verdict, effective rating, per-item statuses, diagnostic `reason`) **without** the plan mandating durable persistence of the full structured verdict (not required in v1). Proposed: the runtime `GateResult` is available at the Gate's capture point in-memory (e.g. returned from the gate helper / held on the finalized state for the run) so tests and the CLI can read `verdict`/`effective_rating`/`reason` during the run; tests may capture it via a seam (returned value or an injectable observation hook) rather than requiring it be written to disk. What, if anything, is persisted is a §J decision; this plan does **not** require persisting the full structured verdict.

---

## F. Reporting / HTML / Memory compatibility — **[PROPOSED]**

- `reporting.py` `_header()` (`:26`) and `write_report_tree()` (`:92`): read effective rating; keep signatures **additive-only** (NFR-05 / T-20).
- `report_html.py` (`:251`): read effective rating when a decision is present.
- `memory/log.py` `store_decision()` (`:32`): persist effective rating (caller already passes `rating=` from `record_decision`; after G1 that value becomes effective). Fallback `parse_rating` (`:56`) behaviour preserved for legacy states.
- Durable persistence of the *complete structured verdict* is **not required** in v1 (Member A); only enabled rating outputs must stay consistent (NFR-06, T-21).

---

## G. Unknown Analyst configuration failure handling — **[CONFIRMED behaviour, to be wired]**

- Stage 1 `check_evidence` raises `ValueError` for an unknown analyst key / empty selection, **before** the recoverable handler (Stage 1 T-18 verified).
- Stage 2 wiring must let that `ValueError` **abort authoritative publication** (FR-15/INV): the run must not be reported as a normal `REVIEW`, and no authoritative rating is published. The CLI must surface a clear error and not offer reports as a completed approved result.
- Must **not** be caught by the recoverable-failure path.

---

## H. Proposed shared-file modification scope — **[PROPOSED; exact scope SUBJECT TO A APPROVAL + C VERIFICATION]**

> These files/edits are **proposals**, not authorized scope. Per §I, C owns shared edits; A approves scope; exact lines pending C's re-verification on the latest main. `effective_rating` is the approved state field; `original_rating` is the approved diagnostic field name (§C).

| File | Proposed change |
|---|---|
| `tradingagents/graph/trading_graph.py` | Single authoritative Gate at/around `record_decision` (`:359`) **before** `_log_state` (`:362`) and `store_decision` (`:368–371`); apply S2 `original_rating`/`final_rating`/`effective_rating`; Graph return (`:405`) reads effective rating (no second call). Exact mechanism (inline vs helper) to C. |
| `tradingagents/agents/state.py` | Add `effective_rating` + **`original_rating`** fields (approved names). |
| `cli/run.py` | B1 two-area buffering (PM message area `:249–251` + decision/report section `:310–334`); consume gated result from `record_decision` (`:353`); effective rating display (`:380`); cause-neutral REVIEW message; reports (`:388`). Exact points to C. |
| `tradingagents/reporting.py` | Read effective rating (`:26`, `:92`); additive-only; standalone `decision.md` labelling. |
| `tradingagents/report_html.py` | Read effective rating (`:251`); non-authoritative labelling. |
| `tradingagents/memory/log.py` | Persist effective rating (`:32`). |

**Possible D-owned additive helper [PROPOSED, A/C opt-in]:** a small pure `apply_gate(state, selected_analysts) -> (new_state, GateResult)` in `evidence_gate.py` or a new module, so shared files contain minimal glue. Not assumed approved.

---

## I. Responsibilities, ownership, and cross-feature coordination — **[mixed: see categories]**

**Ownership — explicitly categorized:**
1. **Existing governance + A's confirmed shared-ownership direction [CONFIRMED]:** C is the sole editor of shared `cli/run.py`, `trading_graph.py`, and rating-output wiring (per `A-Requirements-Decisions.md` Integration/CI row, reiterated by Member A); A coordinates and reviews; B/D/F provide isolated modules + tests, then C integrates in one sequence.
2. **Stage 2 exact file modification scope [PROPOSED — still subject to approval]:** the files in §H are *proposed*; they are not authorized until A approves scope and C confirms the interface.
3. **D's isolated O4 contract + offline tests [CONFIRMED ownership]:** D owns `tradingagents/agents/evidence_gate.py` (Stage 1, merged) and O4 offline tests; D does **not** edit shared files.
4. **F's test/CI approval responsibilities [CONFIRMED]:** F owns default-pytest collection, the six CI gates, network-guard proof, and the T-16 harness; F confirms the mandatory test set.

- **D:** maintain Stage 1 checker; author Stage 2 offline tests/fixtures; optionally an additive pure helper (§H) if A/C permit.
- **C:** verify callers/signatures/compatibility (§B.0), perform all shared-file edits in one reviewed sequence, sequence with O6/O2 CLI changes.
- **F:** collection/CI/T-16 harness + mandatory-case confirmation.
- **A:** approve architecture + final execution plan; resolve §J.

**Cross-feature coordination — latest state [based on `origin/main` `d36a677`]:**
- **O6 prerequisite (Member C's review requirement) [CONFIRMED sequencing rule]:** Before any O4 Stage 2 CLI shared-file edits:
  1. **First complete the O6 F identity-binding requirement** (O6-FR-01) **and C's CLI joint verification**.
  2. **Obtain a traceable O6 verification commit/evidence.** *(The exact O6 commit SHA is NOT known here and must not be invented; C/F supply it.)*
  3. **Re-verify the current `main` after O2 PR #16 and subsequent merges.**
  4. **Use the confirmed O6/O2-integrated baseline for O4 CLI changes.**
  5. **Member C remains responsible for shared integration code.**
  - **The O6 prerequisite is NOT equivalent to O4 Stage 2 coding approval** — it is a sequencing prerequisite; O4 Stage 2 still requires C interface confirmation → F test approval → A execution-plan approval.
- **O6 — merged infrastructure vs pending CLI:** O6 statistics infrastructure is merged (`cli/stats_handler.StatsCallbackHandler` in `cli/run.py`; O6 PRs #11/#15). **O6 F identity-binding / CLI rev.5 disclosure-isolation (TC-O6-12/14) is NOT assumed merged/passed** — no O6 verification evidence is claimed. C must supply the traceable O6 verification commit before O4 CLI edits.
- **O2 PR #16 [merged to `origin/main` `d36a677`]:** added **`tradingagents/repro/manifest.py`** (isolated `build_manifest`/`write_manifest`), **not yet wired** into `cli/run.py`/`trading_graph.py` on `d36a677`. Per `A-Requirements-Decisions`, O2 will write `manifest.json` **at run start** in `cli/run.py`, with **manifest failure not altering O4's gated result** (visible provenance-failed warning, no success claim). When O2's CLI wiring lands, C must reconcile O2 run-start manifest writing with O4's completion-boundary Gate and B1 buffering.
- **Ordering rule:** O4 CLI shared-file edits occur only after (a) the O6 prerequisite above is satisfied with traceable evidence, (b) C re-verifies the O6/O2-integrated `main`, (c) C confirms the shared completion interface + compatibility, and (d) F jointly verifies O6 CLI before O4 CLI edits.

---

## J. Remaining technical confirmations (C) and approvals (A/F)

> **Resolved by Member A (do not re-open):** (a) `original_rating` is the approved field name; (b) the S2 new-execution contract order (capture→set `final_rating`→set `effective_rating`→preserve bytes; conflict in `gate.reason`; no full durable `GateResult`); (c) the single-authoritative Gate at the shared completion boundary (`record_decision`), no independent Graph/CLI second evaluation; (d) `Should` latency non-blocking by default.

**Pending C (shared-file integration owner) — exact interface is PENDING C CONFIRMATION:**
1. Confirm the `record_decision()` **contract/signature** and all current callers incl. tests (`trading_graph.py:400`, `cli/run.py:353`, `tests/test_cli_memory_log.py`, `tests/test_memory_log.py`); decide whether the signature changes or a shared helper is added, keeping return-value compatibility (currently returns `None`).
2. Confirm how `selected_analysts` reaches the boundary (`self.selected_analysts` vs a parameter).
3. Confirm the exact implementation mechanism: inline in `record_decision` vs a shared completion helper.
4. Confirm `GateResult` runtime availability/return shape to Graph/CLI/tests (no full durable persistence).
5. Confirm `original_rating` capture point + encoding for **conflicting** / **absent** sources (§C); confirm `original_rating` not overwritten by a prior REVIEW.
6. Confirm effective-rating persistence shape in `_log_state` JSON (add `effective_rating`/`original_rating` fields?) — with B for invariant schema.
7. Confirm B1 two-area insertion points (PM message area + decision/report section) — §D.
8. Confirm repeated-completion / checkpoint / resume / legacy-stale-field rules and re-evaluate-on-completion behaviour — §K.2.
9. **O6 prerequisite:** supply the traceable **O6 F identity-binding verification commit/evidence**; re-verify the O6/O2-integrated `main` after O2 PR #16 and later merges; reconcile O2 run-start manifest and O6 CLI with O4 CLI edits (§I). *(No O6 SHA invented; joint verification not claimed.)*

**Pending A/F:**
8. **A:** approve the updated Stage 2 Execution Plan (final).
9. **F:** approve the Stage 2 Test Plan + confirm the mandatory test set and parameterized subcases; joint verification with C before CLI edits.
10. **A + F:** whether the `Should` (≤10 ms) latency target may ever be CI-blocking (default: non-blocking).
11. Non-authoritative label wording + cause-neutral REVIEW message + CLI display-order placement/wording — A/C.
12. Unknown-config abort UX in CLI — A/C.

---

## K. Rollback & regression risks — **[PROPOSED]**

### K.1 Risks
Pre-gate CLI leak (T-23); multi-surface inconsistency; unknown-config silently downgraded; buffering UX regressions; conflict masking a valid rating; `cli/run.py` line drift vs O6; display-order/O6-stats interaction.

### K.2 Repeated completion, checkpoint / resume — **[PROPOSED rules; C to confirm]**

**Context [CONFIRMED current behaviour]:** `_run_graph` supports resume via `checkpoint_thread_id` + `checkpoint_input(...)`; `clear_checkpoint_on_success(...)` runs after `record_decision`; `record_decision` is **skipped on mid-stream failure** (checkpoint kept for resume).

**Proposed rules for the Gate at the `record_decision` boundary:**

1. **Repeated `record_decision()` within one logical completed execution** (e.g. accidental double call, or programmatic + CLI on the same run): the Gate must not publish twice. The authoritative evaluation/persist is idempotent for a single completed execution — the second call must not create a second authoritative publication or a second memory/state persist. *(Exact mechanism — an invocation guard/flag, or C structuring callers so the boundary runs once — pending C.)*
2. **`original_rating` never overwritten by a previously downgraded REVIEW:** once `original_rating` is set for the execution, do not re-capture from a `final_rating` that a prior Gate already set to `effective_rating` (that would record `REVIEW` as "original"). Capture occurs once, before the overwrite.
3. **No duplicate authoritative publication / persistence:** state log and memory persist exactly once per completed execution, using the effective rating.
4. **Interrupted execution that has not completed:** if the run does not reach authoritative publication, publish **no** authoritative rating and do **not** persist a gated decision (existing skip-`record_decision` behaviour preserved); the checkpoint may be retained for resume.
5. **Checkpoint resumed to successful completion:** the resumed run performs exactly one authoritative gated evaluation on its finalized state before publication (same invariant as fresh).
6. **Legacy checkpoint data with stale `final_rating` / `effective_rating` / `original_rating`:** must **not** be treated as a valid gate decision for a new completion. Presence of `effective_rating` in restored state does **not** prove the Gate ran for the *current* completion. The boundary re-evaluates on the current finalized state; historical/legacy values are read for display/back-compat only.
7. **Historical-state reading vs new authoritative publication:** reading old states (lacking `effective_rating`/`original_rating`) remains supported via `run_rating` semantics, but that must **not** enable an ungated **new** publication.
8. **Do not assume** fresh and resumed paths are implemented identically; exact Gate placement relative to resume/checkpoint clearing is **pending C**.

**Observable tests for these paths [see test plan]:** repeated-call idempotence (single authoritative publication/persist); `original_rating` not overwritten by a prior REVIEW; interrupted → no authoritative rating; resumed-to-completion → exactly one gated evaluation; legacy stale-field state → re-evaluated, not trusted; equivalent wording errors checked.

### K.3 Rollback / containment
Rollback/containment [CONFIRMED policy direction]: Gate is fail-closed with no production bypass toggle; pre-merge rollback = revert the integration commit; any post-merge rollback/disable affecting the Gate must follow an A/C-approved containment strategy + ADR preventing silent ungated publication; no rollback may publish a rating the Gate would downgrade.

### K.4 Regression controls — **[PROPOSED]**
- **T-20 backward compatibility extended (see test plan §T-20):** cover the **actual gated paths** (Graph return, `record_decision`, CLI display, reports, HTML, memory) and relevant **legacy/checkpoint** behaviour (states without `effective_rating`, checkpointed/older states handed back unchanged), not only signature diffs. `run_rating` semantics for legacy states preserved; default `pytest -q` green.
- **Mandatory collection (see test plan §13):** all mandatory Stage 2 tests and their parameterized subcases must be collected, executed, and passed for final safety acceptance — no unexpected skips/xfails/errors; a missing mandatory node blocks acceptance.

---

## L. Governance & approval workflow (Member A's required order) — **[CONFIRMED order; no step skipped]**

1. **D** revises and shares the **v0.4** plans (this document + companion test plan).
2. **C — O6 prerequisite first:** complete the **O6 F identity-binding** requirement + C's CLI joint verification, produce a **traceable O6 verification commit/evidence**, and re-verify `main` after O2 PR #16 + later merges. *(This is a sequencing prerequisite, NOT O4 Stage 2 coding approval.)*
3. **C** confirms the shared completion interface, compatibility, O6/O2-integrated baseline, and assigned file scope (§J items 1–9). Exact interface **PENDING C CONFIRMATION**.
4. **F** re-reviews the Stage 2 Test Plan, verifies mandatory cases, and records test approval.
5. **A** formally approves the updated Stage 2 Execution Plan.
6. **Only after** all required approvals (and the O6 prerequisite evidence) may approved Stage 2 code implementation begin.

Additional prerequisites (still required, do not bypass):
- Record a completed Stage 2 Test Approval entry (per `docs/test-approvals/TEMPLATE.md`) with real comment links/timestamps before the first Stage 2 code edit.
- A read-only OpenCode Stage 2 execution plan approved before the first code edit (D9).
- AI-use log + redacted session evidence maintained (REQ-GOV-06).

**Member C's v0.3 review comments are architecture/interface feedback, NOT coding approval. This document records no approval and authorizes no code.**
