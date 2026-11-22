# ADR 001 — Incremental integration of O1–O6 into one CLI analysis path

**Status:** Accepted as description of the current architecture. **Not** a
record of a historical architecture-review event.
**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
**Owner:** C
**Date of this record:** closeout stage, written from existing records. No
historical date is backfilled.

---

## 0. How to read this ADR

This document was written **after** the work, from records that already existed.
Three things it deliberately does **not** do:

1. It does not invent a date on which an architecture decision meeting occurred.
2. It does not claim that an architecture approval was granted that is not
   recorded anywhere.
3. It does not reconstruct a candidate-evaluation process that the team did not
   document while it was happening.

Where this ADR describes *alternatives considered*, it distinguishes:

- **historically considered** — the option is named in an existing plan,
  requirement or PR decision, and the source is cited; and
- **analytical comparison added at closeout** — the option was not on the record
  at the time, but is a reasonable alternative that a reader would otherwise
  expect to see discussed. These are labelled **[closeout analysis]**.

---

## 1. Context

The application already existed as a working multi-agent analysis CLI before the
six optimisation areas were added. The Registry
([`docs/req/requirements.yaml`](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml)) records
that the team chose to add O1–O6 to that existing system rather than to
re-architect it:

- `development_contract.integration_owner` names C as the sole editor of
  `cli/run.py`, `trading_graph.py` and rating-output wiring "for O2/O4/O6".
- `development_contract.approval_roles` assigns a separate test-plan reviewer
  per area (F for O1/O3/O4/O5, A for O2/O6), which assumes areas proceed
  independently.
- The Registry `status` is `"selected_for_development; test and agent-plan
  approvals still required"`, and `authority` states the file "does not claim
  retroactive approval by B-F".

The forcing problem: several requirements are *safety-relevant boundaries on
model output*, and the model output is produced by a shared orchestration path.
Adding them one by one to a shared file risks the classic outcome — each area
looks correct alone, and the combination publishes something none of them
approved.

---

## 2. The decision

**Integrate O1–O6 incrementally into the single existing CLI analysis path, with
C as sole editor of the shared orchestration files, and with each area's
deterministic boundary enforced at its own code path.**

Concretely, the decision has five parts:

1. **One orchestration entry.** `run_analysis` in `cli/run.py` remains the only
   place where a run is sequenced. No area gets its own entry point.
2. **Areas attach at their own seam.** O1 in the Yahoo market adapter, O3 in the
   condensation module used to build one analyst's input, O5 in the news adapter
   plus a pure selector, O2 in run-directory reservation and manifest
   finalisation, O4 in a pure gate function, O6 in the stats handler and the
   terminal summary.
3. **Authoritative outputs are gated, advisory outputs are not.** Only the
   effective rating, the guarded SMA values and the news selection are treated
   as authoritative; analysis prose, debate text and O6 telemetry remain
   advisory (see blueprint §5.2).
4. **Degradation is bounded and named.** A soft failure logs a named diagnostic
   and serves the honest result; it does not fabricate an empty or no-news
   outcome (`development_contract.o5.sink_failure`, `…invariant_failure`).
5. **Governance is machine-checked where it can be.** Registry validation,
   approval gates, AI-use evidence and workflow-permission guards run in CI.

---

## 3. Alternatives considered

### 3.1 Historically considered (cited)

| # | Alternative | Where it is on the record | Why it was not chosen |
|---|---|---|---|
| H1 | **Per-area separate pipelines** — each optimisation runnable on its own | `development_contract.approval_roles` gives each area its own test-plan reviewer; the Registry `status` treats approvals as per-area. This structure implies areas could be developed in parallel and separately. | A user runs one analysis, not six. Separate pipelines would leave no single place where the effective rating is decided, which is exactly what `O4-INV-03` forbids. |
| H2 | **Out-of-process wrapper** — an external supervisor invoking the CLI | **[closeout analysis]** — not on the record. | Would place the gate outside the code that publishes, so a second caller (library use, tests) could bypass it. |
| H3 | **Defer O4 until after O1/O3/O5 land** | The Registry orders areas O1…O6, and `approval_roles` grants O4 to F independently. | O4's invariant ("no surface reads the ungated rating") constrains *where* the other areas may publish. Landing them first and adding the gate later would have required re-opening every publication surface. |
| H4 | **Public sink/factory interface for O5 evidence** | Explicitly rejected in the S2–S4 test-plan review (PR #3 review `5986202826`, §2): "I5b 仍是 S5 生产 sink 构造失败，本批不新增公共 sink/factory 接口". | A public factory becomes an API the project must then keep compatible. The chosen form is a private scope manager. |
| H5 | **Treat the S5 evidence sink as a hard requirement** | `development_contract.o5.sink_failure` states the opposite: "log SINK_FAILED and continue serving the honest result". | Making persistence mandatory would let a disk problem destroy a valid analysis. |
| H6 | **Bound the AI context by token count** | `development_contract.o3.token_claim` and `REQ-O3-07` restrict token claims to measured tokenizer counts or observed provider usage. | See §4.2 — the implemented mechanism is a **character** budget, not a token cap. |

### 3.2 Analytical comparison added at closeout

| # | Alternative | Assessment |
|---|---|---|
| A1 | **Rewrite the graph** so each optimisation is its own node | Would make attachment points explicit and testable in isolation, but replaces the existing baseline, which `REQ-GOV-04` and the course's "extends the existing baseline, never replaces it" rule both discourage. **[closeout analysis]** |
| A2 | **Make everything authoritative** (gate every analyst report) | Would require a definition of "complete evidence" for free text, which does not exist and cannot be deterministically checked. `development_contract.o4.report_presence` deliberately accepts non-empty text even when it mentions unavailable data. **[closeout analysis]** |
| A3 | **Make everything advisory** (gate nothing) | Contradicts `O4-INV-01` directly. **[closeout analysis]** |

---

## 4. The AI component's layered context design

The course requires the ADR to present the layered context the AI receives on
every turn, the assembly pipeline, the token-budget cap with its compaction
threshold, and the policy for re-injecting critical constraints after
compaction.

**This section separates two different things**, which the course wording tends
to conflate:

- **Application runtime LLM context** — what the *product's* analysts send to a
  model on each turn (§4.2–4.5).
- **OpenCode development context** — what the *coding agent* receives while
  building the system (§4.6).

### 4.1 The distinction that matters for honesty

The implemented artefact in this repository addresses the **runtime** side, and
it does so with a **character budget**. No token-budget cap with a compaction
threshold is implemented in the product. Where the course asks for a token cap,
this ADR states what exists and names the gap rather than asserting a mechanism
that is not there.

### 4.2 Runtime context: what actually exists

The only context-assembly mechanism implemented in the product is O3 input
condensation, in `tradingagents/agents/analysts/condensation.py`.

**Its unit is characters, not tokens.**

- Defaults (`development_contract.o3`): total 24 000 characters; news 12 000;
  StockTwits 6 000; Reddit 6 000.
- `validate_caps(config)` **rejects** invalid caps or a sum exceeding the total,
  raising `ValueError`.
- `condense_source(...)` raises `CondensationError` for a non-string block or a
  non-positive budget.
- Token counts are **optional and estimated**: `count_tokens` is a caller-supplied
  callable; when absent, `tokens_before`/`tokens_after` are `None`, and the
  report says so. `REQ-O3-07` permits a token-reduction claim only when measured
  by a labelled offline tokenizer or observed provider usage.

**Assembly pipeline, in the order `condense_source` executes it:**

| Step | What happens | Code |
|---|---|---|
| 1. Validate | Type and budget checks; a non-positive or non-int budget raises | `condense_source` prologue |
| 2. Protect | An empty block returns unchanged; a recognised placeholder is kept verbatim and, if it exceeds the cap, raises with `budget_exception=True` | `_is_placeholder` |
| 3. Parse | Source-specific structure recovered, with a count of parse fallbacks | `parse_source`, `_parse_news`, `_parse_stocktwits`, `_parse_reddit` |
| 4. Rank | Items ordered by identity terms and ticker relevance | `_rank` |
| 5. Deduplicate | Exact duplicates collapse with counts; near-duplicates merged at a Jaccard threshold (default 0.8), first wins | `_dedupe`, `_matchable_title` |
| 6. Fit | Items admitted until the per-source cap; oversized single items truncated or dropped | `_fit_flat`, `_fit_reddit`, `_truncate_news` |
| 7. Report | Counts-only `CondensationReport`; stable non-secret identifiers | `CondensationReport`, `safe_id` |

**Ordering constraint that the code enforces:** deduplicate **before** fitting,
and rank **before** truncation. Fitting first would spend budget on content that
is later discarded as a duplicate, producing a smaller result than the budget
allows. This ordering is the subject of `T-N3` and `T15`-adjacent cases.

### 4.3 Budget overflow and protected content

`development_contract.o3.budget_exception` is precise: when a protected block
exceeds its cap, the system **uses the original affected block**, records
`budget_exception`, and **excludes that block from budget-pass calculations**.
A protected-content overflow therefore must never be reported as a budget pass.
`condense_source` implements this by raising `CondensationError(budget_exception=True)`.

### 4.4 What is *not* implemented

| Course asks for | Status here |
|---|---|
| Token-budget cap | **Not implemented as tokens.** A character budget exists. |
| Compaction threshold | **Not implemented.** There is no summarisation/compaction step and no threshold that triggers one. |
| Re-injection of critical constraints after compaction | **Not applicable** — without compaction there is no post-compaction state to re-inject into. The protected-placeholder rule in step 2 is the nearest implemented analogue: a recognised placeholder is preserved verbatim rather than condensed. |
| Resumable conversation state inside the LLM context | **Not implemented as context assembly.** Resumability is handled by the graph checkpointer (§ blueprint 6.3), which persists workflow state, not a model conversation window. |
| Retrieved knowledge layer | **Not implemented.** Analysts receive tool results and the condensed source blocks; there is no retrieval index. |

**These are evidence gaps, not design secrets.** They are listed so that a
reader does not infer a token cap from the presence of a character budget, and
does not infer compaction from the presence of the word "condense": O3
*condenses input text by structural selection*, which is not LLM summarisation.

### 4.5 Where the runtime context is assembled in the run

The Sentiment Analyst's input is the only place O3 applies. The other three
analysts receive their tool outputs directly. This means the runtime context is
**per-analyst and per-turn**, and the four legs are assembled independently and
in parallel — again, not a single serial pipeline.

Critical-constraint protection in practice: analyst prompt construction includes
identity, date and safety text, and a test asserts the prompt keeps those
(`test_T_N5_node_prompt_keeps_identity_date_and_safety_text` in
`test/offline/test_input_condensation.py`). That is the mechanism that survives
condensation; it is not a general post-compaction re-injection policy.

### 4.6 OpenCode development context

Separately, the *coding agent* that built this system received context governed
by project instructions. At the baseline SHA the project-level entry files do
not exist:

- `AGENTS.md` — absent
- `Prompt.md` — absent
- `.opencode/rules.md`, `.opencode/permissions.jsonc` — absent (`.opencode/` is empty)
- `.agent/rules.md` — absent (`.agent/` is empty)

What did exist and was used in practice: the Registry, the per-area plans under
`docs/req/reviews/`, the test-approval records under `docs/test-approvals/`, and
PR review decisions. PR records show reviewers requiring agents to state the
baseline SHA, the approved file list, and to stop outside scope — for example
PR #3 comment `6943145906`: "在会话里写清基线 SHA、批准链接、允许修改的文件和超范围时停止".

**No layered context structure for the development agent is implemented as a
file artefact.** It is therefore not claimed here. This is a D3 deliverable gap
(see permission-model §7).

---

## 5. Consequences

### 5.1 Positive

- One place decides what may be published, satisfying `O4-INV-03` structurally.
- Each area is testable offline without the CLI, because the seams are pure
  functions (`select_macro_news`, `check_evidence`, `condense_source`).
- Degradation is uniform: soft failures name themselves and never fabricate.

### 5.2 Negative / costs

| Cost | Consequence |
|---|---|
| `cli/run.py` is a large shared file with one owner | C becomes a bottleneck; every area's integration waits on one person |
| The O5 scope wraps ~370 lines of `run_analysis` | Reviewers see a mostly-indented diff; the substantive change is two lines |
| Gate-before-publication requires buffering PM text | The live view holds back a decision it already has, which is deliberate but looks like latency |
| Character budgets are not token budgets | Cost cannot be predicted from configuration; `REQ-O3-07` forbids the inference |
| Governance files absent | Course D3 is unmet; process rules rely on human conformance. The CI gates themselves are implemented and have recorded real blocking evidence — see [`../architecture-blueprint.md`](../architecture-blueprint.md) §8.4 and [`../trace-matrix.md`](../trace-matrix.md) §GOV; what is absent is the *coding-agent permission/governance file set*, not the gates. |

### 5.3 Neutral / follow-on

- Because O5 evidence is soft-fail, a run can complete with no JSONL. Consumers
  must not treat a missing file as "no events occurred".
- Because two CI jobs are pull-request-only, a main-commit run shows them as
  `skipped`; this is expected, not a hidden failure.

### 5.4 State of the S5 outcome on the pinned baseline

This ADR's alternatives H4 and H5 concern the O5 evidence sink. Their outcome is
settled at the pinned baseline `252fe311d8d1483b5713de69b04ce2769c33f1dd`:

- The private scope manager (`o5_evidence_run`) **is on `main`**, brought in by
  E's commit `483e1f6` and C's integration `c1fa362`, merged through PR #40 on
  `2026-11-22T05:17:25Z` after the approval-binding PR #42 merged on
  `2026-11-22T04:57:23Z`.
- An earlier observation that PR #40's `test approval` job was red (missing
  approval records) was correct **at that time** and was closed by #42 before
  #40 merged. Statements that S5 is unmerged or that the approval red light is
  still open do not apply to this baseline.
- That merge does **not** establish that the O5 requirements are verified; the
  evidence status is recorded in [`../trace-matrix.md`](../trace-matrix.md) and
  is not restated here.

**S6 / T17 status for this ADR:** S6 is **stopped and its acceptance is not
completed**. `REQ-O5-10` is not accepted as satisfied, no performance threshold
is met, and this ADR does not claim, restore or imply any T17 measurement. The
§4.4 gap table (no token cap, no compaction) is independent of S6 and unchanged.

---

## 6. Conditions that would reopen this decision

| # | Condition | What would change |
|---|---|---|
| R1 | A second caller needs the gate (library use, an API server) | The gate would have to move out of `cli/run.py` into the graph or a shared service, and `O4-INV-03` would need re-verification on every new surface |
| R2 | The four analysts stop being parallel | The O5 `ContextVar` propagation assumption and the checkpoint `analysts=parallel` key both change |
| R3 | Token-level budgeting becomes a requirement | O3 would need a real tokenizer path and a measured provider-usage path; the character budget would become a secondary cap |
| R4 | A production monitor is required for a business invariant | Currently no invariant is monitored at runtime; adding one changes the observability section of the blueprint |
| R5 | `AGENTS.md` / `.opencode` / `.agent` are authored | §7 of the blueprint moves those rules from "document rule" to "machine-enforced" |
| R6 | S6 is restarted | `REQ-O5-10` re-enters scope with a measured T17 result; this ADR's §4.4 gap table is unaffected but the blueprint §9.3 changes |
| R7 | Persistence becomes mandatory for O5 | Contradicts `development_contract.o5.sink_failure`; would need a Registry change, not just code |

---

## 7. What this ADR does not establish

- It does **not** establish that an architecture review occurred on a given date.
- It does **not** establish that the alternatives in §3.1 were evaluated and
  scored; the sources show them being *decided against*, not compared.
- It does **not** establish that any requirement is verified. Verification
  status lives in the trace matrix and in CI results.
- It does **not** claim the course's token-budget/compaction requirements are
  met; §4.4 names them as gaps.
