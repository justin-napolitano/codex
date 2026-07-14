---
name: run-research-pass
description: Run a reproducible evidence audit over technical documentation, implementation claims, literature reviews, benchmark syntheses, or publication drafts. Use when claims must be traced to inspected sources, classified by evidence strength, challenged adversarially, corrected when overstated, and recorded in a reusable claim ledger and result bundle.
---

# Run Research Pass

Turn prose into an auditable set of atomic claims, then test every claim against inspected evidence. Treat citations as pointers, not proof: open the cited source, record what it actually supports, and weaken or remove prose that outruns it.

## Choose a profile

Read [references/output-profiles.md](references/output-profiles.md), then select the narrowest applicable profile:

- `implementation-audit` for repository documentation and behavior claims.
- `literature-review` for claims synthesized from papers or standards.
- `publication-pass` for a manuscript or public technical report.

Read [references/research-pass-standard.md](references/research-pass-standard.md) before auditing. It is the normative procedure bundled with this skill.

## Run the workflow

1. Define the research question, target files, evidence cutoff, included source classes, and explicit exclusions in `review-protocol.json`.
2. Inventory every inspected source in `source-audit.json`. Pin mutable repository evidence to a commit. Record exact files, symbols, sections, pages, or test names.
3. Extract substantive target statements into `claim-ledger.json`. Keep claims atomic enough that one evidence-strength label and one review decision apply.
4. Distinguish direct source claims from local observations and inferences. Never present an inference as a source statement.
5. Assign one strength: `established`, `supported`, `suggestive`, `hypothesis_only`, `local_observation_only`, or `unsupported`.
6. Perform an adversarial pass. For each claim, record the strongest objection, source limitation, conflicting evidence, and one decision: `accepted`, `weakened`, `moved_to_hypothesis`, `moved_to_evidence_gap`, or `removed`.
7. Edit the target prose to match the reviewed claim. Mark design recommendations, analogies, experimental interfaces, and historical documents explicitly.
8. Record unresolved questions in `evidence-gaps.json`; do not hide them in prose.
9. Summarize exact totals and completion state in `research-pass-result.json`.
10. Run the validator. A complete pass must have no `unsupported` target claim and no unreviewed claim.

## Create an audit bundle

Run:

```bash
python3 .codex/skills/run-research-pass/scripts/init_research_pass.py \
  --profile implementation-audit \
  --output path/to/audit
```

Then fill the generated records and validate them:

```bash
python3 .codex/skills/run-research-pass/scripts/validate_research_pass.py path/to/audit
```

Use the templates under `assets/templates/` when automation is unavailable.

## Evidence rules

- Prefer implementation, tests, generated schemas, specifications, and primary research over summaries.
- Use documentation to establish stated intent; use code and tests to establish observed implementation behavior.
- Do not infer runtime behavior from type names or comments alone when an executable path can be inspected.
- Record negative search results as evidence gaps, not proof that a behavior does not exist.
- Scope invariants to the layer that enforces them. A UI convention is not automatically a runtime invariant.
- Treat versioned or experimental interfaces as unstable unless compatibility is established separately.
- Preserve contradictory evidence in the ledger and explain the resulting decision.
- Link target prose to the audit index when the audit is intended for future maintainers.

## Completion contract

Call a pass `complete` only when:

- every in-scope substantive claim has a ledger row;
- every ledger row names inspected evidence or is explicitly a hypothesis/evidence gap;
- every claim has an adversarial review record;
- prose and diagrams reflect the final decisions;
- counts in `research-pass-result.json` match the records; and
- `validate_research_pass.py` exits successfully.

Otherwise leave the pass `in_progress` and state exactly what remains.
