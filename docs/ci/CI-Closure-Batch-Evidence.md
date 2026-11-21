# CI Closure — Batch Evidence Inventory & Process Deviation

Honest inventory of the authorizations and scopes covering this continuation
branch (`feat/ci-six-gates-closure`) relative to approved PR #30 (`e085bfd`).
**This is a record of what evidence exists — not a manufactured approval.**

## Actual implementation timeline (author dates, +08:00)
| Commit | Author time | Change |
|---|---|---|
| `d964724` | 2026-11-20T22:18:43+08:00 | deterministic semantic reporting + closure docs |
| `78a3fce` | 2026-11-20T23:01:19+08:00 | semantic runner applicability + robust execution/exit |
| `268a8e1` | 2026-11-20T23:57:03+08:00 | semantic push-event applicability |
| `9ebfc47` | 2026-11-21T00:22:25+08:00 | Test Approval Gate implementation |
| `4ff57a4` | 2026-11-21T00:39:46+08:00 | Test Approval hardening |

## Actual authorizations found
- **PR #30 @ `e085bfd`** — A formally approved the consolidated six-gate batch at
  that commit. This covers the PR #30 scope only; it does **not** pre-approve the
  closure commits above (they were written after `e085bfd`).
- **A comment `7043217684`** (2026-11-20T15:19:39Z) — confirms the **Test Approval
  Gate rules** and authorizes F to *implement the gate*. It is a **rule/scope
  authorization for building the checker**, not a pre-code approval of the
  already-written semantic runner / closure code.
- **A comment `7041514834`** — the §1 proposal (rules + division of labour).
- **PR #18** A `7004478311` / F review `5972069186` (`aa9fda60`, v0.4) — used only
  as the **delegation fixture/example**; it authorizes O2 Stage 2, not CI.

## Deviation (exact)
The closure implementation commits (`d964724` .. `4ff57a4`) have **no pre-code
Test Approval record** under `docs/test-approvals/`, and `reviewers.yaml` is a
**first introduction** on this branch (absent on base `origin/main`). Under the
gate's own rules:
- the implementation timeline is **not** preceded by an authorized pre-code test
  plan + execution plan approval for the CI-closure batch;
- `7043217684` is a rule confirmation and cannot be backdated into a pre-code
  approval of code already written.

## Missing authority / requested disposition (A/B)
One of the following is required, recorded **as a later disposition** (never
reported as historical pre-code compliance):
1. A/B create a genuine pre-code approval record for the CI-closure batch (with
   original evidence + times), or
2. A explicitly scopes these CI-closure commits as **approved in-scope CI
   corrections** under the existing #30 authorization, recorded with its date,
   or
3. A/B direct a remediation (e.g. re-do under a fresh approved batch).

Until one exists, this gate has **no passing record for this branch** and CI
`test approval` will fail closed on the closure PR. This is documented, not
silently exempted.

## Verification limits
- Author dates are evidence, not proof of preserved provenance; the checker flags
  non-monotonic/ambiguous history but cannot cryptographically prove authorship.
- `reviewers.yaml` bootstrap (base absent) is allowed for first introduction with
  an explicit A-review notice; it is not silently trusted.
- Locally verified only; not remote-CI verified until submitted.
