# Permission Model

**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
**Owner:** C (document), with A as the authority for any new or widened permission.

**Integration note (this PR):** The statements below about missing D3 files are a historical audit of the named baseline commit. This PR adds those files. The JSONC file is a documented whitelist, but no OpenCode filesystem enforcement has been verified; CI and human review remain separate controls. Do not read the historical gap table as the status after this PR.

---

## 0. Scope and honesty statement

The course requires a permission model with **file-level read/write rights for
each AI coding agent's role, default no read / no write, every path explicitly
whitelisted**, in machine-readable form at `.opencode/permissions.jsonc`.

**That file does not exist at this baseline SHA**, and neither do `AGENTS.md`,
`Prompt.md`, `.opencode/rules.md`, `.agent/rules.md`, or the three
`docs/code-governance/*.md` files. `.opencode/` and `.agent/` are empty
directories at `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`.

**Scope of that statement:** it is a fact about **that commit only**. It is not a
claim that the project never authored these files, that no other branch or later
commit added them, or that the team never operated under path-scoped
instructions — review records show reviewers requiring an approved file list per
batch (§5 P3). The absence is verified for this SHA and is stated only for this
SHA.

This document therefore does three things:

1. Records what **is** machine-enforced today (CI guards and pytest).
2. Records what exists only as **approved scope** in human records (PR comments,
   registry contract text).
3. States plainly that the **default-deny, per-path whitelist** the course asks
   for is **not implemented** — rather than describing an aspiration as if it
   were a control.

**This document does not add, widen or reinterpret any permission granted by A.**
Every rule below is traced to an existing record; where no record exists, the row
says so.

---

## 1. Three different things that get called "permission"

| Layer | Question it answers | Enforced by | Status |
|---|---|---|---|
| **L1 Machine-enforced** | Does CI/git/test block the change? | `ci.yml` jobs, `scripts/check_*.py`, `tests/` | Implemented |
| **L2 Approved scope** | Did an authorized person approve this work in this file? | PR comments, test-approval records | Recorded, human-checked |
| **L3 Document rule** | What is the team supposed to do? | Registry contract text, plans | Declared only |

A rule existing at L3 does not imply L1. Section 5 states, per rule, which
layers actually hold.

---

## 2. Human roles and their authority

From `development_contract.approval_roles` and
`development_contract.integration_owner` in
[`docs/req/requirements.yaml`](https://github.com/Caicys297/TradingAgents-CS5351/blob/252fe311d8d1483b5713de69b04ce2769c33f1dd/docs/req/requirements.yaml):

| Role | Authority recorded |
|---|---|
| **A** | Owns the feature set; approves **execution scope** for every scoped plan before first code edit; reviews test plans for **O2** and **O6** |
| **B** | Maintains the Registry and its schema |
| **C** | **Sole editor/integrator** of `cli/run.py`, `trading_graph.py` and rating-output wiring for O2/O4/O6 |
| **D** | O4 safety semantics and D-owned offline tests |
| **E** | O5 requirements and the news adapter |
| **F** | Reviews test plans for **O1/O3/O4/O5**; owns CI and test tooling |

**No role is granted a filesystem permission by this table.** It allocates
authority to approve and edit by convention, subject to human review.

---

## 3. Path-level rights

### 3.1 What is claimed at L2/L3

| Path | Owner | Basis |
|---|---|---|
| `cli/run.py` | C only | `integration_owner` |
| `tradingagents/graph/trading_graph.py` | C only | `integration_owner` |
| Rating-output wiring (in `cli/run.py`) | C only | `integration_owner` |
| `tradingagents/dataflows/vendors/yahoo/news.py` | E | PR #36 file list; E's commits |
| `tradingagents/dataflows/macro_news_filter.py` | E (selector), consumed by others | Registry `selector_module`; S1 ownership |
| `tradingagents/agents/evidence_gate.py` | D | O4 ownership records |
| `test/offline/test_input_condensation.py` | O3 owner | plan/PR records |
| `docs/req/requirements.yaml`, `req-schema.json` | B | `approval_roles`, PR #3 discussion |
| `.github/workflows/ci.yml` | F | CI ownership records |

### 3.2 What is enforced at L1

**Nothing in the list above is enforced by a machine check.** There is no
`.opencode/permissions.jsonc`, no CODEOWNERS file, and no CI job that fails when,
for example, a non-C author edits `cli/run.py`. The rule holds because reviewers
apply it, and because the approval gate (§4.2) requires the changed files to
match an approved file list.

The approval gate is therefore the closest thing to a path-level control: an
unapproved *file* cannot ride along with an approved change.

---

## 4. Machine-enforced controls

### 4.1 Workflow permissions (`governance permissions`)

`scripts/check_permissions.py` implements one rule, quoted from its own header:

> "untrusted PR code must not obtain write credentials or secrets — **NOT a
> blanket ban on all write permissions**"

What it checks (fail-closed; ambiguity is a failure):

- workflow-level and job-level `permissions`, honouring inheritance;
- any `write-all`;
- `permissions:` values that cannot be resolved to read-only;
- PR-reachable (`pull_request`) jobs whose **effective** permissions include any
  `write` scope;
- `pull_request_target` combined with secrets or a PR-head checkout;
- PR-reachable checkout whose `persist-credentials` is not explicitly `false`;
- removal of the baseline `permissions` block;
- unsafe inheritance (a PR job with no `permissions` when the workflow grants
  more than baseline).

**Current baseline:** `ci.yml` declares
`permissions: contents: read` and `pull-requests: read`. Both workflows
(`ci.yml`, `release-assets.yml`) declare their own blocks.

**Applicability:** the job runs when a workflow file (or the guard/config) changes.
It is a **static check of the declared boundary** — it does not prove every
runtime credential flow.

### 4.2 Test approval (`test approval`)

`scripts/check_test_approval.py`. Approves *scope*, which indirectly bounds which
files may change:

- every changed file must fall inside the record's `allowed_files`;
- the approval evidence must carry a machine-readable approval marker binding
  plan SHA, version, kind and scope, or match a base-trusted historical binding;
- the approval must predate the first implementation commit;
- a record may not self-approve (the approver must not also be an implementer).

**Pull-request only.** On a `push` to `main` the job is `skipped`, which is why a
main-run shows it as skipped rather than successful.

**Recorded real-world behaviour:** the gate is observed **passing** on a complete
batch — #37 approval-closure run [`44979161445`](https://github.com/Caicys297/TradingAgents-CS5351/actions/runs/44979161445)
at `1c0b740`, 17 checks successful. A real *rejection* of a complete PR is **not**
recorded; the negative cases are unit-level. **PR #38 remains a batch-specific
process deviation** and is not generalised here.

### 4.3 AI-use evidence (`ai-use log`)

`scripts/check_ai_use_log.py`. A PR changing code or prompts must add AI-use
evidence under `transcripts/`, with `task`, `scope`, `commit` labels, a real
session/export reference, no machine-absolute paths, and an implementation
commit that exists inside the PR range.

### 4.4 Contract / security / API guards

`scripts/check_contracts.py`, `check_security.py`, `check_api.py` run as three
separate CI jobs on safety-relevant paths.

### 4.5 Import boundary

`tests/test_layering.py` asserts that only `tradingagents/dataflows` imports
`yfinance`. This is the only module-boundary rule enforced as a test.

---

## 5. Rule-by-rule enforcement status

| # | Rule | L1 machine | L2 approved scope | L3 document | Evidence |
|---|---|---|---|---|---|
| P1 | Untrusted PR code must not obtain write credentials or secrets | **Yes** | — | — | `check_permissions.py`, job `governance permissions` |
| P2 | Baseline workflow permissions are read-only | **Yes** | — | — | `ci.yml:9-11` |
| P3 | Changed files must match an approved scope | **Partly** | Yes | — | `check_test_approval.py` `allowed_files`; historical binding required |
| P4 | Approval must predate implementation | **Yes** | Yes | — | `check_test_approval.py` earliest-impl rule |
| P5 | Approver must not be an implementer | **Yes** | — | — | `check_test_approval.py` self-approval rule |
| P6 | Code/prompt PRs must carry AI-use evidence | **Yes** | — | — | `check_ai_use_log.py` |
| P7 | Only the data layer may import `yfinance` | **Yes** | — | — | `tests/test_layering.py` |
| P8 | Only C edits `cli/run.py` / `trading_graph.py` / rating wiring | **No** | Yes | Yes | `integration_owner`; no automated check |
| P9 | Per-role, per-path read/write, default deny | **No** | — | — | `.opencode/permissions.jsonc` **absent** |
| P10 | Coding agent reads `AGENTS.md` as the single entry point | **No** | — | Yes (course) | `AGENTS.md` **absent** |
| P11 | Safety-critical changes need an architecture decision + human review | **No** | Partly | Yes | `REQ-GOV-08`; branch protection is a repo setting, not a checked-in file; no per-change architecture-decision link is recorded |
| P12 | Project covenant in `.agent/rules.md` | **No** | — | Yes (course) | `.agent/rules.md` **absent** |

**Reading P8–P12:** these are real team obligations that a machine does not
check. They are not "permissions" in the course's sense, and listing them as if
enforced would be false.

**Reading P1–P7:** "Yes" in column L1 means a checker exists and enforces its
rule; it does **not** mean the rule has been observed blocking a real merge. The
recorded real blocking event is the PR #41 E2/E5 Schema/regression chain (§4.2
and [`architecture-blueprint.md`](architecture-blueprint.md) §8.4). No real
blocking event is recorded for the workflow-permission guard itself; its coverage
is limited to workflow-file changes.


---

## 6. Default-deny: what the course asks and what exists

The course requires: *"default is no read, no write; every path is explicitly
whitelisted"*, expressed in `.opencode/permissions.jsonc`.

**Current state:** the coding agent has whatever access the operator's machine
and configuration give it. There is no project-level deny-by-default list, no
per-role path whitelist, and no machine-readable permission file in the
repository.

What partially substitutes for it in practice:

1. **Approval-bounded file lists** — an approved execution plan names the files
   the agent may touch, and F/A reviewers enforce it in review.
2. **Workflow-credential guard** — prevents PR-reachable code from getting write
   credentials, which is the highest-impact permission failure.
3. **Import boundary test** — restricts one specific cross-layer capability.

None of these is a per-role filesystem permission model.

---

## 7. Gaps, stated precisely

| Gap | What is missing | Consequence |
|---|---|---|
| G1 | `.opencode/permissions.jsonc` | No machine-readable per-role path rights; the course's D3.4 deliverable is absent |
| G2 | `AGENTS.md` | The coding agent has no single checked-in entry point declaring build target, reading order, baseline, readable/modifiable/frozen paths |
| G3 | `Prompt.md` | No static startup prompt instructing plan-then-approve-then-build |
| G4 | `.opencode/rules.md`, `.agent/rules.md` | No always-on behavioural rules or project covenant in-file |
| G5 | `docs/code-governance/*.md` | Module-organisation, verification and tool-manifest rules exist only in plans and reviews |
| G6 | CODEOWNERS or equivalent | Path ownership is not enforced by GitHub |
| G7 | Per-change architecture-decision record | `REQ-GOV-08`'s "accompanying architecture decision" has no artefact linking a safety-critical change to a decision |
| G8 | `.github/workflows` runtime credential proof | The permission guard is static; runtime flows are not traced |

Listing G1–G8 is not a request to relax anything. It is the accurate state of a
document that would otherwise be read as complete.

---

## 8. Change policy for this document

Any change that would **add or widen** a permission must come from A, be recorded
with its original evidence, and be reflected in §5 with the layer it actually
achieves. C does not add permissions here; this document records what exists.
