# Trace one complete turn

This is the shortest path from “I know the architecture” to “I can navigate
the code.” Follow it with a search window open; the runtime is asynchronous,
so type names and events are more reliable anchors than linear call stacks.

## 1. A client gives Codex work

For the terminal surface, begin in `codex-rs/cli/src/main.rs`, then follow the
TUI into the core. For an IDE/desktop client, begin at app-server request
processors. Both paths ultimately submit an internal `Op` to a live Codex
session.

The internal types are in `codex-rs/protocol/src/protocol.rs`:

```text
Submission { id, op }
Op::UserTurn { ... }
Event { id, msg: EventMsg }
```

`Session::submit`, `Session::submit_with_id`, and `Session::next_event` in
`codex-rs/core/src/session/mod.rs` are the useful hand-off points. A surface
does not wait for one final string; it consumes events as the run progresses.

## 2. The session creates the turn’s working world

Find `run_turn` in `core/src/session/turn.rs`. It resolves the current turn’s
effective settings, collects instructions/capabilities, establishes context,
and builds model-visible tool specs. This is where a thread’s historical
context meets *current* realities such as cwd, permission profile, selected
apps, model, and enabled skills.

The turn is not only a prompt. It holds cancellation, event correlation,
settings, token accounting, and the mutable working state for repeated model
steps. The current turn is serialized within a live session so two loops do
not concurrently rewrite the same context/history.

## 3. Codex sends a size-governed model request

Still in `turn.rs`, follow `build_prompt`, `built_tools`, and
`run_sampling_request`. The request consists of retained history plus current
context fragments and selected tool schemas. The response is streamed as typed
items; text deltas can immediately become user-visible events while Codex
retains the complete response state needed for tools and persistence.

If old history is too large, compaction can run before or during turn work.
Read `core/src/compact.rs` next. Compaction changes the *model context
projection* by introducing a summary and a new context window. Rollout records
remain the reconstruction source, but whether they constitute a complete
product audit trail is a separate retention and redaction policy question.

## 4. A model tool call becomes a local invocation

When a streamed item is a function/custom tool call, start in
`core/src/tools/router.rs`:

```text
ResponseItem
  -> ToolRouter::build_tool_call
  -> ToolCall { tool_name, call_id, payload }
  -> ToolInvocation
```

`ToolInvocation` adds runtime authority and observability to model arguments:
the live session, current step/turn context, a cancellation token, diff
tracking, source, and `call_id`. The call ID is retained all the way to the
returned function-call output.

## 5. The registry owns the tool lifecycle

Follow `dispatch_tool_call_with_terminal_outcome` into
`core/src/tools/registry.rs`. The registry finds a typed tool runtime and wraps
its execution with lifecycle events, hooks, telemetry, cancellation behavior,
and consistent model-visible output conversion.

The concrete local runtimes live under `core/src/tools/runtimes/`:

- `shell.rs` and `unified_exec.rs` handle command execution;
- `apply_patch.rs` handles file edits;
- MCP, skills, apps, and other capabilities enter through their corresponding
  tool/runtime adapters.

This is the point to inspect when adding a tool. Do not start by adding a
function schema to the model request; first decide the runtime handler,
capability exposure, policy, event shape, and durable result shape.

## 6. Side effects pass two controls

Concrete shell and patch runtimes can request approval through
`Session::request_command_approval` or `Session::request_patch_approval`.
`core/src/exec_policy.rs` determines whether a command is automatically
allowed, requires approval, or is forbidden. The sandbox then constrains the
approved process according to the filesystem/network policy.

The useful distinction is:

```text
Policy/approval: should the runtime attempt this operation?
Sandbox: once attempted, what resources can its process access?
```

Both must be correct for local shell/patch work. Remote tools and connectors
need equivalent explicit controls at their own process, credential, and
service boundaries; they are not automatically covered by Codex’s local OS
sandbox. A prompt or a UI warning cannot replace enforceable controls.

## 7. Results become events, history, and next-step input

The tool registry converts a handler result to a `ResponseInputItem` tied to
the original `call_id`. Session helpers record the response item, emit
turn-item events, and persist rollout data. The next model sample receives the
result as tool output. If there are more tool calls, the loop repeats; a final
assistant response ends the turn.

Read `core/src/context_manager/normalize.rs` after this. It explains why
interrupted calls cannot be left dangling: a resumed model must never be asked
to infer whether a recorded side effect completed.

## 8. A later resume rebuilds a new live session

`core/src/thread_manager.rs` coordinates start/resume/fork behavior.
`thread-store` reads the recorded thread representation; rollout reconstruction
turns it into initial history and the new session rebuilds a size-governed
current context. A resume recreates the runtime state needed for the *next* turn; it
does not revive an old process or blindly reuse stale in-memory permissions.

For the external form of that flow, read `app-server/README.md` alongside
`app-server/src/request_processors/thread_processor.rs` and
`turn_processor.rs`.

## What to trace next

| If you want to understand… | Read next |
| --- | --- |
| Why a command asked for approval | `core/src/exec_policy.rs` and `tools/approvals.rs` |
| Why a tool is absent from a request | `core/src/tools/spec_plan.rs` and `session/turn.rs` |
| How a client receives progress | `protocol.rs`, app-server event mapping, and TUI event handling |
| How context fits the model window | `context_manager/`, `compact.rs`, and `rollout_budget.rs` |
| How external tools are added | `codex-mcp`, `mcp-server`, `skills`, and `core/src/mcp*.rs` |

## The four boundaries people most often confuse

### 1. Session versus thread manager

`Session` is the live operating context for a loaded thread. It has async
channels, active cancellation state, an event sender, current settings, an
in-memory context manager, and services needed to run now. It is the thing a
tool invocation receives because tools need to ask for approval, emit
progress, inspect the effective permissions, and observe cancellation.

`ThreadManager` is one layer above that. It decides whether a request should
create a fresh session, locate an already-loaded one, reconstruct a cold thread
from its persisted history, or create a fork. It also avoids treating two live
sessions as the mutation owner for one thread. Read `thread_manager.rs` when
the question is “which conversation should be alive?” Read `session/mod.rs`
when the question is “how does this active conversation do work?”

This separation is a reusable pattern. A database row or JSONL transcript is
not an actor. It cannot own cancellation, long-lived connections, or an
approval waiter. Conversely, a process-local actor is not durable state. A
production agent system needs both and needs an explicit lifecycle joining
them.

### 2. Model-visible tools versus executable tools

The model is given a list of `ToolSpec` values for the current turn. A spec is
an interface description: name, schema, description, and exposure behavior.
It tells the model what it may ask for. It is not permission to execute a
command, and it is not the handler implementation.

At runtime, `ToolRouter` interprets a streamed response item and `ToolRegistry`
finds the registered `CoreToolRuntime`. The registry can still reject a call,
and the runtime can still request approval or fail under sandbox constraints.
That gives Codex two intentionally separate checks:

```text
Can the model discover/request this capability?  -> tool exposure/spec plan
Can this invocation perform its side effect now? -> handler policy + approval + sandbox
```

Do not merge those checks when building your own tool system. The first is
about prompt surface and user experience; the second is about authority.
Keeping them separate makes it possible to expose a tool only in certain
modes, restrict it to an approved root, or ask for confirmation per call.

### 3. Events versus durable records

An `EventMsg` tells a currently connected client what changed: text arrived,
a tool started, an approval is needed, a turn completed, or an error occurred.
Events are optimized for liveness and rendering. They may be deltas, they may
be received by multiple subscribers, and their usefulness is immediate.

Rollout/thread records are optimized for recovery and history. The
implementation uses ordered, append-oriented records, repairs interrupted
tails, and derives bounded model context from them. They help a fresh process
answer “what was recorded for this thread?”—which is narrower than proving
that every external side effect was captured. The same underlying action often
has both an event representation and a durable item representation, but
neither should be naively reconstructed from the other by parsing terminal
text.

When debugging, use the event flow to learn why a UI looked wrong *during* a
run. Use rollout/history and context normalization to learn why a resumed
agent remembered or omitted something *after* a run.

### 4. App-server versus core

App-server is an adapter and connection manager; it is not a second agent
implementation. It validates a JSON-RPC session, translates versioned
requests into core operations, manages client subscriptions, maps core events
to app-server notifications, and sends server-to-client approval requests.

That is why the app-server source has request processors for `initialize`,
threads, turns, config, MCP, and other client-facing concerns, while the core
source has the model loop, context, tools, policies, and persistence behavior.
If a behavior must be identical in TUI and IDE usage, it probably belongs in
core. If it is about JSON wire compatibility, connection state, or generated
client schema, it belongs in app-server/protocol.

## Follow the data, not just the functions

For an asynchronous agent, the most informative question is often “what data
changes shape here?” These are the important transformations to identify in
the debugger or code:

| From | To | Why it changes |
| --- | --- | --- |
| `Op::UserTurn` | turn/session work | The client’s request becomes owned async work. |
| retained history + context fragments | model request | Selected conversation state is projected into a prompt governed by current size policy. |
| streamed `ResponseItem` | surface delta or `ToolCall` | Text is rendered; executable items are routed. |
| `ToolCall` | `ToolInvocation` | Runtime state, cancellation, and correlation are attached to raw arguments. |
| handler result | function/custom-tool output | A local side effect becomes a model-readable result. |
| selected events/response items | rollout records | Runtime activity becomes recorded recovery evidence according to persistence policy. |
| rollout/store history | initial history + live session | A cold thread becomes a new executable actor. |

The model request boundary deserves special caution. The model does not receive
arbitrary Rust objects or access to the local filesystem. It receives a
serialized, curated representation: instructions, selected tool schemas,
retained conversation items, and tool outputs that Codex has chosen to expose.
That representation is a security, privacy, cost, and correctness boundary.

## Trace a failure without guessing

Use this order when a run behaves unexpectedly:

1. **Did the client submit the expected operation?** Inspect the input and the
   assigned submission/turn identifiers. If app-server is involved, first
   verify `initialize` and the versioned request shape.
2. **Was the turn constructed with the expected effective settings?** Check
   cwd, model, collaboration mode, permission profile, approval policy, and
   selected capabilities before blaming the model.
3. **Did the model receive the tool or instruction you expected?** Inspect
   `built_tools` and the constructed prompt/context rather than assuming a
   registered tool was visible.
4. **Did the model actually emit a tool call?** Differentiate a missing model
   call from a malformed/unrecognized call in `ToolRouter::build_tool_call`.
5. **Did policy block, pause, or permit it?** A pending approval is a healthy
   intermediate state, not a failed dispatch.
6. **Did the execution host run it in the expected sandbox?** Check both the
   command’s environment and filesystem/network grant—not merely process exit
   status.
7. **Was a correlated output persisted and returned to the model?** Follow the
   `call_id`; this detects lost results and incomplete histories.
8. **Did compaction or resume change later context?** Inspect normalized/
   compacted context separately from the raw durable rollout.

This order narrows a failure at the correct boundary. It avoids vague fixes
such as adding more prompt wording when the actual problem is tool exposure,
approval handling, a sandbox policy, or a malformed resumed transcript.

## How a second surface should integrate

If you build another UI, resist the urge to call core internals directly. Use
app-server v2 and implement the complete interaction contract:

- send `initialize`, then `initialized`, before thread work;
- create/resume a thread and retain its stable identifier;
- start a turn and subscribe to item/turn notifications;
- render streaming text and tool lifecycle as events rather than polling a
  final result;
- handle server-initiated approval requests and return a decision;
- handle interruption/retry and resume historical threads deliberately;
- treat experimental methods/fields as conditional capabilities, not permanent
  dependencies.

That makes the UI a replaceable surface. It can be a terminal, an IDE, a
desktop application, or an automated controller without changing the core
agent’s authority model.

## Advanced paths are extensions of the same loop

Once the ordinary turn is clear, the larger repository becomes less
intimidating. Most advanced capabilities add a new contributor, executor, or
transport around the same routing/result loop. Each one must still answer
where state, authorization, isolation, cancellation, and result correlation
are actually enforced.

### MCP, apps, plugins, and skills

Skills and plugins primarily influence what the model knows and what tools it
can discover for a turn. MCP servers and connected apps can add capabilities
that are executed outside the local binary. In each case, ask four questions:

1. **Discovery:** How is the capability found and selected for this turn?
2. **Exposure:** What tool spec or instruction is inserted into model context?
3. **Invocation:** Which handler/connection receives the model’s call?
4. **Control:** What approval, credential, error, output-size, and persistence
   rules apply before the result returns to the model?

The extension answer may differ by feature, but the shape is intentionally
recognizable. An MCP call is still an observed tool call with a correlation
ID, lifecycle events, a result/error, and a model-visible output. It should
not become an invisible side channel that bypasses history or the user’s
understanding of what happened.

### Multi-agent work

Multi-agent features add child sessions/threads and communication between
them. They do not mean that one session should run arbitrary competing turns
against one mutable context. Parent/child relationships, task delivery, result
delivery, and child completion must be represented explicitly so the parent
can incorporate the child’s final output into its next decision.

When studying this area, start with `core/src/session/multi_agents.rs`,
`core/src/codex_delegate.rs`, and the relevant tool handlers. First establish
which agent owns the user-facing thread, which data is passed to children, and
whether child side effects share the parent’s policy/environment. Treat
parallelism as an orchestration problem with state and cancellation semantics,
not simply “launch several prompts.”

### Remote execution

`exec-server` exists because a client surface, agent core, and execution
environment need not live on the same OS or host. This matters when the editor
is local but the repository is in a container, a remote development machine,
or a controlled build runner. The same authority questions apply, but the
transport must carry the execution request, result, cancellation, and
sandbox-related metadata across the boundary.

For a new remote-execution design, make the execution host a narrow service:
it should receive a validated request plus an already-resolved permission
profile, enforce the sandbox locally, stream bounded output, and return a
typed result. Do not give a remote executor a copy of the whole UI protocol or
let it independently reinterpret user approvals. That would create two
competing policy engines.

### Memory and compaction

Memories, summaries, and compacted history all answer a context-budget
problem, but they are not interchangeable. Rollout history records selected
reconstruction facts. Compaction makes a concise representation of earlier
history for the next model window. Memory is a separately selected/retrieved source of
potentially useful information. Each needs provenance, size limits, and clear
rules for when it becomes model-visible.

The general lesson is simple: every new source of model context should be
treated like an input API. Define its format, maximum size, selection rule,
provenance, and failure behavior. Otherwise an apparently harmless feature
eventually becomes an unbounded, stale, or privacy-sensitive prompt injection
path.
