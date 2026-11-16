# O5 Macro News Filter — OpenCode Execution Plan (pre-code upload, v1.1-DRAFT)

**Owner:** Member E (O5). **Execution-plan reviewer:** Member A (registry `approval_roles.coding_agent_execution_plan`: "A reviews each scoped plan before first code edit").
**Companion:** [`O5-Test-Plan-precode-v1.1-DRAFT.md`](./O5-Test-Plan-precode-v1.1-DRAFT.md) — **F** reviews that one.
**Status:** DRAFT (revision **v1.3**). **NOT approved.** **No code written; no project tests or benchmarks run; no commands run beyond the inspections in §1.**
> **v1.3 review-revision note (supersedes the v1.2 note).** This file keeps its v1.1 filename so it replaces the same path in PR #3 and keeps stable links; **v1.3 is the active document revision**.
> v1.3 responds to A's review of commit `27c8e4be0f0e8b1af4611ae29a86ac106fd00967` and changes: **ownership** (§3.2 — E implements the O5 private integration in `news.py`), the **evidence lifecycle** (§3.4, replacing the loop-`finally` emission), the **`rules_version` blocking decision** (§7), and **T17 digest references** (§8). The merged baseline `4f87e29f7a52842dba8272071d2a4a1b527def10` and v1.2's collection findings are unchanged.

---

## 1. Inspections actually performed (v1.2)

| Check | Result |
|---|---|
| Local `HEAD` / status | `970a9eab6b4b3a819dc22f417a4df1e7eaa73d04` on `main`; working tree clean |
| Remote branch tips (`git ls-remote --heads origin`) | `main` = **`4f87e29f7a52842dba8272071d2a4a1b527def10`**; `docs/o5-precode-review-v1.1` = `85ffc242b10ebd242501ef61e7c7b95deee0a9d2`; also `3cb83f3`, `docs/requirements-review-20261116`, `feature/f-ci-regression-phase1` |
| PR #2 | **Merged.** F's identified baseline `4f87e29` resolves to `4f87e29f7a52842dba8272071d2a4a1b527def10`. (Branch `refs/heads/3cb83f3` still exists on the remote, which is why the old SHA looked like a tip.) |
| Fetches | `git fetch --no-tags --depth=1 origin 4f87e29…` and `… origin 85ffc24…` — **objects and `FETCH_HEAD` only**. Local `main`, `HEAD`, index and tracked files unchanged. The shallow tracking ref `origin/main` was **not** advanced, so the merged baseline was read by explicit SHA. **Git metadata changed** (objects + `FETCH_HEAD`). |
| `docs/req/` @ `4f87e29` | present (same file set as before, plus `docs/req/reviews/o5/precode-v1.1/`) |
| `pyproject.toml` @ `4f87e29` | `testpaths = ["tests", "test/offline"]`, SHA-256 `cd3f44217eadcb8b945f68b70d7f8391f87ce6b3e491728a5832611804617f9d` |
| `test/offline/conftest.py` @ `4f87e29` | **exists**, 1,206 bytes, SHA-256 `abd1c54e8170ec90c09b8ac31a1b0b09401a20502e3c145c32f9ff11702fa2d8` |
| `tradingagents/dataflows/vendors/yahoo/news.py` @ `4f87e29` | byte-identical to `970a9ea` (8,529 bytes) |
| Selector module | `tradingagents/dataflows/macro_news_filter.py` **still absent** |
| Repo instructions | no `AGENTS.md`; `.agent/` only `.gitkeep`; `.opencode/` tooling only |

**Collection infrastructure already exists** on the merged baseline; the v1.1 claim that F must add initial collection is withdrawn. O5's own collection/isolation is **untested** (no O5 module, no run).

## 2. Base revision (v1.2)

- **Reviewed/merged baseline:** `4f87e29f7a52842dba8272071d2a4a1b527def10` (PR #2 merged; `refs/heads/main` at inspection time).
- **Current remote `main`:** the same SHA at inspection. If it moves later, it is a **different** revision; the baseline is the SHA above, not "whatever main is".
- **Implementation base:** the branch A names for the feature. **PB-1 (A):** confirm the implementation base SHA and that it contains the registry at `4f87e29` (or state the authoritative registry revision). The `feature/o1-sma-guard` line in `A-Requirements-Decisions.md` is the **author's authoring context**, not E's required branch and not a registry contradiction.
- **PB-2:** confirm `docs/test-approvals/TEMPLATE.md` and governance readiness on that base; an empty template is not approval.
- **PB-3 (new in v1.2):** re-check the base before implementation, because this package was authored at `970a9ea` while the baseline is `4f87e29`. Confirm `testpaths`, the existing `test/offline/conftest.py` and `news.py` are as recorded here.

## 3. Proposed boundaries and the `news.py` change surface (v1.2)

Existing code at `4f87e29` (byte-identical to `970a9ea`), with the inspected locations:

| Existing function | Location | Role |
|---|---|---|
| `_extract_article_data` | `vendors/yahoo/news.py:16-54` | article extraction (nested/flat) |
| `_search_news` | `news.py:57-72` | Yahoo search fallback (ticker path) |
| `_format_articles` | `news.py:75-84` | output formatter |
| `get_news_yfinance` | `news.py:87-134` | ticker news (must not change) |
| `get_global_news_yfinance` | `news.py:137-201` | global news: config `:155-160`, window `:162-164`, query loop `:169-189`, early stop `:188`, `_format_articles(...[:limit])` `:191`, empty handling `:193-199` |
| `route_to_vendor` | `router.py:200-297` | vendor chain; `DATA_UNAVAILABLE` at `:265-266` |
| `yf_retry` | `vendors/yahoo/common.py:64-91` | retry + `VendorUnavailableError` at `:85-87,88-91` |
| `get_global_news` tool | `agents/tools.py:194-215` | public `str` entry |

### 3.1 The four `news.py` change regions (precise)

**Region 1 — request validation and K=0, before retrieval.** Immediately after the config defaults are read (`:155-160`) and before `start_dt`/the loop; validate `limit` (int ≥ 0, not bool) and resolve `rules_version` from config. If `limit == 0`, return the LIMIT_ZERO result **without** calling `yf.Search`. Today no such block exists; lines `:162-201` run unconditionally.

**Region 2 — retrieval-loop exception and evidence handling.** Wrap the existing loop `:169-189` in a `try/except` that preserves its body byte-for-byte (queries, `news_count`, fuzzy, window filter, title dedup, early stop at `:188`). The `except` path builds and emits the single failure event (`V-PARTIAL` when candidates were collected, else `V-VENDOR` from the typed cause) and then re-raises so the existing error path is unchanged. **`finally` performs cleanup only and emits nothing** (`V1.3`). `yf_retry` still converts non-rate-limit errors into `VendorUnavailableError` inside the loop; retry behaviour is unchanged and retries are not evidence events.

**Region 3 — selection, before the final slice/format.** Between the loop end (`:189`) and `_format_articles(in_window_news[:limit])` (`:191`), normalize the collected records and call the selector; then format the selector's `selected` list instead of `in_window_news[:limit]`.

**Region 4 — post-selection empty handling.** Keep the existing `:193-199` coverage-gap branch for an empty pool; add the filtered-to-empty and suppression branches according to Interface §5.

### 3.2 Ownership table (v1.3, A's requested direction)

| Item | Owner | Status |
|---|---|---|
| **O5 private adapter integration inside `tradingagents/dataflows/vendors/yahoo/news.py`** (regions 1-4) | **E** | **A's requested direction.** No existing team governance assigns this file to C; the v1.2 claim is withdrawn. Execution-plan approval still Pending. |
| Selector module `tradingagents/dataflows/macro_news_filter.py` + classification/allocation | **E** | proposed |
| **O2 run-directory handoff** into the evidence sink | **C confirms** | **unconfirmed interface detail** |
| C-owned shared integration, where applicable (`default_config.py` `o5_*` keys; any `cli/run.py` / graph wiring) | **C** | unconfirmed; E does not edit these |
| `docs/req/*` registry text | **B/A** | not E's |
| CI workflows, `test/offline/conftest.py` | **F** | E must not edit |
| Invariant-failure wording / negation-flag field name | **D** | unconfirmed |

**Distinction A asked for:** A's ownership direction (E owns the `news.py` integration) is **separate from** (a) C's still-unconfirmed O2 handoff and (b) A's approval of the whole execution plan. None of the three implies the others.

### 3.4 Evidence lifecycle (v1.3, A3) — replaces loop-`finally` emission

The v1.2 text said terminal evidence is emitted from the retrieval loop's `finally`. **Withdrawn** — at loop exit no selection has happened. The authoritative path plan is the Test Plan's §4.6 table (P-K0, P-OK, P-PARTIAL, P-VENDOR, P-INVARIANT, P-INVALID-REQ) plus its pseudocode. Implementation consequences here:

| Path | Emit at | Nothing else may emit |
|---|---|---|
| K=0 | region 1, before `yf.Search` | no success event |
| success | region 4, **after** selector + invariant validation + final result | no `finally` emission |
| partial/full retrieval failure | region 2 except path, with candidate/query counts and the exception | no second event on re-raise; router emits none |
| invariant failure | region 4 after the check, result suppressed | no `V-SELECTED` |
| invalid request | region 1, zero retrieval | — |

`finally` is cleanup only. Exactly-once is per **invocation** of `get_global_news_yfinance` (not per query, not per `yf_retry` retry). T13c-D/T13c-R still each emit exactly one `V-PARTIAL` and no `V-VENDOR`.

### 3.3 How the O2 run directory reaches the evidence sink

Registry `development_contract.o5.evidence_path` = "same O2 run directory/o5_evidence.jsonl, when a CLI run context exists". O2's contract reserves `<results_dir>/<safe_ticker>/<analysis_date>/runs/<uuid4>/` at run start. The proposed route (unconfirmed, C):

1. O2 reserves the run directory and exposes it in run scope (O2's `run_dir`).
2. The adapter reads the active run context (a contextvar or `run_config`-carried value, mirroring how `_run_config` already scopes config at `dataflows/config.py:13`) and builds `<run_dir>/o5_evidence.jsonl`.
3. With no CLI run context, no path exists: the sink logs `SINK_FAILED` and the honest string is still served.

**This is a proposal; the mechanism must be confirmed by C and is not implemented.**

---

## 4. Exact allowed files (proposed)

**Create:**
1. `tradingagents/dataflows/macro_news_filter.py` — selector.
2. `test/offline/test_o5_macro_news_filter.py` — S cases.
3. `test/offline/test_o5_evidence_builder.py` — B cases (I9-a etc.).
4. `test/offline/test_o5_macro_news_integration.py` — A cases (T13*, T15).
5. `test/offline/test_o5_invariants.py` — I cases.
6. `test/offline/test_o5_regression.py` — RT cases.
7. `test/offline/test_o5_macro_news_perf.py` — **T17 harness** (see §6; must have an implementation step, not just a command).
8. `test/offline/fixtures/o5/` — copies of DEV20 and the four T17 artifacts, with hashes.

**Modify (E-owned, v1.3):**
9. `tradingagents/dataflows/vendors/yahoo/news.py` — the O5 private integration (regions 1-4: pre-fetch validation + K=0, retrieval-loop failure handling, selection before the final slice, post-selection empty/invariant branches). **Owner: E** per A's direction. No change to `_extract_article_data`, `_format_articles`, query strings, fuzzy matching, `news_count`, or early stop.

**Conditionally modify (not yet approved):**
10. `default_config.py` — only if the `o5_*` config keys are adopted (C-owned).
11. `test/offline/conftest.py` — **verified to already exist at `4f87e29`** (1,206 bytes). E must **not** create or replace it. Any O5-specific per-test config/cache reset is a **separate, F-coordinated** change and is not in this allowed list.

**Not allowed:** `router.py`, `common.py`, `date_window.py`, `agents/tools.py`, `docs/req/*`, `docs/test-approvals/*`, CI workflows, `pyproject.toml`, `cli/run.py`, `graph/trading_graph.py`.

---

## 5. Required seams (identified, not silently expanded)

| Seam | Needed for | Owner |
|---|---|---|
| Pre-fetch request validation + K=0 zero-fetch short-circuit before `yf.Search` | T10f/T10g/T10h/T10i/T10j, **T03a-A** | C (hook A) |
| Retrieval-loop wrapper (try/except/finally) | T13a–T13d, V-PARTIAL/V-VENDOR evidence | C (hook B) |
| Invariant check + suppression + "filter-unavailable" | I1–I3, I11 | C/D |
| Evidence sink invocation on every exit path | I5, T13*, T03a-A | C |
| O2 run-directory context | evidence path | C (Q3) |

If any seam is missing, the affected cases are **blocked**, not dropped; the allowed-file list is not expanded without re-approval.

---

## 6. Ordered steps (planned)

1. **Gate check:** record F's test-plan approval and A's execution-plan approval (version, IDs, files, exclusions). Stop if absent.
2. **Base verification:** confirm PB-1/PB-2/PB-3. At `4f87e29`, `testpaths` already includes `test/offline` and `test/offline/conftest.py` already blocks the network; **reuse it, do not create a second one**. If the implementation base differs from `4f87e29`, re-verify and stop if it lacks collection or isolation.
3. **Selector skeleton** (pure): request/result types, `rules_version` validation, canonical `candidate_id`, ordering helpers.
4. **Selector logic:** validation precedence → ID registration → title/timestamp/window → classification → buckets/round-robin. Add **S** cases to `test_o5_macro_news_filter.py`, including **T03c (A-1)** and **T12 (A-2)**.
5. **Evidence builder** + fault-injection seams. Add **B** cases (`test_o5_evidence_builder.py`) and **I** cases (`test_o5_invariants.py`), keeping I6–I10 parameter tables intact.
6. **Adapter wiring by E** in `news.py` (K=0 zero-fetch + failure handling + post-selection emission). Add **A** cases (`test_o5_macro_news_integration.py`) including **T03a-A** and T13c-D/T13c-R, plus the §3.4 lifecycle assertions (no event from `finally`).
7. **Regression** (`test_o5_regression.py`): RT-1..RT-4; adapt inherited macro-news tests only where owner review agrees.
8. **Fixtures:** copy DEV20 (`a6f65bf2…`) and the four T17 artifacts (hashes in the test plan §7) into `test/offline/fixtures/o5/`.
9. **T17 harness:** implement `test_o5_macro_news_perf.py` with the boundary in test plan §7 (load outside; selector inside; assertions outside); runner ubuntu-latest/Py3.11 per the registry; 100 ms unverified.
10. **Hand to C/F:** C integrates the shared `news.py` regions; F confirms the existing CI collection covers the new O5 modules (collection is already configured; F only verifies the new files are picked up).
11. **PR review.**

---

## 7. Blocking decisions and review questions (v1.3)

**BLOCKING (A1) — canonical `rules_version`.** `requirements.yaml` carries both `o5-rules-v1.1` (inside `REQ-O5-01.statement`) and `o5-rules-v1.1-draft` (`development_contract.o5.rules_version`); the DEV20 fixture repeats `-draft`. Verified at `4f87e29` **and** the PR head `27c8e4b`; no A/B resolution exists. A/B must select one literal and update: `requirements.yaml` statement, `development_contract.o5.rules_version`, the DEV20 fixture's `rules_version` (bytes → `dev20_fixture_sha256` change), the `o5_rules_version` config value, and every active plan/evidence example. **E proposes `o5-rules-v1.1`**; it is not approved, and this package changes no requirement text and no fixture byte.

Other open questions:

1. **A:** PB-1/PB-2/PB-3 base checks on the implementation branch; PB-3 is required because this package was authored at `970a9ea` and the baseline is `4f87e29`.
2. **C:** O2 run-directory handoff into the sink; whether `o5_*` keys enter `default_config.py` or stay module constants.
3. **D:** exact "filter-unavailable" string; negation-flag field name.
4. **C7:** whether a `V-VENDOR` should accompany `V-PARTIAL` (the plans preserve exactly one `V-PARTIAL`).
5. **F:** per-invariant case mapping; any extra per-test config/cache reset.
6. **F/E:** T17 runner realization and 100 ms.

## 8. Planned verification commands (NOT executed)

```
pytest --collect-only -q tests test/offline
pytest -q test/offline/test_o5_macro_news_filter.py
pytest -q test/offline/test_o5_evidence_builder.py
pytest -q test/offline/test_o5_macro_news_integration.py
pytest -q test/offline/test_o5_invariants.py
pytest -q test/offline/test_o5_regression.py
pytest -q test/offline/test_o5_macro_news_perf.py
pytest -q
ruff check test/offline tradingagents/dataflows/macro_news_filter.py
```

Every module named above is in the §4 create-list, so each command has a corresponding implementation step (§6 steps 4–9). At the time of this plan **none of these modules exists**, so none is runnable as an O5 check. I did not run them.

---

## 9. Acceptance condition vs approval vs measurement

`REQ-O5-10` **specifies** ubuntu-latest/Python 3.11, 5 warmups, **30 measured calls**, nearest-rank p95 ≤ 100 ms. That specification is distinct from F/E approval of this plan (Pending), runner realization (not done) and actual measurements (none). **If any of the 30 measured selector calls returns an incorrect result or raises an unexpected exception, T17 fails overall**; the sample is not discarded or replaced. A relaxation requires an explicit registry decision.

---

## 10. Completion criteria

Approved cases pass with the T17 correctness gate; no added retrieval/LLM calls; public `str` and ticker output unchanged; evidence JSONL emitted per schema for every exercised path; sink failure does not corrupt results; approval record filled with real times; applicable CI gates block on failure.

## 9a. T17 digest references (v1.3, A4)

This plan does not hard-code manifest/handoff digests. The authoritative values are in [`README.md`](./README.md) and are computed from actual bytes:

| File | Value source |
|---|---|
| fixture | SHA-256 `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0` (bytes unchanged) |
| expected results | SHA-256 `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6` (bytes unchanged) |
| handoff | digest recorded **in the manifest**; also in README |
| manifest | digest recorded **in README only** (manifest does not hash README) |

**One-way:** manifest → {fixture, expected, handoff}; handoff → manifest by filename; README/plans → manifest digest. No cycle.

## 10a. A/F review-comment mapping (v1.2 + v1.3)

| Comment | Revised section |
|---|---|
| A1 merged baseline `4f87e29` | §1, §2 (§2 records the full SHA) |
| A2 PR #2 merged | §1, §2; README |
| A3 rules-version mismatch unresolved | §7 Q-list (Execution) + Test Plan §8 D-02/§9 Q3 |
| A4 news.py regions, ownership, O2 path | §3.1, §3.2, §3.3 |
| A5 collection already exists on main | §1, §4 item 11, §6 step 2 |
| F6 verification mapping | `O5-Test-Plan-precode-v1.1-DRAFT.md` §3 |
| F7 I9-a vs I9-b layers | Test Plan §4.2, §4.3 |
| F8 invariant reconciliation | Test Plan §4.5 |
| F9/F10 T17 hash integrity | `README.md`, `O5-T17-F-Handoff-v1-DRAFT.md`, `O5-T17-Manifest-v1-DRAFT.json`, Test Plan §7 |
| F11 runner/threshold/fail-overall | Test Plan §7, Execution §9 |
| **A1 (v1.3)** canonical `rules_version` | Test Plan §0a, §8 D-02, §9 Q3; Execution §7 |
| **A2 (v1.3)** ownership of `news.py` | Execution §3.2, §4 item 9; Test Plan §0a |
| **A3 (v1.3)** evidence lifecycle | Test Plan §4.6, §9b; Execution §3.4 |
| **A4 (v1.3)** T17 hashes | Test Plan §7; Execution §9a; `README.md` |

## 11. Status

**DRAFT v1.1. Not approved. No code, no tests, no commands executed.** All proposed interfaces are unimplemented and pending C. **F reviews the test plan; A reviews this execution plan.**
