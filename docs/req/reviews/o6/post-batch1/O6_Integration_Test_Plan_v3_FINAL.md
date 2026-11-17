# O6 Integration Test Plan — v3 FINAL (for A's pre-code review)

**Snapshot:** local `origin/main` = `c861d0307238a3b763a35446f7da1245b1e8322a` (PR #11 merge). Read-only; no fetch/pull/switch/edit. Grounding: `cli/run.py` (`run_analysis` @:99, handler @:115, constructor callbacks @:122-128, graph config @:224, Live streaming @:241), `cli/display.py` (`update_display` @:183, stats footer @:352-378 rendering `get_stats()` only; `console` @:23; `display_complete_report` @:382), `tradingagents/graph/{setup,analyst_execution,trading_graph,propagation}.py`, `tradingagents/agents/analysts/turn.py`, `cli/stats_handler.py`, `tests/test_graph_end_to_end.py`, `tests/test_cli_headless.py`, `docs/req/{requirements.yaml,Team-O1-O6-Test-Case-Catalog-v2.0-DRAFT.md}`.

> **Production rendering fact (grounds §2):** today the only statistics region production renders is the footer "Stats" row built in `update_display` from `stats_handler.get_stats()` (`display.py:352-378`), printed through the module-level `console`/`Live`. `get_agent_stats()` is **not** rendered anywhere yet; surfacing per-Analyst rows + disclosures is a **pending C display change** (decision O-5). The plan below distinguishes *what exists now* from *what the acceptance case requires after that change*.

## 1. Restored executable specs — TC-O6-11 and TC-O6-13

### TC-O6-11 — real-subgraph out-of-scope exclusion (O6-FR-01)
- **Production entry point:** `TradingAgentsGraph.propagate(...)` (or `cli.run.run_analysis` for the CLI variant) — a full run in which a **non-Analyst node** (Trader / Research Manager / risk / Portfolio Manager) makes a model call, exercising the real graph at `tradingagents/graph/setup.py` (nodes added at `setup.py:154-162`).
- **Fixture action:** `ScriptedModel` (deterministic usage, §3.2) + the `offline` vendor-stub fixture from `tests/test_graph_end_to_end.py`; select all default analysts so downstream nodes run. A callback recorder (constructor + graph-config, §3.1) plus a handler instance capture every callback.
- **Exact assertions:**
  1. A captured non-Analyst model invocation carries **no** `scope="analyst"` metadata (or a scope label A confirms as out-of-scope per O-4).
  2. **Before vs. after** the out-of-scope call: every named Analyst row is **deep-equal unchanged** in `get_agent_stats()["analysts"]`.
  3. `unattributed_calls` is **unchanged** across that call (out-of-scope contributes to neither).
  4. Downstream (out-of-scope) calls contribute **zero** calls/tokens/duration to any named row.
- **Evidence to capture:** the out-of-scope invocation's `run_id` + metadata keys; `get_agent_stats()` snapshots immediately before and after it; node ID; pass/fail.
- **Blocked by:** O-1 (binding), O-4 (scope-label semantics). If O-4 is undecided, mark assertions 1–3 **provisional** pending the label contract.

### TC-O6-13 — wrap_up attribution, isolated (O6-FR-01, O6-NFR-01)
- **Production entry point:** real Analyst subgraph via `_analyst_graph` wrap_up path — `setup.py:83` closure → `turn.py:20-25` (forced by low `max_tool_rounds`), reached through `TradingAgentsGraph.propagate`.
- **Fixture action:** `_graph(..., max_tool_rounds=1)` with a `ScriptedModel` that calls a tool once then answers; deterministic usage (ordinary vs wrap_up values distinct); injected clock for duration; callback recorder.
- **Exact assertions:**
  1. The **wrap_up** model call carries the **same `agent_key`** as its Analyst (equal to the ordinary call's key).
  2. The invocation is attributed **exactly once**: the Analyst row's `calls` equals expected (ordinary + wrap_up), token totals reflect wrap_up usage added once, duration = sum of both with the injected clock.
  3. No other Analyst row changes.
- **Evidence to capture:** wrap_up invocation `run_id` + `agent_key`; row snapshot before/after the wrap_up terminal; node ID.
- **Blocked by:** O-1/O-2 (binding + shared-file edit).

## 2. Two-run CLI test — observing the production-created handler and capturing each run's rendered statistics

**Constraint (verified):** `run_analysis` creates `stats_handler = StatsCallbackHandler()` as a **local** (`run.py:115`) and **never returns/exposes it**; production must keep creating the handler (no test injection). Therefore the test observes the run through **the production rendering path** — capturing *what production prints* — and reads the handler **non-invasively** by wrapping the render functions, never by constructing it.

- **Requirement (unchanged):** two calls to `cli.run.run_analysis` in one process; Run 1 = `analysts="market,news"`, Run 2 = `analysts="news"` with distinct fixed usage values.
- **Rendered-statistics capture (follows production path):** production renders the footer row via `update_display(..., stats_handler=...)` → `layout["footer"]` → `console`/`Live`. Capture each run's rendered statistics region by **spying on the render functions** — a thin wrapper (monkeypatch) around `cli.display.update_display` (and `display_complete_report` for the final report) that records the `stats_handler` object and/or a rendered `console` snapshot, then delegates to the real function. Use a fresh per-run capture buffer so **run 1 and run 2 outputs are captured separately** (not a shared console).
- **Handler observation (non-invasive, production-created):** the same wrapper records the `stats_handler` argument production passes (the local created at `run.py:115`); after the run, read `get_agent_stats()` and `get_stats()` **from that recorded object**. This preserves production construction while giving a per-run statistics snapshot.
- **Assertions (Run 2):**
  - Run 2 **rendered output** contains only run-2 data: News label present, **no Market label**; News token totals equal run-2 fixed values (not run-1's).
  - Run 2 **statistics snapshot** (`get_agent_stats()` of the run-2 recorded handler): `{"news"}` only, **no `"market"` key**, no totals carried from run 1; legacy `get_stats()` has no residual run-1 counters.
  - **Separate per-run comparison:** run-1 capture/snapshot captured in its own buffer and deep-equal to its pre-run-2 values (unaffected by run 2). Assert the two runs' handlers are **distinct objects**.
- **Corrected cross-reference:** the snapshot-reading mechanism is described **here (§2)**, not §3.4; §3.4 is only about overlap/timing. (v3 §1's "see §3.4" is superseded by this section.)
- **Case ID / delivery batch:** for A (see Decisions #5).

## 3. Naturally delivered callbacks + exact totals through the real CLI config

- **3.1 Real delivery, both modes (no synthesis):** the CLI supplies the handler through the **LLM constructor** (`run.py:122-128` → `create_tier_client(..., callbacks=...)` → `llm.with_config`) **and** **graph config** (`run.py:224` → `get_graph_args(callbacks=...)`). Test scaffolding uses a **callback-forwarding** `create_tier_client` stub (`get_llm()` → `model.with_config({"callbacks": callbacks})`) to replace the current `_Client`/`_graph` stub in `tests/test_graph_end_to_end.py:123-128`, which today discards the callback kwarg. Tests assert callbacks are **naturally delivered** (not synth-injected) under constructor-only, graph-only, and **dual** registration (production = dual).
- **3.2 Exact call/token totals via real model:** deterministic-usage `ScriptedModel` subclass returns fixed `usage_metadata` per invocation; assert exact `calls`, `input_tokens`, `output_tokens`, and completeness **from real delivered callbacks** (e.g. TC-O6-12 table: Market 2/180/35, News 1/80/15). Run 2 uses distinct values for leakage detection.
- **3.3 Replay stays synthetic, in the handler regression (§4):** subgraph/CLI tests assert **one contribution per invocation** on naturally delivered events; they do **not** synthesise replays. Replay/duplicate-start coverage remains the handler-level regression in §4.
- **3.4 Overlap + exact durations:** 07b overlap via `threading.Barrier(n, timeout=…)` inside `_generate` (both Analyst generations must reach it; `BrokenBarrierError` fails the test). **Exact durations** in graph-level tests use an **injected clock** — construct the handler under test with `StatsCallbackHandler(keys, clock=fake)` at the integration level (graph-level tests own their handler), so exact-duration asserts are deterministic and independent of production wall-clock. (CLI-level duration timing hook is decision #6.)

## 4. Handler-level unattributed duplicate-start regression (kept separate)
- **Level:** handler only, `test/offline/test_o6_per_analyst_stats.py` (Batch 1 file).
- **Case:** in-scope (`scope="analyst"`) with missing/invalid `agent_key`, same `run_id`: `start → start (dup) → terminal`.
- **Asserts, before and after terminal:** `unattributed_calls == 1`; named rows deep-equal unchanged; legacy `llm_calls` still counts each start.
- **Ownership:** F designs independently now; the **follow-up test + execution scope go to A for approval**.

## 5. Preserved items
- **Fixed CLI expectations (TC-O6-12):** Select `market,news`. Market's ordinary call reports 100 input and 20 output tokens, its `wrap_up` reports 80 input and 15 output tokens, and News's ordinary call reports 80 input and 15 output tokens.

| Render order | Analyst key | Rendered label | Calls | Input tokens | Output tokens |
|---|---|---|---:|---|---|
| 1 | `market` | Market Analyst | 2 | 180 (`complete`) | 35 (`complete`) |
| 2 | `news` | News Analyst | 1 | 80 (`complete`) | 15 (`complete`) |

  The actual CLI statistics section renders exactly these two Analyst rows in plan order. Compare the rows with the same run's `get_agent_stats()` snapshot, including the call and token totals and completeness. Compare displayed duration to the snapshot using the CLI formatting rule. Assert `unattributed_calls == 0` in the snapshot and `unattributed calls: 0` in the CLI output. Assert that both disclosure strings appear verbatim:

  - `first structured-call attribution deferred`
  - `named rows include only selected-Analyst calls with verified identity`

- **Test IDs:** TC-O6-07 (single-Analyst ordinary+wrap_up), 07b (two overlapping), 11, 12, 13, plus two-run isolation (ID for A) and handler regression. Registry remainder (FR-01 list `01,04,07,07b,08,10,11,12,13`; Batch 1 = 01,04,08,10) → **remaining 07, 07b, 11, 12, 13** + isolation + regression.
- **Offline collection checks:** new tests under `test/offline/` (autouse `_no_network` guard); `.venv/bin/python -m pytest --collect-only -q` lists the new nodes; network-guard probe (`socket.connect`/`getaddrinfo` → `OSError`).
- **Key source:** validated execution-plan `spec.key` values via `build_analyst_execution_plan`.

### Open decisions for A/C (preserved)
1. **Binding point** (`_analyst_graph` wrapper / `add_node(config=…)` / subgraph `config={"metadata":…}`) after langgraph-1.2.22 propagation check — A + C.
2. **Scope-label semantics** (in-scope vs out-of-scope value; TC-O6-11) — A.
3. **Shared-file ownership/order** — C owns `run.py`/`display.py` (pass `selected_analyst_keys` into handler @`run.py:115`; render per-Analyst rows + disclosures); A reviews `setup.py`; order vs O2/O4 — A/C.
4. **TC-O6-07/07b IDs** — approve split — A.
5. **Two-run isolation case** — required under NFR-01; final **ID + delivery batch** — A.
6. **CLI-level duration timing hook** (exact durations) — A.
7. **Handler regression follow-up scope** — A.

I remain in Plan mode — no files edited, nothing fetched/pulled/switched. This v3-FINAL is ready for A's pre-code review.
