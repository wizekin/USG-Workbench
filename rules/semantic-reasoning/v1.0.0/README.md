# USG Semantic Rule Model and Registry v1.0.0

This is the first versioned, declarative rule-model and registry contract for Phase 2 Step 2.3.

## Status and execution boundary

- Model: `USG-RULE/1.0.0`
- Registry: `USG-SEMANTIC-RULE-REGISTRY/1.0.0`
- Input semantic profile: `USG-SEM/1.0`
- Registry activation: **disabled**
- All four entries are `SPECIFIED_NOT_EXECUTABLE`.

This package defines data and validation rules only. It does not load executable functions, import Python callables, interpret templates, match premises, or execute inference. A registry entry cannot become active before the later execution step and its benchmark gates.

## Package contents

- `registry.schema.json` — strict JSON Schema Draft 2020-12 contract.
- `registry.json` — four versioned, disabled reference rules.
- `README.md` — this compatibility and activation guide.

## Rule record

Each rule specifies:
- stable opaque ID and semantic version;
- purpose and category;
- typed variables;
- ordered required premise patterns;
- explicit machine-readable constraints and failure diagnostics;
- context, attribution, polarity, modality, quantifier, temporal, role-order, and world-assumption policies;
- conclusion-candidate templates;
- assumptions and closed-domain policy requirements;
- non-applicability conditions;
- diagnostics and positive/negative/boundary benchmark coverage;
- deterministic execution requirements, duplicate/cycle policy, resource interruption behavior;
- USG profile, model, registry, benchmark, and adapter compatibility.

A rule conclusion is a **derived candidate**, not a truth or verification promotion. The model intentionally does not add a first-class Rule record to USG-SEM/1.0; rule data remains in this separately versioned registry.

## Reference rules

| Rule ID | Purpose | Benchmark coverage |
|---|---|---|
| `benchmark-rule:modus-ponens@1.0.0` | Directed implication with an eligible antecedent in the same context | Modus ponens, invalid converse, missing premise, provenance |
| `benchmark-rule:and-elimination-left@1.0.0` | Derive the left conjunct from an eligible asserted AND | Conjunction elimination and unsupported opaque premise |
| `benchmark-rule:closed-domain-negation@1.0.0` | Negation by absence only under an explicit, complete, named closed-domain policy | Closed-world positive, open-world negative, incomplete-domain negative |
| `benchmark-rule:preserve-before@1.0.0` | Preserve directed BEFORE operands without reversal or converse inference | Temporal direction and temporal boundary |

These entries formalize benchmark reference policies; they are not a claim that an inference engine exists or that the current USG Kernel Lab executes them.

## Validation

From the repository root:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_rule_registry.py" -v
```

The validator checks the schema, unique identities, known benchmark fixture references, positive and negative coverage, declared variables, exact benchmark policy IDs/versions, closed-world prerequisites, deterministic execution metadata, and non-promotion safeguards.

## Compatibility

- USG-SEM/1.0 and its JSON Schema are unchanged.
- No Phase 1 adapter, registry, archive, package, or immutable implementation baseline is modified.
- No rule behavior is inferred from existing opaque rule IDs.
- No human-review gate, implicit closed-world assumption, semantic truncation, silent coercion, or automatic truth promotion is allowed.
- Resource interruption is specified as an explicit incomplete result with full input preservation.
