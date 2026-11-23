# Structural constraints

The existing TradingAgents application is the baseline. Team work extends it through bounded modules and reviewed integration. `docs/req/requirements.yaml` is the selected requirement registry. C's architecture blueprint and ADR are included in `docs/architecture/` in this branch. Requirements must map to tests and their implementation paths.

| Area | Responsibility and boundary |
| --- | --- |
| `tradingagents/dataflows/` | Market and news retrieval, O1 SMA validity, O5 news selection, and O3 input preparation. Do not let other layers call `yfinance` directly. |
| `tradingagents/agents/` | Analyst logic and O4 evidence gate. AI advice does not override deterministic safety decisions. |
| `tradingagents/graph/` | Graph state and shared integration; C coordinates changes to `trading_graph.py`. |
| `cli/run.py` | CLI orchestration and O2/O4/O6 shared wiring; C is the sole integrator under the team contract. |
| `test/offline/`, `tests/` | Deterministic feature/contract checks and inherited regression checks. Live-service tests must be identified separately. |
| `docs/req/`, `docs/test-approvals/`, `transcripts/` | Requirements, real plan approvals, and real annotated agent sessions. Do not rewrite history. |

The table is an ownership convention, not a machine-enforced author restriction. For each change, use the exact approved file list. A cross-module change needs an explicit integration plan and human review.

Each architectural element must have one primary owning module; helpers may be called across modules through reviewed interfaces, but do not duplicate authority. Every new module and function should identify the ADR decision and invariant it implements in its plan or adjacent documentation. The AI may propose analysis and code, while the requirement registry, deterministic safety checks, and human approvals are authoritative. Do not replace the inherited application with a generated substitute.
