# Runtime coverage inventory

This inventory maps implementation entry points to the formal operational
model. It is a coverage report, not a claim that the model is complete. The
machine-readable source is
[`runtime-coverage-inventory.json`](runtime-coverage-inventory.json).

The second-pass review found the core submission, routing, policy, approval,
event, persistence, and remote-tool paths represented. Resume, compaction,
fork, cancellation edge cases, retries, and platform-specific adapters remain
only partially modeled or explicitly unmodeled. These are the next formal-model
improvement targets described in the
[formal model limitations section](../07-formal-operational-model.md#known-limitations-and-next-improvement).

| Status | Meaning |
| --- | --- |
| `covered` | A code entry point maps directly to a declared model transition. |
| `partially_covered` | The path is represented, but one or more branches/effects need deeper tracing. |
| `unmodeled` | The implementation path was found but has no complete model transition yet. |

Every entry records an uncertainty class. `observed` means the cited code was
inspected; `inferred` means the model derives a behavior across multiple paths;
`unverified` means the path needs another evidence pass.
