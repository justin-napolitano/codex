# Clickable claim ledger

This is the human-readable companion to
[`claim-ledger.json`](claim-ledger.json). Every claim has a strength, decision,
and a link to its evidence.

| Claim | Strength | Decision | Evidence |
| --- | --- | --- | --- |
| [SK-CLAIM-001](#sk-claim-001) | established | accepted | [E-SK-001](source-audit.md#e-sk-001) |
| [SK-CLAIM-002](#sk-claim-002) | supported | accepted | [E-SK-002](source-audit.md#e-sk-002) |
| [SK-CLAIM-003](#sk-claim-003) | supported | accepted | [E-SK-003](source-audit.md#e-sk-003) |
| [SK-CLAIM-004](#sk-claim-004) | supported | accepted | [E-SK-004](source-audit.md#e-sk-004) |
| [SK-CLAIM-005](#sk-claim-005) | supported | accepted | [E-SK-005](source-audit.md#e-sk-005) |
| [SK-CLAIM-006](#sk-claim-006) | supported | accepted | [E-SK-006](source-audit.md#e-sk-006) |
| [SK-CLAIM-007](#sk-claim-007) | supported | accepted | [E-SK-007](source-audit.md#e-sk-007) |
| [SK-CLAIM-008](#sk-claim-008) | supported | accepted | [E-SK-008](source-audit.md#e-sk-008) |
| [SK-CLAIM-009](#sk-claim-009) | established | accepted | [E-SK-009](source-audit.md#e-sk-009) |
| [SK-CLAIM-010](#sk-claim-010) | established | accepted | [E-SK-010](source-audit.md#e-sk-010) |
| [SK-CLAIM-011](#sk-claim-011) | supported | accepted | [E-SK-011](source-audit.md#e-sk-011) |
| [SK-CLAIM-012](#sk-claim-012) | established | accepted | [E-SK-012](source-audit.md#e-sk-012) |
| [SK-CLAIM-013](#sk-claim-013) | supported | accepted | [E-SK-013](source-audit.md#e-sk-013) |
| [SK-CLAIM-014](#sk-claim-014) | established | accepted | [E-SK-014](source-audit.md#e-sk-014) |
| [SK-CLAIM-015](#sk-claim-015) | established | accepted | [E-SK-015](source-audit.md#e-sk-015) |
| [SK-CLAIM-016](#sk-claim-016) | supported | accepted | [E-SK-016](source-audit.md#e-sk-016) |
| [SK-CLAIM-017](#sk-claim-017) | supported | accepted | [E-SK-017](source-audit.md#e-sk-017) |
| [SK-CLAIM-018](#sk-claim-018) | supported | accepted | [E-SK-018](source-audit.md#e-sk-018) |
| [SK-CLAIM-019](#sk-claim-019) | supported | weakened | [E-SK-019](source-audit.md#e-sk-019) |
| [SK-CLAIM-020](#sk-claim-020) | supported | accepted | [E-SK-020](source-audit.md#e-sk-020) |

### SK-CLAIM-001

Skill discovery resolves configured roots before metadata loading. See
[E-SK-001](source-audit.md#e-sk-001).

### SK-CLAIM-002

Skill snapshots are reusable metadata/error projections keyed by relevant cwd
or configuration. See [E-SK-002](source-audit.md#e-sk-002).

### SK-CLAIM-003

Discovery validates metadata; body injection is a later read path. See
[E-SK-003](source-audit.md#e-sk-003).

### SK-CLAIM-004

The app-server watcher invalidates skill snapshots after relevant changes. See
[E-SK-004](source-audit.md#e-sk-004).

### SK-CLAIM-005 through SK-CLAIM-020

The remaining atomic wording, limitations, evidence points, and review
decisions are in the linked [machine-readable ledger](claim-ledger.json), with
clickable evidence in the [source index](source-audit.md).
