"""Deterministic O4 Stage 2 offline fixtures (D-owned).

Reusable, network-free states for O4 Stage 2 offline tests. These are plain
builders (not pytest fixtures) so any test module can import them without
pulling in a shared conftest. They exercise the real ``check_evidence()``
entry point only; they do not simulate the Graph/CLI runtime or invent any
Stage 2 Guard / GateResult-observation API (those are Member C's to confirm).
"""

from __future__ import annotations

ALL_ANALYSTS: tuple[str, ...] = ("market", "social", "news", "fundamentals")

# Distinct, deterministic, non-trivial report bodies (fixed four-report fixture).
COMPLETE_REPORTS = {
    "market_report": "Market: trend constructive; SMA50 above SMA200.",
    "sentiment_report": "Sentiment: mildly positive across recent chatter.",
    "news_report": "News: recent items neutral; no material catalysts.",
    "fundamentals_report": "Fundamentals: solid margins and steady cash flow.",
}


def complete_state(final_rating: str = "Buy", body: str = "") -> dict:
    """All four required reports non-empty, plus a clear rating."""
    state = dict(COMPLETE_REPORTS)
    state["final_rating"] = final_rating
    state["final_trade_decision"] = body
    return state


def missing_evidence_state(key: str = "news_report", final_rating: str = "Buy") -> dict:
    """One required report empty (default ``news_report``)."""
    state = complete_state(final_rating)
    state[key] = ""
    return state


def market_news_only_state(final_rating: str = "Buy") -> dict:
    """Selected {market, news}; sentiment/fundamentals empty => not_required."""
    state = complete_state(final_rating)
    state["sentiment_report"] = ""
    state["fundamentals_report"] = ""
    return state


MARKET_NEWS_ANALYSTS: tuple[str, ...] = ("market", "news")


def unavailable_text_state(final_rating: str = "Buy", body: str = "Rating: Buy") -> dict:
    """A structurally non-empty report that merely mentions N/A / unavailable."""
    state = complete_state(final_rating, body)
    state["news_report"] = "N/A — upstream source unavailable for this item."
    return state


def original_review_state() -> dict:
    """A pre-existing REVIEW (never upgraded)."""
    return complete_state("REVIEW")


def conflict_state(final_rating: str = "Buy", body: str = "Rating: Sell") -> dict:
    """final_rating and parsed body disagree -> rating conflict -> REVIEW."""
    return complete_state(final_rating, body=body)


def pre_gate_provenance_state(
    final_rating: str = "Overweight", body: str = "Rating: Overweight"
) -> dict:
    """Complete evidence where pre-gate ``final_rating`` and the parsed body agree.

    Used to assert the *pre-gate* original source (the ``final_rating`` field vs
    the rating parsed from ``final_trade_decision``) before any Gate-driven
    overwrite. The Stage 1 checker never mutates state, so the provenance is
    observable by re-reading the input dict after the call.
    """
    return complete_state(final_rating, body=body)
