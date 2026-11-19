"""O4 Stage 2 — T-21 runtime observation + execution-lifecycle integration (D-owned).

Drives the REAL production completion boundary in ``trading_graph.py`` (PR #25,
commit ``e0ffa3a``) without constructing the full LLM graph:

- the object is built with ``object.__new__(TradingAgentsGraph)`` and only the
  attributes the boundary touches are set (``config``, ``memory_log``,
  ``selected_analysts``, ``_completion``, ``_execution_active``);
- ``_log_state`` writes to an isolated ``tmp_path`` ``results_dir``;
- ``store_decision`` is the real ``TradingMemoryLog`` writing to a ``tmp_path``.

This exercises the production Gate-at-completion-boundary contract, the
``last_completion`` observation record, same-execution dedup / retry reuse,
new-execution and Resume re-evaluation, and persistence-failure handling.

No fake Gate/observation API is introduced; ``check_evidence`` is spied where a
call-count assertion is required.
"""

from __future__ import annotations

import pytest
from o4_stage2_fixtures import (
    ALL_ANALYSTS,
)

from tradingagents.agents import evidence_gate as eg
from tradingagents.agents.evidence_gate import VERDICT_REVIEW, VERDICT_VALID
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.memory import TradingMemoryLog

_TICKER = "NVDA"
_DATE = "2026-01-10"


def _full_state(final_rating="Buy", body="Rating: Buy", news="News: neutral.", **extra):
    """A complete AgentState-shaped mapping (requirements for _log_state)."""
    st = {
        "company_of_interest": _TICKER,
        "trade_date": _DATE,
        "market_report": "Market: ok.",
        "sentiment_report": "Sentiment: ok.",
        "news_report": news,
        "fundamentals_report": "Fundamentals: ok.",
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


def _make_graph(tmp_path, analysts=ALL_ANALYSTS):
    """Construct a boundary-testable TradingAgentsGraph without LLM clients."""
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
    g._execution_active = False
    g._checkpointer_ctx = None
    g._resuming = False
    g.debug = False
    g.memory_log = TradingMemoryLog(g.config)
    return g


def _begin(g):
    """Enter the execution window without the checkpoint machinery.

    ``begin_checkpoint`` resets ``_completion`` and sets ``_execution_active``;
    with checkpoint disabled it returns early, so it is safe offline.
    """
    return g.begin_checkpoint(_TICKER, _DATE)


def _memory_entries(tmp_path):
    path = tmp_path / "memory.md"
    if not path.exists():
        return []
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("[")]


# ---------------------------------------------------------------------------
# T-21 — runtime observation lifecycle
# ---------------------------------------------------------------------------
def test_t21_last_completion_none_before_gate(tmp_path):
    g = _make_graph(tmp_path)
    _begin(g)
    assert g.last_completion is None  # before any Gate in this execution
    g.end_checkpoint()


def test_t21_last_completion_populated_after_gate(tmp_path):
    g = _make_graph(tmp_path)
    _begin(g)
    state = _full_state("Buy", "Rating: Buy")
    g.record_decision(_TICKER, _DATE, state)

    rec = g.last_completion
    assert rec is not None
    # gate / original_rating / published are present
    assert rec.gate.verdict == VERDICT_VALID
    assert rec.gate.effective_rating == "Buy"
    assert rec.original_rating == "Buy"  # trusted pre-Gate rating
    assert rec.published is True  # persistence completed
    # Gate-adjusted state agrees with the published effective rating
    assert state["final_rating"] == state["effective_rating"] == rec.gate.effective_rating == "Buy"
    assert state["original_rating"] == "Buy"
    assert state["final_trade_decision"] == "Rating: Buy"  # bytes preserved
    g.end_checkpoint()


def test_t21_review_verdict_and_reason_observed(tmp_path):
    g = _make_graph(tmp_path)
    _begin(g)
    state = _full_state("Buy", "Rating: Buy", news="")  # missing news -> REVIEW
    g.record_decision(_TICKER, _DATE, state)
    rec = g.last_completion
    assert rec.gate.verdict == VERDICT_REVIEW
    assert rec.gate.effective_rating == "REVIEW"
    assert rec.gate.reason  # non-empty diagnostic reason
    assert rec.gate.statuses.get("news_report") == "missing"
    assert state["effective_rating"] == "REVIEW"
    assert state["original_rating"] == "Buy"  # original captured before overwrite
    g.end_checkpoint()


def test_t21_last_completion_cleared_after_end_checkpoint(tmp_path):
    g = _make_graph(tmp_path)
    _begin(g)
    g.record_decision(_TICKER, _DATE, _full_state())
    assert g.last_completion is not None
    g.end_checkpoint()
    assert g.last_completion is None  # cleared after the window


# ---------------------------------------------------------------------------
# B — duplicate completion within the same execution
# ---------------------------------------------------------------------------
def test_duplicate_completion_single_gate_eval(tmp_path, monkeypatch):
    g = _make_graph(tmp_path)
    _begin(g)
    calls = {"n": 0}
    real = eg.check_evidence

    def counting(state, analysts):
        calls["n"] += 1
        return real(state, analysts)

    monkeypatch.setattr(eg, "check_evidence", counting)

    state = _full_state("Buy", "Rating: Buy")
    g.record_decision(_TICKER, _DATE, state)
    first_original = g.last_completion.original_rating
    # Duplicate completion callbacks in the SAME execution:
    g.record_decision(_TICKER, _DATE, state)
    g.record_decision(_TICKER, _DATE, state)

    assert calls["n"] == 1, "duplicate completion must not re-evaluate the Gate"
    assert g.last_completion.original_rating == first_original == "Buy"
    # No duplicated publication: exactly one memory entry for ticker+date.
    assert len(_memory_entries(tmp_path)) == 1
    g.end_checkpoint()


# ---------------------------------------------------------------------------
# C — persistence failure + same-execution retry
# ---------------------------------------------------------------------------
def test_state_log_failure_retry_reuses_gate_no_duplicate(tmp_path, monkeypatch):
    g = _make_graph(tmp_path)
    _begin(g)
    calls = {"n": 0}
    real = eg.check_evidence
    monkeypatch.setattr(
        eg, "check_evidence", lambda s, a: (calls.__setitem__("n", calls["n"] + 1), real(s, a))[1]
    )

    state = _full_state("Buy", "Rating: Buy")

    # Fail the state log on the first attempt.
    real_log = g._log_state

    def boom_log(trade_date, fs):
        raise OSError("simulated state-log failure")

    monkeypatch.setattr(g, "_log_state", boom_log)
    with pytest.raises(OSError):
        g.record_decision(_TICKER, _DATE, state)
    assert calls["n"] == 1  # gate ran once
    assert g.last_completion is not None  # result retained for retry
    assert g.last_completion.published is False

    # Retry same execution: restore real log; gate must NOT re-run.
    monkeypatch.setattr(g, "_log_state", real_log)
    g.record_decision(_TICKER, _DATE, state)
    assert calls["n"] == 1, "same-execution retry must reuse the valid Gate result"
    assert g.last_completion.published is True
    assert g.last_completion.original_rating == "Buy"  # not recaptured from downgraded
    assert len(_memory_entries(tmp_path)) == 1  # no duplicate persistence
    g.end_checkpoint()


def test_memory_failure_retry_reuses_gate(tmp_path, monkeypatch):
    g = _make_graph(tmp_path)
    _begin(g)
    calls = {"n": 0}
    real = eg.check_evidence
    monkeypatch.setattr(
        eg, "check_evidence", lambda s, a: (calls.__setitem__("n", calls["n"] + 1), real(s, a))[1]
    )

    state = _full_state("Buy", "Rating: Buy")
    real_store = g.memory_log.store_decision

    def boom_store(**kw):
        raise OSError("simulated memory-write failure")

    monkeypatch.setattr(g.memory_log, "store_decision", boom_store)
    with pytest.raises(OSError):
        g.record_decision(_TICKER, _DATE, state)
    assert calls["n"] == 1
    assert g.last_completion.published is False

    monkeypatch.setattr(g.memory_log, "store_decision", real_store)
    g.record_decision(_TICKER, _DATE, state)
    assert calls["n"] == 1  # reused
    assert g.last_completion.published is True
    assert len(_memory_entries(tmp_path)) == 1
    g.end_checkpoint()


def test_retry_does_not_recapture_original_from_downgraded_review(tmp_path):
    """Missing evidence -> REVIEW; retry keeps the true pre-gate original (Buy)."""
    g = _make_graph(tmp_path)
    _begin(g)
    state = _full_state("Buy", "Rating: Buy", news="")  # downgraded to REVIEW
    g.record_decision(_TICKER, _DATE, state)
    assert g.last_completion.gate.effective_rating == "REVIEW"
    assert g.last_completion.original_rating == "Buy"
    # Mutate final_rating as if a prior step had published REVIEW, then retry.
    state["final_rating"] = "REVIEW"
    g.record_decision(_TICKER, _DATE, state)
    assert g.last_completion.original_rating == "Buy", (
        "retry must not recapture original_rating from the downgraded final_rating"
    )
    g.end_checkpoint()


# ---------------------------------------------------------------------------
# D — new execution on the same Graph instance -> fresh Gate
# ---------------------------------------------------------------------------
def test_new_execution_fresh_gate_no_leak(tmp_path, monkeypatch):
    g = _make_graph(tmp_path)
    calls = {"n": 0}
    real = eg.check_evidence
    monkeypatch.setattr(
        eg, "check_evidence", lambda s, a: (calls.__setitem__("n", calls["n"] + 1), real(s, a))[1]
    )

    # Execution 1
    _begin(g)
    g.record_decision(_TICKER, _DATE, _full_state("Buy", "Rating: Buy"))
    assert g.last_completion is not None
    first = g.last_completion
    g.end_checkpoint()
    assert g.last_completion is None  # cleared

    # Execution 2 (same instance, same ticker/date) -> fresh evaluation
    _begin(g)
    assert g.last_completion is None  # reset by begin_checkpoint
    g.record_decision(_TICKER, _DATE, _full_state("Sell", "Rating: Sell"))
    assert calls["n"] == 2  # one per execution
    assert g.last_completion is not first  # no stale record leak
    assert g.last_completion.original_rating == "Sell"
    g.end_checkpoint()


def test_begin_checkpoint_resets_completion_before_gate(tmp_path):
    g = _make_graph(tmp_path)
    _begin(g)
    g.record_decision(_TICKER, _DATE, _full_state("Buy", "Rating: Buy"))
    assert g.last_completion is not None
    # A new begin on the same instance must forget the prior execution's record.
    _begin(g)
    assert g.last_completion is None
    g.end_checkpoint()


# ---------------------------------------------------------------------------
# E — Resume: same instance re-evaluates on complete restored state
# ---------------------------------------------------------------------------
def test_resume_reaches_gate_with_restored_reports(tmp_path, monkeypatch):
    """A resumed execution re-evaluates the Gate on the complete restored state.

    We model 'resume' as a second execution window on the same instance whose
    finalized state carries all restored report fields; the Gate must see them
    (not a bare delta) and re-judge.
    """
    g = _make_graph(tmp_path)
    calls = {"n": 0}
    real = eg.check_evidence
    monkeypatch.setattr(
        eg, "check_evidence", lambda s, a: (calls.__setitem__("n", calls["n"] + 1), real(s, a))[1]
    )

    _begin(g)  # execution 1 (interrupted before completion -> no record)
    g.end_checkpoint()
    assert g.last_completion is None

    _begin(g)  # resume -> execution 2
    restored = _full_state("Overweight", "Rating: Overweight")  # all reports present
    g.record_decision(_TICKER, _DATE, restored)
    assert calls["n"] == 1
    rec = g.last_completion
    assert rec.gate.verdict == VERDICT_VALID
    assert rec.gate.effective_rating == "Overweight"
    # Gate saw the complete restored reports (all present, none "missing").
    assert all(rec.gate.statuses[k] == "present" for k in eg.REQUIRED_REPORT_KEYS)
    g.end_checkpoint()


# ---------------------------------------------------------------------------
# Legacy / conflict sanity at the boundary
# ---------------------------------------------------------------------------
def test_conflict_downgrades_at_boundary(tmp_path):
    """A rating conflict downgrades to REVIEW at the boundary.

    Production behavior (verified): ``_resolve_original_rating`` returns the
    conflict sentinel ``REVIEW`` as its first element, so ``original_rating``
    is ``REVIEW`` here (a conflict has no single trustworthy original). The
    conflict *reason* is preserved on ``gate.reason``.
    """
    g = _make_graph(tmp_path)
    _begin(g)
    state = _full_state("Buy", "Rating: Sell")  # disagree -> conflict
    g.record_decision(_TICKER, _DATE, state)
    rec = g.last_completion
    assert rec.gate.effective_rating == "REVIEW"
    assert rec.gate.error_kind == "rating_conflict"
    assert rec.gate.reason  # conflict reason preserved
    assert state["effective_rating"] == "REVIEW"
    # Conflict => no single trusted original; original_rating is the sentinel.
    assert rec.original_rating == "REVIEW"
    assert state["original_rating"] == "REVIEW"
    g.end_checkpoint()


# ---------------------------------------------------------------------------
# E — resume is a fresh execution for Gate authorization (no checkpoint plumbing)
# ---------------------------------------------------------------------------
def test_resume_is_fresh_execution_for_gate(tmp_path):
    """A 'resume' is modelled as a NEW execution window on the same instance.

    ``begin_checkpoint`` clears ``_completion`` for every execution (including a
    resumed-to-completion run), so the Gate re-evaluates rather than reusing a
    prior authorization. We exercise the real begin/end window with checkpointing
    DISABLED (no SqliteSaver/compile path); the resume re-evaluation contract at
    the boundary is what is under test. A true cross-process Resume that restores
    reports requires an actual graph run (reported separately).
    """
    g = _make_graph(tmp_path)
    _begin(g)  # execution 1
    g.record_decision(_TICKER, _DATE, _full_state("Buy", "Rating: Buy"))
    first = g.last_completion
    assert first.gate.effective_rating == "Buy"
    g.end_checkpoint()
    assert g.last_completion is None

    _begin(g)  # "resume" -> execution 2
    assert g.last_completion is None  # authorization NOT reused
    g.record_decision(_TICKER, _DATE, _full_state("Sell", "Rating: Sell"))
    assert g.last_completion is not first
    assert g.last_completion.original_rating == "Sell"
    assert g.last_completion.gate.effective_rating == "Sell"
    g.end_checkpoint()
