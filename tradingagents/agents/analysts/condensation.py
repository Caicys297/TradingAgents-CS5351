"""Input condensation for the Sentiment Analyst (O3).

Fetched vendor text is sometimes repetitive, partly irrelevant and long.  This
module collapses duplicates, keeps the most relevant items first, and fits each
source inside its own character cap, while recording what it changed so a
reader can tell "nothing found" from "we trimmed it".

It never touches the surrounding prompt: the ticker identity, analysis date and
safety text live outside these blocks and are checked at the analyst node.
"""

import hashlib
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

NEWS = "news"
STOCKTWITS = "stocktwits"
REDDIT = "reddit"

TRUNCATION_MARKER = "…[truncated]"
OMITTED_MARKER = "[all posts omitted by input budget]"
FOOTER_MAX_CHARS = 240

_SOURCE_CAP_PREFIX = {
    NEWS: "input_news_cap_chars",
    STOCKTWITS: "input_stocktwits_cap_chars",
    REDDIT: "input_reddit_cap_chars",
}

# A block shape we do not recognise is kept whole as one item, and counted here.
_PLACEHOLDER_RE = re.compile(r"^\s*<[^>]*(unavailable|no StockTwits|no Reddit|none of)[^>]*>", re.S)
_NEWS_HEADING_RE = re.compile(r"^### (?P<title>.+?) \(source: (?P<publisher>.+?)\)$")
_ST_ITEM_RE = re.compile(r"^\[(?P<when>[^\]]*?)(?: · @(?P<user>[^·\]]*))?(?: · (?P<tag>[^\]]*))?\] (?P<body>.*)$")
_REDDIT_HEADER_RE = re.compile(r"^r/(?P<sub>\S+) — (?P<count>\d+) recent posts mentioning .*:$")
_REDDIT_ITEM_RE = re.compile(r"^  \[(?P<date>[^\]]*)\] (?P<title>.*)$")


class CondensationError(Exception):
    """A source block could not be condensed safely."""

    def __init__(self, message, *, budget_exception=False):
        super().__init__(message)
        self.budget_exception = budget_exception


@dataclass(frozen=True)
class RemovalRecord:
    """One item removed or shortened, identified without carrying its content."""

    source: str
    identifier: str
    reason: str


@dataclass(frozen=True)
class Item:
    """A single budgetable entry, plus enough structure to rebuild its block."""

    text: str
    title: str = ""
    publisher: str = ""
    link: str = ""
    rank: int = 0
    group: str = ""
    source_kind: str = ""

    @property
    def identity_key(self):
        """What makes two items the same article; None when nothing does."""
        link = (self.link or "").strip().lower()
        if link:
            return ("link", link)
        return None


@dataclass(frozen=True)
class CondensationReport:
    source: str
    items_in: int = 0
    items_out: int = 0
    duplicates_removed: int = 0
    items_dropped: int = 0
    items_truncated: int = 0
    chars_before: int = 0
    chars_after: int = 0
    tokens_before: int | None = None
    tokens_after: int | None = None
    parse_fallbacks: int = 0
    budget_exception: bool = False
    removals: tuple = field(default_factory=tuple)

    @property
    def passed_budget(self):
        """Whether this source met its cap; a fallback never counts as a pass."""
        return not self.budget_exception


def _norm_title(title):
    return " ".join(re.findall(r"\w+", (title or "").lower()))


def _tokens(text):
    return set(_norm_title(text).split())


def _jaccard(a, b):
    left, right = _tokens(a), _tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def safe_id(text):
    """A stable identifier for an item that does not reveal its content."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:12]


def validate_caps(config):
    """Return the validated caps, raising ``ValueError`` on an unusable allocation."""
    total = config.get("input_budget_chars")
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
        raise ValueError(f"input_budget_chars must be a positive integer, got {total!r}")
    caps = {}
    for source, key in _SOURCE_CAP_PREFIX.items():
        value = config.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{key} must be a positive integer, got {value!r}")
        caps[source] = value
    if sum(caps.values()) > total:
        raise ValueError(
            f"source caps sum to {sum(caps.values())} which exceeds input_budget_chars={total}"
        )
    return caps


# --- parsing ---------------------------------------------------------------


def _is_placeholder(text):
    return bool(_PLACEHOLDER_RE.match(text or ""))


def _parse_news(text):
    """Split formatted Yahoo news into a prologue and one item per heading."""
    lines = text.splitlines()
    prologue = []
    items = []
    current = None
    for line in lines:
        match = _NEWS_HEADING_RE.match(line)
        if match:
            if current is not None:
                items.append(_finish_news(current))
            current = {"title": match.group("title"), "publisher": match.group("publisher"), "body": []}
            continue
        if current is None:
            prologue.append(line)
            continue
        link = re.match(r"^Link: (?P<link>.+)$", line)
        if link:
            current["link"] = link.group("link").strip()
            continue
        current["body"].append(line)
    if current is not None:
        items.append(_finish_news(current))
    return "\n".join(prologue), items


def _finish_news(current):
    body = list(current["body"])
    trailing = 0
    while body and not body[-1].strip():
        body.pop()
        trailing += 1
    summary = "\n".join(body).strip()
    text = f"### {current['title']} (source: {current['publisher']})\n"
    if summary:
        text += f"{summary}\n"
    if current.get("link"):
        text += f"Link: {current['link']}\n"
    if trailing:
        text += "\n" * trailing
    return Item(
        text=text,
        title=current["title"],
        publisher=current["publisher"],
        link=current.get("link", ""),
        source_kind=NEWS,
    )


def _parse_stocktwits(text):
    """The stance summary is prologue; each message is one item."""
    lines = text.splitlines()
    items = []
    prologue = []
    for line in lines:
        match = _ST_ITEM_RE.match(line)
        if match and not line.startswith("["):
            match = None
        if match:
            items.append(
                Item(
                    text=line,
                    title=match.group("body") or "",
                    # the summary line reports the fetched counts and must not be
                    # mistaken for an item
                    publisher="stocktwits",
                    source_kind=STOCKTWITS,
                )
            )
        else:
            if items:
                items[-1] = Item(
                    text=items[-1].text + "\n" + line,
                    title=items[-1].title,
                    publisher=items[-1].publisher,
                    source_kind=items[-1].source_kind,
                )
            else:
                prologue.append(line)
    return "\n".join(prologue), items


def _parse_reddit(text):
    """Each subreddit group keeps its header; its posts are the items."""
    lines = text.splitlines()
    groups = []  # list of (header_lines, [items])
    current = None
    for line in lines:
        header = _REDDIT_HEADER_RE.match(line)
        if header:
            current = {"header": [line], "items": []}
            groups.append(current)
            continue
        item = _REDDIT_ITEM_RE.match(line)
        if item and current is not None:
            current["items"].append(
                Item(
                    text=line,
                    title=item.group("title"),
                    publisher="reddit",
                    group=header_sub(current),
                    source_kind=REDDIT,
                )
            )
            continue
        if current is None or not current["items"]:
            if current is None:
                current = {"header": [line], "items": []}
                groups.append(current)
            else:
                current["header"].append(line)
            continue
        last = current["items"][-1]
        current["items"][-1] = Item(
            text=last.text + "\n" + line,
            title=last.title,
            publisher=last.publisher,
            group=last.group,
            source_kind=last.source_kind,
        )
    # Every parsed group owns its header, including a group the fetcher
    # reported as having no posts: that header renders once, in place. It is
    # never promoted to a prologue, which would render it a second time.
    return "", groups


def header_sub(group):
    header = group["header"][0] if group["header"] else ""
    return header.split(" — ")[0]


def parse_source(text, source):
    """Return ``(prologue, items)``; an unknown shape becomes one whole item."""
    if source == NEWS:
        return _parse_news(text)
    if source == STOCKTWITS:
        return _parse_stocktwits(text)
    return _parse_reddit(text)


# --- ranking and rendering -------------------------------------------------


def _rank(items, ticker, identity_terms):
    """Sort identity-relevant items first, keeping block order as the tie-break."""
    terms = {str(t).lower() for t in (identity_terms or ()) if t}
    terms.add((ticker or "").lower())
    relevant = []
    rest = []
    for index, item in enumerate(items):
        haystack = f"{item.title} {item.text}".lower()
        if any(term and term in haystack for term in terms):
            relevant.append((index, item))
        else:
            rest.append((index, item))
    relevant.sort(key=lambda row: row[0])
    rest.sort(key=lambda row: row[0])
    return [item for _, item in relevant + rest]


_MISSING_TITLE = "no title"


def _matchable_title(item):
    """The normalised title used for matching, or "" when it cannot identify one.

    ``No title`` is what the news formatter writes when the vendor sent no
    title at all, so it identifies nothing: two items carrying it are two
    different articles, not a duplicate pair.
    """
    title = _norm_title(item.title)
    return "" if title == _MISSING_TITLE else title


def _dedupe(items, near_dup_jaccard):
    """Collapse exact and near duplicates, keeping the first occurrence.

    An exact duplicate is a shared non-empty link, or a shared non-empty
    normalised title.  An empty link and an empty or missing title never
    establish a match, so two untitled items stay distinct.
    """
    kept = []
    removed = []
    for item in items:
        link = (item.link or "").strip().lower()
        title = _matchable_title(item)
        duplicate = None
        for previous in kept:
            previous_link = (previous.link or "").strip().lower()
            if link and previous_link and link == previous_link:
                duplicate = previous
                break
            previous_title = _matchable_title(previous)
            if title and previous_title and title == previous_title:
                duplicate = previous
                break
        if duplicate is None and title:
            for previous in kept:
                previous_title = _matchable_title(previous)
                if (
                    previous.publisher
                    and previous.publisher == item.publisher
                    and previous_title
                    and _jaccard(previous_title, title) >= near_dup_jaccard
                ):
                    duplicate = previous
                    break
        if duplicate is not None:
            removed.append(item)
        else:
            kept.append(item)
    return kept, removed


def _truncate(text, cap):
    """Shorten one item to fit ``cap`` including the marker, on a word boundary."""
    if len(text) <= cap:
        return text
    if cap <= len(TRUNCATION_MARKER):
        return ""
    room = cap - len(TRUNCATION_MARKER)
    cut = text[:room]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return (cut.rstrip() + TRUNCATION_MARKER)[:cap]


# --- the entry point -------------------------------------------------------


def condense_source(
    text,
    *,
    source,
    ticker,
    identity_terms,
    budget_chars,
    near_dup_jaccard=0.8,
    count_tokens: Callable[[str], int | None] | None = None,
):
    """Condense one source block, returning the text to use and its report."""
    if not isinstance(text, str):
        raise CondensationError(f"{source}: expected a string block, got {type(text).__name__}")
    if not isinstance(budget_chars, int) or isinstance(budget_chars, bool) or budget_chars <= 0:
        raise CondensationError(f"{source}: budget_chars must be a positive integer")

    before_tokens = count_tokens(text) if count_tokens else None
    chars_before = len(text)

    if not text.strip():
        return text, CondensationReport(
            source=source, chars_before=chars_before, chars_after=chars_before,
            tokens_before=before_tokens, tokens_after=before_tokens,
        )

    if _is_placeholder(text):
        if len(text) > budget_chars:
            raise CondensationError(
                f"{source}: protected placeholder exceeds its cap ({len(text)} > {budget_chars})",
                budget_exception=True,
            )
        return text, CondensationReport(
            source=source, items_in=0, items_out=0,
            chars_before=chars_before, chars_after=chars_before,
            tokens_before=before_tokens, tokens_after=before_tokens,
        )

    prologue, items = parse_source(text, source)
    fallbacks = 0
    if source == REDDIT and isinstance(items, list):
        groups = items
        flat = [(group, item) for group in groups for item in group["items"]]
        if not groups:
            prologue, flat = text, []
    else:
        groups = None
        flat = items

    if not flat and not groups:
        # Nothing recognisable: budget the block as a single item and keep the
        # bytes intact, so an unknown shape is limited but never reshaped.
        prologue, flat = "", [Item(text=text)]
        fallbacks = 1

    item_list = [item for _, item in flat] if groups is not None else flat

    if not item_list and prologue:
        if len(prologue) > budget_chars:
            raise CondensationError(
                f"{source}: protected preamble exceeds its cap ({len(prologue)} > {budget_chars})",
                budget_exception=True,
            )
        return text, CondensationReport(
            source=source, chars_before=chars_before, chars_after=chars_before,
            tokens_before=before_tokens, tokens_after=before_tokens,
        )

    ranked = _rank(item_list, ticker, identity_terms)
    kept, removed = _dedupe(ranked, near_dup_jaccard)

    if groups is not None:
        out, dropped, truncated, notes = _fit_reddit(prologue, groups, kept, budget_chars)
    else:
        out, dropped, truncated, notes = _fit_flat(prologue, kept, budget_chars)

    if len(out) > budget_chars:
        raise CondensationError(
            f"{source}: protected content cannot fit its cap ({len(out)} > {budget_chars})",
            budget_exception=True,
        )

    after_tokens = count_tokens(out) if count_tokens else None
    removals = tuple(
        RemovalRecord(source=source, identifier=safe_id(item.link or item.title), reason="duplicate")
        for item in removed
    ) + tuple(
        RemovalRecord(source=source, identifier=safe_id(item.link or item.title), reason=reason)
        for item, reason in notes
    )
    report = CondensationReport(
        source=source,
        items_in=len(item_list),
        items_out=len(kept) - dropped,
        duplicates_removed=len(removed),
        items_dropped=dropped,
        items_truncated=truncated,
        chars_before=chars_before,
        chars_after=len(out),
        tokens_before=before_tokens,
        tokens_after=after_tokens,
        parse_fallbacks=fallbacks,
        removals=removals,
    )
    logger.info(
        "%s condensation: items_in=%d items_out=%d duplicates_removed=%d "
        "items_dropped=%d items_truncated=%d chars_before=%d chars_after=%d parse_fallbacks=%d",
        source, report.items_in, report.items_out, report.duplicates_removed,
        report.items_dropped, report.items_truncated, report.chars_before,
        report.chars_after, report.parse_fallbacks,
    )
    return out, report


def _truncate_news(item, room):
    """Shorten a news item's summary, keeping its heading and Link line whole.

    Returns ``""`` when the heading, the summary marker and the Link line cannot
    all fit: a half-written heading or a severed ``Link:`` line is worse than
    dropping the item, because the reader cannot tell what was lost.

    The result never exceeds ``room`` characters, including its trailing newline.
    """
    lines = item.text.split("\n")
    link_idx = None
    for index, line in enumerate(lines):
        if line.startswith("Link: "):
            link_idx = index
            break
    if link_idx is None:
        return ""
    heading = lines[0]
    link_line = lines[link_idx]
    summary = " ".join(ln for ln in lines[1:link_idx] if ln.strip()).strip()

    # heading + newline + summary + newline + link + newline
    fixed = len(heading) + 1 + len(link_line) + 2
    if fixed > room:
        return ""
    available = room - fixed
    if available < len(TRUNCATION_MARKER):
        return ""
    if len(summary) <= available:
        return f"{heading}\n{summary}\n{link_line}\n"
    cut = summary[: available - len(TRUNCATION_MARKER)]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return f"{heading}\n{cut.rstrip()}{TRUNCATION_MARKER}\n{link_line}\n"


def _fit_flat(prologue, kept, cap):
    """Keep whole items while they fit, then shorten at most one summary.

    The source's own separators are preserved: news items end with a trailing
    newline, so joining them with "\\n" would add a blank line that the
    fetcher did not emit.
    """
    out = prologue
    dropped = 0
    truncated = 0
    notes = []
    truncated_already = False
    remaining = list(kept)
    while remaining:
        item = remaining.pop(0)
        separator = ""
        if out and not out.endswith("\n"):
            separator = "\n"
        if len(out) + len(separator) + len(item.text) <= cap:
            out += separator + item.text
            continue
        if not truncated_already:
            room = cap - len(out) - len(separator)
            if item.source_kind == NEWS:
                shortened = _truncate_news(item, room)
            else:
                shortened = _truncate(item.text, room)
            if shortened:
                out += separator + shortened
                truncated = 1
                truncated_already = True
                notes.append((item, "truncated"))
                continue
        dropped += 1
        notes.append((item, "over_budget"))
    return out, dropped, truncated, notes


def _fit_reddit(prologue, groups, kept, cap):
    """Budget Reddit group by group, keeping every header in place.

    Groups render in their original order.  A group that had posts but lost
    them all keeps its header plus an omission marker, so a subject never
    disappears.  A group the fetcher already reported as empty keeps its own
    empty state and is never given an omission marker.
    """
    keep_ids = {id(item) for item in kept}
    out = prologue
    dropped = 0
    notes = []
    for group in groups:
        header = "\n".join(group["header"])
        live = [item for item in group["items"] if id(item) in keep_ids]
        body = ""
        kept_here = 0
        for item in live:
            candidate = ("\n" if body else "\n") + item.text
            if len(out) + len(header) + len(body) + len(candidate) <= cap:
                body += candidate
                kept_here += 1
            else:
                dropped += 1
                notes.append((item, "over_budget"))
        had_posts = bool(group["items"])
        if kept_here:
            block = header + body
        elif had_posts:
            # Posts existed and the budget removed them: say so.
            block = f"{header}\n{OMITTED_MARKER}"
        else:
            # The fetcher reported this group as having no posts at all.
            block = header
        separator = "\n\n" if out else ""
        if len(out) + len(separator) + len(block) > cap:
            raise CondensationError(
                "reddit: group headers and omission markers exceed the source cap",
                budget_exception=True,
            )
        out += separator + block
    return out, dropped, 0, notes


# --- audit footer ----------------------------------------------------------


def render_audit_footer(reports):
    """A short, content-free note telling the model what was trimmed."""
    reports = list(reports)
    parts = []
    for report in reports:
        if report.budget_exception:
            parts.append(f"{report.source}: budget exception, original block kept")
            continue
        bits = []
        if report.duplicates_removed:
            bits.append(f"{report.duplicates_removed} duplicates removed")
        if report.items_dropped:
            bits.append(f"{report.items_dropped} items dropped")
        if report.items_truncated:
            bits.append(f"{report.items_truncated} items shortened")
        if bits:
            suffix = ", listed messages are a subset" if report.source == STOCKTWITS else ""
            parts.append(f"{report.source}: {'; '.join(bits)}{suffix}")
    body = "no items were removed or shortened" if not parts else "; ".join(parts)
    text = f"<input_condensation>\nInput trimmed (character counts, not tokens): {body}.\n</input_condensation>"
    if len(text) > FOOTER_MAX_CHARS:
        head = "<input_condensation>\nInput trimmed (character counts, not tokens): "
        tail = "\n</input_condensation>"
        room = FOOTER_MAX_CHARS - len(head) - len(tail)
        text = head + body[: max(0, room - 1)].rstrip() + "…" + tail
    # The footer sits on its own line between the closing tag of the last data
    # block and the analysis heading; the blank line before the heading is
    # supplied here so an empty footer leaves the prompt byte-identical.
    return text + "\n"


def report_as_dict(report):
    """The persisted form of a report: counts and opaque ids only."""
    return {
        "source": report.source,
        "items_in": report.items_in,
        "items_out": report.items_out,
        "duplicates_removed": report.duplicates_removed,
        "items_dropped": report.items_dropped,
        "items_truncated": report.items_truncated,
        "chars_before": report.chars_before,
        "chars_after": report.chars_after,
        "parse_fallbacks": report.parse_fallbacks,
        "budget_exception": report.budget_exception,
        "removals": [
            {"identifier": record.identifier, "reason": record.reason}
            for record in report.removals
        ],
    }
