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

## Hardening (third pass)

- **Approval meaning (A1):** `_approves_plan` now requires an explicit approving
  statement (approve/批准/同意…) plus plan SHA+version; a neutral SHA/version
  mention is not approval.
- **Source-bound scope (A2):** declared `allowed_files`/requirement/test IDs are
  trusted only if the original body names the files, or an authoritative
  `binding` record (authorized human source) explicitly binds them; otherwise the
  gate fails and asks for that binding. It never invents/backdates approval.
- **Delegation (B1):** requires `to_login`, `to_role`, feature, batch, plan
  SHA+version, an authorization statement referencing grantee+plan, and a
  grantor role A whose original time strictly precedes the delegated approval.
- **Self-approval (C1):** implementers are resolved from the batch's Git authors
  (commits touching applicable files), unioned with declared fields; if identity
  cannot be established the gate fails rather than assuming none.
- **Wiring (W1):** `type check` and `dependency audit` are now PR-only (they need
  a merge-base); push-time per-commit verification is an explicit open A/F
  REQ-GOV-07 decision, not a silent green.

## Hardening (Phase 2 — four defects)

- **Correction 1 (binding vs clarification):** a `binding`/`clarification` is a
  **separate, currently-dated** authorized record that may identify what the
  original approval already covered. It cannot expand scope beyond the immutable
  plan, grant retrospective approval, or predate the approval it clarifies; both
  timestamps are reported separately. Historical prose is not auto-interpreted —
  missing/ambiguous evidence fails with an actionable request for an authorized
  source-binding record.
- **Correction 2 (immutable plan):** the record names `plan_sha` (full 40-hex) +
  `plan_path`; the plan is retrieved at that exact commit and the declared
  version, requirement IDs, test IDs and allowed files must appear in the actual
  plan. PR-declared fields alone are not trusted; missing/mismatched plans fail.
- **Defect 3 (implementer identity):** implementers are resolved from the batch
  commits' **GitHub account association** (`commit.author.login`) or an
  authorized base-trusted `implementers.yaml`; unknown identity fails explicitly.
  (Account association is an identity signal, not cryptographic proof of
  authorship.) Self-approval is rejected even with omitted/false declarations.
- **Correction 3 (GOV-07 per-commit):** `type check` and `dependency audit` now
  run on **pull_request and push** via shared `scripts/ci_event.py`
  (merge-base for PR, before..after for push). Type checking verifies **each
  commit** in the range against the trusted base baseline; dependency audit
  reports per-commit manifest changes and audits the installed env. Zero/missing
  push base, tags and unavailable history fail closed (no silent green/working-tree
  fallback). "Every commit" is treated as an existing requirement.

## Hardening (Phase 2 review — three findings)

- **Explicit evidence (finding 1):** approval and delegation now require an
  explicit machine-verifiable marker in the authorized evidence body —
  `TEST-APPROVAL: plan=<40hex> version=<v> kind=<k> scope=<files>` and
  `TEST-DELEGATION: grantee=<login> plan=<40hex> version=<v> kind=<k> until=<batch|iso>`.
  Keyword inference is no longer accepted. A later clarification must cite the
  original evidence id and confirm only the plan/kind/scope the immutable plan
  supports (no expansion, no predating). Edit metadata is checked: evidence with
  `updated_at != created_at` cannot establish content at approval time → human
  verification required. Mentions of a file do not establish approval for it.
- **Per-commit mypy exit (finding 2):** `_mypy_at_rev` returns `(lines, exit, stderr)`;
  a nonzero exit without usable diagnostics (tool error) fails and names the
  commit; an intermediate commit with a new diagnostic fails even if HEAD is clean.
- **Per-commit dependency audit (finding 3):** each dep-changing commit's
  `requirements.txt` is extracted at that revision and audited with pip-audit
  against the trusted baseline; an intermediate commit's disallowed finding fails
  even if HEAD is clean; a resolver/scanner failure is a non-clean failure (exit 2).

## Hardening (Phase 2 follow-up — two findings)

- **Kind-scoped credit:** a single `TEST-APPROVAL` marker credits ONLY the kind it
  names; one `test_plan` marker never satisfies `execution_plan`, even if the
  record claims both. Both kinds require separate authenticated evidence. A
  clarification must identify the exact original artifact (id/type/source PR) and
  bind the same plan/version/kind/scope; a wrong original reference or a different
  artifact is rejected; a clarification cannot supply missing original approval.
- **Historical dependency audit:** each dep-changing revision is audited in an
  isolated `git worktree` so `requirements.txt` (`.`) resolves THAT revision's
  `pyproject.toml`, not HEAD; worktree always removed. Controlled-scanner test
  shows two revisions with identical `requirements.txt` but different pyproject
  deps are seen distinctly; an intermediate finding fails while HEAD is clean.

## Historical approval compatibility route (A review 6005119233)

A bounded, separate route for **legacy natural-language approvals** written before
structured markers existed. It is distinct from the structured `TEST-APPROVAL`
marker route used for new batches.

- **Trusted source (protected base):** `docs/test-approvals/historical-approvals.yaml`
  is loaded from `origin/<base>` only (like `reviewers.yaml`), so a PR cannot
  self-declare it. **Authorized mappings are reviewed via the protected base:** a
  maintainer lands/updates this file on the base branch through normal review (it is
  part of the reviewed base tree A/B approve), and a PR that merely adds or edits the
  mapping in its own diff is not trusted (see the untrusted-PR-tree negative).
- **One entry = one kind, one plan:** each entry binds a **singular** `kind`
  (`test_plan` **or** `execution_plan`) for one plan of one exact original artifact:
  `batch_id` (the actual workflow batch, e.g. `pr-8`/`pr-18`, not a generic
  `batch-1`), `feature`, `artifact_type`, `artifact_id`, `pr`, `actor`, `kind`,
  full plan identity (`plan_sha` 40-hex + `plan_path` + `plan_version`), `scope`,
  `body_sha256`, `original_time`, and optional `delegation`.
  Because one artifact may approve multiple plans (e.g. A #8 approves both plans),
  it is split into **separate entries** by the real plan version/path.
- **Verification:** the checker re-fetches the original artifact and validates the
  **actual fetched record**: bound actor == original author; the original was not
  edited after creation; `body_sha256` matches the fetched body; the fetched
  `original_time` equals the binding; the record's plan identity (SHA+path+version)
  matches; for a review the fetched `state` must be `APPROVED` and (when present)
  `commit_id` must equal the plan SHA. Role must be authorized for the kind, or a
  **verified delegation** applies (below). Scope equals the binding, is limited to
  the immutable plan, respects exclusions and covers applicable files, and the
  **original timestamp** (never the mapping's) precedes first implementation.
- **Delegation (`delegation`):** instead of a bare `delegated_by` login, the entry
  binds an authorized A grantor artifact by `artifact_type`/`artifact_id`/`pr` with
  its `body_sha256` and `original_time`, plus the `grantee` (must equal the approval
  author) and delegated `kind`. The checker fetches the grantor, requires role A
  (so a comment by B never authorizes), digest/time match, and the grantor's
  original time **strictly earlier** than the approval it authorizes.
- **Cannot:** accept arbitrary prose by keywords, accept a PR-declared/edited/
  changed/unverifiable original, borrow an entry across batch/kind/plan, widen
  scope, or count a later record/mapping timestamp as approval; the mapping only
  records interpretation of the original.
- **#32 still fails** for lack of a historical pre-code approval for this batch;
  structured route and fail-closed behavior are unchanged.

**Effective date (A):** normal (marker) enforcement begins for the next
implementation batch started after #32 merges; this historical review does not
retroactively require new marker text on old approvals.

### Legacy positives/negatives exercised (fixtures preserve original text)
The approval **source** is distinct from the **implementation batch**: an approval
written on PR #8 can authorize a later batch (`pr-16`), and PR #18 approvals can
authorize batch `pr-23`. The source PR for an issue comment is derived from
GitHub's returned `issue_url`, never from a record-declared `pr`.

- Positive: A #8 comment `6920115438` (source PR #8; implementation batch `pr-16`)
  approves BOTH plans; bound as **two entries** —
  `test-plans/O2-Test-Plan-v0.3-DRAFT.md` (v0.3) and
  `test-plans/O2-OpenCode-Execution-Plan-v0.1-DRAFT.md` (v0.1); scope = phase-1
  manifest writer + its test (`tradingagents/repro/manifest.py`,
  `test/offline/test_o2_manifest.py`).
- Positive: A #18 comment `7004478311` (exec) + F review #18 `5972069186` (test) on
  `aa9fda60…` v0.4 Stage-2 plans (source PR #18; implementation batch `pr-23`;
  `test-plans/O2-Stage-2-Test-Plan-v0.4-DRAFT.md`,
  `test-plans/O2-Stage-2-OpenCode-Execution-Plan-v0.4-DRAFT.md`; scope
  `tradingagents/cli/run.py`, `test/offline/test_o2_cli_manifest.py`), F credited
  **only** via A's verified delegation (grantor `7004478311`, earlier timestamp).
  Note: #18 comment `7004545668` is by **B** and cannot authorize.
- Negative: missing original, edited original, body-digest mismatch, API source PR
  (`issue_url`) mismatch, late approval, cross-batch/cross-plan borrowing,
  out-of-scope, review not `APPROVED`, missing delegation, delegation by B,
  delegation timestamped after the approval, declared kinds beyond the bound entry,
  and untrusted (PR-tree-only) mapping. (A record that misdeclares its `pr` is not
  rejected on that basis alone — the source PR comes from `issue_url`.)
