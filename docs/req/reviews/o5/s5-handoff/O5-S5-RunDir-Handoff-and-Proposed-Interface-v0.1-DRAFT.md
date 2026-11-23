# O5 S5 — `run_dir` handoff: C's answer and E's proposed interface (DRAFT)

**Status: DRAFT — design proposal for C's confirmation. No implementation.** This records C's
answer on PR #23 and the exact interface E proposes to consume, so C can pick the mechanism. No
production code, tests, or CLI change is made by this document.

## C's answer (recorded, verbatim source)

From `EloimEssiam` on PR #23, comment `7061542739`, `2026-11-21T10:54:14Z`,
https://github.com/Caicys297/TradingAgents-CS5351/pull/23#issuecomment-7061542739, verified against
`main@e00d5cafd33869f42960c13bc297f9bf42634760`:

- `RunContext` is currently a **local variable of `run_analysis`**, created after the directory is
  reserved and before the graph is constructed. There is **no O5-facing accessor**, so there is also
  no "returns None outside a CLI run" convention today.
- A normal or exceptional exit **does not delete** the reserved directory; it persists for artifacts
  and the O2 manifest.
- **Ownership:** C owns the shared CLI-side context passing and lifecycle wiring; **E owns O5
  consumption and evidence writing.** C asks E to confirm the specific S5 consumer, call site, and
  whether parallel tasks are involved, so C can choose **explicit parameter passing vs run-scoped
  binding**, guaranteeing no active context leaks after normal, exceptional, or interrupted exit.
  A callback is only a candidate; not implemented.
- The S5 interface handoff **does not block S6**.

## Requirement facts this must satisfy

From `docs/req/requirements.yaml` → `development_contract.o5` (current `main`):

- `evidence_path`: **"same O2 run directory/o5_evidence.jsonl, when a CLI run context exists."**
- `sink_failure`: **"log SINK_FAILED and continue serving the honest result; do not claim persisted
  evidence."**
- The adapter already has a `ContextVar` sink (`_o5_evidence_sink`, default `None`) and emits
  `{"variant","action","trigger","disposition","rules_version","occurred_at", ...fields}` dicts via
  `sink.emit(event)`. In production the sink is **never set**, so nothing is currently persisted.

> Note: `requirements.yaml` has **no `I5b` identifier** today. The S5 invariants referenced as
> "I5b" are not yet enumerated in the registry; that gap is flagged to A/F below.

## E's proposed consumer (needs C's OK)

- **Consumer function:** a private O5 writer `o5_evidence_run(run_dir)` that sets
  `_o5_evidence_sink` to an object whose `.emit(event)` appends one JSON line to
  `<run_dir>/o5_evidence.jsonl`, and clears the sink on exit.
- **Call site (verified against `cli/run.py` on `main@ff39cc3`):** `run_context` is reserved at
  `cli/run.py:319` and the graph is built at `:324`; the analysis is driven by
  `graph.stream_run(graph.checkpoint_input(init_agent_state), **args)` inside the `try:` at `:466`.
  The sink must be set **after** `:319` and **before** the `stream_run` loop, and cleared in a
  `finally` that wraps the stream (the same `try/finally` that tears down the checkpointer). E's
  writer should therefore scope exactly the `stream_run` call:
  `with o5_evidence_run(run_context.run_dir): for ... in graph.stream_run(...)`.
- **Parallel tasks:** LangGraph may schedule Analyst nodes concurrently **after** `stream_run`
  starts, so a `ContextVar` set immediately before `stream_run` is inherited by those tasks. The
  risk is only if news tools run on a thread pool that does not copy context; E will confirm from
  the tool wrappers. If so, C's run-scoped binding is the safer mechanism.
- **Outside a CLI run:** `o5_evidence_run` is only used by the CLI, so the sink stays `None` and
  `_emit_o5_evidence` is a no-op — matching "when a CLI run context exists." No public API change.

## Decision requested from C

1. Pass `run_context.run_dir` **explicitly** into `run_analysis`'s graph call (C wires it), with E
   providing `o5_evidence_run(run_dir)`; **or**
2. C exposes a **run-scoped binding** (e.g. `current_run_context()` returning `RunContext | None`,
   set/cleared in C's `finally`) and E's writer reads it.

Prefers (1) because it needs no new public accessor and keeps `RunContext` private; E only needs the
`Path`. Pending C's choice and A/F sign-off, **no code is written.**

## File scope E would touch once approved

- `tradingagents/dataflows/vendors/yahoo/news.py` — the private sink setter only
  (`o5_evidence_run(run_dir)` and its `.emit` writer). No public signature change.
- A test under `test/offline/` for the sink write + clear on normal/exception/interrupted exit.
- **No** change to `cli/run.py` (C-owned), the selector, or S6 files.

## Blockers before implementation

1. C must confirm mechanism (1) or (2) and the task-spawn point for parallel Analysts.
2. A/F must approve this file scope and the exact `o5_evidence.jsonl` record schema.
3. The registry lacks an `I5b` definition; the S5 invariants must be enumerated before tests are
   written.
