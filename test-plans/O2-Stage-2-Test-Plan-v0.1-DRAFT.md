# O2 Stage 2 Integration — Test Plan

**Document version:** v0.1-DRAFT  
**Status:** Draft; A approved the Stage 2 scope supplement in PR #18 review `5959122354`; F’s formal test-plan approval and C’s CLI/test ownership confirmation remain pending. Stage 2 implementation and test execution are not authorized.  
**Owner:** B (QinQilun)  
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. The implementation base must be the verified current `origin/main` containing that merge; record the actual base SHA at implementation time.  
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**Related approved plan:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` Revision 2; its approval applies to Phase 1 documentation alignment only, not Stage 2.  
**A scope supplement:** [PR #18 review 5959122354](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5959122354), submitted `2026-11-18T15:00:01Z`.

## 1. Purpose and boundary

Stage 2 proposes integrating the merged standalone O2 manifest writer with completed normal CLI runs, reserving a unique run directory before Graph execution, and validating the integration on Ubuntu, macOS, and Windows. The manifest fingerprint covers approved normalized run/configuration inputs only. Unless an immutable per-run market/news snapshot exists, `actual_input_data_provenance` remains `not_captured` and no full-reproducibility claim is made.

This is a new approval unit. It does not authorize coding, test execution, CI changes, or merging. The approved Phase 1 writer and its 24-test evidence remain intact.

The Phase 1 24-test evidence and current `main` writer do not validate the newer `input_condensation_audit_note` allowlist expectation. B’s separate writer/TC-23 synchronization must land before Stage 2 can verify that expectation.

## 2. Proposed scope

### Included

- Completed normal CLI analysis runs only; failed analysis and programmatic/API runs remain out of scope unless separately approved.
- Reserve `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph execution using `mkdir(exist_ok=False)`. Retry at most 3 times; if all attempts collide, fail clearly before Graph starts without changing existing files.
- Keep existing report, state, and log paths in place. Reference only artifacts that actually exist when the manifest is written; label existing legacy artifacts `shared_mutable`.
- Write exactly one manifest after normal CLI analysis completes and after the report-save choice is handled.
- On manifest write failure, preserve the completed analysis result and O4 effective rating, finish normally, show a short warning that the manifest was not saved and this run’s provenance record is unavailable, show no success path, and leave no partial manifest.
- Keep existing official test IDs: O2-TC-04/05/11/13/14/15/19/20/21/23. Put full CLI success coverage in TC-04 and failure coverage in TC-13/14; do not add a new ID.
- Keep artifact references within the configured results boundary, use relative paths where possible, and label stability truthfully (`run_unique`, `shared_mutable`, `not_persisted`).
- Add CLI integration coverage at `test/offline/test_o2_cli_manifest.py` after C confirms the CLI/test ownership split.
- B owns the Phase 1 writer and TC-23 synchronization. C owns `cli/run.py` integration; Graph files are touched only if read-only inspection proves it is necessary.
- F owns CI coordination: Ubuntu keeps the existing Python 3.11–3.14 full regression; macOS and Windows run the O2 writer and CLI manifest target tests on Python 3.12.
- Align O2-TC-23 with PR #9’s merged Registry: `input_condensation_audit_note` is included as an allowlisted effective-config field; unknown/unapproved fields and secrets remain excluded.

### Excluded

- Backtests, replay, failed/programmatic runs, UI/database work, immutable vendor-data archiving, report redesign, unrelated CLI/Graph refactoring, new public return values, and the D7 Schema CI Gate.
- Changes to Phase 1 fingerprint semantics, schema version, secret redaction, or approved writer behavior except the separately approved B-owned TC-23 synchronization.
- Moving existing report/state/log paths.
- Ownership transfer for shared files. C remains the `cli/run.py` integrator; Graph changes require read-only proof of necessity. F coordinates CI integration.

## 3. Stage 2 acceptance criteria

1. Each completed in-scope CLI invocation reserves `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` before Graph execution using `mkdir(exist_ok=False)`.
2. Allocation retries at most 3 times. After 3 collisions, the run fails clearly before Graph starts, and all pre-existing files remain unchanged.
3. Two completed same-ticker/date CLI runs, including same-second/concurrent starts, produce distinct run directories and manifests without overwriting prior contents.
4. Exactly one manifest is written after normal CLI analysis completes and after the report-save choice is handled.
5. Successful manifest writing displays the manifest’s unique path.
6. The manifest references only artifacts that actually exist at write time. Existing legacy artifacts are labelled `shared_mutable`; artifact paths stay within the results boundary and are relative where possible.
7. A failed manifest write leaves no partial manifest, preserves the completed analysis result and O4 effective rating, finishes normally, shows a short warning that the manifest was not saved and provenance is unavailable, and shows no success path. Tests assert behavior, not an exact English warning string.
8. Existing report, state, log, memory, checkpoint, and public interface behavior remains compatible because existing paths are not migrated.
9. `input_condensation_audit_note` is treated as allowlisted because PR #9 merged at `d36a677...` and that merge is in the implementation base. No unapproved config keys or secret values are serialized or fingerprinted.
10. Offline tests make no network, live vendor, market-data, or LLM requests. `pytest -q` remains the planned first-layer regression command; integration-only conditions are reported separately.
11. Ubuntu retains the existing Python 3.11–3.14 full regression. macOS and Windows run the O2 writer and CLI manifest target tests on Python 3.12, with exact CI run, commit, OS, and Python versions recorded.

## 4. Proposed test coverage and traceability

Use the existing official O2-TC IDs. Do not add a new ID or silently redefine a Phase 1 unit test as integration evidence.
B’s separate writer/TC-23 synchronization must land before the TC-23 Stage 2 expectation can pass.

| Existing ID | Stage 2 integration assertion | Mapping |
|---|---|---|
| O2-TC-04 | Full CLI success coverage: a completed invocation reserves the approved run path before Graph, writes exactly one manifest after analysis/report-save handling, displays its unique path, and references only actual artifacts | O2-FR-01/02/03/10 |
| O2-TC-05 | Integrated artifact references stay inside results root, are relative where possible, and label legacy artifacts `shared_mutable` | O2-FR-10 |
| O2-TC-11 | Same-second/concurrent invocations remain distinct; allocation retries at most 3 times; after 3 collisions Graph never starts and pre-existing files remain unchanged | O2-FR-02/03 |
| O2-TC-13 | Integrated serialization failure leaves no partial manifest, preserves the completed analysis result and O4 effective rating, and shows no success path | O2-FR-01/13/14 |
| O2-TC-14 | Unwritable destination or promotion failure leaves no partial `manifest.json`; the run finishes normally with preserved result/rating and no success path | O2-FR-01/13/14 |
| O2-TC-15 | Invalid/traversal identity or artifact path cannot write outside the configured results boundary | O2-FR-03; O2-NFR-05 |
| O2-TC-19 | Integration tests use fakes and do not call external services | O2-NFR-04 |
| O2-TC-20 | `pytest -q` regression confirms agreed existing behavior and interfaces | O2-NFR-06 |
| O2-TC-21 | O2 writer and CLI manifest target tests run on Ubuntu, macOS, and Windows under F’s approved matrix | O2-NFR-05 |
| O2-TC-23 | Integrated effective config includes merged allowlisted `input_condensation_audit_note`; unknown keys and secrets are absent | O2-FR-05, O2-FR-11, O2-NFR-03 |

## 5. Decisions

### Resolved by A’s scope supplement

- Run directory: `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/`, reserved before Graph with `mkdir(exist_ok=False)`, at most 3 retries, then a clear failure before Graph without changing existing files.
- Existing report, state, and log paths remain in place; only actual artifacts are referenced; legacy artifacts are `shared_mutable`.
- Exactly one manifest after normal CLI analysis completes and after report-save handling; failure behavior is fail-soft for the analysis result and fail-closed for provenance claims.
- Keep existing test IDs; no new ID. Full CLI success is TC-04; failure is TC-13/14.
- B owns writer/TC-23 synchronization. C owns `cli/run.py`; Graph files only if read-only inspection proves necessary. New CLI test file: `test/offline/test_o2_cli_manifest.py`, after C confirms the CLI/test ownership split.
- F CI matrix: Ubuntu Python 3.11–3.14 full regression; macOS and Windows Python 3.12 O2 writer and CLI manifest target tests.
- O2-TC-23 maps to O2-FR-05, O2-FR-11, and O2-NFR-03.

### Remaining before implementation

- F formal test-plan approval and CI coordination confirmation.
- C confirmation of the CLI/test ownership split and any unavoidable Graph read-only dependency.
- Verify current `origin/main` at implementation time; it must contain PR #9 merge `d36a677...`. Record the actual base SHA.
- Confirm the separate B-owned writer/TC-23 synchronization has landed before verifying TC-23’s Stage 2 expectation.
- Any proposal to move existing report/state/log paths requires a new approval.

## 6. Approval and evidence record

- **A Stage 2 scope supplement:** Approved in PR #18 review `5959122354`, `2026-11-18T15:00:01Z`
- **F formal Stage 2 test-plan approval:** Pending
- **C CLI/test ownership split:** Pending confirmation
- **Implementation start:** Not started / not authorized
- **Test execution and CI:** Not run; no result claimed
- **Reapproval:** Any material scope, expected-result, path, test-ID, or ownership change requires an updated plan and renewed approval before implementation.
