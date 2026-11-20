# O6 Batch 1 — Pre-code review package v1.0

**Owner:** F · **Execution-plan reviewer:** A · **Status:** Documentation ready for review, implementation pending.

**Requirements baseline:** [Merged PR #2](https://github.com/Caicys297/TradingAgents-CS5351/pull/2), `4f87e29f7a52842dba8272071d2a4a1b527def10`. The diagnostic inspection used `diag/o6-callback-scope` at `970a9eab6b4b3a819dc22f417a4df1e7eaa73d04`. A will confirm the implementation branch and base SHA.

## 1. Test plan v1.0 — Handler-only scope

| Case | Requirement coverage in this batch | Deterministic assertion |
|---|---|---|
| TC-O6-01 | O6-FR-01 | Synthetic Market events produce 2 calls, 150/30 tokens, 1.5 s. News produces 1 call, 80/15 tokens, 0.8 s. |
| TC-O6-02 | O6-FR-02 | Missing usage yields Unknown on both fields. Explicit 0/0 yields two complete zero totals. |
| TC-O6-03 | O6-FR-02 | Calls reporting 100/20 and 50/missing yield 150 complete input and 20 partial output tokens. |
| TC-O6-04 | O6-FR-01, O6-NFR-01 | Interleave synthetic events: Market 0.0→1.5 s and News 0.2→1.0 s, with completion in reverse start order. Each row holds its own one call, tokens (100/20 or 80/15), and duration (1.5 or 0.8 s). |
| TC-O6-05 | Supporting assertion for O6-FR-01/02 | Replay the same start/end and compare the new stats exactly to the pre-replay snapshot. An errored call counts once and accrues 0.75 s at 1.0→1.75. A start-only call counts once with 0 s while pending. Unreported usage stays Unknown. |
| TC-O6-06 | O6-NFR-01 | A fresh handler for a News-only run contains no Market row or prior-run counters. |
| TC-O6-08 | O6-FR-01 | An explicitly in-scope call with missing identity increments unattributed_calls once and leaves named rows intact. |
| TC-O6-09 | O6-NFR-02 | One completed call with 100/20 and one tool call returns exactly the four legacy keys and values (1, 1, 100, 20). Replay handling in the new interface preserves legacy counting semantics. |
| TC-O6-10 | O6-FR-01 | In-scope calls with empty or unknown agent_key each increment unattributed_calls once and create no named row. Use A-confirmed valid-key source. |

TC-O6-05 is supporting coverage in this package. The merged Registry's verification lists are unchanged. Use synthetic callback events, fixed clocks and offline fixtures. For partially missing usage, verify that the synthetic payload actually omits the field before invoking the handler.

Batch 1 covers handler behavior. Full O6 acceptance also requires real-subgraph attribution, setup.py binding, known out-of-scope verification, and CLI disclosure/isolation (TC-O6-07/07b/11/12/13/14). The merged Registry requires known out-of-scope calls to leave both named rows and unattributed_calls unchanged. TC-O6-11 still depends on A confirming the binding and scope-label semantics.

## 2. OpenCode execution plan v1.0 — For A's approval

Allowed implementation paths: `cli/stats_handler.py` and `test/offline/test_o6_per_analyst_stats.py`.

1. Confirm the target branch and base SHA with A. Check the merged requirements baseline, default pytest discovery and shared offline guard from PR #1 (`f3983d6`). Preserve the diagnostic worktree and its untracked files. The historical diagnostic checkout predates that configuration.
2. Confirm the source of valid selected-Analyst keys with A. Prefer passing the selected run's verified keys to the handler through a backward-compatible interface if A confirms it. First inspect the pinned callback API for a stable invocation ID shared by start/end/error. Propose the dedup key from that evidence and flag any gap to A before using it.
3. Add synthetic tests at the approved path. Implement per-handler bookkeeping using trusted in-scope metadata and stable invocation identity, with a controlled monotonic clock, completion/error duration, and independent token completeness. Apply replay deduplication to the new per-Analyst statistics. Expose the result through an additive accessor (proposed `get_agent_stats()`), with `unattributed_calls` on that surface. Preserve the legacy `get_stats()` signature, keys, outputs and counter behavior.
4. From the target repository root run `pytest --collect-only -q`, `pytest -q test/offline/test_o6_per_analyst_stats.py`, and `pytest -q`. Reuse the shared autouse guard and record a blocked network probe scoped to the offline tests. Keep deterministic cases in default collection. Record the tested SHA, case-to-node mapping, per-case results, guard evidence and CI run link when available.

**A's decision requested:** approve this execution-plan version and two-file scope, confirm target branch/base and valid Analyst key source, and record approval on the documentation commit. If the confirmed interface needs a third file or shared binding changes, bring the expanded scope back for review.

## 3. Approval record for the Draft PR

| Record | Status |
|---|---|
| Prior Batch 1 test-scope approval | Reported as granted by A in project handoff for the nine cases and two files. Attach the original message or immutable evidence and actual timestamp before recording formal approval for this package. |
| Merged Registry review | [PR #2 mapping and Schema review](https://github.com/Caicys297/TradingAgents-CS5351/pull/2#pullrequestreview-5916156511). This is evidence for the Registry baseline. |
| Exact package version / documentation SHA | v1.0 / pending documentation commit. |
| Execution-plan approval, target branch/base, key-source decision | Pending A. |
| First implementation commit, test output, CI and code review | Pending implementation and execution. |

## 4. Draft PR text

**Title:** `docs(o6): submit Batch 1 pre-code test and execution plans`

Submit O6 Batch 1 package v1.0 against merged requirements at `4f87e29`. Scope: TC-O6-01–06 and TC-O6-08–10, handler-level offline tests, with two implementation paths listed in §2. This PR contains documentation only.

@A, please review §2 and record the reviewed documentation SHA, approved scope, target implementation branch/base SHA, and valid selected-Analyst key source. Please link the original Batch 1 test-scope approval to the review record. Implementation and test/CI evidence remain pending.
