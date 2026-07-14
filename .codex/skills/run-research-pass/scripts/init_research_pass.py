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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    template_root = skill_root / "assets" / "templates"
    args.output.mkdir(parents=True, exist_ok=True)

    for name in TEMPLATES:
        destination = args.output / name
        if destination.exists():
            raise SystemExit(f"refusing to overwrite existing file: {destination}")
        payload = json.loads((template_root / name).read_text(encoding="utf-8"))
        if name in {"review-protocol.json", "research-pass-result.json"}:
            payload["profile"] = args.profile
        destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"created {len(TEMPLATES)} research-pass records in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
