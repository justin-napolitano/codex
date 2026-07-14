# Building an agent runtime like this

## Start with the right boundary

The common mistake is to build “a chatbot that can execute shell commands.”
That collapses planning, authority, execution, storage, and UI into one loop.
It works in a demo and becomes unsafe and unmaintainable as soon as you add
parallel actions, user approvals, retries, resume, or another client.

Instead, build a **runtime** around a model:

```text
model = proposes intent
runtime = validates, authorizes, executes, records, and resumes intent
client = renders state and obtains user decisions
```

The model should never be the source of truth for tool status, permissions,
or persistence.

The Codex diagrams are useful design review prompts, not just illustrations:
[component ownership](diagrams/01-system-components.mmd),
[tool lifecycle](diagrams/02-turn-tool-loop.mmd), and
[durable-state projection](diagrams/06-context-projection-and-compaction.mmd).
For the state-transition and authorization logic behind those diagrams, read
the [formal operational model](07-formal-operational-model.md).

## Minimum viable architecture

You can build a useful first version with six modules:

1. **Thread store** — durable thread/turn/item records.
2. **Context builder** — a bounded projection from history + current state to
   model input.
3. **Model adapter** — streams typed assistant messages and tool calls.
4. **Tool registry** — maps a tool name plus JSON arguments to a typed handler
   and JSON schema/specification.
5. **Policy/approval layer** — decides allow, ask, or deny before side effects.
6. **Event stream** — emits lifecycle updates to the UI and persistence layer.

Keep these interfaces narrow. A tool handler should receive an invocation
context, validated arguments, cancellation, and a capability/policy grant. It
should not receive unrestricted global process access just because it is a
plugin.

## A staged build plan

### Stage 1: one deterministic turn

Implement one thread, one user message, one model request, and one final text
response. Persist both user and assistant items. Do this before tools.

### Stage 2: typed tool calls

Provide model-visible JSON schemas. Parse tool calls into a structure such as:

```text
ToolCall { call_id, name, arguments }
```

Add a registry that returns either a result or a structured error. Persist the
call and result as a pair. Feed the result back to the model for another
sample. Start with read-only tools such as repository search/status.

### Stage 3: event stream and cancellation

Expose `turnStarted`, message deltas, tool started/completed, and
`turnCompleted` events. Add cancellation tokens/timeouts before you introduce
long-running shell processes. This prevents the UI from becoming a guessing
game.

### Stage 4: policy and sandboxing

Classify side effects: read, write, execute, network, credential use. For each
tool call, make one of three explicit decisions: allow, require approval, or
deny. Run shell/file work in a least-privilege environment with specific
readable/writable roots and network policy.

Do not substitute a prompt instruction such as “do not delete files” for this
layer. Prompts influence behavior; they do not enforce it.

### Stage 5: resumability and compaction

Persist incremental records; reconstruct state after a restart; normalize
incomplete tool calls; compact old model context while retaining whatever
recovery/audit record your product policy requires. At this stage you have an
agent runtime rather than an interactive script.

### Stage 6: multiple surfaces and extensions

Add a stable RPC interface for an editor/desktop UI and an extension system
for third-party tools. Keep the internal engine protocol distinct from the
public API. Add quotas, observability, versioned schemas, and compatibility
tests before promising external stability.

## Recommended design invariants

These are targets for a system you build. They summarize lessons from Codex,
but the exact enforcement point must be designed and tested for every tool
family; they are not all repository-wide theorems about every extension.

| Invariant | Why it matters |
| --- | --- |
| Tool calls and outputs have a shared call ID. | You can correlate, retry, render, audit, and safely replay side effects. |
| Every model request obeys an explicit size policy or fails before sampling. | Prevents unbounded cost/latency and protects future turns from oversized tool output. |
| Every side-effecting tool has a named authorization and isolation boundary. | Makes local sandboxing, remote credentials, and user approval reviewable instead of assuming one mechanism fits every tool. |
| A thread’s mutable conversation state has one model-loop owner. | Avoids race conditions and contradictory history while allowing controlled internal parallelism. |
| Cancellation is cooperative and represented in state. | Makes interruption safe and resumable. |
| Durable history is separate from prompt context. | You keep auditability without stuffing everything into the next request. |
| UI consumes events, not terminal text parsing. | Enables different clients and reliable progress/approval UX. |
| External protocols are versioned. | Lets IDEs/plugins evolve without binding them to private internals. |

## Failure modes to design for early

- The model emits malformed tool arguments.
- The model requests a tool that is not enabled for this turn.
- The user denies approval after the tool is already displayed as pending.
- A process hangs, emits huge output, or ignores cancellation.
- The application restarts between a tool call and its result.
- Two tools request incompatible changes to the same file.
- A tool result contains secrets or too much raw data to return to the model.
- A resumed thread has a call without a corresponding result.
- A client disconnects while the agent run continues.

Codex contains separate modules for many of these because they are distinct
engineering problems, not edge cases to patch into a completion loop.

## How to study this repository productively

Trace one complete path rather than reading every crate:

1. `codex-rs/cli/src/main.rs` — locate a chosen surface command.
2. `codex-rs/core/src/session/mod.rs` — find session spawn, submit, and event
   handling.
3. `codex-rs/core/src/session/turn.rs` — follow `run_turn` and model sampling.
4. `codex-rs/core/src/tools/router.rs` — see model item → `ToolCall`.
5. `codex-rs/core/src/tools/registry.rs` — see invocation lifecycle.
6. `codex-rs/core/src/exec_policy.rs` and sandbox crates — see authorization
   and enforcement.
7. `codex-rs/core/src/thread_manager.rs` plus `thread-store`/`rollout` — see
   how the system survives after the live session ends.

When you can explain that path in your own words, you have the foundation to
build a credible tool-using agent. Then explore MCP, skills, plugins,
multi-agent behavior, remote execution, and advanced memory as extensions—not
as the starting point.
