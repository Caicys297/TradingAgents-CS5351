# O2 Stage 2 Integration — Test Plan

**Document version:** v0.2-DRAFT  
**Status:** Draft planning record; A scope supplement approved; F formal test plan and CI matrix approved; C ownership confirmed; **A's integration contract confirmed (this revision)**; final artefact set pending B. PR #18 remains Draft. Implementation and test execution are not claimed here.  
**Owner:** B (QinQilun)  
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. Joint-validation baseline: PR #21 merge `69e91ff115694f3455196e6a4114d4fe653fbb06`; O6 CLI merged via PR #20 `e4b6f9ac625f39579635c840aed98ab8dfefdaf9`. **Actual baseline verified at this plan update: `origin/main` = `102511dd44ad8779a46e09cbefe50edb8a995b45`**; re-verify and record the actual base SHA at implementation time.  
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**Related approved plan:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` Revision 2; its approval applies to Phase 1 documentation alignment only, not Stage 2.  
**A scope supplement:** [PR #18 review 5959122354](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5959122354), submitted `2026-11-18T15:00:01Z`.  
**F formal test-plan approval:** [PR #18 review 5968062524](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968062524), submitted `2026-11-19T01:41:23Z`.  
**C/F ownership and timing confirmation:** [PR #18 review 5968754538](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968754538), submitted `2026-11-19T03:08:27Z`.

## 1. Purpose and boundary

Stage 2 proposes integrating the merged standalone O2 manifest writer with completed normal CLI runs, reserving a unique run directory before Graph execution, and validating the integration on Ubuntu, macOS, and Windows. The manifest fingerprint covers approved normalized run/configuration inputs only. Unless an immutable per-run market/news snapshot exists, `actual_input_data_provenance` remains `not_captured` and no full-reproducibility claim is made.

A/F approval covers the planning scope and division of work. It does not itself claim implementation, test execution, or CI results. The approved Phase 1 writer and its 24-test evidence remain intact.

B’s separate writer/TC-23 synchronization landed through PR #21 merge `69e91ff...`. Stage 2 must still synchronize and verify the integrated CLI expectation for `input_condensation_audit_note`.

## 2. Proposed scope

### Included

- Completed normal CLI analysis runs only; failed analysis and programmatic/API runs remain out of scope unless separately approved.
- Reserve `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph execution using `mkdir(exist_ok=False)`. Retry at most 3 times; if all attempts collide, fail clearly before Graph starts without changing existing files.
- Keep existing report, state, and log paths in place. Reference only artifacts this run actually produced; label shared, unmigrated paths `shared_mutable`. If the user declines report saving, do not list that report.
- Artefact collection per A's confirmed contract (C1–C4): `_offer_reports()` returns only the report paths this call confirmed saved; the state log is registered only after `record_decision()` returns successfully, by its expected path; `results_dir` sets the path boundary and relative paths while `run_dir` decides `run_unique`; a custom save path outside `results_dir` is saved but not referenced.
- Write exactly one manifest after normal CLI analysis completes and after the report-save choice is handled.
- On manifest **write** failure, preserve the completed analysis result and O4 effective rating, finish normally, show a short warning that the manifest was not saved and this run's provenance record is unavailable, show no success path, and leave no partial manifest. Retain the Phase 1 atomic-write guarantee. A report-**writer** failure is a distinct case, verified separately from the manifest-write failure.
- Keep existing official test IDs: O2-TC-04/05/11/13/14/15/19/20/21/23. Put full CLI success coverage in TC-04 and failure coverage in TC-13/14; do not add a new ID.
- Keep artifact references within the configured results boundary, use relative paths where possible, and label stability truthfully (`run_unique` for files under `run_dir`, `shared_mutable` for shared unmigrated paths).
- C owns shared `cli/run.py` integration and coordinates CLI test integration. B owns the manifest interface and `test/offline/test_o2_cli_manifest.py`. F owns test review and approved CI workflow changes.
- This batch does not change Graph, based on C’s read-only inspection. If implementation finds a necessary Graph dependency, stop and provide the exact source call chain and proposed diff for A/C approval.
- F CI matrix: Ubuntu keeps the existing Python 3.11–3.14 full regression and the Python 3.12 non-UTC job; macOS and Windows run `test/offline/test_o2_manifest.py` and `test/offline/test_o2_cli_manifest.py` on Python 3.12.
- Align O2-TC-23 with PR #9’s merged Registry: `input_condensation_audit_note` is included as an allowlisted effective-config field; unknown/unapproved fields and secrets remain excluded.

### Excluded

- Backtests, replay, failed/programmatic runs, UI/database work, immutable vendor-data archiving, report redesign, unrelated CLI/Graph refactoring, new public return values, and the D7 Schema CI Gate.
- Changes to Phase 1 fingerprint semantics, schema version, secret redaction, or approved writer behavior.
- Moving existing report/state/log paths.
- Graph changes for this batch.
- Ownership transfer for shared files.

## 3. Stage 2 acceptance criteria

1. Each completed in-scope CLI invocation reserves `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph execution using `mkdir(exist_ok=False)`.
2. Allocation retries at most 3 times. After 3 collisions, the run fails clearly before Graph starts, Graph is never called, and all pre-existing files remain unchanged.
3. Two completed same-ticker/date CLI runs, including same-second/concurrent starts, produce distinct run directories and manifests without overwriting prior contents.
4. Exactly one manifest is written after normal CLI analysis completes and after the report-save choice is handled.
5. Successful manifest writing displays the manifest’s unique path.
6. The manifest references only artefacts this run actually produced: reports confirmed saved by `_offer_reports()`, plus the state log only when `record_decision()` returned successfully. A declined save, files left by an error, and historical files are never listed. Shared, unmigrated paths are labelled `shared_mutable`; files under `run_dir` may be `run_unique`.
7. A failed manifest **write** leaves no partial manifest, preserves the completed analysis result and O4 effective rating, finishes normally, shows a short warning that the manifest was not saved and provenance is unavailable, and shows no success path. Tests assert behavior, not an exact English warning string. A **report-writer** failure is verified separately: it must not be counted as a manifest-write failure, and whether other successfully saved files remain referenced is pending B's decision.
8. Existing report, state, log, memory, checkpoint, and public interface behavior remains compatible because existing paths are not migrated.
9. `input_condensation_audit_note` is treated as allowlisted because PR #9 merged at `d36a677...` and that merge is in the implementation base. No unapproved config keys or secret values are serialized or fingerprinted.
10. Offline tests make no network, live vendor, market-data, or LLM requests. `pytest -q` remains the planned first-layer regression command; integration-only conditions are reported separately.
11. Ubuntu retains the existing Python 3.11–3.14 full regression plus the Python 3.12 non-UTC job. macOS and Windows run the O2 writer and CLI manifest target tests on Python 3.12, with exact CI run, commit, OS, and Python versions recorded.

## 4. Proposed test coverage and traceability

Use the existing official O2-TC IDs. Do not add a new ID or silently redefine a Phase 1 unit test as integration evidence.

| Existing ID | Stage 2 integration assertion | Mapping |
|---|---|---|
| O2-TC-04 | Full CLI success coverage: a completed invocation reserves the approved run path before Graph, writes exactly one manifest after analysis/report-save handling, displays its unique path, and references exactly the artefact set this run produced (state log only on a successful `record_decision()`) | O2-FR-01/02/03/10 |
| O2-TC-05 | Integrated artefact references match this run's records exactly: only reports `_offer_reports()` confirmed saved plus the state log registered after a successful `record_decision()`; declined saves, error leftovers, and historical files absent; shared paths `shared_mutable`, `run_dir` files `run_unique`, all relative to `results_dir` and inside it | O2-FR-10 |
| O2-TC-11 | Same-second/concurrent invocations remain distinct; allocation retries at most 3 times; after 3 collisions Graph is never called and pre-existing files remain unchanged | O2-FR-02/03 |
| O2-TC-13 | **Report-writer failure** (a report file fails to save): verified separately from manifest write; whether other successfully saved files stay referenced is pending B; no success path is shown | O2-FR-01/13/14 |
| O2-TC-14 | **Manifest write failure** (unwritable destination or promotion failure): leaves no partial `manifest.json`, the run finishes normally with preserved result/rating and no success path | O2-FR-01/13/14 |
| O2-TC-15 | Invalid/traversal identity or artifact path cannot write outside the configured results boundary | O2-FR-03; O2-NFR-05 |
| O2-TC-19 | Integration tests use fakes and do not call external services | O2-NFR-04 |
| O2-TC-20 | `pytest -q` regression confirms agreed existing behavior and interfaces | O2-NFR-06 |
| O2-TC-21 | O2 writer and CLI manifest target tests run on Ubuntu, macOS, and Windows under F’s approved matrix | O2-NFR-05 |
| O2-TC-23 | Integrated effective config includes merged allowlisted `input_condensation_audit_note`; unknown keys and secrets are absent | O2-FR-05, O2-FR-11, O2-NFR-03 |

## 4a. A-confirmed contract and required test cases

A's four confirmed points (C1–C4) drive the expected results:

| Contract | Confirmed rule | Required test cases |
|---|---|---|
| C1 state log | registered only after `record_decision()` returns successfully, by the expected path; not registered on failure even if a stale/historical file exists | success registers the expected path; failure registers nothing; a pre-existing file is not picked up |
| C2 `_log_state()` boundary | writes and closes without `fsync`; acceptable for normal-run registration | no durability claim asserted; registration depends on the successful return, not on file inspection |
| C3 `_offer_reports()` | returns `list[Path]` of confirmed-saved reports only; display/prompting unchanged | exact file set and labels; declined save → none; error leftover → none; historical → none |
| C4 path base | `results_dir` for boundary + relative paths; `run_dir` for `run_unique`; custom path outside `results_dir` saved but omitted | relative paths inside `results_dir`; `run_unique` only under `run_dir`; outside path saved, absent from manifest |

**Required coverage (exact file set and labels):**
1. **Exact set and labels** — the manifest's `artifacts` equals exactly the confirmed set, one entry each, with the correct `shared_mutable` / `run_unique` label.
2. **Declined save** — no report entries; other confirmed artefacts follow their own verdicts.
3. **Partial report-save failure** — the failing file is not claimed; whether other successfully saved files remain referenced is a pending B decision, so the test asserts no *failed* file is referenced and marks the rest as pending.
4. **Historical-file exclusion** — a stale file pre-created under `results_dir` never appears.
5. **External path** — a custom save path outside `results_dir` still saves but is omitted from the manifest.
6. **State log success registration** — appears with `shared_mutable` after a successful `record_decision()`.
7. **State log failure non-registration** — absent after `record_decision()` raises, even with a leftover file present.
8. **TC-13 (report writer) vs TC-14 (manifest writer) split** — two distinct tests; a report-writer failure must not be reported as a manifest-write failure.

All driven through the real `run_analysis()` with a fake Graph; real file writes and real JSON parsing are retained, with the manifest writer exercised against a temporary directory.

## 5. Decisions and remaining work

### Approved

- Run directory: `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/`, reserved before Graph with `mkdir(exist_ok=False)`, up to 3 total attempts, then a clear failure before Graph without changing existing files.
- Existing report, state, and log paths remain in place; shared unmigrated paths are `shared_mutable`; files under `run_dir` may be `run_unique`; declined report saves are not listed.
- **A's confirmed contract (C1–C4):** Graph interface unchanged; state log registered only after a successful `record_decision()`, by the expected path; `_log_state()` writes and closes without `fsync`, accepted for this batch; `_offer_reports()` returns `list[Path]` of confirmed-saved reports with display unchanged; `results_dir` for boundary/relative paths, `run_dir` for `run_unique`, out-of-boundary custom saves saved but unreferenced.
- Exactly one manifest after normal CLI analysis completes and after report-save handling; failure behavior is fail-soft for the analysis result and fail-closed for provenance claims. Report-writer failure (TC-13) and manifest-write failure (TC-14) are verified separately.
- Keep existing test IDs; no new ID. Full CLI success is TC-04; failures are TC-13/14.
- C owns shared `cli/run.py` integration and coordinates CLI test integration. B owns manifest interface and `test/offline/test_o2_cli_manifest.py`. F owns test review and approved CI workflow changes.
- No Graph change for this batch. If a Graph dependency is found, stop with the exact call chain and proposed diff for A/C approval.
- PR #21 merge `69e91ff...` is the joint-validation baseline.
- F CI matrix: Ubuntu Python 3.11–3.14 full regression plus Python 3.12 non-UTC job; macOS/Windows Python 3.12 writer and CLI manifest target tests.
- O2-TC-23 maps to O2-FR-05, O2-FR-11, and O2-NFR-03.

### Pending B's confirmation

These are open in this revision and are not decided here:

- The **final artefact set**: whether live per-section reports, the complete-report directory, the state log, and `message_tool.log` are all included.
- The **write evidence required for each** of those artefacts.
- **Partial report-save failure**: whether references to the other successfully saved files are kept.

### Remaining before implementation results are claimed

- Verify current `origin/main` at implementation time, record the actual base SHA, and confirm it contains PR #9 merge `d36a677...` and PR #21 merge `69e91ff...`.
- C must make the approved `cli/run.py` contract/order available before B adds `test/offline/test_o2_cli_manifest.py`; the current `main` does not yet contain the Stage 2 CLI integration.
- Implement and verify the Stage 2 TC-23 CLI expectation in the separate implementation PR.
- Record actual test and CI results after execution; none are claimed here.

## 6. Approval and evidence record

- **A Stage 2 scope supplement:** Approved in PR #18 review `5959122354`, `2026-11-18T15:00:01Z`
- **F formal Stage 2 test-plan and CI matrix approval:** Approved in PR #18 review `5968062524`, `2026-11-19T01:41:23Z`
- **C/F ownership and timing confirmation:** Recorded in PR #18 review `5968754538`, `2026-11-19T03:08:27Z`
- **A integration contract (C1–C4):** Confirmed; see §4a for the resulting test cases
- **Final artefact set / write evidence / partial-save rule:** Pending B
- **PR #21 writer/TC-23 synchronization:** Merged at `69e91ff115694f3455196e6a4114d4fe653fbb06`
- **O6 CLI integration:** Merged at `e4b6f9ac625f39579635c840aed98ab8dfefdaf9` (PR #20)
- **Actual baseline at this revision:** `origin/main` `102511dd44ad8779a46e09cbefe50edb8a995b45`
- **Implementation/test execution/CI results:** Not claimed in this planning PR
- **Reapproval:** Any material scope, expected-result, path, test-ID, or ownership change requires an updated plan and renewed approval before implementation.
