# O4 Semantic Integration Mapping (dependency + ready-to-apply wiring)

Status: **blocked on upstream merge.** PR #25 and PR #27 are **open, unmerged**
(verified). Per the closure instruction, this batch does **not** import unmerged
production branches and does **not** create a passing placeholder. Below is the
exact dependency and the ready-to-apply wiring to add once the O4 Stage-2
production code merges to `main`.

## Verified upstream state (current)
- O4 **Stage-1** `tradingagents/agents/evidence_gate.py` is already on `main`
  (`check_evidence`, `GateResult`, `VERDICT_VALID/REVIEW`).
- O4 **Stage-2**: PR #25 `feat/o4-stage2-evidence-gate @ 45f8d6b…` — **OPEN**.
- O4 **Stage-2 tests**: PR #27 `integration/o4-stage2-cdf0d7c @ 1731943…` — **OPEN, Draft**.
- Neither is merged; feature production code (Graph/CLI wiring, `display_complete_report`
  REVIEW branch) is not on `main`. A previously reported REVIEW screen-display defect
  remains open on the reviewed remote HEAD.

## Dependency (do not import branches)
The O4 semantic cases need, on `main`:
1. `tradingagents/agents/evidence_gate.py` Stage-2 (already have Stage-1).
2. The Graph/CLI/Resume wiring from #25 (gate at completion boundary; CLI buffering;
   `cli/display.py` REVIEW/non-authoritative branch).
3. The offline tests from #27 (`test/offline/test_evidence_gate_*.py`,
   `o4_stage2_fixtures.py`).

**Action:** C/D complete final-main integration and provide the new `main` SHA.
F then integrates the existing tests below into the same semantic checker; no new
production code is written by F.

## D's approved deterministic safety cases → exact test node IDs (ready-to-apply)

| D safety case | Node ID (PR #27) | Real production path |
|---|---|---|
| Complete evidence preserves rating | `test/offline/test_evidence_gate_cli_publication.py::test_cli_valid_evidence_preserved` | CLI completion + `evidence_gate` |
| Missing selected evidence → REVIEW | `…::test_cli_missing_evidence_review_non_authoritative` | CLI gate boundary |
| Invalid analyst configuration prevents authoritative writes | `test/offline/test_evidence_gate_cli_publication.py::test_cli_unknown_config_aborts_publication` | Graph/CLI config guard |
| Original REVIEW cannot upgrade | `…::test_cli_original_review_not_upgraded` | CLI gate |
| Stale effective_rating re-evaluated | `test/offline/test_evidence_gate_graph_integration.py::test_resume_reaches_gate_with_restored_reports` + `…::test_resume_is_fresh_execution_for_gate` | Graph + Checkpoint/Resume |
| PM not published pre-gate; non-authoritative under REVIEW | `…::test_cli_pm_buffered_pre_gate_and_markdown_safe` + `…::test_cli_missing_evidence_review_non_authoritative` | CLI display/report |

Reviewed-but-flagged: `cli/display.py:display_complete_report` REVIEW/non-authoritative
branch — D reports a remaining display failure on the reviewed remote HEAD; must be
resolved before this case is claimed accepted.

## Ready-to-apply wiring (apply only after merge)
Add these as additional versioned cases in `scripts/semantic_report.py` (same
mechanism as the O5 set: real tests, per-case pass, 100% threshold, nonzero on
failure), plus a workflow step gated on O4 paths. Skeleton:

```python
# in CASES: add O4-* entries pointing at the node IDs above
# CASESET becomes "o5+o4-deterministic-v2" once O4 lands
```

No placeholder jobs are added now. Until merged, the semantic job covers **O5 only**
and explicitly lists O4 prompt/model behavior as uncovered.

## Non-claims
- This document is a mapping + dependency record, not an accepted integration.
- No O4 test is run by this PR's semantic job yet.
- Do not treat #25/#27 green checks as final-main coverage.
