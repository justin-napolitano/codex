# Policy layer: model proposals, discovery, approval, and enforcement

The policy layer answers two different questions:

1. **What can the model ask for?** The session constructs a request-scoped tool
   catalog from configuration, capabilities, plugins, apps, MCP servers, and
   deferred-tool metadata.
2. **What may actually happen?** The runtime validates the model's structured
   request, evaluates policy, obtains approval when required, constructs a
   permission profile, and enforces that profile at the execution boundary.

The model performs semantic reasoning over the tools it can see. It does not
scan the host filesystem for arbitrary tools, and a tool description is not an
authorization grant. The host controls exposure, registration, policy,
approval, sandboxing, and result routing. The reviewed evidence bundle is in
the [policy-layer research pass](audit/policy-layer/README.md).

## The four layers

| Layer | Main question | Typical implementation |
| --- | --- | --- |
| Model proposal | Which visible capability seems relevant? | Model response containing a function/custom/tool-search call |
| Host discovery | Which capabilities are visible or searchable this turn? | `build_tool_router`, exposure modes, feature/config filtering, `tool_search` |
| Authorization | Is this particular request allowed, pending approval, or forbidden? | execpolicy, `AskForApproval`, approval store, network policy |
| Enforcement | What resources can the attempted operation reach? | permission profile, OS sandbox, exec-server, network proxy |

Confusing these layers creates unsafe explanations. The model can choose a
visible `exec_command`, but it cannot bypass a forbidden policy decision. A
user can approve a command, but approval does not automatically grant access to
denied-read paths or unrestricted network access.

## How the model discovers tools

At the start of a sampling step, the session builds a `ToolRouter` and passes
its `model_visible_specs()` into the model request. The specs contain names,
descriptions, namespaces, and input schemas. The model reasons over those
descriptions and emits a structured call when it believes a capability is
needed.

The host determines the choice set first:

- model capabilities and feature flags gate support for tools such as
  `tool_search`;
- configuration enables or disables tools and namespaces;
- directly exposed runtimes become ordinary model-visible tool specs;
- deferred runtimes contribute searchable metadata rather than full callable
  specs;
- plugins, apps, and MCP inventories are filtered for the current client and
  environment;
- dynamic tools and extension tools are added only when the current turn owns
  them;
- hidden or direct-model-only runtimes are withheld from the ordinary tool
  catalog.

When deferred discovery is enabled, the model can call `tool_search`. Codex
searches bounded metadata (the tool-search description identifies BM25-style
matching), returns matching tools, and exposes the selected tools for a later
model request. That is a host-side retrieval heuristic. The semantic decision
to search, the query text, and the eventual choice among returned tools remain
model behavior.

The sequence is therefore:

```text
host builds request-scoped catalog
        ↓
model sees direct specs and possibly tool_search
        ↓
model reasons and emits a structured call
        ↓
host parses, validates, authorizes, and executes
```

## What is model reasoning versus host logic?

### Model-controlled behavior

- interpreting the user's request;
- deciding whether a tool is relevant;
- choosing a visible tool name and arguments;
- deciding whether to search deferred tools;
- selecting a search query;
- deciding how to use a tool result in the next response.

These are behavioral outputs of the model and are not proven by the host's
router. A model can choose an unsuitable tool or malformed arguments.

### Host-controlled behavior

- constructing the tool list and schemas sent to the model;
- deciding whether tool search is available;
- filtering disabled, unavailable, or client-incompatible tools;
- validating the response-item variant and arguments;
- resolving the registered runtime;
- applying hooks, policy, approval, sandbox, network, cancellation, and output
  limits;
- preserving `call_id` and feeding the result into the next request.

The host can constrain the model's options, but it does not generally infer the
user's intent and select a tool on the model's behalf.

## Command policy evaluation

The execpolicy language uses ordered token-prefix rules. A rule can assign
`allow`, `prompt`, or `forbidden`; multiple matching rules resolve to the
strictest severity (`forbidden` > `prompt` > `allow`). A `host_executable`
entry constrains basename fallback when absolute executable paths are resolved.

Example:

```starlark
prefix_rule(
    pattern = ["git", ["status", "diff"]],
    decision = "allow",
    justification = "read-only repository inspection",
)

prefix_rule(
    pattern = ["git", "push"],
    decision = "prompt",
    justification = "publishes changes to a remote",
)

prefix_rule(
    pattern = ["rm", "-rf"],
    decision = "forbidden",
    justification = "Use a reviewed, narrower deletion command.",
)
```

For a command `c`, the implementation first tokenizes command segments,
evaluates matching rules, and then derives a fallback for unmatched commands
from the approval mode, permission profile, sandbox policy, and platform
settings. A rule match can also propose a future policy amendment; that is a
configuration update, not an execution result.

## Approval modes transform prompts

`AskForApproval` controls whether a policy prompt can become a user-facing
approval request:

| Mode | Effect on a prompt |
| --- | --- |
| `never` | Prompt is rejected; no approval request is shown. |
| `on-request` | Prompt can suspend the turn until the user decides. |
| `unless-trusted` | Known safe read-only commands may be auto-approved; other commands prompt. |
| `granular` | Separate booleans control sandbox, rule, skill, permission-request, and MCP-elicitation prompts. |

The implementation can therefore turn an execpolicy `prompt` into
`NeedsApproval` or into `Forbidden` when the active approval mode disallows
that category. There is no execution while a call is waiting for approval.

Approval decisions may be one-time, session-scoped, denied, timed out, or
paired with an execpolicy/network amendment. Cached decisions are keyed by the
approval request rather than being a blanket grant for all tools.

## Permission profiles and enforcement

Approval answers “should this attempt proceed?” The permission profile answers
“what may the attempted process reach?” Relevant profiles include:

- `read-only`, optionally with network access;
- `workspace-write`, with configured writable roots;
- external sandbox, where another environment owns filesystem isolation;
- danger-full-access, with no Codex-managed restrictions;
- additional permissions or explicit escalation requests.

Denied-read restrictions are especially important: an escalation path must not
silently remove a restriction that only exists inside the sandbox. Network
access is also a separate decision, enforced through the network policy/proxy
path rather than inferred from a successful command approval.

## Formal model

Let:

- `M` be the model;
- `V(Σ)` be the visible tool specifications in state `Σ`;
- `S(Σ)` be the searchable deferred-tool metadata;
- `p = Propose(M, context)` be the model's structured proposal;
- `D(p, Σ)` be host discovery/activation for a proposal such as `tool_search`;
- `R(p, Σ)` mean that the requested runtime is registered;
- `Valid(p)` mean that the payload parses and validates;
- `Policy(Σ,p)` be `allow`, `prompt`, or `forbidden` after rule evaluation;
- `Approved(Σ,p)` mean that an allowed approval decision exists;
- `P(Σ)` be the effective permission profile;
- `SandboxAllows(P,r)` mean that profile `P` permits resource `r`;
- `Resources(p)` be the resources reached by executing `p`.

Model proposal is not execution:

```text
p = Propose(M, context)
```

Discovery constrains callable availability:

```text
p.tool ∈ V(Σ) ∨ p.tool ∈ D(S(Σ), p)
```

Final local execution requires every host gate:

```text
MayExecute(Σ,p) ⇔
    Valid(p)
    ∧ R(p,Σ)
    ∧ Policy(Σ,p) = allow_or_approved
    ∧ ∀r ∈ Resources(p): SandboxAllows(P(Σ), r)
```

The formula is a compact model of the implementation, not a proof that the
model selected a good tool. The policy and sandbox predicates are enforced by
host code; the model only supplies `p`.

## Evidence boundaries

The [policy inventory](audit/policy-layer/policy-call-inventory.json) maps each
decision boundary to implementation and test evidence. In particular, it
separates evidence for tool visibility and `tool_search` from evidence for
execpolicy, approval, sandbox, and network enforcement. Platform-specific
behavior and remote provider semantics remain explicit evidence gaps rather
than being generalized from the core layer.
