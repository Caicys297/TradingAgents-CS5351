"""Stage 1 offline unit tests for the O4 Decision Evidence Gate.

Covers the Member-F-approved O4-TEST-v0.5 Stage 1 unit range:
O4-T-01…07, 09…15, 17…19, 24, 25. For O4-T-07, T-18 and T-19 only the
checker-level unit portions are implemented here (Graph/CLI integration
portions are Stage 2). These tests call the real production
``check_evidence()`` entry point and run fully offline under the
``test/offline/conftest.py`` network-blocking fixture.

They do **not** exercise Graph, CLI, report rendering, persistence or
cross-surface publication.
"""

from __future__ import annotations

import pytest

from tradingagents.agents import evidence_gate as eg
from tradingagents.agents.evidence_gate import (
    ERROR_CHECKER_FAILURE,
    ERROR_EVIDENCE,
    ERROR_RATING_CONFLICT,
    REQUIRED_REPORT_KEYS,
    STATUS_MISSING,
    STATUS_NOT_REQUIRED,
    STATUS_PRESENT,
    VERDICT_REVIEW,
    VERDICT_VALID,
    check_evidence,
)

ALL_ANALYSTS = ["market", "social", "news", "fundamentals"]


def _complete_state(final_rating="Overweight", body=None):
    """A state with all four required reports non-empty and a clear rating."""
    state = {
        "market_report": "Market looks constructive.",
        "sentiment_report": "Sentiment is mildly positive.",
        "news_report": "Recent news is neutral.",
        "fundamentals_report": "Fundamentals are solid.",
        "final_rating": final_rating,
        "final_trade_decision": body if body is not None else "",
    }
    return state


# ---------------------------------------------------------------------------
# O4-T-01 — Complete evidence preserves rating
# ---------------------------------------------------------------------------
def test_t01_complete_evidence_preserves_rating():
    result = check_evidence(_complete_state("Overweight"), ALL_ANALYSTS)
    assert result.verdict == VERDICT_VALID
    assert result.effective_rating == "Overweight"
    assert result.reason == ""
    assert result.error_kind == "none"


# ---------------------------------------------------------------------------
# O4-T-02 — Single empty required report forces REVIEW (parameterized)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("empty_key", list(REQUIRED_REPORT_KEYS))
def test_t02_single_empty_report_forces_review(empty_key):
    state = _complete_state("Buy")
    state[empty_key] = ""
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert result.effective_rating == "REVIEW"
    assert set(result.failing) == {empty_key}


def test_t02_two_required_reports_empty():
    state = _complete_state("Buy")
    state["market_report"] = ""
    state["news_report"] = ""
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert set(result.failing) == {"market_report", "news_report"}


# ---------------------------------------------------------------------------
# O4-T-03 — Whitespace-only, whitespace variants, multi-missing (parameterized)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ws", ["   ", "\n\t\r", " \t\n "])
@pytest.mark.parametrize("ws_key", list(REQUIRED_REPORT_KEYS))
def test_t03_whitespace_only_is_missing(ws_key, ws):
    state = _complete_state("Buy")
    state[ws_key] = ws
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert set(result.failing) == {ws_key}
    assert result.statuses[ws_key] == STATUS_MISSING


def test_t03_empty_plus_whitespace_multi_missing():
    state = _complete_state("Buy")
    state["sentiment_report"] = ""
    state["fundamentals_report"] = "   \n\t "
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert set(result.failing) == {"sentiment_report", "fundamentals_report"}


# ---------------------------------------------------------------------------
# O4-T-04 — Unavailable-source text is structurally present (negative/boundary)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "note",
    [
        "N/A",
        "Data unavailable for this source.",
        "NO_DATA_AVAILABLE",
        "10-Q unavailable; showing last filing.",
    ],
)
def test_t04_unavailable_text_stays_present(note):
    state = _complete_state("Buy", body="Rating: Buy")
    state["looks_like_note_report"] = note  # not a tracked field
    # Put the note inside one of the required reports, keeping it non-empty.
    state["news_report"] = f"{note}"
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.statuses["news_report"] == STATUS_PRESENT
    assert result.verdict == VERDICT_VALID
    assert result.effective_rating == "Buy"


# ---------------------------------------------------------------------------
# O4-T-05 — Unselected analysts are not_required
# ---------------------------------------------------------------------------
def test_t05_unselected_analysts_not_required():
    state = _complete_state("Buy")
    state["sentiment_report"] = ""
    state["fundamentals_report"] = ""
    result = check_evidence(state, ["market", "news"])
    assert result.statuses["sentiment_report"] == STATUS_NOT_REQUIRED
    assert result.statuses["fundamentals_report"] == STATUS_NOT_REQUIRED
    assert result.verdict == VERDICT_VALID
    assert set(result.statuses) == set(REQUIRED_REPORT_KEYS)


# ---------------------------------------------------------------------------
# O4-T-06 — Pre-existing REVIEW not upgraded
# ---------------------------------------------------------------------------
def test_t06_preexisting_review_not_upgraded():
    result = check_evidence(_complete_state("REVIEW"), ALL_ANALYSTS)
    assert result.effective_rating == "REVIEW"
    assert result.verdict == VERDICT_REVIEW


# ---------------------------------------------------------------------------
# O4-T-07 — Recoverable checker failure fails closed (checker-level)
# ---------------------------------------------------------------------------
def test_t07_recoverable_failure_fails_closed(monkeypatch):
    """A recoverable internal failure in production logic fails closed.

    We patch the real production computation helper ``_classify_report`` (used
    by ``check_evidence``) to raise, and require the production entry point
    itself to return REVIEW with a non-empty reason. No test-only wrapper.
    """

    def boom(_value):
        raise RuntimeError("injected evidence-processing failure")

    monkeypatch.setattr(eg, "_classify_report", boom)
    result = check_evidence(_complete_state("Buy"), ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert result.effective_rating == "REVIEW"
    assert result.reason
    assert result.error_kind == ERROR_CHECKER_FAILURE


def test_t07_rating_parse_failure_fails_closed(monkeypatch):
    """A recoverable failure during original-rating resolution fails closed.

    Rating resolution is an internal computation inside the production entry
    point. We patch the real ``_resolve_original_rating`` helper (used by
    ``check_evidence``) to raise, and require the production checker itself to
    return REVIEW with a non-empty reason. The input state and
    ``final_trade_decision`` must be unchanged. No test-only wrapper.
    """
    body = "**Rating**: Buy\n\nWe are bullish."
    state = _complete_state("Buy", body=body)
    import copy

    snapshot = copy.deepcopy(state)

    def boom(_state):
        raise RuntimeError("injected rating-resolution failure")

    monkeypatch.setattr(eg, "_resolve_original_rating", boom)
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert result.effective_rating == "REVIEW"
    assert result.reason
    assert result.error_kind == ERROR_CHECKER_FAILURE
    assert state == snapshot
    assert state["final_trade_decision"] == body


# ---------------------------------------------------------------------------
# O4-T-09 — Complete evidence keeps Sell
# ---------------------------------------------------------------------------
def test_t09_complete_evidence_keeps_sell():
    result = check_evidence(_complete_state("Sell"), ALL_ANALYSTS)
    assert result.effective_rating == "Sell"
    assert result.verdict == VERDICT_VALID


# ---------------------------------------------------------------------------
# O4-T-10 — Original decision text preserved (unit)
# ---------------------------------------------------------------------------
def test_t10_decision_text_preserved():
    body = "We rate this Buy for the reasons above."
    state = _complete_state("Buy", body=body)
    state["news_report"] = ""  # force downgrade
    before = state["final_trade_decision"]
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.effective_rating == "REVIEW"
    assert state["final_trade_decision"] == before


# ---------------------------------------------------------------------------
# O4-T-11 — Determinism (100 repetitions)
# ---------------------------------------------------------------------------
def test_t11_determinism():
    state = _complete_state("Hold")
    verdicts = {check_evidence(state, ALL_ANALYSTS).verdict for _ in range(100)}
    assert len(verdicts) == 1


# ---------------------------------------------------------------------------
# O4-T-12 — Structured result completeness
# ---------------------------------------------------------------------------
def test_t12_structured_result_completeness():
    result = check_evidence(_complete_state("Buy"), ALL_ANALYSTS)
    assert set(result.statuses) >= set(REQUIRED_REPORT_KEYS)
    assert result.verdict in {VERDICT_VALID, VERDICT_REVIEW}
    if result.verdict == VERDICT_VALID:
        assert result.reason == ""
    else:
        assert result.reason


def test_t12_non_pass_has_reason():
    state = _complete_state("Buy")
    state["market_report"] = ""
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert result.reason


# ---------------------------------------------------------------------------
# O4-T-13 — Single selected analyst valid
# ---------------------------------------------------------------------------
def test_t13_single_analyst_valid():
    state = _complete_state("Buy")
    # Other reports may be anything; only market is required.
    result = check_evidence(state, ["market"])
    assert result.verdict == VERDICT_VALID
    for key in REQUIRED_REPORT_KEYS:
        if key != "market_report":
            assert result.statuses[key] == STATUS_NOT_REQUIRED


# ---------------------------------------------------------------------------
# O4-T-14 — Single-analyst missing and multi-select partial (parameterized)
# ---------------------------------------------------------------------------
def test_t14_single_select_market_missing():
    state = _complete_state("Buy")
    state["market_report"] = ""
    result = check_evidence(state, ["market"])
    assert result.effective_rating == "REVIEW"
    assert set(result.failing) == {"market_report"}


def test_t14_multi_select_news_missing_unselected_not_flagged():
    state = _complete_state("Buy")
    state["news_report"] = ""
    state["sentiment_report"] = ""  # unselected; must NOT be flagged
    result = check_evidence(state, ["market", "news", "fundamentals"])
    assert result.effective_rating == "REVIEW"
    assert set(result.failing) == {"news_report"}
    assert result.statuses["sentiment_report"] == STATUS_NOT_REQUIRED


# ---------------------------------------------------------------------------
# O4-T-15 — Offline importability
# ---------------------------------------------------------------------------
def test_t15_offline_import_and_call():
    # Import already happened at module load under the offline fixture; make a
    # minimal call to confirm the entry point runs without graph/LLM/network.
    result = check_evidence(_complete_state("Buy"), ALL_ANALYSTS)
    assert result.verdict in {VERDICT_VALID, VERDICT_REVIEW}


# ---------------------------------------------------------------------------
# O4-T-17 — Absent report keys (parameterized)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("absent_key", list(REQUIRED_REPORT_KEYS))
def test_t17_absent_key_is_missing(absent_key):
    state = _complete_state("Buy")
    del state[absent_key]
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.statuses[absent_key] == STATUS_MISSING
    assert set(result.failing) == {absent_key}
    assert result.effective_rating == "REVIEW"


# ---------------------------------------------------------------------------
# O4-T-18 — Unknown analyst configuration raises ValueError (checker-level)
# ---------------------------------------------------------------------------
def test_t18_unknown_analyst_raises_value_error():
    with pytest.raises(ValueError):
        check_evidence(_complete_state("Buy"), ["market", "options"])


def test_t18_unknown_config_not_converted_to_review(monkeypatch):
    """The recoverable-failure handler must not swallow config errors.

    Patch the evidence helper to raise a *recoverable* failure; even so, an
    unknown analyst key must still surface as ValueError, proving the config
    path is resolved before (and outside) the recoverable handler.
    """

    def boom(_value):
        raise RuntimeError("should not be reached for config errors")

    monkeypatch.setattr(eg, "_classify_report", boom)
    with pytest.raises(ValueError):
        check_evidence(_complete_state("Buy"), ["market", "bogus"])


def test_t18_empty_selection_raises():
    with pytest.raises(ValueError):
        check_evidence(_complete_state("Buy"), [])


def test_t18_config_error_beats_rating_failure(monkeypatch):
    """Unknown config must raise ValueError even when rating resolution fails.

    Configuration validation precedes the recoverable rating/evidence
    computation, so an invalid analyst key must surface as ValueError and must
    not be swallowed into a REVIEW by the recoverable handler.
    """

    def boom(_state):
        raise RuntimeError("should not be reached for config errors")

    monkeypatch.setattr(eg, "_resolve_original_rating", boom)
    with pytest.raises(ValueError):
        check_evidence(_complete_state("Buy"), ["market", "bogus"])


# ---------------------------------------------------------------------------
# O4-T-19 — Buy body not presented as approved (checker-level)
# ---------------------------------------------------------------------------
def test_t19_missing_evidence_review_and_body_preserved():
    body = "**Rating**: Buy\n\nWe are bullish."
    state = _complete_state("Buy", body=body)
    state["fundamentals_report"] = ""
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.effective_rating == "REVIEW"
    assert state["final_trade_decision"] == body


# ---------------------------------------------------------------------------
# O4-T-24 — O5 boundary
# ---------------------------------------------------------------------------
def test_t24a_filtered_empty_status_does_not_downgrade():
    # A non-report O5 status field present upstream must not affect the gate.
    state = _complete_state("Buy", body="Rating: Buy")
    state["news_filter_status"] = "filtered_empty"
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_VALID
    assert result.effective_rating == "Buy"


@pytest.mark.parametrize("mode", ["absent", "empty"])
def test_t24b_missing_news_report_downgrades(mode):
    state = _complete_state("Buy")
    if mode == "absent":
        del state["news_report"]
    else:
        state["news_report"] = ""
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.verdict == VERDICT_REVIEW
    assert result.effective_rating == "REVIEW"
    assert set(result.failing) == {"news_report"}


# ---------------------------------------------------------------------------
# O4-T-25 — Rating precedence and conflict
# ---------------------------------------------------------------------------
def test_t25a_sources_agree_preserved():
    result = check_evidence(_complete_state("Buy", body="Rating: Buy"), ALL_ANALYSTS)
    assert result.effective_rating == "Buy"


def test_t25b_body_supplies_rating_when_final_absent():
    state = _complete_state(None, body="Rating: Sell")
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.effective_rating == "Sell"


def test_t25c_conflict_downgrades_with_reason():
    state = _complete_state("Buy", body="Rating: Sell")
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.effective_rating == "REVIEW"
    assert result.reason
    assert result.error_kind == ERROR_RATING_CONFLICT


def test_t25d_original_review_stays_review():
    result = check_evidence(_complete_state("REVIEW"), ALL_ANALYSTS)
    assert result.effective_rating == "REVIEW"


# ---------------------------------------------------------------------------
# Extra: missing-evidence error kind for completeness
# ---------------------------------------------------------------------------
def test_missing_evidence_error_kind():
    state = _complete_state("Buy")
    state["market_report"] = ""
    result = check_evidence(state, ALL_ANALYSTS)
    assert result.error_kind == ERROR_EVIDENCE
