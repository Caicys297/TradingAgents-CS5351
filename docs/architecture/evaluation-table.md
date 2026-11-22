# Candidate Evaluation Table

**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
**Owner:** C

---

## 0. What this table can honestly claim

The course asks for "the comparison that justifies the chosen architecture". This
table gives that comparison **and** states, per row, what kind of evidence stands
behind it.

**No scores, latencies, costs or benefits are invented.** Where a measurement
does not exist, the cell says so. A fabricated number in this table would be the
single easiest way to make the whole architecture document untrustworthy.

Two categories are kept apart, as requested:

- **H — historically considered**: the option appears in an existing plan,
  requirement text, PR decision or review. The source is cited.
- **A — closeout analysis**: the option was not on the record at the time. It is a
  reasonable alternative a reader would expect to see, assessed at closeout from
  the code as it stands.

---

## 1. Evidence key

| Code | Meaning |
|---|---|
| **E-record** | A cited PR comment, review, plan or Registry field states the position |
| **E-code** | A cited function's behaviour at the baseline SHA supports the position |
| **E-none** | No measurement or record exists; the cell states that |

---

## 2. The decision being justified

**Chosen option:** integrate O1–O6 incrementally into the single existing CLI
analysis path, with C as sole integrator of the shared files and each area's
deterministic boundary enforced at its own seam. (Full statement in
[`adr/001-incremental-integration.md`](adr/001-incremental-integration.md) §2.)

---

## 3. Candidate comparison

### 3.1 Integration shape

| # | Candidate | Class | Advantages claimed | Costs | Why not chosen | Evidence |
|---|---|---|---|---|---|---|
| **C1** | **Incremental attachment to the existing pipeline** *(chosen)* | — | One publication point makes `O4-INV-03` structurally satisfiable; each area stays offline-testable; the existing baseline is extended, not replaced | `cli/run.py` becomes a large single-owner file; the O5 scope indents ~370 lines | — | E-record: `integration_owner`; E-code: `run_analysis` |
| C2 | Per-area standalone pipelines | H | Each area could be developed and shipped independently; matches the per-area approval structure | Six publication points; no single place where the effective rating is decided | Contradicts `O4-INV-03` | E-record: `approval_roles` implies per-area work; ADR §3.1 H1 |
| C3 | Out-of-process wrapper invoking the CLI | A | Gate cannot be bypassed by in-process callers | The gate sits outside the code that publishes, so a second caller bypasses it | Would move the safety boundary away from the publication site | E-code: gate applied inline in `cli/run.py` |
| C4 | Defer O4 until O1/O3/O5 land | A | Lets the selector and adapter stabilise first | O4 constrains *where* others may publish; retrofitting means re-opening every surface | Ordering risk | E-record: `approval_roles` grants O4 to F independently of the others |
| C5 | Rewrite the graph so each optimisation is a node | A | Explicit attachment points; isolation for free | Replaces the existing baseline | Course and `REQ-GOV-04` both favour extending the baseline | E-none (no record of this option being evaluated) |

### 3.2 Evidence persistence (O5 sink)

| # | Candidate | Class | Advantages | Costs | Outcome | Evidence |
|---|---|---|---|---|---|---|
| S1 | **Private scope manager writing JSONL into the O2 run directory** *(chosen)* | — | No new public API; evidence lands beside the manifest; failure is soft | Not readable by any product code; a missing file is ambiguous | Chosen | E-code: `o5_evidence_run`, `_JsonlEvidenceSink` |
| S2 | Public sink/factory interface | H | Reusable by other consumers | Becomes an API the project must keep compatible | **Explicitly rejected** for this batch | E-record: PR #3 review `5986202826` §2 — "本批不新增公共 sink/factory 接口" |
| S3 | Make persistence mandatory | H | Strong provenance guarantee | A disk problem would destroy a valid analysis | Rejected by contract | E-record: `development_contract.o5.sink_failure` |
| S4 | Write evidence to a separate `logs/` tree | A | Independent of run directories | Loses the run-dir association the manifest relies on | Not pursued | E-record: `evidence_path` fixes "same O2 run directory" |

### 3.3 Input budgeting (O3)

| # | Candidate | Class | Advantages | Costs | Outcome | Evidence |
|---|---|---|---|---|---|---|
| B1 | **Character budget with structural selection** *(chosen)* | — | Deterministic, offline, no tokenizer dependency, no cost | Not a token cap; cannot predict provider cost | Chosen | E-code: `condense_source`; E-record: `development_contract.o3.total_chars` |
| B2 | Token budget with a mandatory tokenizer | A | Predictable model cost | Adds a model-vocabulary dependency; still an estimate unless provider usage is observed | Not chosen; `REQ-O3-07` restricts what a token claim may assert | E-record: `development_contract.o3.token_claim` |
| B3 | LLM summarisation (compaction) | A | Adaptive; handles prose | Non-deterministic, extra cost, harder to test offline | Not implemented | E-none — no compaction exists (ADR §4.4) |
| B4 | No budgeting | A | Simplest | Input grows with fetched volume; the model may silently truncate | Rejected implicitly by `O3-FR-04` existing | E-record: `O3-FR-04` |
| B5 | Fit-then-dedupe ordering | A | Simpler loop | Spends budget on content later discarded | Not chosen; rank→dedupe→fit ordering implemented and tested | E-code: assembly order in `condense_source`; E-record: `T-N3` |

### 3.4 Rating authority (O4)

| # | Candidate | Class | Advantages | Costs | Outcome | Evidence |
|---|---|---|---|---|---|---|
| G1 | **Single deterministic gate over analyst evidence** *(chosen)* | — | Pure, testable, one decision point; preserves `final_trade_decision` bytes | Only checks report presence, not report quality | Chosen | E-code: `check_evidence` |
| G2 | Gate inside the graph | A | Harder for a caller to bypass | Moves the boundary away from publication; complicates resume | Not chosen | E-code: gate applied in `cli/run.py` before publication |
| G3 | LLM self-review of evidence | A | Could judge evidence quality, not just presence | Non-deterministic; a model cannot be the authority on its own output | Rejected in principle by the course's safety boundary and `O4-INV-01` | E-none |
| G4 | Publish both ratings (gated + original) | A | Maximum transparency | Puts an ungated Buy/Sell on a surface | Forbidden | E-record: `O4-INV-03` |
| G5 | Whole-report sentinel for unavailable data | H | Detects "report says unavailable" textually | Fragile string matching over free text | Deferred; v1 has none | E-record: `development_contract.o4.report_presence` — "no whole-report sentinel in v1" |

### 3.5 Per-Analyst statistics (O6)

| # | Candidate | Class | Advantages | Costs | Outcome | Evidence |
|---|---|---|---|---|---|---|
| M1 | **Identity from graph-config metadata at the subgraph boundary** *(chosen)* | — | Uses declared identity; no inference | Requires the boundary to carry the key | Chosen | E-record: `development_contract.o6.identity` |
| M2 | Infer identity from callback order or node name | H | Needs no metadata plumbing | Wrong under parallelism | Explicitly forbidden | E-record: same field — "never infer identity from callback order or node name" |
| M3 | Global counters only (no per-Analyst rows) | A | Trivial | Cannot show per-analyst cost | Rejected by O6's purpose | E-record: `O6-FR-*` |
| M4 | Persist per-run statistics to disk | A | Cross-run trending | Adds a new artefact with retention/privacy implications | Not implemented | E-code: summary is terminal-only |

### 3.6 Evidence format for O5 events

| # | Candidate | Class | Advantages | Costs | Outcome | Evidence |
|---|---|---|---|---|---|---|
| F1 | **JSONL, one event per line, per-run file** *(chosen)* | — | Append-friendly; partial-write rollback is natural; line-oriented parsing | Not readable by product code | Chosen | E-code: `emit` + `locked` + truncate-to-offset |
| F2 | JSON array per run | A | One valid document | A partial write corrupts the whole file | Not chosen | E-code: line append with rollback |
| F3 | Database | A | Queryable | New dependency and schema migration burden | Not chosen | E-none |
| F4 | Structured logging to the main logger | A | Free | Mixes diagnostic with product output; cannot be rolled back | Not chosen | E-record: independent logger `tradingagents.o5.evidence` |

---

## 4. What is *not* measured

State plainly, so the table is not read as a quantitative study:

| Dimension | Status |
|---|---|
| Latency of the gate | Not measured. `O4-NFR-03` requires "bounded latency without external calls"; `O4-T-16` is the verification node, but no timing result is recorded in this document |
| Latency of the selector | **Not measured.** `REQ-O5-10` / `T17` was not accepted: **S6 was stopped before any T17 result was accepted**, so no threshold is met. Ordinary selector tests are *correctness* evidence, not performance evidence |
| Cost of condensation | Not measured. Character budgets exist; provider-usage reductions were not observed |
| Token savings | **Not claimed.** `REQ-O3-07` forbids it without a labelled tokenizer count or observed provider usage |
| Defect density per option | Not recorded |
| Maintenance cost of `cli/run.py` | Not measured |
| Bandit/regret of ordering choices (e.g. fit-then-dedupe) | Not measured; the ordering argument is structural, not empirical |

### 4.1 What *is* on the record (and what it is not)

The repository does hold evidence that some CI gates blocked real changes — PR
#41 **E2** (Schema fault; the four test matrices failed together while BLOCKED)
and **E4/E5** (repair, green, recovered; [run 44998474208](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44998474208)
at `9462d6c1`, 17/17), plus the #37 approval-closure pass
([run 44979161445](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44979161445)
at `1c0b740`).

That evidence is about **process gates**, not about the architecture options
compared in §3. It does not add a measured advantage to any candidate row, and
it is not used here to justify a choice. Its own limits are preserved in
[`architecture-blueprint.md`](architecture-blueprint.md) §8.4 (E3 not executed,
no independent administrator API read-back, E2 coupling, semantic independent
blocking unverified).

**S6:** development is stopped and acceptance is not completed; no T17
measurement is presented.

---

## 5. Consistency check with the ADR

| ADR claim | Supported here |
|---|---|
| Alternatives H1–H6 were on the record | Rows C2, S2, S3, B2, G5, M2 cite records |
| Alternatives A1–A3 are closeout analysis | Rows C3, C4, C5, B3, B4, G2–G4, M3, M4, F2–F4 |
| No token-budget cap is implemented | §4 and B1/B2 |
| The gate placement is structural, not measured | G1/G2 and §4 latency row |
| T17 is not satisfied (S6 stopped, acceptance incomplete) | §4 latency row |
