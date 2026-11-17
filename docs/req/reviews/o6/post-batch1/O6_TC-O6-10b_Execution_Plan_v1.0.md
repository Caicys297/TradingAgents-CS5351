# TC-O6-10b — OpenCode Execution Plan v1.0 (for A's approval)

**Provenance:** F generated the original plan in the OpenCode Plan session. This review copy keeps that plan and incorporates corrections from the subsequent review.

**Snapshot:** local `origin/main` = `c861d0307238a3b763a35446f7da1245b1e8322a`. Read-only planning; no fetch/pull/switch/edit/test run.
**Status:** A's execution-plan approval is pending. The test plan is [O6 Integration Test Plan v3 FINAL, §4](https://github.com/Caicys297/TradingAgents-CS5351/blob/2755c247bdbc7c9f42994df51a93bff48b97b2b7/docs/req/reviews/o6/post-batch1/O6_Integration_Test_Plan_v3_FINAL.md#4-handler-level-unattributed-duplicate-start-regression-kept-separate). A indicated approval for TC-O6-10b only. The GitHub approval record for this exact document SHA is pending.

## 0. Scope
- **Only permitted file:** `test/offline/test_o6_per_analyst_stats.py` (325 lines; exists on disk; the Batch 1 offline file).
- **Out of scope (explicitly excluded):** production code, CI configuration, and TC-O6-07, 07b, 11, 12, 13, 14. This plan adds **one** handler-level regression only.
- **Nature:** a focused regression for an **in-scope call with a missing or invalid Analyst key**, exercising the duplicate-start *before terminal* timing that A's PR #11 review flagged as a non-blocking gap.

## 1. Existing helpers and coverage (reviewed)
- Helpers (lines 20–77): `MARKET`/`NEWS`/`SELECTED` constants; `FakeClock` (callable, `set()`); `_handler()` → `(StatsCallbackHandler(SELECTED, clock=fake), clock)`; `_start(handler, clock, run_id, *, scope="analyst", agent_key=None, t=None)` (sets `metadata["scope"]`/`["agent_key"]`, calls `on_chat_model_start`); `_end(handler, clock, run_id, *, input_tokens, output_tokens, t=None)`; `_error(handler, clock, run_id, *, t=None)`; `_row(stats, key)` → `stats["analysts"].get(key)`.
- **TC-O6-08** (lines 224–243): baseline Market row → one missing-identity in-scope call → `unattributed_calls == 1`, Market row unchanged → then **replays start after the terminal event** and asserts still `1`.
- **TC-O6-10** (lines 284–306): empty key, unknown key, non-string unhashable key → `unattributed_calls == 3`, no rows → then replays each **start after terminal**, still `3`.
- **Gap this case fills:** existing coverage replays a start **after** the terminal callback. A's note is about a **duplicate start before the terminal** callback. TC-O6-10b targets that exact timing, with the terminal **end** event following the two starts.

## 2. Fixture
- Reuse existing `_handler()` (fresh `StatsCallbackHandler` with `SELECTED = {"market","news"}` and a `FakeClock`).
- Seed **existing named rows** so "unchanged" is meaningful: one completed valid Market call (e.g. `_start("m1", agent_key=MARKET, t=0.0)` → `_end("m1", 100, 20, t=1.0)`), then save the full `handler.get_agent_stats()["analysts"]` snapshot as `before`. Assert the initial `unattributed_calls` is zero.
- Capture `llm_baseline = handler.get_stats()["llm_calls"]` (== 1 after the seed call).
- No new imports beyond what exists (`AIMessage`, `ChatGeneration`, `LLMResult` already imported). No network; the autouse `_no_network` guard applies.

## 3. Callback sequence (same `run_id`, in-scope, missing or unknown key)
Run the same sequence in two parameterized scenarios with a fresh handler per scenario: `agent_key=None` (`missing-key`) and `agent_key="fundamentals"` (`unknown-key`, outside `SELECTED`). Within each scenario use one new `run_id`, e.g. `"u1"`:
1. `_start(handler, clock, "u1", scope="analyst", agent_key=agent_key, t=1.0)` — first start
2. `_start(handler, clock, "u1", scope="analyst", agent_key=agent_key, t=1.5)` — **duplicate start, same run_id, before terminal**
   - **Checkpoint A (before terminal):** assert `unattributed_calls == 1` and all named rows unchanged.
3. `_end(handler, clock, "u1", input_tokens=10, output_tokens=5, t=2.0)` — terminal callback
   - **Checkpoint B (after terminal):** assert `unattributed_calls == 1` and all named rows unchanged.

## 4. Exact assertions
- **Before terminal (Checkpoint A):**
  - `handler.get_agent_stats()["unattributed_calls"] == 1`
  - `handler.get_agent_stats()["analysts"] == before` (deep-equal)
- **After terminal (Checkpoint B):**
  - `handler.get_agent_stats()["unattributed_calls"] == 1` (not 2 — duplicate start deduped)
  - `handler.get_agent_stats()["analysts"] == before` (deep-equal; named rows unchanged)
- **Legacy counter:**
  - `handler.get_stats()["llm_calls"] == llm_baseline + 2` (both starts increment legacy; baseline semantics preserved). With the seed call, `llm_baseline == 1` → expect `3`.
  - Check the `llm_calls` delta after both starts and again after the terminal callback. The legacy token totals may include the terminal event's `10/5` usage.

## 5. Proposed test node ID
- Function: `test_tc_o6_10b_duplicate_start_before_terminal_unattributed`
- Full node ID: `test/offline/test_o6_per_analyst_stats.py::test_tc_o6_10b_duplicate_start_before_terminal_unattributed`
- Parameter IDs: `[missing-key]` and `[unknown-key]`.
- **Placement:** append after TC-O6-10 (after line 306), with a `# -- TC-O6-10b: duplicate start before terminal (in-scope missing/invalid key) --` banner. Do not modify existing tests.

## 6. Offline verification commands (to run at implementation time — not now)
From repo root, using the worktree venv:
1. `.venv/bin/python -m pytest -q test/offline/test_o6_per_analyst_stats.py` → expect all existing tests and both new parameterized cases to pass.
2. `.venv/bin/python -m pytest -q test/offline/test_o6_per_analyst_stats.py::test_tc_o6_10b_duplicate_start_before_terminal_unattributed -v` → both parameterized cases should pass.
3. `.venv/bin/python -m pytest --collect-only -q` → both new parameterized nodes should appear in default collection.
4. `.venv/bin/python -m ruff check test/offline/test_o6_per_analyst_stats.py` → clean.

## 7. Evidence to retain
- Reviewed code snapshot `c861d03`, actual implementation baseline SHA once confirmed by A, and first test commit SHA.
- Both parameterized node IDs and their pass/fail results; before/after `get_agent_stats()` snapshots (Checkpoints A and B) showing `unattributed_calls == 1`.
- Legacy `get_stats()` before/after showing `llm_calls == baseline + 2`.
- `pytest --collect-only -q` output (offline count includes the new node); Ruff result; offline network-guard assurance (autouse `_no_network` applies — no new network use).
- **Test-plan version and document SHA:** O6 Integration Test Plan v3 FINAL, `2755c247bdbc7c9f42994df51a93bff48b97b2b7`. Record A's approval link and time when available.
- **Execution-plan approval:** PENDING (A).

## 8. Guardrails / notes for A
- Adds **one** test function to the single permitted file; **no** production/CI/shared edits.
- Complements (does not duplicate) TC-O6-08/10: those replay a start **after** the terminal; TC-O6-10b asserts the duplicate-start **before** terminal path and that the legacy counter still increments twice.
- The existing header docstring (line 1) lists "TC-O6-01..06, 08..10"; the implementer may add "10b" to that docstring — noted as a minor, in-file documentation touch (still within the permitted file).

---

## Decisions / confirmations needed from A
1. **Approve execution-plan scope:** one handler-level regression in the single permitted file (TC-O6-10b), no production/CI/other-case changes.
2. **Confirm implementation baseline** for the standalone test change and approve the execution plan, including its two parameterized cases.
3. **Record the test-plan approval** for v3 FINAL at `2755c24` and only TC-O6-10b.

No files were edited, nothing was fetched/pulled/switched, and no tests were run. Plan returned for review.
