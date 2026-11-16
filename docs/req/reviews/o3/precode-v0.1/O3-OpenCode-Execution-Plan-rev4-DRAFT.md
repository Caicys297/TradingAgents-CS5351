# O3 Execution Plan — rev.4 (read-only inspection)

Status: DRAFT for A review. Approval pending. Documentation revision only.
Base: branch `docs/o3-precode-review-v0.1`, HEAD `a0f2933`; `origin/main` at `4f87e29`.
Companion: O3 Test Plan v0.3 (draft). Registry: `docs/req/requirements.yaml` @
`a0f2933`, `registry_version: 1.0.0-a-baseline`.

## 1. Inspection baseline

| Item | State at `a0f2933` |
|---|---|
| `tradingagents/agents/analysts/condensation.py` | absent |
| `test/offline/test_input_condensation.py` | absent |
| `test/offline/conftest.py` | present; blocks connect / connect_ex / getaddrinfo / curl_cffi |
| `pyproject.toml:59` | `testpaths = ["tests", "test/offline"]` already set |
| `default_config.py` | no `input_*` keys (checked L130–152) |
| `docs/test-approvals/` | `TEMPLATE.md` only; no O3 record |

Registry-derived, adopted without reinterpretation:
`total_chars: 24000`, `news_cap_chars: 12000`, `stocktwits_cap_chars: 6000`,
`reddit_cap_chars: 6000`, `near_duplicate_jaccard: 0.8`, `first_duplicate_wins: true`,
`budget_exception: "use original affected block, record budget_exception, exclude from
budget-pass calculations"`.
O2 allowlist L29 already names the cap fields, so their names are fixed: `input_news_cap_chars`,
`input_stocktwits_cap_chars`, `input_reddit_cap_chars`, `input_budget_chars`,
`input_condensation_enabled`, `input_near_dup_jaccard`.

## 2. Verified corpus structure

- News (`news.py:78–83`): `### {title} (source: {publisher})` / summary / `Link: {url}` /
  blank line. One item per heading.
- StockTwits (`stocktwits.py:151–162`): optional `Screened by Jev …` note, then a
  **summary line** `Bullish: n (x%) · Bearish: … · Unlabeled: … · Total: {N} most-recent
  messages`, blank line, then one `[created · @user · tag] body` per message.
- Reddit (`reddit.py:324–336`): optional note, then per-subreddit
  `r/{sub} — {n} recent posts mentioning {TICKER}:`, then `  [date] title` plus optional
  `    body excerpt: …`; plus `<no posts …>` placeholder blocks.

## 3. Source structure rules

Prologue = text before the first item of a source. It is preserved verbatim,
rendered at the head of its source block, and **counted inside that source's cap**.

- **StockTwits summary line is prologue, not an item.** It is never ranked, never dropped,
  and never counted in `items_in`.
- **Reddit subreddit header is prologue for that subreddit group.** Parse each header and its posts as a separate group. Rank posts without losing group membership. Render groups in their original order with the original headers and their own retained posts. Count all rendered headers, separators and omission markers in the Reddit source cap.
- **Stance counts must not be misread after trimming.** The StockTwits summary reports the
  counts of messages fetched *before* condensation. When any message item is dropped or
  truncated, the report records `stocktwits_items_dropped` / `stocktwits_items_truncated`,
  and the audit footer states that the listed messages are a subset. The summary line is
  never rewritten, so the model can still read the original stance split.
- **All Reddit posts dropped for a group:** keep the group header and append a fixed marker
  `[all posts omitted by input budget]`, so the reader sees a subject with no rows rather
  than a missing subreddit. A confirmed this behavior in the review of `8508be9`.
- If the combined protected content, including required omission markers and separators, exceeds the source cap, that is a protected-content failure:
  raise `CondensationError` (§5). It is not silently truncated.

## 4. Configuration and budget

Append-only block in `tradingagents/default_config.py`, read through
`dataflows.config.get_config()`:

| Key | Default |
|---|---|
| `input_condensation_enabled` | `True` |
| `input_budget_chars` | `24000` |
| `input_news_cap_chars` | `12000` |
| `input_stocktwits_cap_chars` | `6000` |
| `input_reddit_cap_chars` | `6000` |
| `input_near_dup_jaccard` | `0.8` |
| `input_condensation_audit_note` | `True` |

Validation: each cap must be a positive integer; the sum of the three caps must not exceed
`input_budget_chars`; otherwise `ValueError`.

Rendering and accounting, per FR-04:
- each rendered source block, including its prologue, separators and markers, fits its cap;
- the three rendered blocks together fit `input_budget_chars`; unused capacity stays with
  its own source and is never redistributed;
- the `<input_condensation>` footer is at most 240 characters, measured separately, and
  **is not part of the three-source budget**; static prompt text is also outside it.

## 5. Fallback and interface

Two failure classes are kept distinct:

| Class | Trigger | Handling | `budget_exception` |
|---|---|---|---|
| Protected content exceeds its source cap | a protected placeholder, or a prologue, cannot fit inside that source's cap | `CondensationError`; the node uses the **original block** for that source | **`True`**, and the entire run is excluded from FC-5 pass results |
| Any other parsing / input fault | `None` input, malformed type, unexpected internal error | `CondensationError`; node logs a warning and uses the original block; the run completes | **not set**; it is reported as a parse/input error, never as a budget result |

`budget_exception` is therefore set **only** by the first class.

**Footer attachment point (single, explicit):** the footer is appended by the analyst node
inside `_build_system_message`, at the end of the data-source section and immediately before
the `## How to analyze this data` heading. It is not injected into any source block and not
into `{news_block}` / `{stocktwits_block}` / `{reddit_block}`. The alternative — appending
after `_build_system_message` returns — is rejected because it would place the footer after
the output-field specification.

**Private helper change confirmed by A:** `_build_system_message` keeps its current keyword-only
parameters and adds two defaulted keyword arguments, `audit_footer: str = ""` and
`stocktwits_trimmed: bool = False`. Existing calls remain valid. The helper is private. A confirmed that defaulted keyword arguments are acceptable.

**Byte-level compatibility when disabled:** when `input_condensation_enabled` is `False`,
the node skips the condenser, passes `audit_footer=""`, and the template renders exactly the
baseline string. The audit footer must not leave URL-encoded whitespace (use str.format).
T-R2 asserts byte equality against the baseline and uses spies to compare the fetchers’ call counts, order and arguments.

## 6. Implementation sequence

1. **Test scaffolding first** — `test/offline/test_input_condensation.py` with the approved
   cases, failing against the absent module.
2. **Pure condenser** — new `tradingagents/agents/analysts/condensation.py`:
   `CondensationError`; `RemovalRecord` / `CondensationReport` (including
   `parse_fallbacks`, `budget_exception`); per-source parsers returning
   `(prologue, items)`; `_norm_title`, `_jaccard`; `_rank`; `_validate_caps`; `_render`;
   `safe_id`; `condense_source(...)`; `render_audit_footer(...)`.
   Covers FR-01…04, FR-06, FR-07, FR-09, NFR-01, NFR-05.
3. **Optional tokenizer** — `count_tokens(text) -> int | None`; no `tiktoken` core
   dependency; estimates labelled as estimates. Covers FR-07, FR-09.
4. **Config block** — append-only `input_*` keys; coordinate wording with B. Covers FR-08.
5. **Wire the Sentiment Analyst** — condense the three blocks after the fetches
   (`sentiment_analyst.py:66–76`) and before `_build_system_message`; implement §5 fallback
   and the footer attachment point; skip entirely when disabled. Do not touch the system
   message, `instrument_context` or `current_date`. Covers FR-05, FR-08, NFR-04, NFR-06.
6. **Verification and evidence capture.**

## 7. Requirement and test mapping

| Registry | Automated cases (default collection) | Manual |
|---|---|---|
| O3-FR-01 | T-N8, T-E6 | — |
| O3-FR-02 | T-N1, T-N4, T-B6, T-B7, T-B8 | — |
| O3-FR-03 | T-N3 | — |
| O3-FR-04 | T-N3, T-N7, T-B2, T-B3, T-B5 | — |
| O3-FR-05 | T-N5, T-E2 | — |
| O3-FR-06 | T-N1, T-N3, T-E6 | — |
| O3-FR-07 | T-N6, T-E5, T-E7 | T-R3 |
| O3-FR-08 | T-R2, T-E4 | — |
| O3-FR-09 | T-E5, T-E7 | — |
| O3-NFR-01 | T-R4, T-N3, T-R2 | — |
| O3-NFR-02 | — | T-P1 |
| O3-NFR-03 | T-R1 (sub-check T-R5) | — |
| O3-NFR-04 | T-B4, T-E3 | — |
| O3-NFR-05 | T-E8 | — |
| O3-NFR-06 | T-R1, T-R2 | — |

T-R5 is **a sub-check of T-R1**, not a new registry mapping. Existing registry `verification`
lists are unchanged.

## 8. Verification commands

```sh
# 1. Collection — automated cases only; one case ID may expand to several
#    parametrized nodes, so no total node count is asserted.
pytest --collect-only -q

# 2. Targeted file
pytest -q test/offline/test_input_condensation.py

# 3. Full default suite (already includes test/offline)
pytest -q

# 4. Explicit offline + inherited
pytest -q tests test/offline -m "not integration"

# 5. Contract/shape cases
pytest -q test/offline/test_input_condensation.py -k "shape or contract"

# 6. Lint
ruff check tradingagents/agents/analysts/condensation.py \
           tradingagents/agents/analysts/sentiment_analyst.py \
           test/offline/test_input_condensation.py
```

Collection acceptance: every individual approved case ID is represented by at least one
collected node under `test/offline/test_input_condensation.py`, and no automated approved
case is missing or skipped. The number of collected nodes is not prescribed. T-R3 and T-P1
are not expected in collection any more than any other manual observation.

**T-R5 as a sub-check of T-R1, per approved case:** exercise both the direct condenser call and the complete Sentiment Analyst node with fake fetchers and a fake LLM already installed. For each test, install a counting probe on `socket.socket.connect`, `socket.socket.connect_ex`,
`socket.getaddrinfo`, `curl_cffi.requests.Session.request`,
`curl_cffi.requests.AsyncSession.request` and `urllib.request.urlopen`. Each patched
callable increments a counter and raises. The assertion
`assert probe.attempts == 0` runs **after** the tested call returns, so an implementation
that catches the exception still fails. One recorded attempt fails the case.

## 9. Manual, non-CI records

| Item | When | Evidence | Status |
|---|---|---|---|
| T-R3 | after the offline suite, once, human-run | provider usage in `transcripts/o3/` | diagnostic only |
| T-P1 (FC-14) | once after implementation | elapsed time, peak memory, fixture SHA-256, machine ID | diagnostic only; no threshold |

Both are recorded in the approval record's verification section, not in CI.

## 10. Human approval gates

Per `docs/test-approvals/TEMPLATE.md`, in this order:

1. Requirements registry commit SHA recorded (`a0f2933` unless the registry moves).
2. **F approves the O3 test plan** (v0.3 with the case-ID list from `requirements.yaml`)
   via a fixed GitHub comment on an immutable commit or attachment.
3. **A approves this execution plan** (rev.4) at an immutable commit, including allowed
   files and exclusions.
4. Only then does the first implementation commit exist; its SHA and time are recorded.

The over-cap protected-content case is a T-B4 parameter and the StockTwits trimming assertions belong to T-N8. Use the actual shared news formatter in the T-N8 contract test. Record the final review commit and approved case scope before implementation.

## Open review item

B can confirm whether omitting `input_condensation_audit_note` from the O2 fingerprint allowlist is intentional. This plan does not change the allowlist.
