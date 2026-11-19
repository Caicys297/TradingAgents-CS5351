"""O5 macro-news selector: deterministic filtering and topic allocation.

S1 scope (execution plan v1.4 section 5a). A pure function over already-fetched
records: no I/O, no network, no LLM calls, no wall-clock reads. Retrieval,
evidence emission, persistence and the ``news.py`` adapter are later stages.

The contract implemented here is the merged O5 registry contract plus the
Interface evidence contract:
  * topics are matched with the versioned rule tables (R1-MP, R2-IN, R3-EA);
  * an anchor and its context must be in the same field (title or summary),
    and pairing may cross clause boundaries inside that field;
  * allocation is round-robin over the requested topic order, each bucket
    sorted by ``published_at`` descending then ``candidate_id`` ascending;
  * every input position gets exactly one decision;
  * counts conserve: input == selected + not_selected_limit + irrelevant +
    invalid + out_of_window + duplicate + skipped_zero_limit.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# Keep a stable handle on the stdlib class for isinstance checks.
_StdlibDateTime = datetime

MONETARY_POLICY = "MONETARY_POLICY"
INFLATION = "INFLATION"
ECONOMIC_ACTIVITY = "ECONOMIC_ACTIVITY"

DEFAULT_TOPIC_ORDER: tuple[str, ...] = (
    MONETARY_POLICY,
    INFLATION,
    ECONOMIC_ACTIVITY,
)

RULES_VERSION = "o5-rules-v1.1-draft"

# Decision dispositions.
SELECTED = "SELECTED"
NOT_SELECTED_LIMIT = "NOT_SELECTED_LIMIT"
REJECTED = "REJECTED"
INVALID = "INVALID"
OUT_OF_WINDOW = "OUT_OF_WINDOW"
DUPLICATE_ID = "DUPLICATE_ID"
ZERO_LIMIT = "ZERO_LIMIT"

# Reason codes.
REASON_INVALID_RECORD = "INVALID_RECORD"
REASON_INVALID_TITLE = "INVALID_TITLE"
REASON_INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
REASON_NO_MACRO_EVIDENCE = "NO_MACRO_EVIDENCE"

STATUS_OK = "OK"
STATUS_NO_RELEVANT_NEWS = "NO_RELEVANT_NEWS"
STATUS_LIMIT_ZERO = "LIMIT_ZERO"

# The registry rule catalog (requirements.yaml development_contract.o5.rules).
RULE_TABLE: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "R1-MP",
        MONETARY_POLICY,
        (
            "federal reserve",
            "fed",
            "ecb",
            "bank of england",
            "boe",
            "bank of japan",
            "boj",
            "central bank",
            "monetary policy",
        ),
        (
            "rate",
            "rates",
            "policy",
            "basis points",
            "hike",
            "hikes",
            "cut",
            "cuts",
            "unchanged",
            "holds",
            "held",
            "easing",
            "tightening",
            "normalization",
            "quantitative easing",
            "qe",
            "minutes",
        ),
    ),
    (
        "R2-IN",
        INFLATION,
        (
            "inflation",
            "cpi",
            "consumer price index",
            "pce",
            "core pce",
            "disinflation",
            "deflation",
            "price pressure",
            "price pressures",
        ),
        (
            "percent",
            "%",
            "year over year",
            "yoy",
            "falls",
            "fall",
            "rise",
            "rises",
            "rose",
            "holds",
            "held",
            "cools",
            "eases",
            "eased",
            "easing",
            "target",
            "sticky",
            "pressures",
        ),
    ),
    (
        "R3-EA",
        ECONOMIC_ACTIVITY,
        (
            "gdp",
            "payrolls",
            "nonfarm payrolls",
            "unemployment",
            "jobless",
            "pmi",
            "recession",
            "retail sales",
            "industrial production",
            "manufacturing",
            "consumer spending",
        ),
        (
            "percent",
            "%",
            "growth",
            "grows",
            "contract",
            "contraction",
            "expansion",
            "rose",
            "fell",
            "ticks up",
            "ticked up",
            "beats",
            "beating",
            "forecasts",
            "worries",
            "signals",
            "resilient",
            "slips",
        ),
    ),
)

# R2 numeric context: a bare ``cpi`` with no numeric or percent token in the
# same field is a company name, not a statistic (Requirements section 5.3).
_R2_GAME_CONTEXT = ("game economy", "virtual economy", "expansion pack")

# ``%`` is split into its own token; other boundary punctuation is dropped.
_PERCENT = "\x00"
_TOKEN_RE = re.compile(r"[0-9a-z+.\-]+|\x00")


class InvalidRequestError(ValueError):
    """The request itself is invalid; no selector run is possible."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"invalid request: {field}: {reason}")


@dataclass(frozen=True)
class MacroNewsCandidate:
    """A normalized candidate record handed to the selector."""

    candidate_id: str
    title: str
    summary: str = ""
    published_at: datetime | None = None
    source: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class MacroNewsRequest:
    """The validated selector request."""

    topics: tuple[str, ...]
    start_at: datetime
    end_at: datetime
    limit: int
    rules_version: str = RULES_VERSION


@dataclass(frozen=True)
class Decision:
    input_index: int
    candidate_id: str | None
    disposition: str
    reason_code: str
    matched_topics: tuple[str, ...] = ()
    matched_rule_ids: tuple[str, ...] = ()
    topic: str | None = None
    negated: bool = False


@dataclass(frozen=True)
class SelectedRecord:
    candidate_id: str
    title: str
    summary: str
    source: str | None
    url: str | None
    published_at: datetime | None
    matched_topics: tuple[str, ...]
    primary_topic: str
    matched_rule_ids: tuple[str, ...]
    negated: bool = False


@dataclass
class SelectorResult:
    selected: list[SelectedRecord] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    status: str = STATUS_OK
    rules_version: str = RULES_VERSION
    topic_order: tuple[str, ...] = DEFAULT_TOPIC_ORDER

    def counts(self) -> dict[str, int]:
        buckets = {
            "selected_count": 0,
            "not_selected_limit_count": 0,
            "irrelevant_count": 0,
            "invalid_count": 0,
            "out_of_window_count": 0,
            "duplicate_count": 0,
            "skipped_zero_limit_count": 0,
        }
        for decision in self.decisions:
            if decision.disposition == SELECTED:
                buckets["selected_count"] += 1
            elif decision.disposition == NOT_SELECTED_LIMIT:
                buckets["not_selected_limit_count"] += 1
            elif decision.disposition == REJECTED:
                buckets["irrelevant_count"] += 1
            elif decision.disposition == INVALID:
                buckets["invalid_count"] += 1
            elif decision.disposition == OUT_OF_WINDOW:
                buckets["out_of_window_count"] += 1
            elif decision.disposition == DUPLICATE_ID:
                buckets["duplicate_count"] += 1
            elif decision.disposition == ZERO_LIMIT:
                buckets["skipped_zero_limit_count"] += 1
        return {"input_count": len(self.decisions), **buckets}


def _tokenize(text: str) -> tuple[str, ...]:
    """NFKC + casefold, split ``%`` to its own token, strip boundary punctuation."""

    folded = unicodedata.normalize("NFKC", text).casefold().replace("%", f" {_PERCENT} ")
    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(folded):
        raw = match.group(0)
        if raw == _PERCENT:
            tokens.append("%")
            continue
        cleaned = raw.strip(".-")
        if cleaned:
            tokens.append(cleaned)
    return tuple(tokens)


def _phrase_present(tokens: Sequence[str], phrase: str) -> bool:
    parts = phrase.split()
    if not parts:
        return False
    width = len(parts)
    for index in range(len(tokens) - width + 1):
        if list(tokens[index : index + width]) == parts:
            return True
    return False


def _field_matches_rule(field_tokens: Sequence[str], anchors, context) -> str | None:
    for anchor in anchors:
        if not _phrase_present(field_tokens, anchor):
            continue
        for term in context:
            if _phrase_present(field_tokens, term):
                return anchor
    return None


def _excluded(rule_id: str, tokens: Sequence[str]) -> bool:
    if rule_id == "R2-IN":
        if any(_phrase_present(tokens, phrase) for phrase in _R2_GAME_CONTEXT):
            return True
        if _phrase_present(tokens, "cpi"):
            has_numeric = any(
                token == "%" or any(char.isdigit() for char in token) for token in tokens
            )
            if not has_numeric:
                return True
    return False


def classify(title: str, summary: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return matched topics (request order) and the rule ids that fired."""

    title_tokens = _tokenize(title)
    summary_tokens = _tokenize(summary or "")
    fired: list[tuple[str, str]] = []
    for rule_id, topic, anchors, context in RULE_TABLE:
        matched = False
        for tokens in (title_tokens, summary_tokens):
            anchor = _field_matches_rule(tokens, anchors, context)
            if anchor is not None and not _excluded(rule_id, tokens):
                matched = True
                break
        if matched:
            fired.append((rule_id, topic))
    topics: list[str] = []
    rule_ids: list[str] = []
    for rule_id, topic in fired:
        rule_ids.append(rule_id)
        if topic not in topics:
            topics.append(topic)
    return tuple(topics), tuple(rule_ids)


def _validate_request(request: MacroNewsRequest) -> MacroNewsRequest:
    limit = request.limit
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise InvalidRequestError("limit", "must be an integer, not a boolean or float")
    if limit < 0:
        raise InvalidRequestError("limit", "must be non-negative")
    topics = tuple(request.topics)
    if not topics:
        raise InvalidRequestError("topics", "must be non-empty")
    if len(set(topics)) != len(topics):
        raise InvalidRequestError("topics", "must not repeat a topic")
    for topic in topics:
        if topic not in DEFAULT_TOPIC_ORDER:
            raise InvalidRequestError("topics", f"unsupported topic {topic!r}")
    start_at, end_at = request.start_at, request.end_at
    # ``isinstance`` against the stdlib class (not the module-local name) so a
    # test that swaps the module's clock hook cannot make valid datetimes fail.
    if not isinstance(start_at, _StdlibDateTime) or not isinstance(end_at, _StdlibDateTime):
        raise InvalidRequestError("window", "start_at and end_at must be datetimes")
    if start_at.tzinfo is None or end_at.tzinfo is None:
        raise InvalidRequestError("window", "start_at and end_at must be timezone-aware")
    if start_at > end_at:
        raise InvalidRequestError("window", "start_at is after end_at")
    if request.rules_version != RULES_VERSION:
        raise InvalidRequestError(
            "rules_version", f"unsupported rules version {request.rules_version!r}"
        )
    return MacroNewsRequest(
        topics=topics,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
        rules_version=request.rules_version,
    )


def _record_of(candidate: Any) -> MacroNewsCandidate | None:
    """Coerce one supplied item into a candidate, or None when structurally invalid."""

    if isinstance(candidate, MacroNewsCandidate):
        if not isinstance(candidate.candidate_id, str) or not candidate.candidate_id:
            return None
        if not isinstance(candidate.title, str):
            return None
        if candidate.summary is None:
            candidate = MacroNewsCandidate(
                candidate.candidate_id, candidate.title, "", candidate.published_at,
                candidate.source, candidate.url,
            )
        if not isinstance(candidate.summary, str):
            return None
        if candidate.published_at is not None and not isinstance(
                candidate.published_at, _StdlibDateTime):
            return None
        if candidate.source is not None and not isinstance(candidate.source, str):
            return None
        if candidate.url is not None and not isinstance(candidate.url, str):
            return None
        return candidate
    if not isinstance(candidate, Mapping):
        return None
    candidate_id = candidate.get("candidate_id")
    title = candidate.get("title")
    if not isinstance(candidate_id, str) or not candidate_id:
        return None
    if not isinstance(title, str):
        return None
    summary = candidate.get("summary", "")
    if summary is None:
        summary = ""
    if not isinstance(summary, str):
        return None
    published_at = candidate.get("published_at")
    if published_at is not None and not isinstance(published_at, datetime):
        # A string or other type at the selector boundary is a structural error.
        return None
    source = candidate.get("source")
    url = candidate.get("url")
    if source is not None and not isinstance(source, str):
        return None
    if url is not None and not isinstance(url, str):
        return None
    return MacroNewsCandidate(
        candidate_id=candidate_id,
        title=title,
        summary=summary,
        published_at=published_at,
        source=source,
        url=url,
    )


def _in_window(published_at: datetime | None, start_at: datetime, end_at: datetime) -> bool:
    if published_at is None:
        return False
    if published_at.tzinfo is None:
        return False
    moment = published_at.astimezone(UTC)
    return start_at.astimezone(UTC) <= moment <= end_at.astimezone(UTC)


def _request_order(matched_topics: Sequence[str], requested: Sequence[str]) -> tuple[str, ...]:
    """Matched topics filtered to the request and ordered by the request order."""

    present = set(matched_topics)
    return tuple(topic for topic in requested if topic in present)


def _order_rule_ids(
    matched_topics: Sequence[str], rule_ids: Sequence[str], requested: Sequence[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return topics and rule ids filtered to the request, aligned and request-ordered.

    ``classify`` emits one rule id per matched topic in rule-table order; re-pair
    them with their topics so the request order governs both sequences.
    """

    pairs = dict(zip(matched_topics, rule_ids, strict=True))
    ordered_topics = _request_order(matched_topics, requested)
    ordered_rules = tuple(pairs[topic] for topic in ordered_topics)
    return ordered_topics, ordered_rules


def _primary_topic(matched_topics: Sequence[str], requested: Sequence[str]) -> str | None:
    ordered = _request_order(matched_topics, requested)
    return ordered[0] if ordered else None


def select_macro_news(
    candidates: Sequence[Any],
    request: MacroNewsRequest,
) -> SelectorResult:
    """Filter and allocate already-fetched candidates (pure, deterministic)."""

    request = _validate_request(request)
    items = list(candidates)
    topic_order = request.topics

    if request.limit == 0:
        decisions = [
            Decision(
                input_index=index,
                candidate_id=_coerce_id(item),
                disposition=ZERO_LIMIT,
                reason_code="ZERO_LIMIT",
            )
            for index, item in enumerate(items)
        ]
        return SelectorResult(
            selected=[],
            decisions=decisions,
            status=STATUS_LIMIT_ZERO,
            rules_version=request.rules_version,
            topic_order=topic_order,
        )

    decisions: list[Decision] = []
    reserved: set[str] = set()
    buckets: dict[str, list[tuple[datetime, str, MacroNewsCandidate, tuple[str, ...], tuple[str, ...]]]] = {
        topic: [] for topic in topic_order
    }

    for index, item in enumerate(items):
        record = _record_of(item)
        if record is None:
            decisions.append(
                Decision(
                    input_index=index,
                    candidate_id=_coerce_id(item),
                    disposition=INVALID,
                    reason_code=REASON_INVALID_RECORD,
                )
            )
            continue
        if record.candidate_id in reserved:
            decisions.append(
                Decision(
                    input_index=index,
                    candidate_id=record.candidate_id,
                    disposition=DUPLICATE_ID,
                    reason_code=DUPLICATE_ID,
                )
            )
            continue
        reserved.add(record.candidate_id)
        if not record.title or record.title == "No title":
            decisions.append(
                Decision(
                    input_index=index,
                    candidate_id=record.candidate_id,
                    disposition=INVALID,
                    reason_code=REASON_INVALID_TITLE,
                )
            )
            continue
        if record.published_at is None or record.published_at.tzinfo is None:
            decisions.append(
                Decision(
                    input_index=index,
                    candidate_id=record.candidate_id,
                    disposition=INVALID,
                    reason_code=REASON_INVALID_TIMESTAMP,
                )
            )
            continue
        if not _in_window(record.published_at, request.start_at, request.end_at):
            decisions.append(
                Decision(
                    input_index=index,
                    candidate_id=record.candidate_id,
                    disposition=OUT_OF_WINDOW,
                    reason_code=OUT_OF_WINDOW,
                )
            )
            continue
        topics, rule_ids = classify(record.title, record.summary)
        topics, rule_ids = _order_rule_ids(topics, rule_ids, topic_order)
        primary = topics[0] if topics else None
        if primary is None:
            decisions.append(
                Decision(
                    input_index=index,
                    candidate_id=record.candidate_id,
                    disposition=REJECTED,
                    reason_code=REASON_NO_MACRO_EVIDENCE,
                )
            )
            continue
        buckets[primary].append((record.published_at, record.candidate_id, record, topics, rule_ids))
        decisions.append(
            Decision(
                input_index=index,
                candidate_id=record.candidate_id,
                disposition=SELECTED,
                reason_code=SELECTED,
                matched_topics=topics,
                matched_rule_ids=rule_ids,
                topic=primary,
            )
        )

    for topic in topic_order:
        buckets[topic].sort(key=lambda entry: (-entry[0].timestamp(), entry[1]))

    selected: list[SelectedRecord] = []
    consumed: set[str] = set()
    level = 0
    while len(selected) < request.limit:
        progressed = False
        for topic in topic_order:
            bucket = buckets[topic]
            if level < len(bucket):
                _, candidate_id, record, topics, rule_ids = bucket[level]
                if candidate_id not in consumed:
                    consumed.add(candidate_id)
                    selected.append(
                        SelectedRecord(
                            candidate_id=record.candidate_id,
                            title=record.title,
                            summary=record.summary,
                            source=record.source,
                            url=record.url,
                            published_at=record.published_at,
                            matched_topics=topics,
                            primary_topic=topic,
                            matched_rule_ids=rule_ids,
                        )
                    )
                progressed = True
                if len(selected) >= request.limit:
                    break
        if not progressed:
            break
        level += 1

    final_decisions: list[Decision] = []
    for decision in decisions:
        if decision.disposition == SELECTED and decision.candidate_id not in consumed:
            final_decisions.append(
                Decision(
                    input_index=decision.input_index,
                    candidate_id=decision.candidate_id,
                    disposition=NOT_SELECTED_LIMIT,
                    reason_code=NOT_SELECTED_LIMIT,
                    matched_topics=decision.matched_topics,
                    matched_rule_ids=decision.matched_rule_ids,
                    topic=decision.topic,
                )
            )
        else:
            final_decisions.append(decision)

    status = STATUS_OK if selected else STATUS_NO_RELEVANT_NEWS
    return SelectorResult(
        selected=selected,
        decisions=final_decisions,
        status=status,
        rules_version=request.rules_version,
        topic_order=topic_order,
    )


def _coerce_id(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("candidate_id")
        return value if isinstance(value, str) else None
    if isinstance(item, MacroNewsCandidate):
        return item.candidate_id
    return None
