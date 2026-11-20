"""O4 Stage 2 — real-CLI publication integration tests (D-owned).

Drives the REAL ``cli.run.run_analysis`` publication path (PR #25, ``e0ffa3a``)
with a fake graph/LLM harness in the style of ``test_o2_cli_manifest.py``, but
with one crucial difference: ``record_decision`` is delegated to the **real**
``TradingAgentsGraph.record_decision`` boundary (execution window active), and
``run_rating``/``is_review`` are the **real** production functions. This lets the
tests observe the actual Gate-at-boundary + PM buffering + review-labelling +
real-time Markdown behaviour without any LLM/network.

Covers T-23 (PM buffering / temporal), T-19 (REVIEW non-authoritative), and the
PM-portion of T-08 (enabled output surfaces), plus completion/review/elapsed/
O6/report-options ordering and O2 reserve→…→single-manifest ordering.
"""

from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace

import pytest

# Mandatory offline tests: the CLI runtime is a required dependency. A missing
# import must surface as a hard collection/execution failure, never a skip.
from cli import run as run_mod
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.memory import TradingMemoryLog

TICKER = "NVDA"
TRADE_DATE = "2026-01-10"


# ---------------------------------------------------------------------------
# Fixtures / fakes (mirroring test_o2_cli_manifest.py)
# ---------------------------------------------------------------------------
class _FakePropagator:
    def get_graph_args(self, callbacks=None):
        return {}


class _FakePlan:
    def __init__(self, keys):
        self.specs = [SimpleNamespace(key=k, agent_node=f"{k.title()} Analyst") for k in keys]


class _FakeTracker:
    def __init__(self, plan):
        self.plan = plan

    def mark_started(self, key):
        return None

    def format_summary(self):
        return "elapsed 0.0s"


class _FakeStats:
    def __init__(self, keys):
        self.keys = keys


class _RecordingBuffer:
    """Records every update_report_section call in order for temporal assertions."""

    def __init__(self):
        self.init_for_analysis(["market"])

    def init_for_analysis(self, keys):
        self.messages = []
        self.report_sections = {}
        self.agent_status = {}
        self._processed_message_ids = set()
        self.section_history = []  # (section_name, content) in call order

    def add_message(self, message_type, content):
        # CLI decorator expects (timestamp, message_type, content) 3-tuples.
        self.messages.append(("now", message_type, content))

    def add_tool_call(self, tool_name, args):
        self.messages.append(("now", "Tool Call", f"{tool_name}({args})"))

    def update_report_section(self, section_name, content):
        self.report_sections[section_name] = content
        self.section_history.append((section_name, content))

    def update_agent_status(self, agent, status):
        self.agent_status[agent] = status


class _RecordingConsole:
    def __init__(self):
        self.lines = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))


def _state(final_rating="Buy", body="**Rating**: Buy\n\nBuy NVDA.", news="News: neutral."):
    return {
        "company_of_interest": TICKER,
        "trade_date": TRADE_DATE,
        "market_report": "Market: ok.",
        "sentiment_report": "Sentiment: ok.",
        "news_report": news,
        "fundamentals_report": "Fundamentals: ok.",
        "investment_debate_state": {
            "bull_history": "B",
            "bear_history": "b",
            "history": "",
            "current_response": "",
        },
        "trader_investment_plan": "Trader plan.",
        "risk_debate_state": {
            "aggressive_history": "A",
            "conservative_history": "C",
            "neutral_history": "N",
            "history": "",
        },
        "investment_plan": "Plan.",
        "final_trade_decision": body,
        "final_rating": final_rating,
    }


def _stream_chunks(state):
    """Yield the chunk sequence run_analysis consumes: debate, trader, risk (PM).

    Each chunk carries the identity/date fields the merged final_state needs
    (the real ``values`` stream includes the full state on every step).
    """
    ident = {"company_of_interest": state["company_of_interest"], "trade_date": state["trade_date"]}
    # A PM-originated assistant MESSAGE carrying the decision body, so the CLI
    # message/display area (not just the report section) is exercised.
    from langchain_core.messages import AIMessage

    # Carry the real ``langgraph_node`` metadata production uses to identify the
    # PM's own message, so the CLI buffers it exactly as it does in a real run.
    pm_msg = AIMessage(
        content=state["final_trade_decision"],
        name="Portfolio Manager",
        response_metadata={"langgraph_node": "Portfolio Manager"},
    )
    yield [pm_msg], None
    yield (
        [],
        {
            **ident,
            "investment_debate_state": state["investment_debate_state"],
            "investment_plan": state["investment_plan"],
        },
    )
    yield [], {**ident, "trader_investment_plan": state["trader_investment_plan"]}
    risk = dict(state["risk_debate_state"])
    risk["final_trade_decision"] = state["final_trade_decision"]
    yield (
        [],
        {
            **ident,
            "risk_debate_state": risk,
            "final_trade_decision": state["final_trade_decision"],
            "market_report": state["market_report"],
            "sentiment_report": state["sentiment_report"],
            "news_report": state["news_report"],
            "fundamentals_report": state["fundamentals_report"],
            "final_rating": state.get("final_rating", ""),
        },
    )


def _install(monkeypatch, tmp_path, *, final_state, markdown_failure=False):
    """Install the CLI harness; record_decision delegates to the REAL boundary."""
    results = tmp_path / "results"
    from tradingagents.dataflows.symbols import safe_ticker_component

    reports_dir = results / safe_ticker_component(TICKER) / TRADE_DATE / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_dir = results / TICKER / "TradingAgentsStrategy_logs"
    state_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "results_dir": str(results),
        "data_cache_dir": str(tmp_path / "cache"),
        "memory_log_path": str(tmp_path / "memory.md"),
        "llm_provider": "openai",
        "deep_think_llm": "d",
        "quick_think_llm": "q",
        "analysts": ["market", "news"],
        "output_language": "English",
        "checkpoint_enabled": False,
    }
    selections = {
        "ticker": TICKER,
        "analysis_date": TRADE_DATE,
        "asset_type": "stock",
        "analysts": [SimpleNamespace(value="market"), SimpleNamespace(value="news")],
    }

    # Real boundary object (no LLM): only the attrs record_decision/_log_state touch.
    boundary = object.__new__(TradingAgentsGraph)
    boundary.config = config
    boundary.selected_analysts = ("market", "news")
    boundary._completion = None
    boundary._execution_active = False
    boundary._checkpointer_ctx = None
    boundary._resuming = False
    boundary.debug = False
    boundary.memory_log = TradingMemoryLog(config)

    harness = {
        "calls": [],
        "reports_dir": reports_dir,
        "state_log": state_dir / f"full_states_log_{TRADE_DATE}.json",
        "boundary": boundary,
        "buffer": None,
        "console": None,
    }

    class FakeGraph:
        def __init__(self, analysts, *, config, debug):
            harness["calls"].append("graph_init")
            self.config = config
            self.propagator = _FakePropagator()

        def create_run_state(self, ticker, trade_date, asset_type, portfolio):
            return {"ticker": ticker}

        def begin_checkpoint(self, ticker, trade_date, asset_type, portfolio):
            harness["calls"].append("begin_checkpoint")
            return boundary.begin_checkpoint(ticker, trade_date, asset_type, portfolio)

        def checkpoint_input(self, state):
            return state

        def stream_run(self, state, **kwargs):
            yield from _stream_chunks(final_state)

        def record_decision(self, ticker, trade_date, final_state):
            harness["calls"].append("record_decision")
            harness["merged_final_state"] = final_state
            # --- PRE-GATE snapshot (real boundary has NOT run yet) ---
            ftk_md = harness["reports_dir"] / "final_trade_decision.md"
            harness["pre_gate"] = {
                "sections": dict(harness["buffer"].report_sections),
                "messages": list(harness["buffer"].messages),
                "final_trade_decision_md": (
                    ftk_md.read_text(encoding="utf-8") if ftk_md.exists() else None
                ),
            }
            # Delegate to the REAL production completion boundary (in-window).
            boundary.record_decision(ticker, trade_date, final_state)
            # Capture last_completion inside the window (end_checkpoint clears it).
            harness["last_completion"] = boundary.last_completion

        def clear_checkpoint_on_success(self, ticker, trade_date, asset_type, portfolio):
            return None

        def end_checkpoint(self):
            harness["calls"].append("end_checkpoint")
            boundary.end_checkpoint()

        def default_report_path(self, ticker):
            return results / "reports_saved"

        def save_reports(self, final_state, ticker, save_path, html=True):
            harness["calls"].append("save_reports")
            from tradingagents.reporting import write_report_tree

            save_path.mkdir(parents=True, exist_ok=True)
            return write_report_tree(final_state, ticker, save_path, settings=None, html=html)

    buffer = _RecordingBuffer()
    console = _RecordingConsole()
    harness["buffer"] = buffer
    harness["console"] = console

    def fake_reserve(results_dir, ticker, trade_date):
        harness["calls"].append("reserve")
        run_dir = results / ticker.replace(".", "_") / trade_date / "runs" / "r1"
        run_dir.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(run_id="r1", run_dir=run_dir)

    def fake_finalize(run_context, *, config, artifacts):
        harness["calls"].append("finalize")
        from tradingagents.repro import manifest as manifest_module

        m = manifest_module.build_manifest(
            ticker=TICKER,
            asset_type="stock",
            analysis_date=TRADE_DATE,
            analysts=["market", "news"],
            config=config,
            runtime=manifest_module.collect_runtime_metadata(git_metadata=None),
            artifacts=artifacts,
        )
        p = manifest_module.write_manifest(run_context.run_dir / "manifest.json", m)
        return SimpleNamespace(success=True, manifest_path=p, artifacts=list(artifacts), error=None)

    monkeypatch.setattr(run_mod, "TradingAgentsGraph", FakeGraph)
    monkeypatch.setattr(run_mod, "get_user_selections", lambda flags=None: dict(selections))
    monkeypatch.setattr(run_mod, "unattended_gaps", lambda flags: [])
    monkeypatch.setattr(run_mod, "_build_run_config", lambda selections, checkpoint: dict(config))
    monkeypatch.setattr(run_mod, "build_analyst_execution_plan", lambda keys: _FakePlan(keys))
    monkeypatch.setattr(run_mod, "AnalystWallTimeTracker", _FakeTracker)
    monkeypatch.setattr(run_mod, "StatsCallbackHandler", _FakeStats)
    monkeypatch.setattr(run_mod, "create_layout", lambda: SimpleNamespace())
    monkeypatch.setattr(run_mod, "Live", lambda *a, **k: nullcontext())
    monkeypatch.setattr(run_mod, "update_display", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "update_analyst_statuses", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "update_research_team_status", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "display_agent_summary", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "display_complete_report", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "console", console)
    # Use the REAL rating helpers so the boundary's semantics are what we assert.
    from tradingagents.agents import rating as rating_mod

    monkeypatch.setattr(run_mod, "is_review", rating_mod.is_review)
    monkeypatch.setattr(run_mod, "run_rating", rating_mod.run_rating)
    monkeypatch.setattr(run_mod, "message_buffer", buffer)
    monkeypatch.setattr(run_mod, "_reserve_run_directory", fake_reserve, raising=False)
    monkeypatch.setattr(run_mod, "_finalize_run_manifest", fake_finalize, raising=False)
    return harness


def _run(monkeypatch, tmp_path, final_state):
    harness = _install(monkeypatch, tmp_path, final_state=final_state)
    run_mod.run_analysis(
        checkpoint=False,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market", "news"],
            "save": False,
            "show": False,
            "html": False,
        },
    )
    return harness


def _section_contents(harness):
    return [(s, c) for (s, c) in harness["buffer"].section_history if s == "final_trade_decision"]


# ---------------------------------------------------------------------------
# A — valid evidence preserved, single Gate, surfaces agree
# ---------------------------------------------------------------------------
def test_cli_valid_evidence_preserved(monkeypatch, tmp_path):
    state = _state("Buy", "**Rating**: Buy\n\nBuy NVDA.")
    h = _run(monkeypatch, tmp_path, state)
    # Single authoritative record_decision, inside the window.
    assert (
        h["calls"].index("begin_checkpoint")
        < h["calls"].index("record_decision")
        < h["calls"].index("end_checkpoint")
    )
    # Boundary applied the Gate to the merged final state: surfaces agree.
    merged = h["merged_final_state"]
    assert merged["final_rating"] == merged["effective_rating"] == "Buy"
    assert merged["original_rating"] == "Buy"
    # No REVIEW warning printed for a valid Buy.
    assert not any("recorded for review" in ln for ln in h["console"].lines)


# ---------------------------------------------------------------------------
# B — missing evidence -> REVIEW, body preserved, REVIEW non-authoritative
# ---------------------------------------------------------------------------
def test_cli_missing_evidence_review_non_authoritative(monkeypatch, tmp_path):
    body = "**Rating**: Buy\n\nBuy NVDA."
    state = _state("Buy", body, news="")  # news empty -> REVIEW
    h = _run(monkeypatch, tmp_path, state)
    merged = h["merged_final_state"]
    assert merged["final_rating"] == merged["effective_rating"] == "REVIEW"
    assert merged["final_trade_decision"] == body  # body unchanged
    # The published PM section is explicitly labelled non-authoritative.
    final_pm = [c for (s, c) in _section_contents(h) if "Portfolio Manager Decision" in c]
    assert final_pm, "PM decision section must be published post-gate"
    assert any("unapproved original content" in c for c in final_pm)
    # REVIEW warning printed.
    assert any("recorded for review" in ln for ln in h["console"].lines)


# ---------------------------------------------------------------------------
# D — PM streaming safety (pre-gate buffering / markdown / ordinary sections)
# ---------------------------------------------------------------------------
def test_cli_pm_buffered_pre_gate_and_markdown_safe(monkeypatch, tmp_path):
    """FULL pre-Gate timeline: no PM body in the CLI message area, the PM section,
    or the real-time final_trade_decision.md at ANY event before the Gate — not
    merely a single final snapshot (catches a leak-then-clear transient)."""
    secret = "SECRET BUY BODY."
    body = f"**Rating**: Buy\n\n{secret}"
    state = _state("Buy", body, news="")  # REVIEW

    # Install the harness, then wrap its buffer/decorator to record a TIMELINE.
    h = _install(monkeypatch, tmp_path, final_state=state)
    buf = h["buffer"]
    reports_dir = h["reports_dir"]
    timeline = []  # list of dicts {phase, channel, content}
    phase = {"gate_started": False}

    # Mark the exact moment the real Gate boundary is entered.
    real_record = h["boundary"].record_decision

    def record_and_mark(*a, **k):
        phase["gate_started"] = True
        return real_record(*a, **k)

    monkeypatch.setattr(h["boundary"], "record_decision", record_and_mark)

    real_update = buf.update_report_section

    def wrapped_update(section_name, content):
        real_update(section_name, content)
        ph = "post" if phase["gate_started"] else "pre"
        md = None
        f = reports_dir / f"{section_name}.md"
        if f.exists():
            md = f.read_text(encoding="utf-8")
        timeline.append(
            {
                "phase": ph,
                "channel": "section",
                "section": section_name,
                "content": content,
                "md": md,
            }
        )

    monkeypatch.setattr(buf, "update_report_section", wrapped_update)

    real_add = buf.add_message

    def wrapped_add(mtype, content):
        real_add(mtype, content)
        ph = "post" if phase["gate_started"] else "pre"
        timeline.append({"phase": ph, "channel": "message", "content": content, "md": None})

    monkeypatch.setattr(buf, "add_message", wrapped_add)

    from cli import run as _run_mod

    _run_mod.run_analysis(
        checkpoint=False,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market", "news"],
            "save": False,
            "show": False,
            "html": False,
        },
    )

    pre = [e for e in timeline if e["phase"] == "pre"]
    assert pre, "expected some pre-Gate events to audit"
    # (1) NO pre-Gate message event carries the PM body.
    for e in pre:
        if e["channel"] == "message":
            assert secret not in str(e["content"]), f"PM body in message pre-Gate: {e}"
    # (2) NO pre-Gate PM-section write carries the body, NOR its real-time .md file
    # at that write (catches a transient release then clear).
    for e in pre:
        if e["channel"] == "section" and e.get("section") == "final_trade_decision":
            assert secret not in str(e["content"]), f"PM body in section pre-Gate: {e}"
            if e["md"] is not None:
                assert secret not in e["md"], f"PM body in final_trade_decision.md pre-Gate: {e}"

    # (3) Ordinary Analyst sections still streamed (some pre-Gate non-PM section).
    assert any(
        e["channel"] == "section" and e.get("section") not in (None, "final_trade_decision")
        for e in pre
    ), "ordinary analyst sections must stream"

    # (4) Post-Gate REVIEW: body present AND explicitly non-authoritative (section).
    post_ftk = [
        e
        for e in timeline
        if e["phase"] == "post"
        and e["channel"] == "section"
        and e.get("section") == "final_trade_decision"
        and secret in str(e["content"])
    ]
    assert post_ftk, "post-gate REVIEW body must be published in the PM section"
    assert any(
        "unapproved original content" in str(e["content"]).lower()
        or "not an approved recommendation" in str(e["content"]).lower()
        for e in post_ftk
    )


def test_cli_ordinary_analyst_sections_stream(monkeypatch, tmp_path):
    state = _state("Buy", "**Rating**: Buy")
    h = _run(monkeypatch, tmp_path, state)
    sections = {s for (s, c) in h["buffer"].section_history}
    # Ordinary sections (research / trader) were written as usual.
    assert "investment_plan" in sections
    assert "trader_investment_plan" in sections


# ---------------------------------------------------------------------------
# F — ordering: reserve before graph; record_decision before save/finalize
# ---------------------------------------------------------------------------
def test_cli_ordering_reserve_and_manifest(monkeypatch, tmp_path):
    h = _run(monkeypatch, tmp_path, _state("Buy", "**Rating**: Buy"))
    calls = h["calls"]
    assert calls.index("reserve") < calls.index("graph_init")
    assert calls.index("record_decision") < calls.index("finalize")


# ---------------------------------------------------------------------------
# F — completion -> review -> elapsed ordering of console messages
# ---------------------------------------------------------------------------
def test_cli_completion_and_review_ordering(monkeypatch, tmp_path):
    h = _run(monkeypatch, tmp_path, _state("Buy", "Rating: Buy", news=""))
    lines = h["console"].lines
    idx_complete = next(i for i, ln in enumerate(lines) if "Analysis Complete" in ln)
    idx_review = next(i for i, ln in enumerate(lines) if "recorded for review" in ln)
    idx_elapsed = next(i for i, ln in enumerate(lines) if "elapsed" in ln)
    assert idx_complete < idx_review < idx_elapsed, lines


# ---------------------------------------------------------------------------
# C — selected/unselected analysts, N/A text, original REVIEW not upgraded
# ---------------------------------------------------------------------------
def test_cli_market_news_unselected_not_required_and_na_present(monkeypatch, tmp_path):
    # sentiment/fundamentals empty but unselected (market+news) => not_required
    state = _state("Buy", "**Rating**: Buy")
    state["sentiment_report"] = ""
    state["fundamentals_report"] = ""
    state["news_report"] = "N/A — source unavailable for this item."  # non-empty N/A
    h = _run(monkeypatch, tmp_path, state)
    merged = h["merged_final_state"]
    assert merged["effective_rating"] == "Buy"  # no spurious downgrade
    rec = h["last_completion"]
    assert rec.gate.statuses["sentiment_report"] == "not_required"
    assert rec.gate.statuses["fundamentals_report"] == "not_required"
    assert rec.gate.statuses["news_report"] == "present"


def test_cli_original_review_not_upgraded(monkeypatch, tmp_path):
    state = _state("REVIEW", "Rating: REVIEW")
    h = _run(monkeypatch, tmp_path, state)
    merged = h["merged_final_state"]
    assert merged["effective_rating"] == "REVIEW"
    assert any("recorded for review" in ln for ln in h["console"].lines)


# ---------------------------------------------------------------------------
# E — unknown analyst configuration aborts publication (T-18)
# ---------------------------------------------------------------------------
def test_cli_unknown_config_aborts_publication(monkeypatch, tmp_path):
    harness = _install(monkeypatch, tmp_path, final_state=_state("Buy", "Rating: Buy"))
    # Make the boundary's analyst selection include an unknown key so check_evidence raises.
    harness["boundary"].selected_analysts = ("market", "news", "options")
    with pytest.raises(ValueError):
        run_mod.run_analysis(
            checkpoint=False,
            flags={
                "ticker": TICKER,
                "date": TRADE_DATE,
                "analysts": ["market", "news"],
                "save": False,
                "show": False,
                "html": False,
            },
        )
    # The failure happened inside record_decision (Gate), before finalize/manifest.
    assert "finalize" not in harness["calls"]


# ---------------------------------------------------------------------------
# E — state-log failure prevents finalization
# ---------------------------------------------------------------------------
def test_cli_state_log_failure_prevents_finalize(monkeypatch, tmp_path):
    h = _install(monkeypatch, tmp_path, final_state=_state("Buy", "Rating: Buy"))

    # Make the real boundary's _log_state fail.
    def boom(trade_date, fs):
        raise OSError("state log write failed")

    monkeypatch.setattr(h["boundary"], "_log_state", boom)
    with pytest.raises(OSError):
        run_mod.run_analysis(
            checkpoint=False,
            flags={
                "ticker": TICKER,
                "date": TRADE_DATE,
                "analysts": ["market", "news"],
                "save": False,
                "show": False,
                "html": False,
            },
        )
    assert "finalize" not in h["calls"]


# ---------------------------------------------------------------------------
# E — mid-stream failure after PM content, before Gate
# ---------------------------------------------------------------------------
def test_cli_midstream_failure_after_pm_no_authoritative_publication(monkeypatch, tmp_path):
    """A stream failure AFTER the real CLI consumes a metadata-tagged PM message and
    PM section event, but BEFORE the Gate, must release NO authoritative PM Buy/Sell.

    The fake stream yields the REAL PM message (with ``langgraph_node`` metadata) and
    the PM risk-section chunk exactly as production does, waits until the CLI handler
    has actually processed them (observed via the recording buffer), and only then
    raises — so pre-Gate buffering of genuinely-consumed PM content is proven.
    """
    secret = "SECRET BUY BODY."
    body = f"**Rating**: Buy\n\n{secret}"
    state = _state("Buy", body, news="")
    harness = _install(monkeypatch, tmp_path, final_state=state)
    harness["calls"].clear()  # drop the graph_init/begin from install for clean assertion

    buf = harness["buffer"]
    reports_dir = harness["reports_dir"]
    timeline = []  # every message/section event with the real .md content AT that write

    real_add = buf.add_message
    def wrapped_add(mtype, content):
        real_add(mtype, content)
        timeline.append({"kind": "message", "content": content})
    monkeypatch.setattr(buf, "add_message", wrapped_add)

    real_update = buf.update_report_section
    def wrapped_update(section_name, content):
        real_update(section_name, content)
        f = reports_dir / f"{section_name}.md"
        md = f.read_text(encoding="utf-8") if f.exists() else None
        timeline.append({"kind": "section", "section": section_name, "content": content, "md": md})
    monkeypatch.setattr(buf, "update_report_section", wrapped_update)

    from langchain_core.messages import AIMessage
    pm_msg = AIMessage(
        content=body,
        name="Portfolio Manager",
        response_metadata={"langgraph_node": "Portfolio Manager"},
    )
    risk = dict(state["risk_debate_state"])
    risk["final_trade_decision"] = body
    ident = {"company_of_interest": TICKER, "trade_date": TRADE_DATE}

    from cli import run as run_mod_local

    class PmThenCrashGraph(run_mod_local.TradingAgentsGraph):
        def stream_run(self, st, **k):
            # 1) A real-format PM MESSAGE (metadata-tagged) the CLI must consume.
            yield [pm_msg], None
            # 2) A PM risk/section event carrying the decision (CLI consumes it).
            yield (
                [],
                {
                    **ident,
                    "risk_debate_state": risk,
                    "final_trade_decision": body,
                    "market_report": state["market_report"],
                    "sentiment_report": state["sentiment_report"],
                    "news_report": state["news_report"],
                    "fundamentals_report": state["fundamentals_report"],
                    "final_rating": state.get("final_rating", ""),
                },
            )
            # 3) The CLI has now processed both events; fail BEFORE record_decision.
            raise RuntimeError("simulated mid-stream crash after PM consumption")

    monkeypatch.setattr(run_mod_local, "TradingAgentsGraph", PmThenCrashGraph)

    with pytest.raises(RuntimeError, match="after PM consumption"):
        run_mod_local.run_analysis(
            checkpoint=False,
            flags={"ticker": TICKER, "date": TRADE_DATE, "analysts": ["market", "news"],
                   "save": True, "show": False, "html": True},
        )

    # (1) The PM event was genuinely delivered AND processed by the CLI (the CLI
    # buffer/update path observed the decision-bearing content before the crash).
    assert any(e["kind"] == "section" and e.get("section") == "final_trade_decision"
               for e in timeline), "CLI must have consumed the PM section event"
    # (2) No authoritative Gate / finalization occurred.
    assert "record_decision" not in harness["calls"]
    assert "finalize" not in harness["calls"]
    # (3) NO pre-crash event released the PM body in the message area, the PM
    # section, or the real-time Markdown at that write (catches transient leaks).
    for e in timeline:
        if e["kind"] == "message":
            assert secret not in str(e["content"]), f"PM body in message area before Gate: {e}"
        if e["kind"] == "section" and e.get("section") == "final_trade_decision":
            assert secret not in str(e["content"]), f"PM body in PM section before Gate: {e}"
            if e["md"] is not None:
                assert secret not in e["md"], f"PM body in final_trade_decision.md before Gate: {e}"
    md = reports_dir / "final_trade_decision.md"
    if md.exists():
        assert secret not in md.read_text(encoding="utf-8")


def test_cli_o6_summary_and_report_options_ordering(monkeypatch, tmp_path):
    """Real forwarded-event ordering: completion → REVIEW → elapsed → O6 → options.

    Records each event via the REAL functions the CLI calls (not no-op stubs by
    name-only), so the relative order and single-occurrence counts are genuine.
    """
    order = []
    _install(monkeypatch, tmp_path, final_state=_state("Buy", "Rating: Buy", news=""))

    # Console: capture completion / REVIEW / elapsed prints in order.
    class _OrdConsole:
        def print(self, *a, **k):
            line = " ".join(str(x) for x in a)
            if "Analysis Complete" in line:
                order.append("completion")
            elif "recorded for review" in line:
                order.append("review")
            elif "elapsed" in line:
                order.append("elapsed")

    monkeypatch.setattr(run_mod, "console", _OrdConsole())

    # O6 summary: record when display_agent_summary is actually invoked.
    monkeypatch.setattr(run_mod, "display_agent_summary", lambda *a, **k: order.append("o6"))

    # Report options: record when _offer_reports is actually invoked.
    monkeypatch.setattr(run_mod, "_offer_reports", lambda *a, **k: order.append("options") or [])

    run_mod.run_analysis(
        checkpoint=False,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market", "news"],
            "save": False,
            "show": False,
            "html": False,
        },
    )

    assert order == ["completion", "review", "elapsed", "o6", "options"], order
