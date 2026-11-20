#!/usr/bin/env python3
"""Audit CI-installed dependencies and fail on newly introduced High/Critical vulns.

Policy (per A/C + D):
- Scans the *actually installed* environment (direct + transitive), not just a
  requirements file.
- ``ci/baselines/pip-audit-baseline.json`` records the accepted existing
  findings by (package, id). Newly introduced High/Critical IDs block.
- Existing findings are *not* silently whitelisted: the baseline file is the
  documented record and each entry carries a note. Security exceptions require
  explicit approval (see the baseline's ``_policy`` block) — this script never
  invents owners, severities, or approvals.
- A scanner failure / network-database failure is reported as a distinct
  non-zero outcome, never treated as "clean".

Usage:
    python scripts/dep_audit.py
    python scripts/dep_audit.py --update-baseline   # human-only

Exit codes:
    0  no new High/Critical findings
    1  new High/Critical finding(s) (blocking)
    2  scanner failed / audit could not run (treated as failure; never clean)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASELINE = Path("ci/baselines/pip-audit-baseline.json")
BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}
HIGH_SIGNAL_FIX = ("No fix", "no fix")  # informational only


def run_pip_audit() -> dict:
    cmd = [sys.executable, "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("ERROR: pip-audit not installed in this environment", file=sys.stderr)
        raise SystemExit(2) from None
    # pip-audit exit 1 = vulnerabilities found (still valid JSON); >1 = failure.
    if proc.returncode not in (0, 1):
        print("ERROR: pip-audit failed to run (network/DB/scanner failure):", file=sys.stderr)
        print(proc.stderr.strip()[:2000], file=sys.stderr)
        raise SystemExit(2) from None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("ERROR: pip-audit produced non-JSON output; treating as scanner failure", file=sys.stderr)
        raise SystemExit(2) from None


def findings(report: dict) -> list[tuple[str, str, str, str]]:
    """Return list of (package, version, vuln_id, fix) from a pip-audit JSON report."""
    out: list[tuple[str, str, str, str]] = []
    for dep in report.get("dependencies", []):
        name = dep.get("name", "?")
        version = dep.get("version", "?")
        for vuln in dep.get("vulns", []) or []:
            vid = vuln.get("id", "?")
            fixes = vuln.get("fix_versions", []) or []
            fix = ",".join(fixes) if fixes else "no fix available"
            out.append((name, version, vid, fix))
    return out


def load_baseline() -> dict:
    if not BASELINE.is_file():
        return {}
    return json.loads(BASELINE.read_text())


def baseline_keys(base: dict) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for entry in base.get("findings", []):
        keys.add((entry.get("package", ""), entry.get("id", "")))
    return keys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-baseline", action="store_true", help="rewrite baseline (human-only)")
    args = parser.parse_args(argv)

    report = run_pip_audit()
    found = findings(report)

    if args.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "_policy": (
                "Existing findings accepted at baseline; owners/remediation/exception "
                "approval are recorded separately and reviewed by A/C. New High/Critical "
                "IDs block. This file must not be widened by a PR's own changes."
            ),
            "findings": [
                {"package": p, "version": v, "id": vid, "fix": fix, "owner": "PENDING", "note": "PENDING"}
                for (p, v, vid, fix) in found
            ],
        }
        BASELINE.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"baseline updated: {len(found)} finding(s)")
        return 0

    base_keys = baseline_keys(load_baseline())
    current_keys = {(p, vid) for (p, _v, vid, _f) in found}

    new = [
        (p, v, vid, fix)
        for (p, v, vid, fix) in found
        if (p, vid) not in base_keys
    ]
    # Severity is unavailable from pip-audit's JSON; treat every *new* finding as
    # potentially High/Critical and block, while surfacing the ID and fix so the
    # owner can record the authoritative severity from the advisory.
    new_blocking = new  # conservative: any new finding blocks

    if new_blocking:
        print(f"DEPENDENCY AUDIT FAILED: {len(new_blocking)} new finding(s) beyond baseline:", file=sys.stderr)
        for (p, v, vid, fix) in new_blocking:
            print(f"  - {p}=={v}  {vid}  fix={fix}", file=sys.stderr)
        print(
            "  (severity not provided by pip-audit JSON; record authoritative severity "
            "from the advisory before deciding High/Critical policy; new findings block by default)",
            file=sys.stderr,
        )
        return 1

    removed = base_keys - current_keys
    print(f"OK: no new dependency findings ({len(found)} total, {len(removed)} baseline item(s) resolved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
