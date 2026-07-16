#!/usr/bin/env python3
"""Validate the internal consistency and completion contract of a research pass."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


STRENGTHS = {
    "established",
    "supported",
    "suggestive",
    "hypothesis_only",
    "local_observation_only",
    "unsupported",
}
DECISIONS = {
    "accepted",
    "weakened",
    "moved_to_hypothesis",
    "moved_to_evidence_gap",
    "removed",
}
FILES = {
    "protocol": "review-protocol.json",
    "sources": "source-audit.json",
    "claims": "claim-ledger.json",
    "reviews": "adversarial-claim-review.json",
    "gaps": "evidence-gaps.json",
    "result": "research-pass-result.json",
}


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required file: {path.name}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path.name}: {exc}")
    return {}


def require(record: dict[str, Any], fields: set[str], label: str, errors: list[str]) -> None:
    missing = sorted(field for field in fields if field not in record)
    if missing:
        errors.append(f"{label} missing fields: {', '.join(missing)}")


def duplicate_ids(records: list[dict[str, Any]], field: str) -> set[str]:
    values = [str(record.get(field)) for record in records if record.get(field)]
    return {value for value, count in Counter(values).items() if count > 1}


def validate_clickable_inventory(
    audit_dir: Path,
    sources: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    errors: list[str],
) -> None:
    """Validate the optional clickable call inventory extension."""
    inventory_files = (
        ("skill-call-inventory.json", "skill inventory"),
        ("tool-call-routing-inventory.json", "tool-routing inventory"),
        ("policy-call-inventory.json", "policy inventory"),
    )
    existing = [(audit_dir / name, label) for name, label in inventory_files if (audit_dir / name).exists()]
    if not existing:
        return
    for path, inventory_label in existing:
        _validate_inventory_file(path, inventory_label, audit_dir, sources, claims, errors)


def _validate_inventory_file(
    path: Path,
    inventory_label: str,
    audit_dir: Path,
    sources: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    errors: list[str],
) -> None:
    payload = load_json(path, errors)
    if not isinstance(payload, dict):
        errors.append(f"{path.name} must contain an object")
        return
    records = payload.get("records", [])
    require(payload, {"inventory_id", "pinned_commit", "records"}, inventory_label, errors)
    if not isinstance(records, list):
        errors.append(f"{inventory_label} records must be a list")
        return

    source_ids = {source.get("source_id") for source in sources}
    claim_ids = {claim.get("claim_id") for claim in claims}
    evidence_ids = {
        point.get("evidence_id")
        for source in sources
        for point in source.get("evidence_points", [])
        if isinstance(point, dict) and point.get("evidence_id")
    }
    for source in sources:
        validate_links(source.get("source_links", []), audit_dir, f"source {source.get('source_id')}", errors)
    record_fields = {
        "call_id", "anchor", "phase", "kind", "name", "caller", "target",
        "source_refs", "claim_refs", "evidence_ids", "input", "output",
        "authority_boundary", "side_effects", "failure_modes", "model_visible",
        "links",
    }
    for index, record in enumerate(records):
        require(record, record_fields, f"{inventory_label} record[{index}]", errors)
        call_id = record.get("call_id")
        anchor = record.get("anchor", "")
        if not isinstance(anchor, str) or not re.fullmatch(r"[a-z0-9-]+", anchor):
            errors.append(f"{inventory_label} record {call_id} has invalid anchor")
        for field, known, label in (
            ("source_refs", source_ids, "source"),
            ("claim_refs", claim_ids, "claim"),
            ("evidence_ids", evidence_ids, "evidence"),
        ):
            values = record.get(field, [])
            if not isinstance(values, list):
                errors.append(f"{inventory_label} record {call_id} {field} must be a list")
                continue
            for value in values:
                if value not in known:
                    errors.append(f"{inventory_label} record {call_id} references unknown {label} {value}")
        validate_links(record.get("links", []), audit_dir, f"{inventory_label} record {call_id}", errors)
    duplicate_records = duplicate_ids(records, "call_id")
    if duplicate_records:
        errors.append(f"duplicate {inventory_label} call IDs: {', '.join(sorted(duplicate_records))}")

    for index, claim in enumerate(claims):
        for item in claim.get("evidence", []):
            if not isinstance(item, dict) or not item.get("evidence_id"):
                errors.append(f"claim {claim.get('claim_id')} lacks clickable evidence_id")
            elif item["evidence_id"] not in evidence_ids:
                errors.append(
                    f"claim {claim.get('claim_id')} references unknown evidence {item['evidence_id']}"
                )
            links = item.get("links", [])
            if not links:
                errors.append(f"claim {claim.get('claim_id')} evidence {item.get('evidence_id')} lacks clickable links")
            validate_links(links, audit_dir, f"claim {claim.get('claim_id')} evidence", errors)


def validate_links(links: Any, base_dir: Path, label: str, errors: list[str]) -> None:
    if not isinstance(links, list):
        errors.append(f"{label} links must be a list")
        return
    for link in links:
        if not isinstance(link, dict) or not link.get("label") or not link.get("target"):
            errors.append(f"{label} has malformed clickable link")
            continue
        target = str(link["target"])
        if re.match(r"^(?:https?:|mailto:|#)", target):
            continue
        file_target = target.split("#", 1)[0]
        if not (base_dir / file_target).resolve().exists():
            errors.append(f"{label} link target does not exist: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_dir", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    data = {key: load_json(args.audit_dir / name, errors) for key, name in FILES.items()}

    protocol = data["protocol"] if isinstance(data["protocol"], dict) else {}
    sources = data["sources"].get("sources", []) if isinstance(data["sources"], dict) else []
    claims = data["claims"].get("claims", []) if isinstance(data["claims"], dict) else []
    reviews = data["reviews"].get("reviews", []) if isinstance(data["reviews"], dict) else []
    gaps = data["gaps"].get("gaps", []) if isinstance(data["gaps"], dict) else []
    result = data["result"] if isinstance(data["result"], dict) else {}

    require(
        protocol,
        {
            "protocol_id", "profile", "research_question", "targets", "cutoff_date",
            "search_venues", "search_terms", "allowed_source_classes",
            "inclusion_criteria", "exclusion_criteria", "status",
        },
        "review protocol",
        errors,
    )
    if protocol.get("profile") not in {
        "implementation-audit", "literature-review", "publication-pass"
    }:
        errors.append(f"unknown profile: {protocol.get('profile')}")
    if protocol.get("status") not in {"in_progress", "complete"}:
        errors.append(f"unknown protocol status: {protocol.get('status')}")

    source_fields = {
        "source_id", "source_class", "title", "locator", "version_or_commit",
        "inspected_locations", "supports", "limitations", "accessed_at",
    }
    for index, source in enumerate(sources):
        require(source, source_fields, f"source[{index}]", errors)
    duplicate_sources = duplicate_ids(sources, "source_id")
    if duplicate_sources:
        errors.append(f"duplicate source IDs: {', '.join(sorted(duplicate_sources))}")
    source_ids = {source.get("source_id") for source in sources}

    claim_fields = {
        "claim_id", "claim", "claim_class", "target_location", "evidence",
        "counterevidence_or_limits", "strength", "final_wording", "status",
    }
    for index, claim in enumerate(claims):
        require(claim, claim_fields, f"claim[{index}]", errors)
        if claim.get("strength") not in STRENGTHS:
            errors.append(f"claim {claim.get('claim_id')} has invalid strength")
        if claim.get("status") not in DECISIONS:
            errors.append(f"claim {claim.get('claim_id')} has invalid status")
        evidence = claim.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"claim {claim.get('claim_id')} evidence must be a list")
            continue
        for item in evidence:
            if not isinstance(item, dict) or not item.get("source_id") or not item.get("point"):
                errors.append(f"claim {claim.get('claim_id')} has malformed evidence")
            elif item["source_id"] not in source_ids:
                errors.append(
                    f"claim {claim.get('claim_id')} references unknown source {item['source_id']}"
                )
    duplicate_claims = duplicate_ids(claims, "claim_id")
    if duplicate_claims:
        errors.append(f"duplicate claim IDs: {', '.join(sorted(duplicate_claims))}")
    claim_ids = {claim.get("claim_id") for claim in claims}

    validate_clickable_inventory(args.audit_dir, sources, claims, errors)

    review_fields = {
        "claim_id", "strongest_objection", "source_limitations",
        "conflicting_evidence", "decision", "rationale",
    }
    for index, review in enumerate(reviews):
        require(review, review_fields, f"review[{index}]", errors)
        if review.get("claim_id") not in claim_ids:
            errors.append(f"review references unknown claim {review.get('claim_id')}")
        if review.get("decision") not in DECISIONS:
            errors.append(f"review for {review.get('claim_id')} has invalid decision")
    duplicate_reviews = duplicate_ids(reviews, "claim_id")
    if duplicate_reviews:
        errors.append(f"duplicate claim reviews: {', '.join(sorted(duplicate_reviews))}")

    gap_fields = {"gap_id", "question", "missing_evidence", "searches_performed", "impact", "next_action", "status"}
    for index, gap in enumerate(gaps):
        require(gap, gap_fields, f"gap[{index}]", errors)

    require(
        result,
        {
            "profile", "status", "target_claim_count", "inspected_source_count",
            "strength_counts", "decision_counts", "open_evidence_gap_count",
            "changed_target_files", "validation",
        },
        "research result",
        errors,
    )

    strength_counts = Counter(claim.get("strength") for claim in claims)
    decision_counts = Counter(review.get("decision") for review in reviews)
    open_gap_count = sum(1 for gap in gaps if gap.get("status") == "open")
    expected = {
        "target_claim_count": len(claims),
        "inspected_source_count": len(sources),
        "open_evidence_gap_count": open_gap_count,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            errors.append(f"result {field} is {result.get(field)!r}; expected {value}")
    for strength in STRENGTHS:
        if result.get("strength_counts", {}).get(strength) != strength_counts[strength]:
            errors.append(f"result strength count for {strength} does not match")
    for decision in DECISIONS:
        if result.get("decision_counts", {}).get(decision) != decision_counts[decision]:
            errors.append(f"result decision count for {decision} does not match")

    complete = protocol.get("status") == "complete" or result.get("status") == "complete"
    if protocol.get("status") != result.get("status"):
        errors.append("protocol and result status differ")
    if complete:
        if not claims:
            errors.append("a complete pass must contain claims")
        if strength_counts["unsupported"]:
            errors.append("a complete pass cannot retain unsupported claims")
        if len(reviews) != len(claims):
            errors.append("every claim in a complete pass must have one review")
        for claim in claims:
            if claim.get("status") != next(
                (review.get("decision") for review in reviews if review.get("claim_id") == claim.get("claim_id")),
                None,
            ):
                errors.append(f"claim/review decision mismatch for {claim.get('claim_id')}")
            if claim.get("status") != "removed" and not claim.get("final_wording"):
                errors.append(f"retained claim {claim.get('claim_id')} lacks final wording")

    if errors:
        print("research-pass validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"research-pass validation passed: {len(claims)} claims, "
        f"{len(sources)} sources, {len(reviews)} reviews, {open_gap_count} open gaps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
