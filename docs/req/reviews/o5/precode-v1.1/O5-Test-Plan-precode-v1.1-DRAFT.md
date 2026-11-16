# O5 Macro News Filter — Test Plan (pre-code upload, v1.1-DRAFT)

**Owner:** Member E (O5). **Test-plan reviewer:** Member F (registry `development_contract.approval_roles.O5_test_plan` → "F reviews").
**Execution-plan reviewer:** Member A ("A reviews each scoped plan before first code edit").
**Status:** DRAFT for review (revision **v1.3**). **NOT approved. No software test or benchmark has been run. No project test code exists.**
> **v1.3 review-revision note (supersedes the v1.2 note).** This file keeps its v1.1 filename so it replaces the same path in PR #3 and keeps stable links; **v1.3 is the active document revision**.
> v1.3 responds to A's review of PR #3 commit `27c8e4be0f0e8b1af4611ae29a86ac106fd00967` and adds: a **blocking canonical `rules_version` decision** (§8 D-02), **revised ownership** (§0a), the **evidence lifecycle path table + pseudocode** (§4.6) and **T17 hash consistency across all nine files** (§7).
> v1.2's changes (merged baseline `4f87e29f7a52842dba8272071d2a4a1b527def10` rebase, verification remap, I9-b layer, INV mapping, T17 one-way hashing) remain in force. Everything else stands as written in this file's v1.1 text.
**Development authority for this review:** `docs/req/requirements.yaml` and `docs/req/A-Requirements-Decisions.md` at **merged baseline `4f87e29f7a52842dba8272071d2a4a1b527def10`** (PR #2 **merged**; this is F's identified baseline, full SHA resolved here). It is distinct from the current remote `main` tip if that tip later moves. Neither the registry nor this document is a test-plan or execution-plan approval.

---

## 0. Package contents and how to read them

| File | Role |
|---|---|
| `O5-Test-Plan-precode-v1.1-DRAFT.md` | **This plan (normative for review).** |
| `O5-OpenCode-Execution-Plan-precode-v1.1-DRAFT.md` | Companion execution plan (A's review). |
| [`O5-Detailed-Test-Cases-Reference-r2.md`](./O5-Detailed-Test-Cases-Reference-r2.md) | **Historical supporting reference**: full T01–T20, I1–I12, RT-1..RT-4, I6–I10 parameter tables. |
| [`O5-Interface-Reference-r2.md`](./O5-Interface-Reference-r2.md) | **Historical supporting reference**: evidence schema (Interface §4, 4.1, 4.2, 4.3), hooks, sink. |
| [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](./O5-T17-Perf-Fixture-1000-v1-DRAFT.json) | T17 input fixture (byte-identical copy). |
| [`O5-T17-Expected-Results-v1-DRAFT.json`](./O5-T17-Expected-Results-v1-DRAFT.json) | T17 expected results (byte-identical copy). |
| [`O5-T17-Manifest-v1-DRAFT.json`](./O5-T17-Manifest-v1-DRAFT.json) | T17 manifest (byte-identical copy). |
| [`O5-T17-F-Handoff-v1-DRAFT.md`](./O5-T17-F-Handoff-v1-DRAFT.md) | T17 handoff (byte-identical copy). |

**Reading rule:** the two `*-r2.md` files are the detailed case sources. This plan **amends** them only in §5. Where this plan and an r2 reference disagree **outside** §5, treat it as an error in this plan to be reported, not as license to pick either — there is exactly one contract, amended once, in §5.

---

## 0a. Ownership direction and canonical `rules_version` (v1.3, A's review)

**Ownership (revised).** A's requested direction is that **E implements the O5 private integration in `tradingagents/dataflows/vendors/yahoo/news.py`**. No existing team governance assigns that file to C; the v1.2 text implied C owned it and is **corrected here**. What stays with C is narrower and explicitly conditioned:

| Item | Owner | Status |
|---|---|---|
| O5 private adapter integration inside `vendors/yahoo/news.py` (regions 1-4) | **E** | A's requested direction; final execution-plan approval still Pending |
| Selector module + classifier + allocation | E | proposed |
| **O2 run-directory handoff** into the evidence sink | **C confirms** | **unconfirmed interface detail** |
| Other C-owned shared integration, where applicable (e.g. `default_config.py` `o5_*` keys, any `cli/run.py` or graph wiring) | **C** | unconfirmed; E does not touch those files |
| `docs/req/*`, CI workflows, `test/offline/conftest.py` | B/A, F, F | not E's |

This separation matters: A's ownership direction is **not** approval of the execution plan, and C's O2 handoff is **not** resolved by it.

**Canonical `rules_version` — ONE BLOCKING DECISION (A1).** Inspected at `4f87e29` and on the PR head `27c8e4b`: `docs/req/requirements.yaml` contains **both**

- `REQ-O5-01.statement` → "…using O5 rules version **`o5-rules-v1.1`**…", and
- `development_contract.o5.rules_version` → **`"o5-rules-v1.1-draft"`**,

and `docs/req/O5-Dev20-Fixtures-v0.5.3-DRAFT.json` carries `"rules_version": "o5-rules-v1.1-draft"` (SHA-256 `a6f65bf2…` unchanged). **No A/B resolution exists in any inspected revision.** Therefore:

> **BLOCKING:** A/B must choose the canonical literal and synchronize it across (a) `requirements.yaml` `REQ-O5-01.statement`, (b) `requirements.yaml` `development_contract.o5.rules_version`, (c) `docs/req/O5-Dev20-Fixtures-v0.5.3-DRAFT.json` `rules_version` (and any `expected`/label metadata that repeats it), (d) the `o5_rules_version` config value used by the adapter, (e) every active plan and evidence example that prints the literal, **before any coding**.

**E's proposal:** `o5-rules-v1.1`. It is **not approved**, and this package does **not** change any authoritative requirement text or any fixture byte. The `-draft` values are **historical/provisional**, not approved implementation defaults; where the plans print them they are marked provisional. Changing the fixture literal would change the fixture bytes and therefore `dev20_fixture_sha256`, which is itself a separate registry edit — hence the decision must land before code.

---

## 1. What was actually inspected

| Item | Method | Result |
|---|---|---|
| Local HEAD / status | `git rev-parse HEAD`, `git status --short --branch` | `970a9ea…` on `main`, working tree clean |
| Registry revision present | `git cat-file -t 3cb83f3…` | `commit` (already present locally) |
| Registry files read | `git cat-file blob 3cb83f3:docs/req/...` | `requirements.yaml`, `product-requirements.yaml`, `req-schema.json`, `A-Requirements-Decisions.md`, `Team-O1-O6-Test-Case-Catalog-v2.0-DRAFT.md`, `O5-Dev20-Fixtures-v0.5.3-DRAFT.json`, `docs/test-approvals/TEMPLATE.md` |
| Team DEV20 fixture identity | blob bytes; SHA-256 | `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6`, 24,291 bytes — **identical** to the local r2 fixture and equal to the registry's `development_contract.o5.dev20_fixture_sha256` |
| Selector implementation | filesystem check | `tradingagents/dataflows/macro_news_filter.py` **absent**; `src/` and `test/offline/` contain only `.gitkeep` |
| Repository instructions | filesystem check | no `AGENTS.md`; `.agent/` only `.gitkeep`; `.opencode/` tooling only. Sole repository instruction is `docs/PROJECT_WORKSPACE.md` |

### 1.0 Merged baseline verification (v1.2)

| Item | Evidence |
|---|---|
| PR #2 status | **Merged** (A's review; the branch `refs/heads/3cb83f3` still exists on the remote, which is why the old SHA appeared as a branch tip) |
| Baseline identified as `4f87e29` | Resolved to full SHA `4f87e29f7a52842dba8272071d2a4a1b527def10` = `refs/heads/main` at inspection time |
| Reviewed PR #3 commit | `85ffc242b10ebd242501ef61e7c7b95deee0a9d2` = `refs/heads/docs/o5-precode-review-v1.1` |
| Registry bytes | `docs/req/requirements.yaml` @ `4f87e29` = 88,122 bytes, SHA-256 `365dd2d8bf12b138b19ce8d90e1103f19a48eed8c1fce38be4c2287219d8d5f9` |
| Delta vs `3cb83f3` | 31 diff lines: O6 unattributed/out-of-scope wording, O5 `REQ-O5-04/05/06/08` **fit_criterion** rewrites, `REQ-O5-05` verification gains **T13**, `REQ-O5-08` verification gains **T07**, O6 requirement/verification edits. **No O5 `statement`, `rules_version`, rule table or fixture hash changed.** |
| `development_contract.o5` | unchanged: `rules_version: "o5-rules-v1.1-draft"`, topic_order, matching_scope, negation, evidence_path, sink_failure, invariant_failure, zero_limit, `dev20_fixture_sha256 a6f65bf2…` |
| DEV20 fixture @ `4f87e29` | SHA-256 `a6f65bf271d9c9ac555f5d9f81cde5cbdb4ff526f46772c065cfe2653f0231f6` — identical to the local r2 fixture |
| `test/offline/` @ `4f87e29` | **`conftest.py` exists** (1,206 bytes, SHA-256 `abd1c54e8170ec90c09b8ac31a1b0b09401a20502e3c145c32f9ff11702fa2d8`) |
| `pyproject.toml` @ `4f87e29` | `testpaths = ["tests", "test/offline"]` (SHA-256 `cd3f44217eadcb8b945f68b70d7f8391f87ce6b3e491728a5832611804617f9d`) |
| `news.py` @ `4f87e29` | byte-identical to `970a9ea` (8,529 bytes); insertion points unchanged |
| Selector | `tradingagents/dataflows/macro_news_filter.py` **still absent** at `4f87e29` |

**Collection infrastructure (F requirement 5).** Collection of `test/offline/` is **already configured on the merged baseline**, and a sibling isolation `conftest.py` already exists there. The stale v1.1 claim that F must add initial collection is **withdrawn**. What remains untested is **O5's own** tests and isolation behaviour: no O5 test module exists, and nobody has yet executed a `test/offline/` O5 case. **A new base check is required before implementation** (§9 Q1).

**Historical statements** about PR #2 being unmerged remain only in the preserved v1.1 files and earlier drafts; they are labelled historical and are not active.

### 1.1 Git-state note (corrected wording)

An earlier draft called the requirements fetch "read-only". **Correction:** the fetch *did* populate Git objects and `.git/FETCH_HEAD`, i.e. **Git metadata changed**. What is guaranteed is narrower and accurate: the local `main` ref, `HEAD`, the index and every tracked working-tree file are **unchanged**. No pull, merge, checkout or branch creation occurred. **v1.2 fetches:** `git fetch --no-tags --depth=1 origin 4f87e29…` and `… origin 85ffc24…` were run for review; they added objects and rewrote `FETCH_HEAD` only. Local `main` remains at `970a9ea`, and the shallow `origin/main` tracking ref was **not** advanced, so it still points at `970a9ea` — the merged baseline was read by explicit SHA, not via `origin/main`.

---

## 2. Authority model for this review

The registry is the **proposed development authority** for review purposes. Its statements are of two kinds, and this plan separates them:

- **Selected policy direction (treated as decided for review):** scope (already-fetched Yahoo global news only), selector module path, `rules_version`, topic order, same-field clause-crossing matching, negation selectable-with-flag, evidence path in the O2 run dir, `SINK_FAILED` behaviour, "filter-unavailable" on invariant failure, K=0 returning `LIMIT_ZERO` without vendor fetch, the three rule tables, `config_allowlist` O5 keys, and `REQ-O5-10`'s acceptance condition. This plan does **not** reopen these merely because the older r2 drafts said "Pending".
- **Unresolved implementation seams (still genuinely open):** how the O2 run-directory context reaches the adapter, whether `o5_*` config keys are added to `default_config.py`, the exact "filter-unavailable" string, the negation-flag field name, and the CI wiring for `test/offline/`. These are listed in §9 and are **C/D/A/F** questions, not E policy choices.
- **Author's checkout context:** `A-Requirements-Decisions.md` records the authoring checkout as `feature/o1-sma-guard`. That is **A's recorded context**, not a required branch for E and **not** a registry contradiction. Implementation-base verification is a separate **pre-code check** owned by A (§9 Q1). The local checkout here is `main` @ `970a9ea`.

---

## 3. Traceability, re-derived against merged baseline `4f87e29` (v1.2)

The registry `verification` column below is copied from `4f87e29`. The r2/v1.1 mapping was built from the older `3cb83f3` and is superseded here.

| Requirement | type | Registry `verification` @ `4f87e29` | Cases in this plan | Change vs v1.1 |
|---|---|---|---|---|
| REQ-O5-01 | functional_behavior | T01, T08e, RT-3 | T01, T08a–i, RT-3 | unchanged |
| REQ-O5-02 | functional_behavior | T01, T02, T05, T06, T19, T20 | same | unchanged |
| REQ-O5-03 | functional_behavior | T03, T04, T13 | same | unchanged |
| REQ-O5-04 | functional_behavior | T12, I11 | T12, I11 | fit_criterion rewritten upstream; cases unchanged |
| REQ-O5-05 | functional_behavior | **T10, T11, T13** | **T10, T11, T13** | **added T13** (v1.2) |
| REQ-O5-06 | invariant | T14 | T14 | fit_criterion rewritten upstream; unchanged |
| REQ-O5-07 | quality_attribute | T01, T18 | T01, T18 | unchanged |
| REQ-O5-08 | cost | **T07, T10, T14, T16** | **T07, T10, T14, T16** | **added T07** (v1.2) |
| REQ-O5-09 | invariant | T15, RT-1, RT-4 | T15, RT-1, RT-2, RT-3, RT-4 | unchanged registry; this plan also runs RT-2/RT-3 because REQ-O5-01 cites RT-3 |
| REQ-O5-10 | performance | T17 | T17 | unchanged |
| INV-O5-01 | invariant | "O5 invariant tests I1-I12" | **I1, I3, I11** | per-invariant split amended (F requirement 8) |
| INV-O5-02 | invariant | "O5 invariant tests I1-I12" | **I1, I2, I3** | per-invariant split amended |
| INV-O5-03 | invariant | "O5 invariant tests I1-I12" | **I2, T11f** | per-invariant split amended |
| INV-O5-04 | invariant | "O5 invariant tests I1-I12" | **I4, T16** | per-invariant split amended |

**Why REQ-O5-07's `verification` (T01, T18) is not a contradiction with "add T07":** T07 is not a quality case; the merged registry attaches T07 to **REQ-O5-08 (cost)** because a duplicate-ID input is how "zero extra requests / no mutation on repeats" is exercised. Both lines above are copied from the YAML, not invented.

**REQ-O5-04/05/06/08 fit_criterion text changed upstream.** The active acceptance wording is the YAML string, not the old r2 shorthand ("T12; I11.", "T10/T11.", "T14", "T10/T14/T16"). This plan defers to the YAML text; the case IDs are unchanged.

---

## 4. Layers, files and offline isolation (v1.2)

### 4.1 Layer definitions

| Layer | Meaning | Planned file |
|---|---|---|
| `S` | Pure selector, in-memory inputs, no clock | `test/offline/test_o5_macro_news_filter.py` |
| `B` | **Evidence-builder unit tests** — construct the evidence object directly; no selector under test | `test/offline/test_o5_evidence_builder.py` |
| `A` | **Reachable adapter-path integration** through real `get_global_news_yfinance` / `tools.get_global_news` | `test/offline/test_o5_macro_news_integration.py` |
| `I` | Invariant / fault injection | `test/offline/test_o5_invariants.py` |
| `R` | Public interface / inherited regression | `test/offline/test_o5_regression.py` |
| `P` | T17 measurement harness | `test/offline/test_o5_macro_news_perf.py` |

### 4.2 Schema vs builder vs reachable integration

- **Schema tests** validate an evidence dict against Interface §4 alone (no production code): **I6** (required-key deletion, including the eight I6-RV rows), **I7** (extra key), **I8** (action/trigger/disposition triples), **I10** (V-PARTIAL branch/field/state matrix + count constraints).
- **Builder-only unit test:** **I9-a**. It directly constructs a `V-VENDOR` object for a stage where rules have not yet been resolved and asserts the builder's `rules_version` is present-and-`None`. Production retrieval resolves rules before any fetch, so this stage is unreachable through `get_global_news_yfinance`; it must **not** be described as an integration case.
- **Reachable integration tests:** **T03a-A, T13a, T13b, T13c-D, T13c-R, T13d, T15, I9-b** — they enter through the public adapter/tool path.
- **Selector-level:** T01–T12, T14, T19, T20.

### 4.3 I9-b — full specification (F requirement 7)

| Element | Specification |
|---|---|
| Layer | **A** — reachable adapter-path integration (not a builder test) |
| Entry point | `tradingagents.dataflows.vendors.yahoo.news.get_global_news_yfinance(as_of_date, look_back_days, limit)` called directly; the routed variant through `route_to_vendor("get_global_news", …)` is optional extra coverage |
| Setup | `limit=10`; `global_news_queries=["q1","q2","q3"]`; single-vendor `yfinance`; `common.time.sleep` patched to a no-op; `yf.Search` patched so `q1` returns one in-window article, `q2` returns `[]`, and `q3` raises `RuntimeError("boom")`; adapter sink replaced by a fresh `InMemorySink` |
| Rule-resolution stage | **After** request validation and rule resolution succeeded: `rules_version` is resolved from config (`o5-rules-v1.1-draft` or the active registry value) **before** the retrieval loop begins; the fault occurs later, inside the loop |
| Captured evidence | The single emitted event, from the sink |
| Assertions | exactly one event; `variant="V-PARTIAL"`; `action="PARTIAL_UPSTREAM"`; `trigger="PARTIAL_QUERY_FAILURE"`; `disposition="PARTIAL_UPSTREAM"`; **`rules_version` present and equal to the resolved version string** (not `None`); `executed_query_count=3`; `queries_failed=1`; `pre_filter_candidate_count=1`; `batch_id`, `input_count`, `reason_counts` **present and `None`** (AM-44); **no `V-VENDOR` event**; the direct call raises `VendorUnavailableError` and no article text is returned |
| Contrast with I9-a | I9-a asserts `rules_version` present-and-`None` at the unreachable pre-resolution stage; I9-b asserts present-and-non-`None` at the reachable post-resolution stage. The schema has no stage field, so the **test setup** supplies the stage |

### 4.4 Offline isolation, against the merged baseline (supersedes v1.1 §4)

Verified at `4f87e29`:

- `pyproject.toml` → `testpaths = ["tests", "test/offline"]`. **Collection of the offline tree is already configured.**
- `test/offline/conftest.py` **already exists** and provides the autouse `_no_network` fixture blocking `socket.socket.connect`, `connect_ex`, `socket.getaddrinfo` and `curl_cffi` `Session.request`/`AsyncSession.request`, skipping only `integration`.
- `tests/conftest.py` still provides the inherited suite's isolation and config/cache reset.

Consequences for O5:

1. **F does not need to add initial collection.** The v1.1 statement to that effect is withdrawn.
2. O5 **must not create or replace** `test/offline/conftest.py`; it only adds tests beside it. If O5 needs per-test config reset and a temp `data_cache_dir`, that is a **separate, F-coordinated** addition (the merged sibling conftest does **not** currently reset `tradingagents.dataflows.config` or the cache dir).
3. **O5 collection/isolation remains untested**: no O5 test module exists and no O5 case has been executed.
4. A **new base check** is required before implementation (§9 Q1) because the local package was authored against `970a9ea`, not `4f87e29`.

---

## 4.6 Evidence lifecycle (v1.3, A3) - supersedes any "emit from the retrieval loop's finally" idea

The v1.2 execution plan proposed emitting terminal O5 outcome evidence from the retrieval loop's `finally`. **That is withdrawn:** at loop exit, selection has not run, so a "success" event would be a guess. The table below is the authoritative path plan.

| Path | Stage reached | Retrieval calls | Selection run? | Evidence emitted | Emitted where | Result |
|---|---|---|---|---|---|---|
| **P-K0** | request validated, `limit == 0` | **0** (no `yf.Search`) | no | exactly **one `V-LIMIT-ZERO`** | region 1, before retrieval | LIMIT_ZERO string |
| **P-OK** | retrieval complete, selector + invariant validation + final publishable result all done | n (as baseline) | **yes** | exactly **one** of `V-SELECTED` / `V-FILTERED-EMPTY` / `V-UPSTREAM-EMPTY` | region 4, **after** selection and invariants, **before** return | honest string |
| **P-PARTIAL** | retrieval raised mid-loop with ≥1 collected candidate | k attempted, 1 failed | **no** | exactly **one `V-PARTIAL`** | retrieval-failure boundary (region 2's except path) | direct: raise `VendorUnavailableError`; routed: router `DATA_UNAVAILABLE` |
| **P-VENDOR** | retrieval raised with no usable candidate / rate limit exhausted | n attempted | no | exactly **one `V-VENDOR`** (trigger from the typed cause) | region 2 except path | as baseline error path |
| **P-INVARIANT** | selection returned, invariant check failed | n | yes, result **suppressed** | exactly **one `V-INVARIANT`** | region 4 after the invariant check | "filter-unavailable" message, no articles |
| **P-INVALID-REQ** | request validation failed | 0 | no | exactly **one `V-INVALID-REQUEST`** | region 1, before any fetch | request error |

**Planned control-flow pseudocode (proposed; not code).**

```
get_global_news_yfinance(as_of_date, look_back_days, limit):
    cfg, start_dt, queries = resolve_config_and_window(...)      # existing :155-164
    try:
        request = validate_request(limit, topics, start_at, end_at, rules_version)   # region 1
    except InvalidRequest as e:
        emit_once(V_INVALID_REQUEST(field, reason))              # P-INVALID-REQ, 0 calls
        raise                                                     # existing error path unchanged

    if request.limit == 0:                                        # P-K0
        emit_once(V_LIMIT_ZERO(input_count=0, executed_query_count=0,
                               pre_filter_candidate_count=0, batch_id=None))
        return LIMIT_ZERO_TEXT                                    # zero retrieval calls

    pool, executed, failed, failure = run_retrieval_loop(...)      # region 2; unchanged body
    #   the existing loop body (queries, news_count, fuzzy, window filter,
    #   exact-title dedup, early stop at :188) is byte-identical
    #   the loop wrapper catches the exception, records `failure`, and stops

    if failure is not None:                                       # P-PARTIAL / P-VENDOR
        if pool: emit_once(V_PARTIAL(executed, failed, len(pool),
                                     batch_id=None, input_count=None, reason_counts=None))
        else:    emit_once(V_VENDOR(vendor, method, trigger=typed_trigger(failure)))
        raise failure                                             # then the unchanged error path

    result = select_macro_news(build_selector_request(pool, request))   # region 3
    verify_invariants(result, original=pool)                      # region 4
    if violated:
        emit_once(V_INVARIANT(...))                               # P-INVARIANT
        return FILTER_UNAVAILABLE_TEXT
    final = format(result)                                        # only now is "success" true
    emit_once(terminal_variant_for(result))                       # P-OK: V-SELECTED / filtered / upstream-empty
    return final
```

**Exactly-once rules.**

- `emit_once` is per **invocation** of `get_global_news_yfinance`, not per query and not per retry. It is a single guarded call on each path above; nothing else emits terminal evidence, so a second outcome cannot be published from a `finally`.
- `finally` may only perform **cleanup** (closing the sink, releasing a lock). It must not emit, and must not infer a result.
- **Retry boundary:** `yf_retry` retries *inside* a single query; those retries are invisible to the evidence layer (they are neither invocations nor queries). `executed_query_count` counts **query attempts**, `queries_failed` counts failed queries.
- **T13c-D / T13c-R preserved:** each independent run emits exactly **one `V-PARTIAL`** and **no `V-VENDOR`**; the router never emits O5 evidence, and propagation must not add a second event.
- **Sink failures** are handled by the Interface §7 branches: a **construction** failure and an **emit** failure are distinct; neither changes the served string; `SINK_FAILED` is logged on the independent logger.
- **No CLI run context:** evidence can still be **constructed** in memory; it is **not persisted** (registry `o5.sink_failure`). Construction ≠ persistence, and the plans never claim a file was written when it was not.
- **Unspecified semantics left as review decisions:** whether a `V-VENDOR` should also accompany a `V-PARTIAL` (C7), the exact `filter-unavailable` string (D), and whether evidence is buffered when the sink is constructed late (C).

## 4.5 Invariant-case reconciliation (F requirement 8)

r2's detailed cases name an invariant in their prose; the merged registry gives INV-O5-01..04 one shared `verification` string. This table is the traceable mapping.

| Invariant | Registry statement | Active cases | r2 detailed-case expectation | Verdict |
|---|---|---|---|---|
| INV-O5-01 | No fabrication / irrelevant padding | I1, I3, I11 | I1 → "stub ID∉input ⇒ V-INVARIANT INV-O5-02"; I3 → "duplicate output IDs ⇒ INV-O5-02"; I11 → business-field guard ⇒ INV-O5-01 | **Amended here:** I1 and I3 are **INV-O5-02** (out-of-input / duplicate), not INV-O5-01. Only **I11** asserts INV-O5-01. |
| INV-O5-02 | No out-of-input / duplicate / mutation | I1, I2, I3 | I1, I3 as above; I2 → INV-O5-03 | I1, I3 confirmed INV-O5-02. I2 moves to INV-O5-03. |
| INV-O5-03 | Window containment | I2, T11f | I2 → INV-O5-03; T11 → window boundaries | Confirmed; T11f added as the adapter-side recompute case. |
| INV-O5-04 | No network / LLM | I4, T16 | I4 → import boundary + blocked network; T16 → attempt recording | Confirmed. |

**Historical note.** The r2 §5 mapping line that associated I1/I3 with INV-O5-01 is the **conflicting active expectation**; the r2 reference is retained verbatim as history and this table is the amendment. The multi-violation precedence `INV-O5-04 > INV-O5-02 > INV-O5-03 > INV-O5-01` is unchanged.

---

## 5. Explicit amendments (A-1..A-8 from v1.1 + A-9..A-12 from v1.2) — the ONLY changes to the r2 references

### A-1. T03c — complete, well-formed input (fixes the malformed/abbreviated r2 input)

The r2 T03c input is replaced by this complete record set. Note `title` must be a string for the record to be structurally valid; the r2 example's `title:""` and `"No title"` are both kept, and the two IDs are real fixture-style IDs.

```json
[
  {"candidate_id": "o5:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa01", "title": "", "summary": "x",
   "source": null, "url": null, "published_at": "2026-09-25T00:00:00Z"},
  {"candidate_id": "o5:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa02", "title": "No title", "summary": "y",
   "source": null, "url": null, "published_at": "2026-09-25T00:00:00Z"}
]
```

Request: topics `[MONETARY_POLICY, INFLATION, ECONOMIC_ACTIVITY]`, `start_at=2026-09-20T00:00:00Z`, `end_at=2026-09-27T23:59:59.999999Z`, `limit=3`, `rules_version=o5-rules-v1.1-draft`.
Expected: `status=NO_RELEVANT_NEWS`; `counts = {input_count 2, selected_count 0, not_selected_limit_count 0, irrelevant_count 0, invalid_count 2, out_of_window_count 0, duplicate_count 0, skipped_zero_limit_count 0}` (conserves: 2 = 0+0+0+2+0+0+0); decisions are two `INVALID` / `reason_code=INVALID_TITLE`; adapter layer `empty_kind=ALL_INVALID`.
(Any error in `published_at` string syntax would make the record structurally invalid — the strings above are valid RFC3339, so both records reach the title check.)

### A-2. T12 — corrected count conservation

r2 asserted `len(decisions)=5` with `counts={5,1,0,1,1,1,1,0}`, which does **not** conserve (sums to 5 only if `input_count` is 5, but the ordering of keys is ambiguous and the r2 line is abbreviated). v1.1 restates it canonically:

Pool (5 records, in input order): one valid relevant (SELECTED-eligible), one `INVALID_TITLE`, one `OUT_OF_WINDOW`, one `DUPLICATE_ID` (repeat of the selected ID), one `REJECTED` (irrelevant).
Request: K=10, default window/topics.

Expected `counts` (canonical keys, conserving):
`input_count 5, selected_count 1, not_selected_limit_count 0, irrelevant_count 1, invalid_count 1, out_of_window_count 1, duplicate_count 1, skipped_zero_limit_count 0` → 1+0+1+1+1+1+0 = **5**.
`len(decisions) == 5`, one disposition per index: `SELECTED`(0), `INVALID`(1), `OUT_OF_WINDOW`(2), `DUPLICATE_ID`(3), `REJECTED`(4).

### A-3. Adapter case T03a-A — K=0 must not fetch (registry `o5.zero_limit`)

New adapter case (this was not in r2): `tools.get_global_news(curr_date, limit=0)` with `yf.Search` patched to a counter that records calls.
Expected: **`yf.Search` call count = 0**; returns a short `str` stating limit=0 / nothing analyzed; evidence variant `V-LIMIT-ZERO` with `input_count=0`, `executed_query_count=0`, `pre_filter_candidate_count=0`, `batch_id=null`. This is the registry's zero-fetch path and is a **deliberate change from baseline** (baseline would fetch then format). It does **not** reopen any V-PARTIAL count constraint.

### A-4. Evidence path (registry `o5.evidence_path`)

Evidence is written to `o5_evidence.jsonl` in the **same O2 run directory** when a CLI run context exists. Where no CLI context exists, `SINK_FAILED` is logged and the honest result is still served (registry `o5.sink_failure`). The exact handoff is a **C seam** (§9 Q3), not an E policy choice.

### A-5. Invariant-failure wording (registry `o5.invariant_failure`)

On selector invariant failure the adapter suppresses selected articles and returns an explicit **"filter-unavailable"** message, never "no news". The exact string is a **D** confirmation (§9 Q4).

### A-6. Negation flag (registry `o5.negation`)

A negated match remains **selectable as context** and carries a negation flag. The evidence/selected record must expose that flag; the exact field name is a **D** confirmation (§9 Q5). Add case: a record whose only anchor is negated (`no sign of rising inflation`) is selectable, flagged `negated=true`.

### A-7. Rule-vocabulary strings (registry rule tables)

Use the registry's literal strings. **Verified against the merged YAML (§9a):** R1 context has `basis points` **only** (no `basis point`); R2 anchors have **both** `price pressure` and `price pressures`; R1 has both `hike`/`hikes` and `cut`/`cuts`; R2 context has both `fall`/`falls` and `rise`/`rises`; `easing` is an R2 context token. **Corrected v1.1 over-generalisation:** the r2 list was wrong only about `basis point`, not about `price pressure`. No singular/plural equivalence is inferred. **DEV20 labels have not been re-derived under the registry list** and remain provisional. Tracked as §8 D-03.

### A-8. T17 acceptance condition wording

`REQ-O5-10` **specifies** ubuntu-latest / Python 3.11, 5 warmups, 30 measured runs, nearest-rank p95 ≤ 100 ms. This is the **specified acceptance condition**, distinct from (a) F/E reviewer approval of the plan, (b) runner realization, and (c) actual measurements — none of which have occurred. A relaxation would require an explicit registry decision.

### A-9. Merged-baseline rebase (v1.2)

Every active reference points at `4f87e29f7a52842dba8272071d2a4a1b527def10`, not `3cb83f3`. Statements that PR #2 is unmerged are **withdrawn as active claims** and appear only in labelled history.

### A-10. Verification mapping re-derived from the merged YAML (v1.2)

REQ-O5-05 gains **T13**; REQ-O5-08 gains **T07**; the INV-O5-01..04 split is amended per §4.5. All other O5 mappings were re-checked against the merged YAML (§3).

### A-11. T17 handoff/manifest integrity, one-way only (v1.2)

The **manifest** records the handoff's hash; the handoff must **not** record the manifest's hash (that would be circular). The v1.1 handoff cited a stale manifest digest `53bd45f7…`; that digest is **removed**. The handoff will reference the manifest **by filename**, and after the handoff is edited its digest is recomputed and written into the manifest. The final manifest digest is recorded in `README.md` only, because the manifest does not hash the README.

### A-12. T17 acceptance wording from the merged registry (v1.2)

`REQ-O5-10` **specifies** ubuntu-latest / Python 3.11, 5 warmups, 30 measured calls, nearest-rank p95 ≤ 100 ms. **If any of the 30 measured selector calls returns an incorrect result or raises an unexpected exception, T17 fails overall.** Such a sample is **not** discarded or replaced to obtain a passing p95. A specified threshold is not an observed result, not an approval, and is not relaxed without a registry decision.

Everything not listed A-1..A-12 stands as written in the two r2 references.

---

## 6. Case index (IDs checked for consistency)

`T01–T20` (T13 has sub-cases T13a, T13b, T13c-D, T13c-R, T13d; T03 has T03a, T03a-A, T03b, T03c; T05 T05a/T05b; T07 T07a–e; T08 T08a–i; T10 T10a–l incl. T10c2/T10g2/T10k2; T11 T11a–f; T14 T14a–d).
`I1–I12` (I6 groups I6-VS-1..6, I6-FE-1..7, I6-LZ-1..4, I6-UE-1..6, I6-VV-1..7, I6-PA-A1..6, I6-PA-B1..2, I6-IV-1..4, I6-IR-1..3, I6-RV-1..8, I6-COM-1..5; I9-a, I9-b; I10-A/B × bi/ic/rc × 1..3 plus I10-A-11, I10-A-33, I10-B-11, I10-B-33).
`RT-1..RT-4`. New in v1.1: `T03a-A`.

Case IDs above are defined once, in the r2 detailed reference, and referenced — not redefined — here.

## 7. T17 measurement conditions (registry-specified; v1.3)

**Fail-overall rule.** If **any** of the 30 measured selector calls returns a result that differs from the expected file or raises an unexpected exception, **T17 fails overall**. That sample must not be dropped, retried away, or replaced; a passing p95 cannot be manufactured from the remaining samples.

**One-way hashing.** The manifest records the handoff hash; the handoff references the manifest **by filename only**; `README.md` records the final manifest hash. The manifest does not hash the README, so there is no cycle.

Metric, runner and threshold are the registry's specification (ubuntu-latest / Python 3.11, p95 ≤ 100 ms); they are not an approval and not a measurement.

- Fixture: [`O5-T17-Perf-Fixture-1000-v1-DRAFT.json`](./O5-T17-Perf-Fixture-1000-v1-DRAFT.json), SHA-256 `4b6699eca6a8958779479dabd2063cdf31ce31807ebaeb2e2f047462ae14f1f0`, 1000 records, K=30.
- Expected: [`O5-T17-Expected-Results-v1-DRAFT.json`](./O5-T17-Expected-Results-v1-DRAFT.json), SHA-256 `42e1c0fb5e1d7d42adbe19b3f780a1a8a7b92fe3a6895c6807b9434da49d1bc6`; `status=OK`, selected 30 (10/10/10), counts `{1000,30,890,60,0,0,20,0}`.


- Boundary: load/deserialize/RFC3339 parse/defaults **outside**; validation, classification, sort, allocation, result construction **inside**; assertions and persistence **outside**. Input mutation is a correctness failure.
- Correctness gate before timing; any mismatch or error ⇒ **invalid measurement** and, per the fail-overall rule above, **T17 fails**.
- **Digest references are not hard-coded here.** This section previously froze stale manifest/handoff digests (a `1ed6d0a4`-prefixed manifest digest and a `97a36c51`-prefixed handoff digest, both since superseded). In v1.3 the **manifest and handoff digests are referenced only through [`README.md`](./README.md)**, which records the final values computed from actual bytes. Fixture and expected digests above are unchanged because their bytes are unchanged.
- **One-way dependency:** manifest → {fixture, expected, handoff}; handoff → manifest **by filename only**; README/plans → manifest digest. Nothing hashes the README.
- The T17 artifacts contain the old note "runner pending F". **Superseded only here** by A-8: the registry names ubuntu-latest/Py3.11 as the specified condition. 100 ms remains unverified.

## 8. Registry contradictions kept visible

| ID | Contradiction | Status |
|---|---|---|
| D-02 | `REQ-O5-01` says `o5-rules-v1.1`; `development_contract.o5.rules_version` says `o5-rules-v1.1-draft`; the DEV20 fixture repeats `-draft` (re-verified at `4f87e29` **and** PR head `27c8e4b`) | **BLOCKING** — A/B must pick one literal and synchronize registry, config, fixture metadata and every active plan before coding; E proposes `o5-rules-v1.1`, unapproved. See §0a |
| D-03 | Rule strings: merged YAML has `basis points` only (no `basis point`); `price pressure` **and** `price pressures`; `hike`/`hikes`, `cut`/`cuts`, `fall`/`falls`, `rise`/`rises` | **Open (narrowed)** — only the `basis point` absence differs from r2; verified in §9a; DEV20 labels not re-derived |
| D-04 | INV-O5-01..04 share one `verification` string | **Open** — E's per-invariant mapping Pending F |
| D-06 | REQ-O5-07 needs a human holdout; DEV20 is provisional | **Open** — DEV20 labels **not** human-approved; no quality acceptance or human-label approval claimed |
| D-17 | Collection/CI: merged baseline already configures `testpaths=["tests","test/offline"]` and ships `test/offline/conftest.py` | **Resolved for configuration**; **O5 execution unverified** |
| D-18 | Local checkout `970a9ea` vs merged baseline `4f87e29` | **Open** — base check required before implementation |
| D-19 | Evidence must be emitted **after** selection/invariant validation, not from the retrieval loop's `finally` | **Amended in v1.3** — see §4.6; the v1.2 execution-plan text that emitted terminal evidence in `finally` is withdrawn |
| D-20 | `vendors/yahoo/news.py` ownership was implied to be C's | **Corrected in v1.3** — E implements the O5 private integration there; C confirms only the O2 run-dir handoff and C-owned shared files (§0a) |

## 9. Review questions (v1.2, genuinely open)

1. **A:** confirm the implementation base — the merged baseline `4f87e29…` is the review baseline, but the local package was authored at `970a9ea`; a **new base check** is required before implementation. `A-Requirements-Decisions.md`'s `feature/o1-sma-guard` line is authoring context only.
2. **F:** confirm the per-invariant case mapping in §4.5 (the registry's shared "I1-I12" string does not name cases).
3. **A/B (BLOCKING):** choose the canonical `rules_version` literal and synchronize `requirements.yaml` (statement + `development_contract`), the DEV20 fixture metadata, the `o5_rules_version` config value and every active plan. **Neither value is selected here**; E proposes `o5-rules-v1.1` (§0a). Re-verified at `4f87e29` and PR head `27c8e4b`.
4. **A/B:** rule-vocabulary difference (see §8 D-03 as verified below) — the merged YAML uses `basis points`, `price pressures`, plus `hike`/`hikes`, `cut`/`cuts`, `rise`/`rises`, `fall`/`falls`. No singular/plural equivalence is inferred.
5. **C:** O2 run-directory handoff into the evidence sink, and whether `o5_*` keys enter `default_config.py`.
6. **D:** exact "filter-unavailable" string; negation-flag field name.
7. **F/E:** T17 runner realization and 100 ms; a relaxation requires a registry decision.
8. **F:** whether O5 needs additional per-test config/cache reset beside the existing `test/offline/conftest.py`.

## 9a. Direct verification of amendment A-7 against the merged YAML (A requirement 3)

| Phrase | In R1-MP context | In R2-IN anchors | In R2-IN context | In R3-EA context |
|---|---|---|---|---|
| `basis points` | **present** | — | — | — |
| `basis point` | absent | — | — | — |
| `price pressures` | — | **present** | — | — |
| `price pressure` | — | **present** (also listed) | — | — |
| `hike` / `hikes` | both present | — | — | — |
| `cut` / `cuts` | both present | — | — | — |
| `fall` / `falls`, `rise` / `rises` | — | — | both forms present | — |
| `easing` | in R1 context | — | **present in R2 context** | — |

**Result:** A-7's premise that the merged list uses only `basis points` (no singular `basis point`) is **confirmed**, and `price pressure`/`price pressures` are **both** present (so the earlier r2 list was not wrong for that anchor). The v1.1 wording "no singular variants" was therefore **too broad**; A-7 is corrected here: the only singular/plural asymmetry that matters is **`basis point`**, which the YAML does **not** list. `easing` remains an R2 context token (hence M01/M02 match both topics), which is unchanged by the merge. **DEV20 labels have not been re-derived** and remain provisional.

## 9b. Test cases affected by the v1.3 lifecycle (A3)

Unchanged and preserved: T13c-D, T13c-R (still exactly one `V-PARTIAL`, no `V-VENDOR`), the I10 18 field-state cases, I6-RV-1..8, I9-a builder boundary, and the Interface §4.2 count constraints.

**Renewed review needed only for these:**

| Case | Renewed assertion |
|---|---|
| T03a-A | evidence must be emitted at **region 1 with `executed_query_count=0` and zero `yf.Search` calls** (§4.6 P-K0) |
| T04a/T04b/T04c | terminal `V-UPSTREAM-EMPTY` / filtered variant is emitted **after** selection, not from a `finally` (§4.6 P-OK) |
| T01/T02/T05/T06/T19/T20 | terminal `V-SELECTED` emitted **after** invariant validation (§4.6 P-OK) |
| I1/I2/I3/I11 | `V-INVARIANT` emitted after the invariant check and the result suppressed; no success event beforehand (§4.6 P-INVARIANT) |
| I5/I5b | sink **construction** vs **emit** failures stay distinct; neither changes the string (§4.6) |
| T10f–T10j | `V-INVALID-REQUEST` emitted at region 1 with **zero** retrieval calls (§4.6 P-INVALID-REQ) |
| T13a/T13b | `V-VENDOR` from the typed cause, one event (§4.6 P-VENDOR) |

**A-comment mapping (v1.3):** A1 canonical `rules_version` → §0a, §8 D-02, §9 Q3; A2 ownership → §0a, D-20; A3 evidence lifecycle → §4.6, §9b; A4 T17 hashes → §7 and `README.md`.

## 10. Approval status

- **F reviews this O5 test plan.** **A reviews the execution plan.**
- Implementation and test coding may begin only after both scoped approvals and project governance readiness; an approval comment must name the reviewed version, requirement IDs, case IDs, allowed files and exclusions; an empty `docs/test-approvals/TEMPLATE.md` is **not** approval.
- **All software tests and benchmarks: Not run.**
- **v1.3 status:** both plans remain **pending review** — **F reviews this test plan; A reviews the execution plan.** Neither plan is approved for implementation, and the A1 `rules_version` decision is **blocking**.

## 11. Preserved F closures (r2 document-review scope) - v1.2 status

Preserved unchanged: T13c-D/T13c-R independent sinks + single `V-PARTIAL`; the I10 18 field-state cases; I6-RV-1..8; I9-a builder-only boundary; Interface §4.2 count constraints + the four A/B examples; M02 vocabulary wording. **Not reopened** by A-3 (the K=0 zero-fetch path is a separate adapter case and does not touch V-PARTIAL counts). **v1.2 renewals (only changed assertions need re-review):** §3 verification mapping (A-10), §4.3 I9-b layer correction (F7), §4.5 invariant mapping (F8), §7 T17 wording (F11) and A-7's narrowed vocabulary claim (§9a). Everything else above stays closed.
