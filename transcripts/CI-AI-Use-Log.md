# CI — AI-use log (six-gate consolidated batch)

Owner: Member F (CI). This log records verifiable AI (OpenCode) use on the
consolidated six-gate CI batch, per REQ-GOV-06. It preserves existing log
conventions: the repository does not prescribe a fixed path or schema, and session
evidence lives under `transcripts/` (redacted). This entry does not claim any
approval or test result that does not exist.

## Format notes

- Task: implement the authorized CI gate checkers (Requirements Schema, AI-use
  structural check, type checking, dependency audit) plus deterministic O5 semantic
  cases, in one consolidated PR.
- Usage scope: repository inspection, checker scripts, offline tests, CI workflow
  wiring, and baseline files. No production feature code changes.
- Implementation baseline (real main): `99612ca64445ec650b9a5f42203fa166783800b1`.

## Verified activities

| # | Activity | Evidence basis | Time (UTC) |
|---|---|---|---|
| 1 | Upstream verification via GitHub API (main `99612ca`, PR #27 draft, PR #29 merged, PR #30) | This OpenCode session | 2026-11-20 |
| 2 | Authored `scripts/validate_requirements.py`, `scripts/check_ai_use_log.py`, `scripts/typecheck.py`, `scripts/dep_audit.py` | This OpenCode session | 2026-11-20 |
| 3 | Authored offline checker tests `test/offline/test_ci_gate_checkers.py` | This OpenCode session; pytest output | 2026-11-20 |
| 4 | Wired CI jobs + baselines (`ci/baselines/mypy-baseline.txt`, `pip-audit-baseline.json`) | This OpenCode session | 2026-11-20 |

## Session / export reference

- Tool: OpenCode. The exact model string is not recorded here.
- Implementation commit association: baseline main commit
  `99612ca64445ec650b9a5f42203fa166783800b1`; this batch's own commit is recorded
  on the PR (the log does not need to contain its own final SHA).
- Session/export evidence: `transcripts/CI-session-export.md` is an **authored
  activity summary**, not a raw machine export; the genuine raw session is retained
  by Member F outside the repository. A reviewer-accessible raw export must be
  attached by F before final acceptance.

> Truthfulness of this log is verified by humans; the automated CI check verifies
> only structure and reference association (task/scope/commit markers plus a real
> session or resolvable export reference), not authenticity.
