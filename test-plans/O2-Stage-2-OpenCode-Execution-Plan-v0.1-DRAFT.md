# O2 Stage 2 Integration — OpenCode Execution Plan

**Document version:** v0.1-DRAFT  
**Status:** Draft; A approved the Stage 2 scope supplement in PR #18 review `5959122354`; F’s formal test-plan approval and C’s CLI/test ownership confirmation remain pending. Stage 2 implementation is not authorized.  
**Owner:** B (QinQilun)  
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. The implementation base must be the verified current `origin/main` containing that merge; record the actual base SHA at implementation time.  
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**A scope supplement:** [PR #18 review 5959122354](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5959122354), submitted `2026-11-18T15:00:01Z`.

## 1. Authorization boundary

This document proposes work sequencing only. OpenCode must not edit source, tests, workflows, dependencies, or configuration until F approves the Stage 2 test plan, C confirms the CLI/test ownership split, and A/F/C authorize implementation.

Stage 2 is limited to completed normal CLI runs, unique run-directory reservation, CLI/Graph manifest integration, offline integration/regression tests, and the approved three-platform CI matrix. It excludes backtests, replay, failed/programmatic runs, immutable data snapshots, moving existing report/state/log paths, unrelated refactoring, and the D7 Schema CI Gate.

A’s scope supplement is not F’s formal test-plan approval, and it does not authorize implementation.

## 2. Preconditions before implementation

OpenCode must report all items below and stop if one is unmet:

- Fetch has completed and the exact current `origin/main` SHA is recorded. It must contain PR #9 merge `d36a677...`; if main has advanced, record the actual base SHA and recheck the allowlist.
- Work is on a dedicated Stage 2 implementation branch created from that verified base, not the PR #8 documentation branch, PR #18 planning branch, or retired Phase 1 branch.
- Working tree is clean before branch creation, or existing user changes are preserved and explicitly excluded.
- PR #16 implementation remains present; its approved files are not rewritten or discarded.
- PR #9 allowlist change is present in the base, including `input_condensation_audit_note`.
- F approves the Stage 2 test plan and confirms the CI matrix.
- C confirms the CLI/test ownership split and whether any unavoidable Graph read-only dependency exists.
- B’s separate writer/TC-23 synchronization has landed before the Stage 2 TC-23 expectation is verified.

## 3. Proposed sequence (after approval only)

1. **Read-only source audit:** Inspect the current CLI lifecycle, results-path consumers, artifact creation times, path validation, test collection, platform CI, and current `main` diff. Report exact candidate files and integration points to A/C/F before editing.
2. **Run-directory reservation (C-owned `cli/run.py`):** Reserve `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph starts using `mkdir(exist_ok=False)`. Retry at most 3 times. If all attempts collide, fail clearly before Graph starts without changing existing files.
3. **Manifest lifecycle integration (C-owned `cli/run.py`; B reviews O2 contract):** Write exactly one manifest after normal CLI analysis completes and after the report-save choice is handled. Keep existing report, state, and log paths in place. Reference only artifacts that actually exist at write time; label existing legacy artifacts `shared_mutable`. Pass normalized identity and only Registry-allowlisted effective config, including merged `input_condensation_audit_note`; retain secret redaction and `actual_input_data_provenance: not_captured`.
4. **Failure behavior:** On manifest write failure, preserve the completed analysis result and O4 effective rating, finish normally, show a short warning that the manifest was not saved and the run’s provenance record is unavailable, show no success path, and leave no partial manifest. Assert behavior, not an exact English warning string.
5. **Offline integration tests:** Add approved CLI integration coverage at `test/offline/test_o2_cli_manifest.py` only after C confirms the CLI/test ownership split. Keep existing O2-TC IDs: TC-04 for full CLI success, TC-13/14 for failure, TC-11 for bounded allocation/collision, and TC-05/15/19/20/21/23 for their assigned coverage. Do not add a new ID.
6. **Regression and CI (F coordinates CI):** Run targeted O2 tests and `pytest -q`. Ubuntu keeps the existing Python 3.11–3.14 full regression; macOS and Windows run the O2 writer and CLI manifest target tests on Python 3.12. Record commit SHA, commands, workflow URLs, Python/OS versions, and actual outcomes.
7. **Review handoff:** Report changed files, diff, test/CI evidence, limitations, and plan/approval references. Open a PR for review; do not approve or merge on behalf of A/F.

## 4. Proposed file boundary and ownership

Candidate paths must be checked against the verified base and team ownership before edits.

| Area | Candidate paths | Owner / guard |
|---|---|---|
| CLI lifecycle, run directory, manifest invocation | `cli/run.py` | C owns shared integration; B reviews O2 data contract |
| Graph context and output paths | `tradingagents/graph/trading_graph.py` | Read-only inspection only unless C confirms a necessary shared change; avoid unrelated Graph/API changes |
| Phase 1 writer | `tradingagents/repro/manifest.py` | B owns writer; TC-23 synchronization is a separate implementation PR based on current `main` |
| Existing Phase 1 tests | `test/offline/test_o2_manifest.py` | Preserve; B updates TC-23 in the separate synchronization PR |
| New CLI integration tests | `test/offline/test_o2_cli_manifest.py` | Add only after C confirms CLI/test ownership split |
| Test discovery/config | `pyproject.toml` or current test config | Change only if audit shows necessary and C/F approve ownership |
| CI workflows | `.github/workflows/ci.yml` or current workflow files | F coordinates matrix; no CI edit before approval |
| Setup/dependencies | `setup.py`, `pyproject.toml`, or current packaging files | Out of scope unless a specific approved need is documented; no dependency addition by default |

## 5. Stop conditions

Stop and return evidence for review if implementation requires:

- changing the approved completed-CLI-only scope or adding failed/programmatic runs;
- moving existing report/state/log paths or changing legacy artifact stability away from `shared_mutable`;
- changing manifest schema, fingerprint semantics, secret handling, or allowlist beyond the merged Registry;
- adding or redefining an official O2-TC ID;
- writing more than one manifest or writing before analysis completion/report-save handling;
- changing the approved fail-soft/fail-closed failure behavior or omitting the visible warning/no-success-path requirement;
- changing public APIs, shared Graph behavior, or ownership assignments;
- adding a runtime dependency;
- editing CI without F’s confirmed ownership;
- an unresolved CI platform/version or missing test-to-requirement mapping;
- rebasing, resetting, or rewriting existing Phase 1 history.

## 6. Required implementation records

Before the first code edit, record the verified base SHA, branch, clean working-tree status, approved plan versions, F’s formal test-plan approval, C’s CLI/test ownership confirmation, approvers/evidence, and actual coding-start timestamp with timezone. For each verification, report the exact command and actual output. Do not infer local tests from CI or vice versa. The final PR must not claim full data reproducibility without immutable input snapshots.

## 7. Approval record

- **A Stage 2 scope supplement:** Approved in PR #18 review `5959122354`, `2026-11-18T15:00:01Z`
- **F formal Stage 2 test-plan approval:** Pending
- **C CLI/test ownership split:** Pending confirmation
- **Implementation status:** Not started / not authorized
- **Tests, CI, PR, commit:** None claimed
- **Reapproval:** Any material scope, expected-result, path, test-ID, or ownership change requires an updated plan and renewed approval before implementation.
