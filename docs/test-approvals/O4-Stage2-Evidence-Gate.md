# Pre-code approval record — O4 Stage 2 (Decision Evidence Gate integration)

Separate Stage 2 batch record (Stage 1 has its own record: `docs/test-approvals/O4-Evidence-Gate.md`, unchanged). Filled from real GitHub review/comment evidence on PR #17. Approved planning baseline: **`6275725796e618f15d4794ddc61526963bb41c35`**.

> Scope of this record. It documents **Stage 2 planning/scope approvals only** — shared-interface confirmation (C), pre-implementation test-design approval (F), and six-file execution-scope approval (A). It does **NOT** approve or record Stage 2 code implementation, executed tests, CI acceptance, or merge — none has occurred.

| Field | Actual record |
|---|---|
| Feature / owner | O4 Stage 2 — Evidence Gate Graph/CLI integration / Member D (shared integration: Member C) |
| Requirements registry commit SHA | `docs/req/requirements.yaml`; PR #2 merged at `4f87e29f7a52842dba8272071d2a4a1b527def10` |
| Test plan version and immutable GitHub commit link | `docs/req/O4-Test-Plan-Stage2-DRAFT.md` — **O4-TEST-S2-v0.6-DRAFT**; companion `docs/req/O4-Execution-Plan-Stage2-DRAFT.md` — **O4-EXEC-S2-v0.6-DRAFT**; both at commit `6275725796e618f15d4794ddc61526963bb41c35` |
| Approved requirement IDs and test case IDs | Stage 2 mandatory set approved by F (review `5974514410`): T-07 integration, T-08, T-18/T-19 integration, T-20, T-21, T-23, display-order, checkpoint/resume, repeated-completion, Gate-invocation-count, and §10b–§10e scenarios (per F's review) |
| Test scope: fixtures, expected results, negative/boundary cases, offline command | Defined in `O4-Test-Plan-Stage2-DRAFT.md` §0–§13; offline `test/offline/` under default `pytest -q` with network-blocked `conftest.py` (not `integration`-marked). Not yet written/executed. |
| Test reviewer and GitHub approval-comment link | **Member F** (`fancx777`) — review **APPROVED** `5974514410`: https://github.com/Caicys297/TradingAgents-CS5351/pull/17#pullrequestreview-5974514410 (supplements `5971672933`, `5972448586`) |
| Test approval time with time zone | **2026-11-19T11:55:11Z** (UTC) |
| OpenCode execution plan text/link and version | To be produced and approved (D9) before the first Stage 2 code edit; not yet recorded. |
| Execution-plan reviewer and GitHub approval-comment link | **Member A** (`Caicys297`) — review **APPROVED** `5973684411` (six-file execution scope): https://github.com/Caicys297/TradingAgents-CS5351/pull/17#pullrequestreview-5973684411 |
| Execution-plan approval time with time zone | **2026-11-19T10:56:49Z** (UTC) |
| Feature PR link and later code-review/CI links | PR #17: https://github.com/Caicys297/TradingAgents-CS5351/pull/17 (open, draft). No Stage 2 code/CI yet. |
| **Shared-interface confirmation (Member C)** | **Member C** (`EloimEssiam`) — issue comment `7008779473`: https://github.com/Caicys297/TradingAgents-CS5351/pull/17#issuecomment-7008779473 ; bound to commit `6275725796e618f15d4794ddc61526963bb41c35` |
| **Shared-interface confirmation time with time zone** | **2026-11-19T12:14:12Z** (UTC) — confirmation time is the comment time (as stated by C) |
| **Confirmed interface contract scope (C)** | (1) one authoritative Gate per same-execution repeat; new run after failure / Resume / new execution re-evaluate; (2) `original_rating` from trusted pre-Gate source; Guard/GateResult isolated per execution; (3) real-time PM decision Markdown buffered pre-Gate, covering normal publication, REVIEW, stream interruption and persistence failure; (4) Gate uses the complete `values` state incl. restored reports; ordering Gate→State Log→Memory; legacy-state compatibility and agreed REVIEW display rules preserved. In-scope implementation detail is the integrator's, recorded in the implementation PR. |
| **Approved file scope (A, six shared files)** | `tradingagents/graph/trading_graph.py`, `tradingagents/agents/state.py`, `cli/run.py`, `tradingagents/reporting.py`, `tradingagents/report_html.py`, `tradingagents/memory/log.py` — plus D's O4 offline tests. **Excluded:** `cli/display.py`, new files beyond the six, public API changes, automatic retry. |
| First implementation-code commit SHA and time | **Not yet created** — Stage 2 code not implemented. |
| Implementation / test / CI / merge | **NOT DONE / NOT APPROVED** by these reviews (pre-code planning/scope only). |

## Timestamps (UTC, from GitHub API — not invented)

- A execution-scope approval: `2026-11-19T10:56:49Z` (review `5973684411`).
- F test-design approval (base): `2026-11-19T08:31:20Z` (review `5971672933`, commit `c757d76`); increment review `2026-11-19T09:31:29Z` (`5972448586`).
- F pre-implementation test-design approval (bound SHA): `2026-11-19T11:55:11Z` (review `5974514410`, commit `6275725`).
- C shared-interface confirmation: `2026-11-19T12:14:12Z` (comment `7008779473`, commit `6275725`).

## Not yet satisfied before the first Stage 2 code edit

- D9 OpenCode Stage 2 execution plan produced and approved.
- Implementation PR records actual main/branch SHA, chosen mechanism, O2 `cli/run.py` insertion order, and O6 joint-verification basis (per A).
- C's O6 CLI joint-verification evidence recorded.

This record transcribes independently verified GitHub evidence and grants no implementation/CI/merge approval.
