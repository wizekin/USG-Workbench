# Phase 1 Step 5B — Python kernel 0.5.0 implementation

**Status:** implementation candidate; awaiting automated CI  
**Contract:** [Step 5A semantic contract](STEP-5A-CONTRACT.md)  
**Release:** Python kernel 0.5.0  
**Baseline:** Python kernel 0.4.0 remains unchanged

## Implemented in this change

- Native `PREDICATE_APP` constructor with SIT result sort, ordered role-to-operand alignment, and preservation of argument requirements/bindings, event frame, tense/aspect/temporal frame, attribution, provenance, completeness, evidence references, and source claim identity.
- Native `CONNECTIVE` constructor with PROP result sort, explicit connective identity, one-to-one operand roles, ordered operands, directed conditional role validation, and preserved source metadata.
- Native `QUANTIFIER` constructor with PROP result sort, one PROP body, explicit operator family/identity, stable binder identity, display variable, scope kind, optional restrictor/binding metadata, count, surface text, evidence and attribution.
- Deterministic JSON envelopes for structured source metadata. The AST does not interpret metadata as truth conditions.
- Binder utilities for free variable occurrence reporting, closed-scope checks, alpha-equivalence by binder identity (including binder-linked metadata), and identity-aware free-variable substitution.
- Distinct `OPAQUE` and `UNRESOLVED_REF` preservation nodes; neither is inference-eligible and both retain source sort only as archival metadata.
- Serialization round-trip and canonicalization tests, including legacy `Q` compatibility.
- CI coverage for the complete copied 0.5.0 kernel test suite, including the new constructor tests and an immutable-baseline guard that explicitly excludes only the new v0.5.0 release directory.

## Semantic safeguards

- `PREDICATE_APP` remains SIT. Proposition-taking parents require explicit `HOLDS`.
- `CONNECTIVE` operands must be PROP. No identity is coerced to AND, OR, IMPLIES, or COND; order is retained.
- `QUANTIFIER` remains distinct from legacy `Q`. No conversion is attempted merely because operator labels look similar.
- No arbitrary operand, item-count, or semantic-depth caps are introduced.
- No edits are made to `archives/`, `implementations/python-kernel/v0.4.0/`, or the Workbench v0.5.4 baseline.
- USG-SEM/1.0 remains unchanged.

## Current boundary

Structured metadata is stored as canonical JSON text in immutable AST parameters and recovered with `metadata_value`. This is lossless preservation, not a claim that every metadata field has a complete native reasoning interpretation. Exact frame/connective mappings and full restrictor semantics remain gated by explicit versioned rules and conformance tests.
