# Architecture research pass

This directory is the reproducible evidence record for the high-level Codex
architecture guide. It audits the guide and the architectural/behavioral
contracts in the linked Codex technical documents at commit
`be0e0d791a1b735de307f013037b091d24f57484`, with a review cutoff of
2026-07-14.

Read the records in this order:

1. [`review-protocol.json`](review-protocol.json) freezes scope and exclusions.
2. [`source-audit.json`](source-audit.json) says exactly what was inspected and
   what each source can and cannot establish.
3. [`claim-ledger.json`](claim-ledger.json) maps atomic claims to evidence and
   retained wording.
4. [`adversarial-claim-review.json`](adversarial-claim-review.json) records the
   strongest objection and decision for every claim.
5. [`evidence-gaps.json`](evidence-gaps.json) keeps unresolved questions visible.
6. [`research-pass-result.json`](research-pass-result.json) gives exact totals
   and the validation command.

This is an implementation audit, not a formal verification. `established`
means direct evidence establishes the claim within its stated scope;
`local_observation_only` means it was observed at the pinned commit and must
not be generalized as a permanent product promise. The app-server reference is
audited at the architectural and behavioral-contract level. Exhaustively
duplicating every field in its large API catalog is intentionally excluded;
the checked-in protocol types and generated schemas remain authoritative for
those shapes.

Validate the record from the repository root:

```bash
python3 .codex/skills/run-research-pass/scripts/validate_research_pass.py \
  docs/architecture/audit
```

The companion [tool-call and routing audit](tool-call-routing/README.md) uses
the same implementation-audit contract for the runtime dispatch path. The
[skill/CLI inventory audit](skill-call-inventory/README.md) applies it to skill
discovery, resource reads, and script command boundaries.
