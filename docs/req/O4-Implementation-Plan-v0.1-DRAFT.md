# O4 — Evidence Gate: Implementation Execution Plan

| Field | Value |
|---|---|
| Plan ID | O4-EXEC-v0.1 |
| Status | **DRAFT — NOT approved** |
| Prepared by | Member D |
| Prepared for | Member A (pre-coding review); Member F (test-plan approval) |
| Companion test plan | `O4-Test-Plan.md` (O4-TEST-v0.3, Draft / Approval Pending) |
| Authoritative requirements | `docs/req/requirements.yaml` — Caicys297/TradingAgents-CS5351, PR #2 merged into `main` |
| Merge commit (verified) | `4f87e29f7a52842dba8272071d2a4a1b527def10` |
| PR #2 head commit | `f411763c3d080bddde425c60a7a06d1797913328` |
| Approval | **None claimed.** Member A and Member F have NOT approved any plan. |

> **Verification status.** GitHub API (read-only) confirms PR #2 `state=closed`, `merged=true`, `merge_commit_sha=4f87e29f7a52842dba8272071d2a4a1b527def10`, base `main` (`f3983d68…`), head `f411763…`; `main` head at `4f87e29f…` (2026-11-16). The **local workspace is a pre-merge snapshot**: it is not a Git repository, has no `docs/` or `test/`, and has no `evidence_gate.py`. Line numbers below are from that workspace snapshot and must be re-confirmed on the merged `main` before coding. Where the merged baseline differs, the merged `main` wins.

---

## 0. Scope and constraints

- Documentation-only Draft PR input. **No implementation, no test code, no CI changes, no Git writes** are performed by this plan.
- D-owned files only: `tradingagents/agents/evidence_gate.py` (new), `test/offline/test_evidence_gate*.py` (new).
- Shared files require **A/C approval** before any edit (Section C).
- O4 v1 boundary: presence/non-emptiness of required analyst reports + rating consistency. It does **not** certify report content truth.
- **O4-FR-04 is `Won't` for v1**: no whole-report sentinel recognition. The checker interface therefore has **no** `unavailable_convention` parameter (see Section B).

---

## A. Architecture and source-code call chain (CONFIRMED from workspace source)

**Rating generation**
- `portfolio_manager_node` (`tradingagents/agents/managers/portfolio_manager.py:23–104`): structured output → `final_rating = decision.rating.value`, `final_trade_decision = render_pm_decision(decision)` (`:80–83`); free-text fallback → `parse_rating(final_trade_decision)` (`:85–86`). Node returns both (`:100–104`).
- `rating.py`: `extract_rating` (`:55`), `parse_rating` (`:96–103`), `run_rating` = `final_rating or parse_rating(final_trade_decision)` (`:106–112`), `is_review` (`:115–117`).
- `state.py:69–70`: `final_trade_decision`, `final_rating`.

**Programmatic return & persistence**
- `_run_graph` (`trading_graph.py:373–405`): `record_decision(...)` (`:400`) → `return final_state, run_rating(final_state)` (`:405`).
- `record_decision` (`:359–371`): `_log_state` (`:362`), then `memory_log.store_decision(..., rating=run_rating(final_state))` (`:368–371`).
- `_log_state` writes `"final_rating": run_rating(final_state)` (`:464`).
- `store_decision` tag `[date | ticker | rating | pending]` (`memory/log.py:56–58`).

**CLI path (buffering-relevant)**
- `run_analysis` (`cli/run.py:99`) streams via `graph.stream_run` (`:241`). **PM text is published pre-gate** into the report section at `:330–334` (`update_report_section("final_trade_decision", "### Portfolio Manager Decision\n{judge}")`) and via the message stream (`:241–300`), **before** `record_decision` (`:353`).
- Post-run review message at `:380–385`; `run_rating(final_state)` used there.

**Other readers:** `reporting.py:25–26`, `report_html.py:251`, `cli/run.py:380`.

**Selection source (not on AgentState):** `TradingAgentsGraph.selected_analysts` (`trading_graph.py:109`); mapping `ANALYST_NODE_SPECS` (`analyst_execution.py:20–46`); unknown key raises `ValueError` (`:55–56`).

**Rating read sites:** `trading_graph.py:370,405,464`; `reporting.py:26`; `report_html.py:251`; `cli/run.py:380`; `memory/log.py:56`.

---

## B. Proposed O4 Evidence Gate module and interface

**New module:** `tradingagents/agents/evidence_gate.py` (D authors; no shared edits).

```text
check_evidence(state, selected_analysts) -> GateResult
GateResult:
  verdict        : "valid" | "review"
  effective_rating: str                      # original rating when valid; "REVIEW" otherwise
  items          : [{key, status}]            # status ∈ present | missing | not_required
  reason         : str                        # "" when valid; else diagnostic
  error_kind     : "none" | "evidence" | "checker_failure" | "rating_conflict"
```

- **Pure function** — no I/O, no LLM, no clock (O4-NFR-01/02).
- **Inputs read:** `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`, `final_rating`, `final_trade_decision`.
- **Required set:** derived from `selected_analysts` via `ANALYST_NODE_SPECS`.
- **Status rules (v1 structural):** `present` = non-empty text (including text containing `N/A`/unavailable-source notes — FR-04 `Won't`); `missing` = absent key / empty / whitespace-only; `not_required` = unselected.
- **No `unavailable_convention` parameter.** Sentinel recognition is out of v1 scope; any future sentinel is a separate requirement-change review. `unavailable` is retained only as a schema-allowed status value for forward compatibility, but v1 never emits it.
- **Config error:** unknown analyst key / unrecognizable configuration → raise `ValueError` (consistent with `analyst_execution.py:55–56`); publication aborts (FR-15). Not returned as a normal `REVIEW`.
- **Recoverable internal failure:** return `verdict="review"`, `error_kind="checker_failure"`, reason preserved (FR-09).
- **Rating conflict:** original rating = `final_rating` if present, else parsed body; if both clear and disagree → `REVIEW`, `error_kind="rating_conflict"` (FR-16). Original `REVIEW` never upgraded (FR-05).

Alignment: matches registry `o4` policy block (`requirements.yaml` @ main: required_reports / report_presence / rating_source / checker_failure / publication / state_rule / policy_version `o4-structural-v1`).

---

## C. Integration points and shared files (A/C DECISION REQUIRED — options presented, no decision taken)

The gate must (a) run after the Portfolio Manager and before any authoritative publication, (b) make `effective_rating` the single authoritative value for return, state log, memory log, markdown, HTML and CLI, and (c) not let the raw PM rating reach a surface first.

### C.1 Graph integration point — OPTIONS (pending A/C)

| Option | Where | Pros | Cons |
|---|---|---|---|
| **G1 (recommended minimal)** | In `_run_graph` after graph invoke, before `record_decision` and the return (`trading_graph.py:398–405`); also apply in the CLI path before its `record_decision` (`cli/run.py:353`) | One shared pre-persist gate point; small diff; covers return/log/memory | Requires the same call in the CLI stream merge path; state field needed |
| G2 | Inside `run_rating` (`rating.py:106–112`) so all readers gate by construction | Single choke point for all readers | `run_rating` becomes impure/needs selection config; changes a widely-used pure helper; regressions risk |
| G3 | A dedicated LangGraph node after Portfolio Manager | Graph-native ordering | Larger graph change; violates "no LangGraph redesign" preference (`NFR-07`) |

**Recommendation: G1** (single shared pre-persist gate applied at both programmatic and CLI completion points). **This is a recommendation only; A/C must confirm.**

### C.2 `effective_rating` state representation — OPTIONS (pending A/C)

| Option | Representation | Note |
|---|---|---|
| **S1 (recommended)** | Add `effective_rating` to `AgentState` (`state.py`); keep `final_rating` as the **original** PM rating; keep `final_trade_decision` bytes unchanged | Matches registry `state_rule` ("set final_rating and effective_rating to effective value … retain original separately") — needs A/C to reconcile the registry's exact wording ("set final_rating … to effective value; retain original separately") |
| S2 | Overwrite `final_rating` with the effective value; store original elsewhere (e.g. `original_rating`) | Single value everywhere; loses "original" name; more consumers change |
| S3 | No new field; only mutate what `run_rating` returns | Insufficient: `_log_state` and reports read `final_rating` directly |

**Recommendation: S1** (add `effective_rating`; preserve `final_rating` as original; keep decision bytes). **A/C must confirm and reconcile with the registry `state_rule` wording**, which appears to say `final_rating` itself becomes effective — the two must be made consistent.

### C.3 Original-rating preservation

`final_trade_decision` MUST be preserved byte-for-byte (`FR-12`). Original rating retained for diagnosis (in a field per S1/S2 choice); never mutated by the checker.

### C.4 CLI buffering mechanism — OPTIONS (pending A/C)

| Option | Mechanism | Pros | Cons |
|---|---|---|---|
| **B1 (recommended)** | Hold PM report-section/message writes (`cli/run.py:330–334`, `:241–300`) in a buffer; flush as "unapproved original content" only after gating; print effective rating | No raw Buy/Sell shown as approved pre-gate | Touches CLI streaming; needs careful ordering |
| B2 | Label each PM message "provisional — unapproved" inline, then re-label after gate | Smaller code change | Still displays a direction pre-gate; weaker for INV-03 |
| B3 | Suppress PM text until post-gate entirely | Simplest safety | Loses progress context; may slow perceived UX |

**Recommendation: B1** (buffer, then publish effective rating; label preserved body unapproved when REVIEW). **A/C must confirm** the exact insertion points and whether buffering lives in `cli/run.py` or a shared sink.

### C.5 Shared files requiring A/C approval (D does NOT edit these)

| File | Change | Requirements |
|---|---|---|
| `tradingagents/graph/trading_graph.py` | Apply gate at G1 before `record_decision`/return | FR-07/09/16, INV-03, NFR-08 |
| `tradingagents/agents/state.py` | Add `effective_rating` (S1) or equivalent | FR-12, NFR-06 |
| `cli/run.py` | Buffering (B1) + cause-neutral review message (`:380–385`) | FR-07/13, INV-03 |
| `tradingagents/reporting.py`, `tradingagents/report_html.py` | Read `effective_rating` | FR-07, INV-03 |
| `tradingagents/agents/rating.py` | Only if G2 chosen — otherwise unchanged | (option) |
| `tradingagents/memory/log.py` | Persist effective rating; durable verdict field **pending** (NFR-06) | NFR-06 (pending) |

---

## D. Failure-mode handling

| Case | Behavior | Requirement |
|---|---|---|
| Missing/empty required report | `effective_rating=REVIEW`; exact failing set; `error_kind=evidence` | FR-03 |
| Text mentions `N/A`/unavailable but report non-empty | Status `present`; no downgrade from that text alone | FR-04 (`Won't`) |
| Pre-existing REVIEW | Never upgraded | FR-05 |
| Recoverable checker failure | Fail-closed `REVIEW`, reason preserved, all enabled surfaces agree; distinct from config error | FR-09, INV-04 |
| Unknown analyst / unrecognizable config | Raise `ValueError`; **abort** authoritative publication; not a normal `REVIEW` | FR-15 |
| Rating conflict (`final_rating` vs parsed body) | Downgrade to `REVIEW` with conflict reason | FR-16 |
| Decision body | Bytes unchanged; labelled unapproved when REVIEW | FR-12/13 |

---

## E. CLI buffering and authoritative publication

- No PM Buy/Sell may appear as an approved/tradeable rating before the gate completes (INV-03, FR-07).
- After gating, each enabled surface publishes `effective_rating`; if `REVIEW`, preserved raw body is labelled unapproved original content (FR-13).
- Mechanism and exact insertion points: **pending A/C** (Options B1/B2/B3 in C.4).
- Only **enabled** surfaces are compared (HTML only when `html=True`; memory log only when `memory_log_path` set; etc.) — NFR-08.

---

## F. Implementation steps (dependency order)

1. **A/C confirm** G1 (integration point), S1/registry `state_rule` reconciliation, and B1 (buffering).
2. Implement `evidence_gate.py` (pure checker + `GateResult`) — D.
3. Unit tests — `test/offline/test_evidence_gate.py` (see Section G).
4. Integrate gate at G1 in `trading_graph.py`; add `effective_rating` (A/C).
5. CLI buffering + cause-neutral message (A/C).
6. Reporting/HTML read effective rating (A/C).
7. Offline Graph/CLI integration tests (network-blocked) — Section G/H.
8. Regression (T-20); T-16 instrumentation after A/C timing boundary.
9. CI wiring and evidence capture (F) — Section I.

---

## G. Test implementation mapping — complete O4-T-01 … O4-T-25

All 25 IDs preserved. Mandatory safety set (canonical, per O4-TEST-v0.3 §6.6): **T-02, T-03, T-06, T-07, T-08, T-14, T-17, T-18, T-19, T-23, T-25** including all mandatory parameterized subcases.

| Test | Type | File | Notes |
|---|---|---|---|
| T-01 | Offline unit | `test_evidence_gate.py` | complete evidence preserves rating |
| T-02 | Offline unit (param, **mandatory**) | `test_evidence_gate.py` | each of 4 reports empty + multi-missing; exact failing set |
| T-03 | Offline unit (param, **mandatory**) | `test_evidence_gate.py` | whitespace-only (4) + empty+whitespace multi-missing |
| T-04 | Offline unit (negative/boundary) | `test_evidence_gate.py` | `N/A`/unavailable-source text stays `present`; no downgrade |
| T-05 | Offline unit | `test_evidence_gate.py` | unselected → `not_required` |
| T-06 | Offline unit (**mandatory**) | `test_evidence_gate.py` | REVIEW never upgraded |
| T-07 | Unit + offline Graph integration (**mandatory**) | split | checker failure fails closed across enabled surfaces |
| T-08 | Offline Graph/CLI integration (**mandatory**) | `test_evidence_gate_integration.py` | expected-enabled-surface-set equality, then all `REVIEW` |
| T-09 | Offline unit | `test_evidence_gate.py` | keep `Sell` |
| T-10 | Offline unit | `test_evidence_gate.py` | decision bytes preserved (rendered label proven by T-19/T-23) |
| **T-11** | Offline unit (boundary) | `test_evidence_gate.py` | determinism ×100, no I/O |
| T-12 | Offline unit | `test_evidence_gate.py` | structured result + reason on non-pass |
| T-13 | Offline unit | `test_evidence_gate.py` | single-analyst valid |
| **T-14** | Offline unit (param, **mandatory**) | `test_evidence_gate.py` | single-select missing; multi-select one missing; unselected not flagged |
| **T-15** | Offline unit (collection) | `test_evidence_gate.py` | direct import, no graph/LLM/network |
| T-16 | Benchmark (F) | F harness | p95 <= 10 ms target; see Section J |
| T-17 | Offline unit (param, **mandatory**) | `test_evidence_gate.py` | each key absent; exact failing set |
| T-18 | Unit + offline Graph integration (**mandatory**) | split | unknown key → `ValueError`, publication aborted (not normal REVIEW) |
| T-19 | Unit + offline Graph/CLI integration (**mandatory**) | split | Buy body not approved; preserved + labelled |
| T-20 | Regression (F) | existing suite | gate not wired → unchanged behavior |
| T-21 | Artefact inspection | integration | runtime result; durability documented pending |
| T-22 | Manual scope review | review | not automated |
| T-23 | Offline CLI integration (**mandatory**) | `test_evidence_gate_integration.py` | no pre-gate published Buy; post-gate REVIEW |
| T-24 | Offline unit (boundary) | `test_evidence_gate.py` | O5 filtered-empty alone → `valid`/original; missing selected `news_report` → `REVIEW` with exact failing set `{news_report}` |
| T-25 | Offline unit (**mandatory**) | `test_evidence_gate.py` | precedence (a/b/c/d); conflict → REVIEW with reason |

Every mandatory node ID **and** every required parameterized subcase must be collected, executed, passed; no skip/xfail/error/missing (O4-TEST-v0.3 §6.6/§8/§9).

---

## H. Default `pytest -q` collection and offline network protection

- **Unified policy (Member A):** deterministic offline unit + Graph/CLI tests run under **default `pytest -q`**; `integration` marker reserved for real external services; mocked-dependency Graph/CLI paths are **not** integration-marked.
- **PR #2 config (CONFIRMED from merged baseline):** `testpaths = ["tests", "test/offline"]`; `addopts = '-ra --strict-markers -m "not integration"'`; CI runs `pytest -q`.
- **Network protection (CONFIRMED from PR snapshot, not executed):** `test/offline/conftest.py` `_no_network` is directory-scoped; returns early **only** for integration-marked tests, so it is active for O4 non-integration tests. Must be re-verified on merged `main`.
- **No collection/execution evidence exists yet**; all commands and node IDs are proposed, not run.

---

## I. Safety CI verification and evidence capture

- Mandatory = canonical set + parameterized subcases; collected, executed, passed; none skipped/xfailed/errored/missing.
- **Safety Escape Count == 0** (SE-01…SE-06); missing execution is not a pass.
- Evidence: actual node IDs (incl. parameterized subcase IDs), expected-vs-collected manifest, per-case results, network-guard proof, CI job/command/saved-result location.
- Enforcement is **proposed**, pending F/team; SE-06 pending confirmation.

---

## J. T-16 performance boundary (registry `Should`, p95 <= 10 ms)

- **Target (registry, CONFIRMED):** nearest-rank **p95 added latency <= 10 ms** — fixed four-report fixture, 5 warmups, 30 measured calls, `ubuntu-latest`/Python 3.11; priority **Should** (non-blocking; does not override safety gates).
- **Methodology:** F's `O4_T16_Performance_Verification_Plan.md` v0.1 paired A/B (Path A harness-bypass; Path B real checker). **Sampling-protocol reconciliation (compact registry vs extended A/B) pending F.**
- **Boundary:** start = entry into rating-processing; end = `effective_rating` ready; `time.perf_counter_ns()`; exclude graph/LLM/IO/render. **Actual Gate invocation point + timing wrapper PENDING A/C.**
- No measurement executed; no passing result claimed.

---

## K. Risks, rollback, unresolved decisions

### K.1 Risks
Pre-gate CLI leak (T-23); multi-reader inconsistency; unknown-config silently downgraded to REVIEW; buffering UX regressions; conflict path masking otherwise-valid ratings; divergence between workspace snapshot and merged `main`.

### K.2 Rollback and containment (safety-critical)

A naive "disable the gate" toggle would **silently restore unsafe authoritative rating publication** and is **prohibited**. Rollback rules:

1. The Evidence Gate is **fail-closed by design**; there is no runtime switch that bypasses it in production.
2. **Implementation rollback** (before merge or during review) = revert the integration commit. Because the gate is part of the change, reverting removes the gate **and** restores the known baseline; this is a pre-merge review action only, not a runtime option, and must be recorded in the PR.
3. **Any post-merge rollback or temporary disablement affecting the safety gate** MUST follow an **A/C-approved containment strategy** that prevents silent ungated publication (e.g., the containment keeps `effective_rating = REVIEW` for affected runs, or the event is escalated and the affected runs are quarantined/marked non-authoritative). A containment proposal requires A/C sign-off and an ADR before use.
4. **No rollback** may publish a tradeable rating that the gate would have downgraded; if containment cannot guarantee this, publication is halted rather than downgraded.
5. Rollback and containment events must be logged and reported (not silent).

### K.3 Unresolved decisions (owner)
(1) Graph integration point G1/G2/G3 — **A/C**; (2) `effective_rating` representation S1/S2/S3 and registry `state_rule` reconciliation — **A/C (+B)**; (3) CLI buffering B1/B2/B3 — **A/C**; (4) durable verdict persistence — **A/C**; (5) T-16 sampling protocol — **F**; (6) SE-06 — **F/team**; (7) invariant schema representation — **B**; (8) rebase workspace onto merged `main` — **D/A**.

---

## L. Explicit human approval requirements before coding

1. **Member F** — formal approval of `O4-Test-Plan.md` (O4-TEST-v0.3).
2. **Member A** — formal approval of this execution plan (O4-EXEC-v0.1).
3. **Members A/C** — confirm integration point (C.1), state representation (C.2) + registry reconciliation, and buffering (C.4).
4. Required project governance artifacts present (Test Approval record, AI-use log per `docs/PROJECT_WORKSPACE.md`, ADR for containment if rollback policy adopted).
5. Implementation begins only after 1–4. **This document records no approvals.** Member A and Member F have not approved either plan.

---

## Appendix — Unverified assumptions and pending verification

- Line numbers derive from the pre-merge workspace snapshot; re-confirm on merged `main` (`4f87e29f…`).
- `test/offline/conftest.py` behavior confirmed from PR snapshot only; not executed.
- PR #2 merge state verified via API; no further GitHub write or merge claim is made.
- O4-NFR-03 target (`<= 10 ms`) is the confirmed registry value; it is a requirement target, **not** a measured result.
