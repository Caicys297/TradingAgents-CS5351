# O2 Reproducibility Manifest — Test Plan

**Document version:** v0.3-DRAFT  
**Document revision:** 2 (planning updates after the PR #8 audit)  
**Status:** Draft; approval pending  
**Owner:** Member B  
**Plan file:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md`  
**Requirements baseline:** PR #2 has been merged. A-approved O2 Phase 1 implementation baseline: `main` commit `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`.  
**Phase 1 implementation to preserve:** local commit `70a4eeee0397efc5da5012ebec0bacd4635a260f` exists and contains only `tradingagents/repro/manifest.py` and `test/offline/test_o2_manifest.py`. Its base relationship to `aa549f66...` is not verified here.  
**Approved Phase 1 scope:** standalone manifest writer and its offline tests only. `cli/run.py`, `trading_graph.py`, shared integration, and CI changes are deferred.  
**Pending Registry update:** `input_condensation_audit_note` is not part of the approved O2 fingerprint allowlist and is excluded from this plan pending unmerged Draft PR #9.  
**Test reviewer:** Member A  
**Implementation status:** Phase 1 commit `70a4eee` exists locally with the approved two-file scope; no claim is made that it is rebased onto `aa549f66...`.  
**Test status:** Proposed; no test execution evidence is recorded in this plan.  
**Revision note:** Revision 2 updates this draft after the PR #8 audit. Prior drafts remain in Git history; this revision is not approved.

## 1. Purpose

This plan defines proposed offline tests for O2, which adds a provenance manifest for completed CLI analysis runs.

The manifest fingerprint is a hash of normalized run identity and allowlisted effective configuration. It is **not** a hash of actual market or news data. Unless an immutable per-run data snapshot is implemented and approved, the manifest must state that actual input-data provenance is `not_captured`.

The manifest uses the fixed field `schema_version` with the v1 string value `"1.0.0"`.

## 2. Scope

### Approved Phase 1 scope

- Standalone manifest writer `tradingagents/repro/manifest.py` and offline tests `test/offline/test_o2_manifest.py` only.
- Existing implementation commit `70a4eee` is preserved. Do not claim it is based on `aa549f66...` unless Git evidence verifies that relationship.
- Deferred from Phase 1: `cli/run.py`, `trading_graph.py`, shared integration, UUID run-directory reservation, CLI fail-soft behavior, and CI/platform-matrix changes.

### Proposed full O2 scope

The items below describe full O2. Phase 1 implementation remains limited to the approved standalone writer and tests above.

- Completed CLI invocations.
- Unique invocation IDs and manifest paths for repeated runs.
- Reserving a new run directory before graph execution.
- Retrying UUID collisions without replacing an existing run directory or manifest.
- Manifest fields, fixed schema version, deterministic fingerprint, and configuration allowlisting.
- Rejection of `NaN` and positive or negative `Infinity` during canonical JSON serialization.
- Explicit handling of missing Git, model, and runtime metadata.
- Honest artifact-stability labels and disclosure that immutable market/news snapshots are not captured.
- Atomic manifest writing and visible fail-soft behavior when manifest writing fails.
- Offline tests and compatibility checks.

### Out of scope

- Programmatic API runs and failed analysis runs.
- Live vendors, market-data services, LLM calls, or network-dependent tests as part of the offline suite.
- Capturing or hashing actual market/news payloads.
- Changes to shared CLI or graph integration before the relevant architecture and execution plans are approved.

## 3. Proposed test environment

- **Candidate test location:** `test/offline/`, consistent with the candidate registry’s offline-test policy.
- **First-layer regression command:** `pytest -q`. The current configuration collects `tests/` and `test/offline/`, while excluding tests marked `integration`.
- Tests must use controlled fixtures/fakes and must not access the network, live vendors, market data, or LLM services.
- Any live/integration conditions requiring external services must be listed separately. They must not be described as having run as part of `pytest -q`.
- **O2-TC-21 platform matrix:** `ubuntu-latest`, `macos-latest`, and `windows-latest`, as confirmed by A for this plan. CI integration must be coordinated with F.
- The implementation baseline is A-approved `main` commit `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`.
- Existing Phase 1 implementation commit `70a4eee` must be preserved. Its base relationship to `aa549f66...` is not verified here.
- No test execution evidence is recorded in this plan.

## 4. Proposed test cases

| Test ID | Scenario and expected result | Requirement mapping | Status |
|---|---|---|---|
| `O2-TC-01` | A completed CLI invocation produces one parseable manifest with required fields. It contains `schema_version: "1.0.0"`. | `O2-FR-01`, `O2-FR-12`, `O2-NFR-07` | Proposed |
| `O2-TC-02` | Equivalent normalized inputs/configuration with different mapping-key order produce the same fingerprint. Serialization rejects `NaN` and positive/negative `Infinity`; no fingerprint is produced from non-finite values. | `O2-FR-07`, `O2-FR-08`, `O2-NFR-02` | Proposed |
| `O2-TC-03` | Changing an included identity/configuration field changes the fingerprint; changing excluded run ID, time, duration, output, artifact path, secret, or vendor payload does not. | `O2-FR-07`, `O2-FR-08` | Proposed |
| `O2-TC-04` | Two completed invocations for the same ticker/date produce distinct readable manifests. Assert that the new run directory is reserved before graph execution. Simulate a generated UUID matching an existing run directory; allocation retries, and the existing directory and manifest remain unchanged. | `O2-FR-01`, `O2-FR-02`, `O2-FR-03` | Proposed |
| `O2-TC-05` | Artifact references use relative paths where possible, reject traversal outside the configured base when a base is supplied, and use the correct stability labels. Shared-mutable reports/logs are not represented as immutable run-specific artifacts. | `O2-FR-10` | Proposed |
| `O2-TC-06` | A fixture containing secrets and credential-bearing URLs does not serialize those values. | `O2-FR-05`, `O2-FR-11`, `O2-NFR-03` | Proposed |
| `O2-TC-07` | Without an immutable per-run market/news snapshot, provenance is `not_captured`; no data-hash or full-reproducibility claim is made. | `O2-FR-09` | Proposed |
| `O2-TC-08` | When Git metadata is unavailable, the manifest records an explicit unavailable status and manifest creation can continue. | `O2-FR-06` | Proposed |
| `O2-TC-09` | Missing model/provider metadata is represented explicitly; no value is invented. | `O2-FR-05`, `O2-FR-06` | Proposed |
| `O2-TC-10` | Optional empty values, Unicode, and reordered mappings serialize as valid deterministic JSON under the approved normalization rules. `NaN` and positive/negative `Infinity` are rejected because canonical serialization uses `allow_nan=false`. | `O2-FR-07`, `O2-NFR-02`, `O2-NFR-05` | Proposed |
| `O2-TC-11` | Two invocations started within the same second receive distinct IDs and manifest paths. If a generated UUID collides with an existing run directory, the allocator retries and does not overwrite that directory or its manifest. Assert that the new run directory is reserved before graph execution. | `O2-FR-02`, `O2-FR-03` | Proposed |
| `O2-TC-12` | Raw ticker variants that normalize to the same approved identity produce the same identity-dependent fingerprint; raw ticker is not stored separately. | `O2-FR-04`, `O2-FR-07`, `O2-FR-08` | Proposed |
| `O2-TC-13` | A non-serializable value causes the defined manifest-failure outcome: no partial `manifest.json` remains, the CLI shows a visible provenance-failed warning, no successful manifest path or saved-provenance claim is published, and the already completed O4 effective rating remains unchanged. | `O2-FR-01`, `O2-FR-13`, `O2-FR-14` | Proposed |
| `O2-TC-14` | An unwritable manifest destination, or failed promotion of the temporary manifest, produces the same fail-soft outcome: the analysis result/rating remains unchanged, the CLI displays a provenance-failed warning, failed promotion of the temporary manifest leaves no partial `manifest.json`, and no successful manifest path or provenance claim is shown. | `O2-FR-01`, `O2-FR-13`, `O2-FR-14` | Proposed |
| `O2-TC-15` | An invalid or path-traversal ticker is rejected without writing outside the configured results boundary. | `O2-FR-03`, `O2-NFR-05` | Proposed |
| `O2-TC-16` | Nested secrets and credential-bearing URLs are omitted from the manifest. | `O2-FR-11`, `O2-NFR-03` | Proposed |
| `O2-TC-17` | Git metadata lookup failure, including an OS or timeout error, is represented explicitly without fabricated metadata. | `O2-FR-06` | Proposed |
| `O2-TC-18` | Inspect the O2 implementation PR’s dependency-file diff and writer imports. Confirm that O2 adds no third-party runtime dependency. | `O2-NFR-01` | Proposed; reviewed by dependency diff and import inspection, not an offline pytest case |
| `O2-TC-19` | Run the O2 tests with fakes and network access blocked; tests make no live vendor, market-data, or LLM calls. | `O2-NFR-04` | Proposed |
| `O2-TC-20` | Run the first-layer regression command `pytest -q` and confirm compatibility with the collected `tests/` and `test/offline/` suites. List any live/integration conditions separately; do not claim they ran under this command. | `O2-NFR-06` | Proposed |
| `O2-TC-21` | Run path/serialization checks on `ubuntu-latest`, `macos-latest`, and `windows-latest`. | `O2-NFR-05` | Proposed; CI integration to be coordinated with F |
| `O2-TC-22` | Inspect the manifest identity and confirm normalized ticker, asset type, ISO analysis date, and selected Analyst keys are present, with no separate raw-ticker field. | `O2-FR-04` | Proposed |
| `O2-TC-23` | Supply allowlisted and unapproved configuration fields. Use only the currently merged Registry allowlist; `input_condensation_audit_note` is excluded pending unmerged Draft PR #9. Unknown/unapproved fields and secrets are excluded. | `O2-FR-05`, `O2-FR-11`, `O2-NFR-03` | Proposed; PR #9 pending |
| `O2-TC-24` | Available package version, Python version, and platform are recorded; unavailable values are explicit. | `O2-FR-06` | Proposed |
| `O2-TC-25` | Inspect the manifest and verify the exact field `schema_version` has the string value `"1.0.0"`. | `O2-FR-12` | Proposed |

## 5. Existing test references

The earlier read-only source analysis found related tests that may help implementation and regression planning, but they do not currently test an O2 manifest:

- CLI harness: `tests/test_cli_memory_log.py::test_cli_run_uses_the_memory_log_like_propagate`
- Existing configuration redaction: `tests/test_reporting.py::test_run_settings_record_the_run_without_endpoints_or_paths`
- Atomic-write analogue: `tests/test_cache_writes.py::test_a_file_held_open_elsewhere_keeps_its_old_content`
- Path-safety tests: `tests/test_safe_ticker_component.py` and `tests/test_cli_symbol_handling.py::test_the_run_directory_cannot_escape_the_results_directory`
- Existing default report and overwrite behavior: `tests/test_reporting.py`

These references are context only; they do not prove O2 behavior or coverage. Verify them against the implementation checkout before coding.

## 6. Open items before approval

1. Confirm the requirement and test IDs against the merged Registry baseline and the PR #8 review.
2. PR #9 remains a Draft PR. Keep `input_condensation_audit_note` excluded from the approved O2 fingerprint allowlist until PR #9 merges and the Registry is updated.
3. Confirm the actual GitHub path and immutable commit link for this v0.3 test plan in PR #8.
4. Use A-approved `main` commit `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83` as the implementation baseline. Preserve existing Phase 1 commit `70a4eee`; do not claim it is based on `aa549f66...` unless Git evidence verifies that relationship.
5. Coordinate O2-TC-21 CI integration with F for Ubuntu, macOS, and Windows.
6. Keep the first-layer regression scope for O2-TC-20 as `pytest -q`; list live/integration conditions separately and do not describe them as run.
7. Record the test-plan version, requirement IDs, test IDs, approver, approval time, and evidence after an actual review. The blank approval template is not evidence of approval.

## 7. Approval record

- **Plan version:** v0.3-DRAFT (Revision 2)
- **Plan file:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md`
- **Requirements baseline:** PR #2 merged; A-approved O2 Phase 1 implementation baseline `main` commit `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`
- **Phase 1 implementation to preserve:** local commit `70a4eeee0397efc5da5012ebec0bacd4635a260f`; base relationship to `aa549f66...` not verified here
- **Approved Phase 1 scope:** standalone `tradingagents/repro/manifest.py` and `test/offline/test_o2_manifest.py` only; shared CLI/graph/CI integration deferred
- **Pending Registry update:** `input_condensation_audit_note` excluded from the approved O2 fingerprint allowlist pending unmerged Draft PR #9
- **Requirement IDs:** `O2-FR-01`–`O2-FR-14`, `O2-NFR-01`–`O2-NFR-07`
- **Test IDs:** `O2-TC-01`–`O2-TC-25`
- **Test reviewer:** Member A
- **Approval status:** Pending; no approval of this revision is claimed
- **Approval evidence/time:** Not recorded
- **Implementation status:** Phase 1 commit `70a4eee` exists locally with the approved two-file scope
- **Test execution status:** No execution evidence recorded in this plan
