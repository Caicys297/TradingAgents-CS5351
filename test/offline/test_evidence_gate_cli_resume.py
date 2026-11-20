"""O4 Stage 2 — REAL CLI Checkpoint/Resume integration test (D-owned).

Produces a GENUINE checkpoint by running the real graph (scripted offline model,
no network) and interrupting it mid-run, then drives the REAL CLI resume path
(``cli.run.run_analysis(checkpoint=True)``) which detects the saved step via the
real ``SqliteSaver``, streams the resumed graph, gates the complete restored
state at the completion boundary, and publishes PM text only after authorization.

No checkpoint state is hand-reconstructed: it is written by an actual
``propagate``/``checkpoint_scope`` run and restored through the supported CLI
path. External vendors/LLM are replaced by the repository's scripted model and
offline router (the same technique as ``tests/test_graph_end_to_end.py``).
"""

from __future__ import annotations

import copy
import json
from contextlib import nullcontext
from types import SimpleNamespace

import pandas as pd
import pytest

# Mandatory offline tests: the CLI runtime is a required dependency. A missing
# import must surface as a hard collection/execution failure, never a skip.
from cli import run as run_mod
from tests.test_graph_end_to_end import TRADE_DATE, ScriptedModel

TICKER = "NVDA"


# ---------------------------------------------------------------------------
# Offline graph plumbing (mirrors tests/test_graph_end_to_end.py)
# ---------------------------------------------------------------------------
@pytest.fixture
def offline(monkeypatch):
    from tradingagents.agents import context
    from tradingagents.agents.analysts import sentiment_analyst
    from tradingagents.dataflows import router
    from tradingagents.dataflows.vendors.yahoo import market as yahoo_market, snapshot

    for method, vendors in router.VENDOR_METHODS.items():
        for vendor in vendors:
            monkeypatch.setitem(vendors, vendor, lambda *a, _m=method, **k: f"{_m} data")
    prices = pd.DataFrame(
        {
            "Date": pd.bdate_range(end=TRADE_DATE, periods=60),
            "Open": 100.0,
            "High": 101.0,
            "Low": 99.0,
            "Close": 100.5,
            "Volume": 1_000_000,
        }
    )
    monkeypatch.setattr(snapshot, "load_ohlcv", lambda *a, **k: prices.copy())
    monkeypatch.setattr(sentiment_analyst, "fetch_stocktwits_messages", lambda *a, **k: "no posts")
    monkeypatch.setattr(sentiment_analyst, "fetch_reddit_posts", lambda *a, **k: "no posts")
    monkeypatch.setattr(
        yahoo_market.yf, "Ticker", lambda s: type("T", (), {"info": {"longName": "NVIDIA"}})()
    )
    context._identity.cache_clear()
    return True


def _patch_llm(monkeypatch, model):
    from tradingagents.graph import trading_graph

    class _Client:
        def get_llm(self):
            return model

    monkeypatch.setattr(trading_graph, "create_tier_client", lambda config, tier, **k: _Client())


def _cli_config(tmp_path):
    from tradingagents.default_config import DEFAULT_CONFIG

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg.update(
        results_dir=str(tmp_path / "results"),
        data_cache_dir=str(tmp_path / "cache"),
        memory_log_path=str(tmp_path / "log.md"),
    )
    return cfg


def _produce_interrupted_checkpoint(tmp_path, monkeypatch, offline):
    """Run the REAL graph with a model that fails past the analysts, leaving a
    genuine SqliteSaver checkpoint on disk for the same ticker/date/signature."""
    from tradingagents.graph import trading_graph
    from tradingagents.graph.checkpointer import checkpoint_step

    cfg = _cli_config(tmp_path)
    cfg["checkpoint_enabled"] = True
    _patch_llm(monkeypatch, ScriptedModel(fail_at=12))
    g = trading_graph.TradingAgentsGraph(config=cfg, debug=False)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        g.propagate(TICKER, TRADE_DATE)
    sig = g._run_signature("stock")
    step = checkpoint_step(cfg["data_cache_dir"], TICKER, TRADE_DATE, sig)
    assert step is not None, "a real checkpoint must have been written"
    return step


class _Buf:
    def __init__(self):
        self.init_for_analysis(["market"])

    def init_for_analysis(self, keys):
        self.messages, self.report_sections, self.agent_status = [], {}, {}
        self._processed_message_ids = set()
        self.section_history = []

    def add_message(self, t, c):
        self.messages.append(("now", t, c))

    def add_tool_call(self, n, a):
        self.messages.append(("now", "Tool Call", f"{n}({a})"))

    def update_report_section(self, s, c):
        self.report_sections[s] = c
        self.section_history.append((s, c))

    def update_agent_status(self, a, s):
        self.agent_status[a] = s


class _Console:
    def __init__(self):
        self.lines = []

    def print(self, *a, **k):
        self.lines.append(" ".join(str(x) for x in a))


def _install_cli(monkeypatch, tmp_path, buf, console):
    """Patch only presentation/O2/selection plumbing; keep the REAL graph + Gate."""
    from tradingagents.graph import trading_graph as tg

    # capture the real LastCompletion inside the window from the real boundary
    captured = {}

    cfg = _cli_config(tmp_path)

    selections = {
        "ticker": TICKER,
        "analysis_date": TRADE_DATE,
        "asset_type": "stock",
        "analysts": [
            SimpleNamespace(value="market"),
            SimpleNamespace(value="social"),
            SimpleNamespace(value="news"),
            SimpleNamespace(value="fundamentals"),
        ],
    }

    # Wrap the real record_decision to snapshot last_completion in-window.
    real_record = tg.TradingAgentsGraph.record_decision

    def spying_record(self, ticker, date, final_state):
        captured["active_before"] = self._execution_active
        real_record(self, ticker, date, final_state)
        captured["last_completion"] = self.last_completion

    monkeypatch.setattr(tg.TradingAgentsGraph, "record_decision", spying_record)

    def reserve(results_dir, ticker, date):
        # Mirror the current production _reserve_run_directory: results_dir is the
        # config results root (str), and the ticker/date/runs/<id> path is built
        # inside. Keep it deterministic for the test.
        from pathlib import Path

        from tradingagents.dataflows.symbols import safe_ticker_component

        rd = Path(results_dir) / safe_ticker_component(ticker) / date / "runs" / "r1"
        rd.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(run_id="r1", run_dir=rd)

    def finalize(run_context, *, config, artifacts):
        from tradingagents.repro import manifest as mm

        m = mm.build_manifest(
            ticker=TICKER,
            asset_type="stock",
            analysis_date=TRADE_DATE,
            analysts=config.get("analysts", ["market"]),
            config=config,
            runtime=mm.collect_runtime_metadata(git_metadata=None),
            artifacts=artifacts,
        )
        p = mm.write_manifest(run_context.run_dir / "manifest.json", m)
        return SimpleNamespace(success=True, manifest_path=p, artifacts=list(artifacts), error=None)

    monkeypatch.setattr(run_mod, "get_user_selections", lambda flags=None: dict(selections))
    monkeypatch.setattr(run_mod, "unattended_gaps", lambda flags: [])
    monkeypatch.setattr(
        run_mod, "_build_run_config", lambda s, checkpoint: {**cfg, "checkpoint_enabled": True}
    )
    monkeypatch.setattr(run_mod, "create_layout", lambda: SimpleNamespace())
    monkeypatch.setattr(run_mod, "Live", lambda *a, **k: nullcontext())
    monkeypatch.setattr(run_mod, "update_display", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "update_analyst_statuses", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "update_research_team_status", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "display_agent_summary", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "display_complete_report", lambda *a, **k: None)
    monkeypatch.setattr(run_mod, "console", console)
    monkeypatch.setattr(run_mod, "message_buffer", buf)
    monkeypatch.setattr(run_mod, "_reserve_run_directory", reserve, raising=False)
    monkeypatch.setattr(run_mod, "_finalize_run_manifest", finalize, raising=False)
    return captured


def test_real_cli_resume_from_genuine_checkpoint(tmp_path, monkeypatch, offline):
    """A real checkpoint is written by an interrupted real run, then restored via
    the real CLI path; the resumed completion gates fresh and publishes post-gate."""
    step = _produce_interrupted_checkpoint(tmp_path, monkeypatch, offline)
    assert step is not None

    # Resume run: a *fresh* scripted model that completes the run.
    _patch_llm(monkeypatch, ScriptedModel())

    # Spy the real Gate to prove a fresh evaluation occurs on resume.
    from tradingagents.agents import evidence_gate as eg

    gate_calls = {"n": 0}
    real_check = eg.check_evidence

    def counting(state, analysts):
        gate_calls["n"] += 1
        return real_check(state, analysts)

    monkeypatch.setattr(eg, "check_evidence", counting)

    buf, console = _Buf(), _Console()
    captured = _install_cli(monkeypatch, tmp_path, buf, console)

    run_mod.run_analysis(
        checkpoint=True,
        flags={
            "ticker": TICKER,
            "date": TRADE_DATE,
            "analysts": ["market", "social", "news", "fundamentals"],
            "save": False,
            "show": False,
            "html": False,
        },
    )

    # Resume entered the window and gated a fresh completion.
    assert captured.get("active_before") is True, "resume must run inside the execution window"
    rec = captured.get("last_completion")
    assert rec is not None, "the resumed completion must produce a Gate result"
    # Fresh Gate result reflects the restored evidence (valid -> Overweight).
    assert rec.gate.verdict == "valid"
    assert rec.gate.effective_rating in {"Overweight", "Buy"}
    # PM output published only after authorization (post-gate labelled/present).
    ftk = [c for (s, c) in buf.section_history if s == "final_trade_decision"]
    assert any("Portfolio Manager Decision" in c for c in ftk)
    # A state log was written with the gated rating.
    log = json.loads(
        (
            tmp_path
            / "results"
            / TICKER
            / "TradingAgentsStrategy_logs"
            / f"full_states_log_{TRADE_DATE}.json"
        ).read_text(encoding="utf-8")
    )
    assert log["final_rating"] == rec.gate.effective_rating
    # Fresh authoritative Gate evaluation on resume (not reused from the
    # interrupted run, which never completed/published).
    assert gate_calls["n"] == 1, "resume must perform a fresh Gate evaluation"
    assert rec.published is True
