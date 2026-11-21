"""O4 Stage 2 — bare ``record_decision()`` MUST gate every new authoritative write.

Corrected production contract (PR #25, ``b6b67eb``): every NEW authoritative
rating written by ``record_decision`` is judged by the Evidence Gate first —
whether or not the caller opened an execution with ``begin_checkpoint``. The
execution window only governs *reuse* (one Gate per execution; a retry reuses
the result); it is NOT an exemption from Gate evaluation. A stale
``effective_rating`` already present in state is NOT publication authorization.

These tests exercise the REAL production boundary (``record_decision``) with
real ``check_evidence`` spies and temporary I/O paths. They replace the earlier
"bare call is legacy/ungated" assertions, which the fix invalidated.
"""

from __future__ import annotations

import inspect

import pytest

from tradingagents.agents import evidence_gate as eg
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.memory import TradingMemoryLog

TICKER = "NVDA"
DATE = "2026-01-10"


def _make_graph(tmp_path, analysts=("market", "social", "news", "fundamentals")):
    """A real boundary object (no LLM); bare-call path only needs these attrs."""
    g = object.__new__(TradingAgentsGraph)
    g.config = {
        "results_dir": str(tmp_path / "results"),
        "data_cache_dir": str(tmp_path / "cache"),
        "memory_log_path": str(tmp_path / "memory.md"),
        "llm_provider": "openai",
        "deep_think_llm": "x",
        "quick_think_llm": "x",
        "backend_url": None,
    }
    g.selected_analysts = tuple(analysts)
    g._completion = None
    g._execution_active = False  # BARE call: no execution window open
    g._checkpointer_ctx = None
    g._resuming = False
    g.debug = False
    g.memory_log = TradingMemoryLog(g.config)
    return g


def _state(final_rating="Buy", body="Rating: Buy", news="News: neutral.", **extra):
    st = {
        "company_of_interest": TICKER,
        "trade_date": DATE,
        "market_report": "m",
        "sentiment_report": "s",
        "news_report": news,
        "fundamentals_report": "f",
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
        },
        "trader_investment_plan": "",
        "risk_debate_state": {
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "history": "",
        },
        "investment_plan": "",
        "final_trade_decision": body,
        "final_rating": final_rating,
    }
    st.update(extra)
    return st


def _state_log(tmp_path):
    import json

    p = (
        tmp_path
        / "results"
        / TICKER
        / "TradingAgentsStrategy_logs"
        / f"full_states_log_{DATE}.json"
    )
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _mem_entries(tmp_path):
    p = tmp_path / "memory.md"
    return (
        [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.startswith("[")]
        if p.exists()
        else []
    )


def _spy_gate(monkeypatch):
    calls = {"n": 0}
    real = eg.check_evidence

    def counting(state, analysts):
        calls["n"] += 1
        return real(state, analysts)

    monkeypatch.setattr(eg, "check_evidence", counting)
    return calls


# ---------------------------------------------------------------------------
# A — complete evidence via BARE record_decision: Gate runs, Buy preserved
# ---------------------------------------------------------------------------
def test_bare_complete_evidence_gates_and_preserves_buy(tmp_path, monkeypatch):
    g = _make_graph(tmp_path)
    assert g._execution_active is False  # genuinely a bare call
    calls = _spy_gate(monkeypatch)
    state = _state("Buy", "Rating: Buy")

    g.record_decision(TICKER, DATE, state)

    assert calls["n"] == 1, "bare record_decision MUST evaluate the Gate"
    assert state["final_rating"] == state["effective_rating"] == "Buy"
    assert state["original_rating"] == "Buy"
    assert state["final_trade_decision"] == "Rating: Buy"  # bytes preserved
    # State log + memory received the authorized rating.
    log = _state_log(tmp_path)
    assert log is not None and log["final_rating"] == "Buy"
    mem = _mem_entries(tmp_path)
    assert len(mem) == 1 and "| Buy |" in mem[0]


# ---------------------------------------------------------------------------
# B — missing selected evidence via BARE call: REVIEW, no Buy published
# ---------------------------------------------------------------------------
def test_bare_missing_evidence_gates_to_review(tmp_path, monkeypatch):
    g = _make_graph(tmp_path)
    calls = _spy_gate(monkeypatch)
    body = "**Rating**: Buy\n\nBuy NVDA."
    state = _state("Buy", body, news="")  # news empty -> REVIEW

    g.record_decision(TICKER, DATE, state)

    assert calls["n"] == 1
    assert state["final_rating"] == state["effective_rating"] == "REVIEW"
    assert state["original_rating"] == "Buy"  # original captured pre-Gate
    assert state["final_trade_decision"] == body  # body preserved
    log = _state_log(tmp_path)
    assert log is not None and log["final_rating"] == "REVIEW"
    mem = _mem_entries(tmp_path)
    assert len(mem) == 1 and "| REVIEW |" in mem[0]
    # No authoritative Buy was persisted anywhere.
    assert "| Buy |" not in (mem[0] if mem else "")


# ---------------------------------------------------------------------------
# C — invalid analyst configuration via BARE call: error propagates, no writes
# ---------------------------------------------------------------------------
def test_bare_unknown_config_aborts_no_logging_no_memory(tmp_path, monkeypatch):
    g = _make_graph(tmp_path, analysts=("market", "news", "options"))  # unknown key
    calls = _spy_gate(monkeypatch)
    state = _state("Buy", "Rating: Buy")

    with pytest.raises(ValueError):
        g.record_decision(TICKER, DATE, state)

    # Error propagates from check_evidence; it is NOT a normal REVIEW.
    assert calls["n"] == 1
    assert state.get("effective_rating") != "REVIEW"
    # No authoritative publication: no state log, no memory entry.
    assert _state_log(tmp_path) is None
    assert _mem_entries(tmp_path) == []


# ---------------------------------------------------------------------------
# D — stale effective_rating is NOT publication authorization
# ---------------------------------------------------------------------------
def test_bare_stale_effective_rating_re_gated(tmp_path, monkeypatch):
    """A stale effective_rating from an earlier completion must not authorize a
    new write: the Gate runs again on current evidence."""
    g = _make_graph(tmp_path)
    calls = _spy_gate(monkeypatch)
    # Stale authorization present in state, but current evidence is complete.
    state = _state("Buy", "Rating: Buy", effective_rating="REVIEW", original_rating="REVIEW")

    g.record_decision(TICKER, DATE, state)

    assert calls["n"] == 1, "stale effective_rating must not skip the Gate"
    # New Gate result reflects current evidence (complete -> Buy), not the stale REVIEW.
    assert state["effective_rating"] == state["final_rating"] == "Buy"
    log = _state_log(tmp_path)
    assert log is not None and log["final_rating"] == "Buy"


def test_bare_stale_buy_cannot_bypass_required_review(tmp_path, monkeypatch):
    """A stale Buy/Sell in state must NOT bypass a required REVIEW downgrade for
    a NEW completion whose current evidence is missing."""
    g = _make_graph(tmp_path)
    calls = _spy_gate(monkeypatch)
    # Stale 'Buy' authorization in state, but this completion is missing news.
    state = _state("Buy", "Rating: Buy", news="", effective_rating="Buy", original_rating="Buy")

    g.record_decision(TICKER, DATE, state)

    assert calls["n"] == 1
    assert state["effective_rating"] == "REVIEW", "stale Buy must not bypass REVIEW"
    assert state["final_rating"] == "REVIEW"
    mem = _mem_entries(tmp_path)
    assert len(mem) == 1 and "| REVIEW |" in mem[0]


# ---------------------------------------------------------------------------
# Preserved lifecycle behaviour (kept from the prior phase, still valid)
# ---------------------------------------------------------------------------
def test_record_decision_signature_and_none_return_unchanged():
    sig = inspect.signature(TradingAgentsGraph.record_decision)
    assert list(sig.parameters) == ["self", "company_name", "trade_date", "final_state"]


def test_entrypoints_that_enter_the_window():
    """propagate->checkpoint_scope->begin/end still toggles the window."""
    assert hasattr(TradingAgentsGraph, "begin_checkpoint")
    assert hasattr(TradingAgentsGraph, "end_checkpoint")
    g = object.__new__(TradingAgentsGraph)
    g._completion = None
    g._execution_active = False
    g._checkpointer_ctx = None
    g._resuming = False
    g.config = {"checkpoint_enabled": False}
    seen = {}
    with g.checkpoint_scope(TICKER, DATE):
        seen["inside"] = g._execution_active
    seen["after"] = g._execution_active
    assert seen["inside"] is True and seen["after"] is False
