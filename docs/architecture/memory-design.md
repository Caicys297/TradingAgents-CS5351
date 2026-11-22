# Memory and State Design

**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
**Owner:** C (CLI-side state), with the memory subsystem owned by its module owner.

---

## 0. What this document covers

Six distinct persistence mechanisms exist in this system. They have different
owners, lifetimes and privacy properties, and they are **not** variations of one
"memory" component. Conflating them is the main source of wrong assumptions
about what survives a restart.

| # | Mechanism | Survives process exit | Scope |
|---|---|---|---|
| 1 | Graph state (`AgentState`) | No | One run |
| 2 | Checkpoint / resume (SQLite) | Yes | One ticker + date + analyst signature |
| 3 | Trading memory log (markdown) | Yes | One deployment/config root |
| 4 | O2 run directory + manifest | Yes | One run |
| 5 | O5 evidence JSONL | Yes | One run |
| 6 | O6 per-Analyst statistics | No | One run |

---

## 1. Graph state (`AgentState`)

**File:** `tradingagents/agents/state.py`
**Owner:** graph module.

**What it holds:** `trade_date`, `company_of_interest`, the four analyst reports,
`investment_debate_state`, `risk_debate_state`, `investment_plan`,
`trader_investment_plan`, `final_trade_decision`, and the rating fields the gate
writes (`final_rating`, `effective_rating`) with the original rating retained
separately for diagnosis (`development_contract.o4.state_rule`).

**Write:** by graph nodes during the stream; the gate writes rating fields on the
finalised state.
**Read:** the CLI merges chunk deltas into `final_state`, then passes it to
`record_decision`, the report offer and the manifest.

**Retention:** none by itself — it lives only as long as the process, unless
checkpointed (§2) or written to the state log (§4.4).

**Privacy:** the state log and reports contain analysis text. Neither is
sanitised beyond what the manifest contains; see §7.

---

## 2. Checkpoint and resume

**File:** `tradingagents/graph/checkpointer.py`
**Owner:** graph module.

**Identifiers.**

- `thread_id(ticker, date, signature="")` — the checkpoint thread key.
- `_db_path(data_dir, ticker)` — the SQLite file location.
- `checkpoint_step(...)` — the step number recorded for a thread.

The `signature` component matters: `trading_graph.py` keys the layout on
`analysts=parallel` and `memory=parallel`, so a resume under a **different
analyst set** does not silently continue an earlier, differently-shaped run.

**Write policy.**

- `get_checkpointer(data_dir, ticker)` yields a `SqliteSaver`.
- The CLI calls `begin_checkpoint(...)` before streaming and
  `clear_checkpoint_on_success(...)` after a clean stream.
- A mid-stream failure **skips both**, deliberately, so the checkpoint remains
  available for resume. This is stated in `cli/run.py` and is a designed
  behaviour, not an oversight.

**Read policy.** `checkpoint_input(state)` supplies the initial state; on resume
the CLI feeds `None` so LangGraph continues rather than re-appending.

**Retention and cleanup.**

- `clear_checkpoint(data_dir, ticker, date, signature)` removes one thread.
- `clear_all_checkpoints(data_dir)` removes all threads for a ticker.
- **No time-based expiry is implemented.** A checkpoint that is never resumed
  stays until one of the above is called.
- **No schema migration mechanism is implemented.** A change to the checkpoint
  payload shape is not versioned; the safe action is to clear rather than resume.

**Privacy.** The checkpoint contains the same analysis content as the state.
It lives under the configured data directory, not under `results_dir`.

---

## 3. Trading memory log

**Files:** `tradingagents/memory/log.py` (`TradingMemoryLog`),
`reflection.py`, `settlement.py`.

**Purpose.** An append-only markdown record of each decision and, once settled,
its outcome — so a later run can read past decisions and their lessons.

**Write policy.**

- Writes occur under `locked(self._log_path)` (`dataflows/files.py`), so
  concurrent runs on the same log serialise.
- `store_decision(...)` appends; `update_with_outcome(...)` and
  `batch_update_with_outcomes(...)` settle entries.
- `_resolved_tag(...)` marks settled entries so that rotation can distinguish
  them from pending ones.

**Read policy.** `load_entries()`, `get_pending_entries()`, `get_past_context(...)`
for context injection into a new run.

**Retention / cleanup.** An optional `memory_log_max_entries` cap enables
rotation of **resolved** entries only (`_apply_rotation`). When the cap is `None`,
rotation is disabled and the log grows without bound.

- **No time-based retention is implemented.**
- **No migration mechanism is implemented.** The on-disk format is the markdown
  entry shape parsed by `_parse_entry`; a format change without a migration will
  drop entries it cannot parse (`_parse_entry` returns `None`).

**Ownership.** The log belongs to the deployment's configured
`memory_log_path`, not to a single run. All runs of that deployment share it.

**Privacy.** Entries contain decision text. `_format_reflection_only` exists to
emit a reduced form, but the default full form contains the decision and its
outcome prose.

---

## 4. O2 run directory and manifest

**Files:** `cli/run.py` (`_reserve_run_directory`, `_artifact_references`,
`_finalize_run_manifest`), `tradingagents/repro/manifest.py`.

### 4.1 Run directory

`<config[results_dir]>/<safe_ticker>/<analysis_date>/runs/<uuid4>/`

Reserved **before any graph work**. On collision the reservation retries; a
persistent failure raises `RunDirectoryUnavailable` and the CLI exits with code
1, leaving existing files untouched
(`test_reservation_collision_exits_before_graph_and_preserves_existing_files`).

### 4.2 Manifest

`manifest.json` **in the reserved run directory**, written exactly once, after
the report offer has been handled.

**Contents** (`development_contract.o2.fingerprint`): SHA-256 of UTF-8 canonical
JSON over the normalised identity plus the **allowlisted** effective settings —
sorted keys, `separators=(',',':')`, `ensure_ascii=false`, `allow_nan=false`, ISO
analysis date, fixed Analyst order. Explicitly **excluded**: run ID, time,
duration, output, artifact paths, secrets, vendor payloads.

**Allowlist, not denylist.** `O2-FR-05` requires serialising *only* the
allowlisted keys; `O2-FR-11` excludes API keys, tokens, passwords,
credential-bearing URLs and unrelated environment variables. `O2-NFR-03`
restates this as "use an allowlist; serialized output contains no secrets".

**Artifact inventory.** Only artifacts whose own write succeeded are registered.
The state log counts only if `record_decision()` returned without raising.

### 4.3 Failure behaviour

`development_contract.o2.write_failure`: the analysis remains complete with the
O4 effective rating, a visible manifest-failed warning is shown, and no
provenance claim or partial file is produced. See
[`runtime-policy-catalog.md`](runtime-policy-catalog.md) §5.

### 4.4 Related artifacts outside the run directory

| Artifact | Path | Note |
|---|---|---|
| Message/tool log | `<results_dir>/<ticker>/<date>/message_tool.log` | One entry per file, registered once |
| State log | `<results_dir>/<ticker>/TradingAgentsStrategy_logs/full_states_log_<date>.json` | Written by `record_decision` |

These live at the **ticker/date** level, not per run, so two runs of the same
ticker and date share them. `development_contract.o2.artifact_stability` records
exactly this: ticker/date reports and logs are `shared_mutable` unless per-run
immutability is proven; only the manifest is `run_unique`.

### 4.5 Retention

**No retention policy or cleanup is implemented** for run directories. They
accumulate until an operator removes them. There is no automatic pruning, no
age-based expiry, and no size cap.

### 4.6 Version compatibility

The manifest carries the settings fingerprint but **no explicit schema version
field of its own** beyond the registry's `schema_target`. A consumer reading an
older manifest must not assume a newer allowlist. No migration of historical
manifests is implemented.

---

## 5. O5 evidence JSONL

**File:** `tradingagents/dataflows/vendors/yahoo/news.py`
(`o5_evidence_run`, `_JsonlEvidenceSink`).

**Path:** `<O2 run directory>/o5_evidence.jsonl` — the same run directory as the
manifest, per `development_contract.o5.evidence_path`: "same O2 run directory /
o5_evidence.jsonl, **when a CLI run context exists**".

**Present on the pinned baseline:** this mechanism is on `main` at
`252fe311d8d1483b5713de69b04ce2769c33f1dd` (E's `483e1f6`, C's `c1fa362`,
merged via PR #40 on `2026-11-22T05:17:25Z`). An earlier observation that PR #40
was blocked by a missing-approval red light was correct at the time and was
closed by PR #42 before #40 merged; it does not describe this baseline. Its
*evidence* status is not stated here — see [`trace-matrix.md`](trace-matrix.md).

**Write policy.**

- The scope opens after the reservation succeeds and before the graph is built,
  and covers graph construction, the stream, the report offer and the manifest
  write.
- Each event is appended as one JSON line under `locked(self.path)`.
- A partial write is rolled back to the pre-write offset, so a half-line never
  survives.
- On exit the binding is restored **first**, then the stream is closed; a close
  failure is reported as `SINK_FAILED` without masking an in-flight exception.

**Read policy.** Nothing in the product reads this file back. It is a diagnostic
record for a human or an external tool.

**Failure behaviour** (`development_contract.o5.sink_failure`): log `SINK_FAILED`
on the independent logger `tradingagents.o5.evidence` and **continue serving the
honest result**; do not claim persisted evidence.

- Construction/open failure binds an **inactive** sink for that scope: the run
  proceeds, the file is absent, and the diagnostic names the reason.
- A missing file therefore does **not** mean "no events occurred".

**Retention.** None implemented; the file lives with the run directory.

**Version compatibility.** Each line is a self-describing event carrying
`rules_version`. A reader must tolerate unknown fields rather than assuming a
fixed schema. No reader-side migration exists because there is no reader.

---

## 6. O6 per-Analyst statistics

**Files:** `cli/stats_handler.py` (`StatsCallbackHandler`), `cli/display.py`
(`display_agent_summary`).

**Scope.** Ordinary and wrap-up calls of *selected* Analysts. The identity comes
from Graph Config metadata `scope=analyst` and `agent_key=spec.key` at the
Analyst subgraph boundary — **never** inferred from callback order or node name
(`development_contract.o6.identity`).

**Categorisation.**

- A call tagged in scope with a valid, selected key → named Analyst row.
- A call tagged in scope with a missing/invalid key → `unattributed_calls`.
- A known out-of-scope call → neither.

**Lifetime.** In-memory for the run only. Nothing is persisted; the summary is
printed to the terminal after the run completes.

**Unknown values.** An unknown token count prints `--`, never `0`
(`format_agent_tokens`). The unattributed line is always printed so that a zero
is evidence rather than silence.

**Legacy contract.** `get_stats()` returns exactly the existing four keys with
their existing semantics (`development_contract.o6.legacy_api`).

**Open item.** `development_contract.o6.unattributed` records that "Analyst
binding scope and scope-label semantics await A confirmation". The statistics
are therefore advisory telemetry with one unconfirmed contract detail.

---

## 7. Privacy and data handling

| Data | Contains | Privacy stance |
|---|---|---|
| `manifest.json` | Allowlisted settings + artifact paths | **Designed** to contain no secrets (`O2-FR-05`, `O2-FR-11`, `O2-NFR-03`). Enforced by an allowlist and by `O2-TC-06`/`TC-16`/`TC-23` tests. |
| `o5_evidence.jsonl` | Event variants and counts; no article text by construction | Selected-article *text* is not part of the event; `V-SELECTED` records counts and identifiers |
| Report tree, state log, `message_tool.log` | Full analysis prose | Not sanitised; treat as internal-only artefacts |
| Memory log (markdown) | Decision text + outcomes | Not sanitised; shared across runs of the deployment |
| Checkpoint SQLite | Graph state | Not sanitised; lives under the data directory |
| O3 audit report | Counts and stable non-secret ids only | `O3-NFR-05` requires raw titles, links, payloads, endpoints and credentials to stay out of persisted audit records |

---

## 8. Summary of implemented vs not implemented

| Capability the course asks about | Status |
|---|---|
| What survives across sessions | Memory log, checkpoints, run directories, manifests |
| What survives interruptions | Checkpoint (deliberately retained on mid-stream failure) |
| What survives versions | **Nothing is versioned with a migration path.** No checkpoint schema migration, no memory-log migration, no manifest migration |
| Write policy | Per mechanism, all under `locked()` where the file is shared |
| Retrieval policy | Read-back exists for the memory log and checkpoints; **nothing reads the O5 JSONL or the manifest at runtime** |
| Ownership | Per mechanism (run, ticker+date, deployment) — see §0 and §4.4 |
| Retention | **No retention period is defined anywhere.** Rotation exists only for the memory log, and only when a cap is configured |
| Privacy | Allowlist for the manifest; the rest is unsanitised internal data |

**Explicit gaps, stated rather than papered over:** no retention period, no
migration mechanism, no runtime reader for the O5 evidence, and no per-run
isolation for the ticker/date-level logs.
