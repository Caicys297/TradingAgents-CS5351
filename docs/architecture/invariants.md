# Invariant Register

**Baseline:** `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
**Owner:** C (register assembly), with each invariant owned by the module that enforces it.

---

## 0. What counts as an invariant here

The Registry distinguishes requirement types: `functional_behavior`,
`invariant`, `quality_attribute`, `performance`, `cost`, `governance`,
`security`. The course defines invariants as **non-negotiable rules with
zero-tolerance fit criteria**.

**Only entries the Registry itself types as `invariant` are listed here as
business invariants.** There are 13 such entries. Requirements typed
`functional_behavior`, `quality_attribute` etc. are *not* promoted to invariants
in this register, even where they are important — promoting them would make the
word mean nothing.

**Governance rules are listed separately (Part B)** because they are rules *about
the team's process*, enforced by CI rather than by application code. Mixing them
into the business-invariant register would misrepresent what a runtime failure
of each one means.

Each row gives, as the course requires: **statement**, **source requirement ID**,
**enforcing component**, **verification method**, and a **concrete operational
fallback** — an action, not "fix the bug".

---

## Part A — Business invariants (Registry type `invariant`)

### A.1 O1 — SMA history guard

| Field | O1-I1 |
|---|---|
| **Requirement** | `REQ-O1-03` (Registry line 105) |
| **Statement** | Count cleaned, non-missing closes separately for each reported date. Sort dated closes chronologically for the SMA-only calculation; exclude rows after the analysis date. A duplicate trading date is an invalid SMA input. |
| **Enforcing component** | `tradingagents/dataflows/vendors/yahoo/market.py` (SMA path) |
| **Verification** | `T-O1-04`, `T-O1-11`, `T-O1-12`; offline nodes in `test/offline/test_o1_sma_guard.py` |
| **Operational fallback** | Emit the exact N/A text for the affected window: `N/A: invalid price history (duplicate trading date)`. Do **not** emit a numeric SMA for that window. The report proceeds; only the affected SMA value is replaced. |

| Field | O1-I2 |
|---|---|
| **Requirement** | `REQ-O1-05` (line 127) |
| **Statement** | Leave non-SMA indicators' behavior unchanged. |
| **Enforcing component** | `tradingagents/dataflows/vendors/yahoo/market.py`; unchanged indicator routing |
| **Verification** | `T-O1-07` |
| **Operational fallback** | If a non-SMA indicator's behaviour changes, the change is reverted rather than patched around: the invariant exists to prevent an SMA fix from silently altering another indicator. Concrete action: restore the previous indicator code path and re-run the O1 suite before any other O1 work continues. |

### A.2 O4 — Evidence gate

| Field | O4-I1 |
|---|---|
| **Requirement** | `O4-INV-01` (line 769) |
| **Statement** | No run whose required evidence is incomplete may publish a tradeable rating on any enabled surface; the published rating MUST be the effective rating. |
| **Enforcing component** | `tradingagents/agents/evidence_gate.py::check_evidence`, applied from `cli/run.py` before `record_decision`, report generation, return and final display |
| **Verification** | `O4-T-02`, `O4-T-08`, `O4-T-19`, `O4-T-23`; `test/offline/test_evidence_gate.py`, `test_evidence_gate_cli_publication.py`, `test_evidence_gate_graph_integration.py` |
| **Operational fallback** | Publish `REVIEW` with a preserved reason on every surface. The Portfolio Manager's decision text is still shown, explicitly labelled as unapproved original content and withheld from the run's rating. Do not delete the run; do not re-run automatically. |

| Field | O4-I2 |
|---|---|
| **Requirement** | `O4-INV-02` (line 781) |
| **Statement** | A pre-existing original REVIEW is never upgraded to a tradeable rating. |
| **Enforcing component** | `check_evidence` → `_resolve_original_rating` + `is_review` in `tradingagents/agents/rating.py` |
| **Verification** | `O4-T-06`, `O4-T-25` |
| **Operational fallback** | Keep `REVIEW`. If a code path appears to upgrade it, that path is disabled until a test reproduces and fixes it; there is no manual override. |

| Field | O4-I3 |
|---|---|
| **Requirement** | `O4-INV-03` (line 793) |
| **Statement** | Every enabled rating surface observes the same effective rating; none reads the ungated original rating independently. No raw Portfolio Manager Buy/Sell is published as an approved result before the gate completes. |
| **Enforcing component** | Single gate application in `cli/run.py`; PM text buffered until the gate returns |
| **Verification** | `O4-T-08`, `O4-T-23` |
| **Operational fallback** | If a surface is found reading the original rating, that surface is removed from the publication path (not merely patched) until it reads the effective rating. Concrete action: revert the surface's publication call, keep it behind the gate, and re-verify with the `O4-T-08` node. |

| Field | O4-I4 |
|---|---|
| **Requirement** | `O4-INV-04` (line 805) |
| **Statement** | On a recoverable internal checker failure, the effective rating MUST be REVIEW, a diagnostic reason is preserved, every enabled surface uses that effective_rating, and the ungated original rating is never published. |
| **Enforcing component** | `check_evidence` recoverable-error handler (fail closed) |
| **Verification** | `O4-T-07`, `O4-T-08` |
| **Operational fallback** | Fail closed to `REVIEW` with the diagnostic reason retained. The run completes; the missing guarantee is visible in the reason text rather than silently absent. |

| Field | O4-I5 |
|---|---|
| **Requirement** | `O4-INV-05` (line 817) |
| **Statement** | When `final_rating` and a clearly parsed `final_trade_decision` rating disagree, the effective rating MUST be REVIEW with a preserved conflict reason; an original REVIEW is never upgraded. |
| **Enforcing component** | `check_evidence` conflict branch; `run_rating` parsing |
| **Verification** | `O4-T-25` |
| **Operational fallback** | Publish `REVIEW` and preserve the conflict reason. Do not attempt to pick the "more likely" rating. |

### A.3 O5 — Selector

| Field | O5-I1 |
|---|---|
| **Requirement** | `REQ-O5-06` (line 879) |
| **Statement** | 100× identical input ⇒ full equality; unique-ID permutations equal (input_index differs); conflicting duplicate IDs are not permutation-invariant; no wall-clock in the selector. |
| **Enforcing component** | `tradingagents/dataflows/macro_news_filter.py::select_macro_news` |
| **Verification** | `T14`; `test/offline/test_o5_macro_news_filter.py`, `test/offline/test_o5_invariants.py` |
| **Operational fallback** | The selector is deterministic by construction; a non-deterministic result means the code is wrong, so the concrete action is to **halt O5 selection for the run** by returning the filter-unavailable message (`development_contract.o5.invariant_failure`) rather than serving an unreproducible selection. |

| Field | O5-I2 |
|---|---|
| **Requirement** | `REQ-O5-09` (line 915) |
| **Statement** | Keep public news API signatures and return type `str` unchanged; leave ticker-news behavior unchanged and run all prior applicable news tests. |
| **Enforcing component** | `tradingagents/dataflows/vendors/yahoo/news.py` public entry; ticker-news formatter |
| **Verification** | `T15`, `RT-1`, `RT-4`; nodes `test_rt1_global_news_tool_schema_unchanged`, `test_rt2_public_entry_keeps_signature_and_returns_str`, `test_rt4_ticker_news_path_untouched`, `test_rt4b_ticker_news_signature_unchanged` in `test/offline/test_o5_regression.py` |
| **Operational fallback** | A signature change is not degraded gracefully — it is reverted. Concrete action: restore the previous public signature and re-run the RT nodes before any further O5 change. |

| Field | O5-I3 |
|---|---|
| **Requirement** | `INV-O5-01` (line 927) |
| **Statement** | No fabrication / irrelevant padding. |
| **Enforcing component** | `select_macro_news` + the adapter's exit paths |
| **Verification** | O5 invariant tests I1–I12 (`test/offline/test_o5_invariants.py`) |
| **Operational fallback** | Return an explicit empty status distinct from upstream failure (`K=0` is not "vendor returned nothing"). Zero selected articles are reported as zero, never padded to fill a limit. |

| Field | O5-I4 |
|---|---|
| **Requirement** | `INV-O5-02` (line 939) |
| **Statement** | No out-of-input / duplicate / mutation. |
| **Enforcing component** | `select_macro_news` (pure; does not mutate input) |
| **Verification** | O5 invariant tests I1–I12 |
| **Operational fallback** | On any evidence of a selection referencing an item not in the input, the terminal `V-SELECTED` event is **not** emitted and the filter-unavailable message is served instead. |

| Field | O5-I5 |
|---|---|
| **Requirement** | `INV-O5-03` (line 951) |
| **Statement** | Window containment. |
| **Enforcing component** | `select_macro_news` + `dataflows/date_window.py` helpers |
| **Verification** | O5 invariant tests I1–I12 |
| **Operational fallback** | Articles outside the requested window are excluded by construction; if one appears, the selection for that run is suppressed rather than trimmed after the fact. |

| Field | O5-I6 |
|---|---|
| **Requirement** | `INV-O5-04` (line 963) |
| **Statement** | No network / no LLM. |
| **Enforcing component** | `macro_news_filter.py` imports no vendor or model client |
| **Verification** | O5 invariant tests I1–I12; `T16` via `test_t16_o5_path_adds_no_network_or_llm`; offline `conftest.py` blocks sockets and `curl_cffi` |
| **Operational fallback** | A network call inside the selector is a defect that cannot be degraded; the concrete action is to abort that code path and revert the change before release. |

**Registry count check.** `REQ-O5-06` and `REQ-O5-09` are typed `invariant`;
`REQ-O5-08` is typed `cost` and is therefore **not** listed here even though its
"0 added requests" statement is invariant-like in tone. `INV-O5-01`…`04` are
typed `invariant`. Total O5 invariant-typed entries: 6.

---

## Part B — Governance rules (Registry type `governance`)

These are rules about the team's process. Their "enforcement component" is CI
and human review, not application runtime. A violation means a change should not
merge, not that the product misbehaves.

**These are not business invariants and are deliberately not merged with Part A.**
A green O4 gate suite does not show that CI blocked a change, and a blocked PR
does not show that an invariant holds in production.

**Verification is recorded per row as two separate facts:** whether a concrete
checker and its nodes exist, and whether a **real change was observed to be
blocked**. Unit tests prove the checker's decision logic; only a cited run or PR
proves blocking. Node-level detail is in
[`trace-matrix.md`](trace-matrix.md) §GOV; the summarised blocking record is in
[`architecture-blueprint.md`](architecture-blueprint.md) §8.4.

**Real blocking evidence on the record:** the #37 approval-closure run
(`44979161445`, pinned `1c0b740`, 17 checks successful) shows the approval gate
**passing** on a complete batch; PR #41 **E2** shows a Schema fault **blocking**
a change and **E4/E5** shows recovery (E5 run `44998474208` at `9462d6c1`,
17/17), after which the PR was closed unmerged.

| ID | Statement (abridged) | Enforcing component | Verification | Fallback if violated |
|---|---|---|---|---|
| `REQ-GOV-01` | No code change merges unless its tests were approved before implementation began | `scripts/check_test_approval.py`, CI job `test approval` | node-level negative cases (late / self / only-test-plan / immutable-plan) in `test/offline/test_check_test_approval.py`; #37 run shows the gate passing | The change does not merge. It is not retro-approved; the approval must exist with an original timestamp preceding the first implementation commit. |
| `REQ-GOV-02` | The coding agent produces an execution plan and waits for human approval before generating code | Human review records (PR comments, e.g. A's execution-scope approvals) | plan-then-approve records in PR review history; `test/offline/test_check_test_approval.py::test_only_test_plan_fails` proves the execution-plan half is genuinely required | Work stops at the planning boundary; the agent must not proceed to code. |
| `REQ-GOV-03` | CI validates the registry against its checked-in JSON schema | `scripts/validate_requirements.py`, CI job `requirements schema` | schema nodes in `test/offline/test_ci_gate_checkers.py`; **PR #41 E2 blocked, E5 recovered** | The PR is blocked at the schema job until the registry conforms. |
| `REQ-GOV-04` | Every change runs the full prior regression suite; any regression blocks merge | CI jobs `tests (py3.11/3.12/3.13/3.14)` | four-environment matrix on the pinned main run; **#41 E2 four matrices failed together while BLOCKED, E5 green and recovered** | The merge is blocked. The change is not merged with a known regression and a follow-up promise. |
| `REQ-GOV-05` | Prompt or model changes run a fixed semantic evaluation set against approved thresholds | CI jobs `semantic (deterministic O5)` / `semantic (deterministic O4)`, `scripts/semantic_report.py` | fail-closed runner nodes in `test/offline/test_semantic_report.py` | A failing threshold blocks the change and reports which threshold failed. |
| `REQ-GOV-06` | Code or prompt PRs update the AI-use log and preserve genuine session evidence | `scripts/check_ai_use_log.py`, CI job `ai-use log` | structural nodes in `test/offline/test_ci_gate_checkers.py`; committed AI-use logs under `transcripts/` | The PR is blocked until AI-use evidence under `transcripts/` is added. |
| `REQ-GOV-07` | Every commit runs lint, type and dependency checks; safety-relevant PRs also run contract, security, API-surface and permission checks | CI jobs `ruff (strict, full repo)`, `type check`, `dependency audit`, `governance contract/security/api/permissions` | per-commit Ruff nodes, type/dep nodes, four guard suites; three real contract-mutation cases in `docs/ci/CI-Closure-v5-Evidence.md` @ `3314d52` | The job fails and the merge is blocked. |
| `REQ-GOV-08` | Branch protection requires passing CI and human review with an architecture decision for safety-critical path changes | GitHub branch protection (external setting) + human review records | PR #41 E1/E2/E4/E5 state chain; A's configuration screenshots and SHA256 list (**not read by C**) | **Gap:** branch protection is a repository setting not represented in a checked-in file, and no automated check verifies that an architecture decision accompanies a safety-critical change. |

**Limits that still apply to every GOV row above:**

- **E3 was not executed**; **no independent administrator API read-back** of the
  protection configuration was obtained.
- In **E2** the four matrix failures were **coupled to the Schema fault**, not
  isolated to one job.
- **Independent semantic-job red-light blocking was not verified.**
- **PR #38 is a batch-specific process deviation** and is not generalised here.
- For `REQ-GOV-01/02`, #37 records the gate **accepting** a complete batch; a
  real rejection of a complete PR is not recorded.

---

## Part C — Near-invariants that are deliberately excluded

These read like invariants but are typed otherwise. Listing them here prevents a
reader from assuming they were forgotten.

| Entry | Registry type | Why not in Part A |
|---|---|---|
| `REQ-O5-08` | `cost` | A cost bound (0 added requests/LLM calls/mutations), verified by counting, not a zero-tolerance business rule |
| `O3-FR-04` | `cost` | A budget rule with explicit exception semantics — it *has* a documented fallback, which is the opposite of zero-tolerance |
| `O3-FR-07` | `governance` | A claim-limiting rule: what the team may *assert*, not what the system must do |
| `O3-NFR-05` | `security` | A handling rule with a positive obligation (counts-only logs), not a zero-tolerance invariant |
| `O2-FR-05`, `O2-FR-11`, `O2-NFR-03` | `security` | Secret-exclusion rules; important, but they are obligations on serialisation, not invariants about published decisions |
| `O4-NFR-03` | `performance` | A latency bound |
| `REQ-O5-10` | `performance` | A bound whose measurement (T17) was never accepted: **S6 was stopped before any T17 result was accepted**, so no performance threshold is met. Development is stopped and acceptance is not completed. |

---

## Part D — Enforcement status: three separate statements

For each business invariant, three claims are often conflated. They are kept
separate:

| Invariant | (1) Enforced in code | (2) Test node exists | (3) Observed blocking a real change |
|---|---|---|---|
| O1-I1..I2 | Yes — SMA path | Yes — `test_o1_sma_guard.py` | Not recorded |
| O4-I1..I5 | Yes — `check_evidence` applied in `cli/run.py` | Yes — evidence-gate suites | Not recorded |
| O5-I1..I6 | Yes — pure selector + adapter exits | Yes — filter/invariant/regression suites | Not recorded |

**Column (2) is "node exists", not "passed".** Historical execution evidence is
a fourth, separate statement: F's reading of the Python 3.11 job log for
historical run `44988759013` at `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`
reported PASSED entries for the 166 function references cited in that matrix.
That covers the functions it counted; it is **not** a claim that every invariant
test above passed in that run, and the log body itself was not readable with the
credential available to C. Details: [`trace-matrix.md`](trace-matrix.md)
§"Historical execution evidence".

**Column (3) is the honest gap for business invariants.** A green suite and a
passing job demonstrate (1) and (2). They do not demonstrate that an invariant
regression was ever caught in practice. Note that the *governance* blocking
record in Part B (PR #41 E2/E5, run #37) is a different kind of evidence and does
**not** fill this column — a blocked CI gate is not an observed invariant
violation in the product.

**Column 3 is the honest gap.** A green suite and a passing job demonstrate (1)
and (2). They do not demonstrate that a regression was ever caught in practice.
No record in this repository shows an invariant test failing on a real pull
request, so column 3 remains "not recorded" for every row rather than "yes".

---

## Part E — How to read a fallback

Every fallback in Part A is a **specific action the system or the team takes**,
chosen so that the failure is visible and bounded:

| Fallback class | Shape |
|---|---|
| Substitute honest text | Replace a number/selection with an explicit N/A or empty-status message |
| Subside to REVIEW | Publish a non-tradeable rating with a preserved reason |
| Suppress and name | Withhold the affected output and report why |
| Revert the surface | Remove a publication path that cannot be made correct |

None of them is "log and continue as if nothing happened", because that is the
failure mode each invariant exists to prevent.
