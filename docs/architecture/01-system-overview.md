# System overview

## What Codex is made of

See the reusable component map:
[system components diagram](diagrams/01-system-components.mmd).

The repository is a Rust workspace. The principal executable is the
`codex-cli` crate, but the CLI is a surface over a reusable agent runtime.
The core engine is deliberately usable by more than one surface.

```text
                         ┌──────────────────────────┐
                         │         User/client      │
                         │ TUI · IDE · desktop · MCP│
                         └────────────┬─────────────┘
                                      │ input / events / approvals
                 ┌────────────────────▼────────────────────┐
                 │          Codex surface adapter           │
                 │ CLI/TUI or app-server JSON-RPC/MCP       │
                 └────────────────────┬────────────────────┘
                                      │ Op / Event
                 ┌────────────────────▼────────────────────┐
                 │              codex-core                  │
                 │ Session · turn · context · task lifecycle│
                 └───────┬──────────────────┬──────────────┘
                         │                  │
              model request/stream          │ typed tool invocation
                         │                  │
             ┌───────────▼───────┐  ┌──────▼─────────────────────────┐
             │ Responses/model   │  │ Tool runtime                    │
             │ provider/client   │  │ shell · patch · MCP · web · apps│
             └───────────────────┘  └──────┬─────────────────────────┘
                                             │ policy + OS sandbox
                                      ┌──────▼──────┐
                                      │ Local system│
                                      │ files/processes/network │
                                      └─────────────┘
```

There are two important separations here.

1. **Planning versus authority.** The model can ask for an action, but it
   cannot execute it itself. The runtime checks the policy, may request user
   approval, runs the action in a constrained environment, and decides what
   result goes back to the model.
2. **Live state versus durable history.** A `Session` owns active async work,
   cancellation, configuration, queues, and subscriptions. A `Thread` and its
   rollout/store representation survive the process and can later be resumed.

## Main crates and their jobs

| Area | Primary code | Responsibility |
| --- | --- | --- |
| Command entry | `codex-rs/cli` | Parses commands; starts TUI, app-server, MCP server, login, config, and helpers. |
| Terminal surface | `codex-rs/tui` | Renders state/events and converts user interaction to core operations. |
| Agent engine | `codex-rs/core` | Creates sessions, builds context, calls the model, manages turns, dispatches tools, enforces policy, and emits events. |
| Shared internal protocol | `codex-rs/protocol` | Defines core submissions (`Op`) and events (`EventMsg`). |
| App/IDE server | `codex-rs/app-server` | Exposes Codex through local JSON-RPC and maps its RPCs to core sessions. |
| App-server schema | `codex-rs/app-server-protocol` | Owns typed v1/v2 wire contracts and generated schemas. |
| Persistence | `codex-rs/rollout`, `thread-store`, `state` | Stores/reconstructs conversation history and thread metadata. |
| Tool abstractions | `codex-rs/tools`, `core/src/tools` | Defines tool specs/executors and the core’s dispatch/policy lifecycle. |
| Sandboxing/execution | `exec`, `exec-server`, `sandboxing`, `linux-sandbox`, platform crates | Runs commands in a constrained local or remote environment. |
| Extensibility | `skills`, `plugin`, `codex-mcp`, `ext/*` | Skills, plugins, MCP servers/tools, web search, memories, and other optional capabilities. |

## The real center of gravity: `codex-core`

`codex-core` is the business logic layer. It accepts a typed operation from a
surface, owns the live session, and emits typed events back. It is intentionally
not coupled to terminal rendering or to a particular editor.

The major control path begins around:

- `core/src/session/mod.rs` — spawning a live `Codex` session, accepting
  `submit` operations, producing `next_event`, coordinating approvals,
  persistence, cancellation, and context updates.
- `core/src/session/turn.rs` — preparing a turn and running model sampling.
- `core/src/tasks/regular.rs` and `core/src/tasks/lifecycle.rs` — turn/task
  lifecycle orchestration and start/finish events.
- `core/src/tools/` — converting streamed model tool-call items into execution.

Do not read `core` as one linear file. Start with those seams, then follow
types inward. The code is asynchronous and uses queues/cancellation tokens;
the control flow is clearer when viewed as messages and state transitions.

## Context is assembled, not improvised

Before asking the model for anything, Codex builds a policy-constrained context from
several sources:

- the retained conversation history;
- the current user input and optional images;
- system/developer/user instructions;
- applicable `AGENTS.md` instructions;
- environment facts such as cwd, platform, readable/writable roots, and git
  state;
- enabled skills, plugins, apps, MCP tools, and their instructions;
- current configuration, collaboration mode, and permission policy;
- summaries/compaction output when full raw history no longer fits.

`core/src/context/` contains structured fragments injected into the model
context. `core/src/context_manager/` owns history normalization and size
control. This is a serious architectural choice: model context is treated as a
structured, size-governed input to the state machine, not an unlimited
transcript. Compaction or truncation can still fail visibly when input cannot
be made usable.

## Ownership is the safety model

The fastest way to understand the system is to ask who owns a decision:

| Decision or data | Owner | The model’s role |
| --- | --- | --- |
| What work to attempt | Model response | Proposes text or a tool call. |
| Whether a capability is exposed | Turn/context construction | Sees only the selected tool schemas. |
| Whether an action is allowed | Runtime policy and user approval | Cannot self-authorize. |
| What the action can reach | OS sandbox and execution host | Cannot widen filesystem/network access. |
| What happened | Session, rollout, and thread store | Receives a policy-sized result on a later sample, or a visible size/error outcome. |
| What the user sees | TUI/app-server client events | Produces deltas and lifecycle updates. |

This is why Codex has many crates. A chat UI, an LLM client, and shell
execution are intentionally not collapsed into one component with ambient
authority.
