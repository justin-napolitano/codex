#!/usr/bin/env python3
"""Create a research-pass audit directory from the bundled JSON templates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROFILES = {"implementation-audit", "literature-review", "publication-pass"}
TEMPLATES = (
    "review-protocol.json",
    "source-audit.json",
    "claim-ledger.json",
    "adversarial-claim-review.json",
    "evidence-gaps.json",
    "research-pass-result.json",
)
CALL_INVENTORY_TEMPLATES = {
    "skill": "skill-call-inventory.json",
    "tool-routing": "tool-call-routing-inventory.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--with-call-inventory",
        action="store_true",
        help="also create the clickable skill/API call inventory template",
    )
    parser.add_argument(
        "--with-tool-routing-inventory",
        action="store_true",
        help="also create the clickable tool-call/routing inventory template",
    )
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    template_root = skill_root / "assets" / "templates"
    args.output.mkdir(parents=True, exist_ok=True)

    template_names = list(TEMPLATES)
    if args.with_call_inventory:
        template_names.append(CALL_INVENTORY_TEMPLATES["skill"])
    if args.with_tool_routing_inventory:
        template_names.append(CALL_INVENTORY_TEMPLATES["tool-routing"])

    for name in template_names:
        destination = args.output / name
        if destination.exists():
            raise SystemExit(f"refusing to overwrite existing file: {destination}")
        payload = json.loads((template_root / name).read_text(encoding="utf-8"))
        if name in {"review-protocol.json", "research-pass-result.json"}:
            payload["profile"] = args.profile
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"created {len(template_names)} research-pass records in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
