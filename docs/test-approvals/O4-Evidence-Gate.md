# Pre-code approval record — O4 (Decision Evidence Gate)

Feature owner: Member D (Safety and Reliability Lead). Record prepared by Member D from real
GitHub comments and reviews on PR #7. Times are recorded in UTC exactly as returned by the
GitHub API. Fields that cannot be independently verified are marked **pending verification**.

> Scope of this record. It documents **Stage 1** only: the pure Evidence Gate checker
> (`tradingagents/agents/evidence_gate.py`) and its deterministic offline unit tests
> (`test/offline/test_evidence_gate.py`). **Stage 2 shared integration (Graph, CLI, reporting,
> state, persistence) is NOT approved by this record** and requires separate Member A / Member C
> approval. Passing Stage 1 does not constitute full O4 safety approval.

| Field | Actual record |
|---|---|
| Feature / owner | O4 — Decision Evidence Gate / Member D |
| Verified implementation baseline | `origin/main` `ef1e6a362def6bb24275e6fd3678e4f10d4b1f07` (PR #15), merged into `feature/o4-evidence-gate` at merge commit `c83e7379e417ede2e99c777cd2f04c80b33d5fa3`. Historical review snapshots preserved: `5afb24cf…` (review snapshot), `c861d0307238a3b763a35446f7da1245b1e8322a` (earlier local baseline, still an ancestor). O4 plans unchanged (byte-identical to PR #7 head `27f244a`). |
| Requirements registry commit SHA | `docs/req/requirements.yaml`; PR #2 merged into `main` at `4f87e29f7a52842dba8272071d2a4a1b527def10` (per Member F review and PR #7 comments) |
| Test plan version and immutable GitHub commit link or attached file | `docs/req/O4-Test-Plan.md` — **O4-TEST-v0.5**; reviewed revision `27f244af5aa331eece47b4d4410f69f97b7db34b` (PR #7). Local file matches this revision (`git diff --stat 27f244a -- docs/req/O4-Test-Plan.md` = no diff). |
| Approved requirement IDs and test case IDs | **Stage 1** test IDs: O4-T-01…07, 09…15, 17…19, 24, 25. For **T-07, T-18, T-19 only the checker-level unit portions** (real `check_evidence()` entry point). |
| Test scope: fixtures, expected results, negative/boundary cases, offline command | Defined in `O4-Test-Plan.md` §4, §6 (Stage 1), §7. Deterministic offline unit tests under `test/offline/`; network blocked by CI PR #1 fixture. Commands: `pytest --collect-only -q` and `pytest -q` (documented proposals; not yet executed). **Executed results not yet recorded.** |
| Test reviewer and GitHub approval-comment link | **Member F** (`fancx777`) — formal review **APPROVED**, review id `5934877146`: https://github.com/Caicys297/TradingAgents-CS5351/pull/7#pullrequestreview-5934877146 |
| Test approval time with time zone | **2026-11-17T08:02:32Z** (UTC) |
| OpenCode execution plan text/link and version | `docs/req/O4-Implementation-Plan-v0.1-DRAFT.md` — internal version **O4-EXEC-v0.2-DRAFT** (reviewed revision `27f244a`; reconfirmed at `0b68404`). Execution-plan scope approval by Member A below. |
| Execution-plan reviewer and GitHub approval-comment link | **Member A** (`Caicys297`) — two comments: (1) `2026-11-16T13:56:48Z` approves O4-EXEC-v0.1 D-owned Stage 1: https://github.com/Caicys297/TradingAgents-CS5351/pull/7#issuecomment-6918453325 ; (2) `2026-11-17T07:19:19Z` reconfirms **O4-EXEC-v0.2** D-owned Stage 1 scope: https://github.com/Caicys297/TradingAgents-CS5351/pull/7#issuecomment-6941508499 |
| Execution-plan approval time with time zone | **2026-11-16T13:56:48Z** (v0.1 Stage 1) and **2026-11-17T07:19:19Z** (v0.2 Stage 1 reconfirmation), both UTC |
| First implementation-code commit SHA and time | **Not yet created.** No implementation or test code has been written. To be recorded at Stage 1 start. |
| Feature PR link and later code-review/CI links | PR #7: https://github.com/Caicys297/TradingAgents-CS5351/pull/7 (open, draft=false, base `main`, head `27f244a`). Code-review/CI links: **not yet available.** |

## Approval scope separation (verbatim facts)

**Member A — Stage 1 execution scope:**
- Approves **only** D-owned Stage 1: pure checker in `tradingagents/agents/evidence_gate.py` and
  offline unit tests in `test/offline/test_evidence_gate.py`.
- T-07/T-18/T-19: **unit portions only**.
- G1/S2/B1 integration policy adopted at the architecture-direction level.
- Explicitly states: *"这条是执行计划第一阶段范围确认，不是测试计划审批，也不是 Stage 2 批准"* — this is Stage 1
  execution-scope confirmation, **not** test-plan approval and **not** Stage 2 approval.
- Member A instructed: sync latest `main`, record the real baseline SHA, and record OpenCode
  sessions and first-code time truthfully.

**Member F — Stage 1 test plan:**
- Formally **APPROVED** O4-TEST-v0.5 Stage 1 pre-coding test plan at reviewed commit `27f244a`.
- Approved range: O4-T-01…07, 09…15, 17…19, 24, 25; T-07/T-18/T-19 checker-level offline unit only.
- T-07 must call the real `check_evidence()` and exercise production fail-closed logic; a test-only
  wrapper is not acceptable. T-18 must propagate `ValueError` for unknown Analyst configuration.
- Graph/CLI/state/report/persistence and actual publication behaviour are Stage 2, to be approved
  separately.
- Member F noted two **non-blocking** doc tail items: residual `v0.4` references and clarifying
  §6.6 T-16 execution/traceability + Should non-blocking wording. F stated these do **not** block
  Stage 1.

**Stage 2 — NOT approved:** shared files (`trading_graph.py`, `state.py`, `cli/run.py`,
`reporting.py`, `report_html.py`, `memory/log.py`), integration portions of T-07/T-18/T-19, and
T-08, T-16, T-20, T-21, T-23. Requires separate Member A / Member C approval.

## Status

- Stage 1 test-plan approval (F): **VERIFIED**.
- Stage 1 execution-scope approval (A): **VERIFIED**.
- Stage 2: **NOT APPROVED**.
- This record does not grant approval; it transcribes independently verified GitHub evidence.
