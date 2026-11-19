# O2 Stage 2 Integration — Test Plan

**Document version:** v0.3-DRAFT (A clarification; filename unchanged: `…-v0.1-DRAFT.md`)
**Status:** Draft planning record. A's latest clarification is recorded here; A/F have **not** approved this version and will review the exact updated SHA. Existing formal approvals remain bound to earlier commits (§6). PR #18 remains Draft. This planning update is not implementation approval; no implementation or test/CI result is claimed.
**Owner:** B (QinQilun)
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. Joint-validation baseline: PR #21 merge `69e91ff115694f3455196e6a4114d4fe653fbb06`; O6 CLI merged via PR #20 `e4b6f9ac625f39579635c840aed98ab8dfefdaf9`. **Actual baseline verified at this plan update: `origin/main` = `102511dd44ad8779a46e09cbefe50edb8a995b45`**; re-verify and record the actual base SHA at implementation time.
**Plan update binding:** v0.3-DRAFT based on plan commit `870390d9b7d41f7da7365bc38fa55c76f080aa9d`; this update’s commit SHA is reported in PR #18.
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**Related approved plan:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` Revision 2; its approval applies to Phase 1 documentation alignment only, not Stage 2.  
**A scope supplement:** [PR #18 review 5959122354](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5959122354), submitted `2026-11-18T15:00:01Z`.  
**F formal test-plan approval:** [PR #18 review 5968062524](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968062524), submitted `2026-11-19T01:41:23Z`.  
**C/F ownership and timing confirmation:** [PR #18 review 5968754538](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968754538), submitted `2026-11-19T03:08:27Z`.

## 0. Approval boundary and plan binding

- **A-confirmed implementation scope:** completed normal CLI runs only; no Graph API change; existing legacy report/state/log paths remain; one manifest after analysis and report-save handling; fail-soft analysis result with fail-closed provenance; external saves preserved but omitted; no broadened file scope and no changes to public interfaces, schema, fingerprint, or redaction rules.
- **A latest clarification:** state-log registration is `shared_mutable` only after `record_decision()` returns normally, at the deterministic path, after write+close, with no `fsync` and no power-loss claim. Report saves, live section reports, and `message_tool.log` require this-invocation write evidence; existence alone is insufficient. Declined or wholly failed optional saves contribute no files from that save directory, including partial leftovers. Custom saves outside `results_dir` remain supported but are omitted from the manifest. C8 records the inventory method for HTML and section files without changing `save_reports()`.
- **F-confirmed test boundaries:** existing official test IDs only; separation of report-save failure from manifest-write failure; the approved three-platform CI matrix; F owns test review and approved CI workflow changes. Formal F approval of this revision’s added test cases and exact SHA remains required.
- **C ownership and remaining decisions:** C owns `cli/run.py` integration and must document the actual base SHA and exact file scope before implementation. C7 specifies `RunDirectoryUnavailable` converted by `run_analysis` to `typer.Exit(code=1)`. C8 uses existing `_report_parts(final_state)` only to compute the expected inventory; no `save_reports()`, `write_report_tree()`, `reporting.py`, Graph, schema, or public-interface change.
- **Binding:** this update records v0.3-DRAFT decisions from base plan commit `870390d9b7d41f7da7365bc38fa55c76f080aa9d`. This planning update is not implementation approval unless the recorded approvals expressly say otherwise; existing formal approvals cover earlier commits, not this revision’s new contract text or exact SHA.

## 1. Purpose and boundary

Stage 2 proposes integrating the merged standalone O2 manifest writer with completed normal CLI runs, reserving a unique run directory before Graph execution, and validating the integration on Ubuntu, macOS, and Windows. The manifest fingerprint covers approved normalized run/configuration inputs only. Unless an immutable per-run market/news snapshot exists, `actual_input_data_provenance` remains `not_captured` and no full-reproducibility claim is made.

A/F approval covers the planning scope and division of work. It does not itself claim implementation, test execution, or CI results. The approved Phase 1 writer and its 24-test evidence remain intact.

B’s separate writer/TC-23 synchronization landed through PR #21 merge `69e91ff...`. Stage 2 must still synchronize and verify the integrated CLI expectation for `input_condensation_audit_note`.

## 2. Proposed scope

### Included

- Completed normal CLI analysis runs only; failed analysis and programmatic/API runs remain out of scope unless separately approved.
- Reserve `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph execution using `mkdir(exist_ok=False)`. Retry at most 3 times; if all attempts collide, fail clearly before Graph starts without changing existing files.
- Keep existing report, state, and log paths in place. Reference only artifacts this run actually produced; label shared, unmigrated paths `shared_mutable`. If the user declines report saving, do not list that report.
- Artefact collection per A's confirmed contract (C1–C7) and C8's inventory approach: `_offer_reports()` registers only report paths this call confirmed saved when the optional save succeeds as a whole; the state log is registered only after `record_decision()` returns successfully, by its expected path; live reports and `message_tool.log` stand on their own write evidence; `results_dir` sets the path boundary and relative paths while `run_dir` decides `run_unique`; a custom save path outside `results_dir` is saved but not referenced. Because `save_reports()` returns only complete Markdown, the saved HTML/section inventory is computed per C8 from `_report_parts(final_state)`, not from the return value or a directory scan.
- Write exactly one manifest after normal CLI analysis completes and after the report-save choice is handled.
- On manifest **write** failure, preserve the completed analysis result and O4 effective rating, finish normally, show a short warning that the manifest was not saved and this run's provenance record is unavailable, show no success path, and leave no partial manifest. Retain the Phase 1 atomic-write guarantee. A report-**writer** failure is a distinct case, verified separately from the manifest-write failure.
- Keep existing official test IDs: O2-TC-04/05/11/13/14/15/19/20/21/23. Put full CLI success coverage in TC-04 and failure coverage in TC-13/14; do not add a new ID.
- Keep artifact references within the configured results boundary, use relative paths where possible, and label stability truthfully (`run_unique` for files under `run_dir`, `shared_mutable` for shared unmigrated paths).
- C owns shared `cli/run.py` integration and coordinates CLI test integration. B owns the manifest interface and `test/offline/test_o2_cli_manifest.py`. F owns test review and approved CI workflow changes.
- This batch does not change Graph, based on C’s read-only inspection. If implementation finds a necessary Graph dependency, stop and provide the exact source call chain and proposed diff for A/C approval.
- F CI matrix: Ubuntu keeps the existing Python 3.11–3.14 full regression and the Python 3.12 non-UTC job; macOS and Windows run `test/offline/test_o2_manifest.py` and `test/offline/test_o2_cli_manifest.py` on Python 3.12.
- Align O2-TC-23 with PR #9’s merged Registry: `input_condensation_audit_note` is included as an allowlisted effective-config field; unknown/unapproved fields and secrets remain excluded.

### TC-05 artifact rules

1. CLI live section reports under `results_dir/<ticker>/<date>/reports/` may be listed only when the CLI has evidence that this invocation actually wrote them. Label them `shared_mutable`; never include historical files based on directory scans or existence.
2. The optional saved report tree under `results_dir/reports/<ticker>_<stamp>/` is included only when `_offer_reports()` confirms the entire save operation succeeded. Its returned `list[Path]` must contain only files this invocation successfully saved: complete Markdown, HTML when generated, and section files actually written. Label them `shared_mutable`. The inventory is computed per C8 from `_report_parts(final_state)` plus complete Markdown and requested HTML; `save_reports()`'s single returned path is not the inventory.
3. If the user declines saving, or saving fails—even if partial files remain—do not list files from that optional saved report tree. Preserve the existing prompt/display behavior. Declining optional report saving affects only that optional save tree; independently written live section reports and `message_tool.log` remain eligible for inclusion based on their own successful write evidence.
4. Preserve saving to user-selected paths outside `results_dir`; omit those files from the manifest rather than rejecting the save path.
5. Include the state log only after `record_decision()` returns normally, then reconstruct and validate the expected path using the same effective config, ticker, and date as the writer. On call failure, do not include it even if an old file exists. Label it `shared_mutable`. No `fsync` is required for this batch; do not claim power-loss durability. Do not change the Graph interface.
6. Include `message_tool.log` only when the CLI has evidence that this invocation actually appended/wrote to it; label it `shared_mutable`. Existing-file presence alone is insufficient.
7. Artifacts confined to the reserved per-run directory remain `run_unique` under the existing contract.
8. `_artifact_references` must receive both `results_dir` and `run_dir`: use `results_dir` for containment and relative paths, and `run_dir` only to determine `run_unique`.

Both per-section sets — live run-directory reports and the saved report tree — are in the expected manifest set when their own write evidence exists; the saved set additionally requires whole-save success. This resolves the earlier pending B set-choice question.

### Excluded

- Backtests, replay, failed/programmatic runs, UI/database work, immutable vendor-data archiving, report redesign, unrelated CLI/Graph refactoring, new public return values, and the D7 Schema CI Gate.
- Changes to Phase 1 fingerprint semantics, schema version, secret redaction, or approved writer behavior.
- Moving existing report/state/log paths.
- Graph changes for this batch.
- Ownership transfer for shared files.

## 3. Stage 2 acceptance criteria

1. Each completed in-scope CLI invocation reserves `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph execution using `mkdir(exist_ok=False)`.
2. Allocation retries at most 3 times. After 3 collisions, the run fails clearly before Graph starts, Graph is never called, and all pre-existing files remain unchanged. C7 specifies `RunDirectoryUnavailable` converted by `run_analysis` to `typer.Exit(code=1)`; tests assert behavior, not fixed English wording.
3. Two completed same-ticker/date CLI runs, including same-second/concurrent starts, produce distinct run directories and manifests without overwriting prior contents.
4. Exactly one manifest is written after normal CLI analysis completes and after the report-save choice is handled.
5. Successful manifest writing displays the manifest’s unique path.
6. The manifest references only artefacts this run actually produced: reports confirmed saved by `_offer_reports()`, plus the state log only when `record_decision()` returned successfully. A declined save, files left by an error, and historical files are never listed. Shared, unmigrated paths are labelled `shared_mutable`; files under `run_dir` may be `run_unique`.
7. A failed manifest **write** leaves no partial manifest, preserves the completed analysis result and O4 effective rating, finishes normally, shows a short warning that the manifest was not saved and provenance is unavailable, and shows no success path. Tests assert behavior, not an exact English warning string. A **report-writer** failure is verified separately and must not be counted as a manifest-write failure; a whole saved-report failure registers no files from that save directory, including partial leftovers.
8. Existing report, state, log, memory, checkpoint, and public interface behavior remains compatible because existing paths are not migrated.
9. `input_condensation_audit_note` is treated as allowlisted because PR #9 merged at `d36a677...` and that merge is in the implementation base. No unapproved config keys or secret values are serialized or fingerprinted.
10. Offline tests make no network, live vendor, market-data, or LLM requests. `pytest -q` remains the planned first-layer regression command; integration-only conditions are reported separately.
11. Ubuntu retains the existing Python 3.11–3.14 full regression plus the Python 3.12 non-UTC job. macOS and Windows run the O2 writer and CLI manifest target tests on Python 3.12, with exact CI run, commit, OS, and Python versions recorded.
12. Live section reports and `message_tool.log` are included only with invocation-specific write evidence; historical files are excluded; both are labelled `shared_mutable`.
13. Both per-section sets — live reports and the saved report tree — are included when their own write evidence exists. The saved set is included only after the entire save succeeds; the returned `list[Path]` contains only files actually saved; declined saves and whole-save failures, including partial files left on disk, contribute no paths; existing prompt/display behavior is preserved.
14. A successful save to a user-selected path outside `results_dir` still saves normally but is omitted from the manifest rather than rejected.
15. The state log is included only after `record_decision()` returns normally, with its expected path reconstructed and validated using the same effective config, ticker, and date as the writer; call failure excludes the log even when an old file exists; no `fsync` or power-loss durability is claimed; no Graph interface changes are made.
16. `_artifact_references` receives both `results_dir` and `run_dir`; `results_dir` is used for containment and relative paths, and `run_dir` only for `run_unique`.
17. The saved HTML and section-file inventory is not inferred from `save_reports()`'s complete-Markdown return. It is computed per C8 from `_report_parts(final_state)` before the save, includes complete Markdown and HTML only when requested, and is registered only after a normal whole-save return. Pre-existing files outside that expected set are excluded; expected paths overwritten by this invocation are included. If `_report_parts` is rejected for use, no implementation starts until C/A approves a specific alternative.

## 4. Proposed test coverage and traceability

Use the existing official O2-TC IDs. Do not add a new ID or silently redefine a Phase 1 unit test as integration evidence.

| Existing ID | Stage 2 integration assertion | Mapping |
|---|---|---|
| O2-TC-04 | Full CLI success coverage: a completed invocation reserves the approved run path before Graph, writes exactly one manifest after analysis/report-save handling, displays its unique path, and references exactly the artefact set this run produced | O2-FR-01/02/03/10 |
| O2-TC-05 | Integrated artefact references match this run's records exactly: only reports `_offer_reports()` confirmed saved plus the state log registered after a successful `record_decision()`; declined saves, save-directory leftovers, and historical files absent; shared paths `shared_mutable`, `run_dir` files `run_unique`, all relative to `results_dir` and inside it | O2-FR-10 |
| O2-TC-11 | Same-second/concurrent invocations remain distinct; allocation retries at most 3 times; after 3 collisions Graph is never called, pre-existing files remain unchanged, and the run reports the failure explicitly | O2-FR-02/03 |
| O2-TC-13 | **Manifest write failure (unchanged scope)** — serialization/write/promotion failure in the manifest writer: no partial manifest, completed analysis result and O4 effective rating preserved, no success path | O2-FR-01/13/14 |
| O2-TC-14 | **Manifest write failure (unchanged scope)** — unwritable destination or promotion failure: no partial `manifest.json`, run finishes normally with preserved result/rating and no success path | O2-FR-01/13/14 |
| O2-TC-15 | Invalid/traversal identity or artifact path cannot write outside the configured results boundary | O2-FR-03; O2-NFR-05 |
| O2-TC-19 | Integration tests use fakes and do not call external services | O2-NFR-04 |
| O2-TC-20 | `pytest -q` regression confirms agreed existing behavior and interfaces | O2-NFR-06 |
| O2-TC-21 | O2 writer and CLI manifest target tests run on Ubuntu, macOS, and Windows under F’s approved matrix | O2-NFR-05 |
| O2-TC-23 | Integrated effective config includes merged allowlisted `input_condensation_audit_note`; unknown keys and secrets are absent | O2-FR-05, O2-FR-11, O2-NFR-03 |

## 4a. A-confirmed contract and required test cases

A's confirmed contract items (C1–C7 in the execution plan) and C8's inventory approach drive the expected results:

| Contract | Confirmed rule | Required test cases |
|---|---|---|
| C1 state log | registered only after `record_decision()` returns successfully, by the expected path; not registered on failure even if a stale/historical file exists | success registers the expected path; failure registers nothing; a pre-existing file is not picked up |
| C2 `_log_state()` boundary | writes and closes without `fsync`; acceptable for normal-run registration | no durability claim asserted; registration depends on the successful return, not on file inspection |
| C3 `_offer_reports()` | returns `list[Path]` only when the optional save succeeded **as a whole**; whole failure registers nothing from that directory | exact set and labels; declined → none; whole-save failure → none including partial leftovers |
| C4 artefact base | `results_dir` for boundary + relative paths; `run_dir` for `run_unique`; no scanning | relative paths inside `results_dir`; `run_unique` only under `run_dir`; historical files never appear |
| C5 live reports & log | each registered on its own confirmed write | live section write succeeds → registered; `message_tool.log` write succeeds → registered; raising write → not registered |
| C6 external path | saves succeed but the reference is omitted | **two separate assertions**: the save happened, and the manifest omits it |
| C7 reservation | 3 attempts, then `RunDirectoryUnavailable` converted to `typer.Exit(code=1)` | Graph never called; pre-existing files byte-unchanged; failure reported explicitly |
| C8 saved-report inventory | `save_reports()` returns only complete Markdown; CLI computes expected writer-owned paths from `_report_parts(final_state)` + complete Markdown + requested HTML and registers them only after normal whole-save return | exact HTML/section inventory; stale unrelated file excluded; stale expected path overwritten by this run included; no scan/mtime/existence inference; save failure registers none |

**Both per-section sets:** the live run-directory reports and the saved report tree are both in the expected manifest set when their own write evidence exists. The saved set additionally requires whole-save success; a declined or wholly failed save contributes nothing from that save directory.

**Required coverage, at the level TC-05's success case needs:**

1. **Exact artefact set and per-item stability labels** for a successful run — one entry each, correct label per item (`shared_mutable` for unmigrated shared locations, `run_unique` only under `run_dir`).
2. **Whole report-save failure** — no file from that save directory is registered, including partial leftovers.
3. **Manifest write failure (TC-13 / TC-14)** — keeps its **existing** meaning: the manifest writer fails; no partial manifest, result and rating preserved, no success path.
4. **Report-writer partial failure — independent case** — a report file fails to save; verified in its own test, not folded into TC-13/14, so the approved TC-13/14 mapping is unchanged.
5. **State log write and close failure** — not registered, even with a leftover file present.
6. **Historical-file exclusion** — a stale file pre-created under `results_dir` never appears.
7. **Declined save** — no report entries.
8. **External save path** — saves successfully, reference omitted; both asserted separately.
9. **Three reservation collisions** — Graph called zero times, existing files unchanged, failure reported.
10. **C8 saved-report inventory** — a successful save registers the exact complete Markdown, requested HTML, and non-empty section files; a pre-existing unrelated file is excluded; a pre-existing expected path overwritten by this invocation is included; no directory scan or existence check determines membership; a whole-save failure registers none.

All driven through the real `run_analysis()` with a fake Graph; real file writes and real JSON parsing are retained, with the manifest writer exercised against a temporary directory.

## 5. Decisions and remaining work

### Approved

- Run directory: `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/`, reserved before Graph with `mkdir(exist_ok=False)`, up to 3 total attempts, then a clear failure before Graph without changing existing files.
- Existing report, state, and log paths remain in place; shared unmigrated paths are `shared_mutable`; files under `run_dir` may be `run_unique`; declined report saves are not listed.
- **A's confirmed contract (C1–C7) and C8 inventory approach:** Graph interface unchanged; state log registered only after a successful `record_decision()`, by the expected path; `_log_state()` writes and closes without `fsync`, accepted for this batch; `_offer_reports()` returns `list[Path]` only on whole-save success, display unchanged; `_artifact_references` takes both `results_dir` and `run_dir`; live reports and `message_tool.log` stand on their own write evidence; both live and saved per-section sets are included when their own write evidence exists; out-of-boundary custom saves saved but unreferenced; reservation aborts after 3 collisions with `RunDirectoryUnavailable` converted to `typer.Exit(code=1)` and Graph uncalled. Because `save_reports()` returns only complete Markdown, C8 computes expected saved HTML/section paths from `_report_parts(final_state)` and registers them only after a normal whole-save return.
- Exactly one manifest after normal CLI analysis completes and after report-save handling; failure behaviour is fail-soft for the analysis result and fail-closed for provenance claims.
- Keep existing test IDs; no new ID. Full CLI success is TC-04. **TC-13/14 keep their original manifest-write failure meaning**; the report-writer partial failure is an independent case.
- C owns shared `cli/run.py` integration and coordinates CLI test integration. B owns manifest interface and `test/offline/test_o2_cli_manifest.py`. F owns test review and approved CI workflow changes.
- No Graph change for this batch. If a Graph dependency is found, stop with the exact call chain and proposed diff for A/C approval.
- PR #21 merge `69e91ff...` is the joint-validation baseline.
- F CI matrix: Ubuntu Python 3.11–3.14 full regression plus Python 3.12 non-UTC job; macOS/Windows Python 3.12 writer and CLI manifest target tests.
- O2-TC-23 maps to O2-FR-05, O2-FR-11, and O2-NFR-03.

### Pending confirmation

Only genuinely unspecified items remain:

- **A:** confirmation of the exact file scope; review of this exact updated SHA.
- **F:** formal approval of this revised test plan and its added test cases.
- **C:** record the actual base SHA and exact `cli/run.py` file scope before implementation; confirm the C8 read-only `_report_parts` import or obtain C/A approval for a specific alternative; implement the specified hooks and write-evidence plumbing.

The earlier B set-choice question is resolved by the approved TC-05 artifact rules: both live and saved per-section sets are included when their own write evidence exists, with the saved set requiring whole-save success.

### Remaining before implementation results are claimed

- Verify current `origin/main` at implementation time, record the actual base SHA, and confirm it contains PR #9 merge `d36a677...` and PR #21 merge `69e91ff...`.
- The interface B tests against is specified in the execution plan (§1 C1–C7, §3); publishing implementation code first is not required by this plan.
- Implement and verify the Stage 2 TC-23 CLI expectation in the separate implementation PR.
- Record actual test and CI results after execution; none are claimed here.

## 6. Approval and evidence record

**Binding of existing approvals (see execution plan §7 for the full table):** A's approval `5959122354` is bound to `3b60af1`; F's approval `5968062524` is bound to `e03b67d`; F's `5968754538` is a supplement, not a re-approval. **F's approval covers the unchanged TC-ID mapping and CI matrix; it does not approve this revision's new contract cases (C1–C7) or the independent report-writer case.**

- **A Stage 2 scope supplement:** Approved in PR #18 review `5959122354` (bound to `3b60af1`), `2026-11-18T15:00:01Z`
- **F formal Stage 2 test-plan and CI matrix approval:** Approved in PR #18 review `5968062524` (bound to `e03b67d`), `2026-11-19T01:41:23Z`; still applies to TC-ID mapping and CI matrix only
- **C/F ownership and timing confirmation:** PR #18 review `5968754538`
- **A integration contract (C1–C7):** Confirmed; see §4a
- **Latest A clarification:** Recorded in this v0.3-DRAFT update; state log, report/live/log write evidence, declined/whole-failure exclusion, external-path omission, and C8 saved-report inventory are specified. A/F version approval is pending review of the exact updated SHA; no review identifier was supplied.
- **Plan update binding:** Base plan commit `870390d9b7d41f7da7365bc38fa55c76f080aa9d`; this update’s commit SHA is reported in PR #18.
- **Pending:** F's formal approval of this revised test plan and added cases; A's file-scope confirmation and review of this SHA; C's recorded actual base SHA/file scope and C8 `_report_parts` confirmation before implementation
- **PR #21 writer/TC-23 synchronization:** Merged at `69e91ff115694f3455196e6a4114d4fe653fbb06`
- **O6 CLI integration:** Merged at `e4b6f9ac625f39579635c840aed98ab8dfefdaf9` (PR #20)
- **Actual baseline at this revision:** `origin/main` `102511dd44ad8779a46e09cbefe50edb8a995b45`
- **Implementation/test execution/CI results:** Not claimed
- **Reapproval:** Any material scope, expected-result, path, test-ID, or ownership change requires an updated plan and renewed approval before implementation.
