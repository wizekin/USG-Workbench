# USG Rule Semantics and Safety Contract v1.0.0

This package gives precise declarative meaning to the rule model in `USG-RULE/1.0.0` and registry `USG-SEMANTIC-RULE-REGISTRY/1.0.0`.

**Execution remains disabled.** This is a normative specification and static consistency check, not a rule matcher or inference executor.

## Files

- `contract.json` — outcomes, premise eligibility, constraint semantics, scope, conflict, open-world, determinism, resource, and safety policies.
- `contract.schema.json` — strict Draft 2020-12 contract schema.
- `README.md` — this overview.

## Core decisions

- Exact typed identity and version matching only; no label matching or coercion.
- Every required premise and constraint must pass in declared order.
- The initial reference-rule eligibility policy admits `SOURCE_ASSERTED` only. The compact Step 2.2 evaluator snapshots are not full canonical documents and must not be passed directly to an executor without an explicit fixture adapter or versioned fixture extension. `INFERRED` is not chained in rule model v1.0.0; `VERIFIED` is not implicitly admitted; `DISPUTED` returns CONFLICTING; `UNKNOWN` remains UNKNOWN; missing status is UNRESOLVED.
- Attribution, context, polarity, modality, quantifier scope, temporal order, and role order are preserved exactly.
- Conflicts are preserved without selecting a winner.
- Open world is the default. Closed-world negation requires an explicit task-scoped policy and a named complete domain.
- Only APPLICABLE can create a conclusion candidate, with complete derivation. A candidate is DERIVED_NOT_VERIFIED.
- Determinism and provenance order are part of semantics.
- Resource interruption returns INCOMPLETE and preserves all input items; no semantic truncation.
- No human-review gate or automatic truth promotion.

## Outcomes

The rule applicability outcomes are APPLICABLE, NOT_APPLICABLE, UNKNOWN, UNRESOLVED, AMBIGUOUS, CONFLICTING, UNSUPPORTED, INVALID_INPUT, and RESOURCE_INTERRUPTED. They are distinct. In particular, a missing premise is not a negative fact, UNKNOWN is not UNRESOLVED, and a conflict is not resolved by recency, frequency, or confidence.

## Validate

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_rule_semantics.py" -v
```
