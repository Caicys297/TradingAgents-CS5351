"""yfinance-based news data fetching functions."""

import contextlib
import hashlib
import json
import logging
import unicodedata
from collections import Counter
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

import yfinance as yf

from tradingagents.dataflows.config import get_config
from tradingagents.dataflows.date_window import coverage_gap, in_window
from tradingagents.dataflows.errors import VendorUnavailableError
from tradingagents.dataflows.macro_news_filter import (
    DEFAULT_TOPIC_ORDER,
    RULES_VERSION,
    InvalidRequestError,
    MacroNewsCandidate,
    MacroNewsRequest,
    SelectedRecord,
    SelectorResult,
    _validate_request,
    select_macro_news,
)
from tradingagents.dataflows.symbols import normalize_symbol
from tradingagents.dataflows.vendors.yahoo.common import yf_retry

_O5_LOGGER = logging.getLogger("tradingagents.o5.evidence")
_o5_evidence_sink: ContextVar[object | None] = ContextVar("o5_evidence_sink", default=None)

_O5_VARIANTS = {
    "V-INVALID-REQUEST": ("REJECT_REQUEST", "INVALID_REQUEST", "INVALID_REQUEST",
                          frozenset({"field", "reason"})),
    "V-LIMIT-ZERO": ("SKIP_CLASSIFICATION", "LIMIT_ZERO", "LIMIT_ZERO",
                     frozenset({"batch_id", "input_count", "executed_query_count",
                                "pre_filter_candidate_count"})),
    "V-UPSTREAM-EMPTY": ("SERVE_UPSTREAM_EMPTY", "UPSTREAM_EMPTY", "UPSTREAM_UNAVAILABLE",
                         frozenset({"batch_id", "input_count", "selected_count",
                                    "reason_counts", "executed_query_count",
                                    "pre_filter_candidate_count"})),
    "V-PARTIAL": ("PARTIAL_UPSTREAM", "PARTIAL_QUERY_FAILURE", "PARTIAL_UPSTREAM",
                  frozenset({"batch_id", "input_count", "reason_counts",
                             "executed_query_count", "queries_failed",
                             "pre_filter_candidate_count"})),
    "V-SELECTED": ("SERVE_SELECTED", "OK", "OK",
                   frozenset({"batch_id", "input_count", "selected_count", "reason_counts",
                              "executed_query_count", "pre_filter_candidate_count"})),
    "V-FILTERED-EMPTY": ("SERVE_FILTERED_EMPTY", "NO_RELEVANT_NEWS", "FILTERED_TO_EMPTY",
                         frozenset({"batch_id", "input_count", "selected_count", "reason_counts",
                                    "executed_query_count", "pre_filter_candidate_count", "empty_kind"})),
    "V-INVARIANT": ("SUPPRESS_BATCH", "INVARIANT_VIOLATION", "INVARIANT_VIOLATION",
                    frozenset({"batch_id", "violated_invariant",
                               "pre_suppression_selected_count", "published_selected_count"})),
}


def _build_o5_evidence(
    variant: str, *, rules_resolved: bool = True, occurred_at: datetime | None = None,
    **fields: object,
) -> dict[str, object]:
    """Build one stage-appropriate event; persistence belongs to a later stage."""
    if variant == "V-VENDOR":
        trigger = fields.pop("trigger", None)
        if trigger not in {"VENDOR_TIMEOUT", "VENDOR_RATE_LIMIT",
                           "VENDOR_PAYLOAD_INVALID", "VENDOR_UNAVAILABLE"}:
            raise ValueError("invalid vendor trigger")
        action, disposition = "VENDOR_UNAVAILABLE", "UPSTREAM_UNAVAILABLE"
        required = {"batch_id", "input_count", "selected_count", "reason_counts",
                    "pre_filter_candidate_count", "vendor", "method"}
        optional = {"executed_query_count"}
    else:
        if variant not in _O5_VARIANTS:
            raise ValueError(f"unknown O5 evidence variant {variant!r}")
        action, trigger, disposition, required = _O5_VARIANTS[variant]
        optional = {"matched_topic_counts"} if variant in {
            "V-SELECTED", "V-FILTERED-EMPTY"} else set()
    if set(fields) - (set(required) | optional) or set(required) - set(fields):
        raise ValueError("O5 evidence fields do not match variant")
    if not rules_resolved and variant not in {"V-VENDOR", "V-INVALID-REQUEST"}:
        raise ValueError("unresolved rules cannot reach this variant")
    if variant == "V-INVALID-REQUEST" and rules_resolved:
        raise ValueError("invalid requests precede rule resolution")
    moment = occurred_at or datetime.now(UTC)
    if moment.tzinfo is None:
        raise ValueError("occurred_at must be timezone-aware")
    return {
        "variant": variant, "action": action, "trigger": trigger,
        "disposition": disposition,
        "rules_version": RULES_VERSION if rules_resolved else None,
        "occurred_at": moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **fields,
    }


def _emit_o5_evidence(event: dict[str, object]) -> None:
    sink = _o5_evidence_sink.get()
    if sink is not None:
        sink.emit(event)


def _record_o5_evidence(variant: str, **fields: object) -> None:
    try:
        _emit_o5_evidence(_build_o5_evidence(variant, **fields))
    except Exception:
        _O5_LOGGER.exception("SINK_FAILED: O5 evidence was not retained")


def _build_o5_request(
    as_of_date: str, look_back_days: int, limit: int,
    *, rules_version: str = RULES_VERSION,
) -> MacroNewsRequest:
    if not isinstance(as_of_date, str):
        raise InvalidRequestError("as_of_date", "must be YYYY-MM-DD")
    try:
        curr_dt = datetime.strptime(as_of_date, "%Y-%m-%d")
    except ValueError as exc:
        raise InvalidRequestError("as_of_date", "must be YYYY-MM-DD") from exc
    if curr_dt.strftime("%Y-%m-%d") != as_of_date:
        raise InvalidRequestError("as_of_date", "must be YYYY-MM-DD")
    if isinstance(look_back_days, bool) or not isinstance(look_back_days, int) or look_back_days < 0:
        raise InvalidRequestError("look_back_days", "must be a non-negative integer")
    start_dt = curr_dt - timedelta(days=look_back_days)
    request = MacroNewsRequest(
        topics=DEFAULT_TOPIC_ORDER,
        start_at=start_dt.replace(tzinfo=UTC),
        end_at=(curr_dt + timedelta(days=1) - timedelta(microseconds=1)).replace(tzinfo=UTC),
        limit=limit,
        rules_version=rules_version,
    )
    return _validate_request(request)


def _o5_timestamp(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        raise ValueError("O5 candidate timestamp must be timezone-aware")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _o5_canonical_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _o5_canonical_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    netloc = host if port is None or default_port else f"{host}:{port}"
    if parsed.username:
        credentials = parsed.username
        if parsed.password:
            credentials += f":{parsed.password}"
        netloc = f"{credentials}@{netloc}"
    return urlunsplit((scheme, netloc, parsed.path.rstrip("/"), "", ""))


def _map_news_dict_to_candidate(data: dict) -> MacroNewsCandidate:
    """Map extracted Yahoo fields without rewriting their business values."""
    title = data["title"]
    source = data["publisher"]
    url = data["link"]
    published_at = data["pub_date"]
    parts = (
        _o5_canonical_text(title), _o5_canonical_text(source),
        _o5_canonical_url(url), _o5_timestamp(published_at),
    )
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:32]
    return MacroNewsCandidate(
        candidate_id=f"o5:{digest}", title=title, summary=data["summary"],
        source=source, url=url, published_at=published_at,
    )


def _map_selected_to_article_dict(record: SelectedRecord) -> dict:
    return {
        "title": record.title, "summary": record.summary,
        "publisher": record.source, "link": record.url,
        "pub_date": record.published_at,
    }


def _o5_batch_id(request: MacroNewsRequest, candidates: list[MacroNewsCandidate]) -> str:
    records = [
        {
            "title": item.title, "summary": item.summary,
            "source": item.source, "url": item.url,
            "published_at": _o5_timestamp(item.published_at),
        }
        for item in candidates
    ]
    payload = {
        "rules_version": request.rules_version, "limit": request.limit,
        "topics": list(request.topics),
        "start_at_iso": _o5_timestamp(request.start_at),
        "end_at_iso": _o5_timestamp(request.end_at),
        "records": records,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return "b:" + hashlib.sha256(encoded).hexdigest()


class O5InvariantError(ValueError):
    def __init__(self, invariant: str):
        self.invariant = invariant
        super().__init__(invariant)


def _check_o5_invariants(
    candidates: list[MacroNewsCandidate], request: MacroNewsRequest, result: SelectorResult,
) -> None:
    """Check the runtime invariants before any selected article is published."""
    supplied = {}
    for item in candidates:
        supplied.setdefault(item.candidate_id, item)
    selected_ids = [item.candidate_id for item in result.selected]
    decision_ids = [item.candidate_id for item in result.decisions
                    if item.disposition == "SELECTED"]
    if (len(selected_ids) != len(set(selected_ids))
            or any(item_id not in supplied for item_id in selected_ids)
            or len(selected_ids) > request.limit
            or len(result.decisions) != len(candidates)
            or [item.input_index for item in result.decisions] != list(range(len(candidates)))
            or set(selected_ids) != set(decision_ids)
            or result.counts()["input_count"] != len(candidates)):
        raise O5InvariantError("INV-O5-02")
    for item in result.selected:
        original = supplied[item.candidate_id]
        if (item.title, item.summary, item.source, item.url, item.published_at) != (
            original.title, original.summary, original.source, original.url,
            original.published_at,
        ):
            raise O5InvariantError("INV-O5-01")
        timestamp = item.published_at
        if (timestamp is None or timestamp.tzinfo is None
                or not request.start_at <= timestamp.astimezone(UTC) <= request.end_at):
            raise O5InvariantError("INV-O5-03")


def _o5_reason_counts(result: SelectorResult) -> dict[str, int]:
    return dict(sorted(Counter(item.reason_code for item in result.decisions).items()))


def _select_o5_batch(
    articles: list[dict], request: MacroNewsRequest,
) -> tuple[SelectorResult, str]:
    candidates = [_map_news_dict_to_candidate(article) for article in articles]
    result = select_macro_news(candidates, request)
    _check_o5_invariants(candidates, request, result)
    return result, _o5_batch_id(request, candidates)


def _o5_empty_kind(result: SelectorResult) -> str:
    """Pick the V-FILTERED-EMPTY ``empty_kind`` for this batch.

    The enum values are fixed by Interface section 4 (M2/§4); which member
    applies to an all-irrelevant filtered batch still awaits D's confirmation,
    so no test pins this literal.
    """
    codes = {item.reason_code for item in result.decisions}
    if codes and codes <= {"NO_MACRO_EVIDENCE"}:
        return "ALL_IRRELEVANT"
    return "MIXED_NONE_RELEVANT"


def _o5_invariant_failure_text() -> str:
    """Provisional suppression notice; D must confirm the exact wording."""
    return (
        "Fetched candidate(s) whose selected subset failed an integrity check, "
        "so no articles are shown. This is not an absence of news."
    )


def _o5_filtered_empty_text(count: int) -> str:
    """Provisional wording, isolated so D can confirm without touching flow."""
    return (
        f"Fetched {count} candidate(s); none carry the requested macro evidence. "
        "This is a filter result, not a statement that no macro news exists."
    )


def _extract_article_data(article: dict) -> dict:
    """Extract article data from yfinance news format (handles nested 'content' structure).

    Yahoo sends some fields as null rather than leaving them out, so each falls
    back to its default on a null as well as on a missing key (#1458).
    """
    content = article.get("content")
    if isinstance(content, dict):
        url_obj = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        pub_date_str = content.get("pubDate") or ""
        pub_date = None
        if pub_date_str:
            with contextlib.suppress(ValueError, AttributeError):
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))

        return {
            "title": content.get("title") or "No title",
            "summary": content.get("summary") or "",
            "publisher": (content.get("provider") or {}).get("displayName") or "Unknown",
            "link": url_obj.get("url") or "",
            "pub_date": pub_date,
        }
    # Fallback for flat structure. Parse the epoch publish time so flat
    # articles are date-filterable too (otherwise they bypass the
    # historical window and leak future news, #992/#1007).
    pub_date = None
    ts = article.get("providerPublishTime")
    if ts:
        # Epoch seconds are UTC; parse them as UTC-aware so filtering does
        # not shift with the host timezone (#1126).
        with contextlib.suppress(ValueError, OSError, TypeError):
            pub_date = datetime.fromtimestamp(ts, tz=UTC)
    return {
        "title": article.get("title") or "No title",
        "summary": article.get("summary") or "",
        "publisher": article.get("publisher") or "Unknown",
        "link": article.get("link") or "",
        "pub_date": pub_date,
    }


def _search_news(canonical: str, limit: int) -> tuple[list, bool]:
    """Yahoo search's articles tagged with ``canonical``, and whether it knows the symbol.

    Search answers when the quote feed is empty, but its articles are a
    relevance-picked sample, and some are tagged loosely; only those tagged with
    the symbol are about it.
    """
    search = yf_retry(lambda: yf.Search(canonical, news_count=limit))
    if search is None:  # Yahoo answered "not found": its search is down
        return [], False
    tagged = [
        a for a in (search.news or [])
        if canonical in (t.upper() for t in a.get("relatedTickers") or [])
    ]
    knows = any((q.get("symbol") or "").upper() == canonical for q in search.quotes or [])
    return tagged, knows or bool(search.news)


def _format_articles(articles: list[dict]) -> str:
    out = ""
    for data in articles:
        out += f"### {data['title']} (source: {data['publisher']})\n"
        if data["summary"]:
            out += f"{data['summary']}\n"
        if data["link"]:
            out += f"Link: {data['link']}\n"
        out += "\n"
    return out


def get_news_yfinance(
    ticker: str,
    start_date: str,
    end_date: str,
) -> str:
    """News about ``ticker`` published in the window, from Yahoo Finance.

    The symbol's quote feed comes first. When it is empty, Yahoo search serves
    the articles tagged with the symbol; when it has none, or neither answers,
    Yahoo news is unavailable, which is not an absence of news, and a configured
    next vendor is tried. Search results are a sample, so finding none in the
    window never reads as "no news".
    """
    article_limit = get_config()["news_article_limit"]
    # Query Yahoo with the canonical symbol, like every other yfinance path —
    # a raw broker/forex/crypto alias (XAUUSD, BTCUSD) otherwise silently
    # returns no news. Keep the user's ticker in the report header.
    canonical = normalize_symbol(ticker)
    resolved = "" if canonical == ticker else f" (resolved to {canonical})"
    subject = f"news for {ticker}{resolved}"
    feed = yf_retry(lambda: yf.Ticker(canonical).get_news(count=article_limit)) or []
    articles = [_extract_article_data(a) for a in feed]
    if not feed:
        found, answered = _search_news(canonical, article_limit)
        if not answered:
            raise VendorUnavailableError(f"Yahoo Finance returned no news response for {canonical}")
        if not found:
            # With the quote feed empty, no tagged article says nothing about the
            # company's news (Yahoo tags no article with most non-US listings).
            raise VendorUnavailableError(f"Yahoo Finance has no news articles tagged {canonical}")
        articles = [_extract_article_data(a) for a in found]

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    # Keep only articles within the requested window (look-ahead safe).
    in_range = [a for a in articles if in_window(a["pub_date"], start_dt, end_dt)]
    if in_range:
        return f"## {ticker}{resolved} News, from {start_date} to {end_date}:\n\n{_format_articles(in_range)}"

    if not feed:
        return (f"<Yahoo Finance news unavailable for {start_date}..{end_date}: Yahoo search "
                f"returns only a sample of recent articles about {canonical}, so this is not "
                f"an absence of {subject}>")
    gap = coverage_gap(
        (a["pub_date"] for a in articles),
        start_date, end_date, "Yahoo Finance news", subject,
    )
    return gap or f"No news found for {ticker}{resolved} between {start_date} and {end_date}"


def get_global_news_yfinance(
    as_of_date: str,
    look_back_days: int | None = None,
    limit: int | None = None,
) -> str:
    """
    Retrieve global/macro economic news using yfinance Search.

    Args:
        as_of_date: Current date in yyyy-mm-dd format
        look_back_days: Number of days to look back. ``None`` falls back to
            ``global_news_lookback_days`` from the active config.
        limit: Maximum number of articles to return. ``None`` falls back to
            ``global_news_article_limit`` from the active config.

    Returns:
        Formatted string containing global news articles
    """
    config = get_config()
    if look_back_days is None:
        look_back_days = config["global_news_lookback_days"]
    if limit is None:
        limit = config["global_news_article_limit"]
    search_queries = config["global_news_queries"]

    try:
        request = _build_o5_request(as_of_date, look_back_days, limit)
    except InvalidRequestError as exc:
        _record_o5_evidence(
            "V-INVALID-REQUEST", rules_resolved=False,
            field=exc.field, reason=exc.reason,
        )
        raise
    curr_dt = request.end_at.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
    start_dt = request.start_at.replace(tzinfo=None)
    start_date = start_dt.strftime("%Y-%m-%d")

    if limit == 0:
        _record_o5_evidence(
            "V-LIMIT-ZERO", batch_id=None, input_count=0,
            executed_query_count=0, pre_filter_candidate_count=0,
        )
        return "LIMIT_ZERO: no global news requested."

    in_window_news = []
    seen_titles = set()
    executed_query_count = 0

    # Scope: the collector keeps its approved early stop at ``len >= limit``
    # raw in-window candidates. Queries are never revisited because the fetched
    # candidates turned out to be irrelevant — those queries stay unfetched and
    # are outside the O5 selector's claim (REQ-O5-08: no added requests).
    for query in search_queries:
        executed_query_count += 1
        try:
            found = yf_retry(lambda q=query: yf.Search(
                query=q,
                news_count=limit,
                enable_fuzzy_query=True,
            ).news)
        except VendorUnavailableError as exc:
            if in_window_news:
                _record_o5_evidence(
                    "V-PARTIAL", batch_id=None, input_count=None,
                    reason_counts=None, executed_query_count=executed_query_count,
                    queries_failed=1, pre_filter_candidate_count=len(in_window_news),
                )
            else:
                message = str(exc).casefold()
                trigger = ("VENDOR_RATE_LIMIT" if "rate limit" in message
                           else "VENDOR_TIMEOUT" if "timeout" in message
                           else "VENDOR_UNAVAILABLE")
                _record_o5_evidence(
                    "V-VENDOR", trigger=trigger, batch_id=None,
                    input_count=None, selected_count=None, reason_counts=None,
                    pre_filter_candidate_count=None, vendor="yfinance",
                    method="Search", executed_query_count=executed_query_count,
                )
            raise

        for article in found or []:
            # Window first: the limit counts what the run may read, so an
            # out-of-window article must not spend the budget or cut the
            # remaining searches short (#1356). Flat articles are filtered
            # on the same rule, so none can leak future news (#1007).
            data = _extract_article_data(article)
            if not in_window(data["pub_date"], start_dt, curr_dt):
                continue
            if data["title"] and data["title"] not in seen_titles:
                seen_titles.add(data["title"])
                in_window_news.append(data)

        if len(in_window_news) >= limit:
            break

    # Nothing fell inside the window -> say so rather than return an
    # empty-bodied report (#993).
    if not in_window_news:
        _record_o5_evidence(
            "V-UPSTREAM-EMPTY", batch_id=None, input_count=None,
            selected_count=None, reason_counts=None,
            executed_query_count=executed_query_count,
            pre_filter_candidate_count=0,
        )
        # Results merge several fuzzy searches, so their timestamps prove no
        # continuous coverage; judge the window against the present only.
        gap = coverage_gap((), start_date, as_of_date, "Yahoo Finance global news", "market news")
        return gap or f"No global news found between {start_date} and {as_of_date}"

    # O5 selection happens on the whole pre-slice pool, before any truncation,
    # so an early article can never crowd out later macro evidence.
    try:
        result, batch_id = _select_o5_batch(in_window_news, request)
    except O5InvariantError as exc:
        # The batch is suppressed: no selected article is published. The public
        # function must still return ``str`` and must not claim either success or
        # an upstream outage, so it returns a caller-facing suppression notice
        # rather than raising a non-vendor exception through the router.
        _record_o5_evidence(
            "V-INVARIANT", batch_id=None, violated_invariant=exc.invariant,
            pre_suppression_selected_count=0, published_selected_count=0,
        )
        return _o5_invariant_failure_text()

    if not result.selected:
        _record_o5_evidence(
            "V-FILTERED-EMPTY", batch_id=batch_id,
            input_count=result.counts()["input_count"], selected_count=0,
            reason_counts=_o5_reason_counts(result),
            executed_query_count=executed_query_count,
            pre_filter_candidate_count=len(in_window_news),
            empty_kind=_o5_empty_kind(result),
        )
        return _o5_filtered_empty_text(len(in_window_news))

    _record_o5_evidence(
        "V-SELECTED", batch_id=batch_id,
        input_count=result.counts()["input_count"],
        selected_count=len(result.selected),
        reason_counts=_o5_reason_counts(result),
        executed_query_count=executed_query_count,
        pre_filter_candidate_count=len(in_window_news),
    )
    news_str = _format_articles([_map_selected_to_article_dict(item) for item in result.selected])
    return f"## Global Market News, from {start_date} to {as_of_date}:\n\n{news_str}"
