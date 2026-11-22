# Coding agent entry point

This file describes the team's current working rules for AI coding agents. The selected requirement registry is `docs/req/requirements.yaml`. The architecture handoff is integrated under `docs/architecture/` in this branch; check it against the selected requirements and current code. Earlier plans and transcripts are evidence of their own time, not current approval for new work.

**Build target and baseline:** extend the team's TradingAgents repository, derived from upstream commit `9fa1196fffbcfd9de5146d2dd2869df84ab99838` (see `docs/PROJECT_WORKSPACE.md`). Record the current `main` SHA in each new task plan; do not treat this document's date as a frozen code baseline.

## Start a scoped task

1. Read `Prompt.md`, `.opencode/rules.md`, `.agent/rules.md`, and `docs/code-governance/structural-constraints.md`, `mcp-tool-manifest.md`, and `verification-constraints.md`. Read the architecture blueprint, ADR, invariants, and permission model under `docs/architecture/`.
2. Read only the relevant requirement IDs, interface contract, test plan, approval record, and source files for the assigned task. State the exact baseline commit, test IDs, and proposed read/write paths in a short execution plan.
3. Wait for the required human test-plan review and A's execution-scope approval **before the first code edit**. An approval for an older plan or SHA does not approve a changed plan. Do not invent or backdate an approval.
4. Work only within the approved file list. Stop and request a revised plan if a new file, dependency, interface, safety rule, or architecture decision is needed.
5. Run the applicable approved offline tests and regression checks. Report the commands, actual results, failing cases, and commit SHA. Keep the real agent session and mark human interventions with reasons. Submit a PR for human review; do not merge your own work.

## Roles and authority

A coordinates the feature set and reviews each scoped agent execution plan. F reviews O1/O3/O4/O5 test plans and owns CI/test tooling. A reviews O2/O6 test plans. B maintains the requirements registry. C is the sole human editor/integrator of shared `cli/run.py`, `tradingagents/graph/trading_graph.py`, and rating-output wiring for O2/O4/O6. D owns O4 safety semantics and its isolated tests; E owns O5 news work. These assignments come from `docs/req/requirements.yaml`; they do not create operating-system permissions. For a specific agent session, the approved plan's exact file list is the operative scope.

## Boundaries

- Extend the existing TradingAgents baseline. Keep the authoritative requirements, interface contracts, deterministic safety checks, and existing public APIs intact unless a reviewed change explicitly says otherwise.
- Module ownership and integration contracts are in `docs/code-governance/structural-constraints.md` and the selected registry. In particular, keep data retrieval behind the dataflows layer, preserve public Yahoo tool signatures, and route shared CLI/graph wiring through C's integration review.
- Do not read secrets, credentials, private exports, `.env`, or `agent.env`. Never put secret values in prompts, logs, tests, or transcripts.
- `.opencode/rules.md`, `.agent/rules.md`, `AGENTS.md`, `Prompt.md`, and `.opencode/permissions.jsonc` are human-governed. An agent may suggest an edit but must not alter them during feature implementation.
- Treat proposed agent output as advisory. Humans approve requirements, scope, tests, reviews, and merge decisions. Do not claim an unrun test, a passing gate at another SHA, or a control that has not been verified.
- S6 is terminated and is not part of the final S1–S5 delivery. A future proposal to restart it needs a new review.

The path matrix in `.opencode/permissions.jsonc` documents allowed *task scopes*. It is not evidence that OpenCode or the local filesystem enforces those paths. CI and GitHub protections are separate controls; see `docs/code-governance/verification-constraints.md`.
