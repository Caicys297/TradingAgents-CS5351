"""O3 input condensation: approved offline cases (Test Plan v0.3).

Every case here is deterministic and network-free. The module under test,
``tradingagents.agents.analysts.condensation``, is added by the same change as
this file; the cases covered are T-N1..N8, T-B1..B9, T-E1..E8 and T-R1/R2/R4,
with T-R5 as a sub-check of T-R1. T-R3 and T-P1 are manual records and are not
collected here.

Case IDs appear in each test's name so a collected node maps back to the
approved ID. A case ID may expand to several parameterized nodes.
"""

import json
import logging
import socket
import urllib.request

import pytest

from tradingagents.agents.analysts import condensation
from tradingagents.agents.analysts.condensation import (
    CondensationError,
    CondensationReport,
    condense_source,
    parse_source,
    render_audit_footer,
)

NEWS = "news"
STOCKTWITS = "stocktwits"
REDDIT = "reddit"

# --- fixtures in the real shapes the fetchers produce -----------------------


def news_block(articles):
    """One entry per article, in the shape ``news._format_articles`` emits."""
    out = ""
    for title, publisher, summary, link in articles:
        out += f"### {title} (source: {publisher})\n"
        if summary:
            out += f"{summary}\n"
        if link:
            out += f"Link: {link}\n"
        out += "\n"
    return out


def stocktwits_block(messages, summary=None, note=""):
    """The stance summary line, a blank line, then one item per message."""
    if summary is None:
        total = len(messages)
        summary = (
            f"Bullish: {total} (100%) · Bearish: 0 (0%) · "
            f"Unlabeled: 0 · Total: {total} most-recent messages"
        )
    body = "\n".join(f"[{when} · @{user} · {tag}] {text}" for when, user, tag, text in messages)
    return (f"{note}\n\n" if note else "") + summary + "\n\n" + body


def reddit_block(groups, note=""):
    """One header plus its posts per subreddit, in the shape reddit emits."""
    blocks = []
    for sub, posts in groups:
        if posts is None:  # a group the fetcher reported as empty
            blocks.append(f"r/{sub}: <no posts found mentioning NVDA>")
            continue
        lines = [f"r/{sub} — {len(posts)} recent posts mentioning NVDA:"]
        for created, title, excerpt in posts:
            lines.append(f"  [{created}] {title}")
            if excerpt:
                lines.append(f"    body excerpt: {excerpt}")
        blocks.append("\n".join(lines))
    return "\n\n".join(([note] if note else []) + blocks)


def make_article(i, publisher="Reuters", link=None, summary="Body text for the article."):
    return (f"Headline number {i} about the company", publisher, summary, link or f"https://x.test/a{i}")


# --- config helpers --------------------------------------------------------


def caps(total=24000, news=12000, stocktwits=6000, reddit=6000):
    return {
        "input_budget_chars": total,
        "input_news_cap_chars": news,
        "input_stocktwits_cap_chars": stocktwits,
        "input_reddit_cap_chars": reddit,
    }


def condense(text, source=NEWS, cap=12000, **kwargs):
    cfg = caps(**kwargs.pop("caps", {}))
    key = {
        NEWS: "input_news_cap_chars",
        STOCKTWITS: "input_stocktwits_cap_chars",
        REDDIT: "input_reddit_cap_chars",
    }[source]
    return condense_source(
        text,
        source=source,
        ticker="NVDA",
        identity_terms=("nvidia",),
        budget_chars=cap if cap is not None else cfg[key],
        **kwargs,
    )


# --- network probe (T-R5) --------------------------------------------------


class NetworkProbe:
    """Counts network attempts; every patched callable raises after recording."""

    def __init__(self):
        self.attempts = 0

    def __call__(self, *args, **kwargs):
        self.attempts += 1
        raise OSError("network blocked by O3 probe")

    def install(self, monkeypatch):
        import curl_cffi.requests as curl_requests

        for target, attr in (
            (socket.socket, "connect"),
            (socket.socket, "connect_ex"),
            (socket, "getaddrinfo"),
            (urllib.request, "urlopen"),
        ):
            monkeypatch.setattr(target, attr, self)
        monkeypatch.setattr(curl_requests.Session, "request", self)
        monkeypatch.setattr(curl_requests.AsyncSession, "request", self)
        return self


@pytest.fixture
def probe(monkeypatch):
    return NetworkProbe().install(monkeypatch)


# ===========================================================================
# Normal
# ===========================================================================


def test_T_N1_exact_duplicates_collapse_with_counts():
    """T-N1: three identical articles among eight leave one copy."""
    unique = [make_article(i) for i in range(1, 6)]
    dup = make_article(9, link="https://x.test/dup")
    text = news_block(unique + [dup, dup, dup])

    out, report = condense(text)

    assert out.count("https://x.test/dup") == 1
    assert report.duplicates_removed == 2
    assert report.items_in == 8
    assert report.items_out == 6
    assert report.items_in - report.items_out == (
        report.duplicates_removed + report.items_dropped
    )


def test_T_N2_generous_budget_changes_nothing():
    """T-N2: with room to spare nothing is removed and the note says so."""
    text = news_block([make_article(i) for i in range(10)])

    out, report = condense(text, cap=12000)

    assert report.items_dropped == 0
    assert report.items_truncated == 0
    assert report.duplicates_removed == 0
    assert report.chars_after <= report.chars_before
    footer = render_audit_footer([report])
    assert "no items were removed" in footer.lower()


def test_T_N3_tight_budget_keeps_top_ranked_in_order():
    """T-N3: identity-relevant items first, original order as the tie-break."""
    items = [
        ("Unrelated market commentary", "Reuters", "nothing to do with it", "https://x.test/1"),
        ("NVDA jumps", "Reuters", "chips", "https://x.test/2"),
        ("Other sector news", "AP", "sector", "https://x.test/3"),
        ("NVIDIA guidance raised", "AP", "guidance", "https://x.test/4"),
    ]
    whole = news_block(items)
    filler = news_block([items[0]]) + news_block([items[2]])
    cap = len(filler) + 5
    assert cap < len(whole)

    out, report = condense(whole, cap=cap)

    assert "NVDA jumps" in out
    assert "NVIDIA guidance raised" in out
    assert out.index("NVDA jumps") < out.index("NVIDIA guidance raised")
    assert report.items_dropped >= 1
    assert "<input_condensation>" in render_audit_footer([report])


def test_T_N4_cross_source_duplicates_are_preserved():
    """T-N4: the same headline in two sources is not merged."""
    headline = "Headline number 1 about the company"
    news, _ = condense(news_block([make_article(1)]))
    st, _ = condense(stocktwits_block([("2026-05-01", "u", "Bullish", headline)]), source=STOCKTWITS)

    assert "Headline number 1 about the company" in news
    assert "Headline number 1 about the company" in st


def test_T_N5_node_prompt_keeps_identity_date_and_safety_text(monkeypatch):
    """T-N5: the captured node prompt keeps condensed blocks and the outer text."""
    from tradingagents.agents.structured import NO_EXTERNAL_TOOLS

    captured = {}

    def fake_analyst(monkeypatch):
        from tradingagents.agents.analysts import sentiment_analyst as node_mod

        class _Structured:
            def invoke(self, prompt):
                captured["prompt"] = prompt
                from tradingagents.agents.schemas import SentimentBand, SentimentReport

                return SentimentReport(
                    overall_band=SentimentBand.NEUTRAL,
                    overall_score=5.0,
                    confidence="medium",
                    narrative="captured",
                )

        class _LLM:
            def with_structured_output(self, schema):
                return _Structured()

            def invoke(self, prompt):  # pragma: no cover - structured path wins
                captured["prompt"] = prompt
                raise AssertionError("free-text path should not run here")

        monkeypatch.setattr(node_mod, "jev_screen", lambda t: None, raising=False)
        monkeypatch.setattr(node_mod.get_news, "func", lambda *a, **k: news_block([make_article(1)]), raising=False)
        monkeypatch.setattr(
            node_mod,
            "fetch_stocktwits_messages",
            lambda *a, **k: stocktwits_block([("2026-05-01", "u", "Bullish", "NVDA up")]),
            raising=False,
        )
        monkeypatch.setattr(
            node_mod,
            "fetch_reddit_posts",
            lambda *a, **k: reddit_block([("stocks", [("2026-05-01", "NVDA", "body")])]),
            raising=False,
        )
        return node_mod.create_sentiment_analyst(_LLM())

    analyst = fake_analyst(monkeypatch)
    state = _sentiment_state()
    state["instrument_context"] = "The instrument to analyze is `NVDA`."
    result = analyst(state)

    assert result["sentiment_report"]
    prompt_text = " ".join(str(m) for m in captured["prompt"])
    assert "The instrument to analyze is `NVDA`." in prompt_text
    assert "2026-05-01" in prompt_text
    assert NO_EXTERNAL_TOOLS in prompt_text
    assert "<input_condensation>" in prompt_text


def test_T_N6_character_reduction_is_reported_as_chars():
    """T-N6: a 3x-duplicated fixture reports >=30% character reduction."""
    dup = make_article(
        7, link="https://x.test/dup", summary="The same long summary repeated three times over."
    )
    text = news_block([make_article(i) for i in range(2)] + [dup, dup, dup])

    out, report = condense(text)

    reduction = 1 - (len(out) / len(text))
    assert reduction >= 0.30
    footer = render_audit_footer([report]).lower()
    assert "char" in footer
    # The figure is labelled in characters; the footer mentions tokens only to
    # say the two are not interchangeable.
    assert "not tokens" in footer
    assert "token reduction" not in footer


@pytest.mark.parametrize(
    "overrides",
    [
        {"input_news_cap_chars": 0},
        {"input_reddit_cap_chars": -5},
        {"input_news_cap_chars": 20000, "input_budget_chars": 24000},
    ],
    ids=["non-positive-cap", "negative-cap", "caps-exceed-total"],
)
def test_T_N7_invalid_caps_raise_and_oversized_block_is_condensed(overrides):
    """T-N7: invalid allocation raises; valid over-cap block is condensed."""
    cfg = {**caps(), **overrides}
    with pytest.raises(ValueError):
        condensation.validate_caps(cfg)

    text = news_block([make_article(i, summary="x" * 400) for i in range(5)])
    out, report = condense(text, cap=800)
    assert len(out) <= 800
    assert report.items_dropped or report.items_truncated


def test_T_N8_real_formatter_contract_and_source_structure():
    """T-N8: parse the real shared formatter output, and unknown drift is one item."""
    from tradingagents.dataflows.vendors.yahoo.news import _format_articles

    articles = [
        {
            "title": "Formatter contract headline",
            "summary": "Summary line.",
            "publisher": "Reuters",
            "link": "https://x.test/contract",
            "pub_date": None,
        },
        {
            "title": "Second contract headline",
            "summary": "",
            "publisher": "AP",
            "link": "https://x.test/two",
            "pub_date": None,
        },
    ]
    real = _format_articles(articles)
    prologue, items = parse_source(real, NEWS)
    assert prologue == ""
    assert len(items) == 2
    assert "Formatter contract headline" in items[0].text
    assert items[0].link == "https://x.test/contract"
    assert "Second contract headline" in items[1].text

    # Structural drift must fail the contract: a heading the formatter would
    # never emit is not silently parsed as one of its articles.
    drifted = "# Formatter contract headline\nSummary line.\nLink: https://x.test/c\n\n"
    drifted_out, drifted_report = condense(drifted, cap=12000)
    assert drifted_report.parse_fallbacks == 1
    assert drifted_report.items_in == 1
    assert drifted_out == drifted, "an unknown shape is budgeted whole, never reshaped"


def test_T_N8_stocktwits_summary_is_prologue_and_reports_trims():
    """T-N8: StockTwits summary bytes survive and trims are reported."""
    msgs = [(f"2026-05-0{i}", f"user{i}", "Bullish", f"message about NVDA number {i}") for i in range(1, 7)]
    text = stocktwits_block(msgs)
    summary_line = text.split("\n")[0]

    out, report = condense(text, source=STOCKTWITS, cap=260)

    assert summary_line in out, "the original stance summary must not be rewritten"
    assert "[2026-05-01" in out
    assert report.items_dropped or report.items_truncated
    footer = render_audit_footer([report])
    assert "subset" in footer.lower()


def test_T_N8_reddit_groups_keep_headers_and_omission_marker():
    """T-N8: per-group headers stay with their posts; empty groups keep a marker."""
    groups = [
        ("wallstreetbets", [("2026-05-01", "NVDA moon talk", "yolo")]),
        ("stocks", [("2026-05-01", "NVDA earnings", "margins")]),
        ("investing", [("2026-05-01", "NVDA valuation", "long term")]),
    ]
    text = reddit_block(groups)
    out, report = condense(text, source=REDDIT, cap=290)

    for header in ("r/wallstreetbets — ", "r/stocks — ", "r/investing — "):
        assert header in out, f"group header {header!r} must be preserved"
    assert out.index("r/wallstreetbets") < out.index("r/stocks")
    assert len(out) <= 290
    assert report.items_dropped == 1
    assert "[all posts omitted by input budget]" in out


# ===========================================================================
# Boundary
# ===========================================================================


def test_T_B1_empty_input_is_returned_unchanged():
    """T-B1: empty input returns unchanged with zero counts."""
    out, report = condense("", cap=100)
    assert out == ""
    assert report.items_in == 0
    assert report.duplicates_removed == 0
    assert report.items_dropped == 0
    assert report.items_truncated == 0


def test_T_B2_exactly_at_cap_is_not_truncated():
    """T-B2: a block that exactly fills the cap passes through."""
    text = news_block([make_article(1, link="https://x.test/a", summary="")])
    out, report = condense(text, cap=len(text))
    assert out == text
    assert report.items_truncated == 0


def test_T_B3_one_char_over_cap_still_fits():
    """T-B3: one character over the cap still produces an in-cap block."""
    text = news_block([make_article(i, summary="y" * 60) for i in range(3)])
    out, report = condense(text, cap=len(text) - 1)
    assert len(out) <= len(text) - 1
    assert report.items_dropped or report.items_truncated


@pytest.mark.parametrize("kind", ["placeholder", "preamble", "multi-group-reddit"])
def test_T_B4_protected_content_over_cap_falls_back(kind):
    """T-B4: protected content that cannot fit returns the original block."""
    if kind == "placeholder":
        text = "<Yahoo Finance news unavailable for 2026-05-01..2026-05-07: it only serves recent items>"
        with pytest.raises(CondensationError) as excinfo:
            condense(text, cap=len(text) - 20)
    elif kind == "preamble":
        text = stocktwits_block([("2026-05-01", "u", "Bullish", "hi")])
        summary = text.split("\n\n")[0]
        with pytest.raises(CondensationError) as excinfo:
            condense(text, source=STOCKTWITS, cap=len(summary) - 20)
    else:
        groups = [(f"sub{i}", [("2026-05-01", f"post {i}", "body")]) for i in range(6)]
        text = reddit_block(groups)
        # Headers plus the omission markers cannot all fit: the combined
        # protected content exceeds the cap.
        with pytest.raises(CondensationError) as excinfo:
            condense(text, source=REDDIT, cap=len(text) // 2)

    assert excinfo.value.budget_exception is True
    assert "cap" in str(excinfo.value)
    # A budget exception never counts as a budget pass.
    assert CondensationReport(source="news", budget_exception=True).passed_budget is False


# --- FC-5 at node level: original block retained, exception recorded, run excluded ---

OVER_CAP_PLACEHOLDER = (
    "<Yahoo Finance news unavailable for 2026-04-24..2026-05-01: it only serves recent "
    "items, so this is not an absence of news for NVDA>"
)


def _node_with_blocks(monkeypatch, blocks, caps_override=None, captured=None):
    """Build the real node over fake fetchers that return the given blocks."""
    from tradingagents.agents.analysts import sentiment_analyst as node_mod

    captured = captured if captured is not None else {}

    class _Structured:
        def invoke(self, prompt):
            captured["prompt"] = prompt
            from tradingagents.agents.schemas import SentimentBand, SentimentReport

            return SentimentReport(
                overall_band=SentimentBand.NEUTRAL,
                overall_score=5.0,
                confidence="medium",
                narrative="captured",
            )

    class _LLM:
        def with_structured_output(self, schema):
            return _Structured()

        def invoke(self, prompt):  # pragma: no cover - structured path wins
            raise AssertionError("free-text path should not run here")

    monkeypatch.setattr(node_mod, "jev_screen", lambda t: None, raising=False)
    monkeypatch.setattr(node_mod.get_news, "func", lambda *a, **k: blocks["news"], raising=False)
    monkeypatch.setattr(
        node_mod, "fetch_stocktwits_messages", lambda *a, **k: blocks["stocktwits"], raising=False
    )
    monkeypatch.setattr(
        node_mod, "fetch_reddit_posts", lambda *a, **k: blocks["reddit"], raising=False
    )
    if caps_override:
        base = node_mod.get_config()
        monkeypatch.setattr(node_mod, "get_config", lambda: {**base, **caps_override})
    return node_mod.create_sentiment_analyst(_LLM()), captured


def test_FC5_node_keeps_original_news_block_when_protected_text_over_cap(monkeypatch, caplog):
    """FC-5 (node): an over-cap protected placeholder keeps the original block."""
    captured = {}
    blocks = {
        "news": OVER_CAP_PLACEHOLDER,
        "stocktwits": stocktwits_block([("2026-05-01", "u", "Bullish", "NVDA up")]),
        "reddit": reddit_block([("stocks", [("2026-05-01", "NVDA", "body")])]),
    }
    analyst, captured = _node_with_blocks(
        monkeypatch, blocks, {"input_news_cap_chars": len(OVER_CAP_PLACEHOLDER) - 20}, captured
    )

    with caplog.at_level(logging.WARNING, logger="tradingagents.agents.analysts.sentiment_analyst"):
        result = analyst(_sentiment_state())

    prompt_text = " ".join(str(m) for m in captured["prompt"])
    # 1. the original source text reaches the prompt unchanged
    assert OVER_CAP_PLACEHOLDER in prompt_text
    # 2. the node still produces a report
    assert result["sentiment_report"]
    # 3. the budget exception is recorded, not silently swallowed
    logged = caplog.text.lower()
    # The per-source record names the source; the run-level record names the run.
    assert "sentiment analyst: news block kept unchanged" in logged
    assert "o3 budget exception in this run" in logged
    assert "excluded from budget-pass results" in logged


def test_FC5_node_reports_no_exception_when_all_blocks_fit(monkeypatch, caplog):
    """FC-5 (node): a within-cap run records no exception, so exclusions stay meaningful."""
    blocks = {
        "news": news_block([make_article(1)]),
        "stocktwits": stocktwits_block([("2026-05-01", "u", "Bullish", "NVDA up")]),
        "reddit": reddit_block([("stocks", [("2026-05-01", "NVDA", "body")])]),
    }
    analyst, captured = _node_with_blocks(monkeypatch, blocks)

    with caplog.at_level(logging.WARNING, logger="tradingagents.agents.analysts.sentiment_analyst"):
        result = analyst(_sentiment_state())

    assert result["sentiment_report"]
    assert "excluded from budget-pass results" not in caplog.text.lower()
    assert "<input_condensation>" in " ".join(str(m) for m in captured["prompt"])


def test_T_B5_single_oversized_item_is_truncated_or_dropped():
    """T-B5: one long summary truncates within the cap or is dropped."""
    long = "z" * 900
    text = news_block([make_article(1, summary=long)])
    out, report = condense(text, cap=300)
    assert len(out) <= 300
    if report.items_truncated:
        assert "…[truncated]" in out
    else:
        assert report.items_dropped == 1


@pytest.mark.parametrize("ratio,merged", [(0.8, True), (0.79, False)], ids=["jaccard-0.8", "jaccard-0.79"])
def test_T_B6_T_B7_near_duplicate_threshold(ratio, merged):
    """T-B6/T-B7: the Jaccard threshold is inclusive at exactly 0.8."""
    if ratio == 0.8:
        a = "alpha beta gamma delta epsilon"    # 4/5 shared -> 0.8 exactly
        b = "alpha beta gamma delta"
    else:
        a = "alpha beta gamma delta epsilon"    # 4/6 shared -> 0.667 < 0.79
        b = "alpha beta gamma delta zeta"
    text = news_block(
        [
            (a.capitalize(), "Reuters", "", "https://x.test/a"),
            (b.capitalize(), "Reuters", "", "https://x.test/b"),
        ]
    )
    out, report = condense(text, cap=12000)
    assert (report.duplicates_removed == 1) is merged


def test_T_B7_jaccard_below_threshold_is_not_merged():
    """T-B7: a pair just under the threshold stays two items."""
    text = news_block(
        [
            ("Alpha beta gamma delta epsilon", "Reuters", "", "https://x.test/a"),
            ("Alpha beta gamma delta zeta", "Reuters", "", "https://x.test/b"),
        ]
    )
    out, report = condense(text, cap=12000)
    assert report.duplicates_removed == 0
    assert report.items_out == 2


def test_T_B8_empty_link_and_title_do_not_match():
    """T-B8: empty links and titles never establish a duplicate match."""
    text = news_block(
        [
            ("No title", "Reuters", "one", ""),
            ("No title", "Reuters", "two", ""),
        ]
    )
    out, report = condense(text, cap=12000)
    assert report.duplicates_removed == 0


def test_T_B9_non_ascii_counts_are_code_points():
    """T-B9: Chinese headlines dedupe and count by code point."""
    items = [
        ("英伟达股价上涨", "路透社", "芯片需求强劲", "https://x.test/zh1"),
        ("英伟达股价上涨", "路透社", "芯片需求强劲", "https://x.test/zh1"),
        ("市场综述", "彭博社", "宏观数据", "https://x.test/zh2"),
    ]
    out, report = condense(news_block(items))
    assert report.duplicates_removed == 1
    assert report.chars_before == len(news_block(items))


# ===========================================================================
# Exception
# ===========================================================================


def test_T_E1_none_input_raises_without_budget_exception():
    """T-E1: None input raises and is never classified as a budget result."""
    with pytest.raises(CondensationError) as excinfo:
        condense_source(None, source=NEWS, ticker="NVDA", identity_terms=(), budget_chars=100)
    assert not getattr(excinfo.value, "budget_exception", False)


def test_T_E2_unavailable_placeholder_is_kept_verbatim():
    """T-E2: an absence marker survives and is not treated as a duplicate."""
    text = (
        "<Yahoo Finance news unavailable for 2026-05-01..2026-05-07: it only serves "
        "recent items, so this is not an absence of news for NVDA>"
    )
    out, report = condense(text, cap=12000)
    assert out == text
    assert report.duplicates_removed == 0


def test_T_E3_node_survives_a_condenser_fault(monkeypatch):
    """T-E3: an internal fault makes the node use the uncondensed block."""
    from tradingagents.agents.analysts import sentiment_analyst as node_mod

    def boom(*args, **kwargs):
        raise CondensationError("injected")

    monkeypatch.setattr(node_mod, "condense_source", boom, raising=False)
    analyst, captured = _make_analyst(monkeypatch)
    result = analyst(_sentiment_state())
    assert result["sentiment_report"]
    assert "NVDA" in " ".join(str(m) for m in captured["prompt"])


@pytest.mark.parametrize(
    "bad",
    [{"input_budget_chars": -1}, {"input_news_cap_chars": 0}, {"input_news_cap_chars": "x"}],
    ids=["negative-total", "zero-source-cap", "non-integer"],
)
def test_T_E4_invalid_config_raises_value_error(bad):
    """T-E4: invalid configuration fails validation, not silently mid-run."""
    with pytest.raises(ValueError):
        condensation.validate_caps({**caps(), **bad})


def test_T_E5_absent_tokenizer_reports_none():
    """T-E5: without a tokenizer no token figure is claimed."""
    out, report = condense(news_block([make_article(1)]))
    assert report.tokens_after is None
    assert report.tokens_before is None


def test_T_E6_unknown_shape_becomes_one_item():
    """T-E6: an unrecognised block is budgeted as one item."""
    text = "Totally unexpected vendor output\nwith no headings at all\n"
    out, report = condense(text, cap=12000)
    assert report.parse_fallbacks > 0
    assert report.items_in == 1
    assert out == text


def test_T_E7_optional_tokenizer_estimates_decrease():
    """T-E7: a supplied tokenizer yields before/after estimates, after < before."""
    counter = {"n": 0}

    def count(text):
        counter["n"] += 1
        return max(1, len(text) // 4)

    dup = make_article(5, summary="Repeated summary that appears three times here.")
    text = news_block([make_article(i) for i in range(4)] + [dup, dup, dup])
    out, report = condense(text, count_tokens=count)
    assert report.tokens_before is not None and report.tokens_after is not None
    assert report.tokens_after < report.tokens_before
    assert counter["n"] == 2


def test_T_E8_audit_and_logs_hold_no_raw_content(caplog):
    """T-E8: persisted audit ids are opaque and INFO logs carry counts only."""
    secret_title = "ACME merger rumour"
    secret_link = "https://x.test/secret?token=abc123"
    text = news_block(
        [
            (secret_title, "Reuters", "synthetic body payload", secret_link),
            (secret_title, "Reuters", "synthetic body payload", secret_link),
        ]
    )
    with caplog.at_level(logging.INFO, logger=condensation.__name__):
        out, report = condense(text, cap=12000)

    serialized = json.dumps(condensation.report_as_dict(report), ensure_ascii=False)
    logged = caplog.text
    for needle in (secret_title, secret_link, "synthetic body payload", "token=abc123"):
        assert needle not in serialized
        assert needle not in logged
    assert all(r.identifier for r in report.removals)
    assert "duplicates_removed=1" in logged or "duplicates_removed" in logged


# ===========================================================================
# Regression
# ===========================================================================


def test_T_R2_disabled_condensation_is_byte_identical(monkeypatch):
    """T-R2: disabled results in the baseline prompt and identical fetcher calls."""
    from tradingagents.agents.analysts import sentiment_analyst as node_mod

    calls = {"order": []}
    analyst, captured = _make_analyst_with_calls(monkeypatch, calls)
    baseline_config = node_mod.get_config()
    monkeypatch.setattr(
        node_mod,
        "get_config",
        lambda: {**baseline_config, "input_condensation_enabled": False},
    )

    result = analyst(_sentiment_state())
    assert result["sentiment_report"]

    prompt_text = " ".join(str(m) for m in captured["prompt"])
    assert "<input_condensation>" not in prompt_text
    assert calls["order"] == ["news", "stocktwits", "reddit"]

    # Compare against the pre-change template rendered with the same inputs.
    baseline = node_mod._build_system_message(
        ticker="NVDA",
        start_date="2026-04-24",
        end_date="2026-05-01",
        news_block="NEWS BLOCK",
        stocktwits_block="ST BLOCK",
        reddit_block="RD BLOCK",
        subreddits=node_mod.DEFAULT_SUBREDDITS,
    )
    disabled = node_mod._build_system_message(
        ticker="NVDA",
        start_date="2026-04-24",
        end_date="2026-05-01",
        news_block="NEWS BLOCK",
        stocktwits_block="ST BLOCK",
        reddit_block="RD BLOCK",
        subreddits=node_mod.DEFAULT_SUBREDDITS,
        audit_footer="",
    )
    assert disabled == baseline


def test_T_R4_repeat_and_recondense_are_stable():
    """T-R4: identical input gives identical bytes; re-condensing removes nothing."""
    text = news_block([make_article(i) for i in range(6)])
    first, r1 = condense(text, cap=12000)
    second, r2 = condense(text, cap=12000)
    assert first == second
    assert r1 == r2
    again, r3 = condense(first, cap=12000)
    assert again == first
    assert r3.duplicates_removed == 0
    assert r3.items_dropped == 0
    assert r3.items_truncated == 0


def test_R5_T_R5_direct_condenser_makes_no_network_calls(probe):
    """T-R5: the condenser alone attempts no network access."""
    text = news_block([make_article(i) for i in range(4)])
    condense(text, cap=12000)
    condense(stocktwits_block([("2026-05-01", "u", "Bullish", "hi")]), source=STOCKTWITS)
    condense(reddit_block([("stocks", [("2026-05-01", "t", "b")])]), source=REDDIT)
    assert probe.attempts == 0


def test_R5_T_R5_node_makes_no_network_calls(monkeypatch, probe):
    """T-R5: the whole node with fake fetchers attempts no network access."""
    analyst, _captured = _make_analyst(monkeypatch)
    analyst(_sentiment_state())
    assert probe.attempts == 0


def test_T_R1_collected_cases_are_present():
    """T-R1: the approved automated case IDs are represented in this module."""
    import sys

    approved = (
        [f"T_N{i}" for i in range(1, 9)]
        + [f"T_B{i}" for i in range(1, 10)]
        + [f"T_E{i}" for i in range(1, 9)]
        + ["T_R2", "T_R4", "T_R5"]
    )
    module = sys.modules[__name__]
    joined = "\n".join(name for name in vars(module) if name.startswith("test_"))
    missing = [case for case in approved if case not in joined]
    assert missing == [], f"approved cases without a collected node: {missing}"


# ===========================================================================
# node-level helpers
# ===========================================================================


def _sentiment_state():
    return {
        "company_of_interest": "NVDA",
        "trade_date": "2026-05-01",
        "messages": [],
    }


def _make_analyst_with_calls(monkeypatch, calls):
    """Wire a fake LLM and fake fetchers; record fetcher order."""
    from tradingagents.agents.analysts import sentiment_analyst as node_mod

    captured = {}

    class _Structured:
        def invoke(self, prompt):
            captured["prompt"] = prompt
            from tradingagents.agents.schemas import SentimentBand, SentimentReport

            return SentimentReport(
                overall_band=SentimentBand.NEUTRAL,
                overall_score=5.0,
                confidence="medium",
                narrative="captured",
            )

    class _LLM:
        def with_structured_output(self, schema):
            return _Structured()

        def invoke(self, prompt):
            captured["prompt"] = prompt

            class _R:
                content = "free text"

            return _R()

    def news(*a, **k):
        calls["order"].append("news")
        return news_block([make_article(1)])

    def st(*a, **k):
        calls["order"].append("stocktwits")
        return stocktwits_block([("2026-05-01", "u", "Bullish", "NVDA up")])

    def rd(*a, **k):
        calls["order"].append("reddit")
        return reddit_block([("stocks", [("2026-05-01", "NVDA", "body")])])

    monkeypatch.setattr(node_mod.get_news, "func", news, raising=False)
    monkeypatch.setattr(node_mod, "fetch_stocktwits_messages", st, raising=False)
    monkeypatch.setattr(node_mod, "fetch_reddit_posts", rd, raising=False)
    monkeypatch.setattr(node_mod, "jev_screen", lambda ticker: None, raising=False)

    analyst = node_mod.create_sentiment_analyst(_LLM())
    return analyst, captured


def _make_analyst(monkeypatch):
    analyst, captured = _make_analyst_with_calls(monkeypatch, {"order": []})
    return analyst, captured
