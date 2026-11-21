# Administrator Handoff — Required Checks & Merge Enforcement

**Not performed by F.** This PR does not change repository settings or branch
protection. Below is what A/admin must do after the stable jobs are merged and
reviewed. Merge enforcement is **UNVERIFIED** until configured and trialled.

## Stable, actual check names (from the workflow `jobs.<id>.name`)
| Check name | Source job |
|---|---|
| `requirements schema` | `requirements-schema` |
| `type check` | `type-check` |
| `dependency audit` | `dependency-audit` |
| `ai-use log` | `ai-use-log` (PR-only) |
| `semantic (deterministic O5)` | `semantic-deterministic` |
| `tests (py3.11)` / `tests (py3.12, America/New_York)` / `tests (py3.13)` / `tests (py3.14)` | `test` matrix |
| `ruff (strict, full repo)` | `lint` |
| `clean-install smoke` | `smoke-install` |

Notes:
- `ai-use log` runs only on `pull_request`; required-check selection must account for
  it being PR-only (it will not appear on `push`).
- Do **not** add a required check whose name does not exist (e.g. never-created Test
  Approval / O4 checks) — that would make all PRs permanently pending. Add those only
  after F delivers them with stable names.

## Required-review settings & bypass
- Require at least one approving review from a non-author.
- Keep a documented **administrator bypass** only for emergencies; record each use.
- For safety-critical path changes, require human review + an accompanying architecture
  decision (per REQ-GOV-08). Path list is a C/D deliverable.

## Controlled, non-merged verification procedure (A/admin)
1. On a throwaway branch/PR (not merged), introduce a change that fails **one** required
   check (e.g. a schema violation).
2. Confirm GitHub shows the PR as **blocked** and merge is prevented by that check.
3. Separately, a PR with a failing required check and/or missing qualifying review must be
   blocked by review requirements.
4. Record: the settings changed, the failing check name, the blocked-merge evidence
   (screenshot/PR state), and the trial PR link. Keep the trial PR unmerged/closed.
5. Only after this record exists may "merge enforcement" be marked verified.

No setting was changed here; no trial PR was created by F.
