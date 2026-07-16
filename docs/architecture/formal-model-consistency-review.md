# Formal-model consistency review

Scope: `docs/architecture/07-formal-operational-model.md` with
`docs/architecture/formal-model-spec.json` and the runtime coverage inventory.

## Deterministic checks

✅ No structural consistency findings.

✅ Machine-readable model validation passed.

✅ Runtime coverage references resolved and use valid statuses.

✅ Representative trace validation passed for approval/dispatch and steering.

✅ Every declared transition now includes cost dimensions from the shared cost
vector.

## Semantic review

- Submission, steering, policy, approval, dispatch, persistence, and event
  paths are represented by declared transitions.
- The model distinguishes observed, inferred, and unverified claims.
- The single-normal-turn and approval-pauses-execution invariants identify the
  transitions expected to preserve them.
- The cost model separates measured tokens/time from estimated monetary cost
  and keeps unknown provider/tool rates explicit.
- Resume, compaction/normalization, fork, cancellation edge cases, retries,
  and platform-specific adapters remain partial or unverified in the coverage
  inventory and are explicitly documented as the next improvement area in the
  [formal model limitations section](07-formal-operational-model.md#known-limitations-and-next-improvement).

## Remaining evidence gaps

The registry and traces are consistency gates, not a theorem prover. They do
not establish reachability of every state, fairness/liveness, absence of
duplicate results, or correctness of every remote and platform-specific tool
adapter. Those limitations remain explicit rather than being treated as
proof.

Cost optimization is also intentionally advisory. No verified universal rate
card exists in this repository, so recommendations must not present token
counts or subscription credits as exact dollars without dated external rates.
