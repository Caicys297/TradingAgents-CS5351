# O5 S6 T17 — AI-use log (offline performance test)

Owner: Member E (O5, S6 T17). This log records verifiable AI (OpenCode) use of the S6 T17
performance test, per REQ-GOV-06 (`docs/req/requirements.yaml`): "Code or prompt PRs update the
AI-use log and preserve links to genuine agent-session evidence." Session evidence is kept under
`transcripts/` per `docs/PROJECT_WORKSPACE.md`, with secrets and personal data removed.

> No timestamps, token counts, prompts, commands or tool outputs below are invented. Where a value
> is not independently verifiable it is marked **not recorded**. This log does not claim any
> approval, test result, or code that does not exist. A local measurement is **not** the required
> CI result; the CI result is reported only for the runs linked below.

## Format notes

- The repository does not prescribe a fixed AI-use-log path or schema. This file follows the
  existing convention (`transcripts/*-AI-Use-Log.md`, e.g. `transcripts/CI-AI-Use-Log.md`).
- Tool: OpenCode. Model per session recorded in the session store; the exact provider/model string
  is not restated here.

## Entry (this PR)

- **Task:** implement the PR #31-approved O5 S6 T17 offline performance and correctness test — a
  fixed 1000-record fixture, an independently derived frozen oracle, a dual-SHA-256 manifest, and
  an offline harness that times only the `select_macro_news` call.
- **Scope:** `test/offline/fixtures/o5/O5-T17-*` (three fixed-data files + the independent oracle
  builder) and `test/offline/test_o5_macro_news_perf.py`. No O5 production code, `news.py`, `cli/`,
  or S5 files are changed by this entry. `.github/workflows/ci.yml` is F-owned; the `o5-perf` job
  was added by F, not by this AI-assisted batch.
- **Commit:** `37c09de8cde26c3288b065f8222bb6e51d8af2b8` — the implementation commit of this PR
  (S6 T17 rebased onto `main@e00d5cafd33869f42960c13bc297f9bf42634760`). The three data files and
  the two Python files are exactly those introduced at this commit; F's later CI commit sits on top
  of it.

## Session evidence (genuine, real)

- **OpenCode session:** `ses_e2a9d9cf9ffeDsLIgBv7qpqk4h` (this machine's OpenCode session store;
  title `CONNECTION_OK`). 1,099 messages recorded for this session (user 58, assistant 1,041).
- **Transcript association:** the session content contains this batch's real work — e.g.
  `select_macro_news` (311 occurrences), the fixture sha256 prefix `4dbf85d7` (39 occurrences),
  `O5-T17` (1,158 occurrences). This is the machine-verifiable basis for associating the session
  with the implementation commit; it is not fabricated.
- **Reviewer-accessible reference file:** `transcripts/CI-session-excerpt.md` (a bounded excerpt of
  real dialogue already preserved in this repository). Note for reviewers: the `CI-session-excerpt.md`
  excerpt documents the **six-gate CI** interaction by F, not this T17 batch; it is referenced here
  only as the repository's existing genuine-session-export artefact, and it is **not** claimed to be
  the T17 transcript. The T17 interaction is the OpenCode session `ses_e2a9d9cf9ffeDsLIgBv7qpqk4h`
  above, whose raw export is retained locally and not committed.
- **Raw export:** not committed to this repository. Status: **available locally, pending redacted
  export** from the session store. No raw transcript contents are pasted or invented in this file.

## Verified results (reported truthfully, separately)

### Required CI result — ubuntu-latest / Python 3.11 (dedicated gate)

- Workflow run `44898951061` (event `pull_request`, head `1370bf66348b3b9f6aac4bb7a43787f195fe924e`),
  job **`o5 perf (threshold enforced)`** → **conclusion `success`** (started
  `2026-11-21T11:24:25Z`, completed `2026-11-21T11:25:01Z`).
- On that runner (ubuntu-latest / CPython 3.11): **4 tests passed**, `p95 = 81.944 ms` with the
  `<= 100 ms` threshold enforced, and **5/5 warmups + 30/30 measured calls correct** against the
  frozen oracle.

### Local measurement (not the CI gate)

- Local run on Windows / CPython 3.13.9 with the threshold **not enforced** produced a higher p95
  (≈127 ms) than the Ubuntu/Python 3.11 runner. This is a local, non-gating observation only; it is
  **not** the required result and is not claimed as a pass.

### Pre-existing Windows encoding failures (separate, unrelated)

- The full local suite records **5 failures** in `test/offline/test_ci_gate_checkers.py`, all caused
  by `Path.read_text()` being called without `encoding` under this machine's Windows **GBK** locale
  (`UnicodeDecodeError`). These are **pre-existing and unrelated to T17**: they reproduce identically
  on a clean detached checkout of `main@e00d5ca`, and they do **not** occur on the UTF-8 Linux CI
  runners. As such, this log does **not** claim that the full suite passed on Windows.
- Contributing local totals (Windows, GBK-affected): focused T17 file **4 passed**; full suite
  **1,886 passed, 6 skipped, 1 deselected, 5 failed** (the 5 above); `ruff check .` clean.

## Provenance

- Approval of the T17 design and file scope: PR #31 (`fancx777` APPROVED at review `5993326783`;
  `Caicys297` scope confirmation in comment `7040220409`).
- **File-scope approval for the fifth file.** `Caicys297` (Member A) verified
  `test/offline/fixtures/o5/build_o5_t17_fixture.py` on PR #33 and agreed to add it to the approved
  S6 T17 file scope — as offline fixture/frozen-expectation generation only, deriving the oracle from
  independent rule text and allocation logic, with the three JSON outputs unchanged and no selector,
  `news.py`, public-interface, or S5 change. Comment `7062448781`,
  `2026-11-21T12:16:25Z`:
  https://github.com/Caicys297/TradingAgents-CS5351/pull/33#issuecomment-7062448781
  A stated this is a **file-scope supplement, not a PR #33 implementation/CI APPROVE**.
- CI ownership of `.github/workflows/ci.yml`: F (per A's PR #31 note); F added the `o5-perf` job in
  the follow-up commit on this branch.

## Measurement vs. review status (kept distinct)

Two different things must not be conflated:

1. **T17 performance measurement — PASSED on the required runner.** The dedicated
   `o5 perf (threshold enforced)` job on ubuntu-latest / Python 3.11 (run `44898951061`) is
   **success** with p95 `81.944 ms`, 5/5 warmups and 30/30 measured calls correct, 4 tests passed.
   This is the required CI result for T17.
2. **Final implementation review — PENDING.** A's comment above is a **file-scope** agreement only and
   explicitly is not an implementation/CI APPROVE of PR #33. F's final review of the completed test
   and CI (including the Windows encoding follow-up) is still outstanding. A green T17 measurement
   does **not** by itself approve the implementation, and this draft PR is not claimed as reviewed or
   mergeable on the strength of the measurement.

The PR remains **Draft** until the final implementation review is recorded.
