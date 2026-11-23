# Runtime Policy Catalog

**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
**Owner:** C (catalog), with each policy owned by the module that implements it.

---

## 0. How to read this catalog

For each degraded or failure path the catalog states four things in this order:

1. **Trigger** — the condition, in the terms the code tests.
2. **Actual behaviour** — what the code does, traced to a function.
3. **User-visible message / diagnostic** — what a human sees, and on which
   channel (terminal text, a named logger, or both).
4. **Artifact / state impact** — what is or is not written, and what a later
   reader may wrongly conclude.

**One rule applies to every row:** a soft runtime failure is **not** permission
for the corresponding regression test to fail. Green-washing a soft path by
loosening its test would violate `REQ-GOV-04`. The "Test posture" column names
the node that must stay green.

---

## 1. Data insufficiency — O1 SMA history

| Field | Detail |
|---|---|
| **Trigger** | Fewer than 50 (resp. 200) cleaned, non-missing dated closes through the reported date; or a duplicate trading date; or an all-missing frame |
| **Actual behaviour** | Return the exact N/A sentence instead of a numeric SMA. Duplicate dates are rejected rather than averaged. An empty/no-close frame keeps the existing no-market-data outcome. |
| **Message** | `N/A: insufficient history (needs {window} sessions, have {count})`; duplicate → `N/A: invalid price history (duplicate trading date)` |
| **Artifact impact** | The Market Analyst report contains the N/A sentence in place of the number. Downstream prose may describe the market without that indicator. |
| **What a reader must not conclude** | That the indicator was unavailable from the vendor. "Insufficient history" is a statement about the data window, not an outage. |
| **Registry** | `development_contract.o1.insufficient_text`, `…date_rule`; `REQ-O1-01`, `-02`, `-03` |
| **Test posture** | `test/offline/test_o1_sma_guard.py` (12 nodes) must stay green |

---

## 2. Invalid configuration — O3 caps

| Field | Detail |
|---|---|
| **Trigger** | A non-int / boolean / non-positive budget, or a cap sum exceeding the configured total |
| **Actual behaviour** | `validate_caps(config)` raises `ValueError`; `condense_source` raises `CondensationError` for a bad block or budget. Configuration is rejected **before** any condensing runs. |
| **Message** | Python exception text naming the offending field (`test_T_E4_invalid_config_raises_value_error`) |
| **Artifact impact** | No condensed output is produced; the run does not silently fall back to an unbounded budget |
| **Reader caution** | An invalid config is a hard error, not a degraded run. It is not the same class as a budget overflow (§4). |
| **Registry** | `O3-FR-04`, `O3-FR-08` |
| **Test posture** | `test/offline/test_input_condensation.py` must stay green |

---

## 3. Condensation exception — O3 budget overflow

| Field | Detail |
|---|---|
| **Trigger** | A protected placeholder exceeds its cap, or an item cannot be fitted within the per-source cap |
| **Actual behaviour** | For protected content: raise `CondensationError(..., budget_exception=True)`. The caller uses the **original affected block**. |
| **Message** | The exception carries `budget_exception`; the report records it |
| **Artifact impact** | The original block is used and the block is **excluded from budget-pass calculations** |
| **Reader caution** | A run containing a budget exception must **not** be reported as having met the budget. `development_contract.o3.budget_exception` is explicit on this. |
| **Registry** | `O3-FR-04`, `development_contract.o3.budget_exception`; nodes `test_T_B4_protected_content_over_cap_falls_back`, `test_FC5_node_keeps_original_news_block_when_protected_text_over_cap` |
| **Test posture** | Both fallback nodes must stay green; loosening them would make a budget exception look like a pass |

---

## 4. Token counting unavailable — O3 optional tokenizer

| Field | Detail |
|---|---|
| **Trigger** | `count_tokens` is not supplied |
| **Actual behaviour** | `tokens_before` / `tokens_after` are `None`; character counts are still recorded |
| **Message** | Report fields are `None`, not `0` |
| **Artifact impact** | The run makes no token claim |
| **Reader caution** | Characters ≠ tokens. `REQ-O3-07` forbids a token-reduction claim without a labelled tokenizer count or observed provider usage. A `None` is honest; a `0` would be a false measurement. |
| **Registry** | `development_contract.o3.token_claim`, `REQ-O3-07` (governance) |
| **Test posture** | `test_T_E5_absent_tokenizer_reports_none`, `test_T_E7_optional_tokenizer_estimates_decrease` |

**Limit on what those nodes prove:** `test_T_E7_optional_tokenizer_estimates_decrease`
injects a **simulated** counter of the form `len(text)//4`. It proves the optional
counting interface is wired and that estimates decrease; it does **not** exercise
a real tokenizer and does **not** observe provider-reported usage. No
provider-token evidence is claimed anywhere in this catalog.

---

## 5. Gate failure — O4 evidence gate

### 5.1 Recoverable internal checker failure

| Field | Detail |
|---|---|
| **Trigger** | Unexpected error while resolving the original rating or classifying evidence |
| **Actual behaviour** | Fail **closed**: effective rating becomes `REVIEW`; the diagnostic reason is preserved; `final_trade_decision` bytes are untouched |
| **Message** | The reason is carried into the run's diagnostic output; the gate does not print a tradeable rating |
| **Artifact impact** | All enabled surfaces use `effective_rating`; the ungated original is not published |
| **Reader caution** | `REVIEW` here does **not** mean "the model said REVIEW" — it means the checker could not complete. The reason distinguishes them. |
| **Registry** | `O4-INV-04`, `development_contract.o4.checker_failure` |
| **Test posture** | `O4-T-07`, `O4-T-08` |

### 5.2 Invalid analyst configuration

| Field | Detail |
|---|---|
| **Trigger** | Unknown analyst key, or missing selection |
| **Actual behaviour** | `check_evidence` raises `ValueError` **before** the recoverable handler, so the run aborts rather than being converted to `REVIEW` |
| **Message** | `ValueError` naming the configuration problem |
| **Artifact impact** | Authoritative publication does not happen |
| **Reader caution** | A configuration error is not a safety downgrade; it is a refusal to proceed. `development_contract.o4.checker_failure` states "invalid analyst configuration → abort authoritative publication". |
| **Registry** | `O4-FR-15`-adjacent; `development_contract.o4.checker_failure` |
| **Test posture** | `O4-T-18` |

### 5.3 Rating disagreement

| Field | Detail |
|---|---|
| **Trigger** | `final_rating` and a clearly parsed `final_trade_decision` rating disagree |
| **Actual behaviour** | Effective rating becomes `REVIEW`; the conflict reason is preserved; an original `REVIEW` is never upgraded |
| **Message** | Conflict reason retained for diagnosis |
| **Artifact impact** | Published rating is `REVIEW` on every surface |
| **Registry** | `O4-INV-05`, `development_contract.o4.rating_source` |
| **Test posture** | `O4-T-25` |

### 5.4 Incomplete evidence

| Field | Detail |
|---|---|
| **Trigger** | A required analyst report is empty or missing for a selected analyst |
| **Actual behaviour** | Effective rating `REVIEW`; every surface uses it |
| **Reader caution** | A non-empty report **that mentions unavailable data** is treated as present. `development_contract.o4.report_presence` deliberately has "no whole-report sentinel in v1". Do not read a `REVIEW` as "an analyst failed". |
| **Registry** | `O4-INV-01`, `development_contract.o4.required_reports` / `…report_presence` |
| **Test posture** | `O4-T-02`, `O4-T-19` |

---

## 6. Manifest failure — O2

| Field | Detail |
|---|---|
| **Trigger** | `write_manifest` raises, or the reserved directory cannot be used |
| **Actual behaviour** | The analysis result stands with the O4 effective rating; the provenance record is not claimed; no partial `manifest.json` is left |
| **Message** | Terminal warning: "The analysis result above stands; only its provenance record is missing." |
| **Artifact impact** | Run directory exists, other artefacts exist, `manifest.json` absent |
| **Reader caution** | A missing manifest means **provenance is unavailable**, not that the analysis failed. Conversely, an existing manifest is a provenance claim — a partial file must never be produced. |
| **Registry** | `development_contract.o2.write_failure` |
| **Test posture** | `test_manifest_write_failure_is_fail_soft_with_effective_rating[Hold]` and `[REVIEW]`; `test_o2_manifest.py` |

### 6.1 Run-directory reservation failure

| Field | Detail |
|---|---|
| **Trigger** | Repeated UUID collision, or the directory cannot be created |
| **Actual behaviour** | `RunDirectoryUnavailable` → CLI exits with code **1**, before any graph work |
| **Message** | Red error line with the exception text |
| **Artifact impact** | Existing files untouched; no graph, no manifest, no O5 JSONL |
| **Reader caution** | This is the only path where the run does not start at all. Distinguish it from a mid-run failure. |
| **Registry** | `development_contract.o2.run_dir` |
| **Test posture** | `test_reservation_collision_exits_before_graph_and_preserves_existing_files` |

---

## 7. Sink failure — O5 evidence

| Field | Detail |
|---|---|
| **Trigger A (construction/open)** | `_JsonlEvidenceSink` cannot open the file |
| **Trigger B (write)** | A write fails mid-line |
| **Trigger C (close)** | Closing the stream fails |
| **Actual behaviour A** | Log `SINK_FAILED` on `tradingagents.o5.evidence`; bind an **inactive** sink for the scope; continue |
| **Actual behaviour B** | Roll the file back to the pre-write offset, log `SINK_FAILED`, continue |
| **Actual behaviour C** | Log `SINK_FAILED`; the binding has already been restored, so an in-flight business exception is **not** masked |
| **Message** | Independent logger only — deliberately not the main logger, so a failing sink cannot suppress its own diagnostic |
| **Artifact impact** | No file (A), or a file containing only complete earlier rows (B) |
| **Reader caution** | **A missing or short JSONL file does not mean no events occurred.** It means persistence failed. Consumers must not infer selection behaviour from file absence. |
| **Registry** | `development_contract.o5.sink_failure`, `…evidence_path` |
| **Test posture** | `test_s5_i5_and_i5b_preserve_full_result[write]` and `[open]`; `test_s5_t07_i5b_open_failure_keeps_result_and_restores_binding` |

### 7.1 Selector invariant failure

| Field | Detail |
|---|---|
| **Trigger** | An invariant check on the selector's output fails |
| **Actual behaviour** | Suppress the selected articles; return an explicit filter-unavailable message |
| **Message** | Filter-unavailable text, explicitly **not** the no-news wording |
| **Reader caution** | `development_contract.o5.invariant_failure` is explicit: "suppress selected articles and return an explicit filter-unavailable message, **not no-news**". Presenting it as "no relevant news" would be a false statement about the market. |
| **Registry** | `development_contract.o5.invariant_failure` |
| **Test posture** | O5 invariant suites |

### 7.2 Zero limit

| Field | Detail |
|---|---|
| **Trigger** | `limit == 0` |
| **Actual behaviour** | Return `LIMIT_ZERO` without any vendor fetch; emit `V-LIMIT-ZERO` |
| **Message** | "No macro news items were requested because the result limit is zero." |
| **Reader caution** | Zero requested is not zero found |
| **Registry** | `development_contract.o5.zero_limit` |
| **Test posture** | `test_s3_zero_limit_skips_vendor`; CLI probe covers this real tool branch only |

---

## 8. Interruption and resume

| Field | Detail |
|---|---|
| **Trigger** | A mid-stream failure or `KeyboardInterrupt` while streaming |
| **Actual behaviour** | The exception propagates **unchanged**; the O5 scope restores the previous binding and closes the file; `record_decision` and `clear_checkpoint_on_success` are **skipped**, so the checkpoint remains for resume |
| **Message** | The original exception; an O5 close failure is logged separately and does not replace it |
| **Artifact impact** | No manifest; no state log; checkpoint retained; any O5 rows already written remain complete |
| **Reader caution** | A run that ends without a manifest may be an interrupted run, not a failed one. `test_s5_t03` / `test_s5_t04` assert the binding restoration for exception and interrupt respectively. |
| **Registry** | O2 `run_dir`; S5 acceptance cases |
| **Test posture** | `test_s5_t03_exception_in_stream_propagates_and_restores_binding`, `test_s5_t04_keyboard_interrupt_propagates_and_restores_binding` |

**Resume caveat.** There is no checkpoint schema migration (see
[`memory-design.md`](memory-design.md) §2). After a code change to the state
shape, resuming an old checkpoint is not guaranteed safe; clearing is the safe
action.

---

## 9. Unknown statistics — O6

| Field | Detail |
|---|---|
| **Trigger** | An Analyst's token count is unknown or partial, or a call cannot be attributed |
| **Actual behaviour** | Print `--` for an unknown value and `n (partial)` for a floor; always print the unattributed line |
| **Message** | Terminal summary after the run; nothing persisted |
| **Reader caution** | `--` is not zero. A partial figure is a floor, not a total. An unattributed count of 0 is evidence that attribution worked, not silence. |
| **Registry** | `development_contract.o6.*`, `O6-FR-*` |
| **Test posture** | `test/offline/test_o6_per_analyst_stats.py` (12 nodes), `test_o6_cli_wiring.py` |

**Open item.** `development_contract.o6.unattributed` records that
"Analyst binding scope and scope-label semantics await A confirmation".

---

## 10. Governance gate failures (change-time, not run-time)

These block a *change*, not a run. Included because they are runtime policies of
the pipeline.

| Gate | Trigger | Behaviour | Diagnostic |
|---|---|---|---|
| `test approval` | Changed files outside an approved scope, or missing/late approval | Change is blocked; exit 1 | Names the failing condition (missing approval, late approval, scope mismatch) |
| `ai-use log` | Code/prompt change without AI-use evidence | Blocked | Names the missing field or unresolvable reference |
| `requirements schema` | Registry not matching `req-schema.json` | Blocked | Schema violation |
| `governance permissions` | PR-reachable write scope, `write-all`, unsafe `pull_request_target`, missing `persist-credentials: false` | Blocked (fail-closed on ambiguity) | Names the workflow/job |
| Regression (`tests`) | Any prior test fails | Blocked | Failing nodes |
| `semantic (deterministic O4/O5)` | Fixed evaluation set below threshold | Blocked and reported | Which case failed |

**Important:** two of these (`test approval`, `ai-use log`) are
pull-request-only and appear as `skipped` on a push to `main`. A `skipped` job is
not a passed job; it means the gate did not apply to that event.

### 10.1 What is actually recorded about these gates

This catalog describes **designed behaviour**. Whether a gate ever blocked a real
change is a separate question, and is answered only by a cited run or PR:

| Gate | Real blocking on the record |
|---|---|
| `requirements schema` / regression `tests` | **Yes** — PR #41 E2 blocked (Schema fault; the four test matrices failed together), then E5 repaired and reapproved with [run 44998474208](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44998474208) 17/17; separately, E4 missing-review blocking recovered at E1. PR then closed unmerged |
| `test approval` | Gate **passing** recorded (#37 run `44979161445`, pinned `1c0b740`, 17 checks); a real rejection of a complete PR is **not** recorded |
| `semantic (deterministic O4/O5)` | **Independent red-light blocking not verified** |
| `governance permissions` | Guard logic and nodes exist; applicability is limited to workflow changes; a real blocking event is **not** recorded here |
| `ai-use log` | Structural rejections covered by nodes; a real blocking event is **not** recorded here |

**Preserved limits:** E3 of the #41 experiment was **not executed**; **no
independent administrator API read-back** of branch protection was obtained; in
E2 the failures were **coupled to the Schema fault** rather than isolated to one
job; and **PR #38 is a batch-specific process deviation** that is not
generalised. Detailed node-level mapping: [`trace-matrix.md`](trace-matrix.md)
§GOV.

**These governance experiments are not evidence for any business invariant in
§1–§9 of this catalog, and vice versa.**

---

## 11. Summary table

| # | Path | Class | Failure visible to user | Writes artefact | Blocks the run |
|---|---|---|---|---|---|
| 1 | O1 insufficient history | Substitute honest text | Yes (N/A sentence) | No | No |
| 2 | O3 invalid config | Hard error | Yes (exception) | No | Yes |
| 3 | O3 budget overflow | Fallback to original | Via report | Original block used | No |
| 4 | O3 no tokenizer | Absent measurement | `None` in report | No claim | No |
| 5a | O4 checker failure | Fail closed | Yes (`REVIEW` + reason) | Normal artefacts | No |
| 5b | O4 invalid config | Abort | Yes (`ValueError`) | No publication | Yes |
| 5c | O4 disagreement | Fail closed | Yes (`REVIEW`) | Normal artefacts | No |
| 6 | O2 manifest failure | Fail soft for result | Yes (warning) | No manifest | No |
| 6.1 | O2 reservation failure | Hard error | Yes | Untouched | Yes (exit 1) |
| 7 | O5 sink failure | Soft, named | Diagnostic only | Partial/none | No |
| 7.1 | O5 invariant failure | Suppress + name | Yes (filter-unavailable) | Normal artefacts | No |
| 7.2 | O5 limit zero | Normal path | Yes (sentence) | One `V-LIMIT-ZERO` row | No |
| 8 | Interruption | Propagate | Yes (original exception) | No manifest/state log | Yes |
| 9 | O6 unknown stats | Display `--` | Yes (terminal) | Nothing | No |
| 10 | Governance gates | Block change | Yes (CI) | — | Blocks merge |

**The column that matters least is "blocks the run".** Most of these policies
exist so that a run **completes honestly** rather than failing loudly; the
failure visibility and the reader caution are what prevent a completed run from
being misread.

---

## 12. Status of the "test posture" nodes

Every row above names a node that must stay green. Four separate statements are
kept apart and should not be substituted for one another:

| Statement | Meaning here |
|---|---|
| **Node exists** | The function is present at `main@252fe311d8d1483b5713de69b04ce2769c33f1dd` |
| **Historical execution passed** | F's reading of the Python 3.11 job log for run [`44988759013`](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44988759013/job/137104997890) reported PASSED entries for the 166 function references cited in that matrix at that SHA — **not** for every node named in this catalog |
| **Requirement covered** | The assertion actually proves the fit criterion; not inferred from a PASSED line |
| **Real merge blocked** | Only where §10.1 cites a run or PR |

The log body was not readable with the credential available to C (the
authenticated logs endpoint returned HTTP 401), so even the 166 figure is F's
transcribed reading, attributed as such.

**S6 / T17:** development is **stopped and acceptance is not completed**. No
performance threshold in this catalog is presented as met, and no new
performance experiment is run or implied.

