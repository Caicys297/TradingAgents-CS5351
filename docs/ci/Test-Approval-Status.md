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

## Hardening (second pass)

The checker now enforces, not merely lists:
- **Trusted identity** via `docs/test-approvals/reviewers.yaml` (login→role). The
  record's declared role is ignored; the original evidence author's real login is
  mapped to a role. Implementers come from batch evidence; self-approval rejected.
- **Batch binding**: records declare `batch_id`; the job uses `pr-<number>`.
  Allowed files must cover every applicable implementation file; excluded files
  are rejected. A historical record cannot authorize a different PR.
- **Both kinds required**: test-plan approval (role per Registry, or delegation)
  AND execution-plan approval (A, or delegation). One record may approve both.
  Removed the "any valid record passes the PR" shortcut.
- **Meaning/immutability**: the original evidence **body** must reference the
  approved `plan_sha` and `plan_version`. A review `state=APPROVED` on a later PR
  is not pre-code approval.
- **Delegation**: evidence-backed only (granting A's original comment references
  the scope); default roles unchanged. Validated against the real O2 Stage-2
  A→F example (PR #18 comments `7004478311` / review `5972069186`, `aa9fda60`,
  v0.4) — scoped to that batch, not all O2.
- **History**: earliest implementation commit is computed over the batch's
  applicable files (`git log ... -- <paths>`), not the first topological entry;
  unavailable/ambiguous history → error; no impl commit despite applicable
  changes → failure.

## Workflow honesty (corrected)
The `test approval` job runs the checker **from the PR checkout** with a
read-only `GITHUB_TOKEN` (no write creds, no `pull_request_target`). A PR can
therefore modify its own checker; trust anchors are the protected `main`
reviewers mapping and the original read-only-resolved GitHub evidence. The job
comment no longer claims the PR cannot change its checker.
