#!/usr/bin/env python3
"""Run mypy over the approved scope and fail on any *new* diagnostic.

Policy (per A/C + D):
- Reuses mypy (F-pinned version) — no suitable type tool pre-existed.
- Scope is the CS5351 safety/entry-point paths present on the baseline plus this
  batch's new scripts. ``--follow-imports=silent`` keeps third-party and
  unrelated-module noise out while still type-checking the listed files' bodies.
- An itemized baseline (``ci/baselines/mypy-baseline.txt``) records every
  existing diagnostic by *stable identity* = ``file:code``. New diagnostics block
  merge. Removing old errors is fine; it never offsets a new error.
- Broad module ignores / total-count allowances are not used.

Usage:
    python scripts/typecheck.py            # check against baseline
    python scripts/typecheck.py --update   # rewrite baseline from current output
                                          # (only humans should run --update; CI never does)

Exit codes:
    0  no new diagnostics
    1  new diagnostic(s) present (blocking)
    2  mypy failed to run / internal error
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

SCOPE = [
    "tradingagents/agents/evidence_gate.py",
    "tradingagents/agents/state.py",
    "tradingagents/graph",
    "cli/display.py",
    "cli/run.py",
    "scripts/validate_requirements.py",
    "scripts/check_ai_use_log.py",
    "scripts/typecheck.py",
    "scripts/dep_audit.py",
]

BASELINE = Path("ci/baselines/mypy-baseline.txt")

# mypy line: "path:line: error: message  [code]"  (notes ignored)
DIAG_RE = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): error: (?P<msg>.*?)(?:  \[(?P<code>[a-z-]+)\])?$")


def run_mypy() -> list[str]:
    cmd = [
        sys.executable, "-m", "mypy", *SCOPE,
        "--ignore-missing-imports",
        "--follow-imports=silent",
        "--show-error-codes",
        "--no-error-summary",
        "--no-incremental",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(2)
    return proc.stdout.splitlines()


def _identity(m: re.Match) -> str:
    code = m.group("code") or "no-code"
    norm = re.sub(r"\b\d+\b", "N", re.sub(r"line \d+", "line N", m.group("msg")))
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]
    return f"{m.group('path')}:{code}:{digest}"


def identities(lines: list[str]) -> list[str]:
    """Stable identity per diagnostic: 'file:code:msghash'.

    The message is normalised (line/column numbers removed) and hashed so that
    two diagnostics sharing a file and code are blocked *individually*, while a
    moved-but-identical error keeps its identity.
    """
    return [_identity(m) for m in (DIAG_RE.match(ln) for ln in lines) if m]


def load_baseline() -> set[str]:
    if not BASELINE.is_file():
        return set()
    return {ln.strip() for ln in BASELINE.read_text().splitlines() if ln.strip() and not ln.startswith("#")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="rewrite baseline (human-only)")
    args = parser.parse_args(argv)

    lines = run_mypy()
    current = identities(lines)

    if args.update:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# mypy itemized baseline (file:code). New diagnostics block; removals are fine.\n"
            "# Regenerate intentionally with: python scripts/typecheck.py --update\n"
        )
        BASELINE.write_text(header + "\n".join(sorted(set(current))) + "\n")
        print(f"baseline updated: {len(set(current))} diagnostic identities")
        return 0

    baseline = load_baseline()
    current_set = set(current)
    new = current_set - baseline

    if new:
        print(f"TYPECHECK FAILED: {len(new)} new diagnostic(s) beyond baseline:", file=sys.stderr)
        # Print the full messages for the new ones so reviewers see file/line/code.
        for line in lines:
            m = DIAG_RE.match(line)
            if m and _identity(m) in new:
                print(f"  {line}", file=sys.stderr)
        return 1

    removed = baseline - current_set
    print(
        f"OK: no new type diagnostics ({len(current_set)} current, "
        f"{len(removed)} baseline item(s) no longer present)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
