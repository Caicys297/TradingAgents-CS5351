# CI Closure v5 — Implementation Evidence (WS A–C)

Bounded evidence for PR #37 (approved plan `ed0589f`). Distinguishes **observed
command output** from **summaries**. This is a record of what was run — not an
approval and not a claim beyond what the commands showed.

## Scope
- WS-A per-commit Ruff (`scripts/lint_commits.py`, `ci_event.py` explicit PR head).
- WS-B deterministic O4 CI job (six fixed nodes).
- WS-C governance guards: contract / security / api / permission.
- WS-D genuine approval records (submitted; see Test Approval limitation below).
- WS-E AI-use evidence.

## Focused validation (observed)
```
$ pytest -q test/offline/test_lint_commits.py test/offline/test_contracts_guard.py \
    test/offline/test_security_guard.py test/offline/test_api_guard.py \
    test/offline/test_permissions_guard.py test/offline/test_ci_event_ranges.py \
    <six O4 nodes>
47 passed
$ ruff check .          → All checks passed
```
Full regression recorded before this follow-up: `2090 passed, 1 skipped, 1 deselected`.

## Real-contract negative experiments (WS-C)

Purpose: the unit tests use deliberately failing temporary pytest nodes to prove
failure propagation; they do **not** establish that the real mapped contracts are
protected. The experiments below do. Each ran in an **isolated temporary clone** of
the branch (a real git repo so `ci_event.resolve_range` works). **No production
mutation entered the implementation branch or any commit.**

Invocation for each (push range `origin/main..HEAD`):
```
GITHUB_EVENT_NAME=push GITHUB_BEFORE=$(git rev-parse origin/main) \
GITHUB_AFTER=$(git rev-parse HEAD) python scripts/check_<category>.py --root .
```

### Contract — fresh-resume completion reset
- Mapped node: `test/offline/test_evidence_gate_graph_integration.py::test_resume_is_fresh_execution_for_gate`.
- Control (unmodified temp copy): `1 passed` (observed).
- Isolated mutation (one): `tradingagents/graph/trading_graph.py` `end_checkpoint` no longer resets `_completion` (a stale verdict could be reused across windows).
- Guard: `scripts/check_contracts.py` → **exit 1** (observed).
- Key assertion (observed): `AssertionError: assert ... is None` at
  `test/offline/test_evidence_gate_graph_integration.py:388` (`assert g.last_completion is None`).
- Guard message (observed): `CONTRACT GUARD FAILED: a mapped contract node failed`.

### Security — manifest base-directory escape rejection
- Mapped node: `test/offline/test_o2_manifest.py::test_o2_tc_05_artifact_stability_labels_and_relative_paths`.
- Control (unmodified temp copy): `1 passed` (observed).
- Isolated mutation (one): `tradingagents/repro/manifest.py` `_relative_posix_path` no longer rejects a path that escapes the provided base.
- Guard: `scripts/check_security.py` → **exit 1** (observed).
- Key assertion (observed): `Failed: DID NOT RAISE ValueError` at
  `test/offline/test_o2_manifest.py:113` (expected `pytest.raises(ValueError)` for the escaping path).
- Guard message (observed): `SECURITY GUARD FAILED: a mapped security node failed`.

### API — Yahoo news parameter signature
- Mapped node: `test/offline/test_o5_regression.py::test_rt4b_ticker_news_signature_unchanged`.
- Control (unmodified temp copy): `1 passed` (observed).
- Isolated mutation (one): `tradingagents/dataflows/vendors/yahoo/news.py` `get_news_yfinance` parameter `end_date` renamed to `to_date`.
- Guard: `scripts/check_api.py` → **exit 1** (observed).
- Key assertion (observed): `AssertionError: assert ['ticker','start_date','to_date'] == ['ticker','start_date','end_date']` at `test/offline/test_o5_regression.py:89` (`'to_date' != 'end_date'`).
- Guard message (observed): `API GUARD FAILED: a mapped api node failed`.

Summary of outcomes:

| Category | Mapped node | Control | Mutation | Guard exit | Assertion |
|---|---|---|---|---|---|
| Contract | `test_resume_is_fresh_execution_for_gate` | pass | `end_checkpoint` reset removed | 1 | `assert g.last_completion is None` |
| Security | `test_o2_tc_05_artifact_stability_labels_and_relative_paths` | pass | base-escape rejection removed | 1 | `DID NOT RAISE ValueError` |
| API | `test_rt4b_ticker_news_signature_unchanged` | pass | `end_date`→`to_date` | 1 | `'to_date' != 'end_date'` |

None of the failures were missing dependencies, import errors, syntax errors, or
missing nodes — each was the intended contract assertion. The temporary clones
were deleted; the implementation checkout was untouched.

### Limitation on raw logs
The three experiments' raw terminal logs were not retained as standalone files.
The observed lines above are reproduced from the recorded fix reports
(`2026-11-22_021538_PR37_Reviewed_Gaps_Fix_Report.md` and the companion reply) and
the session evidence; full raw scrollback is not preserved. This document does not
reconstruct output beyond what those records contain.

## Test Approval limitation (unchanged, honest)
The pre-migration checker maps O4 `test_plan` to reviewer role **F**; A (role A)
approved both plans. Locally reproduced: `test_plan for O4 requires reviewer F (or
delegation); author role 'A'` and `missing required test-plan approval`;
`execution_plan` verifies. The `test approval` job therefore fails. No fabricated
approval, no #32 exception reuse, no checker/record modification. Final approval-
record reconciliation depends on the separate authorization-migration PR.
