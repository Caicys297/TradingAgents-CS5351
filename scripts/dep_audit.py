#!/usr/bin/env python3
"""Audit CI-installed dependencies and fail on newly introduced vulnerabilities.

Policy and honesty notes (corrections 1 & 4):
- The baseline is read from the **trusted base revision**
  (``origin/<base>:ci/baselines/pip-audit-baseline.json``), never from the PR tree,
  so a PR cannot widen its own allowances. Bootstrap uses the PR's file with a
  clear notice for A review.
- Scans the *actually installed* environment (direct + transitive).
- pip-audit's JSON does not carry severity. This checker therefore treats **every
  new finding as blocking** — a deliberately *conservative temporary* behavior,
  NOT verified severity-aware High/Critical classification. Adopting severity-aware
  blocking requires an additional authoritative source (e.g. OSV severity) and an
  owner decision; that is called out, not fabricated.
- Allowances are keyed by (package, id, affected-version); an allowance never
  silently covers a future affected version.
- Structural validation: a report that is not a well-formed pip-audit document
  (e.g. ``{}``) is a scanner failure (exit 2), never "clean". Skipped / unresolvable
  packages are reported. The local editable project is identified separately from
  unaudited third-party dependencies.

Usage:
    python scripts/dep_audit.py
    python scripts/dep_audit.py --update-baseline   # human-only

Exit codes:
    0  no new findings (and report structure valid)
    1  new finding(s) beyond the trusted baseline
    2  scanner failed / report invalid / could not validate
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

BASELINE = Path("ci/baselines/pip-audit-baseline.json")
VALID_APPROVAL = {"APPROVED", "ACCEPTED"}


class ScannerError(RuntimeError):
    pass


def run_pip_audit() -> dict:
    cmd = [sys.executable, "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise ScannerError("pip-audit not installed") from exc
    if proc.returncode not in (0, 1):
        raise ScannerError(
            f"pip-audit failed (exit {proc.returncode}): {proc.stderr.strip()[:1500]}"
        )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ScannerError("pip-audit produced non-JSON output") from exc
    validate_report(report)
    return report


def validate_report(report: object) -> None:
    """Reject structurally-incomplete reports (e.g. ``{}``) as scanner failures."""
    if not isinstance(report, dict) or "dependencies" not in report:
        raise ScannerError("report has no 'dependencies' key (incomplete scan)")
    if not isinstance(report["dependencies"], list):
        raise ScannerError("report 'dependencies' is not a list")
    # pip-audit includes a 'skip_reason'/'skips' in some versions; capture if present.
    deps = report["dependencies"]
    if deps and not all(isinstance(d, dict) and "name" in d for d in deps):
        raise ScannerError("report dependency entries malformed")


def findings(report: dict) -> list[tuple[str, str, str, str]]:
    """(package, installed_version, vuln_id, fix)."""
    out: list[tuple[str, str, str, str]] = []
    for dep in report.get("dependencies", []):
        name = dep.get("name", "?")
        version = dep.get("version", "?")
        for vuln in dep.get("vulns", []) or []:
            vid = vuln.get("id", "?")
            fixes = vuln.get("fix_versions", []) or []
            out.append((name, version, vid, ",".join(fixes) if fixes else "no fix available"))
    return out


def skipped(report: dict) -> list[str]:
    out: list[str] = []
    for dep in report.get("dependencies", []):
        reason = dep.get("skip_reason")
        if reason:
            out.append(f"{dep.get('name','?')}=={dep.get('version','?')}: {reason}")
    return out


def local_editable(report: dict) -> list[str]:
    """Identify this project's own editable install (not third-party)."""
    names: list[str] = []
    for dep in report.get("dependencies", []):
        name = str(dep.get("name", "")).lower()
        if name in ("tradingagents",):
            names.append(f"{dep.get('name')}=={dep.get('version')}")
    return names


def _load_baseline() -> tuple[dict, str]:
    base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and base_ref:
        try:
            proc = subprocess.run(
                ["git", "show", f"origin/{base_ref}:{BASELINE.as_posix()}"],
                capture_output=True, text=True,
            )
        except FileNotFoundError:
            proc = None
        if proc is not None and proc.returncode == 0:
            return json.loads(proc.stdout), f"trusted base origin/{base_ref}"
        print(
            "BOOTSTRAP: dependency baseline absent on base revision; using this PR's "
            "checked-in baseline. A must review this initial baseline.",
            file=sys.stderr,
        )
    if BASELINE.is_file():
        return json.loads(BASELINE.read_text()), f"working tree {BASELINE}"
    return {"findings": []}, "empty"


def baseline_keys(base: dict) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for entry in base.get("findings", []):
        pkg = entry.get("package", "")
        vid = entry.get("id", "")
        ver = entry.get("affected_version", entry.get("version", ""))
        keys.add((pkg, vid, ver))
    return keys


def validate_baseline(base: dict) -> list[str]:
    """Reject PENDING owners / unapproved exceptions in the baseline."""
    problems: list[str] = []
    for entry in base.get("findings", []):
        if entry.get("owner", "PENDING") == "PENDING":
            problems.append(f"baseline finding {entry.get('package')} {entry.get('id')} has no owner")
        if entry.get("status") and entry["status"] not in VALID_APPROVAL:
            problems.append(
                f"baseline finding {entry.get('package')} {entry.get('id')} status "
                f"{entry.get('status')!r} not approved"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-baseline", action="store_true", help="rewrite baseline (human-only)")
    args = parser.parse_args(argv)

    try:
        report = run_pip_audit()
    except ScannerError as exc:
        print(f"ERROR: dependency scan failed: {exc}", file=sys.stderr)
        return 2

    found = findings(report)

    if args.update_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "_policy": (
                "Existing findings; each requires owner + remediation + (for any "
                "exception) approved status. New findings block. PRs must not widen "
                "this file. Severity is not provided by pip-audit JSON; new findings "
                "block conservatively until an authoritative severity source is adopted."
            ),
            "scanned_packages": len(report.get("dependencies", [])),
            "findings": [
                {
                    "package": p, "affected_version": v, "id": vid,
                    "fix": fix, "owner": "PENDING", "status": "PENDING",
                }
                for (p, v, vid, fix) in found
            ],
        }
        BASELINE.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"baseline updated: {len(found)} finding(s) from {len(report.get('dependencies', []))} packages")
        return 0

    base, source = _load_baseline()
    meta_problems = validate_baseline(base)
    if meta_problems:
        print("ERROR: baseline metadata invalid (owners/exceptions must be approved):", file=sys.stderr)
        for p in meta_problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    base_keys = baseline_keys(base)
    new = [(p, v, vid, fix) for (p, v, vid, fix) in found if (p, vid, v) not in base_keys]

    skip = skipped(report)
    signed = local_editable(report)
    print(f"scanned packages: {len(report.get('dependencies', []))} (baseline source: {source})")
    if signed:
        print(f"local editable project (audited for version only): {', '.join(signed)}")
    if skip:
        print("skipped/unscannable packages (reported, not treated as clean):")
        for s in skip:
            print(f"  - {s}")

    if new:
        print(f"DEPENDENCY AUDIT FAILED: {len(new)} new finding(s) beyond baseline:", file=sys.stderr)
        for (p, v, vid, fix) in new:
            print(f"  - {p}=={v}  {vid}  fix={fix}", file=sys.stderr)
        print(
            "  NOTE: severity not supplied by pip-audit JSON; ALL new findings block "
            "(conservative temporary policy, not severity-aware). Adopt an authoritative "
            "severity source + owner decision to refine.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: no new dependency findings ({len(found)} total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
