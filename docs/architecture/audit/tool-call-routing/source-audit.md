# Clickable source and evidence index

The JSON source audit records exact inspected locations and limitations. The
implementation anchors below are the primary evidence paths for the inventory.

| Evidence | Source anchor |
| --- | --- |
| [E-TR-001](source-audit.json#e-tr-001) | [tool specification planning](../../../../codex-rs/core/src/tools/spec_plan.rs#L1) |
| [E-TR-002](source-audit.json#e-tr-002) | [router parsing](../../../../codex-rs/core/src/tools/router.rs#L112) |
| [E-TR-003](source-audit.json#e-tr-003) | [invocation construction](../../../../codex-rs/core/src/tools/router.rs#L210) |
| [E-TR-004](source-audit.json#e-tr-004) | [registry](../../../../codex-rs/core/src/tools/registry.rs#L325) |
| [E-TR-005](source-audit.json#e-tr-005) | [registry hooks](../../../../codex-rs/core/src/tools/registry.rs#L90) |
| [E-TR-006](source-audit.json#e-tr-006) | [exec policy](../../../../codex-rs/core/src/exec_policy.rs#L269) |
| [E-TR-007](source-audit.json#e-tr-007) | [approval store](../../../../codex-rs/core/src/tools/sandboxing.rs#L65) |
| [E-TR-008](source-audit.json#e-tr-008) | [sandbox override](../../../../codex-rs/core/src/tools/sandboxing.rs#L242) |
| [E-TR-009](source-audit.json#e-tr-009) | [parallel runtime](../../../../codex-rs/core/src/tools/parallel.rs#L94) |
| [E-TR-010](source-audit.json#e-tr-010) | [unified execution](../../../../codex-rs/core/src/tools/runtimes/unified_exec.rs#L258) |
| [E-TR-011](source-audit.json#e-tr-011) | [apply patch](../../../../codex-rs/core/src/tools/handlers/apply_patch.rs#L329) |
| [E-TR-012](source-audit.json#e-tr-012) | [MCP handler](../../../../codex-rs/core/src/tools/handlers/mcp.rs#L67) |
| [E-TR-013](source-audit.json#e-tr-013) | [app-server turn processor](../../../../codex-rs/app-server/src/request_processors/turn_processor.rs#L462) |
| [E-TR-014](source-audit.json#e-tr-014) | [registry completion](../../../../codex-rs/core/src/tools/registry.rs#L676) |
| [E-TR-015](source-audit.json#e-tr-015) | [session persistence](../../../../codex-rs/core/src/session/mod.rs#L1967) |
| [E-TR-016](source-audit.json#e-tr-016) | [history preparation](../../../../codex-rs/core/src/session/mod.rs#L2769) |
| [E-TR-017](source-audit.json#e-tr-017) | [failure handling](../../../../codex-rs/core/src/tools/registry.rs#L753) |
| [E-TR-018](source-audit.json#e-tr-018) | [cancellation tests](../../../../codex-rs/core/src/tools/parallel.rs#L408) |
| [E-TR-019](source-audit.json#e-tr-019) | [dynamic response matching](../../../../codex-rs/core/src/session/mod.rs#L2723) |
| [E-TR-020](source-audit.json#e-tr-020) | [exposure override](../../../../codex-rs/core/src/tools/registry.rs#L241) |
