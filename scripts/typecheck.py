#!/usr/bin/env python3
"""Run mypy over the approved scope and fail on any *new* diagnostic.

Trust model (correction 1): the baseline is read from the **trusted base
revision** (``origin/<base>:ci/baselines/mypy-baseline.txt``), never from the
PR's own tree, so a PR cannot widen its allowances for its own new findings.
Bootstrap: if the baseline file does not exist on the base revision (first
introduction), the job uses the checked-in file from THIS PR and prints a clear
BOOTSTRAP notice — A must review that initial baseline.

Diagnostic identity (correction 2): ``file:code:msghash`` **with multiplicity**.
Identical diagnostics are tracked as a multiset (a count per identity), so two
identical errors in different functions do not collapse; removing an old error
never offsets introducing a new one.

mypy exit semantics (correction 2): exit 1 is normal "errors found", but the
process must have produced recognizable diagnostics. If mypy exits nonzero with
**no parseable diagnostics**, that is an execution failure (exit 2), not success.

Usage:
    python scripts/typecheck.py
    python scripts/typecheck.py --update     # human-only: rewrite the local baseline

Exit codes:
    0  no new diagnostics
    1  new diagnostic(s) beyond the trusted baseline
    2  mypy failed / produced output we could not parse
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from collections import Counter
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

DIAG_RE = re.compile(
    r"^(?P<path>[^:\n]+):(?P<line>\d+)(?::(?P<col>\d+))?: error: (?P<msg>.*?)(?:  \[(?P<code>[a-z-]+)\])?$"
)


def _identity(m: re.Match) -> str:
    code = m.group("code") or "no-code"
    # Normalise line numbers/raw digits so a moved-but-identical error keeps its key;
    # include the message text so distinct errors in the same file+code stay distinct.
    norm = re.sub(r"\b\d+\b", "N", m.group("msg"))
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]
    return f"{m.group('path')}:{code}:{digest}"


def parse(lines: list[str]) -> Counter:
    """Return a multiset (Counter) of diagnostic identities from mypy output lines."""
    counts: Counter = Counter()
    for ln in lines:
        m = DIAG_RE.match(ln)
        if m:
            counts[_identity(m)] += 1
    return counts


def _parse_baseline_text(text: str) -> Counter:
    """Parse a baseline file: one identity (``file:code:hash``) per line, counted."""
    counts: Counter = Counter()
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        counts[s] += 1
    return counts


def readable(lines: list[str]) -> list[str]:
    return [ln for ln in lines if DIAG_RE.match(ln)]


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
    out = proc.stdout.splitlines()
    diags = readable(out)
    if proc.returncode not in (0, 1):
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(2)
    # exit 1 with no parseable diagnostics is an execution problem, not success.
    if proc.returncode == 1 and not diags:
        print("ERROR: mypy exited 1 but produced no recognizable diagnostics:", file=sys.stderr)
        print(proc.stdout[-2000:], file=sys.stderr)
        print(proc.stderr[-2000:], file=sys.stderr)
        raise SystemExit(2)
    return out


def _load_baseline_text(base_ref: str) -> str | None:
    """Read the baseline from the trusted base revision; None if absent there."""
    try:
        proc = subprocess.run(
            ["git", "show", f"origin/{base_ref}:{BASELINE.as_posix()}"],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def load_baseline() -> tuple[Counter, str]:
    """Return (baseline multiset, source string) from the trusted base revision."""
    base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and base_ref:
        text = _load_baseline_text(base_ref)
        if text is not None:
            return _parse_baseline_text(text), f"trusted base origin/{base_ref}"
        print(
            "BOOTSTRAP: baseline absent on base revision; using this PR's checked-in "
            "baseline. A must review this initial baseline before merge.",
            file=sys.stderr,
        )
    if BASELINE.is_file():
        return _parse_baseline_text(BASELINE.read_text()), f"working tree {BASELINE}"
    return Counter(), "empty (no baseline)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true", help="rewrite local baseline (human-only)")
    args = parser.parse_args(argv)

    lines = run_mypy()
    current = parse(lines)

    if args.update:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# mypy itemized baseline (file:code:msghash), one line per occurrence.\n"
            "# Trusted base revision supplies this to CI; regenerate with --update.\n"
        )
        rows: list[str] = []
        for ident, n in sorted(current.items()):
            rows.extend([ident] * n)
        BASELINE.write_text(header + "\n".join(rows) + ("\n" if rows else ""))
        print(f"baseline updated: {sum(current.values())} diagnostic occurrence(s)")
        return 0

    baseline, source = load_baseline()
    # Multiset difference: a new occurrence beyond the baseline count is blocking.
    new: Counter = Counter()
    for ident, n in current.items():
        excess = n - baseline.get(ident, 0)
        if excess > 0:
            new[ident] = excess

    if new:
        total = sum(new.values())
        print(f"TYPECHECK FAILED: {total} new diagnostic occurrence(s) beyond baseline ({source}):", file=sys.stderr)
        # Report readable messages for the offending identities.
        remaining = Counter(new)
        for ln in lines:
            m = DIAG_RE.match(ln)
            if not m:
                continue
            ident = _identity(m)
            if remaining.get(ident, 0) > 0:
                print(f"  {ln}", file=sys.stderr)
                remaining[ident] -= 1
        return 1

    print(
        f"OK: no new type diagnostics (baseline source: {source}; "
        f"{sum(current.values())} current occurrence(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
