# C — AI-use log (architecture documents)

Owner: Member C. Records AI (OpenCode) use on the CS5351 architecture-document
deliverable, per REQ-GOV-06.

## Entry

- Task: produce the eight architecture documents required by the course's D2
  (blueprint, ADR, invariants, trace matrix, memory/state design, permission
  model, runtime policy catalog, candidate evaluation table), plus a CLI demo
  guide, against the pinned source baseline.

- Usage scope: document authoring only. `docs/architecture/` and
  `docs/CLI-Demo-Guide.md`. No business code, test, CI workflow, Registry entry,
  approval record, `Report.md` or `README.md` was modified by this work.

- Implementation commit: `e8cce9197e2950f06f8550df86426b841a6ed93e` (this document-only PR; in
  `origin/main..HEAD`). The documents describe `main@252fe311d8d1483b5713de69b04ce2769c33f1dd`.

- Session/export evidence: `transcripts/C-architecture-docs-session-export.json`
  — a real OpenCode session record mechanically extracted from the local session
  store, filtered to this work, then redacted. Message order, role and original
  wording are preserved; credentials, personal identifiers and machine-absolute
  paths were replaced with explicit placeholders. This is not an authored
  summary.

- Export integrity: sha256 `a4e6ab036b4e2ec0f0bdc1eabab070a7f57caeb20fb41d965ef4ebd0029c33b1`; covered message sequence range
  `22773–24541` of session `ses_e3156feceffeB6Oza74L3gXwQ3`; original session
  store rows were not modified and are not committed.

## Corrections made during this work

The documents were checked against the pinned source and corrected where an
earlier draft overstated evidence. Notable corrections, visible in the session:

- A statement that PR #40 was blocked was replaced with its factual history:
  the approval red light was real at the time and was closed by PR #42 before
  #40 merged; S5 is on `main` at the pinned SHA.
- The trace matrix claim of "suite-level evidence only" was replaced with F's
  authenticated reading of historical run `44988759013`, while keeping the limit
  that 166 referenced functions were counted there and that figure does not
  extend to the 227 node IDs the revised matrix cites.
- S6/T17 is stated as stopped with acceptance not completed; no performance
  threshold is presented as met.

## Handling note

The redacted export was generated and inspected outside the repository before
inclusion. Credentials are never included; machine-absolute paths are replaced
rather than recorded.
