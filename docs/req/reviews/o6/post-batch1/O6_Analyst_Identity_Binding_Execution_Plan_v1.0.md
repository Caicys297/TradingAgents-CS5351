# O6 Analyst Identity Binding — OpenCode Execution Plan v1.0

**Status: PENDING A's pre-code approval.**
**Historical inspection baseline:** `808df04` (`808df04f320d95c1ab4ef5a6e88149335cdeff41`).
**Approved implementation starting point:** `main@d36a677` (`d36a677d4738efd365b6bbcf6f69f993acf8fd3c`).
**Actual implementation branch HEAD: MUST be recorded before the first code edit** in the implementation PR.
**A's decision reference:** PR #6 https://github.com/Caicys297/TradingAgents-CS5351/pull/6#issuecomment-6977306501.

## 1. Scope — F-owned, one independent PR (exactly two files)
| File | Change | Owner |
|---|---|---|
| `tradingagents/graph/setup.py` | node-level `metadata={"scope":"analyst","agent_key":spec.key}` at the analyst boundary | **F** |
| `test/offline/test_o6_analyst_subgraph.py` | TC-O6-07/07b/11/13 + **local** helpers | **F** |

**Out of scope:** `cli/run.py`, `cli/display.py` (C); TC-O6-12/14, W-15a/b; edits to `tests/test_graph_end_to_end.py`.

## 2. Steps
1. **Record the actual implementation branch HEAD** in the PR **before the first code edit**.
2. Apply the `setup.py` metadata binding from the current run's validated `spec.key` (candidate: one `add_node(..., metadata=…)` at `setup.py:144-146`).
3. Add **local** helpers in the new file: forwarding client (single constructor registration path), recorder, deterministic-usage model. Registration per test-plan §1: for TC-O6-07/07b/11 register recorder+handler **once each via constructor** and pass the **validated keys** to the handler; for TC-O6-13 register **only the observing callback** (forwards each event to the handler once and takes the S0/S1/S2 snapshots).
4. Implement 07/07b/11/13 per the Test Plan v1.0:
   - 07: Market 100/20 @1.0 s + 80/15 @0.5 s → 2 calls, 180/35, 1.5 s.
   - 07b: own fixture; Market as 07; News 80/15 @0.8 s + 40/5 @0.4 s → 2 calls, 120/20, 1.2 s; barrier overlap of the two ordinary calls; at least one out-of-order completion; `run_id` pairing; independent identities; zero cross-attribution.
   - 11: positive occurrence of the out-of-scope call; `scope != "analyst"`; named rows + `unattributed_calls` unchanged.
   - 13: 100/20 @1.0 s + 50/10 @0.5 s → 2 calls, 150/30, 1.5 s; plus the S0/S1/S2 snapshot assertions (+1 calls at start; +0 calls and exact +50/+10/+0.5 s at terminal).
   - Binding-removal check applies to **07, 07b, 13 only**.
5. Do **not** modify the handler, `run.py`, or `display.py`.

## 3. Acceptance
- 07/07b/13 pass **only** when graph config delivers identity (verify by toggling the binding off during dev — must fail; not committed).
- 11 positively proves occurrence and exclusion (no binding-removal dependence).
- `--collect-only` lists the new nodes; **Ruff clean on both changed files**; **default regression** unaffected.
- If real-subgraph propagation fails: **stop and report** observed events + proposed minimum scope to A.

## 4. Handoff to C
Provide the actual implementation branch HEAD, the binding commit SHA, and captured evidence (07b per-row totals + zero cross-attribution; 11 occurrence+unchanged; 13 S0/S1/S2 deltas). C then reruns TC-O6-12/14 and W-15a/b, and performs **graph-config-only CLI validation**, after `run.py` passes the validated keys and `display.py` renders the rows and the two disclosures (TC-O6-12's §5 display table).

## 5. Data-use constraint
Use C's diff/output only as actually supplied. **C supplied a local handoff**: the first failing assertions for TC-O6-12/14 and the relevant three-file diff. **F has not rerun the tests.** No GitHub-side results are assumed.
