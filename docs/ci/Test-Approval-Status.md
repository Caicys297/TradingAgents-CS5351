# Test Approval Gate — Status (rules proposed, not yet confirmed)

Per the closure record, the Test Approval rules are **proposed**, not confirmed by A/B.
This batch does **not** enable an invented policy as mandatory, and there is **no**
Test Approval checker implemented here (doing so before A/B confirmation would fabricate
policy).

## Proposed rules (summary, pending A/B)
- Reuse `docs/test-approvals/TEMPLATE.md`; each approved batch links an immutable plan
  SHA/version, requirement/test IDs, allowed files and exclusions.
- Approval authority from the registry: O2/O6 test plans → A; O1/O3/O4/O5 test plans → F;
  execution plan → A. Implementer cannot self-approve.
- The original approval time must precede the batch's first **implementation** commit
  (test/fixture/workflow commits count; doc-plan commits do not).
- Small corrections within an approved scope reuse the approval; only requirement-outcome,
  public-interface, file-ownership, or material-scope changes require re-approval.
- The automated job must not fabricate GitHub timestamps; missing/late approval is referred
  to A/B, not rewritten historically.

## Positive example (from B, real record)
- PR #8 comment `6920115438`, `2026-11-16T15:02:47Z`, plan `b0287da` / v0.3 / v0.1,
  two approved files.

## Negative examples (must fail)
- Missing record; approval later than first implementation commit; unauthorized/self-approval;
  scope/version mismatch; API/history incomplete.

## What this batch does/does-not do
- **Does:** document the concrete record format and the positive/negative examples above.
- **Does not:** implement the checker, add a passing placeholder, or approve any PR.
- **To proceed:** A/B confirm the rules (or one concrete change). F then implements the
  checker + offline tests matching the confirmed policy, and A/admin wires its stable
  check name once it exists.
