"""Build a redacted, reviewer-accessible excerpt of the real T17 OpenCode session.

Reads the OpenCode sqlite store (read-only), selects only the parts needed to
verify the T17 fixture, oracle, test and measurement work, redacts secrets and
machine-specific paths, and writes ``transcripts/O5-S6-T17-session-excerpt.md``.

It preserves the original part order, the original message/part identifiers and
the original millisecond timestamps. It records which parts were omitted and why.
It never synthesises messages: every included line is copied from a stored part.

Run from the repository root:
    python transcripts/_build_o5_s6_t17_excerpt.py
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

SESSION_ID = "ses_e2a9d9cf9ffeDsLIgBv7qpqk4h"
DB = str(Path.home() / ".local" / "share" / "opencode" / "opencode.db")
OUT = Path(__file__).resolve().parent / "O5-S6-T17-session-excerpt.md"

# Parts are kept only if their text mentions one of these T17 verification anchors.
ANCHORS = (
    "O5-S6-T17-Performance",
    "build_o5_t17_fixture",
    "test_o5_macro_news_perf",
    "O5-T17-Perf-Fixture-1000",
    "O5-T17-Expected-Results",
    "O5-T17-Manifest",
    "4dbf85d7",
    "5a9e292d",
    "select_macro_news",
)

MAX_CHARS = 700

REDACTIONS = (
    (re.compile(r"[A-Za-z]:\\[^\s\"'`)]*"), "<PATH>"),
    (re.compile(r"/Users/[^\s\"'`)]*"), "<PATH>"),
    (re.compile(r"/home/[^\s\"'`)]*"), "<PATH>"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "<TOKEN>"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{20,}"), "<TOKEN>"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "<KEY>"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "<EMAIL>"),
    (re.compile(r"https://[^\s]*?@github\.com[^\s]*"), "<URL>"),
)


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def redact(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + " …[truncated for excerpt]"
    return text


def part_text(part: dict) -> str:
    kind = part.get("type")
    if kind == "text":
        return part.get("text", "")
    if kind == "tool":
        state = part.get("state", {}) or {}
        tool = part.get("tool", "")
        args = json.dumps(state.get("input", {}) or {}, ensure_ascii=False)[:400]
        out = str(state.get("output", "") or "")[:400]
        return f"[tool:{tool}] input={args} output={out}"
    return ""


def main() -> None:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    cur = con.cursor()
    if not cur.execute("select 1 from session where id=?", (SESSION_ID,)).fetchone():
        sys.exit(f"session {SESSION_ID} not found")

    rows = cur.execute(
        "select p.id, p.message_id, p.time_created, p.data "
        "from part p where p.session_id=? order by p.time_created",
        (SESSION_ID,),
    ).fetchall()
    total = len(rows)
    con.close()

    kept: list[tuple[int, str, str, str, str]] = []
    omitted = 0
    for pid, mid, ms, raw in rows:
        part = json.loads(raw)
        text = part_text(part)
        if not text or not any(anchor in text for anchor in ANCHORS):
            omitted += 1
            continue
        kept.append((ms, str(mid), str(pid), part.get("type", "?"), redact(text)))

    first = iso(rows[0][2]) if rows else "?"
    last = iso(rows[-1][2]) if rows else "?"

    lines = [
        "# O5 S6 T17 — redacted session excerpt (real OpenCode session)",
        "",
        "This file is a **bounded, redacted excerpt of real stored parts** from OpenCode",
        f"session `{SESSION_ID}`. It is derived mechanically from the session store; it is",
        "**not** a raw export and **not** an authored summary. Every entry below is copied",
        "verbatim from a stored message part except for redaction (paths, tokens, emails,",
        "URL credentials) and length truncation, both marked inline.",
        "",
        f"- Session: `{SESSION_ID}` (title `CONNECTION_OK`).",
        f"- Full session span: {first} .. {last} (UTC).",
        f"- Parts in session: {total}. Included here: {len(kept)}. Omitted: {omitted}",
        "  (omitted parts do not match any T17 verification anchor: the session also",
        "  contains unrelated earlier/later work; those parts are not reproduced).",
        "- Selection rule: a part is included only if its text mentions one of",
        "  `O5-S6-T17-Performance`, `build_o5_t17_fixture`, `test_o5_macro_news_perf`,",
        "  `O5-T17-Perf-Fixture-1000`, `O5-T17-Expected-Results`, `O5-T17-Manifest`,",
        "  `4dbf85d7`, `5a9e292d`, or `select_macro_news`.",
        "- Order: original ascending `time_created`. Identifiers are the original",
        "  `message_id` / `part_id`; timestamps are the original epoch-ms rendered as UTC.",
        "- Redaction: `[A-Za-z]:\\\\…`, `/Users/…`, `/home/…` → `<PATH>`; GitHub/OpenAI-style",
        "  tokens → `<TOKEN>`/`<KEY>`; emails → `<EMAIL>`; credentialed URLs → `<URL>`.",
        "  No unredacted secrets or private paths are published.",
        "",
        "## Entries (chronological)",
        "",
    ]
    for ms, mid, pid, kind, text in kept:
        lines.append(f"### {iso(ms)} | {kind} | part `{pid}` | message `{mid}`")
        lines.append("")
        lines.extend("    " + ln for ln in text.splitlines() or [""])
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT} (kept {len(kept)} / {total} parts, omitted {omitted})")


if __name__ == "__main__":
    main()
