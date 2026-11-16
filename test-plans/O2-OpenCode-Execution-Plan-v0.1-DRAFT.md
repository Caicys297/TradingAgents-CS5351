# O2 Implementation Execution Plan — Draft for Human Review

**Status: Draft — pending A’s test-plan approval and A’s OpenCode execution-plan approval. No implementation, test execution, commit, CI result, or approval is claimed.**

**Local source inspected:** `D:\Downloads\TradingAgents-CS5351-main`  
**Commit verification:** This ZIP-extracted copy has no `.git`; the local commit is **unverifiable**. The implementation base remains A-specified: `main` at `5afb24cf1b48e15e5000ee1365826eebb30d01ae`. That base is **not verified from this ZIP copy**. All source observations below are from the inspected ZIP snapshot and are not verified against A’s specified base commit.

**Test-plan limitation:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` is not present in this local ZIP. The confirmed v0.3 review decisions supplied for this plan are used; no claim is made that the local plan file was inspected. This does not claim the file is absent from GitHub.

## 1. Preconditions and approval gates

No code edit may begin until both gates are recorded:

1. **A approves the versioned O2 test plan.** The registry requires test-plan approval before code generation (`docs/req/requirements.yaml:7-15`), with O2 test-plan review assigned to A (`:10`).
2. **A approves this exact OpenCode execution plan** before the first code edit (`requirements.yaml:15`).

Additional preconditions:

- Confirm the implementation branch and base commit `main` at `5afb24cf1b48e15e5000ee1365826eebb30d01ae`.
- Confirm C remains the sole integrator for shared `cli/run.py` and `trading_graph.py` changes (`requirements.yaml:16`).
- Confirm O2 scope remains completed CLI runs only; failed/programmatic runs remain out of scope (`requirements.yaml:24`).
- Confirm the v0.3 test plan includes:
  - UUID collision retries without overwriting an existing run directory or manifest, and the new run directory is reserved before graph execution.
  - `allow_nan=false`; NaN and positive/negative Infinity are rejected.
  - Manifest write/serialization failure leaves no partial manifest, shows a provenance-failed warning, publishes no success path, and preserves the completed O4 effective rating.
  - Manifest `schema_version: "1.0.0"`.
  - O2-TC-18 uses the implementation PR’s dependency-file diff and writer-import inspection.
  - O2-TC-20 first-layer regression is `pytest -q`; live/integration conditions are listed separately.
  - O2-TC-21 covers Ubuntu, macOS, and Windows through F’s CI integration.
  - O2-TC-23 includes `input_condensation_audit_note` only as a proposed allowlisted field from unmerged Draft PR #9; it is not part of the merged baseline.
- Record approval in the project’s pre-code approval record. No completed O2 approval is present in this local copy.

## 2. Implementation branch and base commit

- Proposed branch: `feat/o2-reproducibility-manifest` (name pending team convention).
- Base: `main` at `5afb24cf1b48e15e5000ee1365826eebb30d01ae`, supplied by A.
- The ZIP copy cannot verify this commit, branch state, or repository history.

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

### C-owned shared integration

C owns shared integration unless the team explicitly approves otherwise:

- `cli/run.py`: unique run-directory reservation, manifest invocation, fail-soft CLI reporting, artifact path collection.
- `tradingagents/graph/trading_graph.py`: access to effective settings/run context and any report/state/checkpoint/public-interface integration.
- Shared CLI success/failure flow and path layout.

B may provide helper design and tests but must not edit C-owned shared files without explicit approval.

## 4. Ordered implementation steps

1. **Freeze approved schema and defaults.** Confirm `schema_version: "1.0.0"`, normalized identity fields, merged allowlist, and the proposed-but-unmerged `input_condensation_audit_note` distinction.
2. **Create isolated B-owned manifest writer.** Build pure construction, normalization, allowlist, artifact-label, and fingerprint helpers.
3. **Implement canonical fingerprint.** SHA-256 over UTF-8 canonical JSON with sorted keys, comma/colon separators, `ensure_ascii=false`, `allow_nan=false`, ISO analysis date, and fixed Analyst order; exclude run ID, time, duration, output, artifact paths, secrets, and vendor payloads (`requirements.yaml:28`).
4. **Implement B-owned atomic writing.** Write to a temporary file in the reserved run directory and promote to `manifest.json`; serialization/write failure must leave no partial manifest.
5. **Coordinate unique run-directory reservation with C.** Candidate path is `<results_dir>/<safe_ticker>/<analysis_date>/runs/<uuid4>/`, reserved before graph execution. On UUID collision, retry without overwriting the existing directory or manifest (`requirements.yaml:25-26`).
6. **Build manifest through C invocation.** Include normalized ticker, asset type, ISO date, analysts, allowlisted settings, package/Python/platform availability, Git availability, and `actual_input_data_provenance: not_captured`.
7. **Represent missing metadata explicitly.** Missing Git/model/runtime values carry explicit unavailable status; no fabricated values.
8. **Assign artifact stability labels.** Use `run_unique`, `shared_mutable`, or `not_persisted`; ticker/date reports/logs remain shared-mutable unless immutability is proven (`requirements.yaml:31`).
9. **Implement fail-soft CLI reporting through C.** On write/serialization failure, preserve the completed O4 effective rating, show a visible provenance-failed warning, publish no success path, and make no provenance claim (`requirements.yaml:27`).
10. **Add B-owned offline tests** under `test/offline/`.
11. **Coordinate C/F integration checks.** O2-TC-18 dependency diff/import check, O2-TC-20 regression scope, and O2-TC-21 three-platform CI matrix.

## 5. File-by-file plan

| File / path | Purpose | Owner | Rationale |
|---|---|---|---|
| `tradingagents/repro/manifest.py` (candidate) | Isolated manifest construction, allowlist, fingerprint, metadata, artifact labels, canonical JSON, atomic temp-file write and promotion | **B** | Design proposal. No manifest implementation was found in the inspected ZIP snapshot. Registry assigns isolated modules/tests to B (`requirements.yaml:16`). |
| `test/offline/test_o2_manifest.py` (candidate) | O2 offline unit/behavior tests, including UUID collision simulation and NaN/Infinity rejection | **B** | In the inspected ZIP snapshot, `test/offline/` is collected by pytest (`pyproject.toml:59`); it currently contains only `.gitkeep` and `conftest.py`. |
| `cli/run.py` | Reserve unique run directory before graph execution, invoke manifest writer, surface provenance-failed warning, collect artifact references | **C** | Shared CLI integration. In the inspected ZIP snapshot, the run directory is `<results_dir>/<safe_ticker>/<date>` (`cli/run.py:36-42`, `:135-136`); message log appends (`:150-151`, `:162-163`); section reports use fixed names (`:175-178`); graph streams at `:241`; decision recorded at `:353`; cleanup at `:357-359`; report offer at `:388-389`; report-save failure at `:453-454`. |
| `tradingagents/graph/trading_graph.py` | Provide effective settings/run context without changing report/state/checkpoint contracts | **C** | Shared graph integration. In the inspected ZIP snapshot: `run_settings()` `:255-275`; report path `:288-291`; state log `:438-476`; run signature `:140-165`. |
| `tradingagents/dataflows/files.py` | Reuse or assess atomic temp-file/promotion pattern | **C for edits; B may call** | In the inspected ZIP snapshot, `replace_file()` uses temp + `os.replace` (`:14-33`); its cache-oriented `PermissionError` behavior (`:28-32`) must be reviewed against O2’s fail-soft provenance rules. |
| `tradingagents/dataflows/symbols.py` | Reuse path-safe ticker validation | **No edit; B/C reuse** | In the inspected ZIP snapshot, `safe_ticker_component()` validates traversal and unsafe values (`:155-180`). |
| `pyproject.toml` | Test discovery and markers | **C/F if changed** | In the inspected ZIP snapshot, `testpaths` includes `tests` and `test/offline` (`:59`); integration excluded by default (`:60`); markers at `:61-64`. |
| `.github/workflows/ci.yml` | Three-platform CI and O2-TC-18 dependency gate | **C/F** | In the inspected ZIP snapshot, CI runs `pytest -q` (`:36`) on `ubuntu-latest` only (`:15`, `:40`, `:56`); O2-TC-21 needs F’s CI coordination. |
| `test/offline/conftest.py` | Offline no-network fixture | **No edit expected** | In the inspected ZIP snapshot, this blocks network/curl access unless integration-marked (`:14-30`). |
| `test-plans/O2-Test-Plan-v0.3-DRAFT.md` | Draft test-plan baseline for review; pending A’s approval. | **Review source; not B-owned edit** | Absent from this local ZIP. This row does not approve the v0.3 plan. No local inspection or GitHub-presence claim. |

## 6. Mapping to O2-TC-01 through O2-TC-25

All mappings are proposed. Candidate default command is `pytest -q`; it has **not** been run for O2.

| Test | Coverage | Owner / integration need |
|---|---|---|
| `O2-TC-01` | Valid completed invocation produces parseable manifest with required fields and `schema_version: "1.0.0"` | B; offline test |
| `O2-TC-02` | Reordered mapping keys produce identical fingerprint; NaN and positive/negative Infinity are rejected under `allow_nan=false` | B; isolated unit test |
| `O2-TC-03` | Changing included fields changes fingerprint; excluded fields do not | B; isolated unit test |
| `O2-TC-04` | Two same-ticker/date invocations retain two readable manifests; simulate UUID collision, verify retry, preserve pre-existing directory/manifest, and assert the new run directory is reserved before graph execution | **C integration** for reservation/retry; B assertions |
| `O2-TC-05` | Report/state/message references have correct stability labels | B helper; **C** supplies actual artifact paths |
| `O2-TC-06` | Fake secrets/credential URL absent from manifest | B; isolated test |
| `O2-TC-07` | No immutable snapshot → `not_captured`; no data hash | B; isolated test |
| `O2-TC-08` | Git unavailable → explicit status; manifest creation continues | B helper; **C** CLI status test |
| `O2-TC-09` | Missing model/provider → explicit missing status; no invented value | B; isolated test |
| `O2-TC-10` | Empty optional fields, Unicode, reordered mappings → valid deterministic JSON/fingerprint; NaN and positive/negative Infinity are rejected under `allow_nan=false` | B; isolated test |
| `O2-TC-11` | Two invocations in same second get distinct IDs/paths; simulate UUID collision, verify retry, preserve pre-existing directory/manifest, and assert new run directory is reserved before graph execution | **C integration**; B assertions |
| `O2-TC-12` | Raw ticker variants normalize identically; fingerprint stable when raw ticker excluded | B; isolated test |
| `O2-TC-13` | Non-serializable value → no partial manifest, visible provenance-failed warning, no success path/provenance claim, and unchanged completed O4 effective rating | B + **C** for CLI fail-soft path |
| `O2-TC-14` | Unwritable destination → no partial manifest, visible provenance-failed warning, no success path/provenance claim, and unchanged completed O4 effective rating | **C integration** + B writer test |
| `O2-TC-15` | Invalid/path-traversal ticker rejected; no write outside results boundary | B helper + **C** run-directory test |
| `O2-TC-16` | Nested secret or credential URL excluded/redacted | B; isolated test |
| `O2-TC-17` | Git lookup OS/timeout failure → explicit unavailable/error status | B; isolated test |
| `O2-TC-18` | Dependency-file diff plus writer-import inspection show no new third-party runtime dependency | **F/C CI or Static Analysis Gate**, not automatically an offline pytest case |
| `O2-TC-19` | Manifest tests use fakes; no network/vendor/market-data/LLM access | B; offline fixture |
| `O2-TC-20` | First layer: `pytest -q` regression; live/integration conditions separately listed | **C/F** define regression scope; B may supply tests |
| `O2-TC-21` | Path/JSON checks on Ubuntu, macOS, and Windows | **F/C** CI matrix; B supplies platform-agnostic tests |
| `O2-TC-22` | Manifest contains normalized ticker, asset type, ISO date, selected analysts | B; isolated test |
| `O2-TC-23` | Only allowlisted fields serialized; unapproved keys absent; includes `input_condensation_audit_note` only as proposed in unmerged Draft PR #9, not merged baseline | B; isolated test |
| `O2-TC-24` | Package version, Python version, platform recorded when available | B; isolated test |
| `O2-TC-25` | Manifest contains agreed schema-version field and value `"1.0.0"` | B; isolated test |

## 7. Candidate offline test path and planned commands

- Candidate test file: `test/offline/test_o2_manifest.py`.
- Planned default command: `pytest -q`.
- Planned targeted command: `pytest -q test/offline/test_o2_manifest.py`.

These are planned commands only. No O2 test has been run in this review. Integration/live conditions remain separate and are not part of the offline default command.

## 8. Stop conditions and draft status

Stop and request human/team approval before any edit if:

- O2 scope changes beyond completed CLI runs.
- B is asked to edit `cli/run.py` or `trading_graph.py` without an explicit ownership change.
- Shared interfaces, report/state/memory/checkpoint behavior, or public signatures must change.
- A new runtime dependency is proposed.
- UUID reservation/collision policy changes.
- `schema_version`, fingerprint fields, `allow_nan=false`, or allowlist content changes.
- `input_condensation_audit_note` moves from Draft PR #9 scope into the merged baseline without approval.
- Fail-soft write-failure behavior changes.
- O2-TC-18 command or O2-TC-20 regression scope is undefined.
- O2-TC-21 platform scope changes or F does not support the CI matrix.
- The approved test plan or execution plan differs materially from this plan.

**Draft — pending human review and approval.** No approval, implementation, test execution, test result, commit, push, PR, or GitHub action is claimed. No files were created, edited, or deleted.
