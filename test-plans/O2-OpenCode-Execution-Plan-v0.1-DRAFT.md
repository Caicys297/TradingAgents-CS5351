# O2 Implementation Execution Plan — Draft for Human Review

**Document version:** v0.1-DRAFT (Revision 2)  
**Status: Draft — Revision 2 post-implementation documentation alignment; Stage 2 not approved. Phase 1 merged by PR #16 at `808df04...`; Revision 2 is not a new pre-code approval.**

**Original pre-code approval:** A (Caicys297) approved commit `b0287da171cb77673bc7c03c4a6b13535d427730`, test plan `v0.3-DRAFT`, and execution plan `v0.1-DRAFT` in [PR #8 comment 6920115438](https://github.com/Caicys297/TradingAgents-CS5351/pull/8#issuecomment-6920115438) at `2026-11-16T15:02:47Z`.

**Revision 2 alignment approval:** A’s [PR #8 comment 6973848349](https://github.com/Caicys297/TradingAgents-CS5351/pull/8#issuecomment-6973848349) at `2026-11-18T08:59:29Z` approves Revision 2 as documentation alignment, not as a new pre-code approval or Stage 2 approval.

**Phase 1 implementation:** Merged by PR #16 at `main` merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`; PR head `2d2c63b162290a3dce6360fe88218927ea76a7bb`; two approved files only.

**Implementation baseline:** Phase 1 base `main` at `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`; merged at `808df04...`.

**Test-plan basis:** `test-plans/O2-Test-Plan-v0.3-DRAFT.md` Revision 2 in this documentation branch; not Stage 2 approval.

**PR #9 timing:** At the Phase 1 documentation approval point, PR #9 was open/unmerged. It later merged at `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`; the merged O2 allowlist now includes `input_condensation_audit_note`, and TC-23 below is aligned to that merged state.

## 1. Preconditions and approval gates

These gates applied to the original Phase 1 implementation and are recorded below. They do not approve Stage 2:

1. **Original pre-code test-plan approval:** A approved test plan `v0.3-DRAFT` in [PR #8 comment 6920115438](https://github.com/Caicys297/TradingAgents-CS5351/pull/8#issuecomment-6920115438) at `2026-11-16T15:02:47Z`.
2. **Original pre-code execution-plan approval:** The same PR #8 comment approved execution plan `v0.1-DRAFT` at docs commit `b0287da171cb77673bc7c03c4a6b13535d427730`.

Additional preconditions for Stage 2:

- Phase 1 implementation is merged at `main` commit `808df04...`; PR #16 head was `2d2c63b...`.
- Confirm Phase 1 scope remains the standalone manifest writer and its offline tests only. Stage 2 is not approved.
- Defer `cli/run.py`, `trading_graph.py`, shared integration, real unique run-directory integration, and three-platform CI acceptance until separately approved.
- Confirm C remains the sole integrator for shared `cli/run.py` and `trading_graph.py` changes when Stage 2 is approved (`requirements.yaml:16`).
- Confirm full O2 scope remains completed CLI runs only; failed/programmatic runs remain out of scope (`requirements.yaml:24`).
- Confirm the v0.3 test plan includes:
  - UUID collision retries without overwriting an existing run directory or manifest, and the new run directory is reserved before graph execution.
  - `allow_nan=false`; NaN and positive/negative Infinity are rejected.
  - Manifest write/serialization failure leaves no partial manifest, shows a provenance-failed warning, publishes no success path, and preserves the completed O4 effective rating.
  - Manifest `schema_version: "1.0.0"`.
  - O2-TC-18 uses the implementation PR’s dependency-file diff and writer-import inspection.
  - O2-TC-20 first-layer regression is `pytest -q`; live/integration conditions are listed separately.
  - O2-TC-21 covers Ubuntu, macOS, and Windows through F’s CI integration.
  - O2-TC-23 uses the merged Registry allowlist at `d36a677...`, including `input_condensation_audit_note`; unknown/unapproved fields and secrets remain excluded.
- Record Stage 2 approval separately. Revision 2 documentation alignment is not Stage 2 approval.

## 2. Implementation branch and base commit

- Implementation branch: `feat/o2-reproducibility-manifest`.
- Phase 1 base: `main` at `aa549f662a4cdb1836aaf448e3f51fbe57c6ce83`.
- Phase 1 was merged by PR #16 at `main` merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`; PR head was `2d2c63b162290a3dce6360fe88218927ea76a7bb`.
- Stage 2 has no approved branch or baseline yet; a new approved plan is required.

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

> **Phase 1 evidence boundary:** The original Phase 1 implementation and its 24 passing tests used the earlier merged allowlist, which excluded `input_condensation_audit_note`. PR #16’s 24 passing tests and CI validate that original Phase 1 state only; they do not validate the later TC-23 expectation. The TC-23 update aligned with the Registry merged at `d36a677...` is a planned expectation whose implementation and test synchronization/verification are still pending.

1. **Freeze approved Phase 1 schema and defaults.** Confirm `schema_version: "1.0.0"`, normalized identity fields, and the original Phase 1 merged allowlist used by the implementation. The later merged allowlist at `d36a677...` adds `input_condensation_audit_note`; TC-23’s updated expectation remains planned pending implementation and test synchronization.
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
| `tradingagents/repro/manifest.py` | Phase 1 isolated manifest construction, allowlist, fingerprint, metadata, artifact labels, canonical JSON, atomic temp-file write and promotion | **B** | Phase 1 implementation merged by PR #16 at `808df04...`; PR head `2d2c63b...`. |
| `test/offline/test_o2_manifest.py` | Phase 1 offline unit/behavior tests | **B** | Phase 1 test file merged by PR #16 at `808df04...`; PR head `2d2c63b...`. |
| `cli/run.py` | Reserve unique run directory before graph execution, invoke manifest writer, surface provenance-failed warning, collect artifact references | **C** | **Deferred from Phase 1.** Shared CLI integration. In the inspected ZIP snapshot, the run directory is `<results_dir>/<safe_ticker>/<date>` (`cli/run.py:36-42`, `:135-136`); message log appends (`:150-151`, `:162-163`); section reports use fixed names (`:175-178`); graph streams at `:241`; decision recorded at `:353`; cleanup at `:357-359`; report offer at `:388-389`; report-save failure at `:453-454`. |
| `tradingagents/graph/trading_graph.py` | Provide effective settings/run context without changing report/state/checkpoint contracts | **C** | **Deferred from Phase 1.** Shared graph integration. In the inspected ZIP snapshot: `run_settings()` `:255-275`; report path `:288-291`; state log `:438-476`; run signature `:140-165`. |
| `tradingagents/dataflows/files.py` | Reuse or assess atomic temp-file/promotion pattern | **C for edits; B may call** | **Deferred from Phase 1 for shared edits.** In the inspected ZIP snapshot, `replace_file()` uses temp + `os.replace` (`:14-33`); its cache-oriented `PermissionError` behavior (`:28-32`) must be reviewed against O2’s fail-soft provenance rules. |
| `tradingagents/dataflows/symbols.py` | Reuse path-safe ticker validation | **No edit; B/C reuse** | In the inspected ZIP snapshot, `safe_ticker_component()` validates traversal and unsafe values (`:155-180`). |
| `pyproject.toml` | Test discovery and markers | **C/F if changed** | **Deferred from Phase 1.** In the inspected ZIP snapshot, `testpaths` includes `tests` and `test/offline` (`:59`); integration excluded by default (`:60`); markers at `:61-64`. |
| `.github/workflows/ci.yml` | Three-platform CI and O2-TC-18 dependency gate | **C/F** | **Deferred from Phase 1.** In the inspected ZIP snapshot, CI runs `pytest -q` (`:36`) on `ubuntu-latest` only (`:15`, `:40`, `:56`); O2-TC-21 needs F’s CI coordination. |
| `test/offline/conftest.py` | Offline no-network fixture | **No edit expected** | In the inspected ZIP snapshot, this blocks network/curl access unless integration-marked (`:14-30`). |
| `test-plans/O2-Test-Plan-v0.3-DRAFT.md` | Test-plan baseline; Revision 2 documentation alignment approved by A; Stage 2 not approved. | **Review source; not B-owned edit** | Present in this documentation branch. Revision 2 alignment is not a new pre-code approval. |

## 6. Mapping to O2-TC-01 through O2-TC-25

Phase 1 writer-level mappings are recorded as implemented/tested in PR #16. Stage 2 mappings remain proposed and deferred. Candidate default command is `pytest -q`; Stage 2 tests have not been run.

> **TC-23 status:** The current `main` writer and `test_o2_tc_23_only_merged_allowlist_is_serialized` validate only the original Phase 1 allowlist, which excluded `input_condensation_audit_note`. They do not include or verify the field. TC-23’s updated expectation, aligned with the Registry merged by PR #9 at `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`, is planned; implementation and test synchronization/verification are still pending.

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
| `O2-TC-23` | Planned expectation aligned with the merged Registry at `d36a677...`: only allowlisted fields serialized; unapproved keys absent; allowlist includes `input_condensation_audit_note`. The current Phase 1 writer/test does not yet verify this field. | Pending implementation and test synchronization/verification |
| `O2-TC-24` | Package version, Python version, platform recorded when available | B; isolated test |
| `O2-TC-25` | Manifest contains agreed schema-version field and value `"1.0.0"` | B; isolated test |

## 7. Candidate offline test path and planned commands

- Phase 1 test file: `test/offline/test_o2_manifest.py`, merged by PR #16 at `808df04...` (PR head `2d2c63b...`).
- Phase 1 default command: `pytest -q`.
- Phase 1 targeted command: `pytest -q test/offline/test_o2_manifest.py`; [PR #16 comment 6954201609](https://github.com/Caicys297/TradingAgents-CS5351/pull/16#issuecomment-6954201609) records `24 passed`.
- Six CI checks on `2d2c63b` completed successfully in PR #16.
- Stage 2 commands and coverage require new approval; no Stage 2 execution evidence is recorded.

## 8. Stop conditions and draft status

Stop and request human/team approval before any edit if:

- O2 scope changes beyond the approved Phase 1 standalone writer and offline tests without approval.
- O2 scope changes beyond completed CLI runs.
- B is asked to edit `cli/run.py` or `trading_graph.py` without an explicit ownership change.
- Shared interfaces, report/state/memory/checkpoint behavior, or public signatures must change.
- A new runtime dependency is proposed.
- The Phase 1 merge commit `808df04...` or its approved two-file scope would be rewritten or discarded without explicit approval.
- Stage 2 integration is started without separate approval.
- UUID reservation/collision policy changes.
- `schema_version`, fingerprint fields, `allow_nan=false`, or allowlist content changes.
- The merged allowlist from `d36a677...` is changed without approval, or unknown/unapproved fields are treated as allowlisted.
- Fail-soft write-failure behavior changes.
- O2-TC-18 command or O2-TC-20 regression scope is undefined.
- O2-TC-21 platform scope changes or F does not support the CI matrix.
- The approved test plan or execution plan differs materially from this plan.

**Draft — Revision 2 documentation alignment approved by A; Stage 2 not approved.** No Stage 2 implementation, test execution, test result, commit, push, PR, or GitHub action is claimed.
