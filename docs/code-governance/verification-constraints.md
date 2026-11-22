# Verification constraints and evidence rules

Before implementation, record the requirement and test IDs, test-plan version, approved file scope, reviewer, approval time, and baseline. The repository's `test approval` checker validates machine-readable records on PRs; its passing result does not replace human review. Preserve batch-specific process deviations as deviations.

Every fit criterion needs at least one test. Every invariant needs a test that fails on a real violation. Each test must cite the requirement or invariant it verifies. In every new round, run all earlier rounds' relevant suites and record any regression rather than narrowing the suite to hide it. Verification has three tiers: structural (imports, module boundaries, permissions and architecture checks), regression (prior suites), and behavioral (specified quality thresholds and zero safety escapes). A tier is complete only when its actual evidence exists.

Run the approved deterministic `test/offline/` cases, the default regression suite, and applicable static/contract/security/API checks. Confirm that the selected cases were collected, including negative cases and invariant violations. Report results at the tested SHA. Separate offline checks, live-service probes, and end-to-end behavior; one successful branch probe is not proof of all branches.

The CI workflow has jobs for tests, Ruff, type and dependency checks, contract/security/API/permissions governance, test approval, and AI-use evidence. `test approval` and `ai-use log` are PR-only and can be skipped on a main push. The F handoff records 17 required checks in administrator screenshots and PR #41 E1/E2/E4/E5 behavior: missing review and failing checks blocked, then a repaired, reapproved PR became eligible. PR #41 was closed without merge. E3 (missing required result) was not run. There was no independent administrator API readback; do not claim each check was separately failure-tested.

PR review, CI, branch protection, and agent path instructions are different controls. A green CI job at one SHA does not approve another SHA. A change to a reviewed commit may dismiss stale review. Never bypass a red check or report it as passed.
