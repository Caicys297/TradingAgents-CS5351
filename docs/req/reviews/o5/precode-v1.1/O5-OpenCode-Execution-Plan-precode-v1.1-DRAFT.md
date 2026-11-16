# O5 Macro News Filter — OpenCode Execution Plan (pre-code upload, v1.1-DRAFT)

**Owner:** Member E (O5). **Execution-plan reviewer:** Member A (registry `approval_roles.coding_agent_execution_plan`: "A reviews each scoped plan before first code edit").
**Companion:** [`O5-Test-Plan-precode-v1.1-DRAFT.md`](./O5-Test-Plan-precode-v1.1-DRAFT.md) — **F** reviews that one.
**Status:** DRAFT. **NOT approved.** **No code written; no project tests run; no commands run beyond the read-only inspections in §1.**

---

## 1. Inspections actually performed (evidence for this plan)

| Check | Result |
|---|---|
| `git rev-parse HEAD` / `git status --short --branch` | `970a9ea…` on `main`; working tree clean |
| `git cat-file -t 3cb83f3…` | `commit` (already present locally) |
| Registry files read | `requirements.yaml`, `product-requirements.yaml`, `req-schema.json`, `A-Requirements-Decisions.md`, `Team-O1-O6-Test-Case-Catalog-v2.0-DRAFT.md`, DEV20 fixture, `docs/test-approvals/TEMPLATE.md` |
| Selector module | `tradingagents/dataflows/macro_news_filter.py` **absent** |
| `src/`, `test/offline/` | only `.gitkeep` each |
| Packaging | `pyproject.toml:51-52` includes only `tradingagents*`, `cli*` |
| Repo instructions | no `AGENTS.md`; `.agent/` only `.gitkeep`; `.opencode/` tooling only |

**Git-state wording (corrected):** populating the registry commit earlier fetched Git objects and wrote `.git/FETCH_HEAD` — **Git metadata changed**. `main`, `origin/main`, `HEAD`, the index and all tracked files are unchanged. No pull/merge/checkout/branch creation occurred.

---

## 2. Base revision and pre-code checks

- **Authority base:** `3cb83f3ff8fddb780b9c9c7fb2a6fd930b3395cf`.
- **Implementation base:** whatever branch A names. `A-Requirements-Decisions.md` records **the author's** checkout as `feature/o1-sma-guard`; that is context, **not** a required branch for E and **not** a registry contradiction. **Pre-code check PB-1 (A):** confirm the target branch and its SHA, and confirm it contains the registry at `3cb83f3` (or state which registry revision is authoritative if PR #2 is merged differently).
- **Pre-code check PB-2:** confirm `docs/test-approvals/TEMPLATE.md` is present on the implementation base and that the governance record exists; an empty template is not approval.

---

## 3. Proposed boundaries

**Existing code (today, at `970a9ea`):** `get_global_news_yfinance` (`vendors/yahoo/news.py:137-201`), `_extract_article_data` (`:16-54`), `_format_articles` (`:75-84`), `route_to_vendor` (`router.py:200-297`), `yf_retry` (`vendors/yahoo/common.py:64-91`), `get_global_news` tool (`agents/tools.py:194-215`).

**Proposed, unimplemented, pending C:**

| Item | Proposed | Note |
|---|---|---|
| Selector module | `tradingagents/dataflows/macro_news_filter.py` (registry `o5.selector_module`) | pure, no I/O, no LLM |
| Selector entry | `select_macro_news(request) -> result` | name/shape Pending C |
| Adapter | private insertion inside `get_global_news_yfinance` between the loop end and `_format_articles(...[:limit])` | preserves public `str` |
| Evidence sink | O5 JSONL writer → `<O2 run dir>/o5_evidence.jsonl` | C seam (§7 Q3) |
| Config keys | `o5_rules_version`, `o5_requested_topics`, `o5_limit` | A/C decision (§7 Q3) |

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
11. `test/offline/conftest.py` — **must not be created or replaced** until the eventual implementation base is checked and F coordinates it (§6, step 2).

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
2. **Base verification + conftest coordination:** confirm PB-1/PB-2; inspect the implementation base's existing `test/` layout and `pyproject.toml` collection; **do not create/replace `test/offline/conftest.py`** until F confirms it and the base is checked. If the base already provides isolation, reuse it instead of adding a second conftest.
3. **Selector skeleton** (pure): request/result types, `rules_version` validation, canonical `candidate_id`, ordering helpers.
4. **Selector logic:** validation precedence → ID registration → title/timestamp/window → classification → buckets/round-robin. Add **S** cases to `test_o5_macro_news_filter.py`, including **T03c (A-1)** and **T12 (A-2)**.
5. **Evidence builder** + fault-injection seams. Add **B** cases (`test_o5_evidence_builder.py`) and **I** cases (`test_o5_invariants.py`), keeping I6–I10 parameter tables intact.
6. **Adapter wiring** (insertion + K=0 zero-fetch + sink). Add **A** cases (`test_o5_macro_news_integration.py`) including **T03a-A** and T13c-D/T13c-R.
7. **Regression** (`test_o5_regression.py`): RT-1..RT-4; adapt inherited macro-news tests only where owner review agrees.
8. **Fixtures:** copy DEV20 (`a6f65bf2…`) and the four T17 artifacts (hashes in the test plan §7) into `test/offline/fixtures/o5/`.
9. **T17 harness:** implement `test_o5_macro_news_perf.py` with the boundary in test plan §7 (load outside; selector inside; assertions outside); runner ubuntu-latest/Py3.11 per the registry; 100 ms unverified.
10. **Hand to C/F:** C integrates shared wiring; F wires CI collection of `test/offline/`.
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

`REQ-O5-10` **specifies** ubuntu-latest/Python 3.11, 5 warmups, 30 measured runs, nearest-rank p95 ≤ 100 ms. That specification is distinct from: F/E approval of this plan (Pending), runner realization (not done), and actual measurements (none). A proposed relaxation must be an explicit registry decision.

---

## 10. Completion criteria

Approved cases pass with the T17 correctness gate; no added retrieval/LLM calls; public `str` and ticker output unchanged; evidence JSONL emitted per schema for every exercised path; sink failure does not corrupt results; approval record filled with real times; applicable CI gates block on failure.

## 11. Status

**DRAFT v1.1. Not approved. No code, no tests, no commands executed.** All proposed interfaces are unimplemented and pending C. **F reviews the test plan; A reviews this execution plan.**
