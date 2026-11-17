# TC-O6-10b execution plan v1.0 — for A's approval

- Owner: F. Requirement: O6-FR-01. Test case: TC-O6-10b.
- Test plan: [O6 Integration Test Plan v3 FINAL, §4](https://github.com/Caicys297/TradingAgents-CS5351/blob/2755c247bdbc7c9f42994df51a93bff48b97b2b7/docs/req/reviews/o6/post-batch1/O6_Integration_Test_Plan_v3_FINAL.md#4-handler-level-unattributed-duplicate-start-regression-kept-separate).
- Test-plan disposition: A indicated approval for TC-O6-10b only. A's GitHub record identifying the exact document SHA and approval time is pending.
- Execution-plan disposition: pending A's separate approval. No test or implementation edits have started.
- Code baseline reviewed: [`c861d03`](https://github.com/Caicys297/TradingAgents-CS5351/commit/c861d0307238a3b763a35446f7da1245b1e8322a). Proposed implementation branch: `feature/o6-tc-10b-handler-regression`, from the shared `main` baseline confirmed by A. Record the actual SHA before editing.
- Single permitted file: `test/offline/test_o6_per_analyst_stats.py`. TC-O6-07, 07b, 11, 12, 13, and 14 are outside this scope.

## Proposed change

Add one parametrized test, `test_tc_o6_10b_duplicate_start_before_terminal_unattributed`, with cases `missing-key` (`None`, so the metadata key is omitted) and `unknown-key` (a string outside the selected key set). Use the existing `_handler`, `_start`, and `_end` helpers and controlled clock.

1. Complete one valid Market call to seed a non-empty named row. Record its named statistics and the initial legacy `llm_calls`. Assert the initial `unattributed_calls` is zero.
2. Emit a start event with `scope="analyst"` and a new run ID. Emit a second start with the same ID and same metadata before a terminal callback. After each start, assert that `unattributed_calls == 1` and that the named statistics equal the initial snapshot. After both starts, assert that legacy `llm_calls` increased by exactly two.
3. Emit a successful terminal callback for the same ID. Assert again that `unattributed_calls == 1`, the named statistics are unchanged, and the legacy call counter has retained its two-start increment.

This test exercises the callback handler using synthetic events. The existing offline guard applies. The test needs no API credentials or external model calls. Production code, CI configuration, shared files, and existing case behavior are outside the change scope.

## Verification after approval

Run from the implementation worktree with its existing project Python environment:

- `python -m pytest --collect-only -q` and confirm both new parameter IDs appear in default collection.
- `python -m pytest -v test/offline/test_o6_per_analyst_stats.py::test_tc_o6_10b_duplicate_start_before_terminal_unattributed`
- `python -m pytest -q test/offline/test_o6_per_analyst_stats.py`
- `python -m pytest -q`
- `ruff check test/offline/test_o6_per_analyst_stats.py` and `git diff --check`

Retain the approved plan links, actual baseline and first test commit, both pytest node IDs and their results, the actual regression and lint outcomes, and the implementation PR's CI run when available.
