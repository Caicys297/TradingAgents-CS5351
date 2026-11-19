# O2 Stage 2 Integration — OpenCode Execution Plan

**Document version:** v0.2-DRAFT (TC-05 artifact update; filename unchanged: `…-v0.1-DRAFT.md`)
**Status:** Draft planning record. A implementation-scope confirmation, F test-boundary/CI approval, and latest A/F/C TC-05 artifact decisions are recorded here; existing formal approvals remain bound to earlier commits (§7). This revision needs A file-scope confirmation and F formal review of the revised test cases. PR #18 remains Draft. This planning update is not implementation approval; no implementation or CI result is claimed.
**Owner:** B (QinQilun)
**Requirements baseline reference:** PR #9 merge commit `d36a677d4738efd365b6bbcf6f69f993acf8fd3c`. Joint-validation baseline: PR #21 merge `69e91ff115694f3455196e6a4114d4fe653fbb06`; O6 CLI merged via PR #20 `e4b6f9ac625f39579635c840aed98ab8dfefdaf9`. **Actual baseline verified at this plan update: `origin/main` = `102511dd44ad8779a46e09cbefe50edb8a995b45`**; re-verify and record the actual base SHA at implementation time.
**Plan update binding:** v0.2-DRAFT based on plan commit `c200512379fb38ddb9215cfb0bd71ea0d16aa241`; this update’s commit SHA is reported in PR #18.
**Phase 1 implementation:** PR #16 merge commit `808df04f320d95c1ab4ef5a6e88149335cdeff41`.  
**A scope supplement:** [PR #18 review 5959122354](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5959122354), submitted `2026-11-18T15:00:01Z`.  
**F formal test-plan approval:** [PR #18 review 5968062524](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968062524), submitted `2026-11-19T01:41:23Z`.  
**C/F ownership and timing confirmation:** [PR #18 review 5968754538](https://github.com/Caicys297/TradingAgents-CS5351/pull/18#pullrequestreview-5968754538), submitted `2026-11-19T03:08:27Z`.

## 0. Approval boundary and plan binding

- **A-confirmed implementation scope:** completed normal CLI runs only; no Graph API change; existing legacy report/state/log paths remain; one manifest after analysis and report-save handling; fail-soft analysis result with fail-closed provenance; external saves are preserved but omitted; no broadened file scope and no changes to public interfaces, schema, fingerprint, or redaction rules.
- **F-confirmed test boundaries:** existing official test IDs only; separation of report-save failure from manifest-write failure; the approved three-platform CI matrix; F owns test review and approved CI workflow changes. Formal F approval of this revision’s new test cases remains required.
- **C ownership and remaining decisions:** C owns `cli/run.py` integration and must document the actual base SHA and exact file scope before implementation. C7 now specifies the reservation failure as `RunDirectoryUnavailable`, converted by `run_analysis` to `typer.Exit(code=1)`; hook implementation and write-evidence plumbing remain implementation work.
- **Binding:** this update records v0.2-DRAFT decisions from base plan commit `c200512379fb38ddb9215cfb0bd71ea0d16aa241`. This planning update is not implementation approval unless the recorded approvals expressly say otherwise; existing formal approvals cover earlier commits, not this revision’s new contract text.

## 1. Authorization boundary

This document records the approved Stage 2 planning and execution boundary. Implementation must remain split by ownership and proceed in separate implementation PRs. A/F approval of the planning scope does not itself claim implementation, test execution, or CI results.

Stage 2 is limited to completed normal CLI runs, unique run-directory reservation, CLI/Graph manifest integration, offline integration/regression tests, and the approved three-platform CI matrix. It excludes backtests, replay, failed/programmatic runs, immutable data snapshots, moving existing report/state/log paths, unrelated refactoring, Graph changes for this batch, and the D7 Schema CI Gate.

C owns shared `cli/run.py` integration and coordinates CLI test integration. B owns the manifest interface and `test/offline/test_o2_cli_manifest.py`. F owns test review and approved CI workflow changes. This batch does not change Graph based on C’s read-only inspection.

### C's confirmed CLI integration contract (A-confirmed)

This revision records A's confirmed contract. Superseded wording from earlier revisions is replaced rather than layered.

**C1 — Graph interface unchanged; state log registered only on success.**
The Graph's existing interface is kept. The CLI registers the state log **only after `record_decision()` returns successfully**, by checking the path this run expects, and labels it `shared_mutable`. If the call fails — including a failure while writing or closing the file — the file is **not** registered, even if a stale or historical file sits at that path. Existence is never the evidence; the successful return is.

**State-log call chain and path consistency (`origin/main` `102511dd44ad8779a46e09cbefe50edb8a995b45`), verified read-only:**

| Step | Location | Verified fact |
|---|---|---|
| CLI call | `cli/run.py:360` | `graph.record_decision(selections["ticker"], selections["analysis_date"], final_state)` inside `try/finally`; the `finally` only calls `end_checkpoint()`, no `except` |
| Boundary | `trading_graph.py:359-362` | `record_decision` calls `self._log_state(trade_date, final_state)` **first**; the early `return` at `:367` (no decision) happens **after** `_log_state` |
| Write | `trading_graph.py:470-476` | `Path(self.config["results_dir"]) / safe_ticker_component(...) / "TradingAgentsStrategy_logs"`; `with open(log_path, "w")` + `json.dump` |
| Close | same `with` block | the file is **written and closed**; no early return between `:440` and `:476`; **no `fsync()`** — this batch does not require one |
| Exceptions | none caught | `_log_state` and `record_decision` have no `try/except`; a write or close failure propagates to `:360` and aborts clean completion |

**Path consistency (CLI reconstruction vs the writer):** `results_dir` is the same config dict object passed at construction (`cli/run.py:114` → `:133`); the ticker is the same imported `safe_ticker_component` (`cli/run.py:29`) applied to `company_of_interest`, which `create_initial_state` sets to the CLI's ticker (`propagation.py:32`); the date is the canonical `YYYY-MM-DD` validated at graph start. A non-raising `record_decision()` therefore means the state log was written and closed at the reconstructed path. Because the write is **not atomic**, a failure mid-`json.dump` can leave a partial file — which is why registration keys on the return, never on the file.

**C2 — `_log_state()` write boundary stated precisely.**
`_log_state()` writes with `open(path, "w")` inside a `with` block and closes the file; it does **not** call `fsync()`. For this batch that is sufficient for registering the artefact after a normal run; the limit is stated rather than implying durability. No change to `_log_state()` is requested.

**C3 — `_offer_reports()` returns `list[Path]`.**
The private `_offer_reports()` returns `list[Path]` listing the files **actually written when the optional report save succeeded as a whole**: the complete Markdown report, the HTML report if one was produced, and the per-section files. Its existing display and prompting behaviour is unchanged. **If the save is declined, or fails as a whole, no file in that save directory is registered — including any partially written leftover.**

**C4 — `_artifact_references` takes both roots.**
`_artifact_references` explicitly receives **both** `results_dir` and `run_dir`. `results_dir` performs the boundary check and the relative-path computation; `run_dir` decides `run_unique`. Artefacts produced at their previous (unmigrated) locations are labelled `shared_mutable`. **Directory scanning to pick up historical files is forbidden.**

**C5 — Live per-section reports, `message_tool.log`, and the state log each stand on their own write evidence.**
- **Live per-section reports** (`save_report_section_decorator`, `cli/run.py:184`) and **`message_tool.log`** (`:157`, `:169`) are registered at their own confirmed write: after the `with open(...)` block returns without raising. A raising write is not registered. Both are at their previous (unmigrated) locations and are labelled `shared_mutable`.
- **State log** is registered only after `record_decision()` returns without raising (C1), at the reconstructed path, labelled `shared_mutable`.
- No artefact borrows another's evidence; every registration names the write that produced it.

**C6 — Out-of-boundary report saves.**
A user-supplied save path outside `results_dir` keeps its ability to save. When that external save succeeds, the manifest **omits** the reference. Saving succeeds and reference omission are verified as **two separate assertions**.

**C7 — Run-directory reservation: 3 attempts, then a clean abort.**
Reservation uses `mkdir(exist_ok=False)` with **at most 3 attempts in total**. If every attempt collides, the run **terminates before Graph** and reports the failure explicitly. Concretely: print a short red message naming the ticker/date and stating that no run directory could be reserved, then raise `RunDirectoryUnavailable` (a `RuntimeError` subclass); `run_analysis` converts that to `raise typer.Exit(code=1)`, the convention the CLI already uses for an unrecoverable pre-run condition (`cli/run.py:107-110`). **Graph is called zero times, and existing files keep their original values.** A test may assert either the dedicated exception or the `typer.Exit`, but must assert **Graph was never constructed or called** and that pre-existing files are byte-unchanged.

**Order (unchanged):** user choices/config → reserve run directory → Graph → successful completion and O6 display → report-save choice and artifact collection → one manifest attempt.

**Approved TC-05 artifact rules (summary of C1–C7):**

1. Live CLI section reports under `results_dir/<ticker>/<date>/reports/` are listed only with evidence that this invocation wrote them; label them `shared_mutable`; never include historical files by directory scan or existence.
2. The optional saved report tree under `results_dir/reports/<ticker>_<stamp>/` is included only when `_offer_reports()` confirms the whole save succeeded; its `list[Path]` contains only the complete Markdown, HTML when generated, and section files actually written; label them `shared_mutable`.
3. A declined save, or a failed save even with partial files left behind, contributes no files from that optional saved report tree; existing prompt/display behavior is preserved.
4. Saving to a user-selected path outside `results_dir` remains supported; those files are omitted from the manifest rather than the save path being rejected.
5. The state log is included only after `record_decision()` returns normally, with its path reconstructed and validated using the same effective config, ticker, and date as the writer; call failure excludes it even if an old file exists. Label `shared_mutable`; no `fsync`/power-loss durability claim; no Graph interface change.
6. `message_tool.log` is included only with evidence that this invocation appended or wrote to it; label `shared_mutable`; existing-file presence alone is insufficient.
7. Artifacts confined to the reserved per-run directory remain `run_unique` under the existing contract.
8. `_artifact_references` receives both `results_dir` and `run_dir`; use `results_dir` for containment and relative paths, and `run_dir` only to determine `run_unique`.

Both per-section sets — live run-directory reports and the saved report tree — are in the expected manifest set when their own write evidence exists; the saved set additionally requires whole-save success. This resolves the earlier pending B set-choice question.

### Still pending confirmation

Only genuinely unspecified items remain:

- **A:** confirmation of the exact file scope C may edit.
- **F:** formal approval of this revised test plan and its added test cases.
- **C:** record the actual base SHA and exact `cli/run.py` file scope before implementation; implement the specified hooks and write-evidence plumbing.

The partial-save question is settled by C3: a whole-save failure registers nothing from that directory. The earlier B set-choice question is settled by the approved TC-05 artifact rules: both live and saved per-section sets are included when their own write evidence exists, with the saved set requiring whole-save success.

## 2. Preconditions before implementation

OpenCode must report all items below and stop if one is unmet:

- Fetch has completed and the exact current `origin/main` SHA is recorded. It must contain PR #9 merge `d36a677...` and PR #21 merge `69e91ff...`; if main has advanced, record the actual base SHA and recheck the allowlist.
- Work is on a dedicated Stage 2 implementation branch created from that verified base, not the PR #8 documentation branch, PR #18 planning branch, or retired Phase 1 branch.
- Working tree is clean before branch creation, or existing user changes are preserved and explicitly excluded.
- PR #16 and PR #21 changes remain present; approved files are not rewritten or discarded.
- C documents the actual base SHA and exact `cli/run.py` file scope before implementation; no file scope is broadened beyond the approved contract.
- C's hooks `_reserve_run_directory` and `_finalize_run_manifest` are **specified in this plan** (§1 C7 and §3) with their signatures, return values, failure behaviour and owner, so A/F can approve them and B can write tests against them. Publishing implementation code is **not** a precondition for B writing tests; B may test against the specified interface plus a fake. If any approval process does require published code first, that must cite its own authorising record rather than this plan.
- C specifies the run-directory reservation failure behaviour — stated here in §1 C7 as `RunDirectoryUnavailable` converted to `typer.Exit(code=1)` — before B encodes its expected result.
- No Graph change is made. If implementation finds a necessary Graph dependency, stop and provide the exact source call chain and proposed diff for A/C approval.
- No public interface, manifest schema, fingerprint, redaction, or allowlist change is made.
- F’s approved CI matrix is used; F owns CI workflow changes and test review.

## 3. Proposed sequence

1. **Read-only source audit:** Inspect the current CLI lifecycle, results-path consumers, artifact creation times, path validation, test collection, platform CI, and current `main` diff. Report exact candidate files and integration points to A/C/F before editing.
2. **Run-directory reservation (C-owned `cli/run.py`):** Call `_reserve_run_directory(results_dir, ticker, trade_date) -> RunContext(run_id, run_dir)` exactly once before Graph starts. It reserves `results_dir/<safe ticker>/<date>/runs/<uuid4 hex>/` using `mkdir(exist_ok=False)`, **at most 3 attempts in total**, and does not write the manifest. **Failure behaviour (specified):** after three collisions it raises `RunDirectoryUnavailable` (a `RuntimeError` subclass) after printing a short red message naming the ticker/date; `run_analysis` converts that to `raise typer.Exit(code=1)`, the convention already used at `cli/run.py:107-110`. Graph is called **zero** times and pre-existing files are byte-unchanged.
3. **Artefact collection at each write site (C-owned `cli/run.py`):**
   - **Reports (`_offer_reports`):** returns `list[Path]` only when the optional save **as a whole** succeeded — complete Markdown, HTML (if produced), and per-section files. Declined or wholly failed saves register **nothing from that save directory**, including partial leftovers. Display and prompting are unchanged.
   - **Live per-section reports (`save_report_section_decorator`, `cli/run.py:184`) and `message_tool.log` (`:157`, `:169`):** registered at their own confirmed write, i.e. after the `with open(...)` block returns without raising; a raising write is not registered. Both sit at their previous (unmigrated) locations and are labelled `shared_mutable`.
   - **State log:** registered only after `record_decision()` (`:360`) returns without raising, at the reconstructed path, labelled `shared_mutable`; never registered on a write or close failure.
4. **Manifest finalisation (C-owned `cli/run.py`; B owns manifest interface):** After successful analysis and after `_offer_reports()` handles the report-save choice, call `_finalize_run_manifest(run_context, *, config, artifacts) -> ManifestWriteResult(success, manifest_path, artifacts, error)` exactly once. It must not rerun Graph or reparse the rating. `_artifact_references` receives **both** `results_dir` (boundary + relative paths) and `run_dir` (`run_unique`); no directory scanning. A successful external save path outside `results_dir` is omitted from the manifest. Pass normalized identity and only Registry-allowlisted effective config, including `input_condensation_audit_note`; retain secret redaction and `actual_input_data_provenance: not_captured`.
5. **Failure behaviour:** On manifest **write** failure, preserve the completed analysis result and O4 effective rating, finish normally, show a short warning that the manifest was not saved and the run's provenance record is unavailable, show no success path, and leave no partial manifest. Retain the Phase 1 atomic-write guarantee. Assert behaviour, not an exact English warning string. A report **writer** failure is a distinct case with its own test (see the test plan); it does not change TC-13/14's existing manifest-write acceptance meaning.
6. **Offline integration tests:** B prepares `test/offline/test_o2_cli_manifest.py` against the interface specified in this plan, mainly through real `run_analysis()` with a fake Graph. Verify the call order, hook call counts, unique directory, the exact artefact set with per-item stability labels, and write-failure behaviour; spying on the two hooks is allowed, and the real manifest writer remains in the success path using a temporary directory. Keep existing O2-TC IDs: TC-04 for full CLI success, TC-13/14 for manifest write failure, TC-11 for bounded allocation/collision, and TC-05/15/19/20/21/23 for their assigned coverage. Do not add a new ID.
7. **Regression and CI (F owns CI):** Run targeted O2 tests and `pytest -q`. Ubuntu keeps the existing Python 3.11–3.14 full regression plus the Python 3.12 non-UTC job; macOS and Windows run `test/offline/test_o2_manifest.py` and `test/offline/test_o2_cli_manifest.py` on Python 3.12. Record commit SHA, commands, workflow URLs, Python/OS versions, and actual outcomes.
8. **Review handoff:** Report changed files, diff, test/CI evidence, limitations, and plan/approval references. Open a PR for review; do not approve or merge on behalf of A/F.

## 4. File boundary and ownership

Candidate paths must be checked against the verified base and team ownership before edits.

| Area | Candidate paths | Owner / guard |
|---|---|---|
| CLI lifecycle, run directory, manifest invocation | `cli/run.py` | C owns shared integration: `_reserve_run_directory`, `_finalize_run_manifest`, `_offer_reports` returning `list[Path]`, state-log registration, and artifact write evidence; C must document actual base SHA and exact file scope before implementation; B owns manifest interface |
| Graph context and output paths | `tradingagents/graph/trading_graph.py` | **No Graph changes in this batch** (A-confirmed). If one proves necessary, stop with the exact call chain and proposed diff for A/C approval |
| Phase 1 writer | `tradingagents/repro/manifest.py` | B owns manifest interface; PR #21 synchronization already merged (`69e91ff1`); schema/fingerprint/redaction unchanged |
| Existing Phase 1 tests | `test/offline/test_o2_manifest.py` | Preserve |
| New CLI integration tests | `test/offline/test_o2_cli_manifest.py` | B owns; tests may be written against the interface specified in §1/§3; implementation publication is not a precondition per this plan |
| Test discovery/config | `pyproject.toml` or current test config | Change only if audit shows necessary and C/F approve ownership |
| CI workflows | `.github/workflows/ci.yml` or current workflow files | F owns test review and approved CI workflow changes |
| Setup/dependencies | `setup.py`, `pyproject.toml`, or current packaging files | Out of scope unless a specific approved need is documented; no dependency addition by default |

## 5. Stop conditions

Stop and return evidence for review if implementation requires:

- changing the approved completed-CLI-only scope or adding failed/programmatic runs;
- moving existing report/state/log paths or changing legacy artifact stability away from `shared_mutable`;
- changing manifest schema, fingerprint semantics, secret handling, or allowlist beyond the merged Registry;
- adding or redefining an official O2-TC ID;
- writing more than one manifest or writing before analysis completion/report-save handling;
- changing the approved fail-soft/fail-closed failure behavior or omitting the visible warning/no-success-path requirement;
- listing files from a declined or failed optional report save, including partial files left behind;
- including historical live reports, saved reports, state logs, or message logs based on existence or directory scan;
- rejecting an external user-selected save path instead of preserving the save and omitting it from the manifest;
- claiming `fsync` or power-loss durability for the state log;
- changing Graph or public APIs without the exact dependency and proposed diff approved by A/C;
- changing ownership assignments or broadening C/B/F file scope;
- adding a runtime dependency;
- writing CLI tests before the interface in §1/§3 is available for B to test against;
- editing CI without F’s confirmed ownership;
- an unresolved CI platform/version or missing test-to-requirement mapping;
- rebasing, resetting, or rewriting existing Phase 1, PR #21, or PR #20 history.

## 6. Required implementation records

Before the first code edit, record the verified base SHA, branch, clean working-tree status, approved plan versions, A/F approval references, C’s actual base SHA and exact file scope, C’s CLI/test ownership confirmation, and actual coding-start timestamp with timezone. Record that this v0.2-DRAFT update is bound to base plan commit `c200512379fb38ddb9215cfb0bd71ea0d16aa241` and that its update commit SHA is reported in PR #18. State whether implementation approval has actually been recorded; this planning update alone is not implementation approval. For each verification, report the exact command and actual output. Do not infer local tests from CI or vice versa. The final PR must not claim full data reproducibility without immutable input snapshots.

## 7. Approval record

**What each existing approval actually binds to (checked against PR #18):**

| Approval | Review | Bound to | Scope it covers |
|---|---|---|---|
| A scope supplement | `5959122354` (A, APPROVED, `2026-11-18T15:00:01Z`) | commit **`3b60af18af12d645e19e7f4aaac40a81bd3dcba2`** (the initial v0.1 draft) | Base Stage 2 scope and direction: run-directory reservation (3 attempts, fail before Graph), one manifest after analysis + save choice, TC-ID mapping TC-04/05/11/13/14/15/19/20/21/23, the TC-23 `input_condensation_audit_note` sync, C owns `cli/run.py`, F owns CI |
| F formal test-plan + CI matrix approval | `5968062524` (F, APPROVED, `2026-11-19T01:41:23Z`) | commit **`e03b67d48114164494f7ef346f1e5602e2270c44`** | The v0.1 test design and CI matrix; the same TC-ID range; "serialization and write/promotion failure in TC-13/14" |
| F ownership/timing supplement | `5968754538` (F, COMMENTED, `2026-11-19T03:08:27Z`) | not a re-approval; a supplement to `5968062524` | Ownership split, write timing, no-Graph-change convergence, PR #21 baseline |

**What this revision changes, and therefore needs re-review:**

- The state-log contract (C1/C2): call chain, path consistency, registration only on a successful `record_decision()`, `shared_mutable` label, no `fsync` requirement — **not covered by the `3b60af1`/`e03b67d` approvals**, which predate it.
- `_offer_reports()` returning `list[Path]` with whole-save semantics (C3) — a new interface detail.
- `_artifact_references` taking both `results_dir` and `run_dir` (C4) — new.
- Live-report and `message_tool.log` write evidence (C5), and external-path omission (C6) — new.
- Reservation failure exception and CLI exit behaviour (C7) — specifies what A's approval left as "fail clearly".
- The latest TC-05 artifact rules include both per-section sets when their own write evidence exists; this replaces the earlier pending B set-choice question.

**Recorded decisions:**

- **A Stage 2 scope supplement:** Approved in PR #18 review `5959122354` (bound to `3b60af1`), `2026-11-18T15:00:01Z`
- **F formal Stage 2 test-plan and CI matrix approval:** Approved in PR #18 review `5968062524` (bound to `e03b67d`), `2026-11-19T01:41:23Z`; **continues to apply to the unchanged TC-ID mapping and CI matrix**, and is **not** an approval of this revision's new contract text
- **C/F ownership and timing confirmation:** PR #18 review `5968754538`
- **Latest A/F/C TC-05 artifact decisions:** Recorded in this v0.2-DRAFT update; both live and saved per-section sets are included when their own write evidence exists, with the saved set requiring whole-save success. No additional GitHub review identifier was supplied.
- **Plan update binding:** Base plan commit `c200512379fb38ddb9215cfb0bd71ea0d16aa241`; this update’s commit SHA is reported in PR #18.
- **A-confirmed implementation scope:** Completed normal CLI runs only; no Graph API change; legacy paths preserved; no public interface/schema/fingerprint/redaction broadening; artifact rules recorded here.
- **F-confirmed test boundaries:** Existing official IDs only; report-save and manifest-write failures kept separate; approved CI matrix; F owns test review and CI workflow changes. Formal approval of this revision’s added cases remains pending.
- **C ownership and remaining decisions:** C owns `cli/run.py` integration; C must document actual base SHA and exact file scope before implementation; C7 reservation failure is specified as `RunDirectoryUnavailable` converted to `typer.Exit(code=1)`.
- **Pending:** A's confirmation of the exact file scope; F's formal approval of this revised test plan.
- **PR #21 writer/TC-23 synchronization:** Merged at `69e91ff115694f3455196e6a4114d4fe653fbb06`
- **O6 CLI integration:** Merged at `e4b6f9ac625f39579635c840aed98ab8dfefdaf9` (PR #20)
- **Actual baseline at this revision:** `origin/main` `102511dd44ad8779a46e09cbefe50edb8a995b45`
- **Implementation status:** Not authorised; no implementation or CI result claimed
- **Reapproval:** Any material scope, expected-result, path, test-ID, Graph, or ownership change requires an updated plan and renewed approval before implementation.
