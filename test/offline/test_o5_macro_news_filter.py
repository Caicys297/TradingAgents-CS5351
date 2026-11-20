"""O5 S1 selector cases (test plan v1.7, inventory section 4: 48 rows).

Every case asserts the *selector* contract only: no adapter evidence emission,
no persistence, no public wording. Expected values come from the approved
inventory/DEV20 fixture, never from the implementation's own output.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tradingagents.dataflows import macro_news_filter as o5

MP = "MONETARY_POLICY"
IN = "INFLATION"
EA = "ECONOMIC_ACTIVITY"
TOPICS = (MP, IN, EA)
# Pinned independently of the production constant: an accidental change to the
# selector's literal must not silently update the expected test input.
RULES = "o5-rules-v1.1-draft"

WINDOW_START = datetime(2026, 9, 20, 0, 0, 0, tzinfo=UTC)
WINDOW_END = datetime(2026, 9, 27, 23, 59, 59, 999999, tzinfo=UTC)

FIXTURE_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "o5" / "O5-Dev20-Fixtures-v0.5.3-DRAFT.json"
)
# Approved Registry bytes (d36a677): 24,291 bytes with CRLF line endings.
FIXTURE_SHA256 = "a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6"
FIXTURE_BYTES = 24291

COUNT_KEYS = (
    "input_count",
    "selected_count",
    "not_selected_limit_count",
    "irrelevant_count",
    "invalid_count",
    "out_of_window_count",
    "duplicate_count",
    "skipped_zero_limit_count",
)


# --------------------------------------------------------------------------- helpers


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_dev20_fixture_is_the_approved_bytes():
    """The shipped copy must be the Registry file byte-for-byte, not a rewrite."""

    raw = FIXTURE_PATH.read_bytes()
    assert len(raw) == FIXTURE_BYTES
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA256
    assert b"\r\n" in raw  # CRLF preserved, so no checkout/commit conversion slipped in


def dev20_candidates(fixture: dict) -> list[o5.MacroNewsCandidate]:
    out = []
    for record in fixture["candidates"]:
        out.append(
            o5.MacroNewsCandidate(
                candidate_id=record["candidate_id"],
                title=record["title"],
                summary=record["summary"] or "",
                published_at=datetime.fromisoformat(record["published_at"].replace("Z", "+00:00")),
                source=record["source"],
                url=record["url"],
            )
        )
    return out


def request(topics=TOPICS, limit=20, start=WINDOW_START, end=WINDOW_END, rules=RULES):
    return o5.MacroNewsRequest(topics=tuple(topics), start_at=start, end_at=end, limit=limit,
                               rules_version=rules)


def P(candidate_id, title="Fed holds rates", summary="",
      at=datetime(2026, 9, 25, 0, 0, 0, tzinfo=UTC), source=None, url=None):
    """Complete test-record recipe: only the named overrides differ."""

    return o5.MacroNewsCandidate(candidate_id=candidate_id, title=title, summary=summary,
                                 published_at=at, source=source, url=url)


def counts_of(result) -> tuple[int, ...]:
    counts = result.counts()
    return tuple(counts[key] for key in COUNT_KEYS)


def selected_ids(result) -> list[str]:
    return [record.candidate_id for record in result.selected]


def decision_map(result) -> dict[int, o5.Decision]:
    return {decision.input_index: decision for decision in result.decisions}


def id_of(fixture: dict, key: str) -> str:
    return fixture["fixture_key_to_id"][key]


def assert_common_contract(result, supplied_records):
    """Shared selector assertions from inventory section 6a.

    ``supplied_records`` is the exact ordered input passed to
    ``select_macro_news``. Selected business fields are compared to their source
    records, and every input position is checked.
    """

    supplied_ids = [
        record.candidate_id if isinstance(record, o5.MacroNewsCandidate)
        else (record.get("candidate_id") if isinstance(record, dict) else None)
        for record in supplied_records
    ]

    counts = result.counts()
    assert counts["input_count"] == sum(counts[key] for key in COUNT_KEYS if key != "input_count")
    assert counts["input_count"] == len(result.decisions)
    assert [decision.input_index for decision in result.decisions] == list(
        range(len(result.decisions))
    )
    ids = [record.candidate_id for record in result.selected]
    assert len(ids) == len(set(ids))
    assert set(ids).issubset(set(supplied_ids))

    by_id = {record.candidate_id: record for record in supplied_records
             if isinstance(record, o5.MacroNewsCandidate)}
    for record in result.selected:
        source = by_id[record.candidate_id]
        assert record.title == source.title
        assert record.summary == (source.summary or "")
        assert record.source == source.source
        assert record.url == source.url
        assert record.published_at == source.published_at

    for decision in result.decisions:
        if decision.disposition == o5.SELECTED:
            assert decision.reason_code == o5.SELECTED
            assert decision.matched_topics
            assert decision.topic in decision.matched_topics
            assert decision.topic == decision.matched_topics[0]
        elif decision.disposition == o5.NOT_SELECTED_LIMIT:
            assert decision.reason_code == o5.NOT_SELECTED_LIMIT
            assert decision.matched_topics
        else:
            assert decision.reason_code
            assert decision.reason_code != o5.SELECTED


@pytest.fixture(scope="module")
def fixture():
    return load_fixture()


# --------------------------------------------------------------------------- DEV20 rows


@pytest.mark.unit
def test_t01_dev20_k20(fixture):
    supplied = dev20_candidates(fixture)
    result = o5.select_macro_news(supplied, request(limit=20))
    expected_keys = fixture["expected"]["k20_expected_selected_set"]
    expected_ids = {id_of(fixture, key) for key in expected_keys}
    assert set(selected_ids(result)) == expected_ids
    assert counts_of(result) == (20, 12, 0, 8, 0, 0, 0, 0)
    assert result.status == o5.STATUS_OK
    labels = {label["fixture_key"]: label for label in fixture["labels"]}
    by_id = {record.candidate_id: record for record in result.selected}
    for key in expected_keys:
        record = by_id[id_of(fixture, key)]
        assert list(record.matched_topics) == labels[key]["matched_topics"]
        assert record.primary_topic == labels[key]["primary_topic"]
    rejected = {decision.candidate_id for decision in result.decisions
                if decision.disposition == o5.REJECTED}
    assert rejected == {id_of(fixture, f"N0{i}") for i in range(1, 9)}
    assert_common_contract(result, supplied)


@pytest.mark.unit
def test_t02_dev20_k6(fixture):
    result = o5.select_macro_news(dev20_candidates(fixture), request(limit=6))
    assert selected_ids(result) == fixture["expected"]["k6_order_ids"]
    assert counts_of(result) == (20, 6, 6, 8, 0, 0, 0, 0)


@pytest.mark.unit
def test_t03a_dev20_k0(fixture, monkeypatch):
    calls = []
    original = o5.classify

    def trap(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(o5, "classify", trap)
    result = o5.select_macro_news(dev20_candidates(fixture), request(limit=0))
    assert calls == []  # K=0 short-circuits before classification
    assert result.status == o5.STATUS_LIMIT_ZERO
    assert all(decision.disposition == o5.ZERO_LIMIT for decision in result.decisions)
    assert counts_of(result) == (20, 0, 0, 0, 0, 0, 0, 20)
    assert result.selected == []


@pytest.mark.unit
def test_t03b_irrelevant_only(fixture):
    candidates = [record for record in dev20_candidates(fixture) if record.candidate_id in
                  {id_of(fixture, f"N0{i}") for i in range(1, 9)}]
    result = o5.select_macro_news(candidates, request(limit=3))
    assert result.status == o5.STATUS_NO_RELEVANT_NEWS
    assert counts_of(result) == (8, 0, 0, 8, 0, 0, 0, 0)


@pytest.mark.unit
def test_t03c_invalid_titles():
    payload = [
        {"candidate_id": "o5:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01", "title": "", "summary": "x",
         "source": None, "url": None, "published_at": "2026-09-25T00:00:00Z"},
        {"candidate_id": "o5:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02", "title": "No title", "summary": "y",
         "source": None, "url": None, "published_at": "2026-09-25T00:00:00Z"},
    ]
    candidates = [
        o5.MacroNewsCandidate(item["candidate_id"], item["title"], item["summary"],
                              datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")),
                              item["source"], item["url"])
        for item in payload
    ]
    result = o5.select_macro_news(candidates, request(limit=3))
    assert result.status == o5.STATUS_NO_RELEVANT_NEWS
    assert counts_of(result) == (2, 0, 0, 0, 2, 0, 0, 0)
    assert all(decision.disposition == o5.INVALID for decision in result.decisions)
    assert all(decision.reason_code == o5.REASON_INVALID_TITLE for decision in result.decisions)


@pytest.mark.unit
def test_t04a_empty_pool():
    result = o5.select_macro_news([], request(limit=20))
    assert result.selected == []
    assert counts_of(result) == (0, 0, 0, 0, 0, 0, 0, 0)
    assert result.status == o5.STATUS_NO_RELEVANT_NEWS


@pytest.mark.unit
def test_t05a_mp_only_recent():
    pool = [
        P("o5:b00000000000000000000000000001", "Fed holds rates steady at 5.25 percent",
          at=datetime(2026, 9, 26, 10, 0, 0, tzinfo=UTC)),
        P("o5:b00000000000000000000000000002", "ECB cuts deposit rate by 25 basis points",
          at=datetime(2026, 9, 25, 10, 0, 0, tzinfo=UTC)),
        P("o5:b00000000000000000000000000003", "Bank of Japan keeps policy rate unchanged",
          at=datetime(2026, 9, 24, 10, 0, 0, tzinfo=UTC)),
    ]
    result = o5.select_macro_news(pool, request(limit=2))
    assert selected_ids(result) == [
        "o5:b00000000000000000000000000001",
        "o5:b00000000000000000000000000002",
    ]
    assert counts_of(result) == (3, 2, 1, 0, 0, 0, 0, 0)


@pytest.mark.unit
def test_t05a_tie_order_by_id():
    pool = [P("c"), P("a"), P("b")]
    result = o5.select_macro_news(pool, request(limit=2))
    assert selected_ids(result) == ["a", "b"]
    assert decision_map(result)[0].disposition == o5.NOT_SELECTED_LIMIT
    assert counts_of(result) == (3, 2, 1, 0, 0, 0, 0, 0)


@pytest.mark.unit
def test_t05b_mixed_mp_ea_keeps_topic_order():
    pool = [
        P("mp", "Fed holds rates unchanged", at=datetime(2026, 9, 26, 10, 0, 0, tzinfo=UTC)),
        P("ea", "US payrolls rise 187,000 as unemployment ticks up",
          at=datetime(2026, 9, 27, 10, 0, 0, tzinfo=UTC)),
    ]
    result = o5.select_macro_news(pool, request(limit=2))
    assert selected_ids(result) == ["mp", "ea"]
    assert counts_of(result) == (2, 2, 0, 0, 0, 0, 0, 0)


@pytest.mark.unit
def test_t06_dev20_k2(fixture):
    result = o5.select_macro_news(dev20_candidates(fixture), request(limit=2))
    assert selected_ids(result) == fixture["expected"]["k2_order_ids"]
    assert counts_of(result) == (20, 2, 10, 8, 0, 0, 0, 0)


@pytest.mark.unit
def test_t20_no_padding_beyond_available():
    pool = [
        P("mp", "Fed holds rates unchanged", at=datetime(2026, 9, 26, 10, 0, 0, tzinfo=UTC)),
        P("ea", "US payrolls rise 187,000 as unemployment ticks up",
          at=datetime(2026, 9, 27, 10, 0, 0, tzinfo=UTC)),
    ]
    result = o5.select_macro_news(pool, request(limit=10))
    assert selected_ids(result) == ["mp", "ea"]
    assert counts_of(result) == (2, 2, 0, 0, 0, 0, 0, 0)


# --------------------------------------------------------------------------- duplicate/invalid rows


@pytest.mark.unit
@pytest.mark.parametrize("supported", ["dataclass", "mapping"])
def test_t07a_structural_invalid_first_does_not_reserve_id(supported):
    """A supported record with title=123 is INVALID_RECORD and must not reserve its ID."""

    at_first = datetime(2026, 9, 25, tzinfo=UTC)
    at_second = datetime(2026, 9, 26, tzinfo=UTC)
    if supported == "dataclass":
        # The accepted dataclass representation still gets structural validation.
        bad = o5.MacroNewsCandidate("dup-1", 123, "", at_first, None, None)
        good = P("dup-1", at=at_second)
    else:
        bad = {"candidate_id": "dup-1", "title": 123, "summary": "",
               "published_at": at_first, "source": None, "url": None}
        good = P("dup-1", at=at_second)

    pool = [bad, good]
    result = o5.select_macro_news(pool, request(limit=2))
    assert decision_map(result)[0].disposition == o5.INVALID
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_RECORD
    assert decision_map(result)[1].disposition == o5.SELECTED
    assert decision_map(result)[1].candidate_id == "dup-1"
    assert counts_of(result) == (2, 1, 0, 0, 1, 0, 0, 0)


@pytest.mark.unit
def test_t07b_out_of_window_first_reserves_id():
    pool = [
        P("dup-2", at=datetime(2026, 9, 10, tzinfo=UTC)),
        P("dup-2", at=datetime(2026, 9, 26, tzinfo=UTC)),
    ]
    result = o5.select_macro_news(pool, request(limit=2))
    assert decision_map(result)[0].disposition == o5.OUT_OF_WINDOW
    assert decision_map(result)[1].disposition == o5.DUPLICATE_ID
    assert counts_of(result) == (2, 0, 0, 0, 0, 1, 1, 0)


@pytest.mark.unit
def test_t07c_title_invalid_reserves_id():
    pool = [P("dup-3", title=""), P("dup-3", at=datetime(2026, 9, 26, tzinfo=UTC))]
    result = o5.select_macro_news(pool, request(limit=2))
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_TITLE
    assert decision_map(result)[1].disposition == o5.DUPLICATE_ID
    assert counts_of(result) == (2, 0, 0, 0, 1, 0, 1, 0)


@pytest.mark.unit
def test_t07d_duplicate_after_valid_selection():
    pool = [
        P("dup-4"),
        P("dup-4", title="", at=datetime(2026, 9, 26, tzinfo=UTC)),
    ]
    result = o5.select_macro_news(pool, request(limit=2))
    assert decision_map(result)[0].disposition == o5.SELECTED
    assert decision_map(result)[1].disposition == o5.DUPLICATE_ID
    assert counts_of(result) == (2, 1, 0, 0, 0, 0, 1, 0)


@pytest.mark.unit
def test_t07e_selector_does_not_mutate_inputs(fixture):
    candidates = dev20_candidates(fixture)
    req = request(limit=6)
    candidates_snapshot = copy.deepcopy(candidates)
    request_snapshot = copy.deepcopy(req)
    o5.select_macro_news(candidates, req)
    assert candidates == candidates_snapshot
    assert req == request_snapshot


# --------------------------------------------------------------------------- negative controls


@pytest.mark.unit
@pytest.mark.parametrize(
    "case_id,title,summary,expected_topics,expected_primary",
    [
        ("T08a", "FedEx expands parcel delivery service", "", (), None),
        ("T08b", "CPI Group reports quarterly earnings", "", (), None),
        ("T08c", "Game inflation rises in a virtual economy", "", (), None),
        ("T08d", "Fed holds rates at 5.25%, citing cooling CPI", "", (MP, IN), MP),
        ("T08e", "Tariffs spark debate", "Inflation rose 4 percent.", (IN,), IN),
        ("T08f", "S&P companies report earnings", "", (), None),
        ("T08g", "Economic release", "US CPI rose 3.0 percent year over year", (IN,), IN),
        ("T08h", "Fed holds rates as CPI cools to 2.1 percent", "", (MP, IN), MP),
        (
            "T08i",
            "Economic release",
            "Headline inflation eased toward the ECB target; core inflation held steady.",
            (MP, IN),
            MP,
        ),
    ],
)
def test_t08_negative_and_multitopic_controls(case_id, title, summary, expected_topics,
                                              expected_primary):
    supplied = [P(case_id, title, summary)]
    result = o5.select_macro_news(supplied, request(limit=1))
    assert_common_contract(result, supplied)
    if expected_topics:
        assert selected_ids(result) == [case_id]
        record = result.selected[0]
        assert record.matched_topics == expected_topics
        assert record.primary_topic == expected_primary
    else:
        assert result.selected == []
        assert decision_map(result)[0].disposition == o5.REJECTED


@pytest.mark.unit
def test_t09_dev20_multitopic_labels(fixture):
    wanted = {"M01", "M02", "I02", "I03", "I04"}
    ids = {id_of(fixture, key) for key in wanted}
    candidates = [record for record in dev20_candidates(fixture) if record.candidate_id in ids]
    result = o5.select_macro_news(candidates, request(limit=20))
    assert {record.candidate_id for record in result.selected} == ids
    labels = {label["fixture_key"]: label for label in fixture["labels"]}
    by_id = {record.candidate_id: record for record in result.selected}
    for key in wanted:
        record = by_id[id_of(fixture, key)]
        assert list(record.matched_topics) == labels[key]["matched_topics"]
        assert record.primary_topic == labels[key]["primary_topic"] == MP


# --------------------------------------------------------------------------- validation rows


@pytest.mark.unit
def test_t10a_empty_title():
    result = o5.select_macro_news([P("v", title="")], request())
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_TITLE
    assert result.counts()["invalid_count"] == 1


@pytest.mark.unit
def test_t10b_no_title_sentinel():
    result = o5.select_macro_news([P("v", title="No title")], request())
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_TITLE
    assert result.counts()["invalid_count"] == 1


@pytest.mark.unit
def test_t10c_string_timestamp_is_structural():
    record = {"candidate_id": "v", "title": "Fed holds rates", "summary": "",
              "published_at": "2026-09-25T00:00:00Z", "source": None, "url": None}
    result = o5.select_macro_news([record], request())
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_RECORD


@pytest.mark.unit
def test_t10d_naive_datetime_is_invalid_timestamp():
    result = o5.select_macro_news([P("v", at=datetime(2026, 9, 25, 0, 0, 0))], request())
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_TIMESTAMP


@pytest.mark.unit
def test_t10e_missing_candidate_id():
    result = o5.select_macro_news(
        [{"title": "Fed holds rates", "summary": "", "published_at": datetime(2026, 9, 25, tzinfo=UTC),
          "source": None, "url": None}],
        request(),
    )
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_RECORD


@pytest.mark.unit
@pytest.mark.parametrize(
    "case_id,override",
    [
        ("T10f", {"limit": True}),
        ("T10g", {"limit": -1}),
        ("T10g2", {"limit": 2.5}),
        ("T10i", {"start": datetime(2026, 9, 27, tzinfo=UTC), "end": datetime(2026, 9, 20, tzinfo=UTC)}),
        ("T10j", {"rules": "unsupported-o5-version"}),
    ],
)
def test_t10_request_rejections(case_id, override):
    with pytest.raises(o5.InvalidRequestError):
        o5.select_macro_news([P("v")], request(**override))


@pytest.mark.unit
def test_t10k2_absent_and_null_optionals_agree():
    at = datetime(2026, 9, 25, tzinfo=UTC)
    # summary, source and url are entirely absent in this record ...
    absent = {"candidate_id": "v", "title": "Fed holds rates", "published_at": at}
    # ... and all three are explicitly null in this one.
    nulls = {"candidate_id": "v", "title": "Fed holds rates", "published_at": at,
             "summary": None, "source": None, "url": None}
    absent_snapshot = copy.deepcopy(absent)
    nulls_snapshot = copy.deepcopy(nulls)
    first = o5.select_macro_news([absent], request())
    second = o5.select_macro_news([nulls], request())
    assert selected_ids(first) == selected_ids(second) == ["v"]
    assert counts_of(first) == counts_of(second)
    assert decision_map(first)[0].matched_topics == decision_map(second)[0].matched_topics
    # Defaults are applied; neither input object is mutated.
    assert absent == absent_snapshot
    assert nulls == nulls_snapshot


@pytest.mark.unit
def test_t10l_non_mapping_candidate():
    result = o5.select_macro_news([123], request())
    assert counts_of(result) == (1, 0, 0, 0, 1, 0, 0, 0)
    assert decision_map(result)[0].reason_code == o5.REASON_INVALID_RECORD


# --------------------------------------------------------------------------- window boundaries


@pytest.mark.unit
@pytest.mark.parametrize(
    "case_id,raw,expected_disposition",
    [
        ("T11a", "2026-09-20T00:00:00Z", o5.SELECTED),
        ("T11b", "2026-09-27T23:59:59.999999Z", o5.SELECTED),
        ("T11c", "2026-09-28T00:00:00Z", o5.OUT_OF_WINDOW),
        ("T11d", "2026-09-27T23:00:00-08:00", o5.OUT_OF_WINDOW),
        ("T11e", "2026-09-26T23:00:00+05:00", o5.SELECTED),
    ],
)
def test_t11_window_containment(case_id, raw, expected_disposition):
    moment = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    result = o5.select_macro_news([P(case_id, at=moment)], request(limit=1))
    assert decision_map(result)[0].disposition == expected_disposition
    assert assert_counts_conserved(result)


def assert_counts_conserved(result) -> bool:
    counts = result.counts()
    return counts["input_count"] == sum(c for key, c in counts.items() if key != "input_count")


@pytest.mark.unit
def test_t12_one_decision_per_position():
    pool = [
        P("keep"),
        P("bad", title=""),
        P("old", at=datetime(2026, 9, 10, tzinfo=UTC)),
        P("keep"),
        P("irrelevant", title="Local bookstore opens"),
    ]
    result = o5.select_macro_news(pool, request(limit=10))
    dispositions = [decision.disposition for decision in result.decisions]
    assert dispositions == [o5.SELECTED, o5.INVALID, o5.OUT_OF_WINDOW, o5.DUPLICATE_ID, o5.REJECTED]
    assert counts_of(result) == (5, 1, 0, 1, 1, 1, 1, 0)
    assert_common_contract(result, pool)


# --------------------------------------------------------------------------- determinism


@pytest.mark.unit
def test_t14a_hundred_identical_runs(fixture):
    candidates = dev20_candidates(fixture)
    baseline = o5.select_macro_news(candidates, request(limit=6))
    for _ in range(99):
        repeat = o5.select_macro_news(candidates, request(limit=6))
        # Complete result equality: selected records, decisions, status, metadata.
        assert repeat.selected == baseline.selected
        assert repeat.decisions == baseline.decisions
        assert repeat.status == baseline.status
        assert repeat.rules_version == baseline.rules_version
        assert repeat.topic_order == baseline.topic_order
        assert repeat.counts() == baseline.counts()


PERMUTATION = [19, 0, 18, 1, 17, 2, 16, 3, 15, 4, 14, 5, 13, 6, 12, 7, 11, 8, 10, 9]


@pytest.mark.unit
@pytest.mark.parametrize("order", ["original", "reversed", "permutation"])
def test_t14b_permutation_invariance(fixture, order):
    """Original, reversed and fixed permutations select the same IDs by input order."""

    candidates = dev20_candidates(fixture)
    baseline = o5.select_macro_news(candidates, request(limit=6))

    if order == "original":
        indices = list(range(len(candidates)))
    elif order == "reversed":
        indices = list(reversed(range(len(candidates))))
    else:
        indices = list(PERMUTATION)
    inputs = [candidates[index] for index in indices]

    result = o5.select_macro_news(inputs, request(limit=6))
    assert selected_ids(result) == selected_ids(baseline)
    assert counts_of(result) == counts_of(baseline)

    # decisions.input_index follows the actual input order, not the baseline order.
    for position, decision in enumerate(result.decisions):
        assert decision.input_index == position
        assert decision.candidate_id == inputs[position].candidate_id
    by_id = {decision.candidate_id: decision for decision in result.decisions}
    for decision in baseline.decisions:
        mirrored = by_id[decision.candidate_id]
        assert mirrored.disposition == decision.disposition
        assert mirrored.reason_code == decision.reason_code
        assert mirrored.matched_topics == decision.matched_topics


@pytest.mark.unit
def test_t14c_no_wall_clock_read(fixture, monkeypatch):
    called = {"count": 0}

    def trap(*_args, **_kwargs):
        called["count"] += 1
        raise AssertionError("selector read the wall clock")

    # The selector must not reach for "now". Build the request first (so the
    # test's own datetime construction is unaffected), then replace the clock
    # class the selector module sees with one whose now()/utcnow() raise.
    candidates = dev20_candidates(fixture)
    req = request(limit=6)

    class NoClock(o5.datetime):
        @classmethod
        def now(cls, tz=None):
            trap()

        @classmethod
        def utcnow(cls):
            trap()

    monkeypatch.setattr(o5, "datetime", NoClock)
    result = o5.select_macro_news(candidates, req)
    assert called["count"] == 0
    assert selected_ids(result) == fixture["expected"]["k6_order_ids"]


@pytest.mark.unit
def test_t14d_conflicting_duplicates_first_occurrence_wins():
    forward = [
        P("conflict"),
        P("conflict", title="Local bookstore opens", at=datetime(2026, 9, 26, tzinfo=UTC)),
    ]
    result = o5.select_macro_news(forward, request(limit=1))
    assert decision_map(result)[0].disposition == o5.SELECTED
    assert decision_map(result)[1].disposition == o5.DUPLICATE_ID

    reverse = list(reversed(forward))
    reversed_result = o5.select_macro_news(reverse, request(limit=1))
    assert decision_map(reversed_result)[0].disposition == o5.REJECTED
    assert decision_map(reversed_result)[1].disposition == o5.DUPLICATE_ID


# --------------------------------------------------------------------------- topic subset


@pytest.mark.unit
def test_t19_requested_topic_subset_reorders_primary(fixture):
    wanted = {"M01", "I01"}
    ids = {id_of(fixture, key) for key in wanted}
    candidates = [record for record in dev20_candidates(fixture) if record.candidate_id in ids]
    result = o5.select_macro_news(candidates, request(topics=(IN, MP), limit=2))
    by_id = {record.candidate_id: record for record in result.selected}
    m01 = by_id[id_of(fixture, "M01")]
    # Exact tuple in requested order, in both selected and decisions.
    assert m01.primary_topic == IN
    assert m01.matched_topics == (IN, MP)
    assert m01.matched_rule_ids == ("R2-IN", "R1-MP")
    decisions = decision_map(result)
    m01_index = next(d.input_index for d in result.decisions
                     if d.candidate_id == id_of(fixture, "M01"))
    i01_index = next(d.input_index for d in result.decisions
                     if d.candidate_id == id_of(fixture, "I01"))
    # Pinned independently: request (INFLATION, MONETARY_POLICY).
    assert decisions[m01_index].matched_topics == (IN, MP)
    assert decisions[m01_index].matched_rule_ids == ("R2-IN", "R1-MP")
    assert decisions[m01_index].topic == IN
    assert decisions[i01_index].matched_topics == (IN,)
    assert decisions[i01_index].matched_rule_ids == ("R2-IN",)
    assert decisions[i01_index].topic == IN
    assert selected_ids(result) == [id_of(fixture, "M01"), id_of(fixture, "I01")]


@pytest.mark.unit
def test_t19_single_topic_subset_filters_matched_topics(fixture):
    wanted = {"M01", "I01"}
    ids = {id_of(fixture, key) for key in wanted}
    candidates = [record for record in dev20_candidates(fixture) if record.candidate_id in ids]
    result = o5.select_macro_news(candidates, request(topics=(IN,), limit=2))
    for record in result.selected:
        # Only the requested topic survives, and it is the primary.
        assert record.primary_topic == IN
        assert record.matched_topics == (IN,)
        assert record.matched_rule_ids == ("R2-IN",)
    for decision in result.decisions:
        assert decision.matched_topics in ((), (IN,))
        if decision.disposition == o5.SELECTED:
            # Pinned independently: INFLATION-only subset -> ("R2-IN",).
            assert decision.matched_topics == (IN,)
            assert decision.matched_rule_ids == ("R2-IN",)
            assert decision.topic == IN
    assert selected_ids(result) == [id_of(fixture, "M01"), id_of(fixture, "I01")]
