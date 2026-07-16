#!/usr/bin/env python3
"""Validate the machine-checkable formal-model registry using stdlib only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    state = data.get("state", {})
    components = state.get("components", {})
    symbols = data.get("symbols", {})
    if state.get("name") != "Σ":
        errors.append("state.name must be Σ")
    if set(components) != set("TAHQPKE"):
        errors.append("state.components must define exactly T, A, H, Q, P, K, and E")
    if len(symbols) != len(set(symbols)):
        errors.append("symbols contain duplicate names")
    for name, spec in symbols.items():
        if spec.get("kind") not in {"sort", "set", "predicate", "function"}:
            errors.append(f"symbol {name} has an invalid kind")
        if spec.get("kind") in {"predicate", "function"} and not spec.get("args"):
            errors.append(f"symbol {name} must declare args")
    known = set(symbols)
    for transition in data.get("transitions", []):
        for field in ("name", "action", "preconditions", "writes", "postconditions"):
            if not transition.get(field):
                errors.append(f"transition {transition.get('name', '<unnamed>')} missing {field}")
        for component in transition.get("writes", []):
            if component not in components:
                errors.append(f"transition {transition.get('name')} writes undeclared component {component}")
        for predicate in transition.get("preconditions", []):
            base = predicate.replace("not ", "").split(" OR ")[0].split("=")[0]
            if base and base not in known and base not in {"ActiveNonSteerableTurn"}:
                errors.append(f"transition {transition.get('name')} references undeclared predicate {base}")
    for invariant in data.get("invariants", []):
        if not invariant.get("name") or not invariant.get("scope") or not invariant.get("formula"):
            errors.append("each invariant requires name, scope, and formula")
        for component in invariant.get("scope", []):
            if component not in components:
                errors.append(f"invariant {invariant.get('name')} scopes undeclared component {component}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate(args.path)
    if errors:
        print(f"formal-model spec failed: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("formal-model spec validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
