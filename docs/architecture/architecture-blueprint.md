# Architecture Blueprint — TradingAgents (CS5351 O1–O6)

**Status:** Closeout draft, written from the records that exist at
`main@252fe311d8d1483b5713de69b04ce2769c33f1dd`.
**Owner:** C (architecture integrator and sole editor of shared CLI/graph wiring).

**Scope of this document.** It states what the system actually is at the
verified commit above. It is the master constraint document the Plan agent
reads before proposing changes. It does not grant approval, does not restate
requirements, and does not claim that any requirement is verified beyond the
evidence named here.

**Verification baseline.** Every statement below is checked against
[`main@252fe311`](https://github.com/Caicys297/TradingAgents-CS5351/tree/252fe311d8d1483b5713de69b04ce2769c33f1dd).
Where this document says "exists", it means the file or symbol is present at
that commit. Where it says "runs", it means a CI job exists and ran; the
result is named separately.

---

## 1. Scope and boundaries

### 1.1 What the system is

TradingAgents is a CLI-driven multi-agent equity analysis application. A user
runs one analysis for a ticker and a trade date; a LangGraph workflow of LLM
agents produces analysis reports and a final trade decision; the CLI streams
that work to a live terminal view, saves the report tree, and writes a
reproducibility manifest.

The system contains genuine AI components (LLM agents that plan, debate and
decide) and several safety-relevant deterministic boundaries (evidence gating,
SMA history guards, JSONL evidence persistence, manifest provenance).

### 1.2 In scope

- The six optimisation areas O1–O6, as recorded in
  [`docs/req/requirements.yaml`](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml) at the baseline SHA.
- The CLI entry path `run_analysis` in [`cli/run.py`](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/cli/run.py).
- The offline-deterministic test suite under `test/offline/`.
- The blocking CI gates declared in [`ci.yml`](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/.github/workflows/ci.yml).

### 1.3 Out of scope

- Live-market trading and brokerage integration. The system produces analysis,
  not orders.
- Claims about news topics that were never fetched (`development_contract.o5.scope`).
- S6 / T17 performance measurement: **development is stopped and acceptance is
  not completed; REQ-O5-10 is not accepted as satisfied.** See §9.3.
- Course deliverables D3 (: `AGENTS.md`, `Prompt.md`, `docs/code-governance/`,
  `.opencode/`, `.agent/`) — these files **do not exist** at the baseline SHA.
  See §7.4.

---

## 2. Architectural drivers

These are the forces that shaped the design, derived from the Registry's own
framing rather than from a retrospective narrative.

| Driver | Why it constrains the design | Registry anchor |
|---|---|---|
| **A tradeable rating must never be published from incomplete evidence** | The single highest-consequence failure: an agent output reaching the user as an approved recommendation. | `O4-INV-01`, `O4-INV-03` |
| **An LLM's output cannot be trusted to bound itself** | Every place where model text reaches a user must pass a deterministic check first. | `O4-INV-01`, `REQ-O5-06` |
| **Reproducibility must be auditable without re-running** | A run must be explainable from artifacts alone; secrets must not leak into them. | `O2-FR-05`, `O2-FR-11`, `O2-NFR-03` |
| **Character budgets are not token budgets** | The system may not claim a token reduction it did not measure. | `O3-FR-07`, `development_contract.o3.token_claim` |
| **Degradation must be honest and bounded** | A failing vendor or sink must not fabricate an empty/no-news result. | `REQ-O5-06`, `INV-O5-01`, `development_contract.o5.invariant_failure` |
| **Short price history must not be labelled as a long-window SMA** | A 50-day SMA computed over 12 closes is a false statement, not a degraded one. | `REQ-O1-01`, `REQ-O1-02`, `REQ-O1-03` |
| **Governance itself must be machine-checked** | Human process rules decay unless CI enforces them. | `REQ-GOV-01` … `REQ-GOV-08` |

---

## 3. System boundaries and components

### 3.1 Component map

```
cli/
  run.py            run_analysis: the single orchestration entry
  display.py        live view, report display, per-Analyst summary (O6)
  stats_handler.py  StatsCallbackHandler: run counters + per-Analyst stats (O6)
  selections.py     interactive selection, depth from env

tradingagents/
  graph/
    trading_graph.py      TradingAgentsGraph: builds and drives the workflow
    setup.py              graph topology (four Analysts in parallel)
    analyst_execution.py  build_analyst_execution_plan: per-run Analyst plan
    checkpointer.py       SQLite checkpoint/resume
  agents/
    state.py              AgentState
    tools.py              LLM-facing tools, incl. get_global_news
    rating.py             run_rating / is_review: rating normalisation
    evidence_gate.py      check_evidence: the deterministic O4 gate
    analysts/
      condensation.py     O3 input condensing (parse/rank/dedupe/fit)
  dataflows/
    config.py             run_config / run_config_context
    files.py              locked(): per-file advisory locking
    macro_news_filter.py  O5 selector (pure, offline)
    symbols.py            safe_ticker_component
    vendors/yahoo/
      market.py           SMAs (O1 guard)
      news.py             news adapter + O5 evidence sink
    repro/…               manifest construction (O2)
  memory/                 trading memory log, reflection, settlement
  reporting.py            report tree writer

docs/req/requirements.yaml   the Registry (97 entries)
ci.yml + scripts/check_*.py  the blocking gates
```

### 3.2 Responsibility boundaries

| Boundary | Authority | Rationale |
|---|---|---|
| `cli/run.py`, `trading_graph.py`, rating-output wiring | **C only** (`development_contract.integration_owner`) | Shared files with one integrator prevent concurrent edits to the orchestration path. |
| Module-internal logic (filter, condensation, gate, adapter) | Module owner (B/D/E/F) with C review on the seam | Isolated modules are testable without touching the CLI. |
| Registry and schema | B maintains; F owns schema CI wiring | Single writer for the requirements baseline. |

---

## 4. Actual data flow

### 4.1 One CLI run, in the order the code executes it

The controlling function is `run_analysis` in `cli/run.py`. The order below is
the order of statements, not of concepts.

1. **Selection and config.** `get_user_selections` resolves ticker, date,
   analysts and asset type; `_build_run_config` merges defaults, env and
   overrides into the effective config.
2. **Analyst plan.** `build_analyst_execution_plan(selected_analyst_keys)`
   produces the ordered plan; `StatsCallbackHandler(selected_spec_keys)` is
   constructed from it (O6).
3. **Run directory reservation.** `_reserve_run_directory(config["results_dir"],
   ticker, date)` creates `<results_dir>/<safe_ticker>/<analysis_date>/runs/<uuid4>/`
   **before any graph work**. A reservation failure raises `RunDirectoryUnavailable`
   and exits with code 1, leaving existing files untouched.
4. **O5 evidence scope.** `with o5_evidence_run(run_context.run_dir):` opens
   immediately after a successful reservation and before the graph is built.
   It wraps **graph construction, the stream, the report offer and the manifest
   write** — that is, every remaining step and every exit path.
5. **Graph construction.** `TradingAgentsGraph(selected_analyst_keys, config=…,
   debug=True)` builds the workflow. A construction failure still exits through
   the O5 scope's cleanup.
6. **Stream.** `graph.stream_run(graph.checkpoint_input(init_agent_state), **args)`
   drives the workflow inside a `try/finally` that also tears down the
   checkpointer. Messages are classified and routed to the live view; chunk
   deltas are merged into `final_state`.
7. **Decision record.** On a clean stream, `graph.record_decision(...)` writes
   the state log and the `state_log_written` flag is set — "only a normal return
   proves this run's state log was written and closed".
8. **Report offer.** `_offer_reports(final_state, graph, ticker, save=…, show=…,
   html=…)` saves the report tree and returns the paths it actually wrote.
9. **Manifest.** `_artifact_references(...)` resolves registered paths against
   `run_context.run_dir`; `_finalize_run_manifest(...)` writes `manifest.json`
   exactly once. On failure the analysis result stands and the user is told the
   provenance record is missing.

### 4.2 Where each optimisation attaches

O1–O6 are **not** a serial pipeline. O1, O3 and O5 all sit inside the analyst
leg of the graph and are reached through different call paths. The diagram in
§5 is the authoritative form of this.

| Area | Attachment point | Kind of change |
|---|---|---|
| **O1** | `dataflows/vendors/yahoo/market.py` SMA computation | Guard inside the tool result path |
| **O3** | `agents/analysts/condensation.py`, called when building the Sentiment Analyst's input | Pre-model transformation of one source |
| **O5** | `dataflows/vendors/yahoo/news.py` adapter + `macro_news_filter.py` selector, reached via the `get_global_news` tool | Selection of already-fetched news + evidence emission |
| **O2** | `cli/run.py` reservation and manifest finalisation | Run-scoped provenance |
| **O4** | `agents/evidence_gate.py` applied in `cli/run.py` before publication | Deterministic gate on model output |
| **O6** | `cli/stats_handler.py` + `cli/display.py` summary | Non-authoritative usage reporting |

---

## 5. O1–O6 attachment and the advisory/authoritative boundary

### 5.1 The workflow shape

The four Analysts (Market, Social, News, Fundamentals) run **in parallel**, not
in sequence. `trading_graph.py` keys the checkpoint layout on
`"analysts=parallel"` and `"memory=parallel"`, and `ANALYST_ORDER` in
`cli/display.py` fixes only the *display* order, not the execution order.

```
                    ┌──────────────────────────┐
                    │  Selected Analysts (∥)   │
   O1  ── market ──►│  market analyst          │
   O3  ── social ──►│  sentiment analyst       │──┐
   O5  ── news   ──►│  news analyst            │  │  four parallel legs;
       ── fund.  ──►│  fundamentals analyst    │  │  each may call tools
                    └──────────────────────────┘  │
                                                  ▼
                                   ┌──────────────────────────────┐
                                   │ Research debate (bull/bear)  │
                                   │ Research manager             │
                                   │ Trader                       │
                                   │ Risk debate (aggressive/     │
                                   │   conservative/neutral)      │
                                   │ Portfolio Manager            │
                                   └──────────────────────────────┘
                                                  │
                                                  ▼
                          ┌───────────────────────────────────────┐
                          │ O4 gate: check_evidence(state, sel.)  │◄── O2 run dir
                          │ deterministic; pure; never mutates    │
                          └───────────────────────────────────────┘
                                                  │ effective rating
                                                  ▼
                ┌────────────────────────────────────────────────────┐
                │ CLI publication: live view → reports → manifest    │
                │ O2 manifest · O5 JSONL · O6 summary                │
                └────────────────────────────────────────────────────┘
```

**Reading the diagram.** O1, O3 and O5 attach to *different analyst legs*, in
parallel. Writing them as `O1 → O3 → O5` would be wrong: O3 transforms the
Sentiment Analyst's source text before its model call; O5 selects among news
candidates the News Analyst's tool already fetched; O1 guards the Market
Analyst's SMA arithmetic. They do not feed one another.

### 5.2 Advisory vs authoritative

| Output | Status | Enforced by |
|---|---|---|
| LLM analysis prose (market, sentiment, news, fundamentals reports) | **Advisory.** Informational text for a human reader. | Nothing gates its content; O4 only checks *presence* (`development_contract.o4.report_presence`). |
| Debate histories, investment plan, trader plan | **Advisory.** | — |
| Portfolio Manager's raw decision text | **Advisory until gated.** Held back in the CLI buffer so no Buy/Sell is published before the gate completes. | `cli/run.py` buffering; `O4-INV-03` |
| **Effective rating** | **Authoritative.** This is the only rating that may be presented as the run's result. | `check_evidence` → `effective_rating`; `O4-INV-01` |
| SMA values | **Authoritative** for the value, **guarded** for sufficiency. | `REQ-O1-01`/`-02`; insufficient-history text instead of a number |
| O5 selected news | **Authoritative** as a selection over fetched candidates; explicitly **not** a claim about unfetched topics. | `macro_news_filter.select_macro_news` |
| O5 evidence JSONL | **Diagnostic record**, written under `logs`-style semantics; failure is soft. | `o5_evidence_run`; `development_contract.o5.sink_failure` |
| Manifest | **Provenance**, not analysis. Failure is fail-soft for the result, fail-closed for the provenance claim. | `_finalize_run_manifest` |
| O6 per-Analyst usage | **Advisory telemetry.** Never a rating input. | `display_agent_summary` |

**The one invariant that ties this together:** no surface may read the ungated
original rating independently (`O4-INV-03`). Every enabled surface — live view,
report tree, return value, final display — observes the same effective rating.

---

## 6. Agent workflow (the application's own agents)

### 6.1 Graph and state

`AgentState` (`tradingagents/agents/state.py`) carries `trade_date`/`company_of_interest`,
the four analyst reports, debate states, `investment_plan`,
`trader_investment_plan`, `final_trade_decision`, and the rating fields the gate
sets (`final_rating`, `effective_rating`).

### 6.2 Parallelism

The four Analysts are separate graph branches launched together. Tools run
inside their own legs. This matters for O5: the evidence `ContextVar` is set
before the stream starts, so parallel analyst tasks inherit the binding; a
binding set *inside* one branch would not be visible to the others.

### 6.3 Checkpoint and resume

`graph/checkpointer.py` provides `thread_id(ticker, date, signature)`,
`checkpoint_step(...)`, `get_checkpointer(...)`, `clear_checkpoint(...)` and
`clear_all_checkpoints(...)`. The thread id includes an analyst-signature
component, so a resume under a different analyst set does not collide with an
earlier layout. The CLI calls `begin_checkpoint(...)` and
`clear_checkpoint_on_success(...)`; a mid-stream failure deliberately skips
both so the checkpoint remains for resume.

### 6.4 Memory

`tradingagents/memory/` holds an append-only markdown decision log
(`TradingMemoryLog`) plus reflection and outcome settlement. Entries are
written under `locked(self._log_path)`; an optional
`memory_log_max_entries` cap enables rotation of *resolved* entries.
See [`memory-design.md`](memory-design.md).

---

## 7. Permissions

### 7.1 What is actually enforced by a machine

| Mechanism | What it enforces | Where |
|---|---|---|
| `scripts/check_permissions.py` (CI job `governance permissions`) | Untrusted PR code must not obtain **write credentials or secrets** — not a blanket ban on write permissions. Checks workflow/job `permissions`, `write-all`, PR-reachable write scopes, `pull_request_target` with secrets or PR-head checkout, `persist-credentials: false` on PR-reachable checkouts, and removal of the baseline block. | `ci.yml` job `governance-permissions` |
| Baseline workflow permissions | `contents: read`, `pull-requests: read` | `ci.yml:9-11` |
| `scripts/check_test_approval.py` (CI job `test approval`) | No code change merges unless batch approval records exist and match an authorized reviewer's evidence | `ci.yml` job `test-approval` |
| `scripts/check_ai_use_log.py` (CI job `ai-use log`) | A code/prompt change must add AI-use evidence under `transcripts/` | `ci.yml` job `ai-use-log` |
| `scripts/check_contracts.py`, `check_security.py`, `check_api.py` | Contract, security and API-surface guards | `governance *` jobs |
| `tests/test_layering.py` | Only `tradingagents/dataflows` may import `yfinance` | pytest |

### 7.2 What is a document rule, not machine-enforced

| Rule | Source | Enforcement status |
|---|---|---|
| C is sole editor of `cli/run.py`, `trading_graph.py`, rating wiring | `development_contract.integration_owner` | **Document rule.** No automated check detects a non-C edit. |
| Per-path read/write rights for each AI coding agent role, default-deny | Course D3.6 | **Not implemented.** `.opencode/permissions.jsonc` does not exist at this SHA. |
| Safety-critical changes need an architecture decision plus human review | `REQ-GOV-08`; course §6 | **Partly.** Human review is a GitHub setting (branch protection); no repository file records the "architecture decision" link per change. |
| Memory-log ownership and rotation | `memory_log_max_entries` | Config-driven behaviour, not a permission. |

### 7.3 Human roles

| Role | Responsibility (from `development_contract.approval_roles`) |
|---|---|
| **A** | Owns the feature set; approves execution scope and, for O2/O6, test plans |
| **B** | Maintains the Registry and schema |
| **C** | Sole integrator of shared CLI/graph/rating wiring |
| **D** | O4 safety semantics and D-owned offline tests |
| **E** | O5 requirements and the news adapter |
| **F** | Reviews test plans for O1/O3/O4/O5; owns CI and test tooling |

### 7.4 Governance files that do not exist

The course requires `AGENTS.md`, `Prompt.md`, `docs/code-governance/{structural-constraints,verification-constraints,mcp-tool-manifest}.md`,
`.opencode/permissions.jsonc`, `.opencode/rules.md` and `.agent/rules.md`.
**None of these exist at `main@252fe311`.** `.opencode/` and `.agent/` are empty
directories. This blueprint therefore cannot cite them as constraints; it
records their absence as a gap.

See [`permission-model.md`](permission-model.md) for the full model and its
evidence status.

---

## 8. Verification strategy

### 8.1 Three tiers (course D4) mapped to what exists

| Tier | Course intent | What exists here |
|---|---|---|
| **Structural** | imports, module boundaries, permissions, fitness functions | `tests/test_layering.py` (yfinance only in dataflows), `scripts/check_contracts.py`, `check_api.py`, `check_security.py`, `check_permissions.py` |
| **Regression** | all prior suites pass | CI job `tests (py3.11/3.12/3.13/3.14)`; default `pytest -q` collects `test/offline/` |
| **Behavioral** | quality thresholds, zero safety escapes | `semantic (deterministic O5)` and `semantic (deterministic O4)` CI jobs running `scripts/semantic_report.py` against fixed fixtures |

### 8.2 Blocking gates as implemented

`ci.yml` declares 17 jobs at this SHA:

`tests (py3.11)`, `tests (py3.12, America/New_York)`, `tests (py3.13)`,
`tests (py3.14)`, `clean-install smoke`, `ruff (strict, full repo)`,
`requirements schema`, `type check`, `dependency audit`, `test approval`,
`ai-use log`, `semantic (deterministic O5)`, `semantic (deterministic O4)`,
`governance contract`, `governance security`, `governance api`,
`governance permissions`.

Two of these (`test approval`, `ai-use log`) are **pull-request-only**: they are
`skipped` on a `push` to `main`, which is why the CI run on a main commit
reports 15 successes and 2 skips rather than 17 successes.

### 8.3 How to read evidence claims

Four different statements must not be conflated:

| Claim | What it means | Where it is claimed here |
|---|---|---|
| **"A test exists"** | The node is present in the named file at the baseline SHA | Throughout |
| **"A historical execution passed"** | A real CI run produced `PASSED` for that node | Only where a run is cited |
| **"The requirement is covered"** | The assertions actually prove the fit criterion | Rarely, and only with the assertion named |
| **"A real merge was actually blocked"** | A gate is observed to have prevented a real change | Only in §8.4, with the specific run or PR |

The first two are never treated as proof of the third or fourth.

**On historical execution evidence specifically.** F's fact check of Draft PR
#43 read the authenticated Python 3.11 job log of historical run
[`44988759013`](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013/job/137104997890)
at `main@252fe311d8d1483b5713de69b04ce2769c33f1dd` and reported that the **166
source-declared test-function references cited in that matrix** all had matching
`PASSED` entries, with a job summary of 2126 passed / 1 skipped / 1 deselected /
100 subtests passed.

That number is **not** transferable to this blueprint. The revised trace matrix
cites **227** distinct full node IDs after F's mapping additions were
incorporated; the 166 figure covers only the functions in the original draft.
No claim is made here that all 227 passed. The log body was not readable with
the credential available to C (the authenticated logs endpoint returned HTTP
401), so even the 166 figure is F's transcribed reading rather than an
independent re-measurement.

### 8.4 Real blocking evidence, and what it does not cover

Governance gates are **not** evidenced by unit tests alone. The repository holds
a state-transition record from a real PR:

| Observation | Where |
|---|---|
| Approval gate **passing** on a complete batch | [#37 run 44979161445](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44979161445), pinned `1c0b740`, 17 checks successful |
| Schema fault **blocking** a change | PR #41 **E2** |
| Repair and **recovery** | PR #41 **E4/E5**, [E5 run 44998474208](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44998474208) at `9462d6c1`, 17/17 success |
| Final read-back, then closed **unmerged** | [PR #41 comment 7076164337](https://github.com/Caicys297/TradingAgents-CS5351/pull/41#issuecomment-7076164337) |

Limits that remain true and are not waived:

- **E3 was not executed** (per A's decision recorded in the #41 closing comment).
- **No independent administrator API read-back** of the branch-protection
  configuration was obtained.
- In **E2** the four test-matrix failures were **coupled to the Schema fault**;
  this is not evidence of a single job failing in isolation.
- **Independent semantic-job red-light blocking was not verified.**
- Enforcement of an *accompanying architecture decision* on safety-critical
  paths was not independently verified.
- **PR #38 is a batch-specific process deviation** and must not be generalised
  into "every batch had prior approval" or into "no batch ever deviated".

Detailed node-level mapping for these gates lives in
[`trace-matrix.md`](trace-matrix.md) §GOV, which also records which individual
governance rows have a real rejection versus only a passing run.

**Governance blocking experiments and business-invariant tests are different
kinds of evidence.** A green O4 gate suite does not demonstrate that CI blocked a
change; a blocked PR does not demonstrate that an invariant holds in production.
Neither substitutes for the other.

---

## 9. Observability

### 9.1 What a run leaves behind

| Artifact | Location | Purpose |
|---|---|---|
| Run directory | `<results_dir>/<safe_ticker>/<date>/runs/<uuid4>/` | Isolation of one run |
| Manifest | `<run_dir>/manifest.json` | Provenance: identity, effective settings fingerprint, artifact inventory |
| O5 evidence | `<run_dir>/o5_evidence.jsonl` | One JSON line per selector event |
| Message/tool log | `<results_dir>/<safe_ticker>/<date>/message_tool.log` | Human-readable transcript of agent messages |
| State log | `<results_dir>/<safe_ticker>/TradingAgentsStrategy_logs/full_states_log_<date>.json` | Decision record written by `record_decision` |
| O6 summary | terminal only | Per-Analyst usage for this run |

### 9.2 Runtime diagnostics

- `tradingagents.o5.evidence` is an **independent logger**: `SINK_FAILED` is
  emitted there, not on the main logger, so a failing sink cannot suppress its
  own diagnostic.
- The manifest failure path prints a user-visible warning and leaves the
  analysis result intact.
- O6 prints `--` for an unknown token count rather than `0`, and always prints
  the unattributed-call line so a zero is evidence rather than silence.

### 9.3 What is not observed

- **S6 / T17 is not measured.** `REQ-O5-10` has verification `T17`, and
  development is **stopped, not accepted**. No performance threshold is claimed
  as met, and ordinary selector correctness is not performance evidence.
- No runtime monitor claims to detect a violated business invariant after the
  fact. Invariants are enforced at the code path and checked by tests; there is
  no independent production monitor.

### 9.4 S5 evidence-merge status (verified, not assumed)

S5 is the stage that carried the `run_dir` handoff into the O5 evidence sink.
Its state **at the pinned baseline `252fe311d8d1483b5713de69b04ce2769c33f1dd`**:

| Item | State |
|---|---|
| E's adapter commit `483e1f6` (private `o5_evidence_run`, JSONL sink) | On `main` |
| C's integration commit `c1fa362` (`with o5_evidence_run(...)` in `cli/run.py`) | On `main` |
| E's and C's test files (`test_o5_macro_news_integration.py`, `test_o2_cli_manifest.py`) | On `main` |
| AI-use evidence (`transcripts/O5-S5-AI-Use-Log.md`, `transcripts/O5-S5-session-export.json`) | On `main` |
| Approval records (`docs/test-approvals/historical-approvals.yaml`, `o5-s5.test_plan.json`, `o5-s5.execution_plan.json`) | On `main` |
| Merging PR | **#40 — merged** (`2026-11-22T05:17:25Z`), preceded by the approval-binding PR #42 (merged `2026-11-22T04:57:23Z`) |
| Design-record PR #36 | **Still open** (it carried the planning document, not the implementation) |

**Historical red light, with its time and closure (kept for the record).** An
earlier finding, made while #40 was still open, was that the `test approval`
job failed on it because the batch had no approval records. That finding was
**true at that time** and is not retracted here. It was closed by first merging
the approval-binding work in PR #42 (`2026-11-22T04:57:23Z`) and then letting
#40 pass and merge (`2026-11-22T05:17:25Z`). On the pinned baseline the job
reads `skipped` (it is pull-request-only), **not** failing.

**Therefore:** any statement that "PR #40 is unmerged", "the approval red light
is unresolved", or "S5 has not reached `main`" is **stale as of this baseline**.
S5 *is* in `252fe31`.

**What that does *not* mean:** merging does not establish that every O5
requirement is verified, and it does not touch `REQ-O5-10`/T17, which remains
unmeasured and stopped. Evidence status for the S5 tests is recorded in
[`trace-matrix.md`](trace-matrix.md) and is deliberately not restated here.

---

## 10. Change policy

### 10.1 What a change must satisfy before merge

1. **Test approval before code** (`REQ-GOV-01`, `REQ-GOV-02`): a versioned test
   plan and a scoped execution plan exist and are approved.
2. **Registry agreement**: the change maps to a Registry ID; new IDs go through
   B.
3. **File ownership**: only the owner edits the module; only C edits
   `cli/run.py`, `trading_graph.py` and rating wiring.
4. **No regression** (`REQ-GOV-04`): the full prior suite passes.
5. **Gates**: schema, contract, security, API, permission, AI-use as applicable.
6. **Human review** with an architecture decision for safety-critical paths
   (`REQ-GOV-08`).

### 10.2 When this blueprint must change

| Trigger | Action |
|---|---|
| A new attachment point in the analyst graph | Update §5.1 before merging the change |
| A change to what is authoritative (§5.2) | New ADR; this section is not edited in place |
| The gate moves from `cli/run.py` into the graph | New ADR and re-verification of `O4-INV-03` |
| The governance files in §7.4 are added | Promote them from "document rule" to "machine-enforced" in §7.1 |
| S6 is ever restarted | New ADR; `REQ-O5-10` re-enters §9.3 with a measured result |

### 10.3 Known state of the decision record

This blueprint was assembled at closeout from records that already existed. It
does not backfill historical dates, does not claim an architecture approval that
was never recorded, and does not reconstruct a candidate-evaluation process that
was not documented at the time. Where the record is silent, the silence is
stated — see [`adr/001-incremental-integration.md`](adr/001-incremental-integration.md).

---

## 11. Related artifacts

- [`adr/001-incremental-integration.md`](adr/001-incremental-integration.md) — the integration decision and its reopen conditions
- [`invariants.md`](invariants.md) — invariant register with enforcement and fallback
- [`memory-design.md`](memory-design.md) — state, checkpoint, memory log, run directory
- [`permission-model.md`](permission-model.md) — roles, path rights, enforcement status
- [`runtime-policy-catalog.md`](runtime-policy-catalog.md) — degraded-path behaviour
- [`evaluation-table.md`](evaluation-table.md) — candidate comparison and its evidence limits
- [`trace-matrix.md`](https://github.com/Caicys297/TradingAgents-CS5351/pull/43) — requirement → component → test (separate draft, Draft PR #43; not part of this delivery)
