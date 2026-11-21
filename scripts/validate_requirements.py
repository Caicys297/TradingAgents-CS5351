#!/usr/bin/env python3
"""Validate the CS5351 requirements registry against its checked-in JSON Schema.

Checks performed (all produce a nonzero exit code on failure):

1. Both inputs exist and parse (the schema is itself a valid Draft 2020-12 schema).
2. The registry contains no duplicate mapping keys (PyYAML silently keeps the
   last one otherwise).
3. The registry validates against ``docs/req/req-schema.json`` (Draft 2020-12).
4. Requirement ``id`` values are unique (the schema cannot express this).

The registry and schema files are read-only inputs; this script never rewrites
them.

Usage:
    python scripts/validate_requirements.py
    python scripts/validate_requirements.py --registry PATH --schema PATH

Exit codes:
    0  valid
    1  validation failure (missing file, bad YAML/JSON, duplicate keys,
       schema violation, duplicate requirement IDs)
    2  usage / unexpected internal error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError as exc:  # pragma: no cover - exercised via subprocess in tests
    print(f"ERROR: missing dependency: {exc}", file=sys.stderr)
    raise SystemExit(2) from None


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys."""

    def construct_mapping(self, node, deep=False):  # type: ignore[override]
        seen: set[Any] = set()
        for key_node, _value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in seen
            except TypeError:  # unhashable key; YAML itself will reject it
                duplicate = False
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key: {key!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def load_registry(path: Path) -> Any:
    """Load the YAML registry, rejecting duplicate keys and malformed YAML."""
    text = path.read_text(encoding="utf-8")
    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"malformed YAML in {path}: {exc}") from exc


def load_schema(path: Path) -> dict[str, Any]:
    """Load and structurally check the JSON Schema (Draft 2020-12)."""
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON schema {path}: {exc}") from exc
    if not isinstance(schema, dict):
        raise ValueError(f"schema {path} is not a JSON object")
    declared = schema.get("$schema", "")
    if "2020-12" not in declared:
        raise ValueError(
            f"schema {path} declares dialect {declared!r}; expected a 2020-12 dialect"
        )
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ValueError(f"schema {path} is not a valid JSON Schema: {exc.message}") from exc
    return schema


def validate(registry_path: Path, schema_path: Path) -> list[str]:
    """Return a list of human-readable errors (empty means valid)."""
    if not registry_path.is_file():
        return [f"registry not found: {registry_path}"]
    if not schema_path.is_file():
        return [f"schema not found: {schema_path}"]

    try:
        schema = load_schema(schema_path)
    except ValueError as exc:
        return [str(exc)]

    try:
        registry = load_registry(registry_path)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []
    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(registry), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{location}: {err.message}")

    # Duplicate requirement IDs (the schema cannot express uniqueness).
    if isinstance(registry, dict) and isinstance(registry.get("requirements"), list):
        first_index: dict[str, int] = {}
        for idx, item in enumerate(registry["requirements"]):
            if not isinstance(item, dict):
                continue
            rid = item.get("id")
            if not isinstance(rid, str):
                continue
            if rid in first_index:
                errors.append(
                    f"requirements/{idx}/id: duplicate requirement id "
                    f"{rid!r} (first at index {first_index[rid]})"
                )
            else:
                first_index[rid] = idx

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the requirements registry.")
    parser.add_argument("--registry", default="docs/req/requirements.yaml", type=Path)
    parser.add_argument("--schema", default="docs/req/req-schema.json", type=Path)
    args = parser.parse_args(argv)

    try:
        errors = validate(args.registry, args.schema)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"ERROR: unexpected failure: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(f"INVALID: {len(errors)} problem(s) in {args.registry}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: {args.registry} validates against {args.schema}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
