"""O4 Stage 2 — REAL programmatic Graph entrypoint (`propagate`) coverage (D-owned).

F#3: exercise the actual supported programmatic entrypoint
``TradingAgentsGraph.propagate(...)`` end-to-end (real graph, scripted offline
model, no network) and assert the RETURNED state/rating are Gate-authoritative —
not a lower-level ``record_decision`` call and not a hand-built final state.

Covers:
- complete valid evidence → preserved rating, final_rating == effective_rating,
  original decision-body bytes unchanged, exactly one authoritative Gate call,
  returned signal == observed Gate result.
- missing selected evidence → REVIEW (empty News report), returned signal REVIEW,
  body bytes preserved.

If the real entrypoint reveals a production defect, these tests report it; they
do not edit production code.
"""

from __future__ import annotations

import copy

import pandas as pd
import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from tests.test_graph_end_to_end import TEXT as SCRIPTED_TEXT, TRADE_DATE, ScriptedModel

TICKER = "NVDA"


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


class EmptyNewsModel(ScriptedModel):
    """ScriptedModel whose News-analyst wrap-up yields an EMPTY news report.

    Only the News analyst's tool history contains ``get_news`` (market uses
    ``get_stock_data``/``get_indicators``; fundamentals uses statement tools).
    On the FIRST tool-less (wrap-up) turn whose rendered history mentions
    ``get_news`` we return empty content, leaving ``news_report`` empty so the
    complete-state Gate must downgrade to REVIEW. Other analysts and the PM
    decision are unaffected.
    """

    news_emptied: bool = False

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        if not self.tools and not self.news_emptied:
            history = "\n".join(str(getattr(m, "content", "")) for m in messages)
            if "get_news" in history:
                self.news_emptied = True
                self._count()
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])
        return super()._generate(messages, stop, run_manager, **kwargs)


def _patch_llm(monkeypatch, model):
    from tradingagents.graph import trading_graph

    class _Client:
        def get_llm(self):
            return model

    monkeypatch.setattr(trading_graph, "create_tier_client", lambda config, tier, **k: _Client())


def _graph(tmp_path, monkeypatch, model, **config):
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph import trading_graph

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg.update(
        results_dir=str(tmp_path / "results"),
        data_cache_dir=str(tmp_path / "cache"),
        memory_log_path=str(tmp_path / "log.md"),
        **config,
    )
    _patch_llm(monkeypatch, model)
    return trading_graph.TradingAgentsGraph(config=cfg, debug=False)


def _spy_gate(monkeypatch):
    from tradingagents.agents import evidence_gate as eg

    calls = {"n": 0, "gate": None}
    real = eg.check_evidence

    def counting(state, analysts):
        calls["n"] += 1
        result = real(state, analysts)
        calls["gate"] = result
        return result

    monkeypatch.setattr(eg, "check_evidence", counting)
    return calls


def test_graph_propagate_valid_evidence_returns_gated_state(tmp_path, monkeypatch, offline):
    """Real propagate(): complete evidence preserves the authorized rating; the
    RETURNED state/rating are Gate-authoritative; one Gate evaluation."""
    calls = _spy_gate(monkeypatch)
    graph = _graph(tmp_path, monkeypatch, ScriptedModel())

    state, signal = graph.propagate(TICKER, TRADE_DATE)

    assert calls["n"] == 1, "propagate must perform exactly one authoritative Gate"
    gate = calls["gate"]
    assert gate is not None
    # Returned signal is the Gate-adjusted rating and agrees with the gate result.
    assert gate.effective_rating == signal
    assert signal == state["final_rating"] == state["effective_rating"]
    assert signal in {"Overweight", "Buy"}  # valid preserved rating
    # Original decision body is returned EXACTLY unchanged (independently
    # established expected body = the scripted model's TEXT).
    assert state["final_trade_decision"] == SCRIPTED_TEXT


def test_graph_propagate_missing_evidence_returns_review(tmp_path, monkeypatch, offline):
    """Real propagate(): empty News report → REVIEW; returned state/rating agree;
    original PM body preserved."""
    calls = _spy_gate(monkeypatch)
    graph = _graph(tmp_path, monkeypatch, EmptyNewsModel())

    state, signal = graph.propagate(TICKER, TRADE_DATE)

    assert calls["n"] == 1
    gate = calls["gate"]
    assert gate is not None
    assert signal == state["final_rating"] == state["effective_rating"] == "REVIEW", (
        f"missing news evidence must yield REVIEW; got {signal!r}"
    )
    assert gate.effective_rating == "REVIEW"
    assert gate.reason  # a diagnostic reason accompanies the REVIEW downgrade
    # The original decision body is returned EXACTLY unchanged on REVIEW too.
    assert state["final_trade_decision"] == SCRIPTED_TEXT
