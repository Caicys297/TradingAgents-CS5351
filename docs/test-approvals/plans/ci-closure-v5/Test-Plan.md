# CI Closure v5 — Test Plan

- **Document type:** Test Plan (pre-code)
- **Batch identity:** `ci-closure-v5` (implementation PR batch key `pr-<N>` at implementation time)
- **Status:** PENDING A's formal approval against this file's fixed commit SHA. Not approved. This document is planning only; it does not authorize implementation.
- **Recorded baseline:** `main@be51ff077cc3109d2bba19448c8d87317806ef8e` (verified read-only at publication). If `main` changes after publication, inspect the relevant differences before implementation; do not silently redefine scope.
- **Supersedes:** the unresolved options in `2026-11-21_235554_CI_Closure_Review_Package_v4…` (A's decisions below resolve them).

## A's decisions incorporated (authoritative)
1. A agrees in principle with WS A–E scope: per-commit Ruff, fixed O4 cases, and the four minimum GOV-07 checks. Design is not expanded here.
2. For CI/governance batches implemented by F, **non-implementer A reviews BOTH the Test Plan and Execution Plan**.
3. That authorization rule is implemented by a **separate, narrowly scoped migration PR** that must merge into `main` before the main closure batch relies on it.
4. No other member is mapped to role F; the main implementation PR does not authorize itself.
5. Any legacy-gate inability to verify the migration is recorded transparently; no fabricated passing approval or retrospective pre-code compliance.
6. Permission baseline: read-only permissions for PR execution; PR-reachable checkout steps use `persist-credentials: false`. No exceptions pre-approved for this batch.
7. A/admin configures required checks and verifies merge blocking once new jobs have stable names.
8. A will formally approve the two published plans and file scope against their fixed commit SHA. The main batch is not implemented before those approvals exist.

## Scope (identical to Execution Plan)
Workstreams:
- **WS-A** Per-commit Ruff (retaining existing final-tree lint).
- **WS-B** Deterministic O4 CI wiring (fixed six nodes).
- **WS-C** Minimum Contract / Security / API / Permission guards with bounded negatives.
- **WS-D** Genuine pre-code approval records for this batch.
- **WS-E** AI-use evidence, final validation, administrator settings and actual merge-blocking verification.

## Two-stage ordering (identical to Execution Plan)
1. Publish plans → A formally approves fixed versions and scoped migration + main-batch work.
2. Separate authorization-migration PR → A's review/disposition of any legacy-gate limitation → merge into `main`.
3. Prepare the main batch's genuine records under the new rule, referencing the original approved plan commit and original A approval artifacts.
4. Implement the main closure batch only after its required approvals and the prerequisite migration are in place.

## Test Plan — acceptance cases

### WS-A Per-commit Ruff (F-owned)
Protected behavior: lint every commit while keeping final-tree `ruff check .`.
Acceptance (controlled temporary Git histories; no network; no disposable PRs):
- **T1** clean commit range → exit 0.
- **T2** bad intermediate commit k, fixed by k+1, HEAD clean → nonzero naming commit k though final-tree lint passes.
- **T3** PR enumeration uses the **actual PR head** + trusted merge-base, excluding `refs/pull/N/merge`.
- **T4** push `before..after` enumerated.
- **T5** missing/unresolvable base/head/before/after/required history → explicit nonzero (via `ci_event.EventError`).
- **T6** worktree/checkout/tool error → explicit nonzero.
- **T7** final-tree `ruff check .` retained and blocking.

### WS-B Deterministic O4 (F-owned) — fixed six nodes (verified on baseline)
1. `test/offline/test_evidence_gate_legacy_boundary.py::test_bare_complete_evidence_gates_and_preserves_buy` — complete evidence preserves rating.
2. `test/offline/test_evidence_gate_legacy_boundary.py::test_bare_missing_evidence_gates_to_review` — missing selected evidence → REVIEW.
3. `test/offline/test_evidence_gate_legacy_boundary.py::test_bare_unknown_config_aborts_no_logging_no_memory` — invalid analyst config prevents authoritative writes.
4. `test/offline/test_evidence_gate_legacy_boundary.py::test_bare_stale_buy_cannot_bypass_required_review` — stale effective_rating cannot bypass fresh evaluation.
5. `test/offline/test_evidence_gate_graph_integration.py::test_conflict_downgrades_at_boundary` — conflicting evidence → REVIEW.
6. `test/offline/test_evidence_gate.py::test_t07_recoverable_failure_fails_closed` — recoverable checker failure fails closed → REVIEW.

### WS-C Minimum GOV-07 — verified exact node IDs and protected paths
**Contract** — protected paths: `cli/run.py`, `tradingagents/graph/trading_graph.py`, `tradingagents/agents/state.py`, `tradingagents/repro/manifest.py`.
- Existing nodes: `test/offline/test_evidence_gate_cli_publication.py::test_cli_ordering_reserve_and_manifest`; `test/offline/test_evidence_gate_cli_publication.py::test_cli_completion_and_review_ordering`; `test/offline/test_evidence_gate.py::test_t25a_sources_agree_preserved`; `test/offline/test_evidence_gate_graph_integration.py::test_conflict_downgrades_at_boundary`; `test/offline/test_evidence_gate_graph_integration.py::test_resume_reaches_gate_with_restored_reports`; `test/offline/test_evidence_gate_graph_integration.py::test_resume_is_fresh_execution_for_gate`; `test/offline/test_o2_cli_manifest.py::test_real_reservation_retries_and_isolates_two_runs`; `test/offline/test_o2_cli_manifest.py::test_reservation_collision_exits_before_graph_and_preserves_existing_files`; `test/offline/test_o2_cli_manifest.py::test_manifest_write_failure_is_fail_soft_with_effective_rating`.
- Smallest addition: `scripts/check_contracts.py` runs the mapped node(s) when a protected path changes; negative = scratch-copy contract break (reservation vs graph order) → mapped node fails → nonzero.

**Security** — protected paths: `tradingagents/repro/manifest.py`, `cli/run.py`, `cli/display.py`, `tradingagents/reporting.py`.
- Existing nodes: `test/offline/test_o2_manifest.py::test_o2_tc_06_secret_fields_and_unapproved_keys_are_excluded`; `test/offline/test_o2_manifest.py::test_o2_tc_16_nested_secret_and_credential_url_are_redacted`; `test/offline/test_o2_manifest.py::test_o2_tc_16_credential_in_url_query_is_redacted_from_manifest_and_fingerprint`; `test/offline/test_o2_cli_manifest.py::test_tc23_effective_config_allowlist_and_secret_exclusion`; `test/offline/test_o2_manifest.py::test_o2_tc_05_artifact_stability_labels_and_relative_paths` (base-escape → `ValueError`); `test/offline/test_o2_manifest.py::test_o2_tc_13_serialization_failure_leaves_no_partial_manifest`; `test/offline/test_o2_cli_manifest.py::test_whole_save_failure_excludes_partial_leftover`; `test/offline/test_o2_cli_manifest.py::test_reservation_collision_exits_before_graph_and_preserves_existing_files`.
- Smallest addition: `scripts/check_security.py` runs these nodes on those path changes; negative = injected base-escape / unredacted secret in a scratch copy → nonzero. The O4 invalid-config test is a fail-closed **pattern only**; preserve manifest-write and O5 sink-failure policies; vulnerability scanning is not a substitute.

**API** — protected paths (verified from source): `tradingagents/graph/trading_graph.py` (`TradingAgentsGraph.record_decision`), `tradingagents/dataflows/vendors/yahoo/news.py` (`get_global_news_yfinance`, `get_news_yfinance`), `tradingagents/agents/tools.py` (`get_news`, `get_global_news` adapter tools).
- Reuse four: `test/offline/test_evidence_gate_audit.py::test_t20_record_decision_signature_unchanged`; `test/offline/test_evidence_gate_legacy_boundary.py::test_record_decision_signature_and_none_return_unchanged`; `test/offline/test_o5_regression.py::test_rt2_public_entry_keeps_signature_and_returns_str`; `test/offline/test_o5_regression.py::test_rt4b_ticker_news_signature_unchanged`.
- Smallest addition: `scripts/check_api.py` runs these four on API path changes; negative = altered parameter name / removed str return in a scratch copy → nonzero. Not every signature change is prohibited; judged against these expectations; no repo-wide snapshot system.

**Permission** — protected paths: `.github/workflows/*.yml`, `*.yaml`, and declared local actions/scripts consuming credentials.
- Baseline (per A): read-only for PR execution; PR-reachable checkout `persist-credentials: false`; no exceptions for this batch. `scripts/check_permissions.py` evaluates effective (workflow ⊕ job) permissions honoring inheritance; fails on `write-all`, ambiguous/expression values, PR-reachable write scopes, `pull_request_target` + secrets/PR-head checkout, `persist-credentials` not `false`, restriction removal, and unsafe inheritance; fails closed on unparseable/ambiguous YAML; normalizes the literal `on` key. Negative cases: escalation, restriction removal, unsafe inheritance, credential exposure. Static analysis does not prove all runtime credential flows.

### WS-D Genuine approval records
Records at `docs/test-approvals/*.json`, `batch_id=pr-<N>`, `feature=O4`, `plan_sha`=published plan commit, `plan_version`, `plan_path`, `requirement_ids`, `approved_test_ids`, `allowed_files`, `evidence`→A's genuine `TEST-APPROVAL` artifacts (test-kind + exec-kind). Two approvals are bound to the original approved plan commit; no borrowed approvals, no retrospective compliance.

### WS-E AI-use and final validation
AI-use evidence entry for this batch's code changes; focused unit tests per guard + WS-A + six O4 nodes; representative end-to-end negatives (one per protected category, one WS-A intermediate, one O4 failing node, one resolution error); focused regression for the `ci_event` explicit-head adaptation; **one** final regression + Ruff after stabilization; normal remote CI on the final SHA. Administrator sets required checks and verifies actual merge blocking with evidence.

## Migration prerequisite (separate PR; visible, not implemented here)
Authorization migration enabling non-implementer A to review BOTH plans for genuine F-implemented CI/governance batches. Minimal scope (see Execution Plan §Migration for the same list):
- Checker: narrow authorization addition preserving author authentication, self-approval prohibition, original timestamps, immutable plan identity, batch binding, scope checks, and existing historical-approval boundaries; no blanket A override.
- Focused tests for the new authorization path + negatives (non-F-implemented batch, self-approval, unrelated batch denied).
- Documentation of the rule and the legacy-gate limitation.
- The migration has its own approval/evidence, separate from the main batch's records.

## Completion criteria
Implementation merged (after prerequisite migration and both plan approvals) + guard negatives pass + genuine approvals recorded + remote CI green on final SHA + administrator enforcement verified with evidence. No CI category is declared complete in planning; no universal-coverage claim.
