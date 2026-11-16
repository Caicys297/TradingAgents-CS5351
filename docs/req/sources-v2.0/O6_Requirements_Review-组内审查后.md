# O6 — Per-Agent Usage Tracker

**Owner:** F  
**Status:** Revised draft for requirements registry review, 15 November 2026. C confirmed the v1 design baseline. B reviewed the IDs and fit criteria. The four O6 IDs are retained. Registry Schema validation is pending.  
**Team baseline:** `970a9ea` (imports upstream `9fa1196`)

## 1. Existing Problem

The baseline `StatsCallbackHandler` in `cli/stats_handler.py` reports run-level LLM calls, tool calls, and input/output tokens. Its output does not show which analyst made each model call or whether the reported token totals omit calls with missing usage data. The existing `AnalystWallTimeTracker` in `cli/display.py` measures elapsed time until each analyst's report arrives. O6 adds per-analyst model-call statistics, including cumulative model-call duration.

**O6 v1 scope confirmed by C.** Track ordinary model calls and `wrap_up` for Analysts selected in the execution plan during one CLI analysis run. Market and News are the acceptance test roles. Attribution of the first structured model call is deferred. The reported statistics must show that limitation and describe coverage as selected-Analyst calls with verified identity. Real-subgraph metadata propagation, `wrap_up` attribution, and cross-Analyst isolation are Planned.

## 2. Functional Requirements

| Proposed ID | Requirement |
|---|---|
| O6-FR-01 | Expose per-Analyst statistics through a new interface and show one CLI summary row for each selected Analyst with attributed calls, including ordinary model calls and `wrap_up`. Report distinct model calls, input tokens, output tokens, and cumulative model-call duration. Apply the same rules for call counts, token usage, and duration to ordinary calls and `wrap_up`. Each observed invocation contributes at most once to its analyst's counts, usage, and duration. Report missing or invalid identity through `unattributed_calls`. Exclude calls with unknown identity and calls outside the selected-Analyst scope from named rows. State in the CLI statistics that first structured-call attribution is deferred and that the named rows cover only verified in-scope calls. |
| O6-FR-02 | Report input and output token completeness independently. If every counted call reported a value for a field, show the total. If some did, show the known subtotal marked partial. If none did, show `Unknown`. Treat an explicitly reported zero as a known value. |

## 3. Non-functional Requirements

| Proposed ID | Requirement |
|---|---|
| O6-NFR-01 | Attribute model calls correctly when invocations overlap or complete out of order. Keep statistics isolated across CLI analysis runs. |
| O6-NFR-02 | Preserve the baseline `get_stats()` interface, output and run-level counter semantics. The O6 offline tests must be repeatable with simulated model events and a controlled clock, without API credentials or network access. |

## 4. Fit Criteria

| Requirement | Pass criteria |
|---|---|
| O6-FR-01 | Two Market calls (one ordinary call and one `wrap_up`) with `100/20` and `50/10` input/output tokens and durations of `1.0 s` and `0.5 s` yield **2 calls, 150/30 tokens, 1.5 s**. One News call with `80/15` tokens and a duration of `0.8 s` yields **1 call, 80/15 tokens, 0.8 s**. Repeating a notification for an existing invocation leaves these values unchanged. One call without a verified analyst ID appears in `unattributed_calls=1` and no named row. An offline test through the real Analyst subgraph verifies that ordinary and `wrap_up` calls reach the callback with the expected selected Analyst key and that a known out-of-scope call contributes nothing to the named rows. The CLI integration test verifies exact counts, token attribution, and a visible statement that first structured-call attribution is deferred and named rows cover only verified in-scope calls. |
| O6-FR-02 | No reported token data yields `Unknown` for both fields. A reported `0/0` yields two complete zero totals. For calls reporting `100/20` and `50/missing`, input is `150` and complete, and output is `20` and partial. |
| O6-NFR-01 | Interleave ordinary and `wrap_up` calls for Market and News and complete them out of order. Assert that each invocation contributes only to the named row matching its trusted `agent_key`. Verify exact counts, tokens, and durations in each row, with zero contribution to the other Analyst's row. A new run contains only its own events. |
| O6-NFR-02 | For one completed call with `100/20` tokens and one tool call, the baseline interface still reports `llm_calls=1`, `tool_calls=1`, `tokens_in=100`, and `tokens_out=20`. The CI log shows both the baseline suite and the new O6 offline tests running successfully. |

## 5. Proposed Test Cases

| Test | Type | Input or action | Expected result | Requirement |
|---|---|---|---|---|
| TC-O6-01 | Normal | Feed the three calls in the FR-01 fixture. | Both analyst rows match the exact expected values. | FR-01 |
| TC-O6-02 | Boundary | Compare a completed call with missing usage to one reporting `0/0`. | The first has two unknown fields. The second has two complete zero totals. | FR-02 |
| TC-O6-03 | Negative | Feed `100/20` and `50/missing` for one analyst. | Input is `150`, complete. Output is `20`, partial. | FR-02 |
| TC-O6-04 | Concurrency | Start Market at `0.0 s` and News at `0.2 s`. Finish News at `1.0 s` with `80/15`, then Market at `1.5 s` with `100/20`. | Each analyst has one call. Market has `100/20` and `1.5 s`. News has `80/15` and `0.8 s`. | FR-01, NFR-01 |
| TC-O6-05 | Negative | Replay the start and completion notifications for one invocation. Separately, send a call that ends with an error and one that has only a start event. | Replays leave totals unchanged. Both other calls count once. An invocation that errors at 1.75 s after starting at 1.0 s contributes 0.75 s. A start-only invocation contributes 0 s while no terminal event is present. Both have unknown usage if no usage was reported. | FR-01, FR-02 |
| TC-O6-06 | Regression | Run the NFR-02 baseline fixture, then start a new analysis with events from News only. | The first run preserves all four baseline values. The second run has no Market row or prior-run totals. | NFR-01, NFR-02 |
| TC-O6-07 | Integration | Use the approved CLI path with a deterministic test model. Through the real Analyst subgraph, Market makes one ordinary call with `100/20` and News makes one `wrap_up` call with `80/15`. | The CLI shows exactly one call per Analyst with the expected tokens and discloses that first structured-call attribution is deferred. | FR-01, NFR-01 |
| TC-O6-08 | Boundary | Add one model call with no verified analyst identifier alongside known Market and News calls. | The named rows stay unchanged and `unattributed_calls=1` is visible; the summary does not claim full attribution. | FR-01 |

## 6. Proposed Module Interface

- **Inputs:** Explicit Graph Config metadata (`scope="analyst"` and `agent_key=spec.key`), invocation identifier within the run, start and terminal events, and optional provider-reported input/output token counts.
- **Outputs:** An analyst summary containing call count, the value and completeness of each token field, and cumulative duration in seconds.
- **Event handling:** Count a distinct invocation when its start is observed. Add elapsed time from start to successful completion or error. If a terminal event has not arrived, the invocation contributes no elapsed time yet. A call without a verified analyst identifier is excluded from named analyst rows but included in an `unattributed_calls` coverage count. Model errors continue to propagate through the existing application path. Use `spec.key` from the Analyst subgraph assembly boundary as the trusted Analyst identifier. Consume explicit metadata in `cli/stats_handler.py`; node names, event order, and `checkpoint_ns` are outside the attribution contract. Real propagation and callback invocation IDs remain to be verified.
- **Timing:** Cumulative duration is the sum of individual model-call durations. Concurrent calls can overlap in time.

## 7. Expected Code Changes

| Candidate location | Purpose |
|---|---|
| `cli/stats_handler.py` | Evaluate reuse of the existing callback. Retain the existing `get_stats()` contract. |
| `tradingagents/graph/setup.py` | Inspect the shared analyst subgraph for a point that can carry the existing analyst key to the model invocation. |
| `cli/run.py` | Candidate location for connecting the tracker to one run and showing its summary. |
| `test/offline/` | Add offline coverage. Ensure the CI command discovers it alongside the baseline `tests/` suite. |

C confirmed that the initial production change should prioritize `tradingagents/graph/setup.py` and `cli/stats_handler.py`. Coordinate the exact binding point and any `cli/run.py` change with A. The current O6 design has no direct conflict with O3's `sentiment_analyst.py` change.

## 8. Dependencies and Conflicts

- **B:** Reviewed the four O6 IDs and fit criteria. The IDs remain stable for O6. Check their compatibility with the final Registry Schema and add per-entry MoSCoW priority, tradeoff, and source if required.
- **C:** The v1 scope, identity contract, and initial file boundaries are confirmed. F and C will verify metadata propagation in the real Analyst subgraph.
- **A:** Coordinate shared `cli/run.py` changes with B's manifest and D's rating-gate integration; confirm one integration owner and the first integration test.
- **F:** Confirm that the CI log shows both test directories being collected and executed. The baseline pytest configuration currently lists only `tests/` as the default discovery directory.

## 9. Open Questions

1. Which exact `setup.py` binding point will F and A select?
2. Do the real-subgraph callbacks carry the expected metadata and invocation identifiers for ordinary and `wrap_up` calls without cross-Analyst attribution? Verification is Planned.
3. Where will the CLI summary and its coverage statement appear, and who will own the shared integration change?

## Separate course CI responsibility (not part of O6's feature fit criteria)

F also owns the team's CI integration. Before feature implementation approval, agree on one test discovery policy that runs the inherited `tests/` suite and new deterministic `test/offline/` tests. The course requires six **blocking** gates: prior test approval, static/dependency/permission checks, YAML schema validation, semantic evaluation for prompt/model changes, full prior-suite regression, and AI-use-log updates for code/prompt changes. A passing O6 unit suite alone does not satisfy this course deliverable. F should publish a separate CI gate plan with an owner, trigger, pass/fail rule and evidence for each gate; obtain approval before implementation. The repo's existing `pytest -q` and `testpaths = ["tests"]` do not yet collect `test/offline/` by default.

## 10. Review Status

| Review item | Status |
|---|---|
| Requirements and fit criteria | Draft for registry integration. B reviewed the stable IDs and fit criteria, and the requested clarifications are incorporated. Final Registry Schema validation, formal test mapping, and execution evidence are pending. |
| Architecture and allowed files | C confirmed the v1 design baseline. ADR-O6-001 remains Proposed. |
| Test plan and OpenCode implementation plan | Pending separate human approval before implementation |
| Reviewer, date, and approval evidence | To be recorded when the review takes place |
