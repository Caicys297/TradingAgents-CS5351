# Authorized Protection Verification Trial — E4 / E1 (NEVER MERGE)

**Status: controlled verification PR. This pull request MUST NEVER be merged.**

This branch exists only to empirically verify that `main`'s branch protection actually blocks merges when required conditions are not met. It contains documentation only.

## Authorization

- Original trial authorization: PR #37 comment `7073583150` (E1/E2/E4/E5; E3 excluded).
- Latest instruction to proceed empirically: PR #37 comment `7073837395`.
- Repository administrator (A) owns the protection configuration; this trial does not change any settings.

## Scope of this change

- One harmless Markdown file under `docs/ci/` (this file).
- No workflow, Python, requirements-registry, or production-code changes.
- Because the change touches only `docs/`, the `test approval` and `ai-use log` gates are **not applicable** (verified against the actual checkers), so they neither require a fabricated approval nor fail.

## Planned observations

- **E4:** with all required checks passing and no qualifying review, confirm `reviewDecision = REVIEW_REQUIRED` and that merge is blocked.
- **E1:** after a genuine non-author review on the exact SHA, confirm merge eligibility is restored.

## Rules

- Non-bypass observing identity only.
- No self-approval, no impersonation, no merge.
- This PR will be closed (not merged) after observations are captured.
