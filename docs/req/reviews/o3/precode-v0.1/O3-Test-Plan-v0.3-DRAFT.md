# O3 Test Plan v0.3 — Input Condensation

Status: Draft v0.3 for F review. Supersedes v0.2. Owner: C. Test execution and pre-code approval are pending.

Basis: requirements baseline `4f87e29`, inspected from `a0f2933`, `docs/req/requirements.yaml` (O3-FR-01–09 and O3-NFR-01–06).
Use network-disabled fixtures and a fake model for node-level checks. Use the actual source
shapes for news, StockTwits and Reddit. Test configured defaults of 24,000 total and
12,000 / 6,000 / 6,000 characters. Count separators and markers. No redistribution. The audit footer has a separate 240-character cap.
Capture the final node prompt and compare protected text verbatim. Capture logs and use
synthetic values for privacy tests.

### Normal
| ID | Scenario | Expected |
| --- | --- | --- |
| T-N1 | 3 sources, 3 identical news articles among 8 | 1 copy kept, other items intact, `duplicates_removed == 2` |
| T-N2 | 10 real-shaped articles, budget generous | Nothing dropped; `chars_after == chars_before` modulo normalisation; audit note lists 0 removals |
| T-N3 | 10 articles, tight budget | Only top-ranked kept; ordering preserved; `<input_condensation>` footer present |
| T-N4 | News + StockTwits with the same headline | Both kept (FC-3) |
| T-N5 | Node-level test with fake LLM capturing messages | Captured prompt contains condensed blocks plus unchanged instrument identity, date and safety text |
| T-N6 | 3× duplication fixture | Length reduction ≥ 30 % (FC-10), figure labelled "chars" |
| T-N7 | Invalid cap allocation, or a block over its cap while the total fits | A non-positive cap, or caps summing above input_budget_chars, raises ValueError. A valid over-cap block is condensed to its own cap; unused capacity is not redistributed. |
| T-N8 | Real formatter contract and source structure | Feed actual shared news formatter output from fixed input into the parser and compare against the expected structure. Check that structural drift fails the contract. For StockTwits, assert the original summary bytes, subset notice when the audit footer is enabled, and drop/truncation counts. For multi-group Reddit, assert each verbatim header stays attached to its group in original group order, retained posts stay under their own header, and fully omitted groups keep their header and the omission marker. Count headers, markers and separators against the source cap. |

### Boundary
| ID | Scenario | Expected |
| --- | --- | --- |
| T-B1 | Empty input (`""`) | Returns input unchanged, all counts 0, no exception |
| T-B2 | Exactly at cap (chars == cap) | No truncation; the block, its prologue and separators exactly fill the cap. |
| T-B3 | Budget + 1 char | Output fits the cap including the marker, or the ordinary item is dropped |
| T-B4 | Protected placeholder or protected preamble over its source cap | Parameterize both cases. Return the affected source block unchanged, record `budget_exception=True`, and exclude the entire run from FC-5 pass results. Include the combined protected text of multiple Reddit groups. |
| T-B5 | Single ordinary item longer than its source cap | Truncated at a word boundary including …[truncated] when it fits, otherwise dropped; prologue and protected text preserved. |
| T-B6 | Two items, Jaccard exactly 0.8 | Treated as duplicates (inclusive threshold) |
| T-B7 | Two items, Jaccard 0.79 | Not merged |
| T-B8 | Article with no link and empty title | Not merged with another empty-title article; retained or dropped by rank only |
| T-B9 | Non-ASCII (Chinese headline set) | Same dedup/ranking behaviour; char counts are code-point counts |

### Exception
| ID | Scenario | Expected |
| --- | --- | --- |
| T-E1 | None input | CondensationError; the node uses the original block, logs a warning, completes the run; budget_exception is not set. |
| T-E2 | Fetcher returns `<Yahoo Finance news unavailable…>` placeholder | Placeholder retained verbatim, never counted as duplicate (FC-6) |
| T-E3 | Condenser raises an internal fault | Node catches it, uses the uncondensed block, run completes; the record names a parse/input error, not a budget result. |
| T-E4 | Unknown/invalid config value (e.g. `input_budget_chars = -1`) | `ValueError` at config validation, not silent mid-run |
| T-E5 | Tokenizer absent | `tokens_after is None`; no token claim (FC-11) |
| T-E6 | Unknown block shape with sufficient budget | The whole block enters budgeting as one item and parse_fallbacks > 0. |
| T-E7 | Optional tokenizer available | On the duplicate-heavy fixture record before/after estimates from the same tokenizer, `after < before`, explicitly labelled estimated. T-E5 covers absence. |
| T-E8 | Audit privacy | Inject synthetic raw titles, URLs, body text, endpoints and credentials. Capture INFO and any audit serialization used by O3 and assert none of those values appear there. Verify stable safe IDs and counts. |

### Regression and manual observations
| ID | Scenario | Expected |
| --- | --- | --- |
| T-R1 | Explicit offline collection and execution | Collection contains at least one node for every approved automated case; all pre-existing suites pass. Includes sub-check T-R5. |
| T-R2 | Disabled condensation baseline | Compare the final prompt byte-for-byte with the baseline. Spy on all three fetchers and assert the same call count, order and arguments as the baseline. |
| T-R3 | Manual live diagnostic | Run once by a human after the offline suite; record provider usage in transcripts/o3/. Diagnostic only; not a pass criterion; not in CI. |
| T-R4 | Repeat and re-condense | Two runs on identical input/config return byte-identical output and equal reports. Re-condense the first output with the same config. Assert identical text and zero further duplicates, drops or truncations. |
| T-R5 | No-network probe (T-R1 sub-check) | Exercise the condenser directly and the entire Sentiment Analyst node with fake fetchers and a fake LLM already installed. Use a test-local counting probe around each call, including `urlopen`. Assert zero attempts after each call. A recorded attempt fails the corresponding test even if its exception was caught. |
| T-P1 | Manual performance record (FC-14) | Record elapsed time, peak memory, fixture SHA-256 and machine ID on a 200,000-character fixture. No threshold. Diagnostic only; not in CI. |

## Traceability

| Registry ID | Verification |
| --- | --- |
| O3-FR-01 | T-N8, T-E6 |
| O3-FR-02 | T-N1, T-N4, T-B6–B8. Include an explicit same-publisher 0.85 case and assert the first item survives. |
| O3-FR-03 | T-N3. Include ties and check original order within each rank. |
| O3-FR-04 | T-N3, T-N7, T-B2, T-B3, T-B5. Assert default config, individual caps, aggregate cap and separate footer ≤ 240. |
| O3-FR-05 | T-N5, T-E2 |
| O3-FR-06 | T-N1, T-N3, T-E6. Assert both audit count equations including truncations. |
| O3-FR-07 | T-N6, T-E5, T-E7, T-R3 |
| O3-FR-08 | T-R2, T-E4. Check enabled and footer defaults and negative or oversubscribed caps. |
| O3-FR-09 | T-E5, T-E7 |
| O3-NFR-01 | T-R4, T-N3, T-R2 |
| O3-NFR-02 | FC-14 (manual record T-P1): log non-negative elapsed time and peak memory on a 200,000-character fixture with fixture fingerprint and machine identifier. |
| O3-NFR-03 | T-R1, including the T-R5 counting probe and the offline execution sequence. |
| O3-NFR-04 | T-B4, T-E3. Check unchanged source block, recorded budget exception where applicable and exclusion from budget-pass counts. |
| O3-NFR-05 | T-E8 |
| O3-NFR-06 | T-R1, T-R2 |

## Offline execution sequence (T-R1)

From the repository root, using the project test environment:

```sh
pytest --collect-only -q
pytest -q
pytest -q tests test/offline -m "not integration"
```

Check that default collection includes the O3 offline test nodes in
`test/offline/test_input_condensation.py`. Map collected nodes to each approved automated case ID, allowing multiple parameterized nodes per case,
and investigate missing or unexpectedly skipped deterministic cases with F. Keep the
manual T-R3 live observation and FC-14 / T-P1 record outside the offline run.

Record the tested commit, commands, collected case IDs, expected/actual outputs, and failures.
T-R3 is a manual diagnostic when provider usage is available. Record F's test-plan approval
against this version and case IDs using `docs/test-approvals/TEMPLATE.md`.

## Review scope

Automated cases: T-N1–N8, T-B1–B9, T-E1–E8, T-R1, T-R2 and T-R4.
T-R5 is an automated sub-check of T-R1. T-R3 and FC-14 (T-P1) are manual records.
The former T-E9 and T-E10 scenarios are covered by T-B4 and T-N8, respectively.
F's approval of this revision is pending.
