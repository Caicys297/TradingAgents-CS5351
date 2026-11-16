# O5 Macro News Filter — OpenCode Execution Plan (pre-code upload, v1.1-DRAFT)

**Owner:** Member E (O5). **Execution-plan reviewer:** Member A (registry `approval_roles.coding_agent_execution_plan`: "A reviews each scoped plan before first code edit").
**Companion:** [`O5-Test-Plan-precode-v1.1-DRAFT.md`](./O5-Test-Plan-precode-v1.1-DRAFT.md) — **F** reviews that one.
**Status:** DRAFT (revision **v1.2**). **NOT approved.** **No code written; no project tests or benchmarks run; no commands run beyond the inspections in §1.**
> **v1.2 review-revision note.** This file keeps its v1.1 filename so it replaces the same path in PR #3 and keeps stable links; **v1.2 is the active document revision**. v1.2 responds to A's review of PR #3 commit `85ffc242b10ebd242501ef61e7c7b95deee0a9d2` and rebases active baseline references on the **merged** baseline `4f87e29f7a52842dba8272071d2a4a1b527def10`. Anything not amended here stands as in the v1.1 text.

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

**Region 2 — retrieval-loop exception and evidence handling.** Wrap the existing loop `:169-189` in a `try/except/finally` that preserves its body byte-for-byte (queries, `news_count`, fuzzy, window filter, title dedup, early stop at `:188`). The `except` path records the failure kind for the evidence variant and re-raises or lets the caller's exception propagate; the `finally` emits the ordered evidence. `yf_retry` already converts non-rate-limit errors into `VendorUnavailableError` inside the loop, so the wrapper does not change retry behaviour.

**Region 3 — selection, before the final slice/format.** Between the loop end (`:189`) and `_format_articles(in_window_news[:limit])` (`:191`), normalize the collected records and call the selector; then format the selector's `selected` list instead of `in_window_news[:limit]`.

**Region 4 — post-selection empty handling.** Keep the existing `:193-199` coverage-gap branch for an empty pool; add the filtered-to-empty and suppression branches according to Interface §5.

### 3.2 Ownership table

| Item | Owner | Status |
|---|---|---|
| Selector module + logic (new file) | **E** | proposed |
| Adapter Regions 1–4 inside `news.py` | **C** (shared vendor file per `development_contract.integration_owner`) with E providing the module call; **A** reviews | proposed |
| Evidence schema and emission content | E | proposed |
| O2 run-directory context plumbing | **C** | unconfirmed |
| Config keys (`o5_*`) or module constants | **A/C** | unconfirmed |
| `test/offline/conftest.py` (already exists) | **F** owns; E must not edit | verified present |
| CI wiring / gates | **F** | partially existing |

**Proposed, unimplemented signatures:** `select_macro_news(request) -> result` (name/shape Pending C), an O5 JSONL sink `emit(evidence)` with a run-scoped path. **No agreement is asserted** where none exists.

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

**Modify:**
9. `tradingagents/dataflows/vendors/yahoo/news.py` — **only** the private adapter insertion plus the evidence hook; no change to `_extract_article_data`, `_format_articles`, query strings, fuzzy matching, `news_count`, early stop.

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
6. **Adapter wiring** (insertion + K=0 zero-fetch + sink). Add **A** cases (`test_o5_macro_news_integration.py`) including **T03a-A** and T13c-D/T13c-R.
7. **Regression** (`test_o5_regression.py`): RT-1..RT-4; adapt inherited macro-news tests only where owner review agrees.
8. **Fixtures:** copy DEV20 (`a6f65bf2…`) and the four T17 artifacts (hashes in the test plan §7) into `test/offline/fixtures/o5/`.
9. **T17 harness:** implement `test_o5_macro_news_perf.py` with the boundary in test plan §7 (load outside; selector inside; assertions outside); runner ubuntu-latest/Py3.11 per the registry; 100 ms unverified.
10. **Hand to C/F:** C integrates the shared `news.py` regions; F confirms the existing CI collection covers the new O5 modules (collection is already configured; F only verifies the new files are picked up).
11. **PR review.**

---

## 7. Plan-level review questions

1. **A:** PB-1 target branch/SHA; PB-2 governance readiness.
2. **C:** seams in §5; whether `o5_*` config keys are added.
3. **F:** whether the base already provides `test/offline/` isolation, so a new conftest is unnecessary.
4. **F/E:** T17 runner realization and 100 ms acceptance; relaxation requires a registry decision.

---

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

## 10a. A/F review-comment mapping (v1.2)

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

## 11. Status

**DRAFT v1.1. Not approved. No code, no tests, no commands executed.** All proposed interfaces are unimplemented and pending C. **F reviews the test plan; A reviews this execution plan.**
