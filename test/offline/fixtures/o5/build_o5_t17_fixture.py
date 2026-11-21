"""Authoring script for the O5 S6 T17 performance fixture and its oracle.

This script is deliberately independent of ``select_macro_news``: it never
imports ``tradingagents.dataflows.macro_news_filter``. It carries its own
copy of the documented rule text (the O5 registry ``RULE_TABLE``) and its own
implementation of the documented allocation algorithm, following the approved
S6 plan (docs/req/reviews/o5/s6-t17, v0.2) sections 2 and 3.

Run it from the repository root::

    python test/offline/fixtures/o5/build_o5_t17_fixture.py

It writes three files next to itself:

* ``O5-T17-Perf-Fixture-1000-v1.json`` -- the fixed 1000-record input.
* ``O5-T17-Expected-Results-v1.json`` -- the frozen oracle.
* ``O5-T17-Manifest-v1.json`` -- dual SHA-256, request, rules version, runner.

The output is byte-stable (sorted keys, ``\\n`` endings, no timestamps of the
run) so the committed files and their hashes are reproducible. Re-running the
script on the same source must reproduce byte-identical files; a hash change
is evidence that the fixture or oracle changed and must be reviewed.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "O5-T17-Perf-Fixture-1000-v1.json"
EXPECTED_PATH = HERE / "O5-T17-Expected-Results-v1.json"
MANIFEST_PATH = HERE / "O5-T17-Manifest-v1.json"

RULES_VERSION = "o5-rules-v1.1-draft"
IMPLEMENTATION_MAIN_SHA = "48d75c38177ea30ab48d33112aaa812a0499ea63"
RUNNER = "ubuntu-latest / CPython 3.11.x"

MP = "MONETARY_POLICY"
IN = "INFLATION"
EA = "ECONOMIC_ACTIVITY"
TOPIC_ORDER = (MP, IN, EA)
LIMIT = 30

# The documented rule catalog, copied by hand from
# tradingagents/dataflows/macro_news_filter.py RULE_TABLE at 48d75c3. Kept as a
# literal so this script cannot inherit an accidental selector change.
RULE_TABLE = (
    (
        "R1-MP",
        MP,
        (
            "federal reserve", "fed", "ecb", "bank of england", "boe",
            "bank of japan", "boj", "central bank", "monetary policy",
        ),
        (
            "rate", "rates", "policy", "basis points", "hike", "hikes", "cut",
            "cuts", "unchanged", "holds", "held", "easing", "tightening",
            "normalization", "quantitative easing", "qe", "minutes",
        ),
    ),
    (
        "R2-IN",
        IN,
        (
            "inflation", "cpi", "consumer price index", "pce", "core pce",
            "disinflation", "deflation", "price pressure", "price pressures",
        ),
        (
            "percent", "%", "year over year", "yoy", "falls", "fall", "rise",
            "rises", "rose", "holds", "held", "cools", "eases", "eased",
            "easing", "target", "sticky", "pressures",
        ),
    ),
    (
        "R3-EA",
        EA,
        (
            "gdp", "payrolls", "nonfarm payrolls", "unemployment", "jobless",
            "pmi", "recession", "retail sales", "industrial production",
            "manufacturing", "consumer spending",
        ),
        (
            "percent", "%", "growth", "grows", "contract", "contraction",
            "expansion", "rose", "fell", "ticks up", "ticked up", "beats",
            "beating", "forecasts", "worries", "signals", "resilient", "slips",
        ),
    ),
)

R2_GAME_CONTEXT = ("game economy", "virtual economy", "expansion pack")


# --------------------------------------------------------------------- matching


def tokens(text: str) -> tuple[str, ...]:
    """NFKC + casefold; split ``%`` into its own token; strip boundary punctuation.

    Mirrors the documented tokenizer contract without importing the selector.
    """

    folded = unicodedata.normalize("NFKC", text).casefold().replace("%", " \x00 ")
    out: list[str] = []
    current: list[str] = []
    for char in folded:
        if char.isspace():
            if current:
                out.append("".join(current).strip(".-"))
                current = []
        elif char == "\x00":
            if current:
                out.append("".join(current).strip(".-"))
                current = []
            out.append("%")
        elif char.isalnum() or char in "+.-":
            current.append(char)
        else:
            if current:
                out.append("".join(current).strip(".-"))
                current = []
    if current:
        out.append("".join(current).strip(".-"))
    return tuple(token for token in out if token)


def phrase(toks: tuple[str, ...], text: str) -> bool:
    parts = text.split()
    if not parts:
        return False
    width = len(parts)
    return any(
        list(toks[start:start + width]) == parts
        for start in range(len(toks) - width + 1)
    )


def excluded(rule_id: str, toks: tuple[str, ...]) -> bool:
    if rule_id != "R2-IN":
        return False
    if any(phrase(toks, item) for item in R2_GAME_CONTEXT):
        return True
    if phrase(toks, "cpi"):
        has_numeric = any(tok == "%" or any(ch.isdigit() for ch in tok) for tok in toks)
        if not has_numeric:
            return True
    return False


def primary_topic(title: str, summary: str) -> str | None:
    """First requested topic that fires, in MP -> IN -> EA order (hand rules)."""

    title_toks = tokens(title)
    summary_toks = tokens(summary or "")
    for rule_id, topic, anchors, context in RULE_TABLE:
        for field_toks in (title_toks, summary_toks):
            fired = any(
                phrase(field_toks, anchor)
                and any(phrase(field_toks, term) for term in context)
                for anchor in anchors
            )
            if fired and not excluded(rule_id, field_toks):
                return topic
    return None


# ------------------------------------------------------------------ id recipe


def canonical_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def timestamp_iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_id(title: str, source: str, url: str, moment: datetime) -> str:
    parts = (canonical_text(title), canonical_text(source), url, timestamp_iso(moment))
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:32]
    return f"o5:{digest}"


# ------------------------------------------------------------- fixture content


WINDOW_START = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
STEP = timedelta(minutes=10)

MP_ANCHORS = ("Federal Reserve", "ECB", "Bank of England", "Bank of Japan", "central bank")
MP_CONTEXT = ("rate", "policy", "hike", "cut", "basis points", "tightening", "easing")
IN_ANCHORS = ("Inflation", "CPI", "PCE", "consumer price index")
IN_CONTEXT = ("percent", "rose", "falls", "sticky", "cools", "target")
EA_ANCHORS = ("Payrolls", "GDP", "unemployment", "PMI", "retail sales", "manufacturing")
EA_CONTEXT = ("growth", "rose", "fell", "beats", "forecasts", "contraction")
IRRELEVANT_TITLES = (
    "Local bakery wins regional award",
    "New park opens downtown this weekend",
    "City council approves library renovation",
    "Volunteers clean up the riverbank",
    "High school team takes state title",
)


def build_records() -> list[dict]:
    records: list[dict] = []
    index = 0

    def add(group: str, title: str, summary: str, source: str) -> dict:
        nonlocal index
        moment = WINDOW_START + STEP * index
        index += 1
        return {
            "fixture_group": group,
            "candidate_id": derive_id(title, source, "", moment),
            "title": title,
            "summary": summary,
            "source": source,
            "url": None,
            "published_at": timestamp_iso(moment),
        }

    for step in range(280):
        anchor = MP_ANCHORS[step % len(MP_ANCHORS)]
        context = MP_CONTEXT[step % len(MP_CONTEXT)]
        records.append(add(
            "F1",
            f"{anchor} signals a cautious {context} at meeting {step}",
            f"Officials discussed the {context} path; no final decision was announced.",
            "FixtureWire MP",
        ))
    for step in range(260):
        anchor = IN_ANCHORS[step % len(IN_ANCHORS)]
        context = IN_CONTEXT[step % len(IN_CONTEXT)]
        records.append(add(
            "F2",
            f"{anchor} report {context} in print number {step}",
            f"The latest reading shows prices {context} on the year.",
            "FixtureWire IN",
        ))
    for step in range(260):
        anchor = EA_ANCHORS[step % len(EA_ANCHORS)]
        context = EA_CONTEXT[step % len(EA_CONTEXT)]
        records.append(add(
            "F3",
            f"{anchor} update shows {context} in survey {step}",
            f"Activity data point to {context} over the quarter.",
            "FixtureWire EA",
        ))
    for step in range(120):
        mp_anchor = MP_ANCHORS[step % len(MP_ANCHORS)]
        mp_context = MP_CONTEXT[step % len(MP_CONTEXT)]
        in_anchor = IN_ANCHORS[step % len(IN_ANCHORS)]
        in_context = IN_CONTEXT[step % len(IN_CONTEXT)]
        records.append(add(
            "F4",
            f"{mp_anchor} weighs {in_anchor} as {mp_context} guidance meets {in_context} print {step}",
            "Policymakers cited the latest prices data while discussing the rate path.",
            "FixtureWire MIX",
        ))
    for step in range(60):
        title = IRRELEVANT_TITLES[step % len(IRRELEVANT_TITLES)]
        records.append(add(
            "F5",
            f"{title} (edition {step})",
            "A community story with no macro-economic content.",
            "FixtureWire LOCAL",
        ))
    return records


def build() -> tuple[list[dict], dict]:
    records = build_records()
    # F6: irrelevant content whose candidate_id copies the first 20 F1 ids.
    f1_ids = [r["candidate_id"] for r in records if r["fixture_group"] == "F1"]

    for step in range(20):
        moment = WINDOW_START + STEP * len(records)
        records.append({
            "fixture_group": "F6",
            "candidate_id": f1_ids[step],
            "title": f"Community notice reposted under a reused id {step}",
            "summary": "No monetary, inflation or activity anchor appears here.",
            "source": "FixtureWire DUP",
            "url": None,
            "published_at": timestamp_iso(moment),
        })

    _assert_id_contract(records)
    expected = derive_expected(records)
    return records, expected


def _assert_id_contract(records: list[dict]) -> None:
    """Every non-F6 row satisfies the recipe; exactly the F6 rows deviate."""

    f1_ids = [
        r["candidate_id"] for r in records if r["fixture_group"] == "F1"
    ][:20]
    for record in records:
        moment = datetime.fromisoformat(record["published_at"].replace("Z", "+00:00"))
        recalculated = derive_id(record["title"], record["source"], "", moment)
        if record["fixture_group"] == "F6":
            assert record["candidate_id"] in f1_ids, record
        else:
            assert record["candidate_id"] == recalculated, record
    assert len(records) == 1000, len(records)
    unique_ids = {r["candidate_id"] for r in records}
    assert len(unique_ids) == 980, len(unique_ids)


def derive_expected(records: list[dict]) -> dict:
    """Allocation by the documented algorithm only; no selector call."""

    start = min(datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) for r in records)
    end = max(datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) for r in records)
    buckets: dict[str, list[tuple]] = {topic: [] for topic in TOPIC_ORDER}
    seen: set[str] = set()
    counts = {
        "input_count": len(records),
        "selected_count": 0,
        "not_selected_limit_count": 0,
        "irrelevant_count": 0,
        "invalid_count": 0,
        "out_of_window_count": 0,
        "duplicate_count": 0,
        "skipped_zero_limit_count": 0,
    }
    relevant: list[tuple] = []
    for record in records:
        cid = record["candidate_id"]
        if cid in seen:
            counts["duplicate_count"] += 1
            continue
        seen.add(cid)
        moment = datetime.fromisoformat(record["published_at"].replace("Z", "+00:00"))
        if not (start <= moment <= end):
            counts["out_of_window_count"] += 1
            continue
        topic = primary_topic(record["title"], record["summary"])
        if topic is None:
            counts["irrelevant_count"] += 1
            continue
        buckets[topic].append((-moment.timestamp(), cid, record))
        relevant.append((topic, cid))

    for topic in TOPIC_ORDER:
        buckets[topic].sort(key=lambda entry: (entry[0], entry[1]))

    selected: list[str] = []
    per_topic = dict.fromkeys(TOPIC_ORDER, 0)
    level = 0
    while len(selected) < LIMIT:
        progressed = False
        for topic in TOPIC_ORDER:
            bucket = buckets[topic]
            if level < len(bucket):
                _, cid, _record = bucket[level]
                selected.append(cid)
                per_topic[topic] += 1
                progressed = True
                if len(selected) >= LIMIT:
                    break
        if not progressed:
            break
        level += 1

    counts["selected_count"] = len(selected)
    counts["not_selected_limit_count"] = len(relevant) - len(selected)
    assert (
        counts["selected_count"]
        + counts["not_selected_limit_count"]
        + counts["irrelevant_count"]
        + counts["invalid_count"]
        + counts["out_of_window_count"]
        + counts["duplicate_count"]
        + counts["skipped_zero_limit_count"]
        == counts["input_count"]
    ), counts

    return {
        "status": "OK",
        "rules_version": RULES_VERSION,
        "topic_order": list(TOPIC_ORDER),
        "request": {
            "topics": list(TOPIC_ORDER),
            "start_at": timestamp_iso(start),
            "end_at": timestamp_iso(end),
            "limit": LIMIT,
        },
        "counts": counts,
        "selected_ids": selected,
        "selected_per_topic": per_topic,
    }


# ---------------------------------------------------------------------- output


def dump(path: Path, payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(data, encoding="utf-8", newline="\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    records, expected = build()
    fixture_payload = {
        "fixture": "O5-T17-Perf-Fixture-1000-v1",
        "rules_version": RULES_VERSION,
        "record_count": len(records),
        "unique_ids": len({r["candidate_id"] for r in records}),
        "group_counts": {
            group: sum(1 for r in records if r["fixture_group"] == group)
            for group in ("F1", "F2", "F3", "F4", "F5", "F6")
        },
        "id_recipe": "o5:sha256(canon(title)+\\x1f+canon(source)+\\x1f+'')[:32]; F6 reuses F1 ids",
        "candidates": records,
    }
    fixture_sha = dump(FIXTURE_PATH, fixture_payload)
    expected_sha = dump(EXPECTED_PATH, expected)
    manifest = {
        "rules_version": RULES_VERSION,
        "record_count": len(records),
        "k": LIMIT,
        "request_topics": list(TOPIC_ORDER),
        "request_window": [expected["request"]["start_at"], expected["request"]["end_at"]],
        "fixture_sha256": fixture_sha,
        "expected_sha256": expected_sha,
        "implementation_main_sha": IMPLEMENTATION_MAIN_SHA,
        "runner": RUNNER,
        "builder": "test/offline/fixtures/o5/build_o5_t17_fixture.py",
        "adjudication_log": [],
    }
    dump(MANIFEST_PATH, manifest)
    print("fixture_sha256  =", fixture_sha)
    print("expected_sha256 =", expected_sha)
    print("counts          =", json.dumps(expected["counts"], sort_keys=True))
    print("selected        =", len(expected["selected_ids"]), expected["selected_per_topic"])


if __name__ == "__main__":
    main()
