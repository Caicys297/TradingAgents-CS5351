# REQ-GOV-07 Coverage Audit (static analysis / safety checks)

Requirement (REQ-GOV-07, Must): "Every commit runs lint, type and dependency checks;
safety-relevant PRs also run contract, security, API-surface and permission checks."
Fit criterion: "CI runs required jobs on the stated triggers and an injected violation
blocks merge."

## Actual triggers and per-commit vs final-head
- `ci.yml` triggers: `push` (main, tags) + `pull_request`. Jobs run on each event.
- **Per-commit:** **NOT enforced.** No workflow runs on every commit of a feature
  branch; `push` covers `main`/tags, `pull_request` runs on the PR's (merge) head.
  A multi-commit PR is validated only at its final head — not "every commit".
  This gap is unresolved and must not be relabelled as complete. (A/F per-commit
  decision remains open; adopting a final-tree substitute requires course-level
  confirmation.)

## Lint / type / dependency (the "every commit" trio)
| Check | Status | Job / command |
|---|---|---|
| Lint | Implemented | `ruff check .` |
| Type | Implemented (scoped, baseline-gated) | `type check` / `python scripts/typecheck.py` |
| Dependency | Implemented | `dependency audit` / `python scripts/dep_audit.py` |

## Safety-relevant checks (contract / security / API-surface / permission)
| Check | Status | Evidence |
|---|---|---|
| API-surface / layering | **Partial** | `tests/test_layering.py` (vendor libs imported only by data layer) exists and runs in `tests` job — a real structural check, but not a formal public-API-surface contract gate on safety PRs |
| Contract | **Missing** | No dedicated contract check job/test |
| Security | **Missing** | `pip-audit` covers dependency vulns only; no code security scan (e.g. bandit) |
| Permission (safety paths) | **Missing** | No permission/safety-path check; `.opencode/`/`.agent/` governance not enforced in CI |

## Reuse note
`tests/test_layering.py` is the only existing safety-structural check; it should be
**reused** (required under safety-path PRs) rather than duplicated. The others require
C/D rules (contract/API-surface inventory, security exceptions, permission model) before
any check can be wired — out of this batch's production scope.

## Honest conclusion
- lint/type/dependency: implemented; per-commit trigger **not** met.
- contract/security/API-surface/permission: mostly **missing** (only a partial layering
  test). Do **not** claim REQ-GOV-07 complete. The smallest next step (C/D) is to adopt
  the existing `test_layering.py` plus define the contract/security/permission rules,
  then F wires them as required on safety-path PRs.
