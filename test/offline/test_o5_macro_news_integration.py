"""S3 adapter checks with fake Yahoo search and a per-test in-memory sink."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tradingagents.dataflows.errors import VendorUnavailableError
from tradingagents.dataflows.macro_news_filter import InvalidRequestError
from tradingagents.dataflows.vendors.yahoo import news


class MemorySink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


@pytest.fixture
def adapter(monkeypatch):
    sink = MemorySink()
    token = news._o5_evidence_sink.set(sink)
    monkeypatch.setattr(news, "get_config", lambda: {
        "global_news_lookback_days": 2,
        "global_news_article_limit": 10,
        "global_news_queries": ["q1", "q2", "q3"],
    })
    monkeypatch.setattr(news, "yf_retry", lambda fn: fn())
    yield sink
    news._o5_evidence_sink.reset(token)


@pytest.mark.parametrize("limit", [True, -1, 2.5])
def test_s3_invalid_limit_never_fetches(monkeypatch, adapter, limit):
    monkeypatch.setattr(news.yf, "Search", lambda **kwargs: pytest.fail("fetched"))
    with pytest.raises(InvalidRequestError) as error:
        news.get_global_news_yfinance("2026-09-28", limit=limit)
    assert error.value.field == "limit"
    assert len(adapter.events) == 1
    assert adapter.events[0]["variant"] == "V-INVALID-REQUEST"
    assert adapter.events[0]["rules_version"] is None


@pytest.mark.parametrize(
    "date,lookback,field",
    [
        ("2026-02-30", 2, "as_of_date"),
        ("2026-9-28", 2, "as_of_date"),
        ("2026-09-28", -1, "look_back_days"),
        ("2026-09-28", True, "look_back_days"),
    ],
)
def test_s3_invalid_date_or_lookback_never_fetches(monkeypatch, adapter, date, lookback, field):
    monkeypatch.setattr(news.yf, "Search", lambda **kwargs: pytest.fail("fetched"))
    with pytest.raises(InvalidRequestError) as error:
        news.get_global_news_yfinance(date, look_back_days=lookback)
    assert error.value.field == field
    assert [event["variant"] for event in adapter.events] == ["V-INVALID-REQUEST"]
    assert adapter.events[0]["rules_version"] is None


def test_s3_zero_limit_skips_vendor(monkeypatch, adapter):
    monkeypatch.setattr(news.yf, "Search", lambda **kwargs: pytest.fail("fetched"))
    result = news.get_global_news_yfinance("2026-09-28", limit=0)
    # D-supplied sentence; registry fixes only "LIMIT_ZERO without vendor fetch".
    assert result == "No macro news items were requested because the result limit is zero."
    assert [event["variant"] for event in adapter.events] == ["V-LIMIT-ZERO"]
    assert adapter.events[0]["executed_query_count"] == 0
    assert adapter.events[0]["input_count"] == 0


def test_s3_out_of_window_feed_is_upstream_empty(monkeypatch, adapter):
    calls = []
    stale = {
        "title": "Fed holds rates", "summary": "Policy unchanged",
        "publisher": "FixtureWire", "link": "https://example.test/fed",
        "providerPublishTime": int(datetime(2026, 9, 20, tzinfo=UTC).timestamp()),
    }

    class Search:
        def __init__(self, *, query, news_count, enable_fuzzy_query):
            calls.append((query, news_count, enable_fuzzy_query))
            self.news = [stale]

    monkeypatch.setattr(news.yf, "Search", Search)
    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    assert isinstance(result, str) and "unavailable" in result
    assert calls == [("q1", 1, True), ("q2", 1, True), ("q3", 1, True)]
    assert [event["variant"] for event in adapter.events] == ["V-UPSTREAM-EMPTY"]
    assert adapter.events[0]["executed_query_count"] == 3
    assert adapter.events[0]["pre_filter_candidate_count"] == 0


def test_s3_empty_vendor_pool_is_distinct_from_filtered_pool(monkeypatch, adapter):
    class Search:
        def __init__(self, **kwargs):
            self.news = []

    monkeypatch.setattr(news.yf, "Search", Search)
    result = news.get_global_news_yfinance("2026-09-28", limit=10)
    assert "unavailable" in result and "not an absence" in result
    assert [event["variant"] for event in adapter.events] == ["V-UPSTREAM-EMPTY"]
    assert adapter.events[0]["executed_query_count"] == 3
    assert adapter.events[0]["pre_filter_candidate_count"] == 0


def test_s3_first_vendor_failure_uses_resolved_version(monkeypatch, adapter):
    def fail(**kwargs):
        raise VendorUnavailableError("rate limited")

    monkeypatch.setattr(news.yf, "Search", fail)
    with pytest.raises(VendorUnavailableError, match="rate limited"):
        news.get_global_news_yfinance("2026-09-28", limit=10)
    assert [event["variant"] for event in adapter.events] == ["V-VENDOR"]
    assert adapter.events[0]["rules_version"] == "o5-rules-v1.1-draft"
    assert adapter.events[0]["trigger"] == "VENDOR_RATE_LIMIT"


def test_s3_partial_failure_does_not_publish_collected_article(monkeypatch, adapter):
    calls = []
    article = {
        "title": "Fed holds rates", "summary": "Policy unchanged",
        "publisher": "FixtureWire", "link": "https://example.test/fed",
        "providerPublishTime": int(datetime(2026, 9, 27, tzinfo=UTC).timestamp()),
    }

    class Search:
        def __init__(self, *, query, **kwargs):
            calls.append(query)
            if query == "q3":
                raise VendorUnavailableError("Yahoo Finance request failed")
            self.news = [article] if query == "q1" else []

    monkeypatch.setattr(news.yf, "Search", Search)
    with pytest.raises(VendorUnavailableError):
        news.get_global_news_yfinance("2026-09-28", limit=10)
    assert calls == ["q1", "q2", "q3"]
    assert [event["variant"] for event in adapter.events] == ["V-PARTIAL"]
    event = adapter.events[0]
    assert event["executed_query_count"] == 3
    assert event["queries_failed"] == 1
    assert event["pre_filter_candidate_count"] == 1
    assert event["batch_id"] is event["input_count"] is event["reason_counts"] is None


def test_s4_candidate_id_matches_approved_dev20_fixture():
    fixture = Path(__file__).parent / "fixtures/o5/O5-Dev20-Fixtures-v0.5.3-DRAFT.json"
    item = json.loads(fixture.read_text(encoding="utf-8"))["candidates"][0]
    mapped = news._map_news_dict_to_candidate({
        "title": item["title"], "summary": item["summary"],
        "publisher": item["source"], "link": item["url"],
        "pub_date": datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")),
    })
    assert mapped.candidate_id == "o5:5bac9b8abe6d5ca1d080daddc17790be"
    assert mapped.title == item["title"]
    assert mapped.summary == item["summary"]
    assert mapped.source == item["source"]


def test_s4_canonical_url_keeps_nondefault_port():
    assert news._o5_canonical_url("HTTPS://Example.TEST:443/report/?q=1#part") == (
        "https://example.test/report"
    )
    assert news._o5_canonical_url("HTTPS://Example.TEST:8443/report/?q=1#part") == (
        "https://example.test:8443/report"
    )


def test_s4_filters_before_slice_and_preserves_fields():
    request = news._build_o5_request("2026-09-28", 2, 3)
    date = datetime(2026, 9, 27, 10, tzinfo=UTC)
    articles = [
        {"title": "Company quarterly earnings", "summary": "", "publisher": "A",
         "link": "https://example.test/earnings", "pub_date": date},
        {"title": "Fed holds rates", "summary": "Policy unchanged", "publisher": "B",
         "link": "https://example.test/fed", "pub_date": date},
        {"title": "CPI rises 2%", "summary": "Inflation pressure", "publisher": "C",
         "link": "https://example.test/cpi", "pub_date": date},
        {"title": "GDP growth 3%", "summary": "Output expansion", "publisher": "D",
         "link": "https://example.test/gdp", "pub_date": date},
    ]
    result, batch_id = news._select_o5_batch(articles, request)
    assert [item.title for item in result.selected] == [
        "Fed holds rates", "CPI rises 2%", "GDP growth 3%",
    ]
    assert [item.disposition for item in result.decisions] == [
        "REJECTED", "SELECTED", "SELECTED", "SELECTED",
    ]
    assert news._o5_reason_counts(result) == {"NO_MACRO_EVIDENCE": 1, "SELECTED": 3}
    assert result.counts()["input_count"] == 4
    assert batch_id.startswith("b:")
    assert news._map_selected_to_article_dict(result.selected[0]) == articles[1]
    changed = [dict(item) for item in articles]
    changed[0]["summary"] = "different"
    assert news._select_o5_batch(changed, request)[1] != batch_id


# --------------------------------------------------------------------- S4 public entry

def _nested(title, summary, url, pub_date, publisher="FixtureWire"):
    """A nested Yahoo article, the shape ``_extract_article_data`` expects."""
    return {"content": {
        "title": title, "summary": summary,
        "provider": {"displayName": publisher},
        "canonicalUrl": {"url": url},
        "pubDate": pub_date,
    }}


def _search_returning(pages):
    calls = []

    class Search:
        def __init__(self, *, query, **kwargs):
            calls.append(query)
            self.news = pages.pop(0) if pages else []

    return Search, calls


def test_s4_selected_path_filters_before_slice_and_keeps_fields(monkeypatch, adapter):
    # K=1 but the first article is irrelevant: the macro item after it must win.
    pages = [[
        _nested("Company reports quarterly earnings", "", "https://example.test/a", "2026-09-27T09:00:00Z", "A"),
        _nested("Fed holds rates", "Policy unchanged", "https://example.test/fed", "2026-09-27T10:00:00Z", "B"),
    ]]
    Search, calls = _search_returning(pages)
    monkeypatch.setattr(news.yf, "Search", Search)

    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)

    assert isinstance(result, str)
    assert "Fed holds rates" in result and "Company reports quarterly earnings" not in result
    # Business fields survive the round trip into _format_articles.
    assert "(source: B)" in result and "Link: https://example.test/fed" in result
    assert calls == ["q1"]  # early stop at the limit, query text unchanged
    assert [event["variant"] for event in adapter.events] == ["V-SELECTED"]
    event = adapter.events[0]
    assert event["selected_count"] == 1
    assert event["input_count"] == 2
    assert event["pre_filter_candidate_count"] == 2
    assert event["executed_query_count"] == 1
    assert event["rules_version"] == "o5-rules-v1.1-draft"
    assert event["reason_counts"] == {"NO_MACRO_EVIDENCE": 1, "SELECTED": 1}


def test_s4_t04d_filtered_to_zero_is_not_upstream_empty(monkeypatch, adapter):
    # The approved T04d fixture: one valid, in-window, non-macro article.
    pages = [[_nested(
        "Company reports quarterly earnings", "", "https://example.test/earnings",
        "2026-09-27T10:00:00Z",
    )]]
    Search, calls = _search_returning(pages)
    monkeypatch.setattr(news.yf, "Search", Search)

    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)

    assert isinstance(result, str)
    # Never unfiltered articles, never an upstream-empty mislabel.
    assert "###" not in result
    assert "unavailable" not in result.casefold() and "no global news found" not in result.casefold()
    # FILTERED_EMPTY sentence (D-supplied; registry fixes no literal).
    assert result == "No news items matched the macro relevance filter."
    assert [event["variant"] for event in adapter.events] == ["V-FILTERED-EMPTY"]
    event = adapter.events[0]
    assert event["input_count"] == 1
    assert event["pre_filter_candidate_count"] == 1
    # Approved raw-candidate early stop: K=1 is filled by q1, so later queries
    # are not issued on account of the candidate being irrelevant.
    assert event["executed_query_count"] == 1
    assert event["selected_count"] == 0
    assert event["reason_counts"] == {"NO_MACRO_EVIDENCE": 1}
    assert calls == ["q1"]


def test_s4_t04d_all_irrelevant_uses_the_all_irrelevant_enum_member(monkeypatch, adapter):
    # All-valid, all-irrelevant input: the existing ALL_IRRELEVANT enum member
    # describes the cause exactly; no enum or public field is added.
    pages = [[_nested("Company reports quarterly earnings", "", "https://example.test/e",
                      "2026-09-27T10:00:00Z")]]
    Search, _ = _search_returning(pages)
    monkeypatch.setattr(news.yf, "Search", Search)
    news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    event = adapter.events[0]
    assert event["empty_kind"] == "ALL_IRRELEVANT"


def _one_macro_article():
    return [[_nested("Fed holds rates", "Policy unchanged",
                     "https://example.test/fed", "2026-09-27T10:00:00Z")]]


def _run_with_sink(monkeypatch, sink, caplog):
    monkeypatch.setattr(news, "get_config", lambda: {
        "global_news_lookback_days": 2, "global_news_article_limit": 10,
        "global_news_queries": ["q1"],
    })
    monkeypatch.setattr(news, "yf_retry", lambda fn: fn())
    Search, _ = _search_returning(_one_macro_article())
    monkeypatch.setattr(news.yf, "Search", Search)
    token = news._o5_evidence_sink.set(sink)
    try:
        with caplog.at_level("ERROR", logger="tradingagents.o5.evidence"):
            result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    finally:
        news._o5_evidence_sink.reset(token)
    return result


def test_s4_i5_failing_sink_matches_working_sink_control(monkeypatch, caplog):
    """I5: an emit failure must not change the honest business result."""
    control_sink = MemorySink()
    caplog.clear()
    control = _run_with_sink(monkeypatch, control_sink, caplog)
    control_events = list(control_sink.events)
    assert [e["variant"] for e in control_events] == ["V-SELECTED"]
    assert "SINK_FAILED" not in caplog.text

    class Boom(MemorySink):
        def emit(self, event):
            raise RuntimeError("sink down")

    failing_sink = Boom()
    caplog.clear()
    failing = _run_with_sink(monkeypatch, failing_sink, caplog)

    # Complete string equality against the control on identical input.
    assert failing == control
    assert isinstance(failing, str) and "Fed holds rates" in failing
    # The failing sink retained no successful event.
    assert failing_sink.events == []
    # The failure is reported independently, not swallowed.
    assert "SINK_FAILED" in caplog.text


def test_s4_builder_failure_diagnostic_is_not_i5b(monkeypatch, caplog):
    """A builder exception must keep the honest result and retain no success.

    This is a diagnostic for ``_build_o5_evidence`` raising; it is NOT I5b,
    which stays in S5 (production sink construction).
    """
    control_sink = MemorySink()
    caplog.clear()
    control = _run_with_sink(monkeypatch, control_sink, caplog)
    assert [e["variant"] for e in control_sink.events] == ["V-SELECTED"]

    real_build = news._build_o5_evidence

    def exploding_build(*args, **kwargs):
        raise ValueError("builder down")

    monkeypatch.setattr(news, "_build_o5_evidence", exploding_build)
    failing_sink = MemorySink()
    caplog.clear()
    failing = _run_with_sink(monkeypatch, failing_sink, caplog)
    monkeypatch.setattr(news, "_build_o5_evidence", real_build)

    assert failing == control          # same honest business result
    assert failing_sink.events == []   # no false retained success
    assert "SINK_FAILED" in caplog.text


def test_s4_invariant_violation_suppresses_publication(monkeypatch, adapter):
    # Make the selector return a record whose business fields differ from input.
    pages = [[_nested("Fed holds rates", "Policy unchanged",
                      "https://example.test/fed", "2026-09-27T10:00:00Z")]]
    Search, _ = _search_returning(pages)
    monkeypatch.setattr(news.yf, "Search", Search)

    from dataclasses import replace as _replace

    real_select = news.select_macro_news

    def tampering_select(candidates, request):
        result = real_select(candidates, request)
        result.selected = [_replace(item, title="Tampered") for item in result.selected]
        return result

    monkeypatch.setattr(news, "select_macro_news", tampering_select)
    # Public API stays str: a suppressed batch returns a notice, never raises.
    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    assert isinstance(result, str)
    assert "###" not in result          # nothing from the tampered batch is published
    assert "Tampered" not in result     # and never the tampered text
    assert [event["variant"] for event in adapter.events] == ["V-INVARIANT"]
    event = adapter.events[0]
    assert event["violated_invariant"] == "INV-O5-01"
    # One item was selected before suppression, so the truthful pre-count is 1.
    assert event["pre_suppression_selected_count"] == 1
    assert event["published_selected_count"] == 0
    # The batch identity is known before the check and must not be dropped.
    assert isinstance(event["batch_id"], str) and event["batch_id"].startswith("b:")
    # Interface section 4.1: V-INVARIANT carries a resolved (str) rules version.
    assert event["rules_version"] == "o5-rules-v1.1-draft"


def test_s4_invariant_batch_id_matches_the_unsuppressed_batch(monkeypatch, adapter):
    """The V-INVARIANT batch_id equals the id the same input produces on success."""
    article = _nested("Fed holds rates", "Policy unchanged",
                      "https://example.test/fed", "2026-09-27T10:00:00Z")

    class Search:
        def __init__(self, **kwargs):
            self.news = [article]  # same input on every call

    monkeypatch.setattr(news.yf, "Search", Search)

    # Control: the untouched batch reports its id on V-SELECTED.
    news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    control_id = adapter.events[0]["batch_id"]
    assert adapter.events[0]["variant"] == "V-SELECTED"

    adapter.events.clear()
    from dataclasses import replace as _replace

    real_select = news.select_macro_news

    def tampering_select(candidates, request):
        result = real_select(candidates, request)
        result.selected = [_replace(item, title="Tampered") for item in result.selected]
        return result

    monkeypatch.setattr(news, "select_macro_news", tampering_select)
    news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    invariant_event = adapter.events[0]
    assert invariant_event["variant"] == "V-INVARIANT"
    assert invariant_event["batch_id"] == control_id


def test_s4_filter_unavailable_text_is_distinct_from_filtered_empty(monkeypatch, adapter):
    """FILTER_UNAVAILABLE must not read like FILTERED_EMPTY or upstream-empty."""
    pages = [[_nested("Fed holds rates", "Policy unchanged",
                      "https://example.test/fed", "2026-09-27T10:00:00Z")]]
    Search, _ = _search_returning(pages)
    monkeypatch.setattr(news.yf, "Search", Search)

    from dataclasses import replace as _replace

    real_select = news.select_macro_news

    def tampering_select(candidates, request):
        result = real_select(candidates, request)
        result.selected = [_replace(item, title="Tampered") for item in result.selected]
        return result

    monkeypatch.setattr(news, "select_macro_news", tampering_select)
    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)

    # D-supplied sentence; registry requires "explicit filter-unavailable, not no-news".
    assert result == (
        "Macro news filtering was unavailable; relevance could not be determined."
    )
    assert "No news items matched the macro relevance filter." not in result
    assert "unavailable for" not in result.casefold()
    assert [event["variant"] for event in adapter.events] == ["V-INVARIANT"]


def test_s4_approved_raw_early_stop_stops_before_later_queries(monkeypatch, adapter):
    """The approved collector stops at K raw candidates; later queries stay unfetched.

    This is the documented scope limit: the selector never claims topics that
    were not retrieved, and O5 adds no requests to look for them.
    """
    irrelevant = [
        _nested(f"Company quarterly earnings {i}", "", f"https://example.test/e{i}",
                "2026-09-27T08:00:00Z")
        for i in range(3)
    ]
    relevant = _nested("Fed holds rates", "Policy unchanged",
                       "https://example.test/fed", "2026-09-27T10:00:00Z")
    pages = [irrelevant, [relevant]]
    Search, calls = _search_returning(pages)
    monkeypatch.setattr(news.yf, "Search", Search)

    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=3)

    # q1 filled K=3 raw candidates, so q2 was never requested.
    assert calls == ["q1"]
    assert "Fed holds rates" not in result
    assert "Company quarterly earnings" not in result
    assert [event["variant"] for event in adapter.events] == ["V-FILTERED-EMPTY"]
    assert adapter.events[0]["executed_query_count"] == 1
    assert adapter.events[0]["pre_filter_candidate_count"] == 3
    assert adapter.events[0]["selected_count"] == 0


def test_s4_early_stop_unchanged_when_supply_is_relevant(monkeypatch, adapter):
    """Relevant supply still stops at the first query that fills K."""
    articles = [
        _nested("Fed holds rates", "", "https://example.test/a", "2026-09-27T10:00:00Z"),
        _nested("ECB cuts rates", "", "https://example.test/b", "2026-09-27T09:00:00Z"),
        _nested("BOJ keeps policy", "", "https://example.test/c", "2026-09-27T08:00:00Z"),
    ]
    Search, calls = _search_returning([articles])
    monkeypatch.setattr(news.yf, "Search", Search)

    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=3)

    assert result.count("### ") == 3
    assert calls == ["q1"]  # early stop preserved
    assert adapter.events[0]["variant"] == "V-SELECTED"
    assert adapter.events[0]["executed_query_count"] == 1
