# CI Closure v5 — Execution Plan

- **Document type:** Execution Plan (pre-code)
- **Batch identity:** `ci-closure-v5` (implementation PR batch key `pr-<N>` at implementation time)
- **Status:** PENDING A's formal approval against this file's fixed commit SHA. Not approved. Planning only; does not authorize implementation.
- **Recorded baseline:** `main@be51ff077cc3109d2bba19448c8d87317806ef8e` (verified read-only at publication). If `main` changes after publication, inspect the relevant differences before implementation; do not silently redefine scope.
- **Supersedes:** unresolved options in `2026-11-21_235554_CI_Closure_Review_Package_v4…`.

## A's decisions incorporated (authoritative)
1. A agrees in principle with WS A–E scope; design not expanded.
2. For CI/governance batches implemented by F, **non-implementer A reviews BOTH the Test Plan and Execution Plan**.
3. Authorization rule implemented by a **separate, narrowly scoped migration PR**, merged into `main` before the main batch relies on it.
4. No other member mapped to role F; the main PR does not authorize itself.
5. Legacy-gate inability to verify the migration is recorded transparently; no fabricated approval.
6. Permission baseline: read-only for PR execution; PR-reachable checkout `persist-credentials: false`; no exceptions for this batch.
7. A/admin configures required checks and verifies merge blocking once jobs have stable names.
8. A formally approves both plans and file scope against their fixed commit SHA before implementation.

## Workstreams and ownership
| WS | Content | Implementer | Approval |
|---|---|---|---|
| A | Per-commit Ruff (retain final-tree lint) | F | A (both plans) |
| B | Deterministic O4 CI wiring (six nodes) | F | A (both plans) |
| C | Minimum Contract/Security/API/Permission guards + negatives | F | A (both plans) |
| D | Genuine pre-code approval records | F prepares; A's genuine artifacts | A |
| E | AI-use evidence, final validation, admin handoff | F inventory/evidence | A/admin enforcement |

## Two-stage ordering
1. Publish plans → A formally approves fixed versions and scoped migration + main-batch work.
2. Separate authorization-migration PR → A's review/disposition of any legacy-gate limitation → merge into `main`.
3. Prepare the main batch's genuine records under the new rule, referencing the original approved plan commit and original A approval artifacts.
4. Implement the main closure batch only after its required approvals and prerequisite migration are in place.

## File / change scope (implementation batch)
| File | WS | Owner | Change |
|---|---|---|---|
| `scripts/lint_commits.py` | A | F | new: per-commit Ruff via `ci_event.resolve_range` |
| `scripts/ci_event.py` | A | F | minimal: optional explicit PR-head param (default unchanged) |
| `test/offline/test_lint_commits.py` | A | F | new: T1–T7 |
| `scripts/check_contracts.py` + `test/offline/test_contracts_guard.py` | C | F | new guard + negatives |
| `scripts/check_security.py` + `test/offline/test_security_guard.py` | C | F | new guard + negatives |
| `scripts/check_api.py` + `test/offline/test_api_guard.py` | C | F | new guard + negatives |
| `scripts/check_permissions.py` + `test/offline/test_permissions_guard.py` | C | F | new guard + negatives |
| `docs/ci/governance-guards.yaml` | C | F | new: protected paths/interfaces → node mappings + job names |
| `.github/workflows/ci.yml` | A/B/C | F | Ruff job edits; new O4 job; governance jobs; applicability includes guard scripts/tests/config/`ci.yml` |
| `docs/test-approvals/<batch>.json` | D | F | approval record(s) bound to published plan commit + PR |
| `docs/test-approvals/plans/ci-closure-v5/*` | D | F | this plan set (published) |
| `transcripts/CI-AI-Use-Log.md` | E | F | AI-use evidence for this batch |

## Governance job/check names (proposed)
`semantic (deterministic O4)`, `governance contract`, `governance security`, `governance api`, `governance permissions`. WS-A adds a per-commit step inside the existing `ruff (strict, full repo)` job.

## Applicability and conclusions
- Applicability (job/step) from changed files that include the guard scripts/tests/`docs/ci/governance-guards.yaml`/`ci.yml` themselves, so edits to a check cannot skip validation.
- Legitimate non-applicability → stable, distinct success ("skipped (no in-scope change)") recorded as a passing required check.
- Range-resolution error / missing required node / failed check → failure (never a skip). Guards write a small JSON result for auditability.

## API paths (verified from source at baseline)
- `TradingAgentsGraph.record_decision` → `tradingagents/graph/trading_graph.py`
- `get_global_news_yfinance`, `get_news_yfinance` → `tradingagents/dataflows/vendors/yahoo/news.py`
- Adapter tools `get_news`, `get_global_news` → `tradingagents/agents/tools.py`
(No `news_data.py`/`langchain_news.py` paths are used.)

## Permission baseline (per A)
Read-only for PR execution; PR-reachable checkout `persist-credentials: false`; no exceptions for this batch. `scripts/check_permissions.py` enforces effective (workflow ⊕ job) permissions with inheritance, `write-all`, ambiguous/expression values, PR-reachable writes, `pull_request_target` + secrets/PR-head checkout, restriction removal, unsafe inheritance; fails closed on unparseable YAML; normalizes the literal `on` key. Static YAML analysis cannot prove all runtime credential flows.

## Migration prerequisite (separate PR — not implemented now)
Purpose: enable non-implementer A to review BOTH plans for genuine F-implemented CI/governance batches, without a blanket override.
Minimal file scope (proposed by read-only inspection; finalize at migration time):
| File | Change |
|---|---|
| `scripts/check_test_approval.py` | narrow authorization addition (see constraints below) |
| `test/offline/test_check_test_approval.py` | focused tests + negatives for the new path and denials |
| `docs/ci/Test-Approval-Status.md` | document the rule + legacy-gate limitation |

Constraints preserved: author authentication; self-approval prohibition; original approval timestamps; immutable plan identity; batch binding; scope checks; existing historical-approval boundaries. No blanket A override for unrelated batches. The migration carries its own approval/evidence, separate from the main batch's records. Its legacy-gate limitation (the pre-migration checker cannot verify the new rule) is recorded transparently.

## Bounded validation
Focused unit tests per guard + WS-A T1–T7 + six O4 nodes; most negatives via temporary fixtures/scratch copies (no edits to `main`); representative end-to-end negatives only (one per protected category, one WS-A intermediate, one O4 failing node, one resolution error); focused regression for `ci_event` explicit-head adaptation; **one** final regression + Ruff after stabilization; normal remote CI on the final SHA. No repeated full runs absent a material change; never rerun known missing-approval failures for green.

## Failure propagation vs merge enforcement
(1) pytest node fails; (2) guard script nonzero → job fails; (3) required check prevents merging — (3) requires admin settings and evidence, not proven by (1)/(2).

## Administrator closure (A/admin; evidence from F)
Required checks on `main`: `tests (py3.11)`, `tests (py3.12, America/New_York)`, `tests (py3.13)`, `tests (py3.14)`, `clean-install smoke`, `ruff (strict, full repo)`, `requirements schema`, `type check`, `dependency audit`, `ai-use log`, `test approval`, `semantic (deterministic O5)`, plus new `semantic (deterministic O4)`, `governance contract`, `governance security`, `governance api`, `governance permissions`. Require approving review by a non-author; non-applicable checks must not block; define bypass boundaries; one controlled, unmerged verification that a required failure blocks merge; evidence that missing review blocks merge. Not complete without evidence.

## Completion criteria
Implementation merged (after prerequisite migration + both plan approvals) + guard negatives pass + genuine approvals recorded + remote CI green on final SHA + administrator enforcement verified with evidence. No category declared complete in planning; no universal-coverage claim.
