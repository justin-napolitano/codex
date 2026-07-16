# Tool-call and routing inventory

This page traces a model-proposed tool call through the Codex runtime. It is
an evidence-linked implementation map, not a promise that every tool follows
one identical path. The registry, policy layer, sandbox, and adapter each own
different authority; a model-visible tool description is not permission to
perform an effect.

The complete reviewed bundle is in the [tool-routing research pass](audit/tool-call-routing/README.md).
Use the [clickable claim ledger](audit/tool-call-routing/claim-ledger.md) and
[source/evidence index](audit/tool-call-routing/source-audit.md) to inspect
the proof behind each statement.

## Read the route

```text
model response item
      ↓ parse and validate
typed ToolCall (call_id, name, payload)
      ↓ ToolRouter
ToolInvocation (turn/session/cancellation/context)
      ↓ ToolRegistry lifecycle
hooks → policy/approval → sandbox → runtime adapter
      ↓
ToolResult / ResponseInputItem (same call_id)
      ↓
events + rollout persistence + normalized history
      ↓
next model request
```

The route can branch for parallel calls, cancellation, MCP/remote providers,
app-server approval requests, and terminal failures. The formal predicates in
[07-formal-operational-model](07-formal-operational-model.md) describe the
admission gates; this inventory identifies where those gates are implemented.

## Clickable call inventory

### TOOL-SPEC-001 — Build model-visible tool specifications

**Phase:** specification · **Kind:** context/router construction · **Model-visible:** yes

`build_tool_router` combines registered runtimes, dynamic tools, extensions,
and configuration into a router and a model-visible specification list. The
list is an exposure projection, not the complete registry.

[source](../../codex-rs/core/src/tools/spec_plan.rs#L1) · [claim TR-CLAIM-001](audit/tool-call-routing/claim-ledger.json#tr-claim-001) · [evidence E-TR-001](audit/tool-call-routing/source-audit.json#e-tr-001)

### TOOL-IN-002 — Parse a response item into a typed call

**Phase:** input · **Kind:** protocol decoding · **Model-visible:** indirect

`ToolRouter::build_tool_call` accepts function, custom, local-shell, web/tool
search, and extension-shaped response items, validates arguments, and preserves
the provider call identifier.

[source](../../codex-rs/core/src/tools/router.rs#L112) · [claim TR-CLAIM-002](audit/tool-call-routing/claim-ledger.json#tr-claim-002) · [evidence E-TR-002](audit/tool-call-routing/source-audit.json#e-tr-002)

### TOOL-ROUTE-003 — Construct the invocation context

**Phase:** routing · **Kind:** typed adapter · **Model-visible:** no

The router converts a `ToolCall` into `ToolInvocation`, carrying call ID,
turn/session context, payload, cancellation, and source metadata. This is the
boundary where a protocol item becomes an executable runtime request.

[source](../../codex-rs/core/src/tools/router.rs#L210) · [claim TR-CLAIM-003](audit/tool-call-routing/claim-ledger.json#tr-claim-003) · [evidence E-TR-003](audit/tool-call-routing/source-audit.json#e-tr-003)

### TOOL-REG-004 — Resolve the registered runtime

**Phase:** routing · **Kind:** registry dispatch · **Model-visible:** no

`ToolRegistry` maps a tool name to a runtime and rejects duplicate registration.
Lookup is based on registration; exposure flags determine what is advertised,
not whether the registry is authoritative.

[source](../../codex-rs/core/src/tools/registry.rs#L325) · [claim TR-CLAIM-004](audit/tool-call-routing/claim-ledger.json#tr-claim-004) · [evidence E-TR-004](audit/tool-call-routing/source-audit.json#e-tr-004)

### TOOL-HOOK-005 — Run pre-tool and post-tool hooks

**Phase:** lifecycle · **Kind:** hook boundary · **Model-visible:** result-dependent

The registry asks a runtime for hook payloads, allows approved argument
rewrites, then converts the runtime result into a post-tool payload and a
protocol response. Hooks observe and transform a call; they do not replace the
policy or sandbox gate.

[source](../../codex-rs/core/src/tools/registry.rs#L90) · [claim TR-CLAIM-005](audit/tool-call-routing/claim-ledger.json#tr-claim-005) · [evidence E-TR-005](audit/tool-call-routing/source-audit.json#e-tr-005)

### TOOL-POLICY-006 — Evaluate command and approval policy

**Phase:** authorization · **Kind:** policy decision · **Model-visible:** status/result

Exec policy evaluates command shape and configuration to produce an approval
requirement or rejection. The policy layer is distinct from the runtime that
will eventually spawn a process.

[source](../../codex-rs/core/src/exec_policy.rs#L269) · [claim TR-CLAIM-006](audit/tool-call-routing/claim-ledger.json#tr-claim-006) · [evidence E-TR-006](audit/tool-call-routing/source-audit.json#e-tr-006)

### TOOL-APPROVAL-007 — Request, cache, or deny approval

**Phase:** authorization · **Kind:** approval service · **Model-visible:** status/result

Approval keys and cached review decisions are handled by the shared approval
layer. A denial is a tool result/error path, not a successful runtime call.

[source](../../codex-rs/core/src/tools/sandboxing.rs#L65) · [claim TR-CLAIM-007](audit/tool-call-routing/claim-ledger.json#tr-claim-007) · [evidence E-TR-007](audit/tool-call-routing/source-audit.json#e-tr-007)

### TOOL-SANDBOX-008 — Select sandbox and escalation behavior

**Phase:** authorization · **Kind:** sandbox boundary · **Model-visible:** indirect

Sandbox permissions, denied-read constraints, network policy, and escalation
rules are assembled before a local effect. Escalation cannot silently discard
denied-read restrictions.

[source](../../codex-rs/core/src/tools/sandboxing.rs#L242) · [claim TR-CLAIM-008](audit/tool-call-routing/claim-ledger.json#tr-claim-008) · [evidence E-TR-008](audit/tool-call-routing/source-audit.json#e-tr-008)

### TOOL-PAR-009 — Admit parallel calls and cancellation

**Phase:** scheduling · **Kind:** concurrency gate · **Model-visible:** result-dependent

`ToolCallRuntime` serializes tools that do not support parallel execution and
uses cancellation tokens plus runtime-specific cleanup behavior. Cancellation
can occur before admission, during execution, or after completion.

[source](../../codex-rs/core/src/tools/parallel.rs#L94) · [claim TR-CLAIM-009](audit/tool-call-routing/claim-ledger.json#tr-claim-009) · [evidence E-TR-009](audit/tool-call-routing/source-audit.json#e-tr-009)

### TOOL-EXEC-010 — Execute unified shell/process work

**Phase:** execution · **Kind:** local/exec-server runtime · **Model-visible:** result

`UnifiedExecRuntime` turns a validated request into a sandboxed process or an
exec-server request, carries environment identity, and emits bounded output.

[source](../../codex-rs/core/src/tools/runtimes/unified_exec.rs#L258) · [claim TR-CLAIM-010](audit/tool-call-routing/claim-ledger.json#tr-claim-010) · [evidence E-TR-010](audit/tool-call-routing/source-audit.json#e-tr-010)

### TOOL-PATCH-011 — Route apply-patch through a file-change runtime

**Phase:** execution · **Kind:** patch runtime · **Model-visible:** result

The patch handler parses custom input, computes path permissions, applies file
changes, emits progress/diff events, and returns a call-correlated result.

[source](../../codex-rs/core/src/tools/handlers/apply_patch.rs#L329) · [claim TR-CLAIM-011](audit/tool-call-routing/claim-ledger.json#tr-claim-011) · [evidence E-TR-011](audit/tool-call-routing/source-audit.json#e-tr-011)

### TOOL-MCP-012 — Route namespaced MCP tools

**Phase:** execution · **Kind:** remote/provider adapter · **Model-visible:** yes

MCP handlers preserve a namespaced tool identity, parse function arguments,
call the configured provider, and convert provider content into a Codex tool
result. Parallel support depends on read-only/provider capabilities.

[source](../../codex-rs/core/src/tools/handlers/mcp.rs#L67) · [claim TR-CLAIM-012](audit/tool-call-routing/claim-ledger.json#tr-claim-012) · [evidence E-TR-012](audit/tool-call-routing/source-audit.json#e-tr-012)

### TOOL-REMOTE-013 — Serve app-server turn and approval requests

**Phase:** external interface · **Kind:** JSON-RPC boundary · **Model-visible:** client-visible

The app-server maps `turn/start`, steering, interruption, and approval-related
requests into session operations, while outbound notifications carry progress
and tool state back to the client.

[source](../../codex-rs/app-server/src/request_processors/turn_processor.rs#L462) · [claim TR-CLAIM-013](audit/tool-call-routing/claim-ledger.json#tr-claim-013) · [evidence E-TR-013](audit/tool-call-routing/source-audit.json#e-tr-013)

### TOOL-OUT-014 — Correlate and convert the result

**Phase:** completion · **Kind:** response conversion · **Model-visible:** yes

Registry completion preserves the original `call_id`, converts runtime output
into `ResponseInputItem`, and records success or failure telemetry. Correlation
is what lets the next model request match output to the proposed call.

[source](../../codex-rs/core/src/tools/registry.rs#L676) · [claim TR-CLAIM-014](audit/tool-call-routing/claim-ledger.json#tr-claim-014) · [evidence E-TR-014](audit/tool-call-routing/source-audit.json#e-tr-014)

### TOOL-PERSIST-015 — Persist events and reconstruct history

**Phase:** state · **Kind:** session/rollout persistence · **Model-visible:** derived

Session event emission can persist rollout items, while history reconstruction
prepares response items for a later turn. Durable records and model context are
related projections, not identical stores.

[source](../../codex-rs/core/src/session/mod.rs#L1967) · [claim TR-CLAIM-015](audit/tool-call-routing/claim-ledger.json#tr-claim-015) · [evidence E-TR-015](audit/tool-call-routing/source-audit.json#e-tr-015)

### TOOL-NORMAL-016 — Normalize malformed or incomplete tool history

**Phase:** recovery · **Kind:** context normalization · **Model-visible:** derived

History normalization repairs or filters incomplete call/output sequences before
they are projected into a model request. This is a recovery boundary, not proof
that every external provider emitted a valid pair.

[source](../../codex-rs/core/src/session/mod.rs#L2769) · [claim TR-CLAIM-016](audit/tool-call-routing/claim-ledger.json#tr-claim-016) · [evidence E-TR-016](audit/tool-call-routing/source-audit.json#e-tr-016)

### TOOL-FAIL-017 — Handle unknown, denied, malformed, and failed calls

**Phase:** failure · **Kind:** error path · **Model-visible:** error/result

Unsupported payloads, unknown tool names, policy denials, provider errors,
spawn errors, and cancellation are represented as failures or bounded tool
outputs rather than being treated as successful effects.

[source](../../codex-rs/core/src/tools/registry.rs#L753) · [claim TR-CLAIM-017](audit/tool-call-routing/claim-ledger.json#tr-claim-017) · [evidence E-TR-017](audit/tool-call-routing/source-audit.json#e-tr-017)

### TOOL-TRACE-018 — Record dispatch timing and telemetry

**Phase:** observability · **Kind:** trace/analytics · **Model-visible:** no

Dispatch traces and timing guards separate waiting, handler execution, abort,
and completion. Observability describes the route; it does not grant authority.

[source](../../codex-rs/core/src/tools/parallel.rs#L122) · [claim TR-CLAIM-018](audit/tool-call-routing/claim-ledger.json#tr-claim-018) · [evidence E-TR-018](audit/tool-call-routing/source-audit.json#e-tr-018)

### TOOL-DYN-019 — Resolve dynamic tool responses by call ID

**Phase:** external tools · **Kind:** asynchronous callback · **Model-visible:** result

Dynamic tools retain pending calls and match later responses by `call_id`; an
unknown response is reported instead of being attached to an arbitrary call.

[source](../../codex-rs/core/src/session/mod.rs#L2723) · [claim TR-CLAIM-019](audit/tool-call-routing/claim-ledger.json#tr-claim-019) · [evidence E-TR-019](audit/tool-call-routing/source-audit.json#e-tr-019)

### TOOL-BOUND-020 — Keep exposure, registration, and authority distinct

**Phase:** invariant · **Kind:** architectural boundary · **Model-visible:** yes/no by layer

The implementation supports a tool being registered, exposed, dispatched, and
authorized through separate mechanisms. The safe design rule is therefore to
audit each boundary independently rather than treating the model catalog as an
authority list.

[source](../../codex-rs/core/src/tools/registry.rs#L241) · [claim TR-CLAIM-020](audit/tool-call-routing/claim-ledger.json#tr-claim-020) · [evidence E-TR-020](audit/tool-call-routing/source-audit.json#e-tr-020)

## Review status

The machine-readable inventory and research-pass result are authoritative for
claim strength and open questions. If implementation changes, rerun the
`run-research-pass` audit at a new pinned commit rather than editing evidence
links silently.
