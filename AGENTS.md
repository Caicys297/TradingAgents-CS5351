# Coding agent guide (team draft)

This file is the entry point for coding agents working on the CS5351 TradingAgents extension. It applies to new agent work after this file is accepted on `main`. It does not approve any feature, test plan, or code change by itself.

## Build target and baseline

Extend the existing TradingAgents Python application for O1–O6 while keeping its CLI and existing behavior working outside each approved change. The imported upstream code is the starting point; team changes must be identifiable in commits and pull requests. At the start of each task, record the current target-branch commit SHA and inspect the files actually present there. Do not assume an older OpenCode session describes the current code.

## Read in this order

1. `docs/req/product-requirements.yaml` for the product goal, then `docs/req/requirements.yaml` for the assigned requirement IDs and acceptance criteria.
2. The assigned feature's versioned test plan, approved scope, and approval record or immutable GitHub links. `docs/test-approvals/TEMPLATE.md` is only a blank record format; it is not approval. The team test case catalog is a draft until its individual cases are approved.
3. The applicable documents under `docs/architecture/` and `docs/code-governance/`, when they exist and have been reviewed. Read interface, state, runtime-policy, ownership, and permissions decisions relevant to the task. Record any missing decision that affects the planned edit rather than inventing one.
4. The relevant existing source and tests in `tradingagents/`, `cli/`, `tests/`, and `test/offline/`. Read the current `.github/workflows/ci.yml` and `pyproject.toml` before naming verification commands.

If the registry, approved plan, code, or interface contract disagree, report the exact conflict and wait for the human owner to decide the affected scope.

## Code and permission boundaries

- Default to reading. Before the first edit, the feature's designated test reviewer must approve the versioned test plan and case scope. Then give A an OpenCode execution plan using the single task prompt in `Prompt.md`; wait for A's approval of its version, requirement IDs, tests, and file scope. Record both decisions before changing production code, test code, or configuration. A test file is still code.
- Edit only files in the approved execution plan. Do not change a shared CLI, Graph, configuration, CI, or other feature's file merely because it seems convenient. Obtain a recorded scope/owner decision before such an edit. C coordinates shared application integration; F coordinates shared test and CI changes; A reviews execution plans and coordinates cross-feature scope.
- Keep O1–O6 changes traceable to requirement IDs, test case IDs, and the implementation PR. Use a separate feature branch. Do not rewrite the imported baseline or unrelated indicators and behavior.
- Never read, print, commit, or send secrets, local environment files, credentials, private data, or unredacted transcripts. Use offline fixtures for deterministic tests. Do not run live provider calls or paid services unless the human explicitly approves that scope.
- Repository guidance is not an enforcement mechanism. The planned `.opencode/permissions.jsonc`, `.opencode/rules.md`, `.agent/rules.md`, and `docs/code-governance/` controls need separate review and implementation. Do not claim they are active merely because this file mentions them.

## Verification and evidence

`pyproject.toml` sets default pytest collection for `tests/` and `test/offline/` and excludes tests marked `integration` by default. The actual CI commands are in the current `.github/workflows/ci.yml`; check that file instead of assuming a fixed command. Authorized, non-editing checks such as test collection or an offline callback probe may be run while planning; record their actual commands and results. They do not authorize code edits. After approval, run the relevant offline tests and required regression checks. Record actual commands, outputs, failures, fixes, and CI links. A green existing CI run does not prove a new feature's acceptance tests passed.

Keep the original agent session, human interventions, approval links and times, and the final PR/CI evidence. Redact secrets and personal data before committing any transcript or AI-use log. Do not invent, backdate, or infer approvals or test results.
