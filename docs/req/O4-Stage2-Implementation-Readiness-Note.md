# O4 Stage 2 — Implementation Readiness Note (D-owned offline tests)

Status: **implementation-readiness record** for the D-owned Stage 2 offline test batch. This note does **not** approve or claim Stage 2 code/CI/acceptance. Shared production edits are Member C's; this batch is Member D.

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
- No invented Guard/GateResult observation API; no fake production seams to force integration tests to pass.

## D9 pre-work record (per Member A review `5973684411`)

- **Actual main/branch SHA:** `5cdd758…` / branch `feature/o4-stage2-tests` from `5cdd758…`.
- **Chosen mechanism:** D writes **only** conformance/independent tests in this batch; shared-mechanism choices (execution-identity guard, observation seam, buffering) are C's and will be recorded in C's shared-integration PR.
- **O2 `cli/run.py` insertion order (contract, not implemented here):** (1) reserve output directory **before** Graph execution; (2) write the manifest **once after** analysis + save-selection. *(PR #18 contract; supersedes old run-start wording.)*
- **O6 merged commits:** identity-binding `6a561ab` (PR #19), CLI `e4b6f9a` (PR #20). **Outstanding: C's O6 CLI joint-verification evidence is not yet recorded** — blocks C's `cli/run.py` integration, not this D test batch.
- **Runtime observation seam:** **pending C confirmation.** Lifecycle/CLI integration tests will target C's actual implemented observation mechanism once confirmed; until then they remain prepared/not-executed (no skip/xfail masking).

## Batch plan (this branch)

1. **T-16 pure-checker benchmark** — `test_evidence_gate_benchmark.py`: `check_evidence()` only; fixed 4-report fixture; 5 warmups + 30 measured; nearest-rank p95; ≤10 ms threshold **diagnostic/non-blocking**; correctness + fixed-call-count + no-network enforceable; no Graph/CLI/disk/memory/I/O timing.
2. **T-20 compatibility helpers** — independent parts only (existing `record_decision` signature + `None` return must be preserved; Stage 1 Gate behaviour + historical-state readability). Full T-20 integration regression awaits C's shared implementation.
3. **Reusable deterministic fixtures** — complete / missing / Market+News `not_required` / non-empty N/A-unavailable / original REVIEW / pre-Gate original-rating provenance.

## Explicit non-claims

Stage 2 code is not implemented; no CI/acceptance/merge claim. Mandatory integration tests that require C's shared wiring (real Graph/CLI publication, cross-surface, checkpoint/resume via real path, real-time Markdown buffering) are **not executed** in this batch.
