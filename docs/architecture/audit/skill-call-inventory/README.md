# Skill-call research pass

This is the evidence bundle for the clickable
[skill and CLI call inventory](../../08-skill-and-cli-call-inventory.md). It is
pinned to commit `be0e0d791a1b735de307f013037b091d24f57484` and reviewed on
2026-07-16.

Read the human navigation files first:

1. [Clickable source and evidence index](source-audit.md)
2. [Clickable claim ledger](claim-ledger.md)
3. [Machine-readable call inventory](skill-call-inventory.json)

The normative audit records are also available:

- [Review protocol](review-protocol.json)
- [Source audit](source-audit.json)
- [Claim ledger JSON](claim-ledger.json)
- [Adversarial review](adversarial-claim-review.json)
- [Evidence gaps](evidence-gaps.json)
- [Research result](research-pass-result.json)

Validate from the repository root:

```bash
python3 .codex/skills/run-research-pass/scripts/validate_research_pass.py \
  docs/architecture/audit/skill-call-inventory
```

The pass contains 20 call records and 20 reviewed claims. It is source-based,
not a live production trace. Open gaps cover product-wide side-effect
persistence, the complete corpus of commands launched by installed skills, and
provider-by-provider authority conformance.
