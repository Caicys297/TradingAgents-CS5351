# O2 Reproducibility Manifest — Test Plan

**Document version:** v0.2-DRAFT  
**Status:** Draft; approval pending  
**Owner:** Member B  
**Requirements baseline:** Candidate `docs/req/requirements.yaml`, registry version `1.0.0-a-baseline`, currently under PR #2 review  
**Requirements commit:** Pending; the supplied ZIP has no Git metadata, so its commit cannot be verified  
**Test reviewer:** Member A  
**Implementation status:** Not started  
**Test status:** Proposed; no tests are claimed implemented or executed  
**Revision note:** This draft revises v0.1-DRAFT for review. Neither version is approved.

## 1. Purpose

This plan defines proposed offline tests for O2, which adds a provenance manifest for completed CLI analysis runs. It uses the O2 requirement and test IDs in the candidate requirements registry.

The manifest fingerprint is a hash of normalized run identity and allowlisted effective configuration. It is **not** a hash of actual market or news data. Unless an immutable per-run data snapshot is added and approved, the manifest must state that actual input-data provenance is `not_captured`.

## 2. Scope

### In scope

- Completed CLI invocations.
- Unique invocation IDs and manifest paths for repeated runs.
- Manifest fields, schema version, deterministic fingerprint, and configuration allowlisting.
- Explicit handling of missing Git, model, and runtime metadata.
- Honest artifact-stability labels and absent immutable market/news snapshots.
- Atomic manifest writing and visible fail-soft behavior when manifest writing fails.
- Offline tests and compatibility checks.

### Out of scope

- Programmatic API runs and failed analysis runs.
- Live vendors, market-data services, LLM calls, or network-dependent tests.
- Capturing or hashing actual market/news payloads.
- Changes to shared CLI or graph integration before the relevant architecture and execution plans are approved.

## 3. Proposed test environment

- **Candidate test location:** `test/offline/`, consistent with the candidate registry’s offline-test policy.
- **Candidate default test command:** `pytest -q`. The read-only source analysis reports this as the current CI command and confirms that `test/offline/` is included in pytest discovery.
- Tests must use controlled fixtures/fakes and must not access the network, live vendors, market data, or LLM services.
- No test command has been run for this plan.
- The candidate registry lists Ubuntu, macOS, and Windows. The inspected CI snapshot runs Ubuntu only; the final platform matrix and CI placement for `O2-TC-21` require confirmation before approval.
- The source analysis was performed on a ZIP-extracted copy without `.git`; the source snapshot’s exact commit is unverified.

## 4. Proposed test cases

| Test ID | Scenario and expected result | Requirement mapping | Status |
|---|---|---|---|
| `O2-TC-01` | A completed CLI invocation produces one parseable manifest with required fields and the agreed schema-version field. | `O2-FR-01`, `O2-FR-12`, `O2-NFR-07` | Proposed |
| `O2-TC-02` | Equivalent normalized inputs/configuration with different mapping-key order produce the same fingerprint. | `O2-FR-07`, `O2-FR-08`, `O2-NFR-02` | Proposed |
| `O2-TC-03` | Changing an included identity/configuration field changes the fingerprint; changing excluded run ID, time, output, artifact path, or payload does not. | `O2-FR-07`, `O2-FR-08` | Proposed |
| `O2-TC-04` | Two completed invocations for the same ticker/date produce distinct readable manifests; the first remains intact. | `O2-FR-01`, `O2-FR-02`, `O2-FR-03` | Proposed |
| `O2-TC-05` | Artifact references use the correct stability labels; shared-mutable reports/logs are not represented as immutable run-specific artifacts. | `O2-FR-10` | Proposed |
| `O2-TC-06` | A fixture containing secrets and credential-bearing URLs does not serialize those values. | `O2-FR-05`, `O2-FR-11`, `O2-NFR-03` | Proposed |
| `O2-TC-07` | Without an immutable per-run market/news snapshot, provenance is `not_captured`; no data-hash or full-reproducibility claim is made. | `O2-FR-09` | Proposed |
| `O2-TC-08` | When Git metadata is unavailable, the manifest records an explicit unavailable status and creation can continue. | `O2-FR-06` | Proposed |
| `O2-TC-09` | Missing model/provider metadata is represented explicitly; no value is invented. | `O2-FR-05`, `O2-FR-06` | Proposed |
| `O2-TC-10` | Optional empty values, Unicode, and reordered mappings serialize as valid, deterministic JSON under the approved normalization rules. | `O2-FR-07`, `O2-NFR-02`, `O2-NFR-05` | Proposed |
| `O2-TC-11` | Two invocations started within the same second receive distinct IDs and manifest paths. | `O2-FR-02`, `O2-FR-03` | Proposed |
| `O2-TC-12` | Raw ticker variants that normalize to the same approved identity produce the same identity-dependent fingerprint; raw ticker is not stored separately. | `O2-FR-04`, `O2-FR-07`, `O2-FR-08` | Proposed |
| `O2-TC-13` | A non-serializable value follows the approved error policy and leaves no partial `manifest.json`. | `O2-FR-01`, `O2-FR-13`, `O2-FR-14` | Proposed |
| `O2-TC-14` | An unwritable manifest destination leaves the analysis result/rating unchanged, displays a provenance-failed warning, creates no partial manifest, and publishes no manifest path. | `O2-FR-01`, `O2-FR-13`, `O2-FR-14` | Proposed |
| `O2-TC-15` | An invalid or path-traversal ticker is rejected without writing outside the configured results boundary. | `O2-FR-03`, `O2-NFR-05` | Proposed |
| `O2-TC-16` | Nested secrets and credential-bearing URLs are omitted from the manifest. | `O2-FR-11`, `O2-NFR-03` | Proposed |
| `O2-TC-17` | Git metadata lookup failure, including an OS or timeout error, is represented explicitly without fabricated metadata. | `O2-FR-06` | Proposed |
| `O2-TC-18` | Review the dependency change to verify that O2 adds no third-party runtime dependency. | `O2-NFR-01` | Proposed; exact gate command pending |
| `O2-TC-19` | Run the O2 tests with fakes and network access blocked; tests make no live vendor, market-data, or LLM calls. | `O2-NFR-04` | Proposed |
| `O2-TC-20` | Run the agreed regression suite and confirm existing reports, state, memory log, checkpoint behavior, and public interfaces remain compatible. | `O2-NFR-06` | Proposed; exact regression scope to be confirmed |
| `O2-TC-21` | Run path/serialization tests on every team-approved CI platform. | `O2-NFR-05` | Proposed; platform matrix and CI placement pending |
| `O2-TC-22` | Inspect the manifest identity and confirm normalized ticker, asset type, ISO analysis date, and selected Analyst keys are present, with no separate raw-ticker field. | `O2-FR-04` | Proposed |
| `O2-TC-23` | Supply allowlisted and unapproved configuration fields; only approved non-secret fields are serialized. | `O2-FR-05`, `O2-FR-11`, `O2-NFR-03` | Proposed |
| `O2-TC-24` | Available package version, Python version, and platform are recorded; unavailable values are explicit. | `O2-FR-06` | Proposed |
| `O2-TC-25` | Inspect the manifest and verify the approved schema-version field and value. | `O2-FR-12` | Proposed |

## 5. Existing test references

The read-only source analysis found related tests that may help implementation and regression planning, but they do not currently test an O2 manifest:

- CLI harness: `tests/test_cli_memory_log.py::test_cli_run_uses_the_memory_log_like_propagate`
- Existing configuration redaction: `tests/test_reporting.py::test_run_settings_record_the_run_without_endpoints_or_paths`
- Atomic-write analogue: `tests/test_cache_writes.py::test_a_file_held_open_elsewhere_keeps_its_old_content`
- Path-safety tests: `tests/test_safe_ticker_component.py` and `tests/test_cli_symbol_handling.py::test_the_run_directory_cannot_escape_the_results_directory`
- Existing default report and overwrite behavior: `tests/test_reporting.py`

These references come from the inspected ZIP snapshot. They are context only; they do not prove O2 behavior or coverage and must be checked against the implementation checkout before coding.

## 6. Open items before approval

1. Confirm that this plan’s requirement and test IDs match the exact unified registry version reviewed in PR #2.
2. **Requirement-to-test traceability:** the candidate registry maps `O2-FR-14` to `O2-TC-08`, `O2-TC-09`, `O2-TC-17`, and `O2-TC-24` in addition to `O2-TC-13` and `O2-TC-14`. The latter two directly test manifest-write failures; the former cases appear to test metadata availability. Ask A to confirm the mapping against the approved test plan. Do not change the registry mapping without review.
3. Confirm the supported platform matrix and where `O2-TC-21` will run; the inspected CI snapshot shows Ubuntu only.
4. Define the exact regression scope for `O2-TC-20`.
5. Define the dependency/static-analysis command for `O2-TC-18`.
6. Confirm the immutable GitHub reference/commit for the requirements baseline before approval.
7. Record the test-plan version, requirement IDs, test IDs, approver, approval time, and evidence after an actual review. The template alone is not an approval.

## 7. Approval record

- **Plan version:** v0.2-DRAFT
- **Plan file:** `docs/test-plans/O2-Test-Plan-v0.2-DRAFT.md`
- **Requirements baseline:** Candidate registry `1.0.0-a-baseline` under PR #2 review; exact commit/reference pending
- **Requirement IDs:** `O2-FR-01`–`O2-FR-14`, `O2-NFR-01`–`O2-NFR-07`
- **Test IDs:** `O2-TC-01`–`O2-TC-25`
- **Test reviewer:** Member A
- **Approval status:** Pending; no approval is claimed
- **Approval evidence/time:** Not recorded
- **Implementation status:** Not started
- **Test execution status:** Not run
