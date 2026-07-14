# Codex architecture guide

This folder is a high-level, source-grounded guide to how the local Codex
agent works. It is written for someone who wants to understand or build an
agentic developer tool—not merely use the CLI.

Codex is not the model. It is a local, stateful runtime that turns model
output into safely mediated actions: it builds context, streams a model
request, executes tools, records the results, and continues until the turn
reaches a terminal state.

## Read in this order

1. [System overview](01-system-overview.md) — components and ownership.
2. [The agent and tool loop](02-agent-tool-loop.md) — the execution cycle in
   detail.
3. [Threads, turns, items, and persistence](03-threads-turns-persistence.md)
   — the conversation and durable-state model.
4. [Interfaces and process boundaries](04-interfaces-and-protocols.md) — how
   the TUI, IDEs, app-server, MCP, and execution hosts communicate.
5. [Building a tool like this](05-building-an-agent-runtime.md) — reusable
   design lessons, a staged implementation plan, and common traps.
6. [Trace one complete turn](06-trace-a-turn.md) — follow the real source
   path from client request to persisted result.
7. [Formal operational model](07-formal-operational-model.md) — a
   symbol-by-symbol state-machine model of the tooling runtime.

## Diagrams

The diagrams are standalone Mermaid source (`.mmd`) so they can be opened in
a Mermaid-capable editor or reused in design discussions. The Markdown guides
link to the relevant source beside the explanation.

| Diagram | Explains |
| --- | --- |
| [System components](diagrams/01-system-components.mmd) | Which process owns planning, authority, state, and side effects. |
| [Turn and tool loop](diagrams/02-turn-tool-loop.mmd) | One user turn from input through repeated model/tool steps. |
| [Approval and execution](diagrams/03-approval-and-execution.mmd) | Why policy, user approval, and sandboxing are separate gates. |
| [Thread lifecycle and resume](diagrams/04-thread-lifecycle-and-resume.mmd) | Live sessions versus durable thread history, resume, and fork. |
| [App-server RPC flow](diagrams/05-app-server-rpc-flow.mmd) | A rich client’s JSON-RPC handshake, streaming, and approval round-trip. |
| [Context projection and compaction](diagrams/06-context-projection-and-compaction.mmd) | How recorded history becomes a model request constrained by context policy. |

## Scope and terminology

This is an architectural interpretation of the code in this fork, not a
stable external API specification. The authoritative wire definitions are in
`codex-rs/app-server-protocol/src/protocol/` and
`codex-rs/protocol/src/protocol.rs`.

The most useful terms are:

| Term | Meaning |
| --- | --- |
| **surface** | A UI/client such as the terminal UI, desktop/IDE client, or MCP client. |
| **thread** | A durable conversation record that can be resumed or forked. |
| **turn** | One user-initiated unit of agent work. |
| **item** | A persisted unit inside a turn, such as a message, tool call, tool result, or file edit. |
| **session** | The live in-memory engine instance operating a thread. |
| **step** | One model sampling request plus the tool work it causes within a turn. |
| **tool** | A typed capability exposed to the model and executed by the local runtime. |
| **rollout** | An append-oriented local history used to reconstruct a thread/session; writers may repair an interrupted tail and add derived compaction records. |

### Diagram legend

- **Solid arrows** move a request, event, or durable record.
- **Dashed arrows** represent a derived projection, callback, or subscription.
- **Model-visible** data is allowed into the next model request; it is not the
  same thing as every durable record.
- **Live** data belongs to an in-memory session and disappears on process
  shutdown; **durable** data is used to reconstruct a later session.

## Source map

| Question | Start in |
| --- | --- |
| How does the `codex` binary start? | `codex-rs/cli/src/main.rs` |
| Where is the core engine created and driven? | `codex-rs/core/src/session/mod.rs` |
| How is a turn prepared and sampled? | `codex-rs/core/src/session/turn.rs` |
| How are tasks/turn lifecycle events emitted? | `codex-rs/core/src/tasks/` |
| How are tool calls translated and dispatched? | `codex-rs/core/src/tools/router.rs`, `registry.rs`, and `orchestrator.rs` |
| How do approvals work? | `codex-rs/core/src/tools/approvals.rs`, `exec_policy.rs`, and `session/mod.rs` |
| How does history stay within context limits? | `codex-rs/core/src/context_manager/` and `compact*.rs` |
| How do threads persist and resume? | `codex-rs/core/src/thread_manager.rs`, `codex-rs/thread-store/`, and `codex-rs/rollout/` |
| How do IDEs/apps control Codex? | `codex-rs/app-server/README.md` and `codex-rs/app-server/src/` |
| What crosses an API boundary? | `codex-rs/app-server-protocol/src/protocol/v2/` |
| What is the formal logic behind the tooling loop? | `07-formal-operational-model.md` |

## A useful mental model

A useful architectural lens is an event-driven state machine around a
non-authoritative planner. This is an analogy, not a claim that the repository
implements a textbook event-sourcing framework. The model proposes messages
and tool calls; the runtime mediates validation, execution, persistence,
cancellation, and user-visible state. That authority split is the main thing
to preserve if you build a similar system.

## Evidence record

The claims in this guide were checked against the repository at a pinned
commit. The reproducible protocol, source inventory, claim ledger,
adversarial decisions, and known evidence gaps are in
[the architecture research pass](audit/README.md).
