# O3 — Input Condensation for the Sentiment Analyst

Status: v0.4 revised draft for team review (approval pending)
Owner: C (O3)
Baseline: TradingAgents `9fa1196` (imported in commit `970a9ea`)

---

## 1. Existing Problem

TradingAgents passes fetched financial data to the model as raw text. Three concrete
problems exist in the baseline:

**P1 — Repeated items can consume the same source budget.** Ticker news is formatted without deduplication (`news.py:87-134`). O3 deduplicates within each Sentiment Analyst source and preserves corroborating evidence across sources.

**P2 — Everything fetched is interpolated at full length.** The Sentiment Analyst
pre-fetches three sources and pastes all of them into one prompt:
`tradingagents/agents/analysts/sentiment_analyst.py:66-76` (`get_news` up to
`news_article_limit` = 20 articles, StockTwits `limit=30`, Reddit posts), then
`_build_system_message` (`sentiment_analyst.py:130-199`) puts each block verbatim into
`<start_of_news>…<end_of_reddit>` (lines 154-170). No length cap, no relevance ranking, no
per-source budget.

**P3 — There is no record of what was dropped.** Nothing in the run says an article was
removed or truncated, so a reader (or the reviewer) cannot tell a "no news" conclusion from
a "news we silently discarded" one. This conflicts with the existing principle encoded in
`context.py:190-201` (`report_or_absent`) and in the `<Yahoo Finance news unavailable…>`
placeholder (`news.py:126-129`), and with the prompt's own instruction to "be honest about
data limits" (`sentiment_analyst.py:184`).

**Supporting evidence the gap is known upstream:** `default_config.py:138-143` suggests
"decrease [news_article_limit] to reduce token usage" — i.e. today the only lever reduces
what is *fetched*, not what is *safely condensed*. So the fix is not a default config
change: we keep the fetched data and condense it with a record.

---

## 2. Functional Requirements

**FR-1 (Scope).** The feature applies to exactly one point in the pipeline: the inputs of
the **Sentiment Analyst** (`sentiment_analyst.py::create_sentiment_analyst`). It must be a
pure function callable without network access, so it is testable and reusable. Other
agents are out of scope for O3. Maintain one text-shape fixture per source and a contract test that fails if the shared news formatter changes shape.

**FR-2 (Deduplication).** Before the prompt is built, exact and near-duplicate items within
a source are collapsed to one representative:
- exact duplicate = same `link` (non-empty), or same normalised title;
- near duplicate = same publisher **and** title token Jaccard similarity ≥ 0.8.
Keep the first occurrence in the source block. Preserve duplicates across sources. Empty links and empty normalized titles do not establish a match.

**FR-3 (Importance-ordered retention).** Rank items mentioning the ticker or a resolved identity term first. Preserve original block order within each rank. Retain a prefix of the ranked items. The formatted v1 interface carries no reliable publication date.

**FR-4 (Input size control).** Apply one total character budget and three explicit source caps. Proposed defaults are 24,000 total and 12,000 / 6,000 / 6,000 for news / StockTwits / Reddit. Reject invalid caps or a sum exceeding the total with `ValueError`. Unused capacity stays with its source. Count rendered separators and any truncation marker. Drop lower-ranked whole items first, then truncate at most one ordinary summary at a word boundary if it fits with `…[truncated]`. Otherwise drop that item. Reserve space for protected placeholders. Measure static prompt text and the audit footer separately.

**FR-5 (Non-removable integrity region).** The following must be present in the final
prompt unchanged, and the condensation step must fail closed if it would remove them:
- the exact-ticker identity sentence produced by `build_instrument_context`
  (`context.py:107-169`), i.e. the current `instrument_context` string, injected at
  `sentiment_analyst.py:97,107`;
- the analysis date (`trade_date`) as injected by the prompt template
  (`Today's date is {current_date}`, `sentiment_analyst.py:97,106`);
- the safety/scope constraints that are already part of the system message: the
  `NO_EXTERNAL_TOOLS` block (`structured.py:36-39`), the "Report what your tools support;
  another agent decides the trade." sentence (`sentiment_analyst.py:93`), and the prompt
  template text itself — O3 condenses only the three interpolated data blocks
  (`{news_block}`, `{stocktwits_block}`, `{reddit_block}`), never the system message;
- any `<unavailable>` / "not an absence of news" placeholder from a fetcher — an absence
  marker is never condensed away or counted as a duplicate.

**FR-6 (Audit record).** Return per-source counts for items in/out, duplicates, drops, truncations, characters before/after, and parser fallbacks. Record each affected item with a stable non-secret identifier and reason. INFO logs contain counts only. When enabled, append an audit footer of at most 240 characters, measured separately from the source budget. Unknown block shapes enter budgeting as a single item and increment `parse_fallbacks`.

**FR-7 (Honest measurement).** We may claim **input length reduction** measured in
characters (deterministic, offline). We may claim **token reduction** only when measured by
one of:
(a) an offline tokenizer whose `encode(text)` length is recorded and labelled as an estimate;
(b) real provider `usage` data from a `test/live/` run, recorded in the transcript.
Character counts must never be labelled "tokens" in code, logs or the report.

**FR-8 (Configuration).** All knobs live in `DEFAULT_CONFIG` and are read through
`dataflows.config.get_config()` so `run_config`/`TRADINGAGENTS_*` overrides work:
`input_condensation_enabled` (True), `input_budget_chars` (total), three explicit source caps,
`input_near_dup_jaccard` (0.8), `input_condensation_audit_note` (True).
When `input_condensation_enabled` is False the prompt is byte-identical to the baseline.

**FR-9 (Opt-in tokenizer).** Token counting is behind an optional interface
`count_tokens(text) -> int | None`. With no tokenizer installed it returns `None` and the
run still works, reporting characters only. We do **not** add `tiktoken` to core
dependencies; if used, it goes in a `dev`/optional extra (see Open Questions).

---

## 3. Non-functional Requirements

**NFR-1 Determinism & idempotence.** Same input + same config → identical output bytes.
`condense(condense(x)) == condense(x)`.

**NFR-2 Performance.** Record elapsed time and peak memory on a 200,000-character fixture, with fixture fingerprint and machine identifier. These are diagnostic observations.

**NFR-3 Offline only.** Zero network calls in the condenser and its tests
(`tests/conftest.py::_no_network` already blocks sockets; the condenser must not need an
exception). Identity is passed in, not looked up.

**NFR-4 Fail-closed safety.** If a protected placeholder exceeds its source cap, raise `CondensationError`. The node uses the original source block and records `budget_exception=True`. Exclude that run from budget-pass results. Malformed inputs follow the baseline fallback path and emit a diagnostic. Verify outer prompt integrity at node level.

**NFR-5 Audit privacy.** Use stable non-secret item identifiers and counts-only INFO logs. Keep raw titles, links, payloads, endpoints and credentials out of persisted audit records.

**NFR-6 Compatibility.** No public signature of existing functions changes. Public names
of `news.py`, `sentiment_analyst.py`'s fetcher call pattern, and `graph/*` are preserved.

---

## 4. Fit Criteria

FC-14 records observations. Verify applicable pass/fail criteria with §5.

| ID | Criterion | Pass condition |
| --- | --- | --- |
| FC-1 | Duplicate collapse | An input where the identical article appears 3× yields exactly 1 copy; `duplicates_removed == 2`; the kept item's link is in the output. |
| FC-2 | Near-duplicate collapse | Same-publisher titles at Jaccard 0.85 retain the first occurrence. |
| FC-3 | Cross-source preserved | The same headline in news and StockTwits is **not** merged; both survive. |
| FC-4 | Ranking | Retain ticker/identity matches first and break ties in original block order. |
| FC-5 | Character budget | Each source fits its cap and the three rendered blocks fit the total. Footer is ≤ 240 characters separately. A budget exception cannot pass FC-5. |
| FC-6 | Protected region | FC-6a checks unchanged identity, date and safety text in the captured node prompt. FC-6b checks verbatim placeholder preservation at function level. |
| FC-7 | Audit completeness | `items_in - items_out == duplicates_removed + items_dropped`; `len(removals) == duplicates_removed + items_dropped + items_truncated`. Every affected item has a stable safe ID and INFO logs contain counts only. |
| FC-8 | Determinism | Two runs on the same fixture produce byte-identical output and equal reports. |
| FC-9 | Idempotence | Second pass reports `duplicates_removed == items_dropped == items_truncated == 0`. |
| FC-10 | Length, honest label | A fixture with 3× duplication reports a **character** reduction ≥ 30 %; the report never emits the word "token" for that figure. |
| FC-11 | Token claim (optional) | With the offline tokenizer, the estimated token count strictly decreases on the same fixture; without it, `tokens_after is None` and no token claim is made. |
| FC-12 | Opt-out | `input_condensation_enabled=False` → output equals baseline string exactly (golden test). |
| FC-13 | Fail-closed | A protected placeholder longer than its source cap raises `CondensationError`. The node uses the original source block, records the budget exception and excludes the run from FC-5. |
| FC-14 | Performance | Record time and peak memory with fixture fingerprint and machine identifier. No threshold. |
| FC-15 | Regression | Collect and run the offline tests explicitly with `pytest -q tests test/offline -m "not integration"`. |
| FC-16 | Source shape | Verify all three known source shapes. A formatter shape change fails the contract test. At runtime an unknown block enters budgeting as one item, with `parse_fallbacks > 0`. |

> FC-10 uses a proposed fixture-specific character-reduction target for team review.

---

## 5. Proposed Test Cases

New file: `test/offline/test_input_condensation.py` (pytest, no network, deterministic
fixtures in the file itself). Test FC-6a in T-N5 and FC-6b in T-E2.

### Normal
| ID | Scenario | Expected |
| --- | --- | --- |
| T-N1 | 3 sources, 3 identical news articles among 8 | 1 copy kept, other items intact, `duplicates_removed == 2` |
| T-N2 | 10 real-shaped articles, budget generous | Nothing dropped; `chars_after == chars_before` modulo normalisation; audit note lists 0 removals |
| T-N3 | 10 articles, tight budget | Only top-ranked kept; ordering preserved; `<input_condensation>` footer present |
| T-N4 | News + StockTwits with the same headline | Both kept (FC-3) |
| T-N5 | Node-level test with fake LLM capturing messages | Captured prompt contains condensed blocks plus unchanged instrument identity, date and safety text |
| T-N6 | 3× duplication fixture | Length reduction ≥ 30 % (FC-10), figure labelled "chars" |
| T-N7 | Invalid allocation or a block over its cap while total input fits | Reject invalid cap allocation with `ValueError`; condense a valid oversized block to its source cap. |
| T-N8 | Three known source shapes and a changed formatter shape | Three fixtures parse as expected; the format contract test fails for the changed shape. |

### Boundary
| ID | Scenario | Expected |
| --- | --- | --- |
| T-B1 | Empty input (`""`) | Returns input unchanged, all counts 0, no exception |
| T-B2 | Exactly at budget (`chars == budget`) | No truncation applied |
| T-B3 | Budget + 1 char | Output fits the cap including the marker, or the ordinary item is dropped |
| T-B4 | Protected placeholder longer than its source cap | Raise, fall back to original block, record exception and fail FC-5 |
| T-B5 | Single ordinary item longer than its source cap | Truncate if it fits including the marker, otherwise drop; preserve protected text |
| T-B6 | Two items, Jaccard exactly 0.8 | Treated as duplicates (inclusive threshold) |
| T-B7 | Two items, Jaccard 0.79 | Not merged |
| T-B8 | Article with no link and empty title | Not merged with another empty-title article; retained or dropped by rank only |
| T-B9 | Non-ASCII (Chinese headline set) | Same dedup/ranking behaviour; char counts are code-point counts |

### Exception
| ID | Scenario | Expected |
| --- | --- | --- |
| T-E1 | `None` input | `CondensationError`; node falls back, logs warning, returns report |
| T-E2 | Fetcher returns `<Yahoo Finance news unavailable…>` placeholder | Placeholder retained verbatim, never counted as duplicate (FC-6) |
| T-E3 | Condenser raises | Node catches, uses uncondensed prompt, run still completes (FC-13) |
| T-E4 | Unknown/invalid config value (e.g. `input_budget_chars = -1`) | `ValueError` at config validation, not silent mid-run |
| T-E5 | Tokenizer absent | `tokens_after is None`; no token claim (FC-11) |
| T-E6 | Unknown block shape with sufficient budget | Preserve the whole block as one item and record `parse_fallbacks > 0`. |

### Regression / integration
| ID | Scenario | Expected |
| --- | --- | --- |
| T-R1 | Explicit offline collection and execution | All pre-existing tests pass (FC-15) |
| T-R2 | `input_condensation_enabled=False` golden | Output byte-identical to baseline (FC-12) |
| T-R3 | `test/live/` (manual, recorded in `transcripts/`) | Record provider input-token usage where available as a diagnostic observation |

---

## 6. Proposed Module Interface

New module: `tradingagents/agents/analysts/condensation.py`

```python
@dataclass(frozen=True)
class RemovalRecord:
    source: str                 # "news" | "stocktwits" | "reddit"
    identifier: str             # stable non-secret identifier
    reason: str                 # "duplicate" | "over_budget" | "truncated"

@dataclass(frozen=True)
class CondensationReport:
    source: str
    items_in: int
    items_out: int
    duplicates_removed: int
    items_dropped: int
    items_truncated: int
    parse_fallbacks: int
    chars_before: int
    chars_after: int
    tokens_before: int | None
    tokens_after: int | None
    removals: tuple[RemovalRecord, ...]

class CondensationError(Exception): ...

def condense_source(
    text: str,
    *,
    source: str,
    ticker: str,
    identity_terms: tuple[str, ...],   # from resolve_instrument_identity
    budget_chars: int,
    near_dup_jaccard: float = 0.8,
    count_tokens: Callable[[str], int | None] | None = None,
) -> tuple[str, CondensationReport]: ...

def render_audit_footer(reports: Iterable[CondensationReport]) -> str: ...
```

- **Inputs:** already-fetched vendor text blocks (news / StockTwits / Reddit), the ticker,
  resolved identity terms, and config values. No network, no LLM.
- **Outputs:** condensed text block and a `CondensationReport`; `render_audit_footer`
  produces the optional `<input_condensation>` prompt footer.
- **Error handling:** `CondensationError` for malformed input, protected placeholder exceeds the source cap,
  or protected-region violation. The caller (`sentiment_analyst_node`) catches it, logs a
  warning, and falls back to the uncondensed block (NFR-4). The node records whether the fallback was a budget exception.

---

## 7. Expected Code Changes

**Existing files to modify:**
| File | Change | Risk |
| --- | --- | --- |
| `tradingagents/agents/analysts/sentiment_analyst.py` | Call `condense_source` for each block before `_build_system_message`; pass reports to the footer; catch `CondensationError` | **Medium** — this file is the analyst's own node, no other owner edits it for O3 |
| `tradingagents/default_config.py` | Append the O3 configuration block | **Medium — shared file**, see §8 |

**New files to create:**
- `tradingagents/agents/analysts/condensation.py`
- `test/offline/test_input_condensation.py`
- `docs/req/O3-input-condensation.md` (this file)

**Deliberately NOT modified:** `graph/trading_graph.py`, `graph/setup.py`,
`graph/propagation.py`, `dataflows/vendors/**`, `agents/structured.py`, `agents/context.py`.

---

## 8. Dependencies and Conflicts

| Feature | Source → consumer | Relationship to O3 |
| --- | --- | --- |
| O1 (A) | Yahoo market SMA → Market Analyst | Independent |
| O2 (B) | Run configuration and report files → CLI run directory and manifest | Shared configuration ownership |
| O3 (C) | Ticker news, StockTwits and Reddit → Sentiment Analyst | C owns the node and condenser |
| O4 (D) | Analyst reports → rating / REVIEW gate | Downstream consumer |
| O5 (E) | Global-news candidates → News Analyst | Parallel path sharing the news formatter |
| O6 (F) | Model callback events → usage summary and CLI | Cross-cutting measurement |

B owns `cli/run.py` and shared configuration structure. Coordinate an append-only O3 key block with B. E owns changes to the shared news formatter. Coordinate a stable text shape or versioned contract before changing it. O3 edits the Sentiment Analyst and its new condenser and tests. Shared state, CLI, graph wiring, structured invocation and vendor files are outside the v1 edit scope.

**O4 evidence boundary (A/C architecture discussion).** O4 consumes the resulting Analyst report. A budget exception, unavailable-source placeholder, or drop/truncation count describes input coverage. A present, non-empty Sentiment Analyst report must remain present for O4's missing-report check even when those markers occur. O4 still applies its missing-evidence rule when the required report is missing or empty. D owns the downstream gate and its tests. Verify this contract with a non-empty trimmed-report fixture and a missing/empty required-report control in O4's test plan.

**O6 file and interface boundary (C/F v1 discussion).** O6 uses Graph Config to deliver callbacks and proposes explicit Analyst identity at the subgraph boundary from `spec.key`. F's current candidate scope is `graph/setup.py` and `cli/stats_handler.py`. O3 owns `sentiment_analyst.py` and can proceed independently. O3 has no callback metadata or usage-handler integration requirement. Real-subgraph attribution and the final wiring point remain pending. First structured-call attribution is deferred. Coordinate with C if a later O6 revision needs to edit the Sentiment Analyst.

O3 measures characters in three source blocks. The team-wide history/debate compression policy and output token settings are a separate architecture decision. C proposes history-only compression with protected system/identity/date/safety text, B owns output configuration, and F coordinates measurement using tokenizer estimates or observed usage.

## 9. Open Questions

1. B supplies measurements from three real ticker runs. A confirms the proposed 24,000 / 12,000 / 6,000 / 6,000 defaults.
2. E and B confirm the shared formatter contract. Revisit passing structured `pub_date` only if the team requires date-based retention and agrees on a shared interface.
3. D tracks verification of the agreed O4 missing-report boundary. B confirms placement of the O3 configuration block and any later audit persistence.
4. Confirm footer default, identifier hashing and optional tokenizer choice before implementation. Review identifier exposure if inputs come from a small known set.
5. A confirms where to record the team-wide compression policy. F coordinates offline collection and D/F review the proposed tests.

## 10. Mapping to the Manager's Submission Template

| Manager's item | Section | One-line answer |
| --- | --- | --- |
| Optimization Target | Title, FR-1 | O3 — input condensation at the Sentiment Analyst's prompt-input stage |
| Issues in the Original Version | §1 | P1 repeated items in ticker news; P2 full verbose interpolation; P3 no removal record |
| Functional Requirement | §2 | FR-1 … FR-9 |
| Non-functional Requirement | §3 | NFR-1 … NFR-6 |
| Fit Criterion | §4 | FC-1 … FC-16, with FC-14 diagnostic |
| Test Cases | §5 | T-N1…8 normal, T-B1…9 boundary, T-E1…6 exception, T-R1…3 regression |
| Expected Modification Locations | §7 | `sentiment_analyst.py`, `default_config.py` (append-only), new `condensation.py` |
| Input and Output | §6 | Three vendor text blocks + ticker/identity/budget in → condensed blocks + `CondensationReport` out |
| Dependencies and Conflicts | §8 | B coordinates configuration, E and C coordinate the formatter, D owns O4 verification, and F owns O6 wiring |

---

## 11. Review Status

Status: v0.4 revised draft. Approval evidence pending. Implementation and test execution are pending.
Reviewer: (B: consolidation, C: architecture, D/F: test standards, A: sign-off)
Revision date: 2026-11-15
Revision basis: manager and C feedback on O3, A/C decisions on O4, and C/F scope review on O6.
Approval evidence: (to be attached — decision log entry + test-plan approval record;
implementation is not authorised until the test plan in §5 is manually approved)
