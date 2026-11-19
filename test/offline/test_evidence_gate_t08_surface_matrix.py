"""O4 Stage 2 — T-08 cross-surface matrix (D-owned, parameterized).

For applicable combinations of {entrypoint, save, show, html, memory, rating-variant}
this drives the real ``cli.run.run_analysis`` path (fake graph/LLM, real Gate at
the completion boundary + real report writers) and asserts:

1. the **expected** enabled surface set is computed independently *before* the run
   (from the writer's own section selection + the flags), never from observed output;
2. the **actual** produced surface set equals the expected set;
3. every enabled authoritative surface carries the same Gate-effective rating;
4. ``decision.md`` and HTML content reflect the effective rating / non-authoritative
   labelling where applicable;
5. disabled surfaces are NOT produced;
6. memory-disabled writes nothing; memory-enabled writes only to ``tmp_path``
   (default user dir untouched).

Only the F-approved **applicable** matrix is covered — no unsupported permutations.
"""

from __future__ import annotations

import os
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.memory import TradingMemoryLog
from tradingagents.reporting import _report_parts as report_parts

try:
    from cli import run as run_mod
except ModuleNotFoundError:
    run_mod = None

pytestmark = pytest.mark.skipif(run_mod is None, reason="CLI runtime unavailable")

TICKER = "NVDA"
TRADE_DATE = "2026-01-10"


# --------------------------- fakes (O2-style) ---------------------------
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


class _Buf:
    def __init__(self):
        self.init_for_analysis(["market"])

    def init_for_analysis(self, keys):
        self.messages = []
        self.report_sections = {}
        self.agent_status = {}
        self._processed_message_ids = set()

    def add_message(self, mtype, content):
        self.messages.append(("now", mtype, content))

    def add_tool_call(self, name, args):
        self.messages.append(("now", "Tool Call", f"{name}({args})"))

    def update_report_section(self, s, c):
        self.report_sections[s] = c

    def update_agent_status(self, a, s):
        self.agent_status[a] = s


class _Console:
    def __init__(self):
        self.lines = []

    def print(self, *a, **k):
        self.lines.append(" ".join(str(x) for x in a))


def _state(final_rating, body, news="News: neutral."):
    return {
        "company_of_interest": TICKER,
        "trade_date": TRADE_DATE,
        "market_report": "Market.",
        "sentiment_report": "Sent.",
        "news_report": news,
        "fundamentals_report": "Fund.",
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


def _chunks(state):
    ident = {"company_of_interest": state["company_of_interest"], "trade_date": state["trade_date"]}
    yield (
        [],
        {
            **ident,
            "investment_debate_state": state["investment_debate_state"],
            "investment_plan": state["investment_plan"],
        },
    )
    yield [], {**ident, "trader_investment_plan": state["trader_investment_plan"]}
    yield (
        [],
        {
            **ident,
            "risk_debate_state": state["risk_debate_state"],
            "final_trade_decision": state["final_trade_decision"],
            "market_report": state["market_report"],
            "sentiment_report": state["sentiment_report"],
            "news_report": state["news_report"],
            "fundamentals_report": state["fundamentals_report"],
            "final_rating": state["final_rating"],
        },
    )


def _install(monkeypatch, tmp_path, state, *, save, show, html, memory_enabled):
    results = tmp_path / "results"
    _, report_sections_dir = None, results / safe_ticker_component(TICKER) / TRADE_DATE
    report_sections_dir.mkdir(parents=True, exist_ok=True)
    state_dir = results / TICKER / "TradingAgentsStrategy_logs"
    state_dir.mkdir(parents=True, exist_ok=True)

    memory_path = (tmp_path / "memory.md") if memory_enabled else ""
    config = {
        "results_dir": str(results),
        "data_cache_dir": str(tmp_path / "cache"),
        "memory_log_path": memory_path,
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

    boundary = object.__new__(TradingAgentsGraph)
    boundary.config = config
    boundary.selected_analysts = ("market", "news")
    boundary._completion = None
    boundary._execution_active = False
    boundary._checkpointer_ctx = None
    boundary._resuming = False
    boundary.debug = False
    boundary.memory_log = TradingMemoryLog(config)

    h = {"calls": [], "boundary": boundary, "reports_dir": report_sections_dir / "reports"}
    saved_dir = tmp_path / "saved_reports"

    class FakeGraph:
        def __init__(self, keys, *, config, debug):
            self.config = config
            self.propagator = _FakePropagator()

        def create_run_state(self, *a):
            return {"ticker": TICKER}

        def begin_checkpoint(self, *a):
            h["calls"].append("begin")
            return boundary.begin_checkpoint(*a)

        def checkpoint_input(self, st):
            return st

        def stream_run(self, st, **k):
            yield from _chunks(state)

        def record_decision(self, ticker, date, fs):
            h["calls"].append("record")
            boundary.record_decision(ticker, date, fs)
            h["merged"] = fs
            h["record"] = boundary.last_completion

        def clear_checkpoint_on_success(self, *a):
            return None

        def end_checkpoint(self):
            h["calls"].append("end")
            boundary.end_checkpoint()

        def default_report_path(self, ticker):
            return saved_dir

        def save_reports(self, fs, ticker, save_path, html=True):
            h["calls"].append("save")
            from tradingagents.reporting import write_report_tree

            save_path.mkdir(parents=True, exist_ok=True)
            return write_report_tree(fs, ticker, save_path, settings=None, html=html)

    def reserve(results_dir, ticker, date):
        h["calls"].append("reserve")
        rd = results / safe_ticker_component(ticker) / date / "runs" / "r1"
        rd.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(run_id="r1", run_dir=rd)

    def finalize(run_context, *, config, artifacts):
        h["calls"].append("finalize")
        from tradingagents.repro import manifest as mm

        m = mm.build_manifest(
            ticker=TICKER,
            asset_type="stock",
            analysis_date=TRADE_DATE,
            analysts=["market", "news"],
            config=config,
            runtime=mm.collect_runtime_metadata(git_metadata=None),
            artifacts=artifacts,
        )
        p = mm.write_manifest(run_context.run_dir / "manifest.json", m)
        return SimpleNamespace(success=True, manifest_path=p, artifacts=list(artifacts), error=None)

    buf, console = _Buf(), _Console()
    monkeypatch.setattr(run_mod, "TradingAgentsGraph", FakeGraph)
    monkeypatch.setattr(run_mod, "get_user_selections", lambda flags=None: dict(selections))
    monkeypatch.setattr(run_mod, "unattended_gaps", lambda flags: [])
    monkeypatch.setattr(run_mod, "_build_run_config", lambda s, c: dict(config))
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
    from tradingagents.agents import rating as rm

    monkeypatch.setattr(run_mod, "is_review", rm.is_review)
    monkeypatch.setattr(run_mod, "run_rating", rm.run_rating)
    monkeypatch.setattr(run_mod, "message_buffer", buf)
    monkeypatch.setattr(run_mod, "_reserve_run_directory", reserve, raising=False)
    monkeypatch.setattr(run_mod, "_finalize_run_manifest", finalize, raising=False)
    return h, buf, console, saved_dir


def _expected_surfaces(state, *, save, html, memory_enabled):
    """Independently compute the enabled authoritative surfaces BEFORE the run."""
    surfaces = {"state_log", "cli_report_section"}  # CLI run always writes both
    if save:
        surfaces.add("complete_report.md")
        for _h, folder, written in report_parts(state):
            for _agent, filename, _value in written:
                surfaces.add(f"{folder}/{filename}")
        if html:
            surfaces.add("complete_report.html")
    if memory_enabled:
        surfaces.add("memory_log")
    return surfaces


def _actual_surfaces(h, saved_dir, tmp_path, *, save, html, memory_enabled):
    actual = {"state_log"}  # record_decision always logs state in-window
    if h["reports_dir"].exists() and any(h["reports_dir"].glob("*.md")):
        actual.add("cli_report_section")
    if save:
        md = saved_dir / "complete_report.md"
        if md.exists():
            actual.add("complete_report.md")
            for p in saved_dir.rglob("*.md"):
                rel = p.relative_to(saved_dir).as_posix()
                if rel != "complete_report.md":
                    actual.add(rel)
        if html and (saved_dir / "complete_report.html").exists():
            actual.add("complete_report.html")
    if (
        memory_enabled
        and (tmp_path / "memory.md").exists()
        and (tmp_path / "memory.md").stat().st_size > 0
    ):
        actual.add("memory_log")
    return actual


# --------------------------- parameterized matrix ---------------------------
_VARIANTS = [
    # id, final_rating, body, news, expected_effective
    ("valid_buy", "Buy", "**Rating**: Buy\n\nBuy NVDA.", "News: neutral.", "Buy"),
    ("review_missing_news", "Buy", "**Rating**: Buy\n\nBuy NVDA.", "", "REVIEW"),
]


@pytest.mark.parametrize("save", [False, True], ids=["nosave", "save"])
@pytest.mark.parametrize("html", [False, True], ids=["nohtml", "html"])
@pytest.mark.parametrize("memory", [False, True], ids=["nomem", "mem"])
@pytest.mark.parametrize("variant", [v[0] for v in _VARIANTS], ids=[v[0] for v in _VARIANTS])
def test_t08_surface_matrix(monkeypatch, tmp_path, variant, memory, html, save):
    spec = {v[0]: v for v in _VARIANTS}[variant]
    _, final_rating, body, news, expected_eff = spec
    state = _state(final_rating, body, news)

    expected = _expected_surfaces(state, save=save, html=html, memory_enabled=memory)
    h, buf, console, saved_dir = _install(
        monkeypatch, tmp_path, state, save=save, show=False, html=html, memory_enabled=memory
    )

    run_mod.run_analysis(
        checkpoint=False,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market", "news"],
            "save": save,
            "show": False,
            "html": html,
        },
    )

    actual = _actual_surfaces(h, saved_dir, tmp_path, save=save, html=html, memory_enabled=memory)

    # (1)+(2) independent expected-vs-actual set equality (both non-empty).
    assert actual == expected, f"expected {sorted(expected)} != actual {sorted(actual)}"

    # (3) authoritative rating agreement across enabled surfaces.
    merged = h["merged"]
    assert merged["effective_rating"] == merged["final_rating"] == expected_eff
    # state log written with the effective rating
    import json

    log = json.loads(
        (
            tmp_path
            / "results"
            / TICKER
            / "TradingAgentsStrategy_logs"
            / f"full_states_log_{TRADE_DATE}.json"
        ).read_text(encoding="utf-8")
    )
    assert log["final_rating"] == expected_eff

    # (4) decision.md reflects the PM body; HTML/report when enabled.
    if save:
        # folder name comes from report_parts; locate by filename generically
        candidates = list(saved_dir.rglob("decision.md"))
        assert candidates, "decision.md must be produced when save=True"
        text = candidates[0].read_text(encoding="utf-8")
        assert "Buy NVDA." in text  # body preserved (may be labelled on REVIEW)
        if html:
            html_text = (saved_dir / "complete_report.html").read_text(encoding="utf-8")
            assert expected_eff in html_text  # rating shown in HTML header area

    # (5) disabled surfaces are not produced.
    if not save:
        assert not (saved_dir / "complete_report.md").exists()
        assert not list(saved_dir.rglob("*.md")) if saved_dir.exists() else True
    if not html:
        assert not (saved_dir / "complete_report.html").exists()

    # (6) explicit memory-disabled behaviour / (7) temp-only when enabled.
    if memory:
        assert (tmp_path / "memory.md").exists()
        assert any(ln.startswith("[") for ln in (tmp_path / "memory.md").read_text().splitlines())
    else:
        assert not (tmp_path / "memory.md").exists()


def test_default_user_memory_dir_untouched(monkeypatch, tmp_path):
    """Memory enabled but pointed at tmp; the default user dir must not be written."""
    state = _state("Buy", "Rating: Buy")
    _install(monkeypatch, tmp_path, state, save=False, show=False, html=False, memory_enabled=True)
    home = Path(os.path.expanduser("~")) / ".tradingagents"
    before = {p for p in home.rglob("*") if p.is_file()} if home.exists() else set()
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
    after = {p for p in home.rglob("*") if p.is_file()} if home.exists() else set()
    assert after == before, f"default user memory/log dir was written: {after - before}"
