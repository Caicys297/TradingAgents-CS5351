# CI — AI-use log (six-gate consolidated batch)

Owner: Member F (CI). Records AI (OpenCode) use on the consolidated six-gate CI
batch, per REQ-GOV-06. The repository does not prescribe a fixed path or schema.

## Format notes

- Task: implement authorized CI gate checkers (Requirements Schema, AI-use
  structural check, type checking, dependency audit) plus deterministic O5
  semantic cases, in one consolidated PR.
- Usage scope: repository inspection, checker scripts, offline tests, CI workflow
  wiring, baselines. No production feature code changes.

## Entry (this PR)

- Task: six-gate CI checkers (schema, ai-use, type, dependency) + deterministic O5.
- Usage scope: scripts/, test/offline/, .github/workflows/, ci/baselines/, transcripts/.
- Implementation commit: `4187333b6325d6b3168b87c76bae4ae401fb3111` (this PR's
  implementation head; in `origin/main..HEAD`). Follow-up evidence-only commits may
  reference preceding implementation commits; no self-SHA requirement.
- Session/export evidence (accessible): `transcripts/CI-session-excerpt.md` — a
  bounded excerpt of **real dialogue** (user instructions, assistant actions, tool
  calls/status) derived mechanically from the genuine raw export, with a documented
  extraction/redaction method and source sha256. This is the reviewer-accessible
  transcript content.
- Provenance metadata (NOT a substitute for content): `transcripts/CI-opencode-session-export.json`
  records session/project id, message counts and the sanitized-export sha256
  `61dd03b4cf3d1cc155dd32fd77b3396ba5727e223a8839c67e1756d1eff7c922`. The full raw
  and sanitized exports are retained by Member F at
  `opencode_export_reply/preserved_session_evidence/` (raw sha256
  `cd3433a1ae1af7236e9b324c7f535910557cbe04cdde86cdb1f50ee86f90e8d3`).
- `transcripts/CI-session-export.md` is an **authored activity summary**, kept for
  human context only; it is **not** transcript content and is explicitly NOT accepted
  as session evidence.

## Entry — Draft PR #32 continuation (CI fixes)

- Task: fix two CI failures on Draft PR #32 — make the type-check base-resolution
  test independent of a real mypy binary, and add this AI-use entry.
- Usage scope: `scripts/typecheck.py` test, `test/offline/test_ci_gate_checkers.py`,
  and `transcripts/CI-AI-Use-Log.md`. No production feature code.
- OpenCode session: `ses_e27f33c94ffeOKeCXPrAQQW93Z`
  ("Revising CS5351 CI Gate plan for team review") — the session that produced this
  continuation.
- Session/export evidence (accessible): `transcripts/CI-session-excerpt.md` (genuine,
  reviewer-accessible excerpt of the session's real dialogue).
- Implementation commit: `3ec9c808ff02ea9d982916ebe27968efe1ea6bad` (in the PR #32
  range `origin/main..HEAD`; follow-up evidence-only commits may reference preceding
  implementation commits).

> Authenticity/access is verified by humans; the automated check verifies only
> structure and reference association, not truthfulness.

## Entry — #32 historical-approval compatibility repair (A review 6005119233)

- Task: implement and then tighten the bounded historical natural-language
  approval compatibility route for #32 (A review 6005119233): bind the real
  workflow batch, exact original artifact (source PR derived from GitHub's
  `issue_url`), one kind + full plan identity, original body digest/timestamp,
  review `APPROVED` state and `commit_id`, and a verified A delegation for F's
  #18 test approval; align the focused tests to the real #8/#18 evidence, plan
  identities, versions and scopes.
- Usage scope: `scripts/check_test_approval.py`,
  `test/offline/test_check_test_approval.py`, `docs/ci/Test-Approval-Status.md`,
  and `transcripts/CI-historical-approval-fix-excerpt.md`. No production feature
  code, type/dependency/semantic logic, or #33 changes.
- OpenCode session: `ses_e27f33c94ffeOKeCXPrAQQW93Z`.
- Session/export evidence (genuine, reviewer-accessible, specific to this repair):
  `transcripts/CI-historical-approval-fix-excerpt.md` — a bounded excerpt derived
  from a fresh `opencode export` of this session (local paths redacted). This is
  the covering excerpt for the work described above; the older generic
  `CI-session-excerpt.md` is not used to establish this repair.
- Implementation commits (original, preserved): `296146cf6dc969e99db6536f13b5113b270a27bb`
  (initial route) and `7425efe41dd8b0f32512ad396fa0d9f9782c72e4` (tightened route +
  tests).
- Replayed equivalents on the branch (same trees, different identities):
  `296146cf… → 8e2569431c61a4941774b42a002e439534f1f93b` and
  `7425efe4… → 37dbc3265d0b158424f54dd46bee1c018e818f97`. Git-over-HTTPS
  connection failures (github.com:443 unreachable) prevented a normal `git push`,
  so the commits were re-created through the GitHub Git Data API; this changed
  commit identities while preserving the final tree (remote HEAD tree ==
  `f53c29b`). The original SHAs above are kept verbatim; the replayed SHAs are the
  identities actually reachable from PR #32's branch head (`95860ca…`).

## Entry — Test Approval authorization migration (separate prerequisite PR #38)

- Task: separately authorized migration enabling a **non-implementer A** to review
  **BOTH** the Test Plan and Execution Plan for **genuine F-implemented
  CI/governance batches** (feature `CI`), plus a follow-up correction that enforces
  the qualification boundary — implementers resolved to trusted role F, and actual
  changed files + immutable approved scope restricted to CI/governance paths — so a
  product implementation merely relabelled `CI` or a non-F batch cannot use the
  special authority. Applied on the marker and historical routes; delegation cannot
  stand in for A on a CI test plan.
- Usage scope: `scripts/check_test_approval.py`,
  `test/offline/test_check_test_approval.py`, `docs/ci/Test-Approval-Status.md`, and
  this AI-use log plus the session excerpt (evidence-only cleanup). No production
  feature code; PR #37's workspace/files/branch/records untouched.
- OpenCode session: `ses_e00d872f7ffe13z09Dg34QBWSc` ("CI Test Approval authorization").
- Session/export evidence (genuine, reviewer-accessible, specific to this migration):
  `transcripts/CI-Test-Approval-Authorization-Migration-excerpt.md` — a bounded
  excerpt derived from a fresh `opencode export` of the session above, with local
  paths redacted; raw export sha256
  `e4c502428f3e10a7700816af0075bfa9f69dd6d5b95525ad1824c487a00cc0db`
  (retained locally, not committed). This excerpt is the covering evidence for the
  work described here; unrelated main-batch (six-gate) evidence is not reused.
- Implementation commits (in the PR #38 range `origin/main..HEAD`):
  `76eef822e82eafaa2283493a5b3a0c4b20953483` (authorization migration) and
  `fd798b47017afa7b9bd38ce1f997659b963c6a27` (qualification-boundary correction).
  A follow-up evidence-only commit follows these.

> Authenticity/access is verified by humans; the automated check verifies only
> structure and reference association, not truthfulness.
