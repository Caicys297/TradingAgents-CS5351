# O2 Stage 2 Integration — Test Plan

**Document version:** v0.1-DRAFT  
**Status:** Draft for A/F/C review; Stage 2 implementation and test execution are not approved.  
**Owner:** B (QinQilun)  
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. Current `origin/main` was fetched and verified at dedicated-branch creation; the verified SHA is the same commit. If `main` advances before implementation, record the actual base SHA and recheck the allowlist.  
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**Related approved plan:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` Revision 2; its approval applies to Phase 1 documentation alignment only, not Stage 2.

## 1. Purpose and boundary

Stage 2 proposes integrating the merged standalone O2 manifest writer with completed normal CLI runs, reserving a unique run directory before Graph execution, and validating the integration on Ubuntu, macOS, and Windows. The manifest fingerprint covers approved normalized run/configuration inputs only. Unless an immutable per-run market/news snapshot exists, `actual_input_data_provenance` remains `not_captured` and no full-reproducibility claim is made.

This is a new approval unit. It does not authorize coding, test execution, CI changes, or merging. The approved Phase 1 writer and its 24-test evidence remain intact.

The Phase 1 24-test evidence and current `main` writer do not validate the newer `input_condensation_audit_note` allowlist expectation. Stage 2 implementation and test synchronization/verification remain pending and are part of this plan.

## 2. Proposed scope

### Included

- Completed normal CLI analysis runs only; failed analysis and programmatic/API runs remain out of scope unless separately approved.
- Reserve a collision-resistant run ID and unique directory beneath the configured results root before Graph execution.
- Invoke the existing Phase 1 writer for the completed run and collect approved metadata/artifact references without expanding the writer's allowlist beyond the merged Registry.
- Preserve the approved fail-soft manifest-write behavior: the completed analysis result remains available, a provenance-failed warning is visible, no success path/provenance claim is shown, and no partial `manifest.json` remains.
- Keep artifact references within the configured results boundary, use relative paths where possible, and label stability truthfully (`run_unique`, `shared_mutable`, `not_persisted`).
- Add offline CLI/Graph integration and compatibility checks, then coordinate three-platform CI acceptance with F.
- Align O2-TC-23 with PR #9's merged Registry: `input_condensation_audit_note` is included as an allowlisted effective-config field; unknown/unapproved fields and secrets remain excluded.

### Excluded

- Backtests, replay, failed/programmatic runs, UI/database work, immutable vendor-data archiving, report redesign, unrelated CLI/Graph refactoring, new public return values, and the D7 Schema CI Gate.
- Changes to Phase 1 fingerprint semantics, schema version, secret redaction, or approved writer behavior except a separately reviewed defect fix.
- Ownership transfer for shared files. Per current execution plan, C remains the shared CLI/Graph integrator unless A explicitly changes that assignment; F coordinates CI integration.

## 3. Stage 2 acceptance criteria

1. Each completed in-scope CLI invocation reserves a distinct run directory before Graph execution, even for same ticker/date and same-second/concurrent starts.
2. Collision handling never overwrites an existing run directory or manifest; allocation retries according to the approved bounded policy and fails visibly if exhausted.
3. The completed invocation has one valid `manifest.json` at its reserved path. Manifest identity, allowlisted config, runtime/Git metadata, and artifact references follow the merged Registry and Phase 1 writer contract.
4. `input_condensation_audit_note` is treated as allowlisted because PR #9 merged at `d36a677...` and that merge is present in the verified current `origin/main` base. No unapproved config keys or secret values are serialized or fingerprinted.
5. A failed manifest write leaves no partial manifest, does not erase the completed analysis result, emits the approved visible warning, and does not report successful manifest persistence.
6. Existing report, state, memory, checkpoint, and public interface behavior remains compatible except for explicitly approved run-directory path changes.
7. Offline tests make no network, live vendor, market-data, or LLM requests. `pytest -q` remains the planned first-layer regression command; any integration-only condition is reported separately.
8. Required Stage 2 tests pass on `ubuntu-latest`, `macos-latest`, and `windows-latest`, with exact CI run, commit, OS, and Python versions recorded.

## 4. Proposed test coverage and traceability

Use the existing official O2-TC IDs where their fit criteria cover integration. Do not silently redefine a Phase 1 unit test as integration evidence. F should confirm whether an additional official case ID is needed for end-to-end CLI integration.

| Existing/proposed ID | Stage 2 integration assertion | Mapping |
|---|---|---|
| O2-TC-04 | Two completed same-ticker/date CLI runs produce distinct run directories and manifests; reserve before Graph; inject UUID collision and prove existing directory/manifest unchanged | O2-FR-01/02/03 |
| O2-TC-05 | Integrated artifact references stay inside results root, are relative where possible, and carry accurate stability labels | O2-FR-10 |
| O2-TC-11 | Same-second/concurrent invocations remain distinct; collision retry is bounded and non-overwriting | O2-FR-02/03 |
| O2-TC-13 | Integrated serialization failure follows approved fail-soft behavior and leaves no partial manifest | O2-FR-01/13/14 |
| O2-TC-14 | Unwritable destination or promotion failure leaves no partial `manifest.json`; warning is visible and result remains available | O2-FR-01/13/14 |
| O2-TC-15 | Invalid/traversal identity or artifact path cannot write outside configured results boundary | O2-FR-03; O2-NFR-05 |
| O2-TC-19 | Integration tests use fakes and do not call external services | O2-NFR-04 |
| O2-TC-20 | `pytest -q` regression confirms agreed existing behavior and interfaces | O2-NFR-06 |
| O2-TC-21 | Path/serialization/integration suite passes on Ubuntu, macOS, Windows | O2-NFR-05 |
| O2-TC-23 | Integrated effective config includes merged allowlisted `input_condensation_audit_note`; unknown keys and secrets are absent | O2-FR-05/11; merged Registry |
| New ID pending F | End-to-end completed CLI invocation through Graph mock verifies one manifest at the reserved run path and approved visible failure behavior | O2-FR-01/03/14; official ID to be assigned if needed |

## 5. Decisions required before approval

- Confirm the exact directory layout and whether existing report/state/log files move under the run-specific directory or remain shared-mutable at legacy paths.
- Confirm run-ID format, atomic reservation primitive, retry bound, and exhausted-collision behavior across Windows/macOS/Linux.
- Confirm the exact lifecycle point for manifest creation and which artifacts are available at that point.
- Confirm CLI warning text and exit behavior for manifest failure, preserving the completed analysis result.
- Confirm C's shared-file integration ownership and F's CI ownership for this stage.
- Confirm whether O2-TC-04/11/13/14/15/19/20/21/23 fully cover Stage 2 or F should add a dedicated integration test ID.
- Confirm supported Python versions and required status checks on each OS.
- Confirm current `main` contains PR #9 merge `d36a677...`; if main has advanced, record the actual base SHA and recheck the allowlist before approval.
- Confirm that synchronizing and verifying the Phase 1 writer/test expectation for `input_condensation_audit_note` is part of Stage 2 and who owns that verification.

## 6. Approval and evidence record

- **Stage 2 test-plan approval:** Pending A/F
- **Approver, time, and evidence:** Not recorded
- **Implementation start:** Not started / not authorized
- **Test execution and CI:** Not run; no result claimed
- **Reapproval:** Any material scope, expected-result, or ownership change requires an updated plan and renewed approval before implementation.
