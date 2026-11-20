"""O5 S4 regression guards: public API and the ticker-news path stay unchanged."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest

from tradingagents.agents import tools
from tradingagents.dataflows.vendors.yahoo import news


def test_rt1_global_news_tool_schema_unchanged():
    properties = tools.get_global_news.tool_call_schema.model_json_schema()["properties"]
    assert set(properties) == {"curr_date", "look_back_days", "limit"}
    assert "trade_date" not in properties


def test_rt2_public_entry_keeps_signature_and_returns_str(monkeypatch):
    parameters = list(inspect.signature(news.get_global_news_yfinance).parameters)
    assert parameters == ["as_of_date", "look_back_days", "limit"]

    monkeypatch.setattr(news, "get_config", lambda: {
        "global_news_lookback_days": 2,
        "global_news_article_limit": 10,
        "global_news_queries": ["q1"],
    })
    monkeypatch.setattr(news, "yf_retry", lambda fn: fn())

    class Search:
        def __init__(self, **kwargs):
            self.news = [{"content": {
                "title": "Fed holds rates", "summary": "Policy unchanged",
                "provider": {"displayName": "FixtureWire"},
                "canonicalUrl": {"url": "https://example.test/fed"},
                "pubDate": "2026-09-27T10:00:00Z",
            }}]

    monkeypatch.setattr(news.yf, "Search", Search)
    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    assert isinstance(result, str)
    assert result.startswith("## Global Market News, from 2026-09-26 to 2026-09-28:")


def test_rt2b_empty_feed_keeps_baseline_absence_wording(monkeypatch):
    monkeypatch.setattr(news, "get_config", lambda: {
        "global_news_lookback_days": 2,
        "global_news_article_limit": 10,
        "global_news_queries": ["q1"],
    })
    monkeypatch.setattr(news, "yf_retry", lambda fn: fn())

    class Search:
        def __init__(self, **kwargs):
            self.news = []

    monkeypatch.setattr(news.yf, "Search", Search)
    result = news.get_global_news_yfinance("2026-09-28", look_back_days=2, limit=1)
    assert isinstance(result, str)
    assert "unavailable" in result or "No global news found" in result


def test_rt4_ticker_news_path_untouched(monkeypatch):
    # get_news_yfinance must not route through the O5 selector at all.
    captured = {}

    def fake_search(canonical, limit):
        captured["searched"] = canonical
        return [], True

    class Ticker:
        def __init__(self, symbol):
            captured["symbol"] = symbol

        def get_news(self, count=20):
            return [{"title": "Company update", "publisher": "P", "link": "l",
                     "providerPublishTime": int(datetime(2026, 9, 27, tzinfo=UTC).timestamp())}]

    monkeypatch.setattr(news.yf, "Ticker", Ticker)
    monkeypatch.setattr(news, "_search_news", fake_search)
    result = news.get_news_yfinance("AAPL", "2026-09-26", "2026-09-28")
    assert "Company update" in result
    assert captured["symbol"] == "AAPL"
    assert "searched" not in captured  # quote feed answered; no search fallback


def test_rt4b_ticker_news_signature_unchanged():
    assert list(inspect.signature(news.get_news_yfinance).parameters) == [
        "ticker", "start_date", "end_date",
    ]
    assert set(tools.get_news.tool_call_schema.model_json_schema()["properties"]) == {
        "start_date", "end_date",
    }


@pytest.mark.parametrize("variant", ["V-SELECTED", "V-FILTERED-EMPTY", "V-UPSTREAM-EMPTY"])
def test_t16_o5_path_adds_no_network_or_llm(variant, monkeypatch):
    # The O5 selector and evidence path must not import or call any client.
    import tradingagents.dataflows.macro_news_filter as selector

    source = inspect.getsource(selector)
    for forbidden in ("requests", "httpx", "yfinance", "langchain", "openai", "anthropic"):
        assert forbidden not in source
    assert not hasattr(selector, "yf")
