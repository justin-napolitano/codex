#!/usr/bin/env python3
"""Validate simple lifecycle traces against the declared transition vocabulary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(spec_path: Path, trace_path: Path) -> list[str]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    traces = json.loads(trace_path.read_text(encoding="utf-8")).get("traces", [])
    actions = {item["action"] for item in spec.get("transitions", [])}
    actions |= {"Handle", "ToolCall", "PolicyChoice", "Approve", "Steer", "Result"}
    errors: list[str] = []
    for trace in traces:
        pending_approval = bool(trace.get("initial_state", {}).get("pending_approval", False))
        active_turns = int(trace.get("initial_state", {}).get("active_normal_turns", 0))
        for index, event in enumerate(trace.get("trace", [])):
            action = event.get("action")
            if action not in actions:
                errors.append(f"{trace.get('trace_id')} step {index}: unknown action {action}")
            if action == "RequestApproval":
                pending_approval = True
            elif action == "Approve":
                if not pending_approval:
                    errors.append(f"{trace.get('trace_id')} step {index}: approval without pending request")
                pending_approval = False
            elif action == "Dispatch" and pending_approval:
                errors.append(f"{trace.get('trace_id')} step {index}: dispatch while approval is pending")
            elif action == "Submit" and active_turns > 0:
                # A subsequent Steer is the only accepted continuation in this compact trace model.
                if index + 1 >= len(trace.get("trace", [])) or trace["trace"][index + 1].get("action") != "Steer":
                    errors.append(f"{trace.get('trace_id')} step {index}: active-turn submission is not followed by steering")
            elif action == "Handle":
                active_turns = max(active_turns, 1)
        if pending_approval:
            errors.append(f"{trace.get('trace_id')}: trace ends with approval pending")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("traces", type=Path)
    args = parser.parse_args()
    errors = validate(args.spec, args.traces)
    if errors:
        print(f"formal traces failed: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("formal trace validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
