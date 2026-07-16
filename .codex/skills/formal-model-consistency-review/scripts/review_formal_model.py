#!/usr/bin/env python3
"""Perform deterministic structural checks on formal-model Markdown."""
from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED = {
    "state tuple (Σ)": r"Σ\s*:=\s*⟨",
    "submission": r"Submit\(u\)",
    "policy choice": r"PolicyChoice",
    "tool routing": r"RouteTool|Dispatch\(runtime\)",
    "new-turn or steering routing": r"CreateTurn|SteerExistingTurn",
    "decision set": r"allow.*require_approval.*deny",
    "durable history": r"H.*durable|durable.*H",
    "live events": r"E.*live|live.*E",
}


def check(path: Path) -> list[tuple[str, str, str]]:
    text = path.read_text(encoding="utf-8")
    findings: list[tuple[str, str, str]] = []
    lines = text.splitlines()

    for label, pattern in REQUIRED.items():
        if not re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            findings.append(("error", label, f"Required concept not found: {pattern}"))

    if text.count("```") % 2:
        findings.append(("error", "code fences", "Unbalanced Markdown code fences."))

    mermaid_blocks = re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.DOTALL)
    for index, block in enumerate(mermaid_blocks, start=1):
        if not re.search(r"(?:flowchart|graph|sequenceDiagram|stateDiagram)", block):
            findings.append(("warning", f"Mermaid block {index}", "No recognized Mermaid diagram declaration."))

    # Catch transition-looking formulas that omit a state on either side.
    for number, line in enumerate(lines, start=1):
        if "──" in line and "▶" in line and not re.search(r"Σ.*──.*▶.*Σ|Σ.*──.*▶.*∃", line):
            findings.append(("warning", f"line {number}", "Transition may not state a postcondition or resulting state."))

    # The model should define the core state components together, not only mention them.
    component_lines = [line for line in lines if re.search(r"(?:^|\|)\s*`?[TAHQPKE]`?\s+(?:\||$)", line)]
    defined_components = {
        match.group(1)
        for line in component_lines
        for match in [re.search(r"(?:^|\|)\s*`?([TAHQPKE])`?\s+(?:\||$)", line)]
        if match
    }
    missing = sorted(set("TAHQPKE") - defined_components)
    if missing:
        findings.append(("error", "Σ residency", f"Missing component definitions: {', '.join(missing)}"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    all_findings: list[tuple[Path, str, str, str]] = []
    for path in args.paths:
        for severity, location, message in check(path):
            all_findings.append((path, severity, location, message))

    errors = sum(severity == "error" for _, severity, _, _ in all_findings)
    warnings = sum(severity == "warning" for _, severity, _, _ in all_findings)
    report = ["# Formal-model consistency review", "", f"Checked {len(args.paths)} file(s).", ""]
    if not all_findings:
        report.append("✅ No structural consistency findings.")
    else:
        report.append(f"Findings: {errors} error(s), {warnings} warning(s).")
        report.append("")
        for path, severity, location, message in all_findings:
            report.append(f"- **{severity}** `{path}:{location}` — {message}")
    output = "\n".join(report) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
