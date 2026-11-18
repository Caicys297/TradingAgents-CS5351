# O2 Stage 2 Integration — OpenCode Execution Plan

**Document version:** v0.1-DRAFT  
**Status:** Draft for A/F/C review; implementation is not approved.  
**Owner:** B (QinQilun)  
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. Current remote `main` was fetched and verified at dedicated-branch creation; the verified SHA is the same commit. If `main` advances before implementation, record the actual base SHA and recheck the allowlist.  
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.

## 1. Authorization boundary

This document proposes work sequencing only. OpenCode must not edit source, tests, workflows, dependencies, or configuration until A/F approve this execution plan and the companion Stage 2 test plan. Before approval, OpenCode may perform read-only inspection and report current repository state, ownership, and conflicts.

Stage 2 is limited to completed normal CLI runs, unique run-directory reservation, manifest lifecycle integration, offline integration/regression tests, and the approved three-platform CI matrix. It excludes backtests, replay, failed/programmatic runs, immutable data snapshots, unrelated refactoring, and the D7 Schema CI Gate.

## 2. Preconditions before implementation

OpenCode must report all items below and stop if one is unmet:

- Fetch has completed and exact current `origin/main` SHA is recorded. At plan creation it was `d36a677...`, and the PR #9 merge is in that base. If main advances before implementation, use and report its actual SHA and recheck the allowlist.
- Work is on a new dedicated Stage 2 branch created from that verified base, not the PR #8 documentation branch or the retired Phase 1 branch.
- Working tree is clean before branch creation, or existing user changes are preserved and explicitly excluded.
- PR #16 implementation remains present; its approved files are not rewritten or discarded.
- PR #9 allowlist change is present in the base, including `input_condensation_audit_note`.
- A/F approve both plan versions and resolve the open decisions in the test plan.
- C confirms responsibility for shared `cli/run.py` / Graph integration; F confirms CI workflow and matrix responsibility. Any ownership change must be explicit.

## 3. Proposed sequence (after approval only)

1. **Read-only source audit:** Inspect the current CLI/Graph lifecycle, results-path consumers, artifact creation times, path validation, test collection, platform CI, and current `main` diff. Report exact candidate files and integration points to A/C/F before editing.
2. **Run-directory reservation (C-owned shared integration):** Implement the approved path layout and collision-safe reservation before Graph starts. Cover repeated same-ticker/date runs, same-second and concurrent starts, traversal rejection, bounded UUID collision retries, and preservation of existing contents.
3. **Manifest lifecycle integration (C-owned shared integration; B reviews O2 contract):** Invoke the Phase 1 writer once at the approved lifecycle point. Pass normalized identity and only Registry-allowlisted effective config, including the merged `input_condensation_audit_note`; retain secret redaction and `actual_input_data_provenance: not_captured`. Phase 1’s 24-test evidence predates the PR #9 allowlist and does not verify this field; Stage 2 must synchronize and verify it.
4. **Artifact collection and failure behavior:** Apply the approved stability labels and root containment. On manifest failure, leave no partial file, preserve completed analysis output, show the approved provenance warning, and never print a successful manifest path.
5. **Offline integration tests:** Add only approved test files/cases. Mock Graph/model/vendor boundaries; exercise side effects and CLI behavior; do not make network calls. Preserve all Phase 1 tests and behavior.
6. **Regression and CI (F coordinates CI):** Run targeted O2 tests and `pytest -q`; execute the approved CI matrix on Ubuntu, macOS, Windows. Record commit SHA, commands, workflow URLs, Python/OS versions, and actual outcomes.
7. **Review handoff:** Report changed files, diff, test/CI evidence, limitations, and plan/approval references. Open a PR for review; do not approve or merge on behalf of A/F.

## 4. Proposed file boundary and ownership

Candidate paths must be checked against the verified base and team ownership before edits.

| Area | Candidate paths | Proposed owner / guard |
|---|---|---|
| CLI lifecycle, run directory, manifest invocation | `cli/run.py` | C owns shared integration per existing execution-plan ownership statement; B reviews O2 data contract |
| Graph context and output paths | `tradingagents/graph/trading_graph.py` | C owns shared integration; avoid unrelated Graph/API changes |
| Phase 1 writer | `tradingagents/repro/manifest.py` | Reuse as-is; B changes only for a separately identified and approved defect |
| Existing Phase 1 tests | `test/offline/test_o2_manifest.py` | Preserve; add integration coverage in an agreed test module |
| Test discovery/config | `pyproject.toml` or current test config | Change only if audit shows necessary and C/F approve ownership |
| CI workflows | `.github/workflows/ci.yml` or current workflow files | F coordinates matrix; no CI edit before approval |
| Setup/dependencies | `setup.py`, `pyproject.toml`, or current packaging files | Out of scope unless a specific approved need is documented; no dependency addition by default |

## 5. Stop conditions

Stop and return evidence for review if implementation requires:

- changing the approved completed-CLI-only scope or adding failed/programmatic runs;
- changing manifest schema, fingerprint semantics, secret handling, or allowlist beyond merged Registry;
- moving/changing existing output paths without the approved compatibility decision;
- changing public APIs, shared Graph behavior, or ownership assignments;
- adding a runtime dependency;
- changing fail-soft behavior or omitting the visible failure warning;
- an unresolved CI platform/version or missing test-to-requirement mapping;
- rebasing, resetting, or rewriting existing Phase 1 history.

## 6. Required implementation records

Before the first code edit, record verified base SHA, branch, clean working-tree status, approved plan versions, approvers/evidence, and actual coding-start timestamp with timezone. For each verification, report the exact command and actual output. Do not infer local tests from CI or vice versa. The final PR must not claim full data reproducibility without immutable input snapshots.

## 7. Approval record

- **Stage 2 execution-plan approval:** Pending A/F/C
- **Approver, timestamp, evidence:** Not recorded
- **Implementation status:** Not started / not authorized
- **Tests, CI, PR, commit:** None claimed
