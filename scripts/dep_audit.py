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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ci_event  # noqa: E402

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


class BaseResolutionError(RuntimeError):
    """The trusted base commit could not be resolved."""


def _baseline_at_sha(base_sha: str) -> tuple[str | None, str]:
    try:
        chk = subprocess.run(["git", "cat-file", "-e", f"{base_sha}:{BASELINE.as_posix()}"],
                             capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise BaseResolutionError("git not available") from exc
    if chk.returncode != 0:
        return None, base_sha
    show = subprocess.run(["git", "show", f"{base_sha}:{BASELINE.as_posix()}"],
                          capture_output=True, text=True)
    if show.returncode != 0:
        raise BaseResolutionError(f"baseline exists but unreadable: {show.stderr.strip()[:200]}")
    return show.stdout, base_sha


def _load_baseline(base_sha: str | None) -> tuple[dict, str]:
    if base_sha is not None:
        try:
            text, sha = _baseline_at_sha(base_sha)
        except BaseResolutionError as exc:
            print(f"ERROR: cannot resolve trusted base baseline: {exc}", file=sys.stderr)
            raise SystemExit(2) from exc
        if text is not None:
            return json.loads(text), f"trusted base {sha[:12]}"
        print(
            "BOOTSTRAP: dependency baseline genuinely absent on trusted base "
            f"{sha[:12]}; using this PR's checked-in baseline. A must review this "
            "initial baseline.",
            file=sys.stderr,
        )
    if BASELINE.is_file():
        return json.loads(BASELINE.read_text()), f"working tree {BASELINE}"
    return {"findings": []}, "empty"


def _depfiles_changed_per_commit(root: Path, commits: list[str]) -> list[str]:
    """Commits in the range that change dependency manifests (per-commit check).

    The installed-environment scan covers HEAD; this surfaces any intermediate
    commit whose declared dependencies changed, so a push cannot hide a dep change
    behind a later revert. Reported and treated as requiring the audit.
    """
    hits: list[str] = []
    for sha in commits:
        proc = subprocess.run(["git", "show", "--name-only", "--format=", "-z", sha],
                              capture_output=True, text=True)
        paths = [x for x in proc.stdout.split("\x00") if x]
        if any(p.endswith(("pyproject.toml", "requirements.txt", "requirements-dev.txt"))
               or p.startswith("requirements") for p in paths):
            hits.append(sha)
    return hits


def _audit_requirements_at_rev(root: Path, rev: str, scanner=None) -> dict:
    """Resolve + audit the dependencies the project AT ``rev`` actually installs.

    Aligns with CI's gate dependency group ``.[dev]`` (not core-only ``.``):
      1. create an isolated git worktree at ``rev`` (so ``.``/pyproject resolve
         THAT revision's project),
      2. create an isolated venv (outside the worktree) and ``pip install ".[dev]"``
         from the worktree,
      3. audit the installed venv (``pip-audit --path <site-packages>``) — the same
         dependency group CI installs.
    A ``scanner(worktree, venv_dir)`` may be injected for controlled tests. Worktree
    and venv are always removed. Raises ScannerError on tool/parse failure; never
    audits an extracted HEAD requirements file.
    """
    import shutil
    import tempfile
    wt = Path(tempfile.mkdtemp(prefix="deprev-wt-"))
    venv = Path(tempfile.mkdtemp(prefix="deprev-venv-")) / "v"
    added = False
    try:
        add = subprocess.run(["git", "-C", str(root), "worktree", "add", "--detach",
                              str(wt), rev], capture_output=True, text=True)
        if add.returncode != 0:
            raise ScannerError(f"cannot create worktree for {rev[:12]}: {add.stderr.strip()[:200]}")
        added = True
        if not (wt / "pyproject.toml").is_file():
            raise ScannerError(f"no pyproject.toml at {rev[:12]}; cannot resolve '.[dev]'")

        if scanner is not None:
            report = scanner(wt, venv)
        else:
            mk = subprocess.run([sys.executable, "-m", "venv", str(venv)],
                                capture_output=True, text=True)
            if mk.returncode != 0:
                raise ScannerError(f"venv create failed for {rev[:12]}: {mk.stderr.strip()[:200]}")
            vpy = venv / "bin" / "python"
            inst = subprocess.run([str(vpy), "-m", "pip", "install", "-q", ".[dev]"],
                                  capture_output=True, text=True, cwd=wt)
            if inst.returncode != 0:
                raise ScannerError(f"install '.[dev]' failed for {rev[:12]} (exit {inst.returncode}): "
                                   f"{inst.stderr.strip()[:200]}")
            # Audit the installed venv's site-packages using the CI interpreter,
            # which has the pinned pip-audit installed (.[dev] does NOT include
            # pip-audit, so the fresh revision venv cannot run it itself).
            sitepkgs = str(venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")
            proc = subprocess.run([sys.executable, "-m", "pip_audit", "--path", sitepkgs,
                                   "--format", "json", "--progress-spinner", "off"],
                                  capture_output=True, text=True, cwd=wt)
            if proc.returncode not in (0, 1):
                raise ScannerError(f"pip-audit failed for {rev[:12]} (exit {proc.returncode}): "
                                   f"{proc.stderr.strip()[:200]}")
            try:
                report = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise ScannerError(f"pip-audit non-JSON for {rev[:12]}") from exc
        validate_report(report)
        return report
    finally:
        if added:
            subprocess.run(["git", "-C", str(root), "worktree", "remove", "--force", str(wt)],
                           capture_output=True, text=True)
        else:
            shutil.rmtree(wt, ignore_errors=True)
        shutil.rmtree(venv.parent, ignore_errors=True)


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
    parser.add_argument("--event", default=None)
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--before", default=None)
    parser.add_argument("--after", default=None)
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

    env = dict(os.environ)
    if args.event is not None:
        env["GITHUB_EVENT_NAME"] = args.event
    if args.base_ref is not None:
        env["GITHUB_BASE_REF"] = args.base_ref
    if args.before is not None:
        env["GITHUB_BEFORE"] = args.before
    if args.after is not None:
        env["GITHUB_AFTER"] = args.after
    root = Path(".").resolve()
    try:
        rng = ci_event.resolve_range(root, env)
    except ci_event.EventError as exc:
        print(f"ERROR: cannot resolve dependency-audit applicability: {exc}", file=sys.stderr)
        return 2

    base, source = _load_baseline(rng.base_sha)
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

    # Per-commit dependency audit: audit the dependencies resolved at EACH commit
    # in the range (not just the installed HEAD env). A commit whose resolved deps
    # introduce a finding beyond the trusted baseline fails even if HEAD is clean.
    depfile_commits = set(_depfiles_changed_per_commit(root, rng.commits))
    per_commit_failures: list[tuple[str, list]] = []
    scanner_errors: list[str] = []
    for sha in rng.commits:
        if sha not in depfile_commits:
            continue  # deps unchanged at this commit -> same as range base resolution
        try:
            crev_report = _audit_requirements_at_rev(root, sha)
        except ScannerError as exc:
            scanner_errors.append(str(exc))
            continue
        cfound = findings(crev_report)
        cnew = [(p, v, vid, fix) for (p, v, vid, fix) in cfound if (p, vid, v) not in base_keys]
        if cnew:
            per_commit_failures.append((sha[:12], cnew))

    if scanner_errors:
        print("DEPENDENCY AUDIT FAILED: could not audit some revisions (not clean):", file=sys.stderr)
        for e in scanner_errors:
            print(f"  - {e}", file=sys.stderr)
        return 2
    if per_commit_failures:
        print("DEPENDENCY AUDIT FAILED: new finding(s) at intermediate commit(s):", file=sys.stderr)
        for sha, cnew in per_commit_failures:
            for (p, v, vid, fix) in cnew:
                print(f"  - commit {sha}: {p}=={v} {vid} fix={fix}", file=sys.stderr)
        return 1
    print(f"OK: no new dependency findings ({len(found)} at HEAD; "
          f"{len(depfile_commits)} dep-changing commit(s) audited; {len(rng.commits)} commit(s) in range)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
