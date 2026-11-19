# O4 Stage 2 — Implementation Readiness Note (D-owned offline tests)

Status: **implementation-readiness record** for the D-owned Stage 2 offline test batch. This note does **not** approve or claim Stage 2 code/CI/acceptance. Shared production edits are Member C's; this batch is Member D.

> **Current PR #24 CI (at commit `4c8469d`):** 6/6 checks passed (success) — run #109 https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44525823121 . The C-owned `last_completion` production contract is **NOT YET LANDED**; tests depending on it are withheld until it exists.

## Baselines

| Item | Value |
|---|---|
| Actual `main` baseline | `5cdd7589cc73817133a7ca73cf768fc02d0cd19a` (merge of PR #22, O5) |
| Implementation branch | `feature/o4-stage2-tests` (created from `5cdd758`) |
| Approved contract baseline (planning) | `6275725796e618f15d4794ddc61526963bb41c35` (Stage 2 v0.6 plans) |
| Requirements registry | `docs/req/requirements.yaml` (PR #2 `4f87e29f…`) |

## Approvals (original GitHub evidence — not invented)

| Reviewer | Role | Evidence | Time (UTC) |
|---|---|---|---|
| Member C | shared-interface confirmation | https://github.com/Caicys297/TradingAgents-CS5351/pull/17#issuecomment-7008779473 (bound `6275725`) | `2026-11-19T12:14:12Z` |
| Member F | pre-implementation test design | https://github.com/Caicys297/TradingAgents-CS5351/pull/17#pullrequestreview-5974514410 (supplements `5971672933`, `5972448586`) | `2026-11-19T11:55:11Z` |
| Member A | pre-implementation execution scope (also the D9 pre-code execution-plan approval per A's review text) | https://github.com/Caicys297/TradingAgents-CS5351/pull/17#pullrequestreview-5973684411 | `2026-11-19T10:56:49Z` |

Full record: `docs/test-approvals/O4-Stage2-Evidence-Gate.md` (Stage 1 record `O4-Evidence-Gate.md` unchanged).

## Scope

**D-owned (this branch):** O4 **offline** integration/benchmark/audit/lifecycle tests under `test/offline/`, deterministic fixtures, Gate observation assertions; optional additive pure helper in `evidence_gate.py` **only if** A/C permit (not assumed here).

**C-owned shared production (NOT touched here):** `tradingagents/graph/trading_graph.py`, `tradingagents/agents/state.py`, `cli/run.py`, `tradingagents/reporting.py`, `tradingagents/report_html.py`, `tradingagents/memory/log.py`. **Excluded by A:** `cli/display.py`, new files beyond the six, public API changes, automatic CLI retry.

## Planned offline test mechanism

- Default `pytest -q` collection (`testpaths` includes `test/offline`); network-blocked by `test/offline/conftest.py::_no_network`; **not** `integration`-marked.
- Real `check_evidence()` production entry point; deterministic synthetic states; isolated `tmp_path` for any artefact writes.
- D does **not** invent a Guard/GateResult observation API and adds **no** fake production seams. Tests that observe the runtime contract will read the **confirmed read-only `Graph.last_completion`** (see the contract below) — **only after** C's implementation lands.

## D9 pre-work record (per Member A review `5973684411`)

- **Actual main/branch SHA:** `5cdd758…` / branch `feature/o4-stage2-tests` from `5cdd758…`.
- **Chosen mechanism:** D writes **only** conformance/independent tests in this batch; shared-mechanism choices (execution-identity guard, observation seam, buffering) are C's and will be recorded in C's shared-integration PR.
- **O2 `cli/run.py` full ordering (confirmed contract, not implemented here):** reserve directory **before** execution → Graph/Stream → **Gate** → **State Log** → **Memory** → **report-saving decision** → **single manifest write**. A state-log write or close failure **prevents finalization**.

## O6 CLI verification basis — **recorded as C-provided evidence (NOT tests executed by D)**

Member C confirmed the O6 CLI verification basis:

- **O6 CLI PR #20 merged**; merge commit **`e4b6f9ac625f39579635c840aed98ab8dfefdaf9`**.
- Head CI: https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44447747676
- Merge CI: https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44450441456
- C reported **three relevant test groups rerun on `main` `5cdd758`, 22 passed**.

> Provenance: the above is **C-provided verification evidence** (recorded verbatim as reported), **not** test results produced by Member D. D has not independently re-executed O6's suites.

## Confirmed O4 execution-lifecycle observation contract (from Member C) — **production NOT YET LANDED**

Member C confirmed the concrete execution-lifecycle observation contract. This is a **contract description**; the C-owned production implementation of it is **NOT YET LANDED** on `main`. D's tests will target this contract **only after** C's implementation exists.

1. `begin_checkpoint()` **resets** execution records for a new execution.
2. `end_checkpoint()` **clears** the records.
3. The Graph will expose **read-only `last_completion`** containing:
   - `gate: GateResult`
   - `original_rating`: first trusted pre-Gate rating
   - `published`: persistence-completion indicator
4. Within one execution, **repeated completion callbacks reuse** the existing `GateResult` and `original_rating`.
5. A **same-execution retry after persistence failure** must **not** evaluate Gate again.
6. A **repeated completion after persistence success** returns **without duplicate publication**.
7. A **new run or Resume** (even same ticker/date and same Graph instance) **re-evaluates** Gate.
8. `last_completion` is **observable only after Gate completion and before `end_checkpoint()`**; outside that window it returns **`None`**.
9. The current **CLI failure-exit behaviour remains unchanged**.

## Planned T-21 / lifecycle assertions vs C's confirmed contract (no implementation invented)

D's future tests will assert **against the confirmed contract**, once C lands it — mapping (to be implemented after the production contract exists; **no** fake seam):

| Confirmed contract rule | Planned offline assertion target |
|---|---|
| #1 `begin_checkpoint()` resets records | New run on same Graph ⇒ `last_completion` None before Gate; fresh records |
| #2 `end_checkpoint()` clears records | After `end_checkpoint`, `last_completion` is None |
| #3 read-only `last_completion` {gate, original_rating, published} | T-21 reads `gate.verdict/effective_rating/reason`, `original_rating`, `published` |
| #4–6 duplicate reuse / retry no re-eval / no duplicate publish | Gate-invocation-count == 1 for same-execution repeat & persistence-retry; single publish |
| #7 new run / Resume re-evaluate | Count == 1 **per** new execution; reused thread/ticker doesn't skip Gate |
| #8 observable only Gate-done..`end_checkpoint` | `last_completion` non-None inside window; None outside |
| #9 CLI failure-exit unchanged | Failure paths publish nothing (existing behaviour) |

(T-21 lifecycle/`last_completion` assertions remain **prepared, not implemented**, until the C-owned contract lands. No skip/xfail is used to mask them.)

## Batch plan (this branch)

1. **T-16 pure-checker benchmark** — `test_evidence_gate_benchmark.py`: `check_evidence()` only; fixed 4-report fixture; 5 warmups + 30 measured; nearest-rank p95; ≤10 ms threshold **diagnostic/non-blocking**; correctness + fixed-call-count + no-network enforceable; no Graph/CLI/disk/memory/I/O timing.
2. **T-20 compatibility helpers** — independent parts only (existing `record_decision` signature + `None` return must be preserved; Stage 1 Gate behaviour + historical-state readability). Full T-20 integration regression awaits C's shared implementation.
3. **Reusable deterministic fixtures** — complete / missing / Market+News `not_required` / non-empty N/A-unavailable / original REVIEW / pre-Gate original-rating provenance.

## Explicit non-claims

Stage 2 code is not implemented; no CI/acceptance/merge claim. Mandatory integration tests that require C's shared wiring (real Graph/CLI publication, cross-surface, checkpoint/resume via real path, real-time Markdown buffering) are **not executed** in this batch.
