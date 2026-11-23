# CLI Demo Guide

**Audience:** whoever presents the CS5351 demo (C's deliverable, usable by A during the video/presentation).
**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`.
**Scope:** how to run the *real* CLI and what each artifact proves. It does not restate requirements and does not claim any requirement is verified.

Every command below is checked against the real entry point at that SHA: `cli/main.py` registers a Typer app whose script name is `tradingagents` (`pyproject.toml` → `[project.scripts] tradingagents = "cli.main:app"`). Options and defaults are quoted from `cli/main.py`, not invented.

---

## 1. What you need before the first command

| Requirement | Detail | Where it comes from |
|---|---|---|
| Python | **3.11 or later** (`requires-python = ">=3.11"`) | `pyproject.toml` |
| Package install | `pip install .` (or `uv pip install .`) from the repository root | `README.md` §Installation |
| An LLM provider key | e.g. `OPENAI_API_KEY`; the default provider is `openai` | `tradingagents/default_config.py` |
| Network | Vendors (Yahoo/StockTwits/Reddit…) and the model provider are called at run time | — |

**This guide was not executed end-to-end while writing it.** It was written from the source at the pinned SHA. Where a step needs a live key or network, that is marked.

---

## 2. Minimal smoke: confirm the CLI is the one you think it is

```bash
tradingagents --help
```

Expected: the analysis options (`--ticker`, `--date`, `--analysts`, `--save/--no-save`,
`--show/--no-show`, `--html/--no-html`, `--checkpoint/--no-checkpoint`,
`--clear-checkpoints`, `--portfolio`) plus the `backtest`, `login` and `logout` subcommands.

**Why this first:** it proves the console script resolves to `cli.main:app`. If it does not, everything later fails for the wrong reason.

---

## 3. CLI analysis (the main demo)

```bash
tradingagents --ticker NVDA --date 2026-11-19 --analysts market,news --no-save --no-show
```

What each flag does (from `cli/main.py`):

| Flag | Effect |
|---|---|
| `--ticker NVDA` | Skips the ticker prompt |
| `--date 2026-11-19` | Analysis date, `YYYY-MM-DD`; skips the date prompt |
| `--analysts market,news` | Comma-separated analyst keys; skips the analyst prompt |
| `--no-save` | Do not save the report tree (keeps the demo directory clean) |
| `--no-show` | Do not print the whole report at the end |
| `--html/--no-html` | HTML page on by default when saving |

This command still prompts for output language, research depth, LLM provider and thinking models unless the corresponding `TRADINGAGENTS_*` settings are supplied. Run it in a real terminal and make those selections on camera. Set your provider key in your local environment before running; do not put a key in the slides, recording or repository. For an unattended run, first set `TRADINGAGENTS_OUTPUT_LANGUAGE`, both `TRADINGAGENTS_MAX_DEBATE_ROUNDS` and `TRADINGAGENTS_MAX_RISK_ROUNDS`, `TRADINGAGENTS_LLM_PROVIDER`, and at least one of `TRADINGAGENTS_QUICK_THINK_LLM` or `TRADINGAGENTS_DEEP_THINK_LLM`, along with any provider credential required by the selected model. The exact missing settings can be checked against `cli/selections.py::unattended_gaps`.

---

## 4. What a run leaves on disk

Paths below are relative to `results_dir`, which defaults to `<TRADINGAGENTS_DATA_DIR>/logs`
(`TRADINGAGENTS_RESULTS_DIR` overrides it in `tradingagents/default_config.py`).

```
<results_dir>/<safe_ticker>/<analysis_date>/
    runs/<uuid4>/                     ← O2: reserved before the graph is built
        manifest.json                 ← O2: provenance (written once)
        o5_evidence.jsonl             ← O5: one JSON line per selector event
    reports/                          ← live section reports
    message_tool.log                  ← agent message/tool transcript
<results_dir>/<safe_ticker>/TradingAgentsStrategy_logs/
    full_states_log_<date>.json       ← decision record
```

**Three things to point at during the demo, and what each proves:**

| Artifact | Proves | Does **not** prove |
|---|---|---|
| `manifest.json` | A run directory was allocated and provenance was recorded | That the analysis is correct |
| `o5_evidence.jsonl` | The O5 selector emitted events for this run | That every news branch was exercised (one `V-LIMIT-ZERO` row proves only that branch) |
| Per-Analyst summary on the terminal | Usage attribution worked for this run | Provider-reported token totals |

**Important caveat for the presenter:** a **missing** `o5_evidence.jsonl` does not mean "no O5 events happened". Evidence persistence is explicitly soft-fail: failure logs `SINK_FAILED` on the independent logger `tradingagents.o5.evidence` and the run continues (`development_contract.o5.sink_failure`).

---

## 5. A run that cannot reach the model is still a useful demo

Deleting the API key makes the CLI fail at the model boundary. That is worth showing once, because it distinguishes a *configuration* failure from a *vendor* failure and from a *gate* outcome. Do not script it as the main demo; it demonstrates error handling, not analysis.

---

## 6. Showing the O4 gate without a live model

The deterministic part of O4 is a pure function, `tradingagents/agents/evidence_gate.py::check_evidence(state, selected_analysts)` — it reads only `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`, `final_rating` and `final_trade_decision`, and never mutates the state.

A safe on-camera alternative to a live run is to run the **existing offline** evidence-gate tests and show the assertions:

```bash
python -m pytest test/offline/test_evidence_gate.py -q
```

This is a **historical test suite run**, not a product demo. Say so. The gate's *authoritative* behaviour is what the tests encode; the demo should not imply that a green suite proves a real merge was ever blocked.

---

## 7. Backtest (optional; needs a longer window)

```bash
tradingagents backtest NVDA,AAPL --start 2026-06-01 --end 2026-06-30 --every 7
```

Flags: `--every` (days between analysis dates, default `7`), `--analysts`, `--asset-type` (`stock` or `crypto`), `--portfolio`, `--run-id`.

**Time cost warning:** a backtest is many full analyses. Do not run one live; record it beforehand or skip it.

---

## 8. Diagrams for the slides

The architecture figures live in the documents; reuse them rather than redrawing:

| Figure | Source | Format |
|---|---|---|
| Analysts in **parallel**, then debate → manager → trader → risk → PM → O4 gate → publication | [`architecture-blueprint.md`](architecture/architecture-blueprint.md) §5.1 | Mermaid (`flowchart TB`), with a plain-text fallback immediately below |
| Component map (`cli/`, `tradingagents/`, `docs/req/`) | [`architecture-blueprint.md`](architecture/architecture-blueprint.md) §3.1 | ASCII block |

**Why parallel matters on the slide:** O1, O3 and O5 attach to *different analyst legs*. Drawing them as `O1 → O3 → O5` would misdescribe the system; the blueprint says this explicitly.

---

## 9. What to say, and what not to say

Safe, evidence-backed statements:

- "The CLI reserves a run directory before the graph is built, and writes one manifest for that run."
- "O5 events land in the same run directory as the manifest."
- "The O4 gate is deterministic and pure; it produces the effective rating."

Statements to avoid unless the specific evidence is on screen:

- "All requirements are verified." — Coverage is partial; see [`trace-matrix.md`](architecture/trace-matrix.md).
- "T17 performance is met." — **S6 is stopped and acceptance is not completed.**
- "The gate blocked a real merge." — Only PR #41 E2/E5 and run #37 are on the record, with the limits listed in [`architecture-blueprint.md`](architecture/architecture-blueprint.md) §8.4.

---

## 10. Known gaps in this guide

| Gap | Detail |
|---|---|
| No end-to-end execution record | Written from source at the pinned SHA; no live run was performed while writing it |
| No screenshot set | Screenshots for the slides are A's to produce; this guide gives the commands, not the images |
| Backtest live-verified? | No. Command and flags are from `cli/main.py`; a full backtest was not executed |
| Exact `results_dir` on the demo machine | Depends on `TRADINGAGENTS_DATA_DIR` / `TRADINGAGENTS_RESULTS_DIR`; check with `python -c "from tradingagents.default_config import DEFAULT_CONFIG; print(DEFAULT_CONFIG['results_dir'])"` before presenting |
| O3 sample output | The O3 example shipped separately is a human-organized summary drawn from several historical dates, **not** one real Yahoo request. Do not present it as an end-to-end trace. |
