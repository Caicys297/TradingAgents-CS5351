"""O4 Stage 2 — T-20 compatibility helpers (D-owned, independent parts only).

Verifies what can be checked **without** Member C's shared Stage 2 wiring:

- ``record_decision()`` keeps its existing signature and ``None`` return
  (introspection only — shared behaviour is C's to wire; this file does not
  exercise the gated runtime).
- Stage 1 Gate behaviour is preserved (delegated to the real ``check_evidence``).
- Historical-state readability: ``run_rating`` still reads legacy states lacking
  ``effective_rating`` without raising, and reading history does not by itself
  publish an ungated new rating.

Full T-20 integration regression (gated Graph/CLI paths, real persistence) is
**not** claimed here; it depends on C's shared implementation.
"""

from __future__ import annotations

import inspect

from o4_stage2_fixtures import (
    ALL_ANALYSTS,
    MARKET_NEWS_ANALYSTS,
    complete_state,
    conflict_state,
    market_news_only_state,
    missing_evidence_state,
    original_review_state,
    pre_gate_provenance_state,
    unavailable_text_state,
)

from tradingagents.agents.evidence_gate import (
    ERROR_RATING_CONFLICT,
    VERDICT_REVIEW,
    VERDICT_VALID,
    check_evidence,
)
from tradingagents.agents.rating import RATING_REVIEW, is_review, run_rating
from tradingagents.graph.trading_graph import TradingAgentsGraph


def test_t20_record_decision_signature_unchanged():
    """record_decision(self, company_name, trade_date, final_state) — no new params."""
    sig = inspect.signature(TradingAgentsGraph.record_decision)
    params = list(sig.parameters)
    assert params == ["self", "company_name", "trade_date", "final_state"], params
    # No required extra parameters added (all params have defaults or are the 4 above).
    for name, p in sig.parameters.items():
        if name == "self":
            continue
        assert p.default is inspect.Parameter.empty  # the original four are positional
        assert p.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        )


def test_t20_stage1_gate_behaviour_preserved():
    """The merged Stage 1 Gate contract is intact (complete/missing/conflict/REVIEW)."""
    assert check_evidence(complete_state("Buy"), ALL_ANALYSTS).verdict == VERDICT_VALID
    assert (
        check_evidence(missing_evidence_state("news_report"), ALL_ANALYSTS).verdict
        == VERDICT_REVIEW
    )
    assert check_evidence(conflict_state(), ALL_ANALYSTS).error_kind == ERROR_RATING_CONFLICT
    assert check_evidence(original_review_state(), ALL_ANALYSTS).effective_rating == RATING_REVIEW


def test_t20_unselected_analysts_not_required_and_unavailable_present():
    """Market+News unselected => not_required; N/A text stays structurally present."""
    r = check_evidence(market_news_only_state("Buy"), MARKET_NEWS_ANALYSTS)
    assert r.verdict == VERDICT_VALID
    assert r.statuses["sentiment_report"] == "not_required"
    assert r.statuses["fundamentals_report"] == "not_required"

    r2 = check_evidence(unavailable_text_state("Buy"), ALL_ANALYSTS)
    assert r2.statuses["news_report"] == "present"
    assert r2.verdict == VERDICT_VALID


def test_t20_historical_state_readable_without_effective_rating():
    """Legacy state lacking ``effective_rating`` is readable via run_rating (no raise)."""
    legacy = {"final_rating": "Hold", "final_trade_decision": "Rating: Hold"}
    assert "effective_rating" not in legacy
    assert run_rating(legacy) == "Hold"
    assert is_review(run_rating(legacy)) is False

    legacy_none = {"final_trade_decision": "no parseable rating here"}
    assert run_rating(legacy_none) == RATING_REVIEW
    assert is_review(run_rating(legacy_none)) is True


def test_t20_pre_gate_provenance_readable_and_unmutated():
    """The pre-gate original source is observable and the input is not mutated.

    Stage 1 ``check_evidence`` is pure, so the caller's pre-gate ``final_rating``
    and ``final_trade_decision`` remain exactly as provided (provenance intact).
    """
    state = pre_gate_provenance_state("Overweight", body="Rating: Overweight")
    final_rating_before = state["final_rating"]
    body_before = state["final_trade_decision"]
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_VALID
    assert state["final_rating"] == final_rating_before == "Overweight"
    assert state["final_trade_decision"] == body_before
    assert "effective_rating" not in state  # checker never injects runtime fields
