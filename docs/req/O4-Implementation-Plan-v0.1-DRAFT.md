# O4 — Evidence Gate: Implementation Execution Plan

| Field | Value |
|---|---|
| Plan ID | O4-EXEC-v0.2-DRAFT |
| Status | Stage 1 implemented (plan text unchanged); Stage 2 not started |
| Prepared by | Member D |
| Prepared for | Member A (pre-coding review); Member F (test-plan approval) |
| Companion test plan | `O4-Test-Plan.md` (O4-TEST-v0.5; Stage 1 test plan formally APPROVED by Member F) |
| Authoritative requirements | `docs/req/requirements.yaml` — Caicys297/TradingAgents-CS5351, PR #2 merged into `main` |
| Historical review snapshot | `main` `5afb24cf1b48e15e5000ee1365826eebb30d01ae` — **historical review snapshot only**, not the implementation baseline |
| Implementation baseline | Verified `main` `ef1e6a362def6bb24275e6fd3678e4f10d4b1f07` merged into `feature/o4-evidence-gate` (merge commit `c83e737`). Stage 1 first code commit `fefd884`; reviewed Stage 1 HEAD `b1982c4`. |
| PR #2 merge commit | `4f87e29f7a52842dba8272071d2a4a1b527def10` |
| O4 Draft PR | PR #7 (`feature/o4-evidence-gate`) |
| CI provenance | Unified collection + `test/offline/` fixture from **CI PR #1** (merged) |
| Approval | **Member A approved the Stage 1 execution scope; Member F formally approved the O4-TEST-v0.5 Stage 1 test plan. Stage 1 implementation committed (`fefd884`), rating-resolution fix `38dad9b`, reviewed HEAD `b441799`, CI #58 6/6 passed; Member F reviewed the fix pass. Final PR approval pending. Shared Stage 2 integration NOT approved.** |
| Approval history | Member A (PR #7) approved **only the O4-EXEC-v0.1 Stage 1** D-owned scope and fixed G1/S2/B1; Member A **reconfirmed the Stage 1 execution scope** for this plan. This revised **v0.2** document is **not** approved as a whole; the T-07 production-entry clarification does not broaden the approved scope. Member F approved the **T-07 test design** only, not the overall revised test plan. |

> **Version history.** O4-EXEC-v0.1 (prior draft) → **O4-EXEC-v0.2-DRAFT** (this revision: G1/S2/B1 adopted, two-stage scope, NFR-06 v1 durability not required, CI PR #1 provenance, T-16 formal-vs-supplementary). Test IDs remain O4-T-01…T-25.

> **Verification status (read-only).** GitHub API confirms PR #7 open (head `60f1496…`, base `main`); `main` head `5afb24cf1b48e15e5000ee1365826eebb30d01ae`; PR #2 merged (`4f87e29f…`); CI PR #1 merged (files: `pyproject.toml`, `test/offline/conftest.py`). Member A's PR #7 comment (2026-11-16) approved **Stage 1 only** and fixed **G1/S2/B1**. The local workspace is a pre-merge snapshot; line numbers must be re-confirmed on the synchronised implementation baseline. `5afb24cf…` is the historical review snapshot; the implementation baseline SHA is pending local sync.

---

## 0. Scope, constraints, and two-stage model

Documentation-only. No implementation, test code, CI, registry, Git, or GitHub writes are performed by this plan.

**Stage 1 — D-owned, Member A approved (scope; implemented and executed — first code `fefd884`, fix `38dad9b`, reviewed HEAD `b441799`, CI #58 6/6):**
- Create `tradingagents/agents/evidence_gate.py` (pure checker) and `test/offline/test_evidence_gate.py` (offline unit tests).
- Stage 1 tests: O4-T-01…T-07, T-09…T-15, T-17…T-19, T-24, T-25. For **T-07, T-18, T-19 only their checker-level unit portions** (real `check_evidence()` entry point).
- Must NOT modify shared Graph, CLI, reporting, logging, state, or runtime integration files.
- Passing Stage 1 is **NOT** complete O4 safety approval.

**Stage 2 — shared integration, coordinated by Member C, separate A/C approval:**
- Shared files (Graph, CLI, state, reporting, log); integration portions of T-07/18/19; plus T-08, T-16, T-20, T-21, T-23 and cross-surface parts of T-02/T-06/T-14/T-17/T-25.
- Member A: shared-file changes must be aligned with A first.

**Full O4 safety CI obligation before final merge:** canonical mandatory set (O4-TEST-v0.4 §6.6) + all parameterized subcases collected, executed, passed.

O4 v1 boundary: report presence/non-emptiness + rating consistency; not content truth. O4-FR-04 is `Won't` (no sentinel).

---

## A. Architecture and source-code call chain (CONFIRMED from workspace snapshot; re-confirm on the synchronised implementation baseline; `5afb24cf…` is the historical review snapshot)

**Rating generation:** `portfolio_manager_node` (`tradingagents/agents/managers/portfolio_manager.py:23–104`): structured → `final_rating = decision.rating.value`, `final_trade_decision = render_pm_decision(...)` (`:80–83`); fallback → `parse_rating(...)` (`:85–86`); returns both (`:100–104`). `rating.py`: `extract_rating` (`:55`), `parse_rating` (`:96–103`), `run_rating` = `final_rating or parse_rating(final_trade_decision)` (`:106–112`), `is_review` (`:115–117`). `state.py:69–70`.

**Programmatic path:** `_run_graph` (`trading_graph.py:373–405`): `record_decision(...)` (`:400`), `return final_state, run_rating(final_state)` (`:405`). `record_decision` (`:359–371`): `_log_state` (`:362`) + `memory_log.store_decision(..., rating=run_rating(final_state))` (`:368–371`). `_log_state` writes `"final_rating"` (`:464`).

**CLI path:** `run_analysis` (`cli/run.py:99`) streams via `stream_run` (`:241`); **PM text published pre-gate** into report section at `:330–334` and message stream (`:241–300`), before `record_decision` (`:353`). Review message `:380–385`.

**Other readers:** `reporting.py:25–26`, `report_html.py:251`, `cli/run.py:380`, `memory/log.py:56`.

**Selection (not on AgentState):** `TradingAgentsGraph.selected_analysts` (`trading_graph.py:109`); `ANALYST_NODE_SPECS` (`analyst_execution.py:20–46`); unknown key → `ValueError` (`:55–56`).

**Rating read sites:** `trading_graph.py:370,405,464`; `reporting.py:26`; `report_html.py:251`; `cli/run.py:380`; `memory/log.py:56`.

---

## B. Proposed O4 Evidence Gate module and interface

**New module (Stage 1):** `tradingagents/agents/evidence_gate.py`.

```text
check_evidence(state, selected_analysts) -> GateResult
GateResult:
  verdict         : "valid" | "review"
  effective_rating: str                      # original rating when valid; "REVIEW" otherwise
  items           : [{key, status}]          # present | missing | not_required
  reason          : str                      # "" when valid; else diagnostic
  error_kind      : "none" | "evidence" | "checker_failure" | "rating_conflict"
```

- **Pure** (no I/O/LLM/clock) — O4-NFR-01/02 (**Must**).
- Reads `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`, `final_rating`, `final_trade_decision`.
- Required set from `selected_analysts` via `ANALYST_NODE_SPECS`.
- **No `unavailable_convention` parameter** (FR-04 `Won't`). `unavailable` is schema-legal but never emitted in v1.
- **Rating precedence uses the ORIGINAL pre-Gate source values** (before any final-state update): `final_rating` if present, else parsed `final_trade_decision`. If both clearly present and disagree → conflict → `REVIEW` (FR-16). Original `REVIEW` never upgraded (FR-05).
- Unknown analyst/config → raise `ValueError`; abort publication (FR-15). Recoverable failure → `review` + reason (FR-09).

The checker is **Stage 1**; it computes on inputs and returns a `GateResult`. It does **not** mutate state.

**T-07 production-entry fail-closed contract (Member F, resolved):** the production checker itself handles a recoverable internal evidence-processing failure. The Stage 1 test calls the real `check_evidence()` entry point and injects a representative recoverable exception (e.g. `RuntimeError`) at a **real internal evidence-processing computation point** (a production helper defined as part of the checked architecture, monkeypatched to raise). Production logic returns `verdict="review"`, `effective_rating="REVIEW"`, and a non-empty `reason`. A test-only wrapper that catches the exception and builds `REVIEW` is **not acceptable**. Configuration errors (T-18) are a separate contract: they raise `ValueError` and are **not** swallowed by the recoverable handler. This contract is now **implemented and reviewed**: the module exists (Stage 1, `fefd884` + `38dad9b`) and the T-07 fail-closed behaviour, including the rating-resolution path, was reviewed by Member F.

**Requirement priorities (authoritative registry, verified @ main 5afb24cf):** O4-FR-10 **Must**, O4-FR-11 **Must**, O4-NFR-01 **Must**, O4-NFR-02 **Must**; O4-FR-04 **Won't (v1)**; O4-NFR-03 **Should** (p95 <= 10 ms); O4-INV-05 → **O4-T-25**. No "Should"/"Must (proposed)" labels are used for FR-10/11 or NFR-01/02.

---

## C. Integration policy — G1 / S2 / B1 (ADOPTED by Member A, PR #7)

### C.1 Graph integration point — **G1 (ADOPTED)**
The same Gate is invoked on the **Graph completion path** and the **CLI path**, before `record_decision` / external publication. Exact line-level insertion scope is confirmed by A/C in Stage 2 (shared files). Recommendation history: G1 chosen over G2 (`run_rating` purity loss) and G3 (graph redesign).

### C.2 `effective_rating` state representation — **S2 (ADOPTED)**
Final-state behavior:
- `final_rating` = Gate-adjusted effective rating.
- `effective_rating` = the same Gate-adjusted effective rating.
- The **original pre-Gate rating is preserved separately** for diagnosis.
- `final_trade_decision` bytes **unchanged**.

Consequence: after Gate application, `final_rating` is **NOT** the original unmodified rating.

**A/C confirmation required:** the exact **original-rating storage field name/interface** (the approved contract does not fix a name) — do not invent it. Consolidated here with the registry `development_contract.o4.state_rule` ("preserve final_trade_decision bytes; set final_rating and effective_rating to effective value on finalized state; retain original rating separately for diagnosis"), which matches S2.

### C.3 Original-rating preservation
Never mutated by the checker. Retained in the S2 diagnostic field (name pending A/C). `final_trade_decision` untouched (FR-12). Precedence/conflict use the original values (Section B).

### C.4 CLI buffering — **B1 (ADOPTED)**
Buffer PM text (report section `cli/run.py:330–334` and message stream `:241–300`); display only after the Gate; then publish `effective_rating`. If `REVIEW`, any preserved body is labelled **unapproved original content**, never an approved recommendation. Exact insertion points confirmed by A/C in Stage 2.

### C.5 Shared files (Stage 2; C coordinates; A aligned first; D does NOT edit)
| File | Change |
|---|---|
| `tradingagents/graph/trading_graph.py` | Apply Gate (G1) before `record_decision`/return; populate S2 state |
| `tradingagents/agents/state.py` | Add `effective_rating` + original-rating diagnostic field (name pending A/C) |
| `cli/run.py` | Buffering (B1) + cause-neutral review message |
| `tradingagents/reporting.py`, `tradingagents/report_html.py` | Read effective rating |
| `tradingagents/memory/log.py` | Persist effective rating (durable verdict field not required in v1) |

---

## D. Failure-mode handling

| Case | Behavior | Requirement |
|---|---|---|
| Missing/empty required report | `REVIEW`; exact failing set; `error_kind=evidence` | FR-03 |
| Non-empty report with `N/A`/unavailable note | `present`; no downgrade from that text | FR-04 (`Won't`) |
| Pre-existing REVIEW | Never upgraded | FR-05 |
| Recoverable internal evidence-processing failure | Handled by production checker logic → `REVIEW`, reason preserved; Stage 1 verifies checker return; surfaces agree in Stage 2 | FR-09, INV-04 |
| Unknown analyst / unrecognizable config | Contract error → `ValueError` **propagates** (not swallowed into REVIEW); abort publication; not a normal `REVIEW` | FR-15 |
| Rating conflict (original sources) | Downgrade to `REVIEW` with conflict reason | FR-16 |
| Decision body | Bytes unchanged; labelled unapproved when REVIEW | FR-12/13 |

---

## E. CLI buffering and authoritative publication

- No PM Buy/Sell appears approved/tradeable before the Gate (INV-03, FR-07).
- After the Gate, each enabled surface publishes `effective_rating`; preserved body labelled unapproved when `REVIEW` (FR-13).
- Only enabled surfaces compared (NFR-08). Mechanism B1, exact points pending A/C (Stage 2).

---

## F. Implementation steps (dependency order)

**Stage 1 (D-owned; after F approves the test plan):**
1. Implement `evidence_gate.py` (pure checker + `GateResult`).
2. Write `test/offline/test_evidence_gate.py` for Stage 1 unit tests (Section G).
3. Pass Stage 1 mandatory unit portions.

**Stage 2 (after separate A/C approval; C coordinates):**
4. Apply G1 in `trading_graph.py` and the CLI path; implement S2 state (field name A/C).
5. CLI buffering B1 + cause-neutral message.
6. Reporting/HTML read effective rating; memory persistence.
7. Integration tests (T-07/18/19 integration halves; T-08, T-21, T-23).
8. Regression T-20; T-16 (after A/C timing boundary).
9. CI wiring + evidence capture (F).

---

## G. Test mapping — full O4-T-01 … O4-T-25 (Stage tags)

All 25 IDs preserved. Canonical mandatory set: T-02, T-03, T-06, T-07, T-08, T-14, T-17, T-18, T-19, T-23, T-25 (+ all parameterized subcases).

| Test | Stage | Type | Notes |
|---|---|---|---|
| T-01 | S1 | unit | complete evidence preserves rating |
| T-02 | S1/S2 | unit (+cross-surface in S2) | each of 4 reports empty + multi-missing (**mandatory**) |
| T-03 | S1 | unit param | whitespace (4) + empty+whitespace (**mandatory**) |
| T-04 | S1 | unit negative | `N/A`/unavailable text stays present |
| T-05 | S1 | unit | unselected `not_required` |
| T-06 | S1/S2 | unit (+cross-surface S2) | REVIEW never upgraded (**mandatory**) |
| T-07 | S1/S2 | checker-level unit (S1, production entry) + Graph integration (S2) | recoverable failure handled by production checker → REVIEW+reason (**mandatory**) |
| T-08 | S2 | Graph/CLI integration | enabled-surface equality (**mandatory**) |
| T-09 | S1 | unit | keep Sell |
| T-10 | S1 | unit | decision bytes preserved |
| T-11 | S1 | unit | determinism ×100 |
| T-12 | S1 | unit | structured result + reason |
| T-13 | S1 | unit | single-analyst valid |
| T-14 | S1/S2 | unit (+cross-surface S2) | single/multi missing; unselected not flagged (**mandatory**) |
| T-15 | S1 | unit collection | offline import |
| T-16 | S2 | benchmark | registry formal acceptance p95 <= 10 ms |
| T-17 | S1 | unit param | each key absent (**mandatory**) |
| T-18 | S1/S2 | checker-level unit (S1, real `check_evidence()`) + Graph integration (S2) | unknown key → `ValueError` propagated (not REVIEW); publication aborts (**mandatory**) |
| T-19 | S1/S2 | checker-level unit (S1) + CLI/Graph integration (S2) | REVIEW + body unchanged (S1); labelled non-authoritative, no leak (S2) (**mandatory**) |
| T-20 | S2 | regression | baseline unchanged |
| T-21 | S2 | artefact inspection | runtime result; durability not required v1 |
| T-22 | S2/manual | manual | scope review |
| T-23 | S2 | CLI integration | no pre-gate published Buy (**mandatory**) |
| T-24 | S1 | unit boundary | O5 filtered-empty no downgrade; missing news → REVIEW |
| T-25 | S1 | unit | precedence/conflict (**mandatory**) |

Stage 1 mandatory-cases (checker-level unit portions): T-02, T-03, T-06, T-07, T-14, T-17, T-18, T-19, T-25. Stage 1 passing alone is **not** full O4 safety approval.

---

## H. Default `pytest -q` collection and offline network protection (CI PR #1)

- Unified policy: deterministic offline unit + Graph/CLI tests run under default `pytest -q`; `integration` marker reserved for real external services; mocked-dependency Graph/CLI paths are not integration-marked.
- **Provenance (CI PR #1, merged):** `pyproject.toml` `testpaths = ["tests", "test/offline"]`; `test/offline/conftest.py` `_no_network` (directory-scoped, active for non-integration tests).
- No collection/execution evidence exists yet; all commands/node IDs are proposed.

---

## I. Safety CI verification and evidence capture

- Mandatory = canonical set + parameterized subcases; collected, executed, passed; none skipped/xfailed/errored/missing.
- Safety Escape Count == 0 (SE-01…SE-06); missing execution is not a pass.
- Stage 1 discharges only the Stage 1 subset; full set required before final merge.
- Evidence: actual node IDs (incl. parameterized), expected-vs-collected manifest, per-case results, network-guard proof, CI job/command.

---

## J. T-16 performance boundary (Should, p95 <= 10 ms)

- **Formal acceptance (registry):** fixed four-report fixture, **5 warm-up calls, 30 measured calls**, single process, `ubuntu-latest`/Python 3.11, nearest-rank **p95 added latency <= 10 ms (inclusive)**; priority **Should** (non-blocking; never overrides safety).
- **Member F's extended paired A/B plan** (`O4_T16_Performance_Verification_Plan.md` v0.1): **supplementary diagnostic only**, not a replacement for formal acceptance.
- **Boundary:** start = entry into rating processing; end = `effective_rating` ready; `time.perf_counter_ns()`; exclude graph/LLM/IO/render. **Actual Gate invocation point + timing wrapper PENDING A/C (Stage 2).**
- No benchmark executed; no passing result claimed.

---

## K. Risks, rollback, unresolved decisions

**Risks:** pre-gate CLI leak (T-23); multi-reader inconsistency; unknown-config silently downgraded; buffering UX; conflict masking valid ratings; snapshot-vs-main drift.

**Rollback and containment (safety-critical):**
1. Gate is **fail-closed**; no production switch bypasses it.
2. **Pre-merge rollback** = revert the integration commit (removes the change and its gate together during review); recorded in the PR.
3. **Any post-merge rollback/disable affecting the Gate** MUST follow an **A/C-approved containment strategy** + ADR preventing silent ungated publication (keep affected runs non-authoritative, or halt publication).
4. No rollback may publish a tradeable rating the Gate would have downgraded; if containment cannot guarantee this, publication is halted.
5. Rollback/containment events must be logged and reported.

**Resolved:** durable persistence of the complete structured Gate verdict is **not required in v1** (Member A decision); enabled authoritative rating outputs must still remain consistent. Shared logging/`memory` implementation details for persisting the effective rating remain open under Stage 2 while the v1 contract above stands.

**Unresolved (owner):** original-rating storage field name/interface (A/C — not invented); exact G1/B1 insertion line scope (A/C); T-16 Gate invocation/timing boundary (A/C, Stage 2); SE-06 (F/team); invariant schema representation (B); synchronise to the pending implementation baseline (D/A); `5afb24cf…` is the historical review snapshot only.

---

## L. Human approval requirements (Stage 1 satisfied; Stage 2 open)

1. **Member F** — formal approval of the Stage 1 test plan: **DONE** (O4-TEST-v0.5 approved, review `5934877146`, `2026-11-17T08:02:32Z`; Stage 1 fix reviewed pass `2026-11-17T15:20:24Z`).
2. **Members A/C** — Stage 2 shared-integration scope (separate approval; C coordinates, A aligned first). **OPEN.**
3. Confirm original-rating storage field and exact G1/B1 insertion scope (A/C). **OPEN (Stage 2).**
4. Governance artifacts present (Test Approval record, AI-use log, ADR for containment if adopted).
5. **Stage 1 implementation is completed** (first code `fefd884`, fix `38dad9b`, reviewed HEAD `b441799`, CI #58 6/6); **final PR approval pending**. Stage 2 only after (2)–(3). **This document records no Stage 2 approval.**

---

## Appendix — Unverified assumptions

- Line numbers from pre-merge snapshot; re-confirm on the synchronised implementation baseline. `5afb24cf…` is the historical review snapshot, not the implementation baseline.
- G1/S2/B1 adopted from Member A's PR #7 comment (architecture direction, not code-level scope).
- CI PR #1 provenance verified via API (files `pyproject.toml`, `test/offline/conftest.py`).
- O4-NFR-03 target is a requirement value, not a measured result.
