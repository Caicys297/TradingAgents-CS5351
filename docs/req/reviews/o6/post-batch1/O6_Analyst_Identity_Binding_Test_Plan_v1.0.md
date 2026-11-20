# O6 Analyst Identity Binding — Test Plan v1.0

**Status: PENDING A's pre-code approval.**
**Historical inspection baseline:** `808df04` (`808df04f320d95c1ab4ef5a6e88149335cdeff41`).
**Approved implementation starting point:** `main@d36a677` (`d36a677d4738efd365b6bbcf6f69f993acf8fd3c`).
**Actual implementation branch HEAD: MUST be recorded before the first code edit** in the implementation PR.
**A's decision reference:** PR #6 https://github.com/Caicys297/TradingAgents-CS5351/pull/6#issuecomment-6977306501.

## 0. Ownership (recorded)
- **F's independent implementation PR is limited to exactly two files:** `tradingagents/graph/setup.py` and the new `test/offline/test_o6_analyst_subgraph.py`.
- **Test helpers are local to the new test file** (no edits to `tests/test_graph_end_to_end.py`).
- **C owns** `cli/run.py` and `cli/display.py`. Graph-config-only CLI validation belongs to C's integration checks.

## 1. Registration and harness

### 1a. TC-O6-07, 07b, 11 — recorder + handler, once each
Register **one observing recorder** and **one `StatsCallbackHandler`**, each registered **once**, through the **single constructor path**: `TradingAgentsGraph(callbacks=[recorder, handler])` → `create_tier_client(config, tier, callbacks=…)` → `llm.with_config({"callbacks": …})` (mirrors `trading_graph.py:78-80`, `run.py:122-128`). No dual constructor+graph-config registration in the harness.

### 1b. TC-O6-13 — observing callback only
For TC-O6-13, register **only the observing callback**. It forwards each real event to the handler **once** and takes the planned snapshots (S0/S1/S2, §7). No separate recorder is registered for this case.

### 1c. Shared harness details
- Handler is given the **current run's validated keys**: `StatsCallbackHandler(selected_analyst_keys={spec.key for spec in plan.specs}, clock=fake)` (else `_valid_keys` is empty and nothing attributes, `stats_handler.py:80`).
- **Local helpers in the new file:** a callback-forwarding client (`get_llm()` → `model.with_config({"callbacks": callbacks})`, fixing the harness `_Client` bare-model discard), a recorder capturing `(run_id, metadata, phase)` at start/end/error, a deterministic-usage model subclass, and a local `_graph`. Tests observe identity **only** from the recorder's `on_chat_model_start` kwargs and from `get_agent_stats()` — they never inject `scope`/`agent_key` themselves.

## 2. Production candidate (unchanged)
- Node-level metadata at the analyst boundary using the current run's validated `spec.key`:
  `add_node(spec.agent_node, _analyst_graph(...), metadata={"scope": "analyst", "agent_key": spec.key})`.
- Baseline trace (verified at `d36a677`, same `setup.py` blob `7cb53be`): `spec.key` only at `setup.py:144-146`; ordinary `turn.py:26`, wrap_up closure `setup.py:79-83`→`turn.py:24`; handler `calls += 1` at start (`stats_handler.py:92`), terminal `_finalize` accrues duration+usage only.
- **If propagation fails in the real subgraph during implementation:** stop and report the observed events and the proposed minimum scope (e.g. a subgraph-invocation-level config) to A — do not widen scope silently.

## 3. Binding-removal check — scoped to 07, 07b, 13 only
For TC-O6-07, 07b, and 13 only: with the `setup.py` metadata removed or set to a wrong key, the test **must fail** (recorder finds no `scope="analyst"`/correct `agent_key`; handler attributes nothing). This is a dev-time property, not a committed passing test. **TC-O6-11 is excluded** from this check.

## 4. TC-O6-07 — one Analyst, ordinary + wrap_up (values FIXED by A)
- **Fixture:** Market selected; offline vendor stubs; deterministic usage; `max_tool_rounds=1` (forces wrap_up); injected clock; recorder+handler via constructor.
- **Events:** ordinary `100/20` @ **1.0 s**; wrap_up `80/15` @ **0.5 s**.
- **Expected:** both callbacks carry `scope="analyst"`, `agent_key=="market"`; row = **2 calls, 180 input, 35 output, 1.5 s**.

## 5. TC-O6-07b — two overlapping Analysts, own fixture (values FIXED by A)
- **Fixture (its own, separate from 07):** Market + News; offline stubs; deterministic usage; shared `threading.Barrier(2, timeout=…)` in `_generate` for tool-bound calls; recorder+handler via constructor.
- **Fixed values:**
  - Market: ordinary `100/20` @1.0 s, wrap_up `80/15` @0.5 s → Market total **2 calls, 180/35, 1.5 s**.
  - News: ordinary `80/15` @ **0.8 s**, wrap_up `40/5` @ **0.4 s** → News total **2 calls, 120/20, 1.2 s**.
- **Overlap:** the two **ordinary** calls must both reach the barrier and be released (else `BrokenBarrierError`/timeout fails); thread names recorded.
- **Out-of-order control:** at least one invocation is forced to complete **out of start order** (e.g. release ordering so a later-start call terminally ends before an earlier-start call), proving results don't depend on completion order.
- **Pairing by `run_id`:** each start's `(run_id, agent_key)` is matched to its **terminal event by `run_id`**; usage/duration are read at that terminal — never from shared state.
- **Independent scripted identities to detect swapped labels:** each Analyst's model carries a distinct identity marker/usage signature; assert every invocation's usage lands only in its own `agent_key` row.
- **Expected:** exact per-row totals above and **zero cross-attribution**.
- **Note:** the PR #6 §5 display table belongs to **TC-O6-12** (C), not to this test.

## 6. TC-O6-11 — out-of-scope exclusion (no binding-removal check)
- **Fixture:** full graph, default analysts; a non-Analyst node makes a model call; recorder+handler via constructor.
- **Occurrence proof:** recorder **positively observes** the out-of-scope start/end (that node's `langgraph_node`/`checkpoint_ns`) — the call **actually happened**.
- **Not Analyst:** assert `scope != "analyst"` for that invocation (a non-Analyst scope value such as a node-level label is allowed).
- **Unchanged:** snapshots before vs after that invocation → named rows **deep-equal unchanged**, `unattributed_calls` **unchanged**.

## 7. TC-O6-13 — wrap_up attributed exactly once (values FIXED by A)
- **Fixture:** one analyst; low `max_tool_rounds` (forces `setup.py:83` wrap_up); deterministic usage; injected clock; **only the observing callback** (per §1b), which forwards each real event to the handler once and takes the three snapshots around handler processing.
- **Events:** ordinary `100/20` @ **1.0 s**; wrap_up `50/10` @ **0.5 s**. Expected total: **2 calls, 150/30, 1.5 s**.
- **Independent identification:** the observing callback identifies the wrap_up start (post-tool / `WRAP_UP`-history) and its `run_id` (distinct from the ordinary call's).
- **Three snapshots** of `get_agent_stats()` for that `agent_key`, around handler processing:
  - **S0 — immediately before the handler processes the wrap_up start.**
  - **S1 — immediately after the handler processes the wrap_up start.**
  - **S2 — immediately after the handler processes the wrap_up terminal** (matched by `run_id`).
- **Assertions:** **S1 − S0:** `calls +1`, tokens/duration **0 delta**. **S2 − S1:** `calls +0`; **exact** input `+50`, output `+10`, duration `+0.5 s`. **Final totals:** row = ordinary + wrap_up = **2 calls, 150/30, 1.5 s** (a double-accrual would show `calls == 3` or inflated totals).

## 8. Verification & evidence
```
.venv/bin/python -m pytest -q test/offline/test_o6_analyst_subgraph.py
.venv/bin/python -m pytest -q test/offline/test_o6_analyst_subgraph.py -v
.venv/bin/python -m pytest -q                       # default regression suite
.venv/bin/python -m pytest --collect-only -q        # new nodes collected
.venv/bin/python -m ruff check test/offline/test_o6_analyst_subgraph.py tradingagents/graph/setup.py
```
**Evidence for C handoff:** `(run_id, scope, agent_key)` rows (ordinary/wrap_up/out-of-scope); 07b per-row totals + zero cross-attribution; 11 occurrence+unchanged proof; 13 S0/S1/S2 deltas + final totals; collect-only; Ruff on both changed files; offline guard (`test/offline/conftest.py` autouse `_no_network`).

## 9. Method attribution and evidence provenance
- **C supplied a local handoff:** the first failing assertions for TC-O6-12/14 and the relevant three-file diff were provided locally to F. **F has not rerun the tests**; C's results remain C-reported (not independently reproduced by F in this stage).
- Earlier simplified-graph probe = supporting evidence only, separate from real-subgraph verification.
