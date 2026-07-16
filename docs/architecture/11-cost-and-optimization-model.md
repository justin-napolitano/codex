# Cost and quality optimization model

This page extends the operational model with resource accounting. It does not
claim that Codex currently computes a complete bill in dollars. The runtime
does expose per-turn token and timing measurements; provider pricing and many
tool charges remain external or unknown.

## Cost vocabulary

For an action `a` moving state `Σ` to `Σ′`, define a resource vector:

```text
Cost(Σ, a, Σ′) :=
  ⟨input_tokens,
    cached_input_tokens,
    output_tokens,
    reasoning_output_tokens,
    wall_time_ms,
    sampling_time_ms,
    tool_blocking_ms,
    tool_call_count,
    tool_output_tokens,
    network_bytes,
    filesystem_process_effects,
    monetary_cost,
    risk_cost⟩
```

The dimensions have different evidence status:

| Dimension | Meaning | Current status |
| --- | --- | --- |
| Token counts | Input, cached input, output, reasoning output, and total model tokens. | Measured through `TokenUsage` and turn facts. |
| Time | Sampling, tool blocking, and turn-level elapsed time. | Partly measured through `TurnProfile` and telemetry. |
| Tool work | Calls, output size, network transfer, local process/filesystem effects. | Family-dependent; some dimensions are partial or unknown. |
| Money | Provider/model/token rates and tool/provider charges. | Unknown unless a verified rate card is supplied. |
| Risk | Destructive, privileged, remote, irreversible, or privacy-sensitive effects. | A policy score, not a bill; must be explicitly defined per deployment. |

`Cost` is therefore a vector, not one universal number. A scalar objective is
chosen only for a particular optimization decision:

```text
ScalarCost(C) =
  λ_money × C.monetary_cost
  + λ_latency × C.wall_time_ms
  + λ_tokens × TokenProxy(C)
  + λ_risk × C.risk_cost
```

The weights are policy choices. They are not properties discovered by the
model.

## Per-turn aggregation

If turn `t` performs actions `a₁ … aₙ`, with states `Σ₀ … Σₙ`, then:

```text
TurnCost(t) = Σᵢ Cost(Σᵢ₋₁, aᵢ, Σᵢ)
```

The implementation already computes a per-turn token delta by subtracting
turn-start usage from total usage. `TurnProfile` separately records sampling
time, tool-blocking time, sampling request count, and retry count. These are
measured facts, not price estimates.

Compaction, retries, approval waits, persistence, and tool execution must be
included as actions when their resource use matters. Waiting for approval may
have latency cost without model-token cost; a retry may add tokens and time
without improving the final result.

## Mapping tokens to money

Monetary cost is a separate function:

```text
MoneyCost(C, RateCard) =
  C.input_tokens × RateCard.input
  + C.cached_input_tokens × RateCard.cached_input
  + C.output_tokens × RateCard.output
  + C.reasoning_output_tokens × RateCard.reasoning
  + ToolCharges(C, RateCard)
```

`RateCard` must be keyed by provider, model, service tier, currency, and
effective date. If any required rate is absent or stale, the result is
`unknown`, not zero. Subscription quotas, workspace credits, and rate limits
are constraints or accounting signals; they are not automatically equivalent
to public per-token dollar prices.

## Quality-constrained optimization

The goal is not “minimize tokens at any cost.” Let `Quality(trajectory)` be a
documented utility score covering task completion, correctness, tool success,
constraint adherence, and answer completeness. Choose a strategy `π` by:

```text
minimizeπ ScalarCost(CostOf(π))
subject to
  Quality(π) ≥ q_min
  CompletionReliability(π) ≥ r_min
  SafetyConstraints(π)
  ToolAuthorization(π)
```

The first implementation is recommendation-only. It may compare shorter
context, cached context, reasoning effort, service tier, deferred tool search,
local versus remote tools, and retry/compaction choices. It must not silently
change policy, bypass sandboxing, or select an unapproved side-effecting tool.

## What is currently knowable

The current codebase supports measured analysis of:

- per-turn input, cached-input, output, reasoning-output, and total tokens;
- context-window and compaction token changes;
- sampling duration, tool-blocking duration, request count, and retry count;
- model/provider identity, reasoning effort, and service tier;
- tool-call outcomes and some tool/runtime telemetry.

It does not provide a universal, built-in monetary rate card for every model,
provider, service tier, MCP server, or local side effect. A cost report must
show measured values, estimates, unknowns, quality assumptions, and evidence
separately.

## Optimization workflow

1. Measure the candidate trajectory and record its action-level cost vector.
2. Attach a dated, verified rate card where applicable.
3. Estimate quality and completion reliability using the explicit rubric.
4. Reject candidates that violate authorization, safety, or quality constraints.
5. Compare scalar costs under declared weights.
6. Return a recommendation with confidence, unknown dimensions, and evidence.

The formal model and optimizer are decision aids. They do not prove that a
cheaper trajectory is better, and a lower token count can increase retries,
latency, or failure probability.

