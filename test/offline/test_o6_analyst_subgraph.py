"""O6 Analyst identity binding — real-subgraph offline tests (TC-O6-07/07b/11/13).

These tests run the real Analyst subgraphs through ``TradingAgentsGraph`` with a
controlled model and offline vendor stubs, and verify that the Analyst identity
(``scope="analyst"`` and the selected ``spec.key``) reaches the model-start
callbacks and is attributed correctly by ``StatsCallbackHandler``.

The harness never injects identity metadata itself: it reads ``scope``/
``agent_key`` only from what the production Analyst-subgraph boundary in
``tradingagents/graph/setup.py`` puts on the callback. A shared scripted model
picks its per-analyst usage from ``run_manager.metadata["agent_key"]`` (the same
metadata the callback receives), so two Analysts can carry distinct usage with a
single model instance.

Determinism: the ``ClockDriver`` is registered *before* the statistics handler.
It records each event and, on start/terminal events, sets the monotonic clock to
that invocation's scheduled tick. Callbacks fire in registration order, so the
handler reads the clock after the driver updates it — durations are exact.
"""

import copy
import threading

import pandas as pd
import pytest
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

from cli.stats_handler import StatsCallbackHandler
from tradingagents.agents import context
from tradingagents.agents.analysts import sentiment_analyst
from tradingagents.dataflows import router
from tradingagents.dataflows.vendors.yahoo import market as yahoo_market, snapshot
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph import trading_graph
from tradingagents.graph.analyst_execution import build_analyst_execution_plan

TRADE_DATE = "2026-01-09"
TEXT = "Report.\n\n**Rating**: Overweight\n\nFINAL TRANSACTION PROPOSAL: **BUY**"

ARGS = {
    "symbol": "NVDA", "ticker": "NVDA", "curr_date": TRADE_DATE,
    "start_date": "2026-01-02", "end_date": TRADE_DATE, "indicator": "rsi",
    "topic": "Fed rate cut", "freq": "quarterly",
}

# Per-analyst usage & duration schedules (FIXED by A).
# Each analyst does an ordinary (tool) call then a wrap_up call.
SCHEDULE = {
    "market": [(100, 20), (80, 15)],   # ordinary, wrap_up  -> 180 / 35
    "news": [(80, 15), (40, 5)],       # ordinary, wrap_up  -> 120 / 20
}


class FakeClock:
    """Deterministic monotonic clock advanced by the test."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def set(self, value: float) -> None:
        self._now = value


class Usage:
    __slots__ = ("input_tokens", "output_tokens")

    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class ClockDriver(BaseCallbackHandler):
    """Records events and drives the clock around each invocation.

    Registered *before* the statistics handler. The test supplies, per
    invocation (in start order), a ``(start_tick, end_tick)`` pair. On start we
    set the clock to ``start_tick``; on terminal we set it to ``end_tick``.
    """

    def __init__(self, clock: FakeClock) -> None:
        super().__init__()
        self.clock = clock
        self.lock = threading.Lock()
        self.events: list[dict] = []
        self._schedule: dict[str, tuple[float, float]] = {}
        self._ticks: list[tuple[float, float]] = []
        # Optional order-independent schedule keyed by (agent_key, node) so exact
        # durations do not depend on the nondeterministic start order of two
        # concurrent analysts: {(agent_key, node): (start_tick, end_tick)}.
        self.identity_schedule: dict[tuple, tuple[float, float]] = {}
        # Optional observation hook: called with (phase, meta) before/after the
        # handler processes each model-start. Phase is "before" or "after". This
        # lets a test snapshot statistics around a specific call regardless of
        # whether identity binding is present.
        self.observer = None  # callable(phase, meta) | None

        # Optional out-of-order latch driven by the *actual model-start callback
        # order* (not lock acquisition): for the two ordinary analyst calls
        # (node == "agent"), the one whose on_chat_model_start is recorded FIRST
        # must block until the one recorded SECOND has passed its terminal
        # callback (on_llm_end). This makes the later starter complete first.
        self.order_latch = None  # dict | None; enabled by the test
        self._ordinary_start_order: list[str] = []   # fixture origins in start order
        self._ordinary_rid: dict[str, str] = {}      # origin -> run_id
        self._later_terminal = threading.Event()

    def program(self, ticks):
        self._ticks = list(ticks)

    def wait_until_later_ordinary_terminates(self, origin: str) -> None:
        """Block if ``origin`` was the earlier ordinary starter, until the later
        ordinary starter's terminal callback has been recorded."""
        if self.order_latch is None:
            return
        # Wait (bounded) until both ordinary starts have been recorded by the
        # callback, so the start order reflects actual model-start callbacks.
        import time as _time
        end_poll = _time.monotonic() + 10
        while True:
            with self.lock:
                if len(self._ordinary_start_order) >= 2:
                    first = self._ordinary_start_order[0]
                    break
            if _time.monotonic() > end_poll:
                raise AssertionError("both ordinary starts not observed")
            _time.sleep(0.001)
        if origin == first and not self._later_terminal.wait(timeout=10):
            raise AssertionError("later ordinary starter did not terminate in time")
        # The later starter returns immediately (it will terminate first).

    def _rec(self, kind, **kw):
        meta = dict(kw.get("metadata") or {})
        with self.lock:
            self.events.append({
                "kind": kind,
                "run_id": str(kw.get("run_id")),
                "scope": meta.get("scope"),
                "agent_key": meta.get("agent_key"),
                "node": meta.get("langgraph_node"),
                "ns": meta.get("langgraph_checkpoint_ns") or meta.get("checkpoint_ns"),
            })

    def on_chat_model_start(self, serialized, messages, **kw):
        rid = str(kw.get("run_id"))
        meta = dict(kw.get("metadata") or {})
        is_analyst = meta.get("scope") == "analyst"
        if self.observer is not None:
            self.observer("before", meta)
        with self.lock:
            ns = meta.get("langgraph_checkpoint_ns") or meta.get("checkpoint_ns") or ""
            origin = ns.split(":")[0]
            key = (origin, meta.get("langgraph_node"))
            if is_analyst and key in self.identity_schedule:
                start, end = self.identity_schedule[key]
            elif is_analyst:
                start, end = self._ticks.pop(0) if self._ticks else (0.0, 0.0)
            else:
                start = end = self.clock()
            self._schedule[rid] = (start, end)
            # Record ordinary (node == "agent") start order from the actual
            # callback, keyed by fixture ORIGIN (not agent_key), not from any
            # later lock acquisition.
            if (self.order_latch is not None and meta.get("langgraph_node") == "agent"
                    and origin and origin not in self._ordinary_start_order):
                self._ordinary_start_order.append(origin)
                self._ordinary_rid[origin] = rid
        self.clock.set(start)
        self._rec("start", **kw)
        if self.observer is not None:
            self.observer("after", meta)

    def on_llm_end(self, response, **kw):
        rid = str(kw.get("run_id"))
        with self.lock:
            _, end = self._schedule.get(rid, (self.clock(), self.clock()))
            release_later = False
            if self.order_latch is not None and len(self._ordinary_start_order) >= 2:
                later_origin = self._ordinary_start_order[1]
                if rid == self._ordinary_rid.get(later_origin):
                    release_later = True
        self.clock.set(end)
        self._rec("end", **kw)
        # Release the earlier ordinary starter only AFTER the later starter's
        # terminal callback has been recorded.
        if release_later:
            self._later_terminal.set()

    def on_llm_error(self, error, **kw):
        rid = str(kw.get("run_id"))
        with self.lock:
            _, end = self._schedule.get(rid, (self.clock(), self.clock()))
        self.clock.set(end)
        self._rec("error", **kw)

    def starts(self):
        return [e for e in self.events if e["kind"] == "start"]

    def analyst_starts(self):
        return [e for e in self.events if e["kind"] == "start" and e["scope"] == "analyst"]


class ScriptedModel(BaseChatModel):
    """One model shared by all Analysts; per-analyst usage from run metadata.

    ``tool_calls_per_analyst`` controls how many tool rounds an analyst emits
    before answering (wrap_up is forced by ``max_tool_rounds``). ``barrier`` (when
    set) synchronises the first tool-bound call of each analyst so overlap is
    observable; ``release_order`` can force an out-of-start-order completion.
    """

    structured: bool = False
    tools: tuple = ()
    calls: list = Field(default_factory=list)   # shared across bound copies
    threads: set = Field(default_factory=set)
    barrier: object = None
    per_key_indices: dict = Field(default_factory=dict)  # agent_key -> next usage idx
    overlap: list = Field(default_factory=list)          # observed (key, thread)
    completion_order: list = Field(default_factory=list)  # agent_keys as they finish tools
    trace: list = Field(default_factory=list)  # diagnostic: (kind, n_tools, has_run_manager)
    schedule: dict = Field(default_factory=dict)  # optional per-key usage override
    identity: dict = Field(default_factory=dict)  # agent_key -> fixture identity marker
    origin_usage: dict = Field(default_factory=dict)  # origin -> {phase: (in, out)}
    driver: object = None  # ClockDriver (owns the out-of-order latch)
    overlap_lock: object = Field(default_factory=threading.Lock)

    @property
    def _llm_type(self) -> str:
        return "o6-subgraph"

    def bind_tools(self, tools, **kwargs):
        # Production-like: return a RunnableBinding (``self.bind``) rather than a
        # ``model_copy``. ``_ChatModelBinding.invoke`` merges the caller/node
        # config into the bound call, so node-level metadata reaches the model
        # callback exactly as it does for a real provider client.
        return self.bind(tools=tuple(tools), **kwargs)

    def with_structured_output(self, schema, **kwargs):
        raise NotImplementedError

    def _usage_for_origin(self, origin: str, key: str, kind: str) -> Usage:
        """Select usage from the fixture identity (origin) and call phase; fall
        back to a per-agent_key schedule when no origin fixture is set."""
        if self.origin_usage:
            pair = self.origin_usage.get(origin, {}).get(kind, (0, 0))
            return Usage(*pair)
        idx = 0 if kind == "ordinary" else 1
        schedule = self.schedule or SCHEDULE
        pair = schedule.get(key, [(0, 0), (0, 0)])
        inp, out = pair[min(idx, len(pair) - 1)]
        return Usage(inp, out)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        md = dict(getattr(run_manager, "metadata", None) or {}) if run_manager else {}
        key = md.get("agent_key") or "unknown"
        # Fixture ORIGIN, independent of the callback's agent_key: the analyst
        # subgraph node name is the first segment of the checkpoint namespace
        # (e.g. "Market Analyst"/"News Analyst"). This is what the fixture keys on.
        ns = md.get("langgraph_checkpoint_ns") or md.get("checkpoint_ns") or ""
        origin = ns.split(":")[0] or "unknown"
        tools = tuple(kwargs.get("tools") or self.tools)
        tool_bound = bool(tools)
        kind = "ordinary" if tool_bound else "wrap_up"
        self.calls.append(1)
        self.trace.append((kind, len(tools), origin, key))
        # Latch is keyed by fixture origin, not by agent_key.
        latch_key = origin

        if tool_bound:
            self.threads.add(threading.current_thread().name)
            if self.barrier is not None:
                with self.overlap_lock:
                    self.overlap.append((latch_key, threading.current_thread().name))
                try:
                    self.barrier.wait(timeout=5)
                except threading.BrokenBarrierError as exc:
                    raise AssertionError("overlap barrier timed out") from exc
                # Out-of-order completion is enforced by the ClockDriver, which
                # knows the ACTUAL model-start callback order and releases the
                # earlier ordinary starter only after the later starter's terminal
                # callback has been recorded. No sleeps; bounded by its timeout.
                if self.driver is not None:
                    self.driver.wait_until_later_ordinary_terminates(latch_key)
            # Record ordinary-call completion origin (used for out-of-order check).
            with self.overlap_lock:
                self.completion_order.append(latch_key)
            if not isinstance(messages[-1], ToolMessage):
                calls = [{"name": t.name, "id": f"call_{i}",
                          "args": {k: v for k, v in ARGS.items()
                                   if k in t.tool_call_schema.model_json_schema()["properties"]}}
                         for i, t in enumerate(tools)]
                u = self._usage_for_origin(origin, key, kind)
                return ChatResult(generations=[ChatGeneration(
                    message=AIMessage(
                        content="", tool_calls=calls,
                        usage_metadata={
                            "input_tokens": u.input_tokens,
                            "output_tokens": u.output_tokens,
                            "total_tokens": u.input_tokens + u.output_tokens,
                        },
                    ))])

        usage = self._usage_for_origin(origin, key, kind)
        msg = AIMessage(
            content=TEXT,
            usage_metadata={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.input_tokens + usage.output_tokens,
            },
        )
        return ChatResult(generations=[ChatGeneration(message=msg)])


class ForwardingClient:
    """Forwards constructor callbacks onto the model (single registration path).

    Production passes ``callbacks`` into the model's constructor
    (``create_tier_client(..., callbacks=...)`` -> ``ChatXxx(callbacks=...)``).
    We mirror that by baking the callbacks onto the model instance rather than
    using ``with_config``: a ``with_config`` callback is dropped across the
    runnable binding that ``bind_tools`` returns, whereas a constructor-level
    callback survives into the bound (tool-calling) invocation.
    """

    def __init__(self, model, callbacks):
        self.model = model
        self.callbacks = callbacks or []

    def get_llm(self):
        if not self.callbacks:
            return self.model
        return self.model.model_copy(update={"callbacks": list(self.callbacks)})


@pytest.fixture
def offline(monkeypatch, tmp_path):
    """Every vendor answers offline; returns the set of router methods called."""
    called: set[str] = set()
    for method, vendors in router.VENDOR_METHODS.items():
        for vendor in vendors:
            monkeypatch.setitem(vendors, vendor,
                                lambda *a, _m=method, **k: called.add(_m) or f"{_m} data")
    prices = pd.DataFrame({
        "Date": pd.bdate_range(end=TRADE_DATE, periods=60),
        "Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.5, "Volume": 1_000_000,
    })
    monkeypatch.setattr(snapshot, "load_ohlcv",
                        lambda *a, **k: called.add("ohlcv") or prices.copy())
    monkeypatch.setattr(sentiment_analyst, "fetch_stocktwits_messages", lambda *a, **k: "no posts")
    monkeypatch.setattr(sentiment_analyst, "fetch_reddit_posts", lambda *a, **k: "no posts")
    monkeypatch.setattr(yahoo_market.yf, "Ticker",
                        lambda s: type("T", (), {"info": {"longName": "NVIDIA"}})())
    context._identity.cache_clear()
    return called


def _graph(tmp_path, monkeypatch, model, callbacks=None, selected=("market",), **config):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg.update(results_dir=str(tmp_path / "results"), data_cache_dir=str(tmp_path / "cache"),
               memory_log_path=str(tmp_path / "log.md"), **config)
    monkeypatch.setattr(trading_graph, "create_tier_client",
                        lambda config, tier, **k: ForwardingClient(model, callbacks))
    return trading_graph.TradingAgentsGraph(
        config=cfg, debug=False, selected_analysts=selected, callbacks=callbacks)


def _row(stats, key):
    return stats["analysts"].get(key)


# -- TC-O6-07: one Analyst, ordinary + wrap_up (FR-01, NFR-01) --------------
@pytest.mark.unit
def test_tc_o6_07_market_ordinary_and_wrap_up(tmp_path, monkeypatch, offline):
    plan = build_analyst_execution_plan(["market"])
    keys = {spec.key for spec in plan.specs}
    clock = FakeClock()
    driver = ClockDriver(clock)
    handler = StatsCallbackHandler(selected_analyst_keys=keys, clock=clock)
    # Market: ordinary @0.0-1.0 (1.0 s), wrap_up @1.0-1.5 (0.5 s).
    driver.program([(0.0, 1.0), (1.0, 1.5)])
    model = ScriptedModel()
    graph = _graph(tmp_path, monkeypatch, model, callbacks=[driver, handler],
                   selected=("market",), max_tool_rounds=1)

    graph.propagate("NVDA", TRADE_DATE)

    starts = driver.analyst_starts()
    assert {e["agent_key"] for e in starts} == {"market"}
    assert all(e["scope"] == "analyst" for e in starts)
    assert any(e["node"] == "wrap_up" for e in starts), "wrap_up call not observed"

    row = _row(handler.get_agent_stats(), "market")
    assert row["calls"] == 2
    assert row["input_tokens"] == {"value": 180, "status": "complete"}
    assert row["output_tokens"] == {"value": 35, "status": "complete"}
    assert row["duration"] == pytest.approx(1.5)


# -- TC-O6-07b: two overlapping Analysts, no cross-attribution --------------
# Fixtures are keyed by the Analyst's ORIGIN (the subgraph node name, the first
# segment of the callback's langgraph_checkpoint_ns), independent of agent_key.
# Each fixture carries its own identity marker, expected callback agent_key,
# per-phase usage, and disjoint (start, end) ticks so exact durations do not
# depend on start order.
ORIGIN_MARKET = "Market Analyst"
ORIGIN_NEWS = "News Analyst"
FIXTURE_07B = {
    ORIGIN_MARKET: {
        "expected_key": "market",
        "usage": {"ordinary": (100, 20), "wrap_up": (80, 15)},
        "ticks": {"ordinary": (0.0, 1.0), "wrap_up": (1.0, 1.5)},   # 1.0 s / 0.5 s
    },
    ORIGIN_NEWS: {
        "expected_key": "news",
        "usage": {"ordinary": (80, 15), "wrap_up": (40, 5)},
        "ticks": {"ordinary": (10.0, 10.8), "wrap_up": (10.8, 11.2)},  # 0.8 s / 0.4 s
    },
}


def _event_origin(event):
    """Fixture origin for a callback event: first segment of checkpoint ns."""
    ns = event.get("ns") or ""
    return ns.split(":")[0]


def _run_07b(tmp_path, monkeypatch, offline, swap_graph_keys=False):
    """Run the two-Analyst fixture. When ``swap_graph_keys`` is True, only the
    graph-emitted Market/News agent_key values are swapped (fixtures fixed), to
    prove the normal assertions catch a mislabeled graph."""
    plan = build_analyst_execution_plan(["market", "news"])
    keys = {spec.key for spec in plan.specs}
    clock = FakeClock()
    driver = ClockDriver(clock)
    handler = StatsCallbackHandler(selected_analyst_keys=keys, clock=clock)

    fx = copy.deepcopy(FIXTURE_07B)
    # Deterministic, order-independent durations keyed by (origin, node).
    driver.identity_schedule = {}
    for origin, v in fx.items():
        driver.identity_schedule[(origin, "agent")] = v["ticks"]["ordinary"]
        driver.identity_schedule[(origin, "wrap_up")] = v["ticks"]["wrap_up"]

    # Scripted usage selected from the fixture identity (origin) + call phase.
    origin_usage = {origin: v["usage"] for origin, v in fx.items()}
    model = ScriptedModel(barrier=threading.Barrier(2), origin_usage=origin_usage,
                          driver=driver)
    driver.order_latch = {"enabled": True}

    if swap_graph_keys:
        _swap_graph_agent_keys(monkeypatch)

    graph = _graph(tmp_path, monkeypatch, model, callbacks=[driver, handler],
                   selected=("market", "news"), max_tool_rounds=1)
    graph.propagate("NVDA", TRADE_DATE)
    return handler, driver, model, fx


def _swap_graph_agent_keys(monkeypatch):
    """Swap only the graph-emitted agent_key metadata for the two Analyst nodes,
    leaving the test fixtures and model untouched. This models a production bug
    where the boundary emits the wrong spec.key."""
    import tradingagents.graph.setup as setup_mod

    real = setup_mod.StateGraph
    key_swap = {"market": "news", "news": "market"}

    class _SwappingGraph:
        def __new__(cls, *args, **kwargs):
            inner = real(*args, **kwargs)
            orig_add = inner.add_node

            def add_node(node, action=None, **kw):
                md = kw.get("metadata")
                if md and md.get("scope") == "analyst" and md.get("agent_key") in key_swap:
                    kw["metadata"] = {**md, "agent_key": key_swap[md["agent_key"]]}
                return orig_add(node, action, **kw)

            inner.add_node = add_node  # type: ignore[assignment]
            return inner

    monkeypatch.setattr(setup_mod, "StateGraph", _SwappingGraph)


def _assert_07b_ok(handler, driver, model, fx):
    starts = [e for e in driver.starts() if e["node"] in ("agent", "wrap_up")]
    assert starts, "no analyst-scope starts recorded"
    # Every invocation's callback identity (scope + agent_key) must match the
    # fixture that owns its ORIGIN, and the two invocations pair by run_id.
    by_rid_start = {e["run_id"]: e for e in driver.events if e["kind"] == "start"}
    by_rid_end = {e["run_id"]: e for e in driver.events if e["kind"] == "end"}
    for rid, ev in by_rid_start.items():
        origin = _event_origin(ev)
        if origin not in fx:
            continue  # downstream non-analyst node (checked in TC-O6-11)
        assert ev["scope"] == "analyst", (origin, ev)
        # Attribution check: callback agent_key equals the fixture's expected key
        # for this origin (paired start<->terminal by run_id).
        assert ev["agent_key"] == fx[origin]["expected_key"], (
            f"origin {origin!r} emitted agent_key {ev['agent_key']!r}, "
            f"expected {fx[origin]['expected_key']!r}")
        assert rid in by_rid_end, f"no terminal event paired for run_id {rid}"

    # Overlap: both ordinary calls reached the barrier on distinct threads.
    assert len(model.overlap) >= 2
    assert len({t for _k, t in model.overlap}) >= 2, f"no overlap: {model.overlap}"

    # Out-of-order completion, from recorded callbacks (start vs terminal order).
    ord_starts = [e for e in driver.starts() if e["node"] == "agent"]
    assert len(ord_starts) == 2, ord_starts
    start_order = [_event_origin(e) for e in ord_starts]
    rid_to_origin = {e["run_id"]: _event_origin(e) for e in ord_starts}
    ord_rids = set(rid_to_origin)
    end_order = [rid_to_origin[e["run_id"]] for e in driver.events
                 if e["kind"] == "end" and e["run_id"] in ord_rids]
    assert len(end_order) == 2, end_order
    assert end_order[0] == start_order[1], \
        f"expected later-start first: start={start_order} end={end_order}"
    assert end_order[-1] == start_order[0], \
        f"expected earlier-start last: start={start_order} end={end_order}"

    # Exact per-Analyst results (fixture oracle; labels come from the fixture).
    stats = handler.get_agent_stats()
    m, n = _row(stats, "market"), _row(stats, "news")
    assert m is not None and n is not None, stats["analysts"]
    exp = {
        "market": (2, 180, 35),   # 100/20 + 80/15
        "news": (2, 120, 20),     # 80/15 + 40/5
    }
    assert (m["calls"], m["input_tokens"]["value"], m["output_tokens"]["value"]) == exp["market"]
    assert (n["calls"], n["input_tokens"]["value"], n["output_tokens"]["value"]) == exp["news"]
    assert m["duration"] == pytest.approx(1.5)
    assert n["duration"] == pytest.approx(1.2)
    # Zero cross-attribution.
    total_in = sum(r["input_tokens"]["value"] for r in stats["analysts"].values())
    total_out = sum(r["output_tokens"]["value"] for r in stats["analysts"].values())
    assert total_in == 180 + 120 and total_out == 35 + 20
    # Zero unattributed in-scope calls.
    assert stats["unattributed_calls"] == 0


@pytest.mark.unit
def test_tc_o6_07b_two_analysts_overlap_no_crossover(tmp_path, monkeypatch, offline):
    handler, driver, model, fx = _run_07b(tmp_path, monkeypatch, offline)
    _assert_07b_ok(handler, driver, model, fx)


@pytest.mark.unit
def test_tc_o6_07b_swapped_graph_keys_fail_attribution(tmp_path, monkeypatch, offline):
    """Swapping only the graph-emitted Market/News agent_key (fixtures fixed) must
    make the normal 07b attribution assertion fail."""
    handler, driver, model, fx = _run_07b(tmp_path, monkeypatch, offline,
                                          swap_graph_keys=True)
    with pytest.raises(AssertionError, match="emitted agent_key"):
        _assert_07b_ok(handler, driver, model, fx)


# -- TC-O6-11: out-of-scope exclusion (occurrence + unchanged) --------------
@pytest.mark.unit
def test_tc_o6_11_out_of_scope_call_excluded(tmp_path, monkeypatch, offline):
    plan = build_analyst_execution_plan(["market"])
    keys = {spec.key for spec in plan.specs}
    clock = FakeClock()
    driver = ClockDriver(clock)
    handler = StatsCallbackHandler(selected_analyst_keys=keys, clock=clock)
    model = ScriptedModel()

    # Snapshot statistics immediately before and after the handler processes the
    # FIRST out-of-scope (non-analyst) call. Independent of identity binding: even
    # if in-scope attribution is absent, an out-of-scope call must not create a
    # named row nor touch unattributed_calls.
    oos_seen = {"before": None, "after": None, "n": 0}

    def observer(phase, meta):
        if meta.get("scope") != "analyst":
            if oos_seen["n"] == 0 and phase == "before":
                oos_seen["before"] = copy.deepcopy(handler.get_agent_stats())
            if oos_seen["n"] == 0 and phase == "after":
                oos_seen["after"] = copy.deepcopy(handler.get_agent_stats())
            if phase == "after":
                oos_seen["n"] += 1

    driver.observer = observer
    graph = _graph(tmp_path, monkeypatch, model, callbacks=[driver, handler],
                   selected=("market",), max_tool_rounds=1)

    graph.propagate("NVDA", TRADE_DATE)

    starts = driver.starts()
    # Positively observe a non-Analyst call downstream (e.g. Research Manager).
    oos = [e for e in starts if e["scope"] != "analyst"]
    assert oos, "expected at least one out-of-scope model call"
    # The out-of-scope call is not marked as Analyst.
    assert all(e["agent_key"] in (None,) for e in oos)

    # Before/after the first out-of-scope call: named rows and unattributed are
    # unchanged.
    assert oos_seen["before"] is not None and oos_seen["after"] is not None
    assert oos_seen["after"] == oos_seen["before"], "out-of-scope call changed statistics"
    # And out-of-scope never creates an unattributed entry.
    assert handler.get_agent_stats()["unattributed_calls"] == 0


# -- TC-O6-13: wrap_up attributed exactly once (FR-01, NFR-01) --------------
class _ObservedHandler(BaseCallbackHandler):
    """Observing callback: forwards each real event to the handler once and takes
    S0/S1/S2 snapshots around the handler's processing of the wrap_up start and
    terminal events (paired by run_id)."""

    def __init__(self, handler, clock, nonempty_tool_set, key):
        super().__init__()
        self.handler = handler
        self.clock = clock
        self.nonempty_tool_set = nonempty_tool_set
        self.key = key
        self.rid = None
        self.s0 = self.s1 = self.s2 = None
        self._ticks = []
        self.trace = []

    def program(self, ticks):
        self._ticks = list(ticks)

    def _snap(self):
        row = self.handler.get_agent_stats()["analysts"].get(self.key)
        if row is None:
            return {"calls": 0, "input_tokens": {"value": 0}, "output_tokens": {"value": 0},
                    "duration": 0.0}
        return copy.deepcopy(row)

    def _tick(self):
        return self._ticks.pop(0) if self._ticks else self.clock()

    def on_chat_model_start(self, serialized, messages, **kw):
        rid = str(kw.get("run_id"))
        md = dict(kw.get("metadata") or {})
        self.trace.append(("start", rid, md))
        # Drive the clock for every invocation (start tick), so each call's
        # duration is exact regardless of which one is wrap_up.
        self.clock.set(self._tick())
        is_wrap = md.get("langgraph_node") == "wrap_up"
        if is_wrap:
            self.rid = rid
            self.s0 = self._snap()          # S0: before handler processes start
        self.handler.on_chat_model_start(serialized, messages, **kw)
        if is_wrap:
            self.s1 = self._snap()          # S1: after handler processes start

    def on_llm_end(self, response, **kw):
        rid = str(kw.get("run_id"))
        self.clock.set(self._tick())
        is_wrap = rid == self.rid
        self.handler.on_llm_end(response, **kw)
        if is_wrap:
            self.s2 = self._snap()          # S2: after handler processes terminal

    def on_llm_error(self, error, **kw):
        self.handler.on_llm_error(error, **kw)


@pytest.mark.unit
def test_tc_o6_13_wrap_up_attributed_once(tmp_path, monkeypatch, offline):
    plan = build_analyst_execution_plan(["market"])
    keys = {spec.key for spec in plan.specs}
    clock = FakeClock()
    handler = StatsCallbackHandler(selected_analyst_keys=keys, clock=clock)
    observer = _ObservedHandler(handler, clock, nonempty_tool_set=True, key="market")
    # Ordinary @0.0-1.0 (1.0 s); wrap_up @1.0-1.5 (0.5 s).
    observer.program([0.0, 1.0, 1.0, 1.5])
    model = ScriptedModel(schedule={"market": [(100, 20), (50, 10)]})
    graph = _graph(tmp_path, monkeypatch, model, callbacks=[observer],
                   selected=("market",), max_tool_rounds=1)

    graph.propagate("NVDA", TRADE_DATE)

    assert observer.s0 is not None and observer.s1 is not None and observer.s2 is not None
    # S1 - S0: calls +1, no token/duration change (start counted at start).
    assert observer.s1["calls"] - observer.s0["calls"] == 1
    assert observer.s1["input_tokens"]["value"] == observer.s0["input_tokens"]["value"]
    assert observer.s1["duration"] == pytest.approx(observer.s0["duration"])
    # S2 - S1: calls +0, exact usage/duration increments (50/10, 0.5 s).
    assert observer.s2["calls"] - observer.s1["calls"] == 0
    assert observer.s2["input_tokens"]["value"] - observer.s1["input_tokens"]["value"] == 50
    assert observer.s2["output_tokens"]["value"] - observer.s1["output_tokens"]["value"] == 10
    assert (observer.s2["duration"] - observer.s1["duration"]) == pytest.approx(0.5)
    # Final totals: ordinary + wrap_up = 2 calls, 150/30, 1.5 s.
    final = _row(handler.get_agent_stats(), "market")
    assert final["calls"] == 2
    assert final["input_tokens"] == {"value": 150, "status": "complete"}
    assert final["output_tokens"] == {"value": 30, "status": "complete"}
    assert final["duration"] == pytest.approx(1.5)
