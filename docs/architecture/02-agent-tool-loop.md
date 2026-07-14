# The agent and tool loop

## The loop in one sentence

Codex repeatedly samples the model, turns any returned tool-call items into
typed local work, records and feeds tool results back to the model, and stops
only when the model produces a terminal response or the run is cancelled,
blocked, or fails.

See the executable interaction map:
[turn and tool loop diagram](diagrams/02-turn-tool-loop.mmd).

```text
user input
   │
   ▼
create turn + assemble policy-constrained context
   │
   ▼
stream model response ──► assistant text events ──► surface renders deltas
   │
   ├─ no tool calls ───────────────────────────────► complete turn
   │
   └─ tool calls
          │
          ▼
   parse + route + policy check + optional hooks/approval
          │
          ▼
   execute under sandbox/cancellation controls
          │
          ▼
   record selected result/lifecycle data + emit surface events
          │
          ▼
   append model-visible tool output ───────────────► next model sample
```

## 1. A surface submits an operation

The core-facing protocol is defined in `codex-rs/protocol/src/protocol.rs`.
The surface sends a `Submission` with an `Op`; common operations include a
user turn, an interrupt, an approval decision, or an answer to a structured
question. `Session::submit` in `core/src/session/mod.rs` puts that work into
the live engine.

The core emits `Event` values containing `EventMsg` variants. Surfaces should
render these incrementally, rather than wait for a final answer: there are
events for turn lifecycle, streamed assistant text, tool lifecycle, approvals,
warnings, errors, token use, and completion.

## 2. Codex prepares a turn

`core/src/session/turn.rs` is the most valuable file to follow. At a high
level, `run_turn`:

1. resolves turn settings—model, cwd, permissions, approval policy, selected
   apps/connectors, collaboration mode, and other per-turn overrides;
2. obtains project/user instruction files and enabled skills/plugins;
3. builds the initial context/history and records the user item;
4. compacts history if it would exceed the usable context window;
5. builds the model-visible tool specifications for this precise turn;
6. sends a streaming sampling request through the model provider client.

This means tool availability is contextual. A tool need not be permanently
available just because the binary supports it; it can be absent because of
permissions, selected capabilities, the active collaboration mode, config, or
tool-search policy.

## 3. The model streams response items

The model response is not just text. It is a stream of typed `ResponseItem`s,
including assistant messages, function calls, custom tool calls, search calls,
and their deltas. Codex emits text deltas to the surface while retaining a
consistent transcript for later context/persistence.

The execution boundary is deliberately typed. `ToolRouter::build_tool_call`
in `core/src/tools/router.rs` recognizes model response items and produces:

```text
ToolCall {
  tool_name,
  call_id,
  payload
}
```

The `call_id` is crucial. It correlates the model’s request, runtime status,
approval, execution result, UI events, and the function-call output returned
to the next model request.

Think of it as a distributed trace key for one requested side effect. It must
survive parsing, an approval pause, execution, persistence, event rendering,
and context reconstruction. A tool result without its matching call is not
safe context; `context_manager/normalize.rs` explicitly handles that failure
case.

## 4. Route and validate the tool call

The router builds a `ToolInvocation` containing more than raw arguments:

- the live `Session` and step/turn context;
- a cancellation token;
- a diff tracker for user-visible progress;
- the model call ID and tool name;
- the payload/source.

It passes that to `ToolRegistry` (`core/src/tools/registry.rs`). The registry
maps the tool name to a typed `CoreToolRuntime`, rejects unknown/invalid calls,
and surrounds execution with cross-cutting behavior:

- tool lifecycle events for the UI;
- optional pre-tool hooks, including controlled argument rewriting;
- telemetry and tool-read accounting;
- approval/policy handling owned by individual tool flows;
- post-tool hooks and feedback;
- consistent conversion to model-visible `ResponseInputItem` output.

`ToolExecutor` is the key abstraction: a handler implements invocation
behavior, while the tool builder decides which specifications are visible to
the model. Registration and model exposure are related but not identical: a
runtime can be registered even when its schema is hidden in a particular
mode. The registry therefore proves that a name has a handler; it does not by
itself prove that the current model was shown that name.

## 5. Permission is a runtime decision

See the decision states:
[approval and execution diagram](diagrams/03-approval-and-execution.mmd).

An LLM saying “run this command” is not authorization. For command-like work,
the runtime evaluates the configured approval policy and the command against
the execution policy (`core/src/exec_policy.rs`). A result can be:

- **allowed without a prompt**;
- **requires approval**;
- **forbidden**.

When approval is required, `Session::request_command_approval` or
`Session::request_patch_approval` emits an approval request event and awaits a
decision from the client. App-server clients receive equivalent JSON-RPC
server-to-client approval requests. The turn remains live but paused; it is
not completed optimistically.

For local command and patch execution, the sandbox is a second, independent
control. Even an approved command runs with the configured OS/filesystem and,
where supported, network constraints. Approval answers “may this action be
attempted?” Sandboxing limits “what can the attempted process reach?” Other
tool families, such as remote MCP or connector calls, have their own trust and
authorization boundaries and must not be assumed to share the local process
sandbox.

For example, a user may approve `npm test`, but that approval does not grant
the process write access outside the configured workspace or network access
when the active sandbox policy denies it. Conversely, an allowed sandbox does
not mean every command is automatically approved.

## 6. Execution, cancellation, and parallelism

Tools can be simple local computations, file edits, shell commands, MCP tool
calls, searches, or app/connector calls. Tool metadata indicates whether a
tool supports parallel calls and whether it must finish teardown after runtime
cancellation. `core/src/tools/orchestrator.rs` and `parallel.rs` coordinate
that behavior.

Every invocation carries a `CancellationToken`. Interrupting a turn should
stop future sampling and signal active tools. A tool may still need a bounded
cleanup phase; that is why cancellation is modeled as a protocol/state concern
rather than killing arbitrary processes from UI code.

## 7. Results re-enter the model loop

`ToolRegistry` turns a handler result into a function/custom-tool output with
the same `call_id`. The result is:

1. emitted to the surface as a tool/item lifecycle update;
2. persisted in the rollout/history;
3. normalized and truncated where necessary;
4. appended to the next model input.

The model is then sampled again with the tool result. It may request more
tools, revise its approach, ask the user a question, or finish with a message.
The runtime therefore owns the loop; a single model response is not assumed to
finish a user request.

## Why normalization matters

Interrupted or failed streams can leave an incomplete pair: a tool call with
no output, or an output with no call. `core/src/context_manager/normalize.rs`
repairs/rejects inconsistent history before it is used again. That prevents a
future model request from seeing a transcript that says “call tool X” but
never reveals its outcome.

For systems you build: record each requested side effect and a correlated
outcome, or explicitly document why a tool family is exempt. Make replay
robust to interruption. This is not bookkeeping—it is what makes resume,
debugging, and reliable continuation possible.

## A concrete mental trace

For a shell request, the high-level chain is:

```text
ResponseItem::FunctionCall
  -> ToolRouter::build_tool_call
  -> ToolInvocation { session, turn, call_id, cancellation_token, payload }
  -> ToolRegistry dispatch + hooks/lifecycle
  -> shell or unified-exec runtime
  -> policy / optional approval / sandboxed process
  -> FunctionCallOutput with the same call_id
  -> persisted history + next model sample
```

The exact tool implementation varies. The reusable contract is that the
runtime parses and observes a model request, applies the controls implemented
for that tool family, and returns a correlated outcome. Which authorization
and isolation controls apply must be verified at the concrete handler; it is
not guaranteed merely by going through the registry.
