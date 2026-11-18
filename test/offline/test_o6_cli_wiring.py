"""O6 CLI integration: the four approved cases.

TC-O6-12 (CLI disclosure), TC-O6-14 (same-process two-run isolation), W-15a
(ordinary path) and W-15b (new checkpoint path), per the O6 CLI Integration
Execution Plan rev.11a archived on PR #6 and approved by A and F.

Every case drives the production entry ``cli.run.run_analysis``. Only the
interactive selections, the model client, the analyst tool bodies and the
console are replaced; the CLI body, the graph execution config, ``stream_run``,
the analyst subgraph, its ``ToolNode`` and the statistics handler are the
production code.

W-1..W-14 are outside this batch and are not collected here.
"""

import copy
import re
import sys

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from tradingagents.graph.checkpointer import checkpoint_step, get_checkpointer, thread_id

TICKER = "NVDA"
TRADE_DATE = "2026-05-01"
START_DATE = "2026-04-24"

# The deterministic decision the fixture's terminal node files. Its first
# content line parses through ``agents.rating.extract_rating`` as Hold.
FIXTURE_DECISION = (
    "**Rating**: Hold\n\n"
    "The fixture supplies a deterministic decision so the CLI publishes a normal result."
)

W15_STATS = {"llm_calls": 3, "tool_calls": 1, "tokens_in": 280, "tokens_out": 55}
W15_FOOTER = "Agents: 10/10 | LLM: 3 | Tools: 1 | Tokens: 280↑ 55↓ | Reports: 3/5"

DISCLOSURE_DEFERRED = "first structured-call attribution deferred"
DISCLOSURE_ROWS = (
    "named rows include only selected-Analyst calls with verified identity"
)


# ---------------------------------------------------------------------------
# offline stand-ins
# ---------------------------------------------------------------------------


class ScriptedChatModel(BaseChatModel):
    """A chat model answering from a per-Analyst script, with real callback traffic.

    ``_generate`` is the model execution point, so LangChain emits the same
    ``on_chat_model_start`` / ``on_llm_end`` notifications a provider client
    would.

    One instance is shared by every Analyst in the run, so a response cannot be
    chosen by a global counter: the Analysts run concurrently, and whichever
    enters first would consume the other's turn. Each response is chosen instead
    by *who is asking*, read from the prompt the Analyst actually sent (the
    system message carries the ticker under analysis), and each Analyst keeps
    its own call index. ``executions`` records every execution with its Analyst
    label, so the independent count is still real.
    """

    script: dict = {}
    executions: list = []
    # Set on the per-Analyst copy returned by ``bind_tools``; empty on the
    # shared instance, which is only used to build those copies.
    _analyst: str = ""

    @property
    def _llm_type(self):
        return "o6-scripted"

    def bind_tools(self, tools, **kwargs):
        """Return a bound copy that knows which Analyst will be calling.

        Each Analyst binds its own tool set at graph build time, and no two
        Analysts share a set, so the tool names identify the caller without
        anything being injected into the prompt. A bound copy keeps its own
        call index, so concurrent Analysts cannot consume each other's turns.

        A bind that is not an Analyst tool set -- a structured-output schema
        bound by a manager, for instance -- is left unbound: those nodes are not
        scripted by this fixture and must keep the model's default behaviour.
        """
        tools = list(tools)
        names = frozenset(getattr(tool, "name", None) for tool in tools)
        key = next(
            (candidate for candidate, spec in _TOOL_SETS.items() if spec == names),
            None,
        )
        if key is None:
            return super().bind_tools(tools, **kwargs)
        return self.model_copy(update={"_analyst": key})

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        key = self._analyst
        if not key:
            # ``wrap_up`` reaches the model without ``bind_tools``, so the copy
            # that knows its Analyst is not the object called. That prompt is
            # still the Analyst's own and lists the tools it offers, so the
            # Analyst is read from those names -- not from call order.
            key = self._analyst_of_prompt(messages)
        turns = self.script[key]
        index = sum(1 for label in self.executions if label == key)
        self.executions.append(key)
        step = turns[min(index, len(turns) - 1)]
        message = AIMessage(
            content=step["content"],
            tool_calls=step.get("tool_calls", []),
            usage_metadata={
                "input_tokens": step["input_tokens"],
                "output_tokens": step["output_tokens"],
                "total_tokens": step["input_tokens"] + step["output_tokens"],
            },
        )
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _analyst_of_prompt(self, messages) -> str:
        """The Analyst whose own prompt this unbound call carries."""
        text = " ".join(str(getattr(m, "content", m)) for m in (messages or []))
        for key, names in _TOOL_SETS.items():
            if names and all(name in text for name in names):
                return key
        raise AssertionError(
            "a scripted model call carried neither an Analyst binding nor a "
            "prompt listing one Analyst's tools"
        )


def _market_script():
    """Market asks for one tool, then files its report: two model executions."""
    return [
        {
            "content": "",
            "tool_calls": [{"name": "get_stock_data", "args": {"symbol": "NVDA", "start_date": "2026-04-24", "end_date": "2026-05-01"}, "id": "call-1"}],
            "input_tokens": 100,
            "output_tokens": 20,
        },
        {"content": "Market report body.", "input_tokens": 100, "output_tokens": 20},
    ]


def _tool_sets():
    """Each Analyst's bound tool names, read from the production specs."""
    from tradingagents.graph.analyst_execution import ANALYST_NODE_SPECS

    return {
        key: frozenset(tool.name for tool in spec.tools)
        for key, spec in ANALYST_NODE_SPECS.items()
        if spec.tools
    }


_TOOL_SETS = _tool_sets()


def _script(market, news):
    """The per-Analyst scripts for one fixture, keyed by Analyst."""
    return {"market": market, "news": news}


def _news_script(in_tokens=80, out_tokens=15):
    return [
        {"content": "News report body.", "input_tokens": in_tokens, "output_tokens": out_tokens}
    ]


# TC-O6-12's own fixture: Market ordinary 100/20 then wrap_up 80/15, News 80/15.
# Market's second turn is the production ``wrap_up`` turn (one tool round), so
# this fixture is deliberately distinct from W-15's tool fixture.
def _tc12_market_script():
    return [
        {
            "content": "",
            "tool_calls": [{"name": "get_stock_data", "args": {"symbol": "NVDA", "start_date": "2026-04-24", "end_date": "2026-05-01"}, "id": "call-1"}],
            "input_tokens": 100,
            "output_tokens": 20,
        },
        {"content": "Market report body.", "input_tokens": 80, "output_tokens": 15},
    ]


TC12_EXPECTED = {
    "market": {"calls": 2, "input_tokens": 180, "output_tokens": 35},
    "news": {"calls": 1, "input_tokens": 80, "output_tokens": 15},
}
TC12_LABELS = {"market": "Market Analyst", "news": "News Analyst"}


def _offline_tools(monkeypatch):
    """Replace the vendor-facing tool bodies with offline stubs, keeping names.

    ``setup_graph`` builds its own plan from ``ANALYST_NODE_SPECS``, so the tools
    it puts in each analyst's ``ToolNode`` are the production tools. Only their
    bodies are swapped here, so a scripted tool call still runs through a real
    ``ToolNode`` and still emits a real ``on_tool_start``.
    """
    from tradingagents.agents import tools as tools_mod

    def stub(name):
        def func(*args, **kwargs):
            return f"{name} result (offline)"

        return func

    patched = []
    for attr in dir(tools_mod):
        candidate = getattr(tools_mod, attr, None)
        func = getattr(candidate, "func", None)
        if func is None or getattr(candidate, "name", None) is None:
            continue
        if not hasattr(candidate, "name"):
            continue
        monkeypatch.setattr(candidate, "func", stub(candidate.name), raising=False)
        patched.append(candidate.name)
    return patched


def _build_fixture_graph(script, record=None, monkeypatch=None, wrap_up_analysts=()):
    """Return a TradingAgentsGraph whose workflow is the analysts + fixture_final.

    Production is retained for everything these cases measure: ``run_analysis``,
    the graph execution config, ``stream_run``, the analyst subgraph, its
    ``ToolNode`` and the statistics handler. Only the graph composition and the
    provider client are replaced, so a run stops after the analysts rather than
    continuing into the debate teams.

    ``wrap_up_analysts`` caps those analysts at one tool round, so their second
    turn is the production ``wrap_up`` turn rather than an ordinary one.
    """
    max_tool_rounds = 1
    from langgraph.graph import END

    from cli import run as run_mod
    from tradingagents.graph import trading_graph as tg

    if monkeypatch is not None:
        # One model object serves every Analyst, as production's shared client
        # does; it routes by the tools each Analyst binds, so concurrent calls
        # cannot consume each other's scripted turn.
        model = ScriptedChatModel(script=copy.deepcopy(script), executions=[])

        class _Client:
            def __init__(self, *a, **k):
                pass

            def get_llm(self):
                return model

        monkeypatch.setattr(tg, "create_tier_client", lambda *a, **k: _Client())

    if monkeypatch is not None:
        _offline_tools(monkeypatch)
    record = record if record is not None else {}
    record["monkeypatch"] = monkeypatch
    record["wrap_up_analysts"] = tuple(wrap_up_analysts)
    record["workflows"] = []
    record["compiled_with_saver"] = []
    class FixtureGraph(run_mod.TradingAgentsGraph):
        def __init__(self, selected_analysts, config=None, debug=False, callbacks=None):
            # The production initializer runs unchanged; only ``create_tier_client``
            # is swapped (by the caller) so both tiers return the scripted model
            # instead of building a provider client.
            super().__init__(selected_analysts, debug=debug, config=config, callbacks=callbacks)
            record["model"] = self.quick_thinking_llm
            assert isinstance(self.quick_thinking_llm, ScriptedChatModel)
            self.workflow = self._fixture_workflow(list(selected_analysts))
            self.graph = self.workflow.compile()

        def record_decision(self, company_name, trade_date, final_state):
            """The state log needs the debate fields an analysts-only graph lacks.

            Recording the decision is outside these cases, which measure CLI
            statistics and display; it is stubbed so the run can finish.
            """
            return None

        def _fixture_workflow(self, selected):
            """The production ``GraphSetup.setup_graph``, terminated after the analysts.

            ``setup_graph`` is called for real, so the Analyst identity metadata
            on each analyst node -- and therefore on every ordinary and wrap_up
            model call -- is whatever production attaches. Only two things are
            arranged around it, both from this file:

            * the downstream debate/trader/risk/PM factories are replaced with
              no-op nodes, so the run stops after the analysts and the fixture's
              model executions stay the approved count;
            * ``fixture_final`` is appended after them to file the deterministic
              decision, since no production node in this excerpt writes it.

            Re-routing is done by copying the analysts' outgoing edges to
            ``fixture_final``; the analysts' own subgraphs, their ``ToolNode``
            and their node metadata come from production.
            """
            from tradingagents.graph import setup as setup_mod

            for factory_name in (
                "create_bull_researcher",
                "create_bear_researcher",
                "create_research_manager",
                "create_trader",
                "create_aggressive_debator",
                "create_neutral_debator",
                "create_conservative_debator",
                "create_portfolio_manager",
            ):
                monkeypatch_target = record.get("monkeypatch")
                if monkeypatch_target is not None:
                    monkeypatch_target.setattr(
                        setup_mod,
                        factory_name,
                        (lambda llm, _n=factory_name: _noop_node(_n)),
                    )

            # A wrap_up fixture needs one tool round; every other run keeps the
            # production cap. The cap is a construction-time setting shared by
            # all analysts, so it only changes when a wrap_up is required.
            self.graph_setup.max_tool_rounds = (
                max_tool_rounds if record["wrap_up_analysts"] else self.config["max_tool_rounds"]
            )
            workflow = self.graph_setup.setup_graph(selected)

            def fixture_final(state):
                # Test fixture only: no model call, no tool call.
                return {"final_trade_decision": FIXTURE_DECISION}

            workflow.add_node("fixture_final", fixture_final)
            plan = setup_mod.build_analyst_execution_plan(selected)
            analysts = [spec.agent_node for spec in plan.specs]
            for node in analysts:
                workflow.add_edge(node, "fixture_final")
            workflow.add_edge("fixture_final", END)

            real_compile = workflow.compile

            def compile_and_record(*args, **kwargs):
                if kwargs.get("checkpointer") is not None:
                    record["compiled_with_saver"].append(workflow)
                return real_compile(*args, **kwargs)

            workflow.compile = compile_and_record
            record["workflows"].append(workflow)
            return workflow

    return FixtureGraph


def _noop_node(name):
    """A downstream node that does nothing, so the run stops after the analysts.

    It also advances the debate counters to their terminal values, so the
    production conditional routers (`should_continue_debate`,
    `should_continue_risk_analysis`) finish immediately instead of looping.
    """

    def node(state):
        debate = dict(state.get("investment_debate_state") or {})
        debate["count"] = 10_000
        debate["current_response"] = "Research Manager"
        risk = dict(state.get("risk_debate_state") or {})
        risk["count"] = 10_000
        risk["latest_speaker"] = "Portfolio Manager"
        return {"investment_debate_state": debate, "risk_debate_state": risk}

    return node


# ---------------------------------------------------------------------------
# CLI harness
# ---------------------------------------------------------------------------


def _footer_text(run_mod, stats_handler):
    """The footer line the CLI renders for this handler, minus the elapsed time."""
    from cli.display import format_tokens

    buffer = run_mod.message_buffer
    agents_completed = sum(1 for s in buffer.agent_status.values() if s == "completed")
    parts = [f"Agents: {agents_completed}/{len(buffer.agent_status)}"]
    stats = stats_handler.get_stats()
    parts.append(f"LLM: {stats['llm_calls']}")
    parts.append(f"Tools: {stats['tool_calls']}")
    if stats["tokens_in"] > 0 or stats["tokens_out"] > 0:
        parts.append(
            f"Tokens: {format_tokens(stats['tokens_in'])}\u2191 "
            f"{format_tokens(stats['tokens_out'])}\u2193"
        )
    else:
        parts.append("Tokens: --")
    parts.append(
        f"Reports: {buffer.get_completed_reports_count()}/{len(buffer.report_sections)}"
    )
    return " | ".join(parts)


@pytest.fixture
def cli_harness(monkeypatch):
    """Drive the production CLI entry with offline doubles, capturing output."""
    return _harness_fixture(monkeypatch)


def _harness_fixture(monkeypatch):
    from cli import run as run_mod
    from cli.models import AnalystType

    harness = {"displays": [], "printed": [], "handlers": [], "graphs": []}
    base = {
        "ticker": TICKER,
        "analysis_date": TRADE_DATE,
        "asset_type": "stock",
        "research_depth": 1,
        "quick_think_llm": "scripted",
        "deep_think_llm": "scripted",
        "backend_url": None,
        "llm_provider": "openai",
        "output_language": "English",
        "analysts": [AnalystType.MARKET, AnalystType.NEWS],
    }
    harness["base"] = base

    monkeypatch.setattr(run_mod, "get_user_selections", lambda flags=None: dict(harness["selections"]))
    harness["selections"] = dict(base)

    real_update = run_mod.update_display

    def recording_update_display(layout, spinner_text=None, stats_handler=None, start_time=None):
        if stats_handler is not None:
            harness["displays"].append(
                {
                    "stats": dict(stats_handler.get_stats()),
                    "agent_status": dict(run_mod.message_buffer.agent_status),
                    "completed_reports": run_mod.message_buffer.get_completed_reports_count(),
                    "sections_with_content": sorted(
                        name
                        for name, body in run_mod.message_buffer.report_sections.items()
                        if body is not None
                    ),
                    "footer": _footer_text(run_mod, stats_handler),
                }
            )
        return real_update(layout, spinner_text, stats_handler=stats_handler, start_time=start_time)

    monkeypatch.setattr(run_mod, "update_display", recording_update_display)

    class _Console:
        def print(self, *args, **kwargs):
            harness["printed"].append(" ".join(str(a) for a in args))

    monkeypatch.setattr(run_mod, "console", _Console())
    # ``display_agent_summary`` lives in display.py and prints through its own
    # console, so capture that one too.
    import cli.display as display_mod

    monkeypatch.setattr(display_mod, "console", _Console())
    monkeypatch.setattr(run_mod, "_offer_reports", lambda *a, **k: None)
    monkeypatch.setattr(run_mod.typer, "prompt", lambda *a, **k: k.get("default", "Y"))
    # Take the unattended path: no terminal, so the CLI validates the flags it
    # was given instead of prompting. ``get_user_selections`` is still the
    # production callee.
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    # The unattended guard also requires the settings the CLI would otherwise
    # ask for. Provide them so the production validation passes.
    monkeypatch.setenv("TRADINGAGENTS_OUTPUT_LANGUAGE", "English")
    monkeypatch.setenv("TRADINGAGENTS_MAX_DEBATE_ROUNDS", "1")
    monkeypatch.setenv("TRADINGAGENTS_MAX_RISK_ROUNDS", "1")
    monkeypatch.setenv("TRADINGAGENTS_LLM_PROVIDER", "openai")
    monkeypatch.setenv("TRADINGAGENTS_QUICK_THINK_LLM", "scripted")
    # Each run starts from a clean display buffer, as a fresh CLI process would.
    run_mod.message_buffer.init_for_analysis(["market", "news"])
    return harness


RUN_FLAGS = {
    "ticker": TICKER,
    "date": TRADE_DATE,
    "analysts": "market,news",
    "save": False,
    "show": False,
}


def _make_harness(monkeypatch, keys):
    """Build the CLI harness for a run selecting ``keys``."""
    from cli.models import AnalystType

    harness = _harness_fixture(monkeypatch)
    harness["selections"] = dict(harness["base"])
    harness["selections"]["analysts"] = [AnalystType(k) for k in keys]
    return harness


def _last_live_display(harness):
    """The final statistics snapshot the CLI took inside the live view."""
    displays = [d for d in harness["displays"] if d is not None]
    assert displays, "the CLI never rendered statistics"
    return displays[-1]


# ---------------------------------------------------------------------------
# TC-O6-12 — CLI disclosure
# ---------------------------------------------------------------------------


def test_tc_o6_12_cli_disclosure_rows_and_wording(monkeypatch):
    """TC-O6-12: the approved table and both disclosure lines render.

    The analyst identity these rows depend on is attached by production
    (``GraphSetup.setup_graph`` node metadata) and reaches the handler through
    the graph execution config; this case adds nothing to it. The reverse check
    below proves that dependence by removing the binding and expecting failure.
    """
    from cli import display as display_mod, run as run_mod

    captured = {}
    real_summary = display_mod.display_agent_summary

    def spy_summary(handler):
        captured["stats"] = handler.get_agent_stats()
        captured["table"], captured["summary_text"] = _capture_summary_table(handler)
        return real_summary(handler)

    monkeypatch.setattr(run_mod, "display_agent_summary", spy_summary)

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_tc12_market_script(), _news_script()),
        record,
        monkeypatch,
        wrap_up_analysts=("market",),
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, ["market", "news"])
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    rendered = "\n".join(harness["printed"])
    assert DISCLOSURE_DEFERRED in rendered
    assert DISCLOSURE_ROWS in rendered

    # The three approved calls really executed: Market ordinary + wrap_up, News ordinary.
    assert len(record["model"].executions) == 3

    stats = captured["stats"]
    assert stats["unattributed_calls"] == 0

    # Handler named statistics: exactly the approved rows, in both directions.
    assert set(stats["analysts"]) == {"market", "news"}
    for key, expected in TC12_EXPECTED.items():
        row = stats["analysts"][key]
        assert row["calls"] == expected["calls"], key
        assert row["input_tokens"] == {"value": expected["input_tokens"], "status": "complete"}
        assert row["output_tokens"] == {"value": expected["output_tokens"], "status": "complete"}

    # Rendered rows come from the Rich Table the real renderer built, not from
    # a reconstruction of the snapshot.
    table = captured["table"]
    assert table is not None, "display_agent_summary did not build a table"
    assert [c.header for c in table.columns] == [
        "Analyst",
        "Calls",
        "Input tokens",
        "Output tokens",
        "Duration",
    ]
    rendered_rows = _table_rows(table)

    # Order and labels: the two analysts, in plan order, then the unattributed row.
    assert [r[0] for r in rendered_rows] == [
        "Market Analyst",
        "News Analyst",
        "unattributed calls",
    ], "rendered row order"

    for key, expected in (
        ("market", TC12_EXPECTED["market"]),
        ("news", TC12_EXPECTED["news"]),
    ):
        label = TC12_LABELS[key]
        row = next(r for r in rendered_rows if r[0] == label)
        assert row[1] == str(expected["calls"]), f"{label} calls"
        assert row[2] == str(expected["input_tokens"]), f"{label} input tokens"
        assert row[3] == str(expected["output_tokens"]), f"{label} output tokens"
        assert _DURATION_RE.match(row[4]), f"{label} duration format: {row[4]!r}"
        # Duration printed agrees with the same handler's snapshot.
        assert abs(float(row[4][:-1]) - stats["analysts"][key]["duration"]) < 1.0, label

    # The unattributed row prints its label with 0 in the Calls cell.
    unattributed_row = next(r for r in rendered_rows if r[0] == "unattributed calls")
    assert unattributed_row[1] == "0", "unattributed Calls cell"

    # Disclosure lines appear in the same rendered output.
    assert DISCLOSURE_DEFERRED in captured["summary_text"]
    assert DISCLOSURE_ROWS in captured["summary_text"]


_DURATION_RE = re.compile(r"^\d+\.\d s?$".replace(" ", ""))


def _capture_summary_table(handler):
    """Run the real renderer, returning the Rich Table it built and its text."""
    import io

    from rich.console import Console
    from rich.table import Table

    from cli import display as display_mod

    recorded = {}

    class _Recorder(Console):
        def print(self, *args, **kwargs):
            for arg in args:
                if isinstance(arg, Table):
                    recorded["table"] = arg
            return super().print(*args, **kwargs)

    buffer = io.StringIO()
    display_mod.display_agent_summary(
        handler, target_console=_Recorder(file=buffer, width=200, force_terminal=False)
    )
    return recorded.get("table"), buffer.getvalue()


def _table_rows(table):
    """Each printed row as a list of plain strings, in render order.

    Reads the cells Rich stores per column. That attribute is private, so a
    read that does not yield exactly one cell per column for every row raises
    instead of returning a short or empty list that later assertions would
    silently accept.
    """
    if table is None:
        raise AssertionError("no Rich Table was captured from display_agent_summary")

    row_count = len(table.rows)
    if row_count == 0:
        raise AssertionError("the captured table has no rows")

    rows = []
    for index in range(row_count):
        cells = []
        for column in table.columns:
            try:
                cells.append(str(column._cells[index]))
            except (AttributeError, IndexError) as exc:
                raise AssertionError(
                    f"could not read row {index} of column {column.header!r} "
                    f"from the Rich table: {exc}"
                ) from exc
        if len(cells) != len(table.columns):
            raise AssertionError(
                f"row {index} yielded {len(cells)} cells for "
                f"{len(table.columns)} columns"
            )
        rows.append(cells)

    if len(rows) != row_count:
        raise AssertionError(
            f"read {len(rows)} rows but the table holds {row_count}"
        )
    return rows


# ---------------------------------------------------------------------------
# W-15a — ordinary path
# ---------------------------------------------------------------------------


def test_w15a_ordinary_path_statistics_and_footer(monkeypatch):
    """W-15a: the final live refresh carries the fixed totals and footer."""
    from cli import run as run_mod

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, ["market", "news"])
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    snap = _last_live_display(harness)
    assert snap["stats"] == W15_STATS
    assert len(record["model"].executions) == 3
    assert snap["agent_status"] and all(v == "completed" for v in snap["agent_status"].values())
    assert snap["completed_reports"] == 3
    assert {"market_report", "news_report", "final_trade_decision"} <= set(
        snap["sections_with_content"]
    )
    assert snap["footer"] == W15_FOOTER


# ---------------------------------------------------------------------------
# W-15b — new checkpoint path
# ---------------------------------------------------------------------------


def test_w15b_new_checkpoint_persists_state(monkeypatch, tmp_path):
    """W-15b: a new checkpoint is written and readable, with the same totals."""
    from cli import run as run_mod

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, ["market", "news"])
    real_build = run_mod._build_run_config
    signatures = []

    def build_with_tmp_cache(selections, checkpoint_flag):
        config = real_build(selections, checkpoint_flag)
        config["data_cache_dir"] = str(tmp_path / "cache")
        config["results_dir"] = str(tmp_path / "results")
        return config

    real_begin = graph_cls.begin_checkpoint
    observed = {}

    def begin_and_capture(self, company_name, trade_date, asset_type="stock", portfolio=None):
        signatures.append(self._run_signature(asset_type, portfolio))
        return real_begin(self, company_name, trade_date, asset_type, portfolio)

    # The CLI drops a completed run's checkpoint (``clear_checkpoint_on_success``,
    # run.py:354), so the persisted record is read at the boundary immediately
    # before that deletion -- still inside ``begin_checkpoint``/``end_checkpoint``
    # and before the saver connection closes.
    real_clear = graph_cls.clear_checkpoint_on_success

    def read_then_clear(self, company_name, trade_date, asset_type="stock", portfolio=None):
        sig = self._run_signature(asset_type, portfolio)
        cache = self.config["data_cache_dir"]
        tid = thread_id(company_name, str(trade_date), sig)
        observed["step"] = checkpoint_step(cache, company_name, str(trade_date), sig)
        with get_checkpointer(cache, company_name) as saver:
            observed["tuple"] = saver.get_tuple({"configurable": {"thread_id": tid}})
        return real_clear(self, company_name, trade_date, asset_type, portfolio)

    monkeypatch.setattr(graph_cls, "begin_checkpoint", begin_and_capture)
    monkeypatch.setattr(graph_cls, "clear_checkpoint_on_success", read_then_clear)
    monkeypatch.setattr(run_mod, "_build_run_config", build_with_tmp_cache)
    cache_dir = tmp_path / "cache"

    assert checkpoint_step(cache_dir, TICKER, TRADE_DATE, "") is None

    run_mod.run_analysis(checkpoint=True, flags=dict(RUN_FLAGS))

    snap = _last_live_display(harness)
    assert snap["stats"] == W15_STATS
    assert snap["footer"] == W15_FOOTER

    # A checkpoint existed for this run before the CLI cleared it.
    assert observed["step"] is not None and observed["step"] >= 1
    cp = observed["tuple"]
    assert cp is not None
    assert len(signatures) == 1
    assert cp.config["configurable"]["thread_id"] == thread_id(TICKER, TRADE_DATE, signatures[0])
    values = cp.checkpoint["channel_values"]
    assert values.get("market_report")
    assert values.get("news_report")
    assert values.get("final_trade_decision") == FIXTURE_DECISION


# ---------------------------------------------------------------------------
# TC-O6-14 — same-process two-run isolation
# ---------------------------------------------------------------------------


def test_tc_o6_14_two_runs_in_one_process_are_isolated(monkeypatch):
    """TC-O6-14: run 2 sees only its own events and run 1 is untouched."""
    from cli import run as run_mod

    handlers = []
    real_handler = run_mod.StatsCallbackHandler

    def recording_handler(keys=None):
        handler = real_handler(keys)
        handlers.append(handler)
        return handler

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", recording_handler)

    run1_script = _script(_market_script() + _market_script(), _news_script())
    record = {}
    graph_cls = _build_fixture_graph(run1_script, record, monkeypatch)
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, ["market", "news"])
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    run1_snapshot = copy.deepcopy(handlers[-1].get_agent_stats())
    run1_handler = handlers[-1]

    run2_record = {}
    monkeypatch.setattr(
        run_mod,
        "TradingAgentsGraph",
        _build_fixture_graph(
            _script(_market_script(), _news_script(23, 7)), run2_record, monkeypatch
        ),
    )
    from cli.models import AnalystType

    # Mutate in place: the patched get_user_selections closes over this dict.
    harness["selections"]["analysts"] = [AnalystType.NEWS]
    # Run 2 starts from a clean buffer, as a fresh CLI invocation would.
    run_mod.message_buffer.init_for_analysis(["news"])
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    assert handlers[-1] is not run1_handler
    run2 = handlers[-1].get_agent_stats()
    assert set(run2["analysts"]) == {"news"}
    news = run2["analysts"]["news"]
    assert news["calls"] == 1
    assert news["input_tokens"] == {"value": 23, "status": "complete"}
    assert news["output_tokens"] == {"value": 7, "status": "complete"}
    assert run2["unattributed_calls"] == 0
    assert handlers[-1].get_stats()["llm_calls"] == 1

    assert run1_handler.get_agent_stats() == run1_snapshot

