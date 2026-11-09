# USG v0.5 Semantic Foundation — Implementation Blueprint

## Objective

Replace the v0.4 practice of treating each interpreted claim as the primary semantic representation with a canonical compositional expression graph. Preserve the old claim representation as a compatibility projection so the UI, knowledge base, and inference engine remain operational while later milestones evolve.

## Implementation layout

```text
Source sentence
   |
   v
Existing LLM / local-rule proposal
   |
   v
v0.4 compatibility claim view
   |
   v
Source normalization and safe repair
   |
   v
semantic-core.js
   |-- entity registry
   |-- mention registry
   |-- evidence registry
   |-- PREDICATION expressions
   |-- scoped OPERATOR expressions
   |-- CONNECTIVE expressions
   |-- source-attributed RELATIONS
   |-- UNRESOLVED items
   |
   v
Canonical semantic graph + structural validation
   |
   +----> inspection UI and JSON export
   |
   +----> explicit human review / acceptance boundary
```

## Component responsibilities

### `app.js`

- Keeps the existing Ollama request and response handling.
- Normalizes source-driven tense, polarity, known clause cues, reference labels, and supported discourse links.
- Retains `claims` as the compatibility projection.
- Calls the semantic core after legacy normalization.
- Includes the canonical graph and validation in exports.
- Marks partial/invalid graphs as non-acceptable and batch results as partial.

### `semantic-core.js`

- Has no external package dependency.
- Runs in both the browser and Node test environment.
- Builds canonical entities, mentions, evidence, predications, operators, connectives, and relations.
- Validates identifiers, references, known argument requirements, quantifier bindings, source spans, scope references, and graph cycles.
- Never treats evidence alignment as proof of meaning or truth.

### JSON Schemas

- `schemas/usg-semantic-record-v0.5.schema.json`: complete record with compatibility fields and canonical graph.
- `schemas/usg-semantic-model-v0.5.schema.json`: standalone canonical graph.
- v0.4 schemas remain in the package for historical validation and migration reference.

## Key representational decisions

1. **Predicates stay affirmative/base-form where possible.** Negation is represented through `NOT` operator scope.
2. **Modal and quantifier operators are graph nodes.** The exact nested order is meaningful.
3. **Quantifier variables are bound to predicate arguments.** A restrictor class and bound variable are not merely free-floating metadata.
4. **Condition clauses are embedded graphs.** The antecedent is not promoted to an independent observed root.
5. **Causal relations are relation edges with attribution and verification status.** `source_asserted` is not the same as verified causation.
6. **Pronouns without antecedents remain unresolved mentions.** They do not create concepts named “it” or “he”.
7. **Known required arguments are explicit.** An absent object for a known transitive predicate is not silently accepted as complete.
8. **No generic relation is invented for missing predicates.** The claim is left unresolved.
9. **Unsupported scope stays visibly unresolved.** It is not converted into an unconditional proposition.
10. **Legacy claims are not discarded.** The canonical graph is added alongside the compatibility view.

## Release acceptance checklist

- [x] Build a canonical graph from legacy v0.4-compatible claims.
- [x] Add scoped NOT and modal operators.
- [x] Add quantifier nodes with explicit variable/restrictor binding for supported forms.
- [x] Add IF, UNLESS, WHEN connectives.
- [x] Preserve unknown/unsupported subordinate clauses.
- [x] Preserve unresolved pronouns without inventing referents.
- [x] Add structured unresolved items.
- [x] Validate expression references and cycles.
- [x] Preserve source evidence and clarify that alignment is not entailment.
- [x] Keep v0.4 claims and records importable.
- [x] Block knowledge acceptance for partial/invalid canonical graphs.
- [x] Add deterministic semantic-core regression tests.
- [x] Validate JSON Schema definitions and representative graph fixtures.
- [ ] Run live Qwen and Gemma batch evaluations on the user's PC.
- [ ] Build and score a human-labelled unseen-sentence benchmark.
- [ ] Complete the full linguistic coverage matrix and close remaining Milestone 1 gaps.

## Definition of completion

The code in this release is the first v0.5 implementation of the semantic foundation. Milestone 1 is not certified complete until the two unchecked evaluation items have been performed, the coverage matrix has been reviewed, and any failures have been fixed without regressing existing tests.
