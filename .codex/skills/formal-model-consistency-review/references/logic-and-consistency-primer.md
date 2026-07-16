# Logic and consistency primer

This primer explains the minimum logic needed to review a runtime model. The
goal is not to turn the reader into a mathematician; it is to make each claim
checkable.

## The basic pieces

- **State**: one complete snapshot of the system. In this repository,
  `Σ := ⟨T,A,H,Q,P,K,E⟩` records threads, active work, durable history,
  pending answers, policy, cancellation, and live events.
- **Transition**: one labeled state change, written `Σ ──a──▶ Σ′`. `Σ` is the
  before-state, `a` is the action, and `Σ′` is the after-state.
- **Predicate**: a true/false question, such as `Cancelled(Σ,t)` or
  `AcceptableSubmit(Σ,u)`.
- **Function**: a mapping from inputs to an output, such as
  `PolicyChoice(Σ,c)`. A function must state its input domain and output
  domain; if it can be undefined, that condition must be explicit.
- **Precondition**: what must be true before an action is enabled.
- **Postcondition**: what must be true after an enabled action completes.
- **Invariant**: a property that must hold in every reachable state, not only
  at startup or after one happy-path example.
- **Reachable state**: a state obtainable from an initial state by a sequence
  of enabled transitions.

## Reading a rule

```text
AcceptableSubmit(Σ,u) ∧ NoActiveRegularTurn(Σ,u)
  ∧ Σ ──Submit(u)──▶ Σ′
  ⇒ ∃t ∈ Turns(Σ′) : TurnId(t) = SubmissionId(u)
```

Read this as:

1. The two predicates before the arrow are preconditions.
2. `Submit(u)` is the action.
3. `Σ′` is the resulting state.
4. `∃t ∈ Turns(Σ′)` introduces a turn that must exist in that state.
5. The expression after the colon is the postcondition for that turn.

The rule does not say every submission creates a turn. Steering and rejection
are separate enabled branches with different postconditions.

## What makes a model consistent?

A model is logically consistent when its declarations and rules can be read
together without contradiction:

1. **Symbol consistency**: every symbol has one definition, sort, and scope.
   A name cannot mean a set in one formula and an identifier in another.
2. **State consistency**: every transition reads and writes declared state
   components, and preserves the declared state shape unless an extension is
   explicitly documented.
3. **Transition consistency**: every enabled branch has a precondition,
   action, state update, postcondition, and observable outcome. Two branches
   with overlapping preconditions must either agree or state their priority.
4. **Predicate consistency**: predicates use arguments of the declared sort
   and do not silently change from observed implementation behavior to a
   normative design requirement.
5. **Invariant consistency**: each invariant is scoped to reachable states and
   is preserved by every relevant transition. A happy-path example is not a
   proof of an invariant.
6. **Policy/routing consistency**: a tool call cannot bypass the declared
   exposure, registry, policy, approval, sandbox, and result path.
7. **Evidence consistency**: implementation claims point to inspected code,
   tests, schemas, or other sources; abstractions and recommendations are
   labeled as such.

## Review levels

- **Structural review** checks fences, required concepts, declarations, and
  cross-references in the machine-readable registry.
- **Semantic review** checks whether the rules agree: for example, steering
  must append to an existing input queue and must not also create a second
  normal turn.
- **Evidence review** checks whether the implementation actually supports the
  modeled behavior. A well-formed formula can still be false of the code.

The bundled checker performs structural checks and validates the declared
machine-checkable subset. The reviewer must still inspect overlapping guards,
reachability, fairness assumptions, and code evidence; this is not a theorem
prover.

