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
# mypy --show-error-context emits, before a file's errors, a context note naming the
# enclosing scope, e.g.  cli/run.py: note: In function "run_analysis":
CONTEXT_RE = re.compile(
    r"^(?P<path>[^:\n]+): note: (?:In function|At top level|In class|In member) "
    r'(?:"(?P<sym>[^"]+)")?'
)


def _pair(lines: list[str]):
    """Yield (match, symbol) per diagnostic, tracking the active context per file.

    The symbol (enclosing function/class or module top level) is part of the
    diagnostic's identity, so an identical error removed from function A and a
    new identical error introduced in function B are NOT the same diagnostic.
    """
    current_file: str | None = None
    current_sym = "<module>"
    for ln in lines:
        cm = CONTEXT_RE.match(ln)
        if cm:
            current_file = cm.group("path")
            current_sym = cm.group("sym") or ("<top>" if "At top level" in ln else "<scope>")
            continue
        m = DIAG_RE.match(ln)
        if m:
            sym = current_sym if m.group("path") == current_file else "<module>"
            yield m, sym


def _identity(m: re.Match, symbol: str = "<module>") -> str:
    code = m.group("code") or "no-code"
    # Normalise raw line numbers so a moved-but-identical error keeps its key.
    # Identity = path : symbol : code : message-hash. Symbol inclusion prevents
    # collapse across functions; message-hash separates distinct diagnostics.
    norm = re.sub(r"\b\d+\b", "N", m.group("msg"))
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]
    return f"{m.group('path')}:{symbol}:{code}:{digest}"


def parse(lines: list[str]) -> Counter:
    """Return a multiset (Counter) of diagnostic identities from mypy output lines."""
    counts: Counter = Counter()
    for m, sym in _pair(lines):
        counts[_identity(m, sym)] += 1
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
        "--show-error-context",
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


class BaseResolutionError(RuntimeError):
    """The trusted base ref/commit could not be resolved (git/ref/permission)."""


def _base_commit(base_ref: str) -> str:
    """Resolve origin/<base> to a commit SHA; raise on any resolution failure."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", f"origin/{base_ref}^{{commit}}"],
            capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise BaseResolutionError("git not available") from exc
    if proc.returncode != 0:
        raise BaseResolutionError(
            f"cannot resolve origin/{base_ref}: {proc.stderr.strip()[:200]}"
        )
    return proc.stdout.strip()


def _baseline_state(base_ref: str) -> tuple[str | None, str]:
    """Return (baseline_text_or_None, base_sha).

    Distinguishes:
      - base resolves AND file exists  -> text (trusted)
      - base resolves AND file absent  -> None (genuine first-introduction bootstrap)
    Raises BaseResolutionError if the base/ref itself cannot be resolved.
    """
    base_sha = _base_commit(base_ref)
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{base_sha}:{BASELINE.as_posix()}"],
            capture_output=True, text=True,
        )
    except FileNotFoundError as exc:
        raise BaseResolutionError("git not available") from exc
    if proc.returncode != 0:
        # Confirm the commit exists but the path does not (genuine absence), vs an
        # unexpected git failure surfaced during cat-file.
        return None, base_sha
    show = subprocess.run(
        ["git", "show", f"{base_sha}:{BASELINE.as_posix()}"],
        capture_output=True, text=True,
    )
    if show.returncode != 0:
        raise BaseResolutionError(
            f"baseline exists but could not be read from {base_sha}: {show.stderr.strip()[:200]}"
        )
    return show.stdout, base_sha


def load_baseline() -> tuple[Counter, str]:
    """Return (baseline multiset, source string) from the trusted base revision."""
    base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and base_ref:
        try:
            text, base_sha = _baseline_state(base_ref)
        except BaseResolutionError as exc:
            print(f"ERROR: cannot resolve trusted base baseline: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if text is not None:
            return _parse_baseline_text(text), f"trusted base {base_sha[:12]} (origin/{base_ref})"
        print(
            "BOOTSTRAP: baseline genuinely absent on trusted base "
            f"{base_sha[:12]}; using this PR's checked-in baseline. A must review this "
            "initial baseline before merge.",
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
        # Report readable messages for the offending identities (with symbol context).
        remaining = Counter(new)
        for m, sym in _pair(lines):
            ident = _identity(m, sym)
            if remaining.get(ident, 0) > 0:
                print(f"  {m.group('path')}:{m.group('line')}: [{sym}] error: {m.group('msg')}"
                      + (f"  [{m.group('code')}]" if m.group('code') else ""), file=sys.stderr)
                remaining[ident] -= 1
        return 1

    print(
        f"OK: no new type diagnostics (baseline source: {source}; "
        f"{sum(current.values())} current occurrence(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
