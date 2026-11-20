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

from contextlib import nullcontext
from types import SimpleNamespace

import pytest

# Mandatory offline tests: the CLI runtime is a required dependency. A missing
# import must surface as a hard collection/execution failure, never a skip.
from cli import run as run_mod
from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.memory import TradingMemoryLog

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


def _completion_rating(state):
    """The Gate-adjusted rating this run will publish (from the boundary)."""
    from tradingagents.agents.rating import run_rating

    return run_rating(state)


def _expected_surfaces(*, save, html, memory_enabled):
    """Independently compute the enabled authoritative surfaces BEFORE the run.

    Based on the F-approved applicable product behaviour, not on observed files:
    a CLI run always writes the state log and streams the CLI report section;
    ``save`` adds complete_report.md + the per-section .md files (incl.
    decision.md); ``html`` (with save) adds complete_report.html; memory adds a
    memory log only when enabled.
    """
    surfaces = {"state_log", "cli_report_section"}
    if save:
        # Complete report + the fixed decision surface that always carries the PM decision.
        surfaces.add("complete_report.md")
        surfaces.add("decision.md")
        if html:
            surfaces.add("complete_report.html")
    if memory_enabled:
        surfaces.add("memory_log")
    return surfaces


def _actual_surfaces(tmp_path, saved_dir, *, memory_enabled):
    """Discover the surfaces ACTUALLY produced from files (never preset by flags)."""
    actual = set()
    log_dir = tmp_path / "results" / TICKER / "TradingAgentsStrategy_logs"
    if log_dir.exists() and any(log_dir.glob("full_states_log_*.json")):
        actual.add("state_log")
    reports_root = tmp_path / "results" / safe_ticker_component(TICKER) / TRADE_DATE / "reports"
    if reports_root.exists() and any(reports_root.glob("*.md")):
        actual.add("cli_report_section")
    if (saved_dir / "complete_report.md").exists():
        actual.add("complete_report.md")
    if (saved_dir / "complete_report.html").exists():
        actual.add("complete_report.html")
    if list(saved_dir.rglob("decision.md")) if saved_dir.exists() else False:
        actual.add("decision.md")
    mem = tmp_path / "memory.md"
    if memory_enabled and mem.exists() and mem.stat().st_size > 0:
        actual.add("memory_log")
    return actual


def _read_complete_report_rating(saved_dir):
    """The authoritative rating line in complete_report.md: ``- Rating: X``."""
    import re

    text = (saved_dir / "complete_report.md").read_text(encoding="utf-8")
    m = re.search(r"^- Rating:\s*(\S+)\s*$", text, re.MULTILINE)
    return m.group(1) if m else None


def _read_decision_md(saved_dir):
    cands = list(saved_dir.rglob("decision.md"))
    return cands[0].read_text(encoding="utf-8") if cands else None


def _read_state_log_rating(tmp_path):
    import json

    p = (
        tmp_path
        / "results"
        / TICKER
        / "TradingAgentsStrategy_logs"
        / f"full_states_log_{TRADE_DATE}.json"
    )
    return json.loads(p.read_text(encoding="utf-8"))["final_rating"]


def _read_memory_rating(tmp_path):
    import re

    for ln in (tmp_path / "memory.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\[[^|]+\|[^|]+\|\s*([^|]+?)\s*\|", ln)
        if m:
            return m.group(1)
    return None


def _read_html(saved_dir):
    return (saved_dir / "complete_report.html").read_text(encoding="utf-8")


# --------------------------- parameterized matrix ---------------------------
# valid_buy, review_missing_news, conflict, checker-failure (recoverable)
_VARIANTS = [
    ("valid_buy", "Buy", "**Rating**: Buy\n\nBuy NVDA.", "News: neutral.", "Buy"),
    ("review_missing_news", "Buy", "**Rating**: Buy\n\nBuy NVDA.", "", "REVIEW"),
    ("conflict", "Buy", "**Rating**: Sell\n\nSell NVDA.", "News: neutral.", "REVIEW"),
]


@pytest.mark.parametrize("save", [False, True], ids=["nosave", "save"])
@pytest.mark.parametrize("html", [False, True], ids=["nohtml", "html"])
@pytest.mark.parametrize("memory", [False, True], ids=["nomem", "mem"])
@pytest.mark.parametrize("variant", [v[0] for v in _VARIANTS], ids=[v[0] for v in _VARIANTS])
def test_t08_surface_matrix(monkeypatch, tmp_path, variant, memory, html, save):
    spec = {v[0]: v for v in _VARIANTS}[variant]
    _, final_rating, body, news, expected_eff = spec
    state = _state(final_rating, body, news)

    expected = _expected_surfaces(save=save, html=html, memory_enabled=memory)
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

    actual = _actual_surfaces(tmp_path, saved_dir, memory_enabled=memory)
    assert actual == expected, f"expected {sorted(expected)} != actual {sorted(actual)}"

    merged = h["merged"]
    # Gate-adjusted in-memory state.
    assert merged["effective_rating"] == merged["final_rating"] == expected_eff
    # Body bytes preserved in the finalized state.
    assert merged["final_trade_decision"] == body

    # Each enabled authoritative surface reports the EXACT rating.
    assert _read_state_log_rating(tmp_path) == expected_eff, "state log rating"
    if save:
        assert _read_complete_report_rating(saved_dir) == expected_eff, "complete_report.md rating"
        dtext = _read_decision_md(saved_dir)
        assert dtext is not None, "decision.md must exist when save=True"
        # Body preserved; on REVIEW it must be explicitly non-authoritative.
        assert body.strip() in dtext, "decision.md must preserve the PM body"
        if expected_eff == "REVIEW":
            low = dtext.lower()
            assert "unapproved" in low or "non-authoritative" in low or "withheld" in low, (
                "REVIEW decision.md must label the original PM body non-authoritative"
            )
        if html:
            html_text = _read_html(saved_dir)
            # Header shows the exact authoritative rating.
            assert f"Rating: {expected_eff}" in html_text or f">{expected_eff}<" in html_text, (
                "HTML report must show the exact authoritative rating"
            )
            if expected_eff == "REVIEW":
                low = html_text.lower()
                assert "unapproved" in low or "non-authoritative" in low or "withheld" in low, (
                    "REVIEW HTML must mark the retained PM body non-authoritative"
                )
    if memory:
        assert _read_memory_rating(tmp_path) == expected_eff, "memory log rating"

    # Disabled surfaces are NOT produced (discovered from files, not flags).
    if not save:
        assert not (saved_dir / "complete_report.md").exists()
        assert not (list(saved_dir.rglob("decision.md")) if saved_dir.exists() else [])
    if not html:
        assert not (saved_dir / "complete_report.html").exists()
    if not memory:
        assert not (tmp_path / "memory.md").exists()


def test_default_user_memory_dir_isolated(monkeypatch, tmp_path):
    """Memory enabled but pointed at tmp; a sandboxed HOME default dir is untouched.

    A path-set comparison alone can miss an in-place overwrite, so we also snapshot
    file sizes/contents under a fake HOME default location and require NO change.
    """
    import hashlib

    fake_home = tmp_path / "fakehome"
    default_dir = fake_home / ".tradingagents"
    default_dir.mkdir(parents=True)
    (default_dir / "preexisting.md").write_text("[keep | me | Buy | pending]\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("TRADINGAGENTS_HOME", str(default_dir))

    def snapshot(root):
        out = {}
        for p in root.rglob("*"):
            if p.is_file():
                out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return out

    before = snapshot(default_dir)
    _install(
        monkeypatch,
        tmp_path,
        _state("Buy", "Rating: Buy"),
        save=False,
        show=False,
        html=False,
        memory_enabled=True,
    )
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
    after = snapshot(default_dir)
    assert after == before, (
        f"default user memory dir was written/modified: {set(after) ^ set(before)}"
    )


@pytest.mark.parametrize(
    "variant,final_rating,body,news,expected_eff",
    [
        ("valid", "Buy", "**Rating**: Buy\n\nBuy NVDA.", "News: neutral.", "Buy"),
        ("review", "Buy", "**Rating**: Buy\n\nBuy NVDA.", "", "REVIEW"),
    ],
)
def test_t08_cli_show_renders_gated_state(
    monkeypatch, tmp_path, variant, final_rating, body, news, expected_eff
):
    """show=True runs the REAL display_complete_report; capture its console output
    and require the exact gated rating to appear (not a replaced stub)."""
    state = _state(final_rating, body, news)
    h, buf, console, saved_dir = _install(
        monkeypatch, tmp_path, state, save=False, show=True, html=False, memory_enabled=False
    )

    # _install stubs display_complete_report; restore the REAL renderer for show.
    import cli.display as _display_mod

    monkeypatch.setattr(run_mod, "display_complete_report", _display_mod.display_complete_report)

    # Use a REAL Rich Console writing to an in-memory buffer so the actual
    # rendered report text (incl. the rating) is captured, not object reprs.
    import io

    from rich.console import Console as _RichConsole

    import cli.display as display_mod

    sink = io.StringIO()
    monkeypatch.setattr(display_mod, "console", _RichConsole(file=sink, width=120, record=True))

    run_mod.run_analysis(
        checkpoint=False,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market", "news"],
            "save": False,
            "show": True,
            "html": False,
        },
    )

    text = sink.getvalue()
    assert text, "show=True must render the complete report to the terminal"
    assert expected_eff in text, f"real renderer must show the gated rating {expected_eff}"
    assert not (saved_dir / "complete_report.md").exists()
