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
- Session/export evidence: `transcripts/CI-opencode-session-export.json` is a
  bounded record derived from a genuine `opencode export
  ses_e27f33c94ffeOKeCXPrAQQW93Z --sanitize` run (session id, project id,
  756 messages = 75 user / 681 assistant; content bodies omitted). The full 2 MB
  sanitized export is retained by Member F outside the repo; its sha256
  `61dd03b4cf3d1cc155dd32fd77b3396ba5727e223a8839c67e1756d1eff7c922` is recorded
  in the bounded record for verification. Sanitization verified: 0 machine-absolute
  paths, 0 key-like strings.
- `transcripts/CI-session-export.md` is an **authored activity summary**, kept for
  human context; it is **not** a raw export and does not by itself satisfy the
  genuine-export requirement.

> Authenticity/access is verified by humans; the automated check verifies only
> structure and reference association, not truthfulness.
