# Output profiles

All profiles produce the same six JSON records. They differ in source preference and the questions asked during adversarial review.

## `implementation-audit`

Use for claims about a repository, protocol, service, or runtime.

Evidence priority:

1. Executed tests or reproducible traces.
2. Implementation at a pinned commit.
3. Generated schemas and checked-in protocol types.
4. Maintainer-facing technical documentation.
5. User-facing documentation and comments.

Required challenge: identify the actual enforcement point. If none is found, phrase the claim as intent, convention, local observation, or hypothesis rather than an invariant.

## `literature-review`

Use for a synthesis of papers, standards, or established theory.

Evidence priority:

1. Primary research, formal standards, and official datasets.
2. Systematic reviews or authoritative textbooks.
3. Reputable technical summaries.

Required challenge: inspect whether population, assumptions, method, and reported result match the target claim. Separate replication from citation count.

## `publication-pass`

Use before publishing a technical report or manuscript. Combine implementation and literature evidence as appropriate.

Required challenge: test every public-facing assertion for source fit, reproducibility, version sensitivity, omitted limitations, and wording strength. Include a stable evidence bundle or explain why a source cannot be archived.

## Common files

| File | Purpose |
| --- | --- |
| `review-protocol.json` | Frozen question, scope, cutoff, and inclusion rules |
| `source-audit.json` | Sources actually inspected and their provenance |
| `claim-ledger.json` | Atomic claims, locations, evidence, strength, and final wording |
| `adversarial-claim-review.json` | Objections, limitations, and decisions |
| `evidence-gaps.json` | Unresolved or untestable questions |
| `research-pass-result.json` | Exact totals, outcome, and validation state |
