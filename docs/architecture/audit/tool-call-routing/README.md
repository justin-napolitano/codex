# Tool-call routing research pass

This audit applies the `implementation-audit` profile of the local
`run-research-pass` skill to the tool-call and routing inventory. The reviewed
commit is `e6611398b020a4d1ebef66f6644e3555375dc3fe`.

Start with the [human inventory](../../09-tool-call-and-routing-inventory.md),
then use the [claim ledger](claim-ledger.md), [source/evidence index](source-audit.md),
and machine-readable [call inventory](tool-call-routing-inventory.json).

The pass contains 20 atomic claims, 20 inspected sources, 20 adversarial
reviews, and two open gaps. Open gaps deliberately limit generalization about
platform-specific sandbox enforcement and remote provider reliability.
