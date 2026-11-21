#!/usr/bin/env python3
"""GOV-07 Workflow-permission guard (WS-C).

Rule (per A): untrusted PR code must not obtain write credentials or secrets —
NOT a blanket ban on all write permissions. Static check of the declared
boundary; does not prove all runtime credential flows.

Enforced (fail closed; ambiguous/unparseable => FAIL):
- workflow-level and job-level permissions, honoring inheritance
  (job inherits workflow when it omits ``permissions``);
- ``write-all`` anywhere;
- ``permissions:`` expression/ambiguous values that cannot be resolved to read-only;
- PR-reachable jobs (``pull_request``) whose *effective* permissions include any
  ``write`` scope;
- ``pull_request_target`` combined with secrets or PR-head checkout;
- PR-reachable checkout whose ``persist-credentials`` is not explicitly ``false``
  (the omitted default is ``true``);
- removal of the baseline ``permissions`` block;
- unsafe inheritance (PR-reachable job without its own ``permissions`` when the
  workflow grants more than the baseline).
- PyYAML parses the literal key ``on`` as boolean True; it is normalized to ``on``.

Applicability: only runs when a workflow file changes (or this guard/config/
workflow changes). Non-applicable -> stable success; resolution/parse -> failure.

Usage: python scripts/check_permissions.py [--root .]
Exit: 0 ok/non-applicable; 1 violation; 2 usage error.
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

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

CONFIG = "docs/ci/governance-guards.yaml"
SELF_FILES = (
    "scripts/check_permissions.py",
    "test/offline/test_permissions_guard.py",
    CONFIG,
    ".github/workflows/ci.yml",
)
BASELINE = {"contents": "read", "pull-requests": "read"}
WRITE_SCOPES = ("contents", "pull-requests", "issues", "actions", "checks",
                "deployments", "packages", "security-events", "statuses",
                "id-token", "discussions", "pages", "repository-projects")


class PermError(RuntimeError):
    pass


def _norm(obj) -> dict:
    """Normalize PyYAML's boolean ``on`` key to the string 'on'."""
    if not isinstance(obj, dict):
        return {}
    return {("on" if k is True else k): v for k, v in obj.items()}


def _eff_perms(job: dict, wf: dict) -> dict | None:
    """Return effective permissions for a job, or None if inherited/ambiguous.
    'write-all' -> {'__write_all__': True}. Unknown expression strings preserved."""
    job_perm = job.get("permissions", "__inherit__")
    if job_perm == "__inherit__":
        wf_perm = wf.get("permissions", "__absent__")
        if wf_perm == "__absent__":
            return None
        return _coerce(wf_perm)
    return _coerce(job_perm)


def _coerce(p) -> dict:
    if p == "write-all":
        return {"__write_all__": True}
    if p == "read-all":
        return dict.fromkeys(WRITE_SCOPES, "read")
    if isinstance(p, dict):
        return {str(k): v for k, v in p.items()}
    # expression / ambiguous scalar
    return {"__ambiguous__": str(p)}


def _is_pr_reachable(wf: dict) -> bool:
    on = _norm(wf).get("on")
    if isinstance(on, dict):
        return "pull_request" in on or "pull_request_target" in on
    if isinstance(on, list):
        return "pull_request" in on or "pull_request_target" in on
    if isinstance(on, str):
        return on in ("pull_request", "pull_request_target")
    return False


def _opens_on_pr(wf: dict, event: str) -> bool:
    on = _norm(wf).get("on")
    if isinstance(on, dict):
        return event in on
    if isinstance(on, list):
        return event in on
    if isinstance(on, str):
        return on == event
    return False


def _scan_workflow(path: Path, text: str) -> list[str]:
    if yaml is None:
        raise PermError("PyYAML required")
    try:
        wf = _norm(yaml.safe_load(text) or {})
    except yaml.YAMLError as exc:
        raise PermError(f"{path.name}: unparseable YAML: {exc}") from exc

    problems: list[str] = []
    if not isinstance(wf, dict):
        raise PermError(f"{path.name}: workflow is not a mapping")

    # Baseline block present? (restriction removal)
    if "permissions" not in wf:
        problems.append(f"{path.name}: baseline workflow-level 'permissions' block is absent (restriction removal)")

    pr_reachable = _is_pr_reachable(wf)
    uses_prt = _opens_on_pr(wf, "pull_request_target")
    wf_perm = wf.get("permissions")

    jobs = wf.get("jobs") or {}
    if not isinstance(jobs, dict):
        raise PermError(f"{path.name}: 'jobs' is not a mapping")
    for jname, job in jobs.items():
        if not isinstance(job, dict):
            continue
        job_perm = job.get("permissions", "__inherit__")
        # effective permissions
        eff = _eff_perms(job, wf)
        if eff is not None:
            if eff.get("__write_all__"):
                problems.append(f"{path.name}:{jname}: 'permissions: write-all' present")
            if "__ambiguous__" in eff:
                problems.append(f"{path.name}:{jname}: ambiguous/expression permissions {eff['__ambiguous__']!r}")
            if pr_reachable:
                for scope, level in eff.items():
                    if scope.startswith("__"):
                        continue
                    if str(level) == "write":
                        problems.append(f"{path.name}:{jname}: PR-reachable job has write scope '{scope}'")
        # unsafe inheritance: PR-reachable job omitting permissions while workflow grants more than baseline
        if pr_reachable and job_perm == "__inherit__" and isinstance(wf_perm, dict):
            for scope, level in wf_perm.items():
                if str(level) == "write" and BASELINE.get(str(scope)) != "write":
                    problems.append(f"{path.name}:{jname}: unsafe inheritance of write scope '{scope}' from workflow")

        # pull_request_target + secrets or PR-head checkout
        if uses_prt:
            jtext = yaml.safe_dump(job, allow_unicode=True)
            if "secrets." in jtext:
                problems.append(f"{path.name}:{jname}: pull_request_target job references secrets")
            if "github.event.pull_request.head" in jtext or "refs/pull/" in jtext:
                problems.append(f"{path.name}:{jname}: pull_request_target checks out PR head")

        # persist-credentials on PR-reachable checkout must be explicitly false
        if pr_reachable:
            for step in (job.get("steps") or []):
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                if uses.startswith("actions/checkout"):
                    with_ = step.get("with") or {}
                    pc = with_.get("persist-credentials", "__absent__") if isinstance(with_, dict) else "__absent__"
                    if pc is not False and str(pc).lower() != "false":
                        problems.append(
                            f"{path.name}:{jname}: PR-reachable checkout persist-credentials "
                            f"is {pc!r} (must be explicitly false)")
    return problems


def _changed(root: Path, commits: list[str]) -> set[str]:
    out: set[str] = set()
    for sha in commits:
        proc = subprocess.run(
            ["git", "-C", str(root), "show", "--pretty=format:", "--name-only", sha],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise ci_event.EventError(f"cannot list files for {sha[:12]}")
        out.update(ln.strip() for ln in proc.stdout.splitlines() if ln.strip())
    return out


def scan_workflows(root: Path) -> list[str]:
    problems: list[str] = []
    wf_dir = root / ".github" / "workflows"
    files = sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")))
    if not files:
        raise PermError("no workflow files found")
    for p in files:
        problems.extend(_scan_workflow(p, p.read_text()))
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GOV-07 permission guard")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        rng = ci_event.resolve_range(root, dict(os.environ))
        changed = _changed(root, rng.commits)
    except ci_event.EventError as exc:
        print(f"PERMISSION GUARD FAILED: {exc}", file=sys.stderr)
        return 1

    def touched(c: str) -> bool:
        return c.startswith(".github/workflows/")

    if not (any(touched(c) for c in changed) or any(c in changed for c in SELF_FILES)):
        print("PERMISSION GUARD: skipped (no in-scope change)")
        return 0

    try:
        problems = scan_workflows(root)
    except PermError as exc:
        print(f"PERMISSION GUARD FAILED: {exc}", file=sys.stderr)
        return 1

    _out = os.environ.get("GOVERNANCE_RESULT_JSON")
    if _out:
        Path(_out).write_text(json.dumps({"guard": "permission", "violations": problems}, indent=2))
    if problems:
        print("PERMISSION GUARD FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("PERMISSION GUARD: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
