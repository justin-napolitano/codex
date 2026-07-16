#!/usr/bin/env python3
"""Validate the machine-checkable formal-model registry using stdlib only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(path: Path, coverage_path: Path | None = None) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    state = data.get("state", {})
    components = state.get("components", {})
    symbols = data.get("symbols", {})
    transitions = data.get("transitions", [])
    cost_dimensions = set(data.get("cost_model", {}).get("dimensions", []))
    if not cost_dimensions:
        errors.append("cost_model.dimensions must be declared")
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
    transition_names = {transition.get("name") for transition in transitions}
    coverage = {}
    if coverage_path:
        coverage_data = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage = {item.get("coverage_id"): item for item in coverage_data.get("coverage", [])}
        if len(coverage) != len(coverage_data.get("coverage", [])):
            errors.append("coverage_ids must be unique")
        for item in coverage.values():
            source = item.get("source", "").split("#", 1)[0]
            source_root = coverage_path.parent.parent.parent.parent
            if source and not (source_root / source).exists():
                errors.append(f"coverage {item.get('coverage_id')} source does not resolve: {source}")
            if item.get("status") not in {"covered", "partially_covered", "unmodeled"}:
                errors.append(f"coverage {item.get('coverage_id')} has invalid status")
    for transition in transitions:
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
        for coverage_id in transition.get("coverage_ids", []):
            if coverage_path and coverage_id not in coverage:
                errors.append(f"transition {transition.get('name')} references unknown coverage {coverage_id}")
        if transition.get("uncertainty") not in {"observed", "inferred", "normative", "hypothesis", "unverified"}:
            errors.append(f"transition {transition.get('name')} has invalid uncertainty")
        if not transition.get("cost_dimensions"):
            errors.append(f"transition {transition.get('name')} must declare cost_dimensions")
        for dimension in transition.get("cost_dimensions", []):
            if dimension not in cost_dimensions:
                errors.append(f"transition {transition.get('name')} uses undeclared cost dimension {dimension}")
    for invariant in data.get("invariants", []):
        if not invariant.get("name") or not invariant.get("scope") or not invariant.get("formula"):
            errors.append("each invariant requires name, scope, and formula")
        for component in invariant.get("scope", []):
            if component not in components:
                errors.append(f"invariant {invariant.get('name')} scopes undeclared component {component}")
        for transition_name in invariant.get("preserved_by", []):
            if transition_name not in transition_names:
                errors.append(f"invariant {invariant.get('name')} references unknown transition {transition_name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--coverage", type=Path)
    args = parser.parse_args()
    errors = validate(args.path, args.coverage)
    if errors:
        print(f"formal-model spec failed: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("formal-model spec validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
