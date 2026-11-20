# Test Approval Gate — Implemented (A-authorized rules)

A confirmed the gate rules (PR #30 comment `7043217684`, 2026-11-20), authorizing
implementation per REQ-GOV-01/02. This batch implements the checker, offline
tests, and CI wiring on the closure branch. **This does not retroactively approve
already-written work** (see "Process gap for this batch").

## Implemented behavior (`scripts/check_test_approval.py`)
- Reviewer roles from the Registry: **O2/O6 test plans → A; O1/O3/O4/O5 → F;
  execution plans → A.** Implementer self-approval rejected.
- Validates **original GitHub evidence** (issue comment or PR review): author,
  original timestamp, reviewer role; a machine record only **indexes** it.
- Requires immutable `plan_sha` + `plan_version`, requirement IDs, approved test
  IDs, allowed files, original `approval_time`.
- Compares approval time against the batch's **earliest implementation commit**
  (code/test/fixture/workflow; docs/transcripts are not implementation), using
  **author dates** so rebase/cherry-pick provenance is preserved.
- Fails with a specific reason on: missing record, late approval, unauthorized
  reviewer, self-approval, approver/evidence author mismatch, backdated
  (mismatched) time, unverifiable evidence / API failure, incomplete history.
- Later PR code-review cannot substitute for pre-code approval.
- Pure-documentation changes → explicit "not applicable".

## CI wiring
Job `test approval` (PR-only), NUL-separated changed files, least-privilege token
(`GH_TOKEN` read-only), does not execute untrusted PR code with privileged creds.

## Offline tests (`test/offline/test_check_test_approval.py`, 12)
Positive (valid pre-code approval; in-scope follow-up reusing approval);
negatives (missing, late, self, unauthorized, version/field mismatch, backdated
time, API failure, incomplete history, cherry-pick provenance preserved,
docs-only not-applicable). Fixture-backed API + genuine temp Git histories.

## Process gap for THIS batch (reported, not fabricated)
A's comment `7043217684` confirms the **rules** and authorizes implementation of
the gate. It is **not** a pre-code approval of the already-written semantic
runner / gate code on this branch, and there is **no** machine record under
`docs/test-approvals/` covering this CI batch. Per policy, the rule-confirmation
timestamp is not treated as retroactive approval. **Action:** if this batch is to
satisfy the gate, A/B must create a genuine pre-code approval record (or A
explicitly scopes it out as approved in-scope CI corrections). Until then this is
an honest, unresolved process item — not a passing record.

## Historical positive example
PR #8 comment `6920115438` (2026-11-16T15:02:47Z, plan `b0287da` v0.3/v0.1,
two O2 Phase-1 files) is used only as a **narrow O2 Phase-1 positive**; it is not
generalized to later O2 or CI batches.

## Note on push coverage
Net push diff (`before..after`) is **not** per-commit verification; it reports the
aggregate changed paths of the push. Per-commit verification remains an open
A/F decision for REQ-GOV-07.
