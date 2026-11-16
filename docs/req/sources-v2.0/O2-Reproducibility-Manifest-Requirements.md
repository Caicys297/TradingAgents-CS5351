# O2 — Reproducibility Manifest
## Requirements and Acceptance Specification

**Owner:** Member B  
**Document version:** O2-REQ-v1.0 (proposed)  
**Status:** Draft — pending team review and human approval before implementation  
**Registry/Schema target:** D1 Registry 1.0.0 / project Schema 1.0.0, pending F's validation  
**Evidence basis:** Read-only OpenCode inspection of `D:\TradingAgents-CS5351-main\TradingAgents-CS5351-main`. The inspected copy had no `.git`, so its current commit is unverified. Source facts below must be checked against the active shared branch before implementation approval.

> This document defines proposed requirements and tests. It does not claim approval, implementation, test execution, or CI success. IDs and priorities remain proposed until the team confirms the Registry convention and values.

## 1. Problem

The inspected TradingAgents baseline records run settings, state, reports, and logs across separate artifacts. Normal CLI analysis runs do not have a unique per-invocation provenance manifest. The CLI reuses a ticker/date directory, so some artifacts are overwritten and others are appended across runs.

O2 adds a structured manifest that records selected normalized run inputs, approved configuration/model fields, available code/runtime identity, and artifact references. Its deterministic fingerprint covers selected run fields/configuration only. Unless an immutable per-run market/news snapshot is captured, actual input-data provenance is **not captured** and O2 must not claim full reproducibility.

## 2. Scope

### Proposed v1 scope

- One manifest per completed CLI analysis invocation.
- Collision-resistant invocation ID and non-overwriting manifest path.
- Allowlisted run/configuration metadata and deterministic input/config fingerprint.
- Explicit missing-metadata status and artifact stability labels.
- Clear declaration when actual market/news data provenance is not captured.

### Excluded unless separately approved

Programmatic runs, backtests, replay, database/UI, immutable vendor-payload archiving, and changes to report formats, memory logs, checkpoint IDs, or public return values.

**Pending:** confirm whether v1 covers completed CLI runs only, whether failed runs need manifests, and the final manifest path/write-failure policy.

## 3. Baseline evidence

The following source references are from the inspected copy, not verified against a current Git commit:

| Finding | Evidence |
|---|---|
| CLI run directory is `<results_dir>/<safe_ticker>/<trade_date>` and is reused | `cli/run.py` `_run_directory()` lines 36–42; creation lines 135–136 |
| `message_tool.log` is appended to | `cli/run.py` lines 139–163 |
| Per-section reports have fixed names and are opened in write mode | `cli/run.py` lines 166–179 |
| Complete reports use fixed filenames; default path includes a timestamp | `tradingagents/reporting.py` lines 113–121; `tradingagents/graph/trading_graph.py` lines 288–291 |
| State log uses a fixed date filename and write mode | `tradingagents/graph/trading_graph.py` lines 470–474 |
| No normal CLI per-invocation ID was found | `cli/run.py` lines 99–389; backtest IDs are separate in `tradingagents/backtest.py` lines 130–140, 168–173 |
| Existing run settings are an allowlist | `tradingagents/graph/trading_graph.py` lines 255–275 |
| Mutable per-symbol data cache is not a run snapshot | `tradingagents/dataflows/vendors/yahoo/ohlcv.py` lines 181–224 |
| Live news/social data changes over time | `README.md` lines 381–401, especially line 387 |
| Ticker path validation helper exists | `tradingagents/dataflows/symbols.py` lines 155–180 |

## 4. Functional requirements

MoSCoW values below are **proposed**: FRs are suggested `Must`; NFRs are suggested `Should`. All require team confirmation.

| ID | Priority | Requirement | Tradeoff (proposed) | Source |
|---|---|---|---|---|
| O2-FR-01 | Must | For each in-scope completed CLI invocation, create one valid JSON provenance manifest. | Adds manifest work/storage to completed CLI runs; failed-run scope remains open. | O2 draft, FR-01 |
| O2-FR-02 | Must | Generate one collision-resistant invocation ID per run, distinguishing same-ticker/date and same-second invocations. | Adds ID generation/collision handling; does not preserve mutable artifact contents. | O2 draft, FR-02 |
| O2-FR-03 | Must | Store each manifest at a unique, non-overwriting path inside the approved results boundary. | Adds per-invocation storage; exact path policy awaits C/A. | O2 draft, FR-03 |
| O2-FR-04 | Must | Record approved normalized identity fields: ticker, asset type, analysis date, selected analysts. Raw ticker is optional and requires approval. | Restricts identity to approved normalized fields; raw input may be omitted. | O2 draft, FR-04 |
| O2-FR-05 | Must | Record only approved effective configuration/model fields using an allowlist; never serialize full config or environment. | Less diagnostic detail than a full config dump. | O2 draft, FR-05 |
| O2-FR-06 | Must | Record package/runtime identity and Git commit/dirty state when available. Represent missing values explicitly; never fabricate them. | Allows incomplete provenance when metadata is unavailable. | O2 draft, FR-06 |
| O2-FR-07 | Must | Compute a deterministic SHA-256 fingerprint over explicitly approved normalized run fields/configuration and document normalization. | Fingerprint covers selected fields/configuration, not vendor data. | O2 draft, FR-07 |
| O2-FR-08 | Must | Exclude run ID, timestamps, duration, artifact paths, secrets, and market/news payloads from the deterministic fingerprint. | Improves stability but prevents data-level identity claims. | O2 draft, FR-08 |
| O2-FR-09 | Must | If no immutable per-run market/news snapshot exists, record `actual_input_data_provenance: not_captured`; do not call the fingerprint a data hash. | Avoids overstating reproducibility; cannot reconstruct vendor payloads. | O2 draft, FR-09 |
| O2-FR-10 | Must | Reference agreed artifacts using relative paths where possible and label each `run_unique`, `shared_mutable`, or `not_persisted`. | Mutable links cannot preserve prior contents. | O2 draft, FR-10 |
| O2-FR-11 | Must | Exclude API keys, tokens, passwords, credential-bearing URLs, unrelated environment variables, and other secrets. | Protects credentials while reducing diagnostic detail. | O2 draft, FR-11 |
| O2-FR-12 | Must | Include an agreed schema version and stable field names. | Requires version and compatibility management. | O2 draft, FR-12 |
| O2-FR-13 | Must | Write valid JSON atomically, leaving no partial manifest after interruption/failure. | Adds write-path care; does not itself choose fail-soft/closed behavior. | O2 draft, FR-13 |
| O2-FR-14 | Must | Define visible handling for unavailable optional metadata and manifest write failures; do not silently fabricate values. | Requires a degradation policy; write-failure behavior remains open. | O2 draft, FR-14 |

## 5. Non-functional requirements

| ID | Priority | Requirement | Tradeoff (proposed) | Source |
|---|---|---|---|---|
| O2-NFR-01 | Should | Use the Python standard library unless another dependency is justified and approved. | May forgo convenient third-party libraries. | O2 draft, NFR-01 |
| O2-NFR-02 | Should | Canonicalization is deterministic: sorted keys, stable separators, UTF-8, documented normalization. | Constrains serialization choices. | O2 draft, NFR-02 |
| O2-NFR-03 | Should | Use an allowlist; serialized output contains no secrets. | Reduces diagnostic detail. | O2 draft, NFR-03 |
| O2-NFR-04 | Should | Tests run offline without live vendors, market data, or LLM calls. | Fakes may not exercise live vendor behavior. | O2 draft, NFR-04 |
| O2-NFR-05 | Should | Paths and serialization work on the team-approved supported platforms, including Windows if approved. | Cross-platform support increases test burden; platform scope is pending. | O2 draft, NFR-05 |
| O2-NFR-06 | Should | Integration is additive and preserves existing report, memory-log, checkpoint, and public API behavior unless separately approved. | Constrains refactoring. | O2 draft, NFR-06 |
| O2-NFR-07 | Should | Manifest is human-readable JSON with documented stable keys. | Stable keys constrain schema evolution. | O2 draft, NFR-07 |

## 6. Fit criteria and traceability

All criteria and tests are proposed. Proposed verification additions are marked accordingly.

| Fit criterion | Measurable pass condition | Requirement(s) | Test ID(s) |
|---|---|---|---|
| O2-FC-01 | In-scope completed invocation creates one valid manifest with required fields/schema version. | FR-01, FR-03, FR-12 | TC-01, TC-25 |
| O2-FC-02 | Two same-ticker/date invocations retain two independently readable manifests. | FR-02, FR-03 | TC-04, TC-11 |
| O2-FC-03 | Same normalized included inputs/config yield identical fingerprint independent of key order. | FR-04, FR-07, NFR-02 | TC-02, TC-10 |
| O2-FC-04 | Changing an included field changes the fingerprint; excluded fields do not. | FR-04, FR-07, FR-08 | TC-03, TC-12 |
| O2-FC-05 | Run ID and volatile timestamps do not affect deterministic fingerprint. | FR-07, FR-08 | TC-02 |
| O2-FC-06 | Missing Git/model metadata is explicit, and available package/runtime values are recorded. | FR-05, FR-06, FR-14 | TC-08, TC-09, TC-17, TC-24 |
| O2-FC-07 | No unapproved config fields or secret values appear in manifest. | FR-05, FR-11, NFR-03 | TC-06, TC-16, TC-23 |
| O2-FC-08 | Every artifact reference has the correct stability label. | FR-10 | TC-05 |
| O2-FC-09 | Without immutable snapshot, provenance is exactly `not_captured`; no data-hash/full-reproducibility claim. | FR-09 | TC-07 |
| O2-FC-10 | Write failure follows approved policy and leaves no partial JSON. | FR-13, FR-14 | TC-13, TC-14 |
| O2-FC-11 | Existing report/state/memory/checkpoint/public-interface behavior is preserved. | NFR-06 | TC-20 (proposed regression check) |
| O2-FC-12 | No new third-party runtime dependency is introduced. | NFR-01 | TC-18 (proposed Static Analysis Gate check) |
| O2-FC-13 | Manifest tests use fakes and run without network/vendor/market-data/LLM access. | NFR-04 | TC-19 (proposed offline test) |
| O2-FC-14 | Path/serialization tests pass on every team-approved CI platform; platform list must be explicit. | NFR-05 | TC-21 (proposed platform check); TC-10/15 supporting only |
| O2-FC-15 | JSON parses, required keys exist, and keys match documented schema. | NFR-07 | TC-01 |
| O2-FC-16 | Manifest contains normalized ticker, asset type, analysis date, selected analysts. | FR-04 | TC-22 (proposed) |
| O2-FC-17 | Only allowlisted config/model fields are serialized; unapproved keys are absent. | FR-05 | TC-23 (proposed) |
| O2-FC-18 | Package version, Python version, and platform are recorded when available. | FR-06 | TC-24 (proposed) |
| O2-FC-19 | Manifest contains the agreed schema-version field and value. | FR-12 | TC-25 (proposed) |

## 7. Proposed test cases

None of these tests are claimed implemented, executed, or approved. `test/offline/` and CI collection must be confirmed with F.

| Test ID | Scenario | Expected result | Requirement mapping |
|---|---|---|---|
| O2-TC-01 | Valid completed invocation | One parseable manifest with required fields and schema version | FR-01, FR-12, NFR-07 |
| O2-TC-02 | Same normalized fields/config with reordered dictionary keys | Identical fingerprint | FR-07/08, NFR-02 |
| O2-TC-03 | Change included fields individually | Corresponding fingerprint changes | FR-07 |
| O2-TC-04 | Two same-ticker/date invocations | Two distinct readable manifest paths; first is not overwritten | FR-02/03 |
| O2-TC-05 | Reference report/state/message artifacts | Correct stability labels; mutable artifacts not claimed immutable | FR-10 |
| O2-TC-06 | Fake secret and credential-bearing URL in supplied config | No secret key/value or credentials serialized | FR-05/11, NFR-03 |
| O2-TC-07 | No immutable market/news snapshot | `actual_input_data_provenance` is `not_captured`; no data hash | FR-09 |
| O2-TC-08 | Git unavailable | Explicit unavailable status; manifest creation continues | FR-06/14 |
| O2-TC-09 | Model/provider metadata missing | Explicit missing status; no invented values | FR-05/06 |
| O2-TC-10 | Empty optional fields, Unicode, reordered mappings | Valid JSON and deterministic equivalent fingerprint | FR-07, NFR-02/05 |
| O2-TC-11 | Two invocations start within same second | Distinct IDs and paths | FR-02/03 |
| O2-TC-12 | Raw ticker variants normalize identically | Same normalized identity/fingerprint if raw ticker excluded | FR-04/07 |
| O2-TC-13 | Non-serializable value | Approved error behavior; no partial/corrupt manifest | FR-13/14 |
| O2-TC-14 | Manifest destination unwritable | Approved fail-soft/closed behavior; no partial file | FR-14 |
| O2-TC-15 | Invalid/path-traversal ticker | Rejected without writing outside results boundary | FR-03, NFR-05 |
| O2-TC-16 | Nested secret or credential URL | Secret excluded/redacted | FR-11, NFR-03 |
| O2-TC-17 | Git lookup OS/timeout failure | Explicit unavailable/error status; no fabricated data | FR-06/14 |
| O2-TC-18 | Inspect runtime dependencies | No new third-party runtime dependency | NFR-01; proposed Static Analysis Gate check |
| O2-TC-19 | Run manifest tests with fakes and network disabled | No vendor/market-data/LLM/network access | NFR-04; proposed |
| O2-TC-20 | Regression-check agreed existing outputs/interfaces | Existing behavior is preserved | NFR-06; proposed |
| O2-TC-21 | Run path/serialization checks on approved CI platform matrix | Checks pass on every explicitly supported platform | NFR-05; proposed, platform matrix pending |
| O2-TC-22 | Inspect produced manifest identity fields | Normalized ticker, asset type, date, analysts are present | FR-04; proposed |
| O2-TC-23 | Supply allowlisted and unapproved config keys | Only allowlisted fields are serialized | FR-05; proposed |
| O2-TC-24 | Supply available package/Python/platform metadata | Those values are present; missing values are explicit | FR-06; proposed |
| O2-TC-25 | Inspect manifest schema-version field | Agreed field/value is present | FR-12; proposed |

## 8. Proposed interface and candidate locations

**Candidate interface, pending C's architecture review:**

```python
build_run_manifest(*, normalized_inputs, approved_config, run_id,
                   git_metadata=None, artifacts=None) -> dict
compute_input_config_fingerprint(*, normalized_inputs, approved_config) -> str
write_run_manifest(path, manifest) -> Path
```

Candidate CLI integration: `cli/run.py`. Candidate module: `tradingagents/repro/manifest.py`; package location must be confirmed. Candidate tests: `test/offline/`, but current inspected pytest configuration does not collect it by default (`pyproject.toml:58-59`). These are candidate locations, not approved changes.

Artifact stability in the inspected snapshot: ticker/date directory, message log, per-section reports, and per-date state log are `shared_mutable`; immutable market/news snapshot is `not_persisted`; a timestamped complete report is `run_unique` by default but not guaranteed. Recheck against the active shared commit.

## 9. Open decisions

- Confirm v1 run scope and whether failed invocations produce a manifest.
- Confirm manifest path/ID policy and whether timestamps/other fields enter no fingerprints (proposed exclusion above).
- Confirm exact fingerprint field allowlist, including portfolio/memory context.
- Confirm fail-soft versus fail-closed behavior for manifest write failure.
- Confirm supported platform matrix and CI placement for TC-21.
- Confirm whether proposed IDs/priorities and registry-level status metadata are accepted by the D1 Schema 1.0.0.
- Confirm offline test directory and CI discovery with F.
- Confirm module boundary/shared-file ownership with C/A.

## 10. Review and approval record

- **Requirements:** Draft — pending team review.
- **Test plan:** Proposed — requires separate human approval before implementation.
- **Approver, timestamp, evidence:** Not recorded.
- **Implementation/test/CI status:** Not claimed; no tests or validator were run for this document.
