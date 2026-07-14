# Research pass standard

This is the local operating form of the research-pass standard supplied from:

`https://github.com/clz-digital-group/digital-labs-coding-lab-intake-api/blob/main/docs/planning/biblio/research-pass-standard.md`

The source was inspected on 2026-07-14. This bundled form preserves its required review loop, evidence classes, adversarial decisions, and output contracts while making the procedure reusable outside the source repository.

## Purpose

A research pass is a structured review protocol, not a bibliography-generation exercise. It must make the path from target claim to inspected evidence visible and reproducible. A citation proves only that a source was named; it does not prove that the source entails the target statement.

## Required loop

1. State the research question and freeze the review protocol before drawing conclusions.
2. Define scope, target files, cutoff date, search venues, search terms, allowed sources, inclusion rules, and exclusions.
3. Inventory sources with stable identifiers and metadata.
4. Extract atomic substantive claims from the target.
5. Map each claim to exact evidence and record contrary or limiting evidence.
6. Classify evidence strength.
7. Conduct an adversarial review.
8. Accept, weaken, relocate, or remove the claim.
9. Reconcile prose, diagrams, tables, and citations with that decision.
10. Publish a result summary with exact counts and unresolved gaps.

## Source audit contract

Each source record must include:

- `source_id`: stable identifier used by claims.
- `source_class`: implementation, test, generated schema, protocol, primary research, standard, official documentation, or another declared class.
- `title` and `locator`: human-readable name and path/URL/DOI.
- `version_or_commit`: commit, release, publication version, or access date for unversioned pages.
- `inspected_locations`: exact files, symbols, tests, sections, or pages actually read.
- `supports`: concise description of what the source can establish.
- `limitations`: what it cannot establish or where it may be stale.
- `accessed_at`: ISO date.

Do not list sources that were found but not inspected as supporting evidence.

## Claim ledger contract

Each claim record must include:

- `claim_id`: stable unique identifier.
- `claim`: one testable or assessable statement.
- `claim_class`: implementation behavior, protocol contract, invariant, recommendation, analogy, literature synthesis, or another declared class.
- `target_location`: precise location in the reviewed work.
- `evidence`: source identifiers plus the exact point relied upon.
- `counterevidence_or_limits`: the strongest known qualification.
- `strength`: one label from the scale below.
- `final_wording`: the wording retained after review, or `null` if removed.
- `status`: the final adversarial decision.

Split compound claims when their clauses require different evidence or strength.

## Strength scale

- `established`: directly established within stated assumptions by authoritative specification, proof, or decisive implementation evidence.
- `supported`: well supported by multiple or strong direct sources, but not universal or formally proven.
- `suggestive`: plausible evidence exists, but important uncertainty, indirectness, or version sensitivity remains.
- `hypothesis_only`: intentionally proposed for testing; not asserted as current fact.
- `local_observation_only`: observed in a bounded repository version, trace, benchmark, or environment and not generalized beyond it.
- `unsupported`: inspected evidence does not justify the statement.

Strength labels describe evidence fit, not rhetorical confidence.

## Adversarial review contract

For every claim, record:

- `claim_id`.
- `strongest_objection`.
- `source_limitations`.
- `conflicting_evidence` or an explicit statement that none was found in the defined search.
- `decision`: `accepted`, `weakened`, `moved_to_hypothesis`, `moved_to_evidence_gap`, or `removed`.
- `rationale`.

The adversarial pass must actively try to falsify scope, causality, universality, freshness, and enforcement. Absence of discovered conflict is not proof of truth.

## Evidence gaps

Use an evidence-gap record when the question matters but the pass cannot responsibly answer it. Include the missing evidence, searches performed, impact on the target, and a concrete next action. Wording that depends on the missing evidence must be removed, weakened, or marked as hypothesis.

## Result contract

The result must report:

- profile and status (`in_progress` or `complete`);
- number of target claims and inspected sources;
- counts by strength and review decision;
- number of open evidence gaps;
- changed target files;
- validation command and result;
- review cutoff and pinned repository commit.

Never mark a pass complete if an in-scope claim remains unsupported, lacks adversarial review, or differs materially from the retained target prose.

## Stop and restart conditions

Restart or amend the protocol when scope changes materially, a newer incompatible version becomes the target, a source previously treated as primary proves derivative, or a key conflict changes the conclusion. Preserve the earlier record; do not silently rewrite research history.
