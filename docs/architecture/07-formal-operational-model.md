# Formal operational model of Codex tooling

This page models the Codex tool runtime as a **state machine**: a system with
a snapshot of its current state and a defined set of allowed changes. It is a
precise way to review the implementation’s logic without requiring you to read
Rust first.

It is **not** a machine-checked proof, a claim that Codex has been formally
verified, or complete TLA+ syntax. It mixes two things and labels them
explicitly: an observational model of the pinned implementation, and normative
properties you would want to enforce in a system built from the same pattern.
The distinction matters because a clean formula can be stronger than the code
that inspired it.

## Known limitations and next improvement

This model is intentionally incomplete. The covered paths are submission,
steering, policy choice, approval, tool routing, persistence, live events, and
the main local/remote execution boundaries. The following runtime behavior is
not yet fully defined by transitions, postconditions, and implementation
evidence:

- resume and history reconstruction;
- compaction and call/output normalization;
- fork and snapshot semantics;
- cancellation during approval or execution;
- retries after partial completion; and
- platform-specific and remote-tool adapter behavior.

The coverage inventory marks these paths as `partially_covered` or `unmodeled`
instead of silently treating them as established behavior. The next formal
modeling pass should trace each path in the implementation, record its state
reads and writes, define its guards and postconditions, add evidence links and
representative traces, and then rerun the consistency and research validators.
Until that work is complete, formulas involving these paths are explanatory
abstractions or explicit hypotheses, not claims of complete runtime coverage.

## Read this notation first

You only need the symbols in this table. They are ordinary mathematical
shorthand; the page defines every symbol it uses.

| Symbol | Read it as | Example meaning |
| --- | --- | --- |
| `:=` | “is defined as” | `T := {t1, t2}` defines `T`. |
| `=` / `≠` | “equals / does not equal” | `x = y` says the two values are equal. |
| `∈` / `∉` | “is/is not a member of” | `c ∈ C` means call `c` is in set `C`. |
| `⊆` | “is a subset of” | `A ⊆ B` means every element of `A` is also in `B`. |
| `∀` | “for every” | `∀c ∈ C` means “for every call `c` in `C`.” |
| `∃` / `∃!` | “there exists / there exists exactly one” | `∃r` means at least one result; `∃!r` means one and only one. |
| `∧` / `∨` / `¬` | “and / or / not” | `A ∧ B` requires both conditions; `¬A` means A is false. |
| `⇒` | “implies” | `A ⇒ B` means when A is true, B must be true. |
| `⇔` | “if and only if” | `A ⇔ B` means A and B are true in exactly the same cases. |
| `{x \| P(x)}` | “all x such that P(x)” | `{c \| Completed(c)}` is the set of completed calls. |
| `⟨a, b, …⟩` | “a tuple containing…” | Groups several state variables into one system state. |
| `f(x)` | “function f applied to x” | `Context(H)` derives model context from history. |
| `≤` | “is less than or equal to” | `n ≤ 1` means n is at most one. |
| `Σ′` | “Sigma-prime” / “next state” | The system state after one transition from `Σ`. |
| `Σ ──a──▶ Σ′` | “action a moves Σ to Σ′” | `Enqueue(u)` or `Dispatch(c)` moves the runtime to a next state. |
| `:` | “such that,” or separates a name from its definition | `∃t : Owner(t)=u` means “there is a t such that…”. |

### Four words that make the formulas readable

- A **state** is one snapshot: which thread is live, which turn is active,
  what history is durable, and which approvals are waiting.
- A **transition** is one permitted state change, such as receiving a model
  tool call or accepting an approval.
- A **predicate** is a true/false question about data: `Cancelled(t)` asks
  whether turn `t` has been cancelled.
- An **invariant** is a property intended to remain true in every reachable
  state, not merely at the start or finish.

### How to judge consistency

This page is consistent only when its symbols, state components, transitions,
predicates, invariants, and implementation evidence agree. Use these tests:

| Concept | Review question | Example here |
| --- | --- | --- |
| State | Is one snapshot complete and typed? | `Σ := ⟨T,A,H,Q,P,K,E⟩` declares the runtime components. |
| Transition | Does every enabled action have a precondition, update, and postcondition? | `Submit(u)` has new-turn, steering, and rejection branches. |
| Predicate | Is each true/false condition defined with stable arguments and scope? | `AcceptableSubmit(Σ,u)` gates submission handling. |
| Invariant | Does the property hold across every reachable transition, not just one example? | `ActiveNormalTurns(s) ≤ 1` constrains ordinary model loops. |
| Evidence | Does the implementation or test evidence support the claim at the stated strength? | Session handlers and protocol types support the submission mapping. |

The full teaching primer is in the review skill’s
[logic-and-consistency primer](../../.codex/skills/formal-model-consistency-review/references/logic-and-consistency-primer.md).
The machine-checkable declaration for this page is
[`formal-model-spec.json`](formal-model-spec.json); it validates names, state
residency, transition contracts, and invariant scopes but does not constitute a
formal proof.

The second-pass implementation coverage map is in the
[runtime coverage inventory](audit/runtime-coverage-inventory.md). It records
which Rust entry points support each transition and leaves resume, compaction,
and fork paths explicitly marked when their evidence or model coverage is
incomplete. The accompanying
[trace fixtures](audit/runtime-traces.json) exercise representative approval
and steering paths without claiming to exhaust the runtime.

The old shorthand “every submission creates a turn” is too strong: a regular
turn can accept additional input as steering. The precise formulas appear in
the submission section below.

For example, read this rule left to right:

```text
AcceptableSubmit(Σ,u) ∧ NoActiveRegularTurn(Σ,u)
  ∧ Σ ──Submit(u)──▶ Σ′
  ⇒ ∃t ∈ Turns(Σ′) : TurnId(t) = SubmissionId(u)
```

It says: “if an acceptable submission arrives when no regular turn is active,
the resulting state contains a turn whose ID is that submission’s ID.” A
steering submission instead updates an existing turn’s pending-input queue.
The colon means “such that.”

## The objects being modeled

Let these be the abstract sets of runtime objects. Each row also names the
concrete implementation projection; the abstract object is not necessarily one
Rust struct.

```text
Thread       = durable conversation identity and metadata
Turn         = one model-loop unit of work owned by a thread/session
Item         = a durable or live turn-associated record
CallId       = correlation identity for one call and its result
Tool         = named capability, schema, and runtime implementation
Event        = live delivery envelope carrying an EventMsg
Profile      = effective permission, sandbox, network, and approval settings
Decision     = {allow, require_approval, deny}
```

| Abstract object | Concrete implementation projection |
| --- | --- |
| `Thread` | `ThreadId`, thread-store metadata, rollout identity, and `CodexThread`/`ThreadManager` handles. |
| `Turn` | `TurnContext`, `ActiveTurn`, `TurnState`, `sub_id`, task kind, input queue, and lifecycle status. |
| `Item` | `ResponseItem`, `TurnItem`, `RolloutItem`, or a lifecycle item depending on the projection. |
| `CallId` | String IDs on `ToolCall`, `ToolInvocation`, approval events, and tool outputs. |
| `Tool` | `ToolName`, `ToolSpec`, `CoreToolRuntime`, and `ToolRegistry` entry. |
| `Event` | `Event { id, msg: EventMsg }` delivered through the event channel. |
| `Profile` | `PermissionProfile`, `ActivePermissionProfile`, sandbox policy, approval policy, and network settings. |
| `Decision` | Execpolicy `Allow`, `Prompt`, or `Forbidden`, normalized here to `allow`, `require_approval`, or `deny`. |

The runtime state is the tuple:

```text
Σ := ⟨T, A, H, Q, P, K, E⟩
```

| Component | Meaning in plain English |
| --- | --- |
| `T` | Thread manager/store identities and durable thread metadata. |
| `A` | Live session state: active turn/task, `TurnContext`, queues, and step state. |
| `H` | Durable rollout/history projections used for recovery and reconstruction. |
| `Q` | Pending approval, user-input, and other external-answer waiters. Conceptually a special live subset of `A`. |
| `P` | Effective turn profile: permission/sandbox, approval, network, and related policy state. |
| `K` | Cancellation tokens and task/tool cancellation state. |
| `E` | Live `Event` envelopes and client delivery stream. |

The tuple separates ownership and purpose, not disjoint object sets. `H` is the
durable rollout projection; `E` is live client delivery. Some events are
persisted as `RolloutItem::EventMsg`, while history also contains response items
that were never live events. `Q` is separated from `A` because pending external
answers have special blocking and resume rules.

The residency map is:

```text
ThreadManager / ThreadStore ───────► T: Thread identities and metadata
Session.active_turn/state ─────────► A: TurnContext, ActiveTurn, TurnState
SessionState.history / rollout ────► H: durable RolloutItem projections
approval/input waiters/mailboxes ──► Q: pending external answers
TurnContext/config/profile ────────► P: effective policy/profile
task/tool CancellationToken ───────► K: cancellation state
event channel / Event{id,msg} ─────► E: live client stream
```

## Derived functions and predicates

The following names describe decisions the runtime derives from state. They
are not new storage tables.

```text
RegisteredTools(Σ, t)    = tool runtimes installed in the turn's registry
VisibleTools(Σ, t)       = tool specifications advertised to the model for turn t
Context(Σ, t)            = model input projected from H plus current facts
Registered(Σ, c)         = c.tool ∈ RegisteredTools(Σ, TurnOf(c))
ValidPayload(c)          = c's payload parses for its registered runtime
Exposed(Σ, c)            = c.tool ∈ VisibleTools(Σ, TurnOf(c))
Policy(Σ, c)             ∈ Decision, when that tool family defines this policy
Cancelled(Σ, t)          = t's cancellation token has been triggered
SandboxAllows(P, r)      = profile P allows access to resource r
ResultOf(c)              = output carrying the same CallId as c
Completed(c)             = c has a terminal output, error, or cancellation record
```

### Submission, routing, and policy functions

The submission is a structured operation, not just a text string:

```text
Submission u :=
  ⟨submission_id, thread_id, input_items, settings_overrides,
   additional_context, output_schema, client_message_id, trace_context⟩
```

`SubmissionId(u)` identifies the queued operation. `TurnId(t)` identifies a
turn; they often match for a newly created turn in this implementation, but
they are conceptually different identifiers.

```text
AcceptableSubmit(Σ,u) :=
  ThreadExists(Σ,u.thread_id)
  ∧ DirectInputAllowed(Σ,u.thread_id)
  ∧ InputWithinBoundary(u.input_items)
  ∧ SettingsOverridesValid(u.settings_overrides)

RouteInput(Σ,u) ∈ {CreateTurn, SteerExistingTurn, RejectSubmission}
ExposeTools(Σ,t) = visible and searchable tool specifications for t
RouteTool(Σ,t,c) ∈ {Dispatch(runtime), AwaitPolicy, RejectToolCall}
```

Normalize the implementation’s execpolicy vocabulary into this page’s
decision vocabulary:

```text
NormalizeDecision(Allow)    = allow
NormalizeDecision(Prompt)   = require_approval
NormalizeDecision(Forbidden)= deny
```

Approval-mode filtering is a second policy step:

```text
PolicyChoice(Σ,c) =
  deny               if ExecPolicy(c) = Forbidden
  require_approval   if ExecPolicy(c) = Prompt
                       ∧ ApprovalModeAllowsPrompt(P(Σ),c)
  deny               if ExecPolicy(c) = Prompt
                       ∧ ¬ApprovalModeAllowsPrompt(P(Σ),c)
  allow              if ExecPolicy(c) = Allow
```

`Submit` establishes the turn’s effective profile; it does not authorize all
future tool calls. A later model proposal is routed through
`PolicyChoice(Σ,c)`, then through sandbox and network enforcement.

Here are the helper names used later in formulas. None is assumed background
knowledge:

| Name | Meaning |
| --- | --- |
| `X(Σ)` | The value of state component or derived set `X` in snapshot `Σ`; for example, `Q(Σ′)` is the pending-answer set in the next state. |
| `TurnOf(c)` | The turn that owns call `c`. |
| `Turns(Σ)` | The turns represented in state `Σ`. |
| `Owner(t)` | The thread/session or originating submission identity associated with turn `t`; it is not the raw input vector. |
| `SubmissionId(u)` | The unique ID assigned to submission `u` before it enters the session queue. |
| `TurnId(t)` | The ID of turn `t`; for a new user turn it is normally derived from the submission ID. |
| `InputOf(t)` | User-input items accepted by turn `t`. |
| `AcceptedBy(t,u)` | True when existing turn `t` accepts submission `u` into its pending-input queue. |
| `ProfileOf(t)` | The effective permission/approval/network profile applied to turn `t`. |
| `ExecPolicy(c)` | Raw implementation decision for command call `c`: allow, prompt, or forbidden. |
| `PolicyChoice(Σ,c)` | Normalized authorization branch after execpolicy and approval-mode filtering. |
| `ApprovalModeAllowsPrompt(P,c)` | True when the active approval configuration permits a prompt for call category `c`. |
| `ThreadExists(Σ,id)` | True when `id` names a thread present in `T(Σ)`. |
| `DirectInputAllowed(Σ,id)` | True when the session accepts direct user input for thread `id`. |
| `InputWithinBoundary(items)` | True when the submitted input satisfies size, shape, and protocol limits. |
| `SettingsOverridesValid(overrides)` | True when requested per-turn settings are recognized and permitted. |
| `NoActiveRegularTurn(Σ,u)` | True when submission `u` has no ordinary model loop currently active in its target session. |
| `ActiveRegularTurn(Σ,t)` | True when ordinary turn `t` is the active model loop in `Σ`. |
| `ActiveNonSteerableTurn(Σ)` | True when the active task cannot accept steering input, such as review or compaction work. |
| `ThreadOf(t)` | The thread identity owning turn `t`. |
| `Status(t)` / `TaskOf(t)` | The lifecycle status / task classification of turn `t`. |
| `RegularTask` | The ordinary user-request model-loop task kind. |
| `PendingInput(t,Σ)` | Input items accepted for `t` but not yet consumed by its model loop. |
| `NoNewNormalTurnCreated(Σ,Σ′)` | True when a transition preserves the existing normal turn rather than creating another. |
| `Error(Σ,u)` / `NoToolEffectStarted(Σ,Σ′)` | An error record for `u` / the absence of a started tool side effect during the transition. |
| `ApplyOverrides(P,overrides)` | The profile produced by applying valid per-turn overrides to profile `P`. |
| `NewCancellationState(t)` | Fresh cancellation state associated with turn `t`. |
| `ActiveNormalTurns(s)` | The number of ordinary user-turn model loops active in live session `s`. |
| `CurrentFacts(Σ,t)` | Current instructions, settings, environment facts, and selected tool specifications for turn `t`. |
| `Normalize(h)` | Repair/project history `h` into coherent model-history shape, including call/output pairing. |
| `Compact(h)` | Produce the retained or summarized history representation chosen under context pressure. |
| `Inject(f,h)` | Combine current facts `f` with history projection `h` into a request representation. |
| `Size(x)` | The size measure used by the applicable context policy, normally token-oriented rather than Rust-object byte size. |
| `Bound(Σ,t)` | The applicable context/input limit for turn `t` in state `Σ`. |
| `Admitted(x)` | True when request `x` passes context construction and is accepted for model sampling. |
| `RunningCalls(Σ)` / `Running(c)` | Calls currently executing in state `Σ` / the true-false question that call `c` is executing. |
| `PendingApproval(c)` | True while call `c` is waiting for an approval answer. |
| `Resources(c)` | Files, network endpoints, processes, or other resources reached by executing `c`. |
| `P(Σ)` | The effective permission/sandbox profile component of state `Σ`. |
| `ModelHistory` | The normalized item sequence selected for a model request, not every raw rollout record. |
| `NeedsOutput(c)` | True when the protocol requires call `c` to have a paired model-visible output. |
| `CallId(x)` | The correlation identifier stored on call or result `x`. |
| `StartLocalEffect(c)` | The transition that begins the governed local command/patch side effect for call `c`. |
| `Execute(c)` | Execution of the locally sandboxed process associated with call `c`; used only in the local-sandbox formula. |
| `InitialHistory(s)` | The history installed when a reconstructed live session `s` starts. |
| `Reconstruct(H,thread)` | Derive usable initial session history for `thread` from recorded history `H`. |
| `Responsive(…)` | An assumption that the listed external participants eventually answer when required. |
| `Eventually(P)` | Informal temporal shorthand saying proposition `P` becomes true at some later state. |
| `Advance(t)` | Turn `t` makes another model/tool/state-machine step. |
| `VisibleBlock(t)` | Turn `t` exposes that it is waiting for user input, approval, or another named dependency. |

Lowercase letters are variables: `s` is a session, `t` a turn, `c` a call,
`r` a result/resource depending on the formula, `u` user input, and `outcome`
a terminal tool outcome. Uppercase names denote sets, state components, or
defined functions/predicates. The surrounding line disambiguates a reused
letter such as `r`; a production specification would normally choose more
distinct names.

`Context` is a **projection**, not a copy of all history. It normalizes the
call/output relationship, retains or compacts history according to the current
model/context policy, and injects current instructions, environment facts, and
tool specifications.

For a request that survives truncation/compaction and is admitted for sampling,
if `Bound(Σ, t)` is the applicable input limit, the intended postcondition is:

```text
Context(Σ, t) := Inject(CurrentFacts(Σ, t), Compact(Normalize(H)))
Admitted(Context(Σ, t)) ⇒ Size(Context(Σ, t)) ≤ Bound(Σ, t)
```

In English: an admitted request should be within the active limit. The runtime
uses compaction and output truncation to pursue that condition, but may reject
or fail on input it cannot make usable. This is more accurate than asserting
that every attempted request is unconditionally small enough.

## The transition system

### Thread and turn lifecycle

```text
StartThread() : add a new thread to T and create a live session in A
Resume(thread) : reconstruct a new live session from H for that thread
Fork(thread) : flush/snapshot its durable history and create a new thread identity
Cancel(t) : mark K for t cancelled and stop admitting new turn work
CompleteTurn(t) : record terminal outcome and clear t from active work
```

### What `Submit(u)` requires and changes

The external request is first enqueued, then handled asynchronously:

```text
Σ ──Enqueue(u)──▶ Σ₁ ──Handle(u)──▶ Σ₂
```

`Enqueue(u)` validates/maps the request at the API boundary, creates a
`Submission` ID, attaches tracing/client correlation, and sends an `Op::UserInput`
through the session submission channel. The handler applies settings and then
chooses one of three input-routing branches.

#### New regular turn

```text
AcceptableSubmit(Σ₁,u) ∧ NoActiveRegularTurn(Σ₁,u)
```

produces a new turn `t`:

```text
Σ₁ ──Handle(u)──▶ Σ₂ ⇒
  ∃t ∈ Turns(Σ₂):
    TurnId(t) = SubmissionId(u)
    ∧ ThreadOf(t) = u.thread_id
    ∧ InputOf(t) = u.input_items
    ∧ Status(t) = in_progress
    ∧ TaskOf(t) = RegularTask
```

The state effects are:

```text
A(Σ₂) = A(Σ₁) + TurnContext(t) + ActiveTurn(t) + InputQueue(t)
P(Σ₂) = ApplyOverrides(P(Σ₁), u.settings_overrides)
K(Σ₂) = NewCancellationState(t)
```

The user prompt is then recorded into durable history and projected into turn
items/events according to persistence policy; model sampling begins only after
the turn context and tool router are built.

#### Steering an active regular turn

If a regular turn `t` is already active:

```text
AcceptableSubmit(Σ₁,u) ∧ ActiveRegularTurn(Σ₁,t)
```

then no second normal model loop is created:

```text
Σ₁ ──Handle(u)──▶ Σ₂ ⇒
  t ∈ Turns(Σ₂)
  ∧ PendingInput(t,Σ₂) = PendingInput(t,Σ₁) ⧺ [u.input_items]
  ∧ AcceptedBy(t,u)
  ∧ NoNewNormalTurnCreated(Σ₁,Σ₂)
```

The existing turn consumes the queued input through its mailbox/input-queue
logic.

#### Rejected submission

Invalid, oversized, disallowed, or non-steerable submissions produce an error
transition:

```text
¬AcceptableSubmit(Σ₁,u) ∨ ActiveNonSteerableTurn(Σ₁)
  ⇒ Σ₁ ──Handle(u)──▶ Σ₂
  ∧ Error(Σ₂,u)
  ∧ NoToolEffectStarted(Σ₁,Σ₂)
```

This is why the stronger statement “every submission creates a turn” is not a
valid invariant.

### Submission → policy → tool routing

After a new turn is created, the effective profile `P(Σ₂)` influences tool
exposure and later authorization, but it does not itself select a tool:

```text
Submit(u)
  → TurnContext(t) + ProfileOf(t)
  → ExposeTools(Σ₂,t)
  → model proposes ToolCall c
  → registry resolves runtime
  → PolicyChoice(Σ,c)
  → Dispatch / AwaitPolicy / RejectToolCall
```

The post-model policy branches are:

```text
PolicyChoice(Σ,c) = allow
  ⇒ Σ ──Dispatch(c)──▶ Σ′
```

```text
PolicyChoice(Σ,c) = require_approval
  ⇒ Σ ──RequestApproval(c)──▶ Σ′
  ∧ c ∈ Q(Σ′) ∧ ¬Running(c)
```

```text
PolicyChoice(Σ,c) = deny
  ⇒ Σ ──RejectToolCall(c)──▶ Σ′
  ∧ ¬StartLocalEffect(c)
```

Approval can move a pending call into the allow branch; denial creates a
correlated denied result. Sandbox and network predicates still apply after an
allow decision.

The central serialization rule is:

```text
∀s : ActiveNormalTurns(s) ≤ 1
```

Read it as: “for every live session `s`, there is at most one normal active
turn.” This does not deny all parallelism; independent tool calls inside a
turn may run concurrently when their runtime permits it. It prevents two
ordinary model loops from concurrently mutating the same session context.

### Tool-call lifecycle

When the model emits a function/custom tool-call response item, the router
derives a call `c`:

```text
ReceiveToolCall(c) :
  model item ─▶ ToolCall⟨tool_name, call_id, payload⟩ ─▶ ToolInvocation(c)
```

The observed registry dispatch condition is deliberately weaker than model
exposure. A call can be dispatched only if a runtime is registered and its
payload is accepted; `Exposed` records whether the model was advertised the
schema, but the generic registry is not itself an exposure-enforcement gate:

```text
MayDispatch(Σ, c) ⇔
  Registered(Σ, c) ∧ ValidPayload(c) ∧ ¬Cancelled(Σ, TurnOf(c))
```

Normally a model calls only advertised tools, so `Exposed(Σ, c)` should hold
for model-originated calls. Treating that as a security invariant would require
an explicit dispatch-time check or equivalent provider guarantee; this audit
did not find that check in the generic registry path.

Authorization is handler-specific. For a command/patch call `c` whose local
side effect is governed by the execution policy, define:

```text
MayStartLocalEffect(Σ, c) ⇔
  MayDispatch(Σ, c) ∧ Policy(Σ, c) = allow
```

MCP, connector, search, and other remote capabilities can have different
credential, consent, and service authorization rules. They must be modeled by
their concrete handler rather than silently folded into `Policy` above.

If policy needs a person’s decision, the runtime does **not** execute. It
creates a pending request in `Q` and emits an approval event in `E`:

```text
Policy(Σ, c) = require_approval
  ⇒ Σ ──RequestApproval(c)──▶ Σ′
  where c ∈ Q(Σ′) and c ∉ RunningCalls(Σ′)
```

After the client/user responds:

```text
Approve(c) : Policy(Σ, c) := allow
Deny(c)    : append denied output for c; do not start its side effect
```

The actual code has a richer enum—skip approval, needs approval, or forbidden,
with reasons and possible policy amendments—but this three-way model preserves
the important authority distinction.

### Approval is not sandboxing

For a locally sandboxed process, an allow decision is necessary but not
sufficient to touch an arbitrary resource. Let `Resources(c)` be the files,
network, processes, and other resources the attempt reaches. The intended
local-execution property is:

```text
Execute(c) ⇒ ∀r ∈ Resources(c) : SandboxAllows(P(Σ), r)
```

In English: even an approved local command is intended to run inside the scope
enforced by its effective profile. Approval answers “should we attempt this?”
The local sandbox answers “what can the attempted process reach?” This formula
does not describe resources reached by an external MCP server or cloud service.

### Commit, retry, and cancellation

The registry converts a handler completion into a model-visible outcome tied
to the original call ID:

```text
Finish(c, outcome) :
  append ResultOf(c) to H
  emit applicable lifecycle events to E
  add ResultOf(c) to the next Context(Σ′, TurnOf(c))
```

`outcome` can be success, structured failure, denial, or cancellation. For a
call retained in normalized model history, the intended property is an
explicit, correlated outcome rather than forcing a later model step to guess.

## Safety properties to review

These are intended implementation properties, not claims of formal proof.

1. **Correlation after normalization.**
   ```text
   ∀c ∈ ModelHistory : NeedsOutput(c) ⇒ ∃r : CallId(r) = CallId(c)
   ```
   A tool call retained in normalized model history has a correlated output.
   The normalizer removes orphan outputs and supplies an aborted output for a
   call missing one. The inspected normalizer establishes pairing, but this
   audit did not find a general proof that duplicate matching outputs can never
   occur, so the formula does not use the “exactly one” quantifier `∃!`.

2. **No unauthorized local command/patch side effect (normative).**
   ```text
   StartLocalEffect(c) ⇒ MayStartLocalEffect(Σ, c)
   ```
   Naming a registered command/patch tool is not sufficient authorization.
   Other side-effecting tool families need their own corresponding predicate.

3. **No execution while waiting for approval.**
   ```text
   c ∈ Q ∧ PendingApproval(c) ⇒ ¬Running(c)
   ```
   A pending UI approval is a real pause in the state machine.

4. **Admitted model input obeys its size policy.**
   ```text
   ∀t : Admitted(Context(Σ, t)) ⇒ Size(Context(Σ, t)) ≤ Bound(Σ, t)
   ```
   Recorded history can grow; context construction, truncation, and compaction
   attempt to make a usable request. If they cannot, failure is preferable to
   silently violating the provider/context policy.

5. **Recovery uses durable state.**
   ```text
   Resume(thread) ⇒ InitialHistory(new session) = Reconstruct(H, thread)
   ```
   Resume creates a new live session from persistent records, not a revived
   reference to an old process or its old cancellation token.

## Conditional liveness

Safety means “nothing bad happens.” Liveness asks whether useful progress can
happen. The following is a **design hypothesis**, not an implementation claim
or a proved fairness property. Codex cannot guarantee progress if an external
dependency never responds:

```text
Responsive(model, tool, store, user) ∧ ¬Cancelled(Σ, t)
  ⇒ Eventually(Advance(t) ∨ VisibleBlock(t) ∨ CompleteTurn(t))
```

Read it as the desired behavior: if the model provider, required tool,
persistence layer, and any needed user decision eventually respond, a
non-cancelled turn should eventually take another step, visibly wait for
input/approval, or complete. `Eventually` is informal temporal-language
shorthand here; no scheduler/fairness proof was established in this pass.

## Where this model is implemented

| Model concern | Code to read |
| --- | --- |
| Submit, active sessions, events, approval waiters, persistence hooks | `codex-rs/core/src/session/mod.rs` |
| Submission envelope and operation variants | `codex-rs/protocol/src/protocol.rs` (`Submission`, `Op::UserInput`, `Event`) |
| New-turn versus steering input handling | `codex-rs/core/src/session/handlers.rs` and `session/input_queue.rs` |
| Live active-turn and turn-state residency | `codex-rs/core/src/state/turn.rs` and `state/session.rs` |
| Turn context, tool construction, sampling, cancellation | `codex-rs/core/src/session/turn.rs` |
| Model item → call → invocation | `codex-rs/core/src/tools/router.rs` |
| Registry, hooks, execution lifecycle, output conversion | `codex-rs/core/src/tools/registry.rs` |
| Allow / needs approval / forbidden policy | `codex-rs/core/src/exec_policy.rs` and `tools/sandboxing.rs` |
| Policy-dependent tool routing | `codex-rs/core/src/tools/router.rs`, `registry.rs`, and `exec_policy.rs` |
| Call/output normalization and bounded context | `codex-rs/core/src/context_manager/` and `compact.rs` |
| Start, resume, and fork from rollout/store history | `codex-rs/core/src/thread_manager.rs`, `thread-store`, and `rollout` |

MCP, skills, apps, remote execution, and multi-agent work are specialized ways
to expose or execute a capability. They reuse portions of the routing and
result loop, but their authorization/isolation boundaries differ. A safe
system should make this sequence true for each family: expose → validate →
authorize at the actual boundary → execute under applicable constraints →
record a correlated outcome → continue or complete.

## Optional background resources

You do not need these to read this page. Use them if you want a deeper
foundation in the notation or want to turn this operational model into a
machine-checkable specification.

- [MIT Mathematics for Computer Science notes on predicates and sets](https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2005/resources/ln2/)
  explain the set and logic notation used above.
- [State Machines in TLA+](https://lamport.azurewebsites.net/video/smintla.html)
  explains the initial-state/next-state mental model used by this page.
- [The TLA+ Video Course](https://lamport.azurewebsites.net/video/videos.html)
  is a deeper optional path into state-machine specifications, checking, and
  liveness/fairness.
