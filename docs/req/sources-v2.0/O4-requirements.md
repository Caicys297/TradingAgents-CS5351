# O4 — Decision Evidence Gate

**Status:** Revised discussion draft, not approved for implementation. **Proposed requirements draft revision:** O4-REQ-r3 (distinct from the team's Requirements Registry / Schema version 1.0.0; not a registry release). **Proposed v1 boundary:** this gate checks whether required analyst reports are present and non-empty. It does not certify the truth or completeness of every datum inside a non-empty report. O1's single-SMA insufficient-history text and O5's filtered-empty status do not automatically trigger `REVIEW`; D must specify any whole-report unavailable convention before expanding the gate. **O4/O5 boundary proposal:** empty O5 filtered news alone does not automatically imply O4 `REVIEW`. **Architecture direction (A/C):** CLI buffering for v1 is the agreed direction; provisional labelling is a documented rejected/alternative design (see §7 and Open Questions). **Registry note:** requirement priorities and the invariant representation below are proposals pending Member B's confirmation against Requirements Registry / Schema 1.0.0.

## 1. Existing Problem

The TradingAgents pipeline can publish a Portfolio Manager rating without any deterministic check that the analytical evidence the rating depends on is present. Confirmed source behavior:

- The Portfolio Manager node reads only `risk_debate_state.history`, `investment_plan`, `trader_investment_plan` and `past_context` (`tradingagents/agents/managers/portfolio_manager.py:30–40`); it does not directly read the four analyst-report fields.
- Those reports influence the run upstream: Bull/Bear researchers and the three risk debators interpolate `market_report`, `sentiment_report`, `news_report`, `fundamentals_report` via `report_or_absent` (`bull_researcher.py:18–21`, `bear_researcher.py:18–21`, `aggressive_debator.py:23–26`, `conservative_debator.py:23–26`, `neutral_debator.py:23–26`). An empty report is replaced by a "(No … report in this run…)" marker (`tradingagents/agents/context.py:190–201`), but no code enforces that the final rating reflects that absence.
- The rating becomes authoritative through `run_rating` (`tradingagents/agents/rating.py:106–112`), returning the typed `final_rating`, else a parsed rating, else `REVIEW`.
- The existing `REVIEW` mechanism (`rating.py:30`, `:74–93`, `:96–117`) is a rating-parsing safeguard only. Its cited rationale is issue "#1170" in code comments (`rating.py:10–13`).
- No deterministic evidence-completeness gate exists. A parseable rating flows unchanged to the memory log (`trading_graph.py:368–371`; `memory/log.py:56–57`), state log (`trading_graph.py:464`), markdown header (`reporting.py:25–26`), HTML header (`report_html.py:251`), and CLI (`cli/run.py:380`). The CLI also writes the Portfolio Manager's raw decision text into the report section and message area during streaming, before the post-run record step (`cli/run.py:330–334`).

**Restated baseline claim:** missing reports can influence the rating indirectly through the research and risk debates; the problem is that the baseline **lacks a deterministic final evidence-completeness gate capable of overriding a parseable rating when required evidence is missing**, and that the Portfolio Manager text is displayed before any such gate could run. `REVIEW` answers "can the rating be read?", not "was the evidence present?".

> GitHub issues referenced in code comments (#1170, #1176, #1435, #1466) are treated as code-comment references only and are **not independently verified** here.

## 2. Functional Requirements (FR)

**Priority column:** MoSCoW. Values are the O4 proposal; Member B confirms schema compatibility.

| ID | Requirement | Priority | Source / rationale |
|---|---|---|---|
| O4-FR-01 | The system MUST run a deterministic evidence-completeness check before the rating is treated as a valid result. | Must | Baseline gap: no evidence gate exists; `run_rating` (`tradingagents/agents/rating.py:106–112`) emits a rating with no report check. |
| O4-FR-02 | When every required report is present under the approved v1 structural rule, the check MUST preserve the original Portfolio Manager rating as the effective rating, unchanged in value. This does not certify data validity inside the reports. | Must | PM rating source: `tradingagents/agents/managers/portfolio_manager.py:80–86`; v1 preserves a valid call. |
| O4-FR-03 | When any required evidence item is missing (field absent) or empty (zero-length or whitespace-only), the effective rating MUST become `REVIEW`, with an explanation naming each failing item. | Must | Empty-report handling today: `report_or_absent` marker only (`tradingagents/agents/context.py:190–201`); `REVIEW` sentinel: `tradingagents/agents/rating.py:30`. |
| O4-FR-04 | If the team later approves an exact, whole-report explicit-unavailable convention, a required report matching that convention MUST be classified `unavailable` and trigger `REVIEW`. In v1 without that convention, non-empty text is only `present` under the structural rule; no broad substring search for `N/A` or `unavailable` is allowed. | Should | Optional extension; avoids falsely treating one unavailable indicator as an absent report. Sentinel not yet approved (Section 9 Q3). |
| O4-FR-05 | If the original Portfolio Manager rating is already `REVIEW`, the gate MUST NOT convert it to any tradeable rating. | Must | Existing `REVIEW` behavior: `tradingagents/agents/rating.py:96–117`; preserves the non-tradeable status. |
| O4-FR-06 | Reports from analysts not selected for the run MUST be classified `not_required` and MUST NOT count as missing evidence. | Must | Analyst selection mapping: `tradingagents/graph/analyst_execution.py:20–62`; unselected reports stay empty. |
| O4-FR-07 | The effective rating MUST be the single authoritative value observed by every enabled output surface that reads the rating. For v1 the agreed direction is **buffering**: the Portfolio Manager's raw final Buy/Sell decision MUST NOT be published as an authoritative result before the gate completes. Ordinary analysis progress may continue to display. The CLI writes PM text both to the report section (`final_trade_decision`, `cli/run.py:330–334`) and the message stream (`cli/run.py:241–300`), so both must be held until gating. After the gate, each surface publishes `effective_rating`. The exact integration location and shared-file modification scope remain subject to A/C confirmation after call-chain review. | Must | Surfaces: `trading_graph.py:370,405,464`, `reporting.py:26`, `report_html.py:251`, `cli/run.py:380`; CLI stream/report display `cli/run.py:241–340`. Buffering chosen by A/C (architecture direction; integration point still pending). |
| O4-FR-08 | Evidence classification MUST be deterministic for the same state and selected-analyst set; it MUST NOT depend on network, LLM, clock, or randomness. | Must | Deterministic identity precedent: `tradingagents/agents/context.py:61–82`; testability requirement. |
| O4-FR-09 | If the checker experiences a **recoverable internal failure** (an exception or inability to complete its own computation), the system MUST fail closed to `effective_rating = REVIEW`, preserve a diagnostic reason, and MUST NOT publish the ungated original tradeable rating. Every enabled final output surface MUST use the same `effective_rating`. This MUST be distinguished from invalid configuration (O4-FR-15), which aborts publication instead of producing a normal `REVIEW`. | Must | Fail-closed safety; parallels `structured.py` fallback design (`tradingagents/agents/structured.py:59–81`). Architecture direction A/C (integration point still pending). |
| O4-FR-10 | The checker MUST return structured results: per-item status (`present`/`missing`/`unavailable`/`not_required`), an overall verdict (`valid`/`review`), an effective rating, and a diagnostic reason when the outcome is not a clean pass. | Should | Testability and auditability; interface defined in Section 6. |
| O4-FR-11 | The required evidence set MUST be derived from the selected-analyst configuration via `ANALYST_NODE_SPECS`. | Should | Mapping source: `tradingagents/graph/analyst_execution.py:20–62`; avoids duplicate selection logic. |
| O4-FR-12 | The checker MUST NOT mutate `final_trade_decision`. When the effective rating is `REVIEW` but the decision body still states a direction (e.g. a `Buy`/`Sell` line), only the authoritative rating label is `REVIEW`; the original body is preserved byte-for-byte, and any surface that shows it MUST label it clearly as unapproved original content (see FR-13). | Must | Source of decision text: `tradingagents/agents/managers/portfolio_manager.py:81–86`; preserves evidence without endorsing it. |
| O4-FR-13 | When the effective rating is `REVIEW` and the original decision body contains a tradeable direction, enabled rating surfaces MUST present the authoritative rating as `REVIEW` and MUST identify any preserved original Buy/Sell body as unapproved original content, never as an approved recommendation. Under v1 buffering, the original body MUST NOT be published as an authoritative result before the gate (per FR-07). The CLI's current review message (`cli/run.py:378–385`) describes only an unreadable rating; it MUST be replaced with a cause-neutral review message so an evidence downgrade or rating conflict is not misreported. Any new display element requires interface approval. | Must | Current CLI review message: `cli/run.py:378–385`; prevents endorsing an unapproved direction. |
| O4-FR-14 | Richer rules (minimum content length, cross-verification of report content, requiring debate histories) are OUT OF SCOPE for O4 v1. | Won't (v1) | Keeps the gate small and reviewable; v1 boundary statement at top of this document. |
| O4-FR-15 | An unknown analyst key, or an unrecognizable required configuration, is a configuration/contract error. The system MUST abort authoritative rating publication, report the error, and MUST NOT (a) silently classify unknown analysts as `not_required`, or (b) present the aborted run as a normally completed `REVIEW` run. If a safe authoritative result cannot be reliably constructed, none is published. | Must | `build_analyst_execution_plan` raises on unknown keys (`tradingagents/graph/analyst_execution.py:55–56`); architecture direction A/C (Decision C). |
| O4-FR-16 | Original-rating precedence and conflict handling: the original rating is `final_rating` when present; only when it is absent does the system fall back to parsing `final_trade_decision`. If both sources clearly provide a rating and disagree, this is a rating-consistency error: the gate MUST downgrade `effective_rating` to `REVIEW` and preserve the conflict reason. An original `REVIEW` is never upgraded. After the gate, `effective_rating` is the single authoritative rating for final return, reporting, persistence, and CLI publication. | Must | `run_rating` precedence (`tradingagents/agents/rating.py:106–112`); architecture direction A/C (Decision D). |

## 3. Non-functional Requirements (NFR)

**Priority column:** MoSCoW, **proposed** pending Member B's confirmation that Schema 1.0.0 accepts a priority on NFR entries. **Invariant representation:** see the note after the invariants table.

| ID | Requirement | Priority (proposed) | Metric / observable condition | Threshold | Verification | Source / rationale |
|---|---|---|---|---|---|---|
| O4-NFR-01 | Checker is a pure function of its inputs (no I/O, no LLM, no clock). | Must (proposed) | No I/O/LLM/clock imports; repeated calls return identical verdicts. | Zero such calls observed. | O4-T-11 (unit) | Determinism requirement O4-FR-08; parallel deterministic-identity precedent `tradingagents/agents/context.py:61–82`. |
| O4-NFR-02 | Checker unit-testable from a plain `dict` state and a selected-analyst set, with no graph/LLM/network. | Must (proposed) | Tests import and run the checker directly, offline. | Zero graph/LLM/network invocations. | O4-T-15 (unit, collection) | Testability of the standalone module proposed in Section 6 (`evidence_gate.py`); supports course offline-test requirement. |
| O4-NFR-03 | Checker adds no external calls; per-run added latency is bounded. | Must (proposed) | Measured added wall time comparing WITH vs WITHOUT the gate, on identical synthetic inputs (complete and missing evidence) with a fixed runner; record p50 and p95. | p95 added latency < bound; bound TBD — Team Approval Required (Member F proposes after a reproducible baseline). | O4-T-16 (benchmark) | Performance concern inherent to adding a per-run step; no shipped threshold exists in the baseline (`pyproject.toml` defines none). |
| O4-NFR-04 | The gate fails closed (O4-INV-03/04) and adds no new runtime dependency. | Must (proposed) | Dependency diff empty; checker-exception case applies the policy. | Zero new dependencies. | O4-T-07 (unit) + dependency review | Safety invariant O4-INV-04; existing `structured.py` graceful-fallback precedent (`tradingagents/agents/structured.py:59–81`); current dependency set in `pyproject.toml:11–31`. |
| O4-NFR-05 | Backward compatible: with the gate not wired into runtime, existing functions behave unchanged; enabled APIs accept only additive parameters. | Should (proposed) | Existing baseline suite passes unchanged; no public signature change in `run_rating`, `record_decision`, `store_decision`, `write_report_tree`. | Zero behavior change and zero signature removal in the existing suite. | O4-T-20 (regression) + signature review (see note) | Public API surface: `tradingagents/agents/rating.py:106–112`, `tradingagents/graph/trading_graph.py:359–371`. |
| O4-NFR-06 | Runtime auditability: the checker MUST return structured evidence results (verdict, effective rating, per-item statuses, diagnostic reason) to its caller at run time (O4-FR-10). These are transient unless persisted; they are NOT recoverable after execution from existing artefacts, because the memory log stores only `[date \| ticker \| rating \| pending]` plus `DECISION:`/`REFLECTION:` blocks (`memory/log.py:56–58`) and the state log stores only `final_rating` (`trading_graph.py:464`) with no evidence-verdict field. Durable audit records therefore require a persistence decision pending team approval (Section 9). | Should (proposed) | Runtime: structured result present in the checker's return value. Durable: effective rating reconstructable from existing artefacts; verdict durability pending approval. | Runtime result: present 100% of invocations. Durable verdict: TBD — Team Approval Required. | O4-T-08 (integration), O4-T-21 (artefact inspection) | Current persistence limits confirmed in `tradingagents/memory/log.py:56–58` (`_parse_entry` fixed fields at `:311–341`) and `tradingagents/graph/trading_graph.py:464`; auditability supports O4-INV-01/03. |
| O4-NFR-07 | Change scope: small new module plus integration points deferred to architecture approval (Section 7). No LangGraph redesign. | Should (proposed) | Change set = new module (+ approved integration points only). | Zero graph redesign; no changes to rating-generation logic. | O4-T-22 (manual scope review) | Design rationale: keep the change within one-week scope and avoid a LangGraph redesign (Section 7). |
| O4-NFR-08 | Output-surface applicability: consistency applies only to enabled surfaces — HTML only when `html=True` (`reporting.py:92`, `:116–123`), CLI message only on CLI path (`cli/run.py:380`), state log always via `record_decision` (`trading_graph.py:362`, `:438–476`), memory log only when `memory_log_path` set (`memory/log.py:44–45`). | Must (proposed) | Compared-surfaces set equals enabled surfaces only. | Exact equality of effective rating across the enabled set. | O4-T-08 (integration) | Surface enablement observed at the cited lines: `tradingagents/reporting.py:92,116–123`; `cli/run.py:380`; `trading_graph.py:362,438–476`; `memory/log.py:44–45`; supports O4-INV-03. |

**Safety invariants**

| ID | Invariant | Priority treatment | Source / rationale |
|---|---|---|---|
| O4-INV-01 | No run whose required evidence is incomplete may publish a tradeable rating on any enabled surface; the published rating MUST be the effective rating. | Invariant — not tradeable against | Safety rule over the recognized failure: empty reports are marked only at prompt time (`tradingagents/agents/context.py:190–201`); no output-level enforcement exists. |
| O4-INV-02 | A pre-existing original `REVIEW` is never upgraded to a tradeable rating. | Invariant — not tradeable against | Existing non-tradeable REVIEW behavior (`tradingagents/agents/rating.py:96–117`, `:106–112`); preserves it. |
| O4-INV-03 | Every enabled rating surface observes the same effective rating; none reads the ungated original rating independently. No raw Portfolio Manager Buy/Sell is published as an approved result before the gate completes. | Invariant — not tradeable against | Multiple independent rating readers observed at `trading_graph.py:370,405,464`, `reporting.py:26`, `report_html.py:251`, `cli/run.py:380`; CLI pre-gate display `cli/run.py:241–340`; A/C Decision A (buffering). |
| O4-INV-04 | On a recoverable internal checker failure, the effective rating MUST be `REVIEW`, a diagnostic reason is preserved, every enabled surface uses that `effective_rating`, and the ungated original rating is never published. This is distinct from a configuration error (O4-FR-15), which aborts publication rather than producing a normal `REVIEW`. | Invariant — not tradeable against | Fail-closed safety; parallels graceful-fallback design (`tradingagents/agents/structured.py:59–81`); A/C Decision B (architecture direction). |
| O4-INV-05 | When `final_rating` and a clearly parsed `final_trade_decision` rating disagree, the effective rating MUST be `REVIEW` with a preserved conflict reason; an original `REVIEW` is never upgraded. | Invariant — not tradeable against | Two rating sources in `run_rating` (`tradingagents/agents/rating.py:106–112`); a wrong direction is worse than none (the rationale recorded at `rating.py:10–13`, issue #1170 comment only); A/C Decision D (architecture direction). |

> **Registry confirmation requested (Member B):** invariants are kept as safety invariants with no MoSCoW priority. Confirm whether Schema 1.0.0 supports an explicit invariant type, or whether invariants should be entered as `Must` requirements with a distinguishing flag. No invariant type is assumed here.

## 4. Fit Criteria

Each criterion is Given/When/Then with an observable pass condition and a mapped verification/test ID. **Executable tests** are marked *unit*, *integration*, *regression*, or *benchmark*. **Manual verification** is marked *manual* and is NOT an automated test.

| ID | Given / When / Then | Pass condition | Verification / Test ID | Verification type |
|---|---|---|---|---|
| O4-FR-01 | Given a run state, When the gate runs, Then a verdict is produced. | Verdict ∈ {valid, review}. | O4-T-01 | Executable (unit) |
| O4-FR-02 | Given all required reports non-empty and original rating `Overweight`, When the gate runs, Then effective == original. | Effective == original == `Overweight`. | O4-T-01, O4-T-09 | Executable (unit) |
| O4-FR-03 | Given all required analysts selected and any required report missing/empty, When the gate runs, Then effective == `REVIEW` and the failing set names exactly that report. | Exact failing set; effective `REVIEW`. | O4-T-02, O4-T-03, O4-T-14, O4-T-17 (parameterized across all four reports), O4-T-24 Case B | Executable (unit) |
| O4-FR-04 | Given a required report with the approved sentinel, When the convention is configured, Then item is `unavailable` and effective == `REVIEW`; When not configured, Then non-empty text is `present`. | Behavior matches configured flag. | O4-T-04 | Executable (unit); depends on unapproved sentinel (Q3) |
| O4-FR-05 | Given all evidence present and original rating `REVIEW`, When the gate runs, Then effective remains `REVIEW`. | Effective == `REVIEW`. | O4-T-06 | Executable (unit) |
| O4-FR-06 | Given selected `{market, news}`, When the gate runs, Then sentiment/fundamentals are `not_required` and cause no downgrade. | Statuses == `not_required`. | O4-T-05, O4-T-13 | Executable (unit) |
| O4-FR-07 | Given original `Buy` but incomplete evidence, When the CLI streams PM messages and report text and enabled surfaces later read the rating, Then no PM Buy is published before the gate, and all authoritative surfaces show effective `REVIEW`. | No pre-gate published rating; final surface set == {`REVIEW`}. | O4-T-08, O4-T-19, O4-T-23 | Executable (integration) |
| O4-FR-08 | Given identical input ×100, When the gate runs, Then verdicts are identical, no I/O. | 100/100 identical. | O4-T-11 | Executable (unit) |
| O4-FR-09 | Given a recoverable checker failure, When applied, Then effective == `REVIEW`, reason preserved, no ungated rating published, all enabled surfaces agree. | Fail-closed observed. | O4-T-07, O4-T-08 | Executable (unit + integration) |
| O4-FR-10 | Given any state, When the checker returns, Then per-item statuses cover every required key, verdict is enumerated, and a reason accompanies non-pass outcomes. | Complete statuses; enumerated verdict; reason on non-pass. | O4-T-12 | Executable (unit) |
| O4-FR-11 | Given selected `{market, news}`, When required items are derived, Then set == {`market_report`, `news_report`}. | Exact set match. | O4-T-05, O4-T-18 | Executable (unit) |
| O4-FR-12 | Given a downgrade with a `Buy` body, When compared with PM output, Then `final_trade_decision` is byte-identical. | Byte equality. | O4-T-10 (unit) | Executable (unit) |
| O4-FR-13 | Given effective `REVIEW` and a `Buy` body, When an enabled surface renders the rating, Then it shows `REVIEW` and labels the preserved `Buy` body unapproved original content. | Surface rating == `REVIEW`; body labelled non-authoritative. | O4-T-19, O4-T-23 (integration); rendered-label asserted offline | Executable (integration) |
| O4-FR-14 | Given v1 scope review, When inspected, Then no length/verification/debate rules exist. | Absent from implementation. | O4-T-22 | Manual scope review (not automated) |
| O4-FR-15 | Given an unknown analyst key or unrecognizable configuration, When the gate runs, Then authoritative publication is aborted with an error and the run is not presented as a normal `REVIEW`. | Error raised; no authoritative rating; not reported as normal REVIEW. | O4-T-18 | Executable (unit + integration) |
| O4-FR-16 | Given (a) both sources agree, Then effective == that rating; (b) `final_rating` absent, Then body parsing supplies the rating; (c) both clear but disagree, Then effective == `REVIEW` with conflict reason; (d) original `REVIEW`, Then stays `REVIEW`. | Precedence and conflict rules hold. | O4-T-25 | Executable (unit) |
| O4-NFR-01 | Given checker code, When inspected and run, Then no I/O/LLM/clock and results deterministic. | Zero such calls; deterministic. | O4-T-11 | Executable (unit) |
| O4-NFR-02 | Given the checker, When imported in a unit test, Then it runs with no graph/LLM/network. | Offline execution succeeds. | O4-T-15 | Executable (unit, collection) |
| O4-NFR-03 | Given repeated evaluations with and without the gate, When timed by Member F, Then p50 and p95 added latency < approved bound. | Measured p95 < TBD — Team Approval Required. | O4-T-16 | Executable (benchmark); threshold pending |
| O4-NFR-04 | Given the change set, When audited, Then no new dependency and fail-closed observed. | Empty dependency diff; O4-T-07 passes. | O4-T-07 | Executable (unit) + dependency review |
| O4-NFR-05 | Given the unchanged baseline, When the existing regression suite runs, Then behavior is unchanged; When enabled APIs are diffed, Then only additive parameters appear. | Existing tests pass unchanged; no removed/renamed public parameter. | O4-T-20 | Executable (regression) + signature review (manual subset) |
| O4-NFR-06 | Given a checker invocation, When it returns, Then structured results (incl. reason) are available at runtime; Given a completed run, When an auditor inspects existing artefacts, Then only the effective rating is reconstructable (verdict durability pending approval). | Runtime result present 100% of invocations; durable verdict TBD — Team Approval Required. | O4-T-08, O4-T-21 | Executable (integration) + artefact inspection |
| O4-NFR-07 | Given the change, When reviewed, Then it is one module plus approved integration points. | Scope matches Section 7; no rating-logic change. | O4-T-22 | Manual scope review (not automated) |
| O4-NFR-08 | Given a disabled surface feature, When consistency is checked, Then only enabled surfaces are compared. | Compared set == enabled set. | O4-T-08 | Executable (integration) |
| O4-INV-01 | Given incomplete required evidence, When enabled surfaces are inspected, Then none shows an approved tradeable rating, including before the gate finishes. | Pre-gate PM text buffered; final enabled ratings all `REVIEW`. | O4-T-02, O4-T-08, O4-T-19, O4-T-23 | Executable (unit/integration) |
| O4-INV-02 | Given original `REVIEW`, When the gate runs, Then never upgraded. | Effective == `REVIEW`. | O4-T-06, O4-T-25 | Executable (unit) |
| O4-INV-03 | Given a downgraded run, When surfaces read the rating, Then all agree and no pre-gate raw Buy/Sell is published. | Equality across enabled surfaces. | O4-T-08, O4-T-23 | Executable (integration) |
| O4-INV-04 | Given a recoverable checker failure, When applied, Then effective == `REVIEW`, reason preserved, surfaces agree, ungated rating unpublished. | Matches fail-closed policy. | O4-T-07, O4-T-08 | Executable (unit/integration) |
| O4-INV-05 | Given disagreeing `final_rating` and parsed body rating, When the gate runs, Then effective == `REVIEW` with conflict reason; original `REVIEW` never upgraded. | Conflict downgrade observed. | O4-T-25 | Executable (unit) |

**Note on O4-NFR-05:** compatibility is verified by running the unchanged existing regression suite against the change with the gate not wired into runtime, plus a signature diff of the public functions. **No new configuration toggle is defined or assumed**; if any integration path requires a toggle, that is an architecture decision pending A/C approval (Section 9 Q4).

## 5. Proposed Test Cases

> **PROPOSED, not executed.** Deterministic and offline unless marked a benchmark or integration activity. Test directory placement pending Member F (Section 7); IDs `O4-T-*` are independent of file layout.

| Test ID | Requirement(s) | Initial state / input | Expected result | Category | Verification |
|---|---|---|---|---|---|
| O4-T-01 | FR-01, FR-02 | All four reports non-empty; original `Overweight`; all selected | Verdict `valid`; effective `Overweight` | Normal | Unit |
| O4-T-02 | FR-03, INV-01 | Parameterized: each of market/sentiment/news/fundamentals report is empty in turn; others present; original `Buy`; all selected | Effective `REVIEW`; failing set == that one report | Negative | Unit |
| O4-T-03 | FR-03 | Parameterized: each required report whitespace-only; plus multi-report-missing case | Those reports `missing`; downgrade; exact failing set | Boundary | Unit |
| O4-T-04 | FR-04 | Required report with approved sentinel; flag on vs off | On → `unavailable`+`REVIEW`; off → `present` | Boundary | Unit |
| O4-T-05 | FR-06, FR-11 | Selected `{market, news}`; sentiment/fundamentals empty | Those `not_required`; no false downgrade | Normal/Boundary | Unit |
| O4-T-06 | FR-05, INV-02 | All evidence present; original `REVIEW` | Remains `REVIEW` | Negative | Unit |
| O4-T-07 | FR-09, INV-04 | Unit: checker raises. Integration: recoverable failure in the wired call path | `REVIEW`, reason preserved, no ungated rating on any enabled surface | Checker failure | Unit + Integration |
| O4-T-08 | FR-07, FR-09, INV-01/03/04, NFR-08 | Downgraded and checker-failure states through real Graph/CLI publication path | Identical `REVIEW` across enabled surfaces only; disabled surfaces not assumed enabled | Integration | Integration (offline Graph/CLI) |
| O4-T-09 | FR-02 | All evidence present; original `Sell` | Effective `Sell`; no spurious downgrade | Normal | Unit |
| O4-T-10 | FR-12 | Downgraded run with a `Buy` body | Effective `REVIEW`; checker leaves `final_trade_decision` byte-identical (label rendering verified by T-19/T-23) | Negative | Unit |
| O4-T-11 | FR-08, NFR-01 | Same input ×100 | Identical verdicts; no I/O | Boundary | Unit |
| O4-T-12 | FR-10 | Any state, incl. non-pass | Complete per-item statuses; enumerated verdict; reason on non-pass | Normal | Unit |
| O4-T-13 | FR-06 | Selected `{market}` only; market present | Valid; others `not_required` | Boundary | Unit |
| O4-T-14 | FR-03, FR-06 | Parameterized: selected `{market}` only, market missing/empty; and multi-select with one required missing | Downgrade `REVIEW`; no false failure for unselected | Negative | Unit |
| O4-T-15 | NFR-02 | Import checker directly | Runs with no graph/LLM/network | Normal | Unit (collection) |
| O4-T-16 | NFR-03 | Benchmark WITH vs WITHOUT gate; complete and missing-evidence inputs | p50/p95 added latency recorded; < approved bound | Benchmark | Benchmark (Member F) |
| O4-T-17 | FR-03 | Parameterized: each required report key entirely absent from the state | Each classified `missing`; exact failing set; `REVIEW` | Negative | Unit |
| O4-T-18 | FR-11, FR-15 | Unit: unknown key raises. Integration: unknown key through wired path | `ValueError`; authoritative publication aborted; not presented as normal `REVIEW` | Negative | Unit + Integration |
| O4-T-19 | FR-07, FR-12, FR-13, INV-01 | Original body contains `Buy`; required evidence incomplete; real Graph/CLI path | Pre-gate no published Buy; post-gate `REVIEW` on enabled surfaces; body preserved and labelled unapproved | Negative | Unit + Integration |
| O4-T-20 | NFR-05 | Existing suite run with gate not wired into runtime | Current behavior unchanged; existing tests pass | Regression / Backward compatibility | Regression (Member F) |
| O4-T-21 | NFR-06 | Completed downgraded run; inspect existing artefacts | Runtime structured result available at capture point; effective rating reconstructable; durability documented pending | Auditability | Artefact inspection |
| O4-T-22 | NFR-07, FR-14 | Change-set and implementation review | One new module + approved integration points; no rating-logic change; no out-of-scope rules | Manual scope review (not an automated test) | Manual review |
| O4-T-23 | FR-07, FR-13, INV-01/03 | Fake CLI stream emits a PM `Buy` body before the gate sees a missing required report; real CLI entry point | Before gate, PM message/report text buffered; no published Buy; after gate, enabled surfaces `REVIEW`; preserved body non-authoritative | Negative integration | Integration (offline CLI) |
| O4-T-24 | FR-03, O5 boundary | Case A: O5 filtered-empty but selected News Analyst `news_report` non-empty. Case B: News Analyst selected and `news_report` missing/empty | A: no downgrade from filtered-empty (filtered-empty is a status, not a missing report). B: `REVIEW` with exact failing set == {`news_report`} | Boundary | Unit |
| O4-T-25 | FR-16, INV-02, INV-05 | (a) `final_rating` and parsed body agree; (b) `final_rating` absent, body supplies rating; (c) both clear but disagree; (d) original `REVIEW` | (a) agree preserved; (b) body rating used; (c) `REVIEW` with conflict reason; (d) stays `REVIEW` | Negative | Unit |

## 6. Proposed Module Interface

**Proposed new module:** `tradingagents/agents/evidence_gate.py` (path pending Member C).

**Inputs**
- `state: Mapping[str, Any]` — read fields: `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`, `final_rating`, `final_trade_decision` (`tradingagents/agents/state.py:52–70`). A required key absent from the mapping is classified `missing` (O4-T-17).
- `selected_analysts: Iterable[str]` — keys via `ANALYST_NODE_SPECS` (`tradingagents/graph/analyst_execution.py:20–46`); source is `TradingAgentsGraph.selected_analysts` (`tradingagents/graph/trading_graph.py:109`). An unknown key is a configuration error (O4-FR-15).
- Optional sentinel-convention configuration (O4-FR-04; pending approval).

**Outputs** (small dataclass or dict; returned to the caller at run time, transient unless persisted)
- `verdict`: `valid` | `review`
- `effective_rating`: rating to publish (`REVIEW` when not a clean pass)
- `items`: list of `{key, status}` with status ∈ `present`/`missing`/`unavailable`/`not_required`
- `reason`: diagnostic reason; `""` when valid, set for missing evidence, checker failure, or rating conflict
- `error_kind`: `none` | `evidence` | `checker_failure` | `rating_conflict` (configuration errors raise instead of returning)

**Error handling**
- Unknown analyst key / unrecognizable configuration → raise `ValueError` (consistent with `tradingagents/graph/analyst_execution.py:55–56`); publication is aborted, not turned into a normal `REVIEW` (O4-T-18). This is a configuration/contract error, distinct from a recoverable checker failure.
- Recoverable internal failure → fail closed: return `REVIEW` with reason and `error_kind="checker_failure"`; no ungated rating published (O4-T-07).
- Rating conflict → return `REVIEW` with `error_kind="rating_conflict"` and reason (O4-T-25).

**Integration is a separate architecture decision** (Section 7); this interface assumes no change to `run_rating`, the graph, or persistence. Any durable audit record requires a persistence decision pending approval (O4-NFR-06; Section 9).

## 7. Expected Code Changes

**Files Member D may modify independently (proposed, subject to approval):**
- `tradingagents/agents/evidence_gate.py` — proposed new checker module.
- `test/offline/test_evidence_gate.py` — proposed new offline tests (placement confirmed by Member F).

**Shared files requiring Member A or C approval (NOT assumed modifiable by Member D):**
- `tradingagents/graph/trading_graph.py` — integration before `record_decision`/`_run_graph` return (`:359–405`).
- `tradingagents/agents/rating.py` — routing `run_rating` through the gate affects all consumers.
- `tradingagents/agents/state.py` — only if Member C adds a gated/explanation field.
- `tradingagents/memory/log.py` — only if a durable verdict field is approved (today none exists, `:56–58`).
- `tradingagents/reporting.py` (`:26`), `tradingagents/report_html.py` (`:251`), `cli/run.py` (`:380`) — explanation/consistency surfacing.
- `cli/run.py` (`:241–340`) — stream-time PM text (report section at `:330–334` and message stream) enters the display before `record_decision`; under the agreed buffering direction this text must be held until gating. Exact integration location and shared-file scope still pending A/C.

**Architecture directions already agreed by A/C (not formal requirements approval, not a confirmed integration point):**
- **Decision A — CLI buffering** for v1 (provisional labelling rejected/alternative). See O4-FR-07, FR-13, INV-03.
- **Decision B — recoverable checker failure** fails closed to `REVIEW` with preserved reason. See O4-FR-09, INV-04.
- **Decision C — unknown analyst / unrecognizable configuration** aborts publication; not a normal `REVIEW`. See O4-FR-15.
- **Decision D — rating precedence** (`final_rating` first, else parsed body) and conflict-to-`REVIEW`. See O4-FR-16, INV-05.

**Still requiring A/C confirmation:** the exact integration location and shared-file modification scope after call-chain review (Section 9 Q4).

**Test directory layout and CI discovery — Member F confirmed `test/offline/`.** The course spec requires `test/offline/` and `test/live/`; offline Graph/CLI tests may use the `integration` marker and therefore need an explicit CI step that includes them (the default `-m "not integration"` filter in `pyproject.toml:60` would exclude them). See the test plan §7.

## 8. Dependencies and Conflicts

- **Shared modules:** `rating.py`, `state.py`, `graph/trading_graph.py`, `memory/log.py`, `reporting.py`, `report_html.py`, `cli/run.py`, `graph/analyst_execution.py`.
- **Member B (requirements):** confirm FR/NFR/INV IDs, MoSCoW, fit criteria, proposed NFR priorities, and invariant representation against Schema 1.0.0; this Markdown is **not** the official `requirements.yaml` — B owns the registry.
- **Member C (architecture/interfaces):** confirm integration location and shared-file scope (Decisions A–D give direction, not a confirmed integration point); approve module boundary and any new persistence/display fields.
- **Member A (workflow integration):** approve selection flow into the gate and cross-surface consistency; may own the integration edit.
- **Member F (testing/CI):** approve proposed tests, `test/offline/` placement, CI step including `integration`-marked offline tests, set the O4-NFR-03 threshold after baseline, benchmark O4-T-16, run the backward-compatibility suite (O4-T-20).
- **Potential conflicts:** edits to `rating.py`/`trading_graph.py`; existing tests asserting current behavior must keep passing (`tests/test_graph_end_to_end.py:138`, `tests/test_reporting.py:158–163`).

## 9. Open Questions

1. **Which evidence is mandatory?** All selected reports, or a fixed minimum subset? TBD — Team Approval Required (B, A).
2. **Disabled analysts:** Proposed `not_required` (FR-06). Confirm (B, C).
3. **Explicit unavailability:** The router has `NO_DATA_AVAILABLE` (`tradingagents/dataflows/router.py:185–198`), but there is no approved rule making a whole analyst report unavailable whenever that text appears inside it. Proposed v1: non-empty = structurally `present`; do not infer data validity. Defer whole-report unavailability until D/C approve a precise status interface. O1's single-SMA insufficiency alone does not trigger `REVIEW`.
4. **Integration location and shared-file scope:** Decisions A–D confirm direction; the exact integration point (e.g. in `run_rating` vs post-run in `trading_graph.py`) and the list of shared files to modify still require A/C confirmation after call-chain review. A post-run-only edit cannot retroactively remove an earlier published `Buy`; buffering must cover the CLI report section (`cli/run.py:330–334`) and message stream. TBD — Team Approval Required (A, C).
5. **Durable persistence of the evidence verdict/explanation** requires a memory-log/state-log interface change; runtime results are transient and not recoverable after execution unless persisted. Deferred from v1. TBD — Team Approval Required (A, C).
6. **Test directory layout and CI discovery** — `test/offline/` confirmed by F; the explicit CI step including `integration`-marked offline tests remains to be wired. TBD — Team Approval Required (F).
7. **Approvers:** Proposed — F approves the test plan (subject to final approval-authority confirmation), C/A confirm architecture and integration, B checks registry and traceability. TBD — Team Approval Required.
8. **Schema 1.0.0 fit for priorities and invariants:** Proposed NFR MoSCoW priorities and the invariant representation require Member B's confirmation before registry ingestion. TBD — Team Approval Required (B).

**Resolved by A/C architecture direction (no longer open; still not formal requirements approval):** CLI buffering for v1 (was Q4); recoverable checker-failure fail-closed policy (was Q5); unknown-analyst configuration abort behavior; rating precedence and conflict-to-`REVIEW`.

## 10. Review Status

Status: Draft
Reviewer: Pending
Review date: Pending
Approval evidence: Not yet available
Draft revision: O4-REQ-r3 (proposed; distinct from Registry/Schema 1.0.0)
