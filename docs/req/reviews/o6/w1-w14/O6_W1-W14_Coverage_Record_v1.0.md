# O6 W-1–W-14 — coverage record (C)

**Baseline:** `main@a2644eba507493df8305f32cd30003d3eeb33d61` (contains PR #26 `4b479c92b0c84f1975f783110ed3592091e225f0`).
**Branch:** `codex/o6-w-series`, created from that commit.
**Implementation start (UTC):** 2026-11-20T03:02:13Z
**Approvals:** EXEC-W-v1.5 (A, `#7000754482`), TEST-W-v1.5 (F, `#7001823145`). Scope: `test/offline/test_o6_cli_wiring.py` plus this evidence directory only.

## Coverage map — reused vs added

| W | Disposition | Node |
|---|---|---|
| W-1 | **Added** | `test_w1_handler_receives_plan_keys` |
| W-2 | **Added** | `test_w2_single_handler_ordinary` |
| W-3 | **Extended additively** | `test_w15b_new_checkpoint_persists_state` now also asserts one handler |
| W-4 | **Reused unchanged** | `test_tc_o6_14_two_runs_in_one_process_are_isolated` (real fake chat model, independent call counts) |
| W-5 | **Added** | `test_w5_single_registration_path` (three observations) |
| W-6 | **Added** | `test_w6_empty_selection_rejected` |
| W-7 | **Added** | `test_w7_reversed_selection_keeps_canonical_rows` |
| W-8 | **Reused unchanged** | `test_tc_o6_12_cli_disclosure_rows_and_wording` |
| W-8b | **Added** | `test_w8b_missing_identity_renders_one` |
| W-9 | **Reused (already on main)** | `test_w9_partial_output_rendered` |
| W-10 | **Reused (already on main)** | four `test_w10_*` cases |
| W-11 | **Added** | `test_w11_news_only_rendered_table` |
| W-12 | **Added** | `test_w12_out_of_scope_summary_unchanged` |
| W-13 | **Evidence here** | source comparison below + retained W-15a/b footer tests |
| W-14 | **Added** | `test_w14_completion_order` |

W-9/W-10 were merged by PR #26 and are referenced, not duplicated.

## W-13 — `update_display` unchanged

The run-level footer (`update_display`) is not modified by this batch. W-13's source comparison is satisfied by inspection of this branch's diff: no hunk touches `cli/display.py` or `cli/run.py`. The retained runtime evidence is `test_w15a_ordinary_path_statistics_and_footer` and `test_w15b_new_checkpoint_persists_state`, which both assert the real rendered footer.

**This is a source comparison, not a runtime verification.** It is reported as such and not as independent evidence that rendering behaviour is correct.

## Scoped fixture edits (both default-off)

Two additive, opt-in changes were needed inside the allowed file for W-12:

1. `_build_fixture_graph(..., real_bull=False)` — when false (every pre-existing caller) all eight downstream factories are replaced exactly as before; when true, `create_bull_researcher` is left to production.
2. `ScriptedChatModel(answer_real_bull=False)` — when true, a prompt containing `"Bull Analyst"` is answered with an untagged, usage-free message; when false, unscripted calls still raise as before.

The Bull node label `"Bull Researcher"` was **confirmed by execution**, not assumed: W-12 asserts on that exact label and fails if it differs.

## Results

| Command | Result |
|---|---|
| `pytest test/offline/test_o6_cli_wiring.py -q` | 18 passed |
| `pytest test/offline/test_o6_cli_wiring.py test/offline/test_o6_per_analyst_stats.py test/offline/test_o6_analyst_subgraph.py -q` | 36 passed |
| `pytest -q` (full) | 1796 passed, 6 skipped, 1 deselected |
| `ruff check test/offline/test_o6_cli_wiring.py` | All checks passed |

The 6 skips are pre-existing and environmental (POSIX file modes, `langchain_aws` absent, POSIX shell upgrade commands).
