# O6 W-10 Unknown-Glyph Correction — Addendum v1.0

**Status:** Implemented in the correction branch; pending A's implementation review.
**Baseline:** `main@5cdd7589cc73817133a7ca73cf768fc02d0cd19a` (PR #20 CLI work at `e4b6f9ac` is included).
**Implementation start (UTC):** 2026-11-19T13:48:07Z
**Implementer:** F (via OpenCode), with C coordinating the shared `cli/display.py`; A reviews.

## Approval and requirement

- **A's supplemental scope approval:** https://github.com/Caicys297/TradingAgents-CS5351/pull/6#issuecomment-7010572705 (2026-11-19T13:30:20Z) — authorizes F to implement; limits scope to `cli/display.py` (`format_agent_tokens` unknown display + the two related docstrings), five additive real-handler display tests in `test/offline/test_o6_cli_wiring.py`, and this addendum; the local handoff note may be appended.
- **Approved correction package:** https://github.com/Caicys297/TradingAgents-CS5351/pull/6#issuecomment-7010031360
- **Authoritative requirement:** merged **O6-FR-02** — a token field with no reported value displays **Unknown**; an explicitly reported zero is a known value; a partial subtotal keeps its known figure marked partial.
- **Prior W-series scope:** the earlier W-1–W-14 approval was **test-only** (`#7000754482`, `#7001823145`) and encoded `--` for W-10; it did not authorize editing `cli/display.py`. This addendum supersedes **only** the W-10 glyph (`--` → `Unknown`), consistent with merged O6-FR-02. All other W-series approvals and expectations are unchanged.

## Change

`cli/display.py::format_agent_tokens` now returns `"Unknown"` (was `"--"`) for a field whose `status` is `"unknown"` or whose value is `None`; explicit zero still returns `"0"`, and a partial field still returns `"<n> (partial)"`. The docstring on `format_agent_tokens` and the corresponding sentence in `display_agent_summary` now say `"Unknown"`.

The legacy **run-level footer** (`update_display`, `"Tokens: --"`) is a different surface and is **outside this correction**; `update_display` is unchanged.

## Test coverage (covers W-9/W-10 once)

Five additive tests in `test/offline/test_o6_cli_wiring.py`, each rendering the real `display_agent_summary` over a real `StatsCallbackHandler` fed with real callback events, asserting the Market Analyst row's Input/Output cells:

| Case | Events | Input cell | Output cell |
|---|---|---|---|
| `test_w10_unknown_usage_renders_unknown` | one attributed call, no usage | `Unknown` | `Unknown` |
| `test_w10_explicit_zero_renders_zero` | one attributed call, `0/0` | `0` | `0` |
| `test_w9_partial_output_rendered` | `100/20` then `50` (output omitted) | `150` | `20 (partial)` |
| `test_w10_known_input_unknown_output` | one call, `input_tokens=100`, output omitted | `100` | `Unknown` |
| `test_w10_unknown_input_known_output` | one call, `output_tokens=5`, input omitted | `Unknown` | `5` |

A genuinely omitted field is modelled by constructing the usage metadata without that key (`AIMessage.model_construct`); it is never fabricated as zero. These five display tests are the single home for W-9/W-10 renderer expectations; the W-series evidence map references them rather than adding duplicates.

## Approval record

| Record | Status |
|---|---|
| Supplemental scope (A, `#7010572705`) | Confirmed |
| Implementation start UTC | 2026-11-19T13:48:07Z |
| Implementation review (A) | **Pending** |
| Merge | **Not requested** — this branch is left for human review |
