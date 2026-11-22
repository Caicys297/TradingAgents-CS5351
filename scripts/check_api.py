#!/usr/bin/env python3
"""GOV-07 API guard (WS-C).

A path change triggers checking; an actual contract violation blocks. When any
protected api path — or this guard's own files/config/workflow — changes in
the event's trusted range, the mapped existing pytest nodes must pass. Otherwise
the job reports a stable non-applicability success.

Failure modes:
- range resolution error / unparseable config / missing node -> FAIL (never skip)
- a mapped node fails -> FAIL
- no in-scope change -> PASS (visible "skipped")

Usage: python scripts/check_api.py [--root .]
Exit: 0 ok or legitimate non-applicability; 1 failure; 2 execution/usage error.
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
    "scripts/check_api.py",
    "test/offline/test_api_guard.py",
    CONFIG,
    ".github/workflows/ci.yml",
)


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


def _load(root: Path) -> dict:
    if yaml is None:
        raise RuntimeError("PyYAML required")
    data = yaml.safe_load((root / CONFIG).read_text()) or {}
    if not isinstance(data, dict) or "api" not in data:
        raise RuntimeError(f"malformed {CONFIG}: missing 'api'")
    return data["api"]


def _touched(changed: set[str], protected: list[str]) -> bool:
    for p in protected:
        prefix = p.rstrip("/") + "/"
        if any(c == p or c.startswith(prefix) for c in changed):
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="GOV-07 api guard")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()

    try:
        rng = ci_event.resolve_range(root, dict(os.environ))
        cfg = _load(root)
        changed = _changed(root, rng.commits)
    except (ci_event.EventError, RuntimeError, OSError) as exc:
        print(f"API GUARD FAILED: {exc}", file=sys.stderr)
        return 1

    protected = [str(p) for p in cfg.get("protected_paths", [])]
    nodes = [str(n) for n in cfg.get("nodes", [])]
    if not nodes:
        print("API GUARD FAILED: no mapped nodes in config", file=sys.stderr)
        return 1

    triggered = _touched(changed, protected + list(SELF_FILES))
    if not triggered:
        print("API GUARD: skipped (no in-scope change)")
        return 0

    # Run the mapped existing nodes; a failure blocks.
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *nodes], cwd=str(root),
    )
    result = {"guard": "api", "commits": len(rng.commits),
              "nodes": nodes, "returncode": proc.returncode}
    _out = os.environ.get("GOVERNANCE_RESULT_JSON")
    if _out:
        Path(_out).write_text(json.dumps(result, indent=2))
    if proc.returncode != 0:
        print("API GUARD FAILED: a mapped api node failed", file=sys.stderr)
        return 1
    print("API GUARD: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
