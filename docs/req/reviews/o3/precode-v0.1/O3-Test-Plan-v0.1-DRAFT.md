# O3 Test Plan v0.1 — Input Condensation

Status: Draft for F review. Owner: C. Test execution and pre-code approval are pending.

Basis: merged PR #2 at `4f87e29`, `docs/req/requirements.yaml` (O3-FR-01–09 and O3-NFR-01–06).
Use network-disabled fixtures and a fake model for node-level checks. Use the actual source
shapes for news, StockTwits and Reddit. Test configured defaults of 24,000 total and
12,000 / 6,000 / 6,000 characters. Count separators and markers. No redistribution.
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
| T-E7 | Optional tokenizer available | On the duplicate-heavy fixture record before/after estimates from the same tokenizer, `after < before`, explicitly labelled estimated. T-E5 covers absence. |
| T-E8 | Audit privacy | Inject synthetic raw titles, URLs, body text, endpoints and credentials. Capture INFO and any audit serialization used by O3 and assert none of those values appear there. Verify stable safe IDs and counts. |

### Regression / integration
| ID | Scenario | Expected |
| --- | --- | --- |
| T-R1 | Explicit offline collection and execution | All pre-existing tests pass (FC-15) |
| T-R2 | `input_condensation_enabled=False` golden | Output byte-identical to baseline (FC-12) |
| T-R3 | `test/live/` (manual, recorded in `transcripts/`) | Record provider input-token usage where available as a diagnostic observation |
| T-R4 | Repeat and re-condense | Two runs on identical input/config return byte-identical output and equal reports. Re-condense the first output with the same config. Assert identical text and zero further duplicates, drops or truncations. |

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
| O3-NFR-02 | FC-14: log non-negative elapsed time and peak memory on a 200,000-character fixture with fixture fingerprint and machine identifier. |
| O3-NFR-03 | T-R1: follow the offline execution sequence below. |
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
`test/offline/test_input_condensation.py`. Compare collected IDs with the approved cases
and investigate missing or unexpectedly skipped deterministic cases with F. Keep the
manual T-R3 live observation outside the offline run.

Record the tested commit, commands, collected case IDs, expected/actual outputs, and failures.
T-R3 is a manual diagnostic when provider usage is available. Record F's test-plan approval
against this version and case IDs using `docs/test-approvals/TEMPLATE.md`.
