# Semantic Schema Index

## Current release: USG-SR/0.5.1

New exports use record version `0.5.1` and representation profile `USG-SR/0.5.1`.

- `schemas/usg-semantic-record-v0.5.schema.json` validates the full record, including compatibility claims, canonical semantic model, and validation metadata.
- `schemas/usg-semantic-model-v0.5.schema.json` validates the canonical semantic graph independently.
- `USG_SEMANTIC_COMPOSITION_SPEC_v0.5.1.md` specifies the source-grounded clause and connective composition layer.
- `SEMANTIC_REPRESENTATION_SPEC_v0.5.md` is retained as the original v0.5 semantic foundation specification; review the v0.5.1 change report for its corrections and extensions.

The canonical model contains entities, mentions, evidence, expressions, typed relations, roots, unresolved items, and an acceptance boundary. Expressions are `PREDICATION`, `OPERATOR`, or `CONNECTIVE` nodes. Current operators include negation, modality, quantifier, and unresolved-scope forms. Connectives include conditional, exception, when, concession, contrast, conjunction, and disjunction.

## Historical release: USG-SR/0.4

`schemas/usg-semantic-record-v0.4.schema.json` and `SEMANTIC_REPRESENTATION_SPEC_v0.4.md` are retained for migration and historical comparison. The Workbench continues to retain the v0.4-compatible `claims` projection.

## Validation interpretation

- `valid`: implemented structural/reference checks passed.
- `valid_with_warnings`: structural checks passed, non-fatal warnings remain.
- `partial`: graph is structurally valid but semantic content remains unresolved/unsupported.
- `invalid`: structural/reference checks failed.
- `unavailable`: canonical core was not loaded.

Structural validity is not semantic accuracy, source entailment, or objective truth. Source-span matching verifies only that a quote aligns with the supplied source substring.
