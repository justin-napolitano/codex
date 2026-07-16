---
name: formal-model-consistency-review
description: Review formal runtime and systems models for undefined symbols, contradictory state transitions, inconsistent terminology, and gaps between equations, diagrams, and implementation references. Use when auditing Markdown specifications, operational models, state machines, or architecture documents.
---

# Formal Model Consistency Review

Review a formal model as a small specification, not as ordinary prose. Check that its vocabulary, state tuple, transition rules, policy functions, diagrams, and implementation claims agree with one another.

Read [references/logic-and-consistency-primer.md](references/logic-and-consistency-primer.md)
before reviewing a model. It defines state, transition, predicate, function,
precondition, postcondition, invariant, reachability, and the difference
between structural, semantic, and evidence consistency.

## Workflow

1. Identify the model boundary: target files, implementation commit or workspace state, and whether the review is semantic, evidence-backed, or both.
2. Run the bundled structural checker:

   ```bash
   python3 .codex/skills/formal-model-consistency-review/scripts/review_formal_model.py \
     docs/architecture/07-formal-operational-model.md
   ```

   Use `--output path/to/report.md` to save the report.

   When a machine-readable registry exists, validate it with:

   ```bash
   python3 .codex/skills/formal-model-consistency-review/scripts/validate_formal_model_spec.py \
     docs/architecture/formal-model-spec.json \
     --coverage docs/architecture/audit/runtime-coverage-inventory.json
   ```

   The registry is a constrained cross-reference check, not a theorem prover.

3. Build a symbol table. For every symbol in an equation, record its definition, sort/type, scope, and whether it denotes a set, element, predicate, function, relation, or state component. Flag symbols that are used before definition or change meaning.
4. Check state transitions. Every transition must identify its precondition, state changes, postcondition, and observable effects. Distinguish durable history (`H`) from live events (`E`), and pending waits (`Q`) from active execution (`A`).
5. Check composition. Verify that submission routing, policy choice, tool exposure, tool dispatch, approval waits, cancellation, and errors form a coherent path. Ensure each branch has an explicit outcome and does not silently bypass policy.
6. Check diagrams against prose and equations. Every named node or transition in a Mermaid chart should have a corresponding definition; prose must not claim a branch that the chart omits.
7. Check evidence links. Implementation claims must point to exact files, symbols, tests, or generated schemas. Mark design recommendations and abstractions as such; do not present them as observed runtime facts.
8. Write findings with severity (`error`, `warning`, or `note`), location, violated invariant, evidence, and a proposed correction. Re-run the checker after edits.

9. Validate representative lifecycle traces when available:

   ```bash
   python3 .codex/skills/formal-model-consistency-review/scripts/validate_formal_traces.py \
     docs/architecture/formal-model-spec.json \
     docs/architecture/audit/runtime-traces.json
   ```

   Treat synthetic traces as path checks, not proof of runtime behavior.

10. When reviewing cost claims, require an action-level cost vector, a declared
    aggregation rule, a quality constraint, and a dated rate-card key. Keep
    measured tokens/time, estimated money, and unknown charges separate.

## Machine-checkable subset

Use JSON to register state components, symbols, predicates, functions,
transitions, and invariants. Every transition must declare preconditions,
written state components, and postconditions. Every invariant must declare its
scope. Keep formulas human-readable and treat the validator as a consistency
gate, not as proof of arbitrary first-order logic or of the implementation.

## Required invariants

- Each state variable in `Σ` has one stable meaning and an explicit runtime residency.
- Every transition preserves the declared state shape or documents an intentional extension.
- A submission has a defined acceptance predicate and routing outcome: new turn, steering, or rejection.
- A tool call passes through exposure, registry resolution, policy choice, and then dispatch, approval wait, or denial.
- `allow`, `require_approval`, and `deny` are not conflated with lower-level policy names such as `Allow`, `Prompt`, or `Forbidden`.
- Durable records and live delivery envelopes are related but not interchangeable.
- Identifiers used for correlation (`thread_id`, `turn_id`, `submission_id`, `call_id`) have distinct scopes and relationships.
- Any claim stronger than the inspected implementation is labeled as an abstraction, recommendation, or hypothesis.
- Every important implementation entry point is mapped to a transition or explicitly marked `unmodeled`.
- Every invariant names the transitions responsible for preserving it.
- Every modeled transition declares the cost dimensions it may consume.
- Cost optimization is recommendation-only unless an explicit authorization is added.

## Output

Return a concise review report containing: scope, structural-check results, symbol table issues, transition issues, policy/routing issues, evidence issues, and a prioritized correction list. A clean review should state that no errors were found and list remaining warnings or evidence gaps explicitly.
