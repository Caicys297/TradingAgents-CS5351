# O2 Stage 2 Integration — OpenCode Execution Plan

**Document version:** v0.2-DRAFT  
**Status:** Draft planning record; A scope supplement approved; F formal test plan and CI matrix approved; C ownership confirmed; **A's integration contract confirmed (this revision)**. PR #18 remains Draft. Implementation and test execution are not claimed here.  
**Owner:** B (QinQilun)  
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. Joint-validation baseline: PR #21 merge `69e91ff115694f3455196e6a4114d4fe653fbb06`; O6 CLI merged via PR #20 `e4b6f9ac625f39579635c840aed98ab8dfefdaf9`. **Actual baseline verified at this plan update: `origin/main` = `102511dd44ad8779a46e09cbefe50edb8a995b45`**; re-verify and record the actual base SHA at implementation time.  
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**A scope supplement:** [PR #18 review 5959122354](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5959122354), submitted `2026-11-18T15:00:01Z`.  
**F formal test-plan approval:** [PR #18 review 5968062524](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968062524), submitted `2026-11-19T01:41:23Z`.  
**C/F ownership and timing confirmation:** [PR #18 review 5968754538](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968754538), submitted `2026-11-19T03:08:27Z`.

## 1. Authorization boundary

This document records the approved Stage 2 planning and execution boundary. Implementation must remain split by ownership and proceed in separate implementation PRs. A/F approval of the planning scope does not itself claim implementation, test execution, or CI results.

Stage 2 is limited to completed normal CLI runs, unique run-directory reservation, CLI/Graph manifest integration, offline integration/regression tests, and the approved three-platform CI matrix. It excludes backtests, replay, failed/programmatic runs, immutable data snapshots, moving existing report/state/log paths, unrelated refactoring, Graph changes for this batch, and the D7 Schema CI Gate.

C owns shared `cli/run.py` integration and coordinates CLI test integration. B owns the manifest interface and `test/offline/test_o2_cli_manifest.py`. F owns test review and approved CI workflow changes. This batch does not change Graph based on C’s read-only inspection.

### C's confirmed CLI integration contract (A-confirmed)

This revision records A's confirmation of the four contract points. They supersede the placeholder wording in v0.1 where they differ.

**C1 — Graph interface unchanged; state log registered only on success.**
The Graph's existing interface is kept. The CLI registers the state log **only after `record_decision()` returns successfully**, by checking the path this run expects (`results_dir/<safe ticker>/TradingAgentsStrategy_logs/full_states_log_<date>.json`), and labels it `shared_mutable`. **If the call fails, the file is not registered even if a stale or historical file exists at that path.** Existence is never the evidence; the successful return is.

**C2 — `_log_state()` write boundary stated precisely.**
`_log_state()` writes with `open(path, "w")` inside a `with` block and closes the file; it does **not** call `fsync()`. For this batch that is sufficient for registering the artefact after a normal run, and the plan states this limit rather than implying durability. No change to `_log_state()` is requested.

**C3 — `_offer_reports()` returns `list[Path]`.**
The private `_offer_reports()` returns `list[Path]` listing **only the report files this call confirmed saved**. Its existing display and prompting behaviour is unchanged. Excluded: declined saves, files left behind by an error, and historical files from earlier runs.

**C4 — `results_dir` for boundary and relative paths; `run_dir` for `run_unique`.**
`results_dir` is used for the path-boundary check and for computing relative paths. `run_dir` decides `run_unique`. A user-supplied custom save path outside `results_dir` keeps its ability to save but is **omitted from the manifest** rather than forced relative or silently trimmed.

**Order (unchanged):** user choices/config → reserve run directory → Graph → successful completion and O6 display → report-save choice and artifact collection → one manifest attempt.

### Still pending B's confirmation

These remain open in this revision and are **not** decided here:

1. **Final artefact set** — whether the manifest includes live per-section reports, the complete-report directory, the state log, and `message_tool.log`.
2. **Write evidence required for each** of those artefacts (what exactly must hold for it to be registered).
3. **Partial report-save failure** — whether references to the other successfully saved files are kept when one report file fails to save.

## 2. Preconditions before implementation

OpenCode must report all items below and stop if one is unmet:

- Fetch has completed and the exact current `origin/main` SHA is recorded. It must contain PR #9 merge `d36a677...` and PR #21 merge `69e91ff...`; if main has advanced, record the actual base SHA and recheck the allowlist.
- Work is on a dedicated Stage 2 implementation branch created from that verified base, not the PR #8 documentation branch, PR #18 planning branch, or retired Phase 1 branch.
- Working tree is clean before branch creation, or existing user changes are preserved and explicitly excluded.
- PR #16 and PR #21 changes remain present; approved files are not rewritten or discarded.
- C’s approved hooks `_reserve_run_directory` and `_finalize_run_manifest` are implemented and published on an available branch/PR before B opens a PR containing the CLI integration tests.
- C specifies the run-directory reservation failure behavior before B encodes its expected result; until then, that assertion remains pending.
- No Graph change is made. If implementation finds a necessary Graph dependency, stop and provide the exact source call chain and proposed diff for A/C approval.
- F’s approved CI matrix is used; F owns CI workflow changes.

## 3. Proposed sequence

1. **Read-only source audit:** Inspect the current CLI lifecycle, results-path consumers, artifact creation times, path validation, test collection, platform CI, and current `main` diff. Report exact candidate files and integration points to A/C/F before editing.
2. **Run-directory reservation (C-owned `cli/run.py`):** Call `_reserve_run_directory(results_dir, ticker, trade_date) -> RunContext(run_id, run_dir)` exactly once before Graph starts. It reserves `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` using `mkdir(exist_ok=False)`, retries at most 3 times, and does not write the manifest. Reservation failure behavior remains pending C's specification; once C specifies it, tests must prove Graph is never called and existing files are preserved.
3. **Manifest lifecycle integration (C-owned `cli/run.py`; B owns manifest interface):** After successful analysis and after `_offer_reports()` handles the report-save choice, call `_finalize_run_manifest(run_context, *, config, artifacts) -> ManifestWriteResult(success, manifest_path, artifacts, error)` exactly once. It must not rerun Graph or reparse the rating. Artefact collection follows the confirmed contract: `_offer_reports()` returns only the report paths this call confirmed saved (declined saves, error leftovers, and historical files excluded); the state log is registered only after `record_decision()` returns successfully, by the expected path, labelled `shared_mutable`; `results_dir` sets the path boundary and relative paths while `run_dir` decides `run_unique`; a custom save path outside `results_dir` is saved but omitted from the manifest. Pass normalized identity and only Registry-allowlisted effective config, including `input_condensation_audit_note`; retain secret redaction and `actual_input_data_provenance: not_captured`. The final artefact set and the partial-save rule remain pending B (see §1).
4. **Failure behavior:** On manifest **write** failure, preserve the completed analysis result and O4 effective rating, finish normally, show a short warning that the manifest was not saved and the run's provenance record is unavailable, show no success path, and leave no partial manifest. Retain the Phase 1 atomic-write guarantee. A report-**writer** failure is a separate case and is verified separately (see the test plan's TC-13/14 split). Assert behavior, not an exact English warning string.
5. **Offline integration tests:** B prepares `test/offline/test_o2_cli_manifest.py` against C’s contract, mainly through real `run_analysis()` with a fake Graph. Verify the call order, hook call counts, unique directory, actual artifact list, and write-failure behavior; spying on the two hooks is allowed, and the real manifest writer remains in the success path using a temporary directory. Do not open a PR containing these tests until C’s hooks are available. Keep existing O2-TC IDs: TC-04 for full CLI success, TC-13/14 for failure, TC-11 for bounded allocation/collision, and TC-05/15/19/20/21/23 for their assigned coverage. Do not add a new ID.
6. **Regression and CI (F owns CI):** Run targeted O2 tests and `pytest -q`. Ubuntu keeps the existing Python 3.11–3.14 full regression plus the Python 3.12 non-UTC job; macOS and Windows run `test/offline/test_o2_manifest.py` and `test/offline/test_o2_cli_manifest.py` on Python 3.12. Record commit SHA, commands, workflow URLs, Python/OS versions, and actual outcomes.
7. **Review handoff:** Report changed files, diff, test/CI evidence, limitations, and plan/approval references. Open a PR for review; do not approve or merge on behalf of A/F.

## 4. File boundary and ownership

Candidate paths must be checked against the verified base and team ownership before edits.

| Area | Candidate paths | Owner / guard |
|---|---|---|
| CLI lifecycle, run directory, manifest invocation | `cli/run.py` | C owns shared integration: `_reserve_run_directory`, `_finalize_run_manifest`, `_offer_reports` returning `list[Path]`, state-log registration; B owns manifest interface |
| Graph context and output paths | `tradingagents/graph/trading_graph.py` | **No Graph changes in this batch** (A-confirmed). If one proves necessary, stop with the exact call chain and proposed diff for A/C approval |
| Phase 1 writer | `tradingagents/repro/manifest.py` | B owns manifest interface; PR #21 synchronization already merged (`69e91ff1`); schema/fingerprint/redaction unchanged |
| Existing Phase 1 tests | `test/offline/test_o2_manifest.py` | Preserve |
| New CLI integration tests | `test/offline/test_o2_cli_manifest.py` | B owns; add only after C's hooks are available on a branch/PR |
| Test discovery/config | `pyproject.toml` or current test config | Change only if audit shows necessary and C/F approve ownership |
| CI workflows | `.github/workflows/ci.yml` or current workflow files | F owns test review and approved CI workflow changes |
| Setup/dependencies | `setup.py`, `pyproject.toml`, or current packaging files | Out of scope unless a specific approved need is documented; no dependency addition by default |

## 5. Stop conditions

Stop and return evidence for review if implementation requires:

- changing the approved completed-CLI-only scope or adding failed/programmatic runs;
- moving existing report/state/log paths or changing legacy artifact stability away from `shared_mutable`;
- changing manifest schema, fingerprint semantics, secret handling, or allowlist beyond the merged Registry;
- adding or redefining an official O2-TC ID;
- writing more than one manifest or writing before analysis completion/report-save handling;
- changing the approved fail-soft/fail-closed failure behavior or omitting the visible warning/no-success-path requirement;
- changing Graph or public APIs without the exact dependency and proposed diff approved by A/C;
- changing ownership assignments;
- adding a runtime dependency;
- writing CLI tests before C’s hooks are available or before C specifies reservation failure behavior;
- editing CI without F’s confirmed ownership;
- an unresolved CI platform/version or missing test-to-requirement mapping;
- rebasing, resetting, or rewriting existing Phase 1, PR #21, or PR #20 history.

## 6. Required implementation records

Before the first code edit, record the verified base SHA, branch, clean working-tree status, approved plan versions, A/F approval references, C’s CLI/test ownership confirmation, and actual coding-start timestamp with timezone. For each verification, report the exact command and actual output. Do not infer local tests from CI or vice versa. The final PR must not claim full data reproducibility without immutable input snapshots.

## 7. Approval record

- **A Stage 2 scope supplement:** Approved in PR #18 review `5959122354`, `2026-11-18T15:00:01Z`
- **F formal Stage 2 test-plan and CI matrix approval:** Approved in PR #18 review `5968062524`, `2026-11-19T01:41:23Z`
- **C/F ownership and timing confirmation:** Recorded in PR #18 review `5968754538`, `2026-11-19T03:08:27Z`
- **A integration contract (C1–C4, this revision):** Graph interface unchanged with the state log registered only after `record_decision()` succeeds; `_log_state()` writes and closes without `fsync`, which this batch accepts; `_offer_reports()` returns `list[Path]` of confirmed-saved reports only, display/prompting unchanged; `results_dir` for boundary/relative paths and `run_dir` for `run_unique`, with out-of-boundary custom save paths saved but not referenced.
- **Reservation failure behavior:** Pending C's specification
- **Final artefact set / write evidence / partial-save rule:** Pending B (see §1)
- **PR #21 writer/TC-23 synchronization:** Merged at `69e91ff115694f3455196e6a4114d4fe653fbb06`
- **O6 CLI integration:** Merged at `e4b6f9ac625f39579635c840aed98ab8dfefdaf9` (PR #20)
- **Actual baseline at this revision:** `origin/main` `102511dd44ad8779a46e09cbefe50edb8a995b45`
- **Implementation status:** Separate B/C implementation work; no implementation or CI result claimed in this planning PR
- **Tests, CI, PR, commit:** None claimed for Stage 2 implementation
- **Reapproval:** Any material scope, expected-result, path, test-ID, Graph, or ownership change requires an updated plan and renewed approval before implementation.
