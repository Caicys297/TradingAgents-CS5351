# CI — AI-use log (six-gate consolidated batch)

Owner: Member F (CI). This log records verifiable AI (OpenCode) use on the
consolidated six-gate CI batch, per REQ-GOV-06. It preserves the existing log
conventions: the repository does not prescribe a fixed path or schema, and raw
session evidence lives under `transcripts/` (redacted). This entry does not claim
any approval or test result that does not exist.

## Format notes

- Task: implement the authorized CI gate checkers (Requirements Schema, AI-use
  structural check, type checking, dependency audit) in one consolidated PR.
- Usage scope: repository inspection, checker scripts, offline tests, CI
  workflow wiring, and baseline files. No production feature code changes.
- Implementation baseline: `a2644eba507493df8305f32cd30003d3eeb33d61`.

## Verified activities

| # | Activity | Evidence basis | Time (UTC) |
|---|---|---|---|
| 1 | Repository inspection at main `a2644eb` (workflows, pyproject, docs/req, transcripts) via GitHub API | This OpenCode session | 2026-11-20 |
| 2 | Authored `scripts/validate_requirements.py`, `scripts/check_ai_use_log.py`, `scripts/typecheck.py`, `scripts/dep_audit.py` | This OpenCode session | 2026-11-20 |
| 3 | Authored offline checker tests `test/offline/test_ci_gate_checkers.py` (16 cases, all passing) | This OpenCode session; pytest output | 2026-11-20 |
| 4 | Wired CI jobs + baselines (`ci/baselines/mypy-baseline.txt`, `pip-audit-baseline.json`) | This OpenCode session | 2026-11-20 |

## Session / export reference

- Tool: OpenCode. The exact model string is not recorded here.
- Implementation commit: recorded when this batch is committed (see the PR's
  commit list). No log commit is required to contain its own final SHA.
- Session/export evidence: condensed redacted export at
  `transcripts/CI-session-export.md` (real, resolvable in-repo). The full raw
  session is retained by Member F outside the repository.

> Truthfulness of this log is verified by humans; the automated CI check verifies
> only structure and reference association (task/scope/commit markers plus a real
> session or resolvable export reference), not authenticity.
