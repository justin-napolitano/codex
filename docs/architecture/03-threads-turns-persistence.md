# Threads, turns, items, and persistence

## The four levels of state

See the lifecycle and storage relationship:
[thread lifecycle and resume diagram](diagrams/04-thread-lifecycle-and-resume.mmd).

Codex uses several related concepts that are easy to conflate.

```text
Thread (durable conversation identity)
  ├─ Turn 1 (one user-requested run)
  │    ├─ user message item
  │    ├─ assistant message item/deltas
  │    ├─ tool-call item(s)
  │    └─ tool-result item(s)
  ├─ Turn 2
  └─ …

Live Session (in-memory execution owner for a thread)
  ├─ current configuration and environment
  ├─ model/context manager
  ├─ active turn cancellation and input queues
  ├─ event subscribers
  └─ persistence/rollout handle
```

### Thread

A thread is the durable unit a UI lists, resumes, forks, archives, or deletes.
It has an ID and persisted history. The app-server’s modern interface exposes
`thread/start`, `thread/resume`, `thread/fork`, `thread/read`, and
`thread/list`.

Forking preserves a prior history as the basis for a new conversation branch;
it does not make two sessions mutate one shared transcript.

### Turn

A turn begins when the user submits work to a specific thread. It can involve
multiple model samples and many tool calls. The thread is the conversation;
the turn is the unit of active work, cancellation, accounting, and completion.

The ordinary user-turn path gives a live session one active normal task at a
time. The task framework also has specialized task kinds, including review
and compaction, so this is a scoped description rather than a theorem that no
other task can ever coexist. Independent tool calls can run inside a turn when
their runtimes permit it, and separately created sessions/threads can run in
parallel.

### Item

Items are the detailed, replayable record. They capture more than chat text:
user inputs, agent messages, tool calls, tool results, command execution,
patch/application state, and other lifecycle facts. Items are what let a UI
render a historical run and what let the runtime rebuild model context.

### Step

Internally a turn may have multiple steps. One step is broadly: assemble the
next input, stream one model response, execute its resulting tools, then feed
their outputs into the next step. This lets a single user request be an actual
agent loop rather than a single completion.

## Persistence model

The exact storage implementation is deliberately separated from the agent
logic.

- `core/src/thread_manager.rs` coordinates thread lifecycle from the core.
- `codex-rs/thread-store/` provides thread storage abstractions/backends.
- `codex-rs/rollout/` manages rollout persistence and replay-oriented state.
- `core/src/session/rollout_reconstruction.rs` reconstructs a live session’s
  usable state from persisted history.
- `core/src/context_manager/` converts retained history into size-governed model
  input.

The key design is append-oriented history plus reconstruction, not “save one
mutable chat blob.” Selected response items and lifecycle records are written
as the agent makes progress. The record is not literally immutable: rollout
code can repair an interrupted JSONL tail, maintain metadata, and add compacted
projections. On resume, Codex rebuilds coherent history and session state
rather than pretending an interrupted in-memory task is still running.

## Resume is not simply loading text

When a client resumes a thread, the runtime must restore enough information to
act consistently:

1. the ordered conversation/item history;
2. which response/tool calls completed and which were interrupted;
3. model and reasoning settings, unless the user explicitly overrides them;
4. token usage and context-window state;
5. configuration/environment details needed for the new turn;
6. a valid model context with tool-call/output pairs normalized.

The app-server README notes that thread resume can return history directly or,
for experimental clients, return metadata and let the client page turn
history. That is a UI/network optimization, not a license to omit the runtime
history reconstruction required for correct model continuation.

## Context is a projection of history

See the separate model-input path:
[context projection and compaction diagram](diagrams/06-context-projection-and-compaction.mmd).

Full stored history does not necessarily fit in a model request. Codex retains
recovery-oriented records and derives a smaller model-visible projection:

```text
recorded thread items
      │
      ├─ normalize orphaned/incomplete tool call pairs
      ├─ retain essential recent/structural items
      ├─ compact older material when necessary
      └─ inject current instructions/environment/tools
      ▼
request constrained by model/context policy
```

`core/src/context_manager/history.rs` and `normalize.rs` handle history shape.
`core/src/compact*.rs` and `core/src/tasks/compact.rs` handle context-window
pressure, while output-truncation policies limit particular tool results. The
repository’s contributor rules explicitly require bounded, structured model
context. That is a design requirement enforced through several limits and
fallbacks, not a mathematical guarantee that every provider request succeeds:
oversized or uncompactable input can still fail visibly.

## Interruption and steering

An interrupt is an event in the agent lifecycle, not a silent UI-only action.
The session cancels current work, emits terminal/error state as appropriate,
and records enough state that later history remains consistent. A subsequent
turn can continue using the stored thread context rather than resuming a
half-alive process.

Steering is related but distinct: it lets the user add input while a run is in
progress. The session owns a queue and rules for incorporating it safely. A
robust agent runtime needs this distinction; treating every new keystroke as a
fresh independent run causes races and incoherent transcript state.

## Design lessons for your own system

- Give every durable entity a stable ID: thread, turn, item, tool call,
  approval, artifact.
- Record both the requested action and its outcome, correlated by call ID.
- Make interruption a first-class persisted outcome.
- Never reuse mutable live-session state as the only source of truth.
- Separate the full audit record from the compacted context projection sent to
  the model.
- Serialize mutations of a single thread; use separate threads/workers for
intentional concurrency.

## What survives what?

| Event | Live session | Thread/rollout history | Consequence |
| --- | --- | --- | --- |
| Normal turn completion | Remains available while loaded | New items are durable | A later turn continues normally. |
| Client disconnect | Server-owned work is not defined by the socket alone; behavior depends on the owning surface and shutdown path | Already written items remain available | A reconnecting UI must resubscribe, read, or resume as the protocol permits. |
| Process shutdown | Lost | Persisted items remain | A new session reconstructs from history. |
| Interrupt mid-tool | Cancellation state ends the active work | Interrupted state/output pairing is normalized | Future context is coherent, not optimistic. |
| Fork | Source session may be flushed first | Snapshot becomes a new thread basis | Branches do not share mutable turn state. |
