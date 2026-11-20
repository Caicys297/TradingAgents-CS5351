"""S2 evidence construction, independent of persistence and vendor calls."""

from datetime import UTC, datetime, timedelta

import pytest

from tradingagents.dataflows.vendors.yahoo import news


def test_i9_a_vendor_before_rule_resolution_has_present_null_version():
    event = news._build_o5_evidence(
        "V-VENDOR", rules_resolved=False,
        occurred_at=datetime(2026, 9, 28, tzinfo=UTC),
        trigger="VENDOR_TIMEOUT", batch_id=None, input_count=None,
        selected_count=None, reason_counts=None,
        pre_filter_candidate_count=None, vendor="yfinance", method="Search",
    )
    assert event == {
        "variant": "V-VENDOR", "action": "VENDOR_UNAVAILABLE",
        "trigger": "VENDOR_TIMEOUT", "disposition": "UPSTREAM_UNAVAILABLE",
        "rules_version": None, "occurred_at": "2026-09-28T00:00:00Z",
        "batch_id": None, "input_count": None, "selected_count": None,
        "reason_counts": None, "pre_filter_candidate_count": None,
        "vendor": "yfinance", "method": "Search",
    }
    with pytest.raises(ValueError, match="fields"):
        news._build_o5_evidence(
            "V-VENDOR", rules_resolved=False, trigger="VENDOR_TIMEOUT",
            input_count=None, selected_count=None, reason_counts=None,
            pre_filter_candidate_count=None, vendor="yfinance", method="Search",
        )
    with pytest.raises(ValueError, match="fields"):
        news._build_o5_evidence(
            "V-VENDOR", rules_resolved=False, trigger="VENDOR_TIMEOUT",
            rules_version="o5-rules-v1.1-draft", batch_id=None,
            input_count=None, selected_count=None, reason_counts=None,
            pre_filter_candidate_count=None, vendor="yfinance", method="Search",
        )


def test_s2_invalid_request_and_zero_limit_have_distinct_shapes():
    clock = datetime(2026, 9, 28, 9, 30, tzinfo=UTC) + timedelta(hours=2)
    invalid = news._build_o5_evidence(
        "V-INVALID-REQUEST", rules_resolved=False, occurred_at=clock,
        field="limit", reason="must be non-negative",
    )
    zero = news._build_o5_evidence(
        "V-LIMIT-ZERO", occurred_at=clock, batch_id=None,
        input_count=0, executed_query_count=0, pre_filter_candidate_count=0,
    )
    assert invalid["rules_version"] is None
    assert zero["rules_version"] == "o5-rules-v1.1-draft"
    assert invalid["occurred_at"] == zero["occurred_at"] == "2026-09-28T11:30:00Z"
    assert "batch_id" not in invalid
    assert zero["batch_id"] is None


def test_s2_rejects_unknown_variant_and_unresolved_terminal_event():
    with pytest.raises(ValueError, match="unknown"):
        news._build_o5_evidence("V-NOT-REAL")
    with pytest.raises(ValueError, match="unresolved"):
        news._build_o5_evidence(
            "V-LIMIT-ZERO", rules_resolved=False, batch_id=None,
            input_count=0, executed_query_count=0, pre_filter_candidate_count=0,
        )
