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

> Authenticity/access is verified by humans; the automated check verifies only
> structure and reference association, not truthfulness.
