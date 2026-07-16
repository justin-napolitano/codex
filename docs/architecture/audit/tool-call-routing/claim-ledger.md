# Clickable claim ledger

Each claim is reviewed against a pinned implementation or test source. The
JSON ledger is authoritative for strength and decision fields.

| Claim | Reviewed wording | Strength | Evidence |
| --- | --- | --- | --- |
| [TR-CLAIM-001](claim-ledger.json#tr-claim-001) | Tool specs are an exposure projection. | supported | [E-TR-001](source-audit.json#e-tr-001) |
| [TR-CLAIM-002](claim-ledger.json#tr-claim-002) | Response items become typed calls with IDs. | established | [E-TR-002](source-audit.json#e-tr-002) |
| [TR-CLAIM-003](claim-ledger.json#tr-claim-003) | Router creates invocation context. | established | [E-TR-003](source-audit.json#e-tr-003) |
| [TR-CLAIM-004](claim-ledger.json#tr-claim-004) | Registry resolves registered names. | established | [E-TR-004](source-audit.json#e-tr-004) |
| [TR-CLAIM-005](claim-ledger.json#tr-claim-005) | Hooks inspect/rewrite/convert payloads. | supported | [E-TR-005](source-audit.json#e-tr-005) |
| [TR-CLAIM-006](claim-ledger.json#tr-claim-006) | Policy derives approval requirements. | supported | [E-TR-006](source-audit.json#e-tr-006) |
| [TR-CLAIM-007](claim-ledger.json#tr-claim-007) | Approval decisions can be cached or denied. | supported | [E-TR-007](source-audit.json#e-tr-007) |
| [TR-CLAIM-008](claim-ledger.json#tr-claim-008) | Escalation preserves denied reads. | established | [E-TR-008](source-audit.json#e-tr-008) |
| [TR-CLAIM-009](claim-ledger.json#tr-claim-009) | Parallelism and cancellation are runtime-gated. | supported | [E-TR-009](source-audit.json#e-tr-009) |
| [TR-CLAIM-010](claim-ledger.json#tr-claim-010) | Unified exec reaches local or exec-server boundary. | supported | [E-TR-010](source-audit.json#e-tr-010) |
| [TR-CLAIM-011](claim-ledger.json#tr-claim-011) | Patch execution checks paths and correlates output. | supported | [E-TR-011](source-audit.json#e-tr-011) |
| [TR-CLAIM-012](claim-ledger.json#tr-claim-012) | MCP preserves namespaced identity. | supported | [E-TR-012](source-audit.json#e-tr-012) |
| [TR-CLAIM-013](claim-ledger.json#tr-claim-013) | App-server routes turn lifecycle requests. | supported | [E-TR-013](source-audit.json#e-tr-013) |
| [TR-CLAIM-014](claim-ledger.json#tr-claim-014) | Completion preserves call ID and telemetry. | supported | [E-TR-014](source-audit.json#e-tr-014) |
| [TR-CLAIM-015](claim-ledger.json#tr-claim-015) | Events can become rollout history. | supported | [E-TR-015](source-audit.json#e-tr-015) |
| [TR-CLAIM-016](claim-ledger.json#tr-claim-016) | History preparation is a bounded projection. | local observation only | [E-TR-016](source-audit.json#e-tr-016) |
| [TR-CLAIM-017](claim-ledger.json#tr-claim-017) | Failure classes have explicit non-success paths. | supported | [E-TR-017](source-audit.json#e-tr-017) |
| [TR-CLAIM-018](claim-ledger.json#tr-claim-018) | Tests distinguish cancellation timing states. | local observation only | [E-TR-018](source-audit.json#e-tr-018) |
| [TR-CLAIM-019](claim-ledger.json#tr-claim-019) | Dynamic responses match pending call IDs. | established | [E-TR-019](source-audit.json#e-tr-019) |
| [TR-CLAIM-020](claim-ledger.json#tr-claim-020) | Exposure is separate from registration/authority. | supported | [E-TR-020](source-audit.json#e-tr-020) |
