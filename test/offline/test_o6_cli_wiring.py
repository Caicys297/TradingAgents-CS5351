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
import io
import re
import sys
from contextlib import contextmanager

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
    # W-12 opt-in: answer a real Bull Researcher prompt instead of treating an
    # unbound, unscripted call as an error. Off by default.
    answer_real_bull: bool = False

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
            if self.answer_real_bull:
                # W-12 opt-in: a real Bull Researcher prompt is answered with an
                # untagged message and no usage, so the call is genuinely
                # unattributed rather than scripted as an Analyst turn.
                text = " ".join(str(getattr(m, "content", m)) for m in (messages or []))
                if "Bull Analyst" in text:
                    self.executions.append("bull")
                    return ChatResult(
                        generations=[ChatGeneration(message=AIMessage(content="Bull case."))]
                    )
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


def _build_fixture_graph(script, record=None, monkeypatch=None, wrap_up_analysts=(), real_bull=False):
    """Return a TradingAgentsGraph whose workflow is the analysts + fixture_final.

    Production is retained for everything these cases measure: ``run_analysis``,
    the graph execution config, ``stream_run``, the analyst subgraph, its
    ``ToolNode`` and the statistics handler. Only the graph composition and the
    provider client are replaced, so a run stops after the analysts rather than
    continuing into the debate teams.

    ``wrap_up_analysts`` caps those analysts at one tool round, so their second
    turn is the production ``wrap_up`` turn rather than an ordinary one.

    ``real_bull`` is default-off and used only by W-12: when set, the Bull
    Researcher is built by production instead of being replaced by a no-op, so
    its real node can be observed. Every existing caller is unaffected.
    """
    max_tool_rounds = 1
    from langgraph.graph import END

    from cli import run as run_mod
    from tradingagents.graph import trading_graph as tg

    if monkeypatch is not None:
        # One model object serves every Analyst, as production's shared client
        # does; it routes by the tools each Analyst binds, so concurrent calls
        # cannot consume each other's scripted turn.
        model = ScriptedChatModel(
            script=copy.deepcopy(script),
            executions=[],
            # W-12 opts in via the record, so the flag is set where the model is
            # built rather than after the graph already holds it.
            answer_real_bull=bool((record or {}).get("answer_real_bull")),
        )

        class _Client:
            def __init__(self, *a, **k):
                # W-5: record what production actually hands the shared client,
                # so a constructor-registered callback cannot hide behind the
                # fixture swallowing its arguments.
                if record is not None:
                    record.setdefault("client_calls", []).append({"args": a, "kwargs": dict(k)})

            def get_llm(self):
                return model

        def _fake_create_tier_client(*a, **k):
            if record is not None:
                record.setdefault("tier_client_calls", []).append({"args": a, "kwargs": dict(k)})
            return _Client(*a, **k)

        monkeypatch.setattr(tg, "create_tier_client", _fake_create_tier_client)

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
                # W-12 opts in to the real Bull node; every other caller keeps
                # the no-op replacement exactly as before.
                if real_bull and factory_name == "create_bull_researcher":
                    continue
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
                # Test fixture only: no model call, no tool call. It records the
                # state it was handed so the test can prove it ran as a fan-in
                # after *both* Analysts, not after whichever finished first.
                record["final_state_seen"] = {
                    "market_report": state.get("market_report"),
                    "news_report": state.get("news_report"),
                }
                record["fixture_final_runs"] = record.get("fixture_final_runs", 0) + 1
                return {"final_trade_decision": FIXTURE_DECISION}

            workflow.add_node("fixture_final", fixture_final)
            plan = setup_mod.build_analyst_execution_plan(selected)
            analysts = [spec.agent_node for spec in plan.specs]
            # One edge from each Analyst; LangGraph runs a node only after every
            # incoming edge has fired, so this is an explicit fan-in.
            for node in analysts:
                workflow.add_edge(node, "fixture_final")
            workflow.add_edge("fixture_final", END)

            # The fan-in shape, recorded from the compiled graph the run uses:
            # every Analyst contributes an edge into ``fixture_final``.
            record["fan_in_sources"] = [
                edge.source
                for edge in workflow.compile().get_graph().edges
                if edge.target == "fixture_final"
            ]

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


def _rendered_footer_text(run_mod, layout):
    """The footer the production ``update_display`` actually wrote into ``layout``.

    ``update_display`` ends by installing a Panel holding the statistics line
    into ``layout["footer"]``. This reads that renderable back -- not a string
    rebuilt from the buffer and the handler -- so the assertion is on what the
    live view would show. The only thing removed is the elapsed-time segment,
    which is wall-clock and therefore not a fixed expectation.
    """
    from rich.console import Console

    buffer = io.StringIO()
    console = Console(
        file=buffer, width=200, color_system=None, force_terminal=False, legacy_windows=False
    )
    console.print(layout["footer"])
    # The footer is a single statistics line inside a bordered Panel. Pull that
    # line out -- the one carrying ``Agents:`` -- and drop only the elapsed-time
    # segment, which is wall-clock and so not a fixed expectation.
    for line in buffer.getvalue().splitlines():
        if "Agents:" not in line:
            continue
        start = line.index("Agents:")
        text = line[start:]
        end = text.rfind("Reports:")
        if end != -1:
            tail = text.find(" | ", end)
            text = text if tail == -1 else text[:tail]
        return text.strip()
    raise AssertionError("the rendered footer carried no statistics line")


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
        # Run production first; the capture is of what it actually installed.
        result = real_update(
            layout, spinner_text, stats_handler=stats_handler, start_time=start_time
        )
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
                    "footer": _rendered_footer_text(run_mod, layout),
                }
            )
        return result

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


@contextmanager
def _live_refresh_recorder(monkeypatch, harness):
    """Record the final in-``Live`` refresh, including the rendered footer.

    ``cli.run`` builds its layout and hands it to ``rich.live.Live``. This wraps
    that ``Live`` to keep a handle on the layout, so the last statistics refresh
    can be read back *after* production rendered it -- ``agent_status``, the
    completed-report count and the actual footer text the run ended on.
    """
    from rich.live import Live

    from cli import run as run_mod

    real_live = Live
    state = {"live": None}

    def recording_live(*args, **kwargs):
        live = real_live(*args, **kwargs)
        state["live"] = live
        return live

    monkeypatch.setattr(run_mod, "Live", recording_live)
    try:
        yield state
    finally:
        # After the run: read what the live view held at its last refresh.
        live = state["live"]
        assert live is not None, "the CLI never opened a live view"
        layout = live.renderable
        footer = _rendered_footer_text(run_mod, layout)
        harness["live_footer"] = footer
        harness["live_rendered"] = _render_layout(layout)


def _render_layout(layout):
    """The whole live layout rendered to plain text, as a terminal would show it."""
    from rich.console import Console

    buffer = io.StringIO()
    console = Console(
        file=buffer, width=200, color_system=None, force_terminal=False, legacy_windows=False
    )
    console.print(layout)
    return buffer.getvalue()


def test_w15a_ordinary_path_statistics_and_footer(monkeypatch):
    """W-15a: the final live refresh carries the fixed totals and rendered footer."""
    from cli import run as run_mod

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, ["market", "news"])
    with _live_refresh_recorder(monkeypatch, harness):
        run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    snap = _last_live_display(harness)
    assert snap["stats"] == W15_STATS
    # The model really executed three times: Market twice, News once.
    assert len(record["model"].executions) == 3
    assert sorted(record["model"].executions) == ["market", "market", "news"]
    assert snap["agent_status"] and all(v == "completed" for v in snap["agent_status"].values())
    assert snap["completed_reports"] == 3
    assert {"market_report", "news_report", "final_trade_decision"} <= set(
        snap["sections_with_content"]
    )

    # The footer is what production wrote into ``layout["footer"]``, then
    # rendered -- not a string rebuilt from the handler and the buffer.
    assert harness["live_footer"] == W15_FOOTER
    # And the same text is present in the layout as a terminal would draw it.
    assert W15_FOOTER in re.sub(r"\s+", " ", harness["live_rendered"])


# ---------------------------------------------------------------------------
# W-15b — new checkpoint path
# ---------------------------------------------------------------------------


def test_w15b_new_checkpoint_persists_state(monkeypatch, tmp_path):
    """W-15b: a new checkpoint is written by the real saver and readable before cleanup."""
    from cli import run as run_mod
    from tradingagents.graph.checkpointer import _db_path

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, ["market", "news"])
    real_build = run_mod._build_run_config
    cache_dir = tmp_path / "cache"
    graph_instances = []

    # W-3: the new-checkpoint path must still build exactly one statistics
    # handler, so the handler count is observed here rather than assumed.
    checkpoint_handlers = []
    real_handler_cls = run_mod.StatsCallbackHandler

    def counting_handler(keys=None):
        handler = real_handler_cls(keys)
        checkpoint_handlers.append(handler)
        return handler

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", counting_handler)

    def build_with_tmp_cache(selections, checkpoint_flag):
        config = real_build(selections, checkpoint_flag)
        config["data_cache_dir"] = str(cache_dir)
        config["results_dir"] = str(tmp_path / "results")
        return config

    # ``clear_checkpoint_on_success`` runs after ``record_decision``. We read
    # the checkpoint at that boundary -- same thread, before the delete -- so
    # the evidence is of what the run actually saved.
    real_clear = graph_cls.clear_checkpoint_on_success
    real_begin = graph_cls.begin_checkpoint
    observed = {"pre": None, "step": None, "tuple": None, "cleared": False}

    def begin_and_remember(self, company_name, trade_date, asset_type="stock", portfolio=None):
        graph_instances.append(self)
        signature = self._run_signature(asset_type, portfolio)
        # Before the run: no checkpoint for this exact run's thread.
        observed["pre"] = checkpoint_step(
            self.config["data_cache_dir"], company_name, str(trade_date), signature
        )
        tid = real_begin(self, company_name, trade_date, asset_type, portfolio)
        observed["tid"] = tid
        observed["signature"] = signature
        observed["resuming"] = self._resuming
        observed["resume_input"] = self.checkpoint_input({"marker": "init"})
        observed["compiled_graph"] = self.graph
        return tid

    def read_then_clear(self, company_name, trade_date, asset_type="stock", portfolio=None):
        signature = self._run_signature(asset_type, portfolio)
        cache = self.config["data_cache_dir"]
        tid = thread_id(company_name, str(trade_date), signature)
        observed["step"] = checkpoint_step(cache, company_name, str(trade_date), signature)
        with get_checkpointer(cache, company_name) as saver:
            observed["tuple"] = saver.get_tuple({"configurable": {"thread_id": tid}})
        result = real_clear(self, company_name, trade_date, asset_type, portfolio)
        observed["cleared"] = (
            checkpoint_step(cache, company_name, str(trade_date), signature) is None
        )
        return result

    monkeypatch.setattr(graph_cls, "begin_checkpoint", begin_and_remember)
    monkeypatch.setattr(graph_cls, "clear_checkpoint_on_success", read_then_clear)
    monkeypatch.setattr(run_mod, "_build_run_config", build_with_tmp_cache)

    # Run before we start: the thread database does not exist yet.
    assert not _db_path(cache_dir, TICKER).exists()

    with _live_refresh_recorder(monkeypatch, harness):
        run_mod.run_analysis(checkpoint=True, flags=dict(RUN_FLAGS))

    # W-3: one handler on the new-checkpoint path as well.
    assert len(checkpoint_handlers) == 1, "the checkpoint path must also build one handler"

    snap = _last_live_display(harness)
    assert snap["stats"] == W15_STATS
    assert len(record["model"].executions) == 3
    assert sorted(record["model"].executions) == ["market", "market", "news"]
    assert harness["live_footer"] == W15_FOOTER

    # Before the run: this run's thread had no checkpoint.
    assert observed["pre"] is None
    # After ``begin_checkpoint``: this is a fresh run, not a resume, so the
    # initial state is what gets streamed.
    assert observed["resuming"] is False
    assert observed["resume_input"] == {"marker": "init"}
    # The graph was recompiled with the real saver, using the fixture workflow.
    assert len(record["compiled_with_saver"]) == 1
    assert record["compiled_with_saver"][0] is record["workflows"][0]
    # And ``begin_checkpoint`` returned this run's exact thread id.
    assert observed["tid"] == thread_id(TICKER, TRADE_DATE, observed["signature"])

    # Before cleanup: the real saver's database holds this thread's checkpoint.
    assert observed["step"] is not None and observed["step"] >= 1
    cp = observed["tuple"]
    assert cp is not None
    assert cp.config["configurable"]["thread_id"] == thread_id(
        TICKER, TRADE_DATE, observed["signature"]
    )
    values = cp.checkpoint["channel_values"]
    assert values.get("market_report")
    assert values.get("news_report")
    assert values.get("final_trade_decision") == FIXTURE_DECISION
    # And only after that read did the CLI clear it.
    assert observed["cleared"] is True

    # ``fixture_final`` ran as an explicit fan-in: both Analysts have an edge
    # into it, it ran exactly once, and when it saw the state both Analysts'
    # reports were already present. So it did not fire after just one of them.
    assert sorted(record["fan_in_sources"]) == ["Market Analyst", "News Analyst"]
    assert record.get("fixture_final_runs") == 1
    fan_in = record["final_state_seen"]
    assert fan_in["market_report"]
    assert fan_in["news_report"]


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



# ---------------------------------------------------------------------------
# W-9 / W-10 — token rendering in the per-Analyst summary
#
# These five cases render the real ``display_agent_summary`` for a handler fed
# with real callback events, and assert the rendered Input/Output cells of the
# Market Analyst row. Per O6-FR-02 an unknown field displays "Unknown", an
# explicit zero displays "0", and a partial subtotal keeps its "(partial)"
# marker. A genuinely omitted field is modelled by constructing the usage
# metadata without that key (``AIMessage.model_construct``); it is never
# fabricated as zero.
# ---------------------------------------------------------------------------


def _w910_handler_and_clock():
    """A real handler over the current run's analyst keys, with a fake clock."""
    from cli.stats_handler import StatsCallbackHandler

    class _Clock:
        def __init__(self):
            self._now = 0.0

        def __call__(self):
            return self._now

        def set(self, value):
            self._now = value

    clock = _Clock()
    return StatsCallbackHandler({"market"}, clock=clock), clock


def _w910_start(handler, clock, run_id, *, t=0.0):
    """An attributed Market Analyst model start."""
    clock.set(t)
    handler.on_chat_model_start(
        {}, [[]], run_id=run_id, metadata={"scope": "analyst", "agent_key": "market"}
    )


def _w910_end(handler, clock, run_id, usage, *, t=0.0):
    """A model end for ``run_id``. ``usage`` is the raw usage_metadata payload
    (None for no usage). A payload that omits a key is passed through as-is."""
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, LLMResult

    clock.set(t)
    if usage is None:
        message = AIMessage(content="ok")
    else:
        message = AIMessage.model_construct(content="ok", usage_metadata=usage)
    response = LLMResult(generations=[[ChatGeneration(message=message)]])
    handler.on_llm_end(response, run_id=run_id)


def _w910_market_cells(handler):
    """Render the real summary and return (input_cell, output_cell) for Market."""
    table, _text = _capture_summary_table(handler)
    rows = _table_rows(table)
    market = next(r for r in rows if r[0] == "Market Analyst")
    return market[2], market[3]


def test_w10_unknown_usage_renders_unknown():
    """A call with no usage renders "Unknown" for both token fields."""
    handler, clock = _w910_handler_and_clock()
    _w910_start(handler, clock, "u1", t=0.0)
    _w910_end(handler, clock, "u1", None, t=1.0)

    stats = handler.get_agent_stats()
    assert stats["analysts"]["market"]["calls"] == 1
    assert stats["unattributed_calls"] == 0
    assert _w910_market_cells(handler) == ("Unknown", "Unknown")


def test_w10_explicit_zero_renders_zero():
    """An explicit 0/0 renders "0" for both token fields."""
    handler, clock = _w910_handler_and_clock()
    _w910_start(handler, clock, "z1", t=0.0)
    _w910_end(
        handler, clock, "z1",
        {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}, t=1.0,
    )
    assert _w910_market_cells(handler) == ("0", "0")


def test_w9_partial_output_rendered():
    """100/20 then input-only 50 renders input 150 (complete), output 20 (partial)."""
    handler, clock = _w910_handler_and_clock()
    _w910_start(handler, clock, "p1", t=0.0)
    _w910_end(
        handler, clock, "p1",
        {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}, t=1.0,
    )
    _w910_start(handler, clock, "p2", t=1.0)
    _w910_end(handler, clock, "p2", {"input_tokens": 50, "total_tokens": 50}, t=2.0)

    market = handler.get_agent_stats()["analysts"]["market"]
    assert market["input_tokens"] == {"value": 150, "status": "complete"}
    assert market["output_tokens"] == {"value": 20, "status": "partial"}
    assert _w910_market_cells(handler) == ("150", "20 (partial)")


def test_w10_known_input_unknown_output():
    """A single call with input=100 and output omitted renders "100" / "Unknown"."""
    handler, clock = _w910_handler_and_clock()
    _w910_start(handler, clock, "k1", t=0.0)
    _w910_end(handler, clock, "k1", {"input_tokens": 100, "total_tokens": 100}, t=1.0)

    market = handler.get_agent_stats()["analysts"]["market"]
    assert market["input_tokens"] == {"value": 100, "status": "complete"}
    assert market["output_tokens"] == {"value": None, "status": "unknown"}
    assert _w910_market_cells(handler) == ("100", "Unknown")


def test_w10_unknown_input_known_output():
    """A single call with output=5 and input omitted renders "Unknown" / "5"."""
    handler, clock = _w910_handler_and_clock()
    _w910_start(handler, clock, "o1", t=0.0)
    _w910_end(handler, clock, "o1", {"output_tokens": 5, "total_tokens": 5}, t=1.0)

    market = handler.get_agent_stats()["analysts"]["market"]
    assert market["input_tokens"] == {"value": None, "status": "unknown"}
    assert market["output_tokens"] == {"value": 5, "status": "complete"}
    assert _w910_market_cells(handler) == ("Unknown", "5")


# ---------------------------------------------------------------------------
# W-1 / W-2 / W-5 — handler construction and single registration
#
# W-1: the handler learns this run's plan keys.
# W-2: exactly one handler serves the ordinary path.
# W-5: one registration path, observed at three points — the request the
#      propagator is asked for, the config the stream actually runs with, and
#      the constructor receiving no callbacks. W-4 (real fake-chat execution
#      with independent call counts) is reused unchanged: it is the
#      ``test_tc_o6_14`` case above.
# ---------------------------------------------------------------------------


def _single_run_with_observers(monkeypatch, *, analysts=("market", "news")):
    """Run one analysis while recording handler construction and registration."""
    from cli import run as run_mod

    seen = {"handlers": [], "ctor_callbacks": [], "graph_args": [], "stream_config": []}
    real_handler = run_mod.StatsCallbackHandler

    def recording_handler(keys=None):
        handler = real_handler(keys)
        seen["handlers"].append(handler)
        return handler

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", recording_handler)

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )

    real_init = graph_cls.__init__

    def recording_init(self, selected, config=None, debug=False, callbacks=None):
        seen["ctor_callbacks"].append(callbacks)
        real_init(self, selected, config=config, debug=debug, callbacks=callbacks)
        real_get_args = self.propagator.get_graph_args

        def get_args(callbacks=None):
            seen["graph_args"].append(callbacks)
            return real_get_args(callbacks=callbacks)

        self.propagator.get_graph_args = get_args

        real_stream_run = self.stream_run

        def stream_run(graph_input, **kwargs):
            seen["stream_config"].append(kwargs.get("config"))
            return real_stream_run(graph_input, **kwargs)

        self.stream_run = stream_run

    graph_cls.__init__ = recording_init
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    harness = _make_harness(monkeypatch, list(analysts))
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))
    # The fixture records what production handed the shared client.
    seen["tier_client_calls"] = record.get("tier_client_calls", [])
    return seen, harness


def test_w1_handler_receives_plan_keys(monkeypatch):
    """W-1: the statistics handler is built from this run's plan keys."""
    from tradingagents.graph.analyst_execution import build_analyst_execution_plan

    seen, _ = _single_run_with_observers(monkeypatch)

    expected = [spec.key for spec in build_analyst_execution_plan(["market", "news"]).specs]
    assert expected == ["market", "news"]
    assert len(seen["handlers"]) == 1
    assert seen["handlers"][0]._valid_keys == set(expected)


def test_w2_single_handler_ordinary(monkeypatch):
    """W-2: exactly one handler object serves the ordinary path."""
    seen, harness = _single_run_with_observers(monkeypatch)

    assert len(seen["handlers"]) == 1, "the ordinary path must build exactly one handler"
    handler = seen["handlers"][0]

    # It is the handler the run's own statistics reflect: both Analysts were
    # counted by that one object, not split across several.
    stats = handler.get_agent_stats()
    assert set(stats["analysts"]) == {"market", "news"}
    assert stats["analysts"]["market"]["calls"] == 2
    assert stats["analysts"]["news"]["calls"] == 1
    assert stats["unattributed_calls"] == 0


def test_w5_single_registration_path(monkeypatch):
    """W-5: the handler is registered once, through the graph execution config."""
    seen, _ = _single_run_with_observers(monkeypatch)

    assert len(seen["handlers"]) == 1
    handler = seen["handlers"][0]

    # A. the request asked of the propagator carries the handler once
    assert len(seen["graph_args"]) == 1, seen["graph_args"]
    requested = seen["graph_args"][0]
    assert requested is not None
    assert list(requested) == [handler]

    # B. the config the stream actually ran with carries it once
    assert len(seen["stream_config"]) == 1
    config = seen["stream_config"][0] or {}
    callbacks = (config.get("callbacks") or [])
    assert callbacks.count(handler) == 1

    # C. the constructor was not given callbacks, so nothing registered twice
    assert seen["ctor_callbacks"] == [None]

    # D. and the shared client was built without callbacks: production passes
    #    extra={"callbacks": ...} only when the graph was constructed with them.
    client_calls = seen.get("tier_client_calls")
    assert client_calls, "create_tier_client was never called"
    for call in client_calls:
        assert "callbacks" not in call["kwargs"], (
            "the shared client must not be constructed with callbacks: "
            f"{call['kwargs'].keys()}"
        )


# ---------------------------------------------------------------------------
# W-6 — empty analyst selection is rejected before anything is constructed
# ---------------------------------------------------------------------------


def test_w6_empty_selection_rejected(monkeypatch):
    """W-6: an empty selection raises ValueError before handler/graph/client setup."""
    import pytest

    from cli import run as run_mod

    monkeypatch.setattr(run_mod, "unattended_gaps", lambda flags: [])
    harness_selections = {
        "ticker": TICKER,
        "analysis_date": TRADE_DATE,
        "asset_type": "stock",
        "research_depth": 1,
        "quick_think_llm": "scripted",
        "deep_think_llm": "scripted",
        "backend_url": None,
        "llm_provider": "openai",
        "output_language": "English",
        "analysts": [],
    }
    monkeypatch.setattr(
        run_mod, "get_user_selections", lambda flags=None: dict(harness_selections)
    )
    monkeypatch.setattr(run_mod, "unattended_gaps", lambda flags: [])

    built = {"handler": 0, "graph": 0}

    def counting_handler(keys=None):
        built["handler"] += 1
        raise AssertionError("handler must not be constructed for an empty selection")

    def counting_graph(*a, **k):
        built["graph"] += 1
        raise AssertionError("graph must not be constructed for an empty selection")

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", counting_handler)
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", counting_graph)

    # The message must not be locked to exact wording, only the type.
    with pytest.raises(ValueError):
        run_mod.run_analysis(
            checkpoint=False,
            flags={"ticker": TICKER, "date": TRADE_DATE, "analysts": [], "save": False},
        )
    assert built == {"handler": 0, "graph": 0}



# ---------------------------------------------------------------------------
# W-7 — a reversed selection still renders canonical Analyst order
# ---------------------------------------------------------------------------


def test_w7_reversed_selection_keeps_canonical_rows(monkeypatch):
    """W-7: rows follow ANALYST_ORDER whatever order the selection arrives in."""
    from cli import run as run_mod
    from cli.display import ANALYST_ORDER
    from cli.models import AnalystType

    handler_records = []
    real_handler = run_mod.StatsCallbackHandler

    def recording_handler(keys=None):
        handler = real_handler(keys)
        handler_records.append(handler)
        return handler

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", recording_handler)

    # A genuinely reversed input: news first, then market.
    harness = _make_harness(monkeypatch, ["news", "market"])
    harness["selections"]["analysts"] = [AnalystType.NEWS, AnalystType.MARKET]

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    # The plan (and so the handler's keys) is in canonical order, not input order.
    handler = handler_records[-1]
    canonical = [key for key in ANALYST_ORDER if key in {"market", "news"}]
    assert canonical == ["market", "news"]
    assert handler._valid_keys == set(canonical)

    # The rendered rows are canonical, with unattributed last.
    table, _text = _capture_summary_table(handler)
    rows = [r[0] for r in _table_rows(table)]
    assert rows == ["Market Analyst", "News Analyst", "unattributed calls"]


# ---------------------------------------------------------------------------
# W-8b — a Market wrap_up start missing its identity key
#
# A single forwarder is the only registered handler. It strips agent_key from
# exactly one event (the first in-scope Market wrap_up start), keeping scope,
# run_id and every other event verbatim.
# ---------------------------------------------------------------------------


class _MissingKeyForwarder:
    """Forwards every callback once, dropping agent_key from one target start."""

    # LangChain's callback manager reads these on every handler.
    ignore_chain = False
    ignore_llm = False
    ignore_agent = False
    ignore_retriever = False
    ignore_chat_model = False
    ignore_custom_event = False
    raise_error = False

    def __init__(self, inner):
        self.inner = inner
        self.dropped = 0
        self.forwarded = []
        self.events = []          # (callback name, run_id) for every dispatch
        self.target_run_ids = []  # the run_id whose start lost its agent_key
        self.before = None        # snapshot before that start is forwarded
        self.after = None         # snapshot after its end is forwarded
        self._seen = set()

    def __getattr__(self, name):
        # Any callback the manager dispatches is forwarded verbatim exactly once,
        # so the wrapper cannot silently swallow an event type it does not know.
        if name.startswith("on_"):
            def forward(*args, **kwargs):
                self.forwarded.append(name)
                return getattr(self.inner, name)(*args, **kwargs)

            return forward
        return getattr(self.inner, name)

    def _forward(self, _cb_name, *args, **kwargs):
        self.forwarded.append(_cb_name)
        return getattr(self.inner, _cb_name)(*args, **kwargs)

    def on_chat_model_start(self, serialized, messages, *, run_id=None, metadata=None, **kwargs):
        meta = metadata or {}
        self.events.append(("on_chat_model_start", run_id))
        is_target = (
            self.dropped == 0
            and meta.get("scope") == "analyst"
            and meta.get("agent_key") == "market"
            and meta.get("langgraph_node") == "wrap_up"
        )
        if is_target and run_id not in self._seen:
            self._seen.add(run_id)
            self.dropped += 1
            self.target_run_ids.append(run_id)
            # Snapshot immediately before the stripped start is forwarded.
            self.before = copy.deepcopy(self.inner.get_agent_stats())
            copied = {k: v for k, v in meta.items() if k != "agent_key"}
            self.forwarded.append("on_chat_model_start")
            return self.inner.on_chat_model_start(
                serialized, messages, run_id=run_id, metadata=copied, **kwargs
            )
        return self._forward("on_chat_model_start", serialized, messages, run_id=run_id, metadata=metadata, **kwargs)

    def on_llm_end(self, response, *, run_id=None, **kwargs):
        self.events.append(("on_llm_end", run_id))
        result = self.inner.on_llm_end(response, run_id=run_id, **kwargs)
        # Snapshot immediately after the matching end is forwarded.
        if self.target_run_ids and run_id == self.target_run_ids[0] and self.after is None:
            self.after = copy.deepcopy(self.inner.get_agent_stats())
        return result

    def on_llm_start(self, serialized, prompts, *, run_id=None, metadata=None, **kwargs):
        return self._forward("on_llm_start", serialized, prompts, run_id=run_id, metadata=metadata, **kwargs)

    def on_llm_error(self, error, *, run_id=None, **kwargs):
        return self._forward("on_llm_error", error, run_id=run_id, **kwargs)

    def on_tool_start(self, serialized, input_str, *, run_id=None, metadata=None, **kwargs):
        return self._forward("on_tool_start", serialized, input_str, run_id=run_id, metadata=metadata, **kwargs)

    def get_stats(self):
        return self.inner.get_stats()

    def get_agent_stats(self):
        return self.inner.get_agent_stats()


def test_w8b_missing_identity_renders_one(monkeypatch):
    """W-8b: dropping Market wrap_up's agent_key moves that call to unattributed."""
    from cli import run as run_mod

    forwarders = []
    real_handler = run_mod.StatsCallbackHandler

    def wrapping_handler(keys=None):
        forwarder = _MissingKeyForwarder(real_handler(keys))
        forwarders.append(forwarder)
        return forwarder

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", wrapping_handler)

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()),
        record,
        monkeypatch,
        wrap_up_analysts=("market",),
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    _make_harness(monkeypatch, ["market", "news"])
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    assert len(forwarders) == 1, "the forwarder must be the sole registered handler"
    forwarder = forwarders[0]
    assert forwarder.dropped == 1, "exactly one Market wrap_up start loses its key"

    # --- forwarding evidence ---
    # Exactly one target start lost its key, and that start was forwarded once.
    assert len(forwarder.target_run_ids) == 1, forwarder.target_run_ids
    target = forwarder.target_run_ids[0]
    dispatches = [name for name, run_id in forwarder.events if run_id == target]
    assert dispatches.count("on_chat_model_start") == 1, forwarder.events
    assert dispatches.count("on_llm_end") == 1, forwarder.events

    # The target start precedes its end.
    kinds = [name for name, run_id in forwarder.events if run_id == target]
    assert kinds.index("on_chat_model_start") < kinds.index("on_llm_end")

    # --- the missing-identity event did not change the named statistics ---
    # Before the stripped start, Market already held its ordinary call and News
    # its own; the wrap_up event must move nothing but the unattributed count.
    assert forwarder.before is not None and forwarder.after is not None
    assert forwarder.after["analysts"]["news"] == forwarder.before["analysts"]["news"]
    assert forwarder.before["unattributed_calls"] == 0
    assert forwarder.after["unattributed_calls"] == 1

    stats = forwarder.get_agent_stats()
    market = stats["analysts"]["market"]
    news = stats["analysts"]["news"]

    # Market keeps its ordinary call (100/20); the wrap_up call moved out.
    assert market["calls"] == 1
    assert market["input_tokens"] == {"value": 100, "status": "complete"}
    assert market["output_tokens"] == {"value": 20, "status": "complete"}
    assert stats["unattributed_calls"] == 1
    # News is untouched: same call count and the same tokens as before.
    assert news["calls"] == 1
    assert news["input_tokens"] == {"value": 80, "status": "complete"}
    assert news["output_tokens"] == {"value": 15, "status": "complete"}

    # The rendered table shows the moved call where the handler counts it.
    table, _text = _capture_summary_table(forwarder)
    rows = {r[0]: r for r in _table_rows(table)}
    assert rows["Market Analyst"][1] == "1"
    assert rows["unattributed calls"][1] == "1"


# ---------------------------------------------------------------------------
# W-11 — a News-only run renders only News, plus the unattributed row
# ---------------------------------------------------------------------------


def test_w11_news_only_rendered_table(monkeypatch):
    """W-11: News-only shows just the News row and the unattributed line."""
    from cli import run as run_mod
    from cli.models import AnalystType

    handlers = []
    real_handler = run_mod.StatsCallbackHandler

    def recording_handler(keys=None):
        handler = real_handler(keys)
        handlers.append(handler)
        return handler

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", recording_handler)

    harness = _make_harness(monkeypatch, ["news"])
    harness["selections"]["analysts"] = [AnalystType.NEWS]
    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)
    run_mod.message_buffer.init_for_analysis(["news"])

    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    handler = handlers[-1]
    table, _text = _capture_summary_table(handler)
    rows = [r[0] for r in _table_rows(table)]
    assert rows == ["News Analyst", "unattributed calls"]



# ---------------------------------------------------------------------------
# W-14 — completion order around Live.__exit__
# ---------------------------------------------------------------------------


def test_w14_completion_order(monkeypatch):
    """W-14: each event happens once, and Live exits before the summary.

    Order asserted from the real recorded sequence:
    ``live_exit < summary`` and ``completion < elapsed < summary < report_options``.
    """
    from cli import run as run_mod

    events = []

    import rich.live as rich_live

    class RecordingLive(rich_live.Live):
        def __exit__(self, *exc):
            try:
                return super().__exit__(*exc)
            finally:
                events.append("live_exit")

    monkeypatch.setattr(run_mod, "Live", RecordingLive)

    # Every wrapper calls the real target first and records only on a successful
    # return, so a raising target never produces a spurious success event.
    real_summary = run_mod.display_agent_summary

    def recording_summary(*args, **kwargs):
        result = real_summary(*args, **kwargs)
        events.append("summary")
        return result

    monkeypatch.setattr(run_mod, "display_agent_summary", recording_summary)

    record = {}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)
    _make_harness(monkeypatch, ["market", "news"])

    # The harness installs its own _offer_reports; wrap that one.
    harness_offer = run_mod._offer_reports

    def recording_offer(*args, **kwargs):
        result = harness_offer(*args, **kwargs)
        events.append("report_options")
        return result

    monkeypatch.setattr(run_mod, "_offer_reports", recording_offer)

    fake_console = run_mod.console
    real_print = fake_console.print

    def recording_print(*args, **kwargs):
        result = real_print(*args, **kwargs)
        text = " ".join(str(a) for a in args)
        if "Analysis Complete" in text:
            events.append("completion")
        elif "Analyst wall time" in text:
            # The elapsed line: cli/run.py prints the tracker's summary here.
            events.append("elapsed")
        return result

    fake_console.print = recording_print

    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    # --- each target event occurs exactly once ---
    for name in ("live_exit", "completion", "elapsed", "summary", "report_options"):
        assert events.count(name) == 1, f"{name} occurred {events.count(name)} times in {events}"

    # --- order, taken from the actual recorded sequence ---
    idx = {n: events.index(n) for n in ("live_exit", "completion", "elapsed", "summary", "report_options")}
    assert idx["live_exit"] < idx["summary"], "the summary must be shown after Live exits"
    assert idx["completion"] < idx["elapsed"], "the completion notice precedes the elapsed line"
    assert idx["elapsed"] < idx["summary"], "the elapsed line precedes the summary"
    assert idx["summary"] < idx["report_options"], "report options come last"



# ---------------------------------------------------------------------------
# W-12 — an out-of-scope Bull call must not disturb the Analyst statistics
#
# Opt-in: the real Bull Researcher is built (``real_bull=True``) and the
# scripted model answers its prompt. A single probe is the sole registered
# forwarding callback; it only collects evidence and the test body asserts.
# ---------------------------------------------------------------------------


class _BullProbe:
    """Sole forwarding callback; snapshots and renders around the Bull call."""

    ignore_chain = False
    ignore_llm = False
    ignore_agent = False
    ignore_retriever = False
    ignore_chat_model = False
    ignore_custom_event = False
    raise_error = False

    def __init__(self, inner, holder):
        self.inner = inner
        self.holder = holder

    def __getattr__(self, name):
        if name.startswith("on_"):
            def forward(*args, **kwargs):
                return getattr(self.inner, name)(*args, **kwargs)

            return forward
        return getattr(self.inner, name)

    def _snapshot(self):
        return copy.deepcopy(self.inner.get_agent_stats())

    def _render(self):
        return _capture_summary_table(self.inner)

    def on_chat_model_start(self, serialized, messages, *, run_id=None, metadata=None, **kwargs):
        meta = metadata or {}
        node = meta.get("langgraph_node")
        scope = meta.get("scope")
        self.holder["events"].append(("start", run_id, node, scope))

        if node == "Bull Researcher" and scope != "analyst":
            self.holder["target_starts"].append(run_id)

        # Before the target start is forwarded: full snapshot + real render.
        if run_id in self.holder["target_starts"] and "before" not in self.holder:
            self.holder["before"] = self._snapshot()
            self.holder["before_table"], self.holder["before_text"] = self._render()

        return self.inner.on_chat_model_start(
            serialized, messages, run_id=run_id, metadata=metadata, **kwargs
        )

    def on_llm_end(self, response, *, run_id=None, **kwargs):
        self.holder["events"].append(("end", run_id, None, None))
        result = self.inner.on_llm_end(response, run_id=run_id, **kwargs)

        # After the matching successful end is forwarded.
        if run_id in self.holder["target_starts"] and "after" not in self.holder:
            self.holder["after"] = self._snapshot()
            self.holder["after_table"], self.holder["after_text"] = self._render()
        return result

    def get_stats(self):
        return self.inner.get_stats()

    def get_agent_stats(self):
        return self.inner.get_agent_stats()


def test_w12_out_of_scope_summary_unchanged(monkeypatch):
    """W-12: a real Bull call leaves the full statistics and rendered table unchanged."""
    from cli import run as run_mod

    holder = {"events": [], "target_starts": []}
    probes = []
    real_handler = run_mod.StatsCallbackHandler

    def probing_handler(keys=None):
        probe = _BullProbe(real_handler(keys), holder)
        probes.append(probe)
        return probe

    monkeypatch.setattr(run_mod, "StatsCallbackHandler", probing_handler)

    record = {"answer_real_bull": True}
    graph_cls = _build_fixture_graph(
        _script(_market_script(), _news_script()), record, monkeypatch, real_bull=True
    )
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", graph_cls)

    _make_harness(monkeypatch, ["market", "news"])
    run_mod.run_analysis(checkpoint=False, flags=dict(RUN_FLAGS))

    assert len(probes) == 1, "the probe must be the sole registered callback"

    # --- exactly one target start and one matching successful end ---
    assert len(holder["target_starts"]) == 1, holder["events"]
    target = holder["target_starts"][0]

    starts = [e for e in holder["events"] if e[0] == "start" and e[1] == target]
    ends = [e for e in holder["events"] if e[0] == "end" and e[1] == target]
    assert len(starts) == 1, f"expected one target start, got {starts}"
    assert len(ends) == 1, f"expected one matching end, got {ends}"

    # --- start precedes end; no Analyst event in between ---
    # The end event records no scope, so scopes are looked up by run_id.
    scope_by_run = {
        run_id: scope for (kind, run_id, _node, scope) in holder["events"] if kind == "start"
    }
    start_i = holder["events"].index(starts[0])
    end_i = holder["events"].index(ends[0])
    assert start_i < end_i, (start_i, end_i)

    between = holder["events"][start_i + 1 : end_i]
    analyst_events = [e for e in between if scope_by_run.get(e[1]) == "analyst"]
    assert not analyst_events, f"Analyst events between Bull start and end: {analyst_events}"

    # The Bull's own call is out of scope.
    assert starts[0][3] != "analyst", starts[0]

    # --- full statistics unchanged across the call ---
    before = holder["before"]
    after = holder["after"]
    assert after == before, "the Bull call changed the reported statistics"
    assert before["unattributed_calls"] == 0
    assert after["unattributed_calls"] == 0
    assert set(after["analysts"]) == {"market", "news"}
    assert after["analysts"]["market"]["calls"] == 2
    assert after["analysts"]["news"]["calls"] == 1

    # --- rendered table identical, from independent buffers ---
    assert holder["after_text"] == holder["before_text"], "the rendered summary changed"
    assert _table_rows(holder["after_table"]) == _table_rows(holder["before_table"])
    assert holder["after_text"].strip(), "the rendered summary was empty"

