# O2 Implementation Execution Plan — Draft for Human Review

**Document version:** v0.1-DRAFT (Revision 2)  
**Status: Draft — revised for A-approved O2 Phase 1 baseline `aa549f66...`; pending review. Phase 1 implementation commit `70a4eee` exists locally and contains the two approved files; its relationship to `aa549f66...` is not verified. No test result or approval of this document revision is claimed.**

**Implementation source:** No local source path is asserted here unless separately verified. Existing Phase 1 implementation commit `70a4eeee0397efc5da5012ebec0bacd4635a260f` exists locally and contains only `tradingagents/repro/manifest.py` and `test/offline/test_o2_manifest.py`. Its base relationship to `aa549f66...` is not verified.

**Implementation baseline:** A-approved `main` commit `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`.

**Test-plan basis:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` in this documentation branch; still draft and pending review.

## 1. Preconditions and approval gates

No code edit may begin until both gates are recorded:

1. **A approves the versioned O2 test plan.** The registry requires test-plan approval before code generation (`docs/req/requirements.yaml:7-15`), with O2 test-plan review assigned to A (`:10`).
2. **A approves this exact OpenCode execution plan** before the first code edit (`requirements.yaml:15`).

Additional preconditions:

- Confirm the implementation baseline is A-approved `main` commit `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`.
- Preserve existing Phase 1 implementation commit `70a4eee`. Do not claim it is based on `aa549f66...` unless Git evidence verifies that relationship.
- Confirm Phase 1 scope is the standalone manifest writer and its offline tests only. Defer `cli/run.py`, `trading_graph.py`, shared integration, and CI changes.
- Confirm C remains the sole integrator for shared `cli/run.py` and `trading_graph.py` changes when those deferred items are approved (`requirements.yaml:16`).
- Confirm full O2 scope remains completed CLI runs only; failed/programmatic runs remain out of scope (`requirements.yaml:24`).
- Confirm the v0.3 test plan includes:
  - UUID collision retries without overwriting an existing run directory or manifest, and the new run directory is reserved before graph execution.
  - `allow_nan=false`; NaN and positive/negative Infinity are rejected.
  - Manifest write/serialization failure leaves no partial manifest, shows a provenance-failed warning, publishes no success path, and preserves the completed O4 effective rating.
  - Manifest `schema_version: "1.0.0"`.
  - O2-TC-18 uses the implementation PR’s dependency-file diff and writer-import inspection.
  - O2-TC-20 first-layer regression is `pytest -q`; live/integration conditions are listed separately.
  - O2-TC-21 covers Ubuntu, macOS, and Windows through F’s CI integration.
  - O2-TC-23 uses only the merged Registry allowlist and excludes `input_condensation_audit_note` pending unmerged Draft PR #9.
- Record approval in the project’s pre-code approval record. No completed approval evidence for this revision is recorded in this local document.

## 2. Implementation branch and base commit

- Implementation branch: `feat/o2-reproducibility-manifest`.
- Base: A-approved `main` at `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`.
- Existing Phase 1 implementation commit `70a4eeee0397efc5da5012ebec0bacd4635a260f` is preserved. Its base relationship to `aa549f66...` is not verified here.
- The active checkout path and commit relationship must be verified separately; no unverified local path is asserted.

## 3. Architecture and ownership boundary

### B-owned isolated work

B owns the isolated manifest writer/module, including:

- Manifest construction and normalized identity fields.
- Effective-configuration allowlist extraction.
- Canonical JSON generation and SHA-256 fingerprint helper.
- Explicit missing Git/model/runtime metadata representation.
- Artifact stability labels.
- **Atomic temporary-file writing and promotion to `manifest.json`.**
- O2 offline tests.

### C-owned shared integration — deferred from Phase 1

C owns shared integration unless the team explicitly approves otherwise. These items are not part of Phase 1 and are deferred until separately approved:

- `cli/run.py`: unique run-directory reservation, manifest invocation, fail-soft CLI reporting, artifact path collection.
- `tradingagents/graph/trading_graph.py`: access to effective settings/run context and any report/state/checkpoint/public-interface integration.
- Shared CLI success/failure flow and path layout.

B may provide helper design and tests but must not edit C-owned shared files without explicit approval.

## 4. Ordered implementation steps

1. **Freeze approved Phase 1 schema and defaults.** Confirm `schema_version: "1.0.0"`, normalized identity fields, and the merged allowlist. Keep `input_condensation_audit_note` excluded pending unmerged Draft PR #9.
2. **Create isolated B-owned manifest writer.** Build pure construction, normalization, allowlist, artifact-label, and fingerprint helpers.
3. **Implement canonical fingerprint.** SHA-256 over UTF-8 canonical JSON with sorted keys, comma/colon separators, `ensure_ascii=false`, `allow_nan=false`, ISO analysis date, and fixed Analyst order; exclude run ID, time, duration, output, artifact paths, secrets, and vendor payloads (`requirements.yaml:28`).
4. **Implement B-owned atomic writing.** Write to a temporary file in the reserved run directory and promote to `manifest.json`; serialization/write failure must leave no partial manifest.
5. **Deferred from Phase 1 — coordinate unique run-directory reservation with C.** Candidate path is `<results_dir>/<safe_ticker>/<analysis_date>/runs/<uuid4>/`, reserved before graph execution. On UUID collision, retry without overwriting the existing directory or manifest (`requirements.yaml:25-26`).
6. **Deferred from Phase 1 — build manifest through C invocation.** Include normalized ticker, asset type, ISO date, analysts, allowlisted settings, package/Python/platform availability, Git availability, and `actual_input_data_provenance: not_captured`.
7. **Represent missing metadata explicitly.** Missing Git/model/runtime values carry explicit unavailable status; no fabricated values.
8. **Assign artifact stability labels.** Use `run_unique`, `shared_mutable`, or `not_persisted`; ticker/date reports/logs remain shared-mutable unless immutability is proven (`requirements.yaml:31`).
9. **Deferred from Phase 1 — implement fail-soft CLI reporting through C.** On write/serialization failure, preserve the completed O4 effective rating, show a visible provenance-failed warning, publish no success path, and make no provenance claim (`requirements.yaml:27`).
10. **Add B-owned offline tests** under `test/offline/`.
11. **Deferred from Phase 1 — coordinate C/F integration checks.** O2-TC-18 dependency diff/import check, O2-TC-20 regression scope, and O2-TC-21 three-platform CI matrix.

## 5. File-by-file plan

| File / path | Purpose | Owner | Rationale |
|---|---|---|---|
| `tradingagents/repro/manifest.py` | Phase 1 isolated manifest construction, allowlist, fingerprint, metadata, artifact labels, canonical JSON, atomic temp-file write and promotion | **B** | Approved Phase 1 implementation exists in local commit `70a4eee`; preserve it. Do not claim it is based on `aa549f66...` without Git evidence. |
| `test/offline/test_o2_manifest.py` | Phase 1 offline unit/behavior tests | **B** | Approved Phase 1 test file exists in local commit `70a4eee`; preserve it. |
| `cli/run.py` | Reserve unique run directory before graph execution, invoke manifest writer, surface provenance-failed warning, collect artifact references | **C** | **Deferred from Phase 1.** Shared CLI integration. In the inspected ZIP snapshot, the run directory is `<results_dir>/<safe_ticker>/<date>` (`cli/run.py:36-42`, `:135-136`); message log appends (`:150-151`, `:162-163`); section reports use fixed names (`:175-178`); graph streams at `:241`; decision recorded at `:353`; cleanup at `:357-359`; report offer at `:388-389`; report-save failure at `:453-454`. |
| `tradingagents/graph/trading_graph.py` | Provide effective settings/run context without changing report/state/checkpoint contracts | **C** | **Deferred from Phase 1.** Shared graph integration. In the inspected ZIP snapshot: `run_settings()` `:255-275`; report path `:288-291`; state log `:438-476`; run signature `:140-165`. |
| `tradingagents/dataflows/files.py` | Reuse or assess atomic temp-file/promotion pattern | **C for edits; B may call** | **Deferred from Phase 1 for shared edits.** In the inspected ZIP snapshot, `replace_file()` uses temp + `os.replace` (`:14-33`); its cache-oriented `PermissionError` behavior (`:28-32`) must be reviewed against O2’s fail-soft provenance rules. |
| `tradingagents/dataflows/symbols.py` | Reuse path-safe ticker validation | **No edit; B/C reuse** | In the inspected ZIP snapshot, `safe_ticker_component()` validates traversal and unsafe values (`:155-180`). |
| `pyproject.toml` | Test discovery and markers | **C/F if changed** | **Deferred from Phase 1.** In the inspected ZIP snapshot, `testpaths` includes `tests` and `test/offline` (`:59`); integration excluded by default (`:60`); markers at `:61-64`. |
| `.github/workflows/ci.yml` | Three-platform CI and O2-TC-18 dependency gate | **C/F** | **Deferred from Phase 1.** In the inspected ZIP snapshot, CI runs `pytest -q` (`:36`) on `ubuntu-latest` only (`:15`, `:40`, `:56`); O2-TC-21 needs F’s CI coordination. |
| `test/offline/conftest.py` | Offline no-network fixture | **No edit expected** | In the inspected ZIP snapshot, this blocks network/curl access unless integration-marked (`:14-30`). |
| `test-plans/O2-Test-Plan-v0.3-DRAFT.md` | Draft test-plan baseline for review; pending approval. | **Review source; not B-owned edit** | Present in this documentation branch. This row does not approve the v0.3 plan. |

## 6. Mapping to O2-TC-01 through O2-TC-25

All mappings are proposed. Candidate default command is `pytest -q`; it has **not** been run for O2.

| Test | Coverage | Owner / integration need |
|---|---|---|
| `O2-TC-01` | Valid completed invocation produces parseable manifest with required fields and `schema_version: "1.0.0"` | B; offline test |
| `O2-TC-02` | Reordered mapping keys produce identical fingerprint; NaN and positive/negative Infinity are rejected under `allow_nan=false` | B; isolated unit test |
| `O2-TC-03` | Changing included fields changes fingerprint; excluded fields do not | B; isolated unit test |
| `O2-TC-04` | Two same-ticker/date invocations retain two readable manifests; simulate UUID collision, verify retry, preserve pre-existing directory/manifest, and assert the new run directory is reserved before graph execution | **Deferred from Phase 1; C integration** for reservation/retry |
| `O2-TC-05` | Report/state/message references use relative paths where possible and correct stability labels; traversal outside a supplied base is rejected | B helper in Phase 1; **C** supplies actual artifact paths later (deferred) |
| `O2-TC-06` | Fake secrets/credential URL absent from manifest | B; isolated test |
| `O2-TC-07` | No immutable snapshot → `not_captured`; no data hash | B; isolated test |
| `O2-TC-08` | Git unavailable → explicit status; manifest creation continues | B helper in Phase 1; **C** CLI status test deferred |
| `O2-TC-09` | Missing model/provider → explicit missing status; no invented value | B; isolated test |
| `O2-TC-10` | Empty optional fields, Unicode, reordered mappings → valid deterministic JSON/fingerprint; NaN and positive/negative Infinity are rejected under `allow_nan=false` | B; isolated test |
| `O2-TC-11` | Two invocations in same second get distinct IDs/paths; simulate UUID collision, verify retry, preserve pre-existing directory/manifest, and assert new run directory is reserved before graph execution | **Deferred from Phase 1; C integration** |
| `O2-TC-12` | Raw ticker variants normalize identically; fingerprint stable when raw ticker excluded | B; isolated test |
| `O2-TC-13` | Non-serializable value → Phase 1 writer-level failure leaves no partial manifest; CLI provenance-failed warning, no success path/provenance claim, and unchanged completed O4 effective rating are deferred with C integration | B Phase 1 writer test; **C** CLI path deferred |
| `O2-TC-14` | Unwritable destination or failed temporary-manifest promotion → Phase 1 writer-level failure leaves no partial `manifest.json`; CLI provenance-failed warning, no success path/provenance claim, and unchanged completed O4 effective rating are deferred with C integration | B Phase 1 writer test; **C** CLI path deferred |
| `O2-TC-15` | Invalid/path-traversal ticker rejected; no write outside results boundary | B helper in Phase 1; **C** run-directory test deferred |
| `O2-TC-16` | Nested secret or credential URL excluded/redacted | B; isolated test |
| `O2-TC-17` | Git lookup OS/timeout failure → explicit unavailable/error status | B; isolated test |
| `O2-TC-18` | Dependency-file diff plus writer-import inspection show no new third-party runtime dependency | **Deferred from Phase 1; F/C CI or Static Analysis Gate**, not automatically an offline pytest case |
| `O2-TC-19` | Manifest tests use fakes; no network/vendor/market-data/LLM access | B; offline fixture |
| `O2-TC-20` | First layer: `pytest -q` regression; live/integration conditions separately listed | **Deferred from Phase 1; C/F** define regression scope |
| `O2-TC-21` | Path/JSON checks on Ubuntu, macOS, and Windows | **Deferred from Phase 1; F/C** CI matrix |
| `O2-TC-22` | Manifest contains normalized ticker, asset type, ISO date, selected analysts | B; isolated test |
| `O2-TC-23` | Only merged allowlisted fields serialized; unapproved keys absent; `input_condensation_audit_note` is excluded pending unmerged Draft PR #9 | B; isolated test |
| `O2-TC-24` | Package version, Python version, platform recorded when available | B; isolated test |
| `O2-TC-25` | Manifest contains agreed schema-version field and value `"1.0.0"` | B; isolated test |

## 7. Candidate offline test path and planned commands

- Phase 1 test file: `test/offline/test_o2_manifest.py`, present in local commit `70a4eee`.
- Planned default command: `pytest -q`.
- Planned targeted command: `pytest -q test/offline/test_o2_manifest.py`.

These are planned commands only. No test execution evidence is recorded in this plan. Integration/live conditions remain separate and are not part of the offline default command.

## 8. Stop conditions and draft status

Stop and request human/team approval before any edit if:

- O2 scope changes beyond the approved Phase 1 standalone writer and offline tests without approval.
- O2 scope changes beyond completed CLI runs.
- B is asked to edit `cli/run.py` or `trading_graph.py` without an explicit ownership change.
- Shared interfaces, report/state/memory/checkpoint behavior, or public signatures must change.
- A new runtime dependency is proposed.
- The implementation baseline changes from A-approved `aa549f66...`.
- Existing implementation commit `70a4eee` would be reset, rebased, amended, or discarded without explicit approval.
- UUID reservation/collision policy changes.
- `schema_version`, fingerprint fields, `allow_nan=false`, or allowlist content changes.
- `input_condensation_audit_note` is treated as part of the approved allowlist before PR #9 merges and the Registry is updated.
- Fail-soft write-failure behavior changes.
- O2-TC-18 command or O2-TC-20 regression scope is undefined.
- O2-TC-21 platform scope changes or F does not support the CI matrix.
- The approved test plan or execution plan differs materially from this plan.

**Draft — pending human review and approval.** No approval, implementation, test execution, test result, commit, push, PR, or GitHub action is claimed for this revision.
