# USG Semantic Workbench v0.5.1 — Milestone 1 acceptance test plan

**Semantic profile:** `USG-SR/0.5.1`  
**Purpose:** Verify that the canonical semantic foundation preserves compositional structure, references, scope, evidence, and uncertainty.  
**Important:** Structural conformance is not a semantic-accuracy score. Live Qwen/Gemma evaluation and a human-labelled unseen-sentence benchmark are still required before Milestone 1 can be declared complete.

## 1. Automated tests

Run from the project root:

```bat
node --check app.js
node --check server.js
node --check semantic-core.js
node tests\semantic_foundation_test.js
node tests\smoke_test.js
```

Or use `tests\run_all_tests.bat`.

The optional JSON Schema fixture validator requires Python and `jsonschema`:

```bat
python -m pip install jsonschema
python tests\validate_schemas.py
```

## 2. Semantic object model

- [ ] Every supported proposition is a `PREDICATION` node with explicit argument roles.
- [ ] Required argument roles are checked using the declared predicate registry.
- [ ] Events/states/relations have a frame and independent grammatical tense/aspect/temporal frame.
- [ ] Entities are provisional and graph-local unless a separate identity decision is supplied.
- [ ] Repeated mentions preserve surface text and occurrence identity.
- [ ] An unresolved pronoun remains a mention; USG does not invent an entity named after the pronoun.
- [ ] Evidence references resolve to evidence records; offsets and quotes match the source exactly.
- [ ] Evidence alignment is not presented as semantic entailment or truth verification.

## 3. Operator scope

For each case, inspect the canonical expression graph, not just the compatibility `claims` array.

| Source | Required representation |
|---|---|
| `The customer does not like the tool.` | `NOT(LIKE(customer, tool))` |
| `The customer does not dislike the tool.` | `NOT(DISLIKE(customer, tool))`; do not infer LIKE |
| `The customer might not need the tool.` | `MIGHT(NOT(NEEDS(customer, tool)))` with explicit operator targets |
| `Not every customer needs the tool.` | `NOT(FORALL x: CUSTOMER(x) -> NEEDS(x, tool))` |
| `No customer needs the tool.` | `FORALL x: CUSTOMER(x) -> NOT(NEEDS(x, tool))` |
| `The customer is expected to need the tool.` | Preserve unsupported scope as UNKNOWN/unresolved; do not flatten to asserted NEEDS |

- [ ] Quantifier variable binds to the corresponding argument and restrictor.
- [ ] Unsupported quantifier scope is represented by `UNRESOLVED_SCOPE` and a structured unresolved item.
- [ ] Operator ordering is preserved; operators are not assumed to commute.

## 4. Connectives and nested clauses

| Source | Required representation |
|---|---|
| `If prices increase, the customer will stop using the tool.` | `CONDITIONAL(antecedent, consequent)`; antecedent is not an independent observation; its present grammatical tense remains separate from future reference time |
| `Unless prices increase, the customer does not need the tool.` | EXCEPTION relation; do not invent what happens when prices increase |
| `When prices increase, the customer stops using the tool.` | Distinct WHEN connective, not generic IF |
| `Although prices increased, the customer stopped using the tool.` | Unsupported scope remains unresolved until a licensed representation is implemented |
| `The customer needs the tool or wants a refund.` | OR connective; do not assume exclusive OR without evidence |
| `The customer needs the tool but does not need it.` | Preserve both propositions; CONTRAST is not itself proof of contradiction |

- [ ] Every connective operand reference exists.
- [ ] Nested antecedents are not promoted as independently asserted facts.
- [ ] Incomplete subordinate clauses are structured unresolved items.
- [ ] Missing predicate/subject is never replaced with a fabricated generic relation.

## 5. Attribution, evidence, and provenance

- [ ] A source “because” clause is represented as a separate proposition and CAUSE relation.
- [ ] Cause relation attribution is `source_asserted` and verification is `not_independently_verified`.
- [ ] LLM, local-rule, and derived provenance remain distinguishable.
- [ ] Missing/invalid evidence quotes do not become verified source spans by assertion; source fallback and model quote status are separately recorded.
- [ ] Top-level legacy unresolved messages are promoted to structured `unresolvedItems`.

## 6. Graph integrity and acceptance

- [ ] Every expression has a unique ID.
- [ ] Every scope, operand, evidence, entity, mention, relation, and bound-variable reference resolves.
- [ ] Expression containment graph has no cycles.
- [ ] Roots are unique and every expression is reachable from a root or reported in validation warnings.
- [ ] A graph can be structurally valid but semantically partial.
- [ ] Partial or invalid canonical graphs cannot be accepted through the UI.
- [ ] Candidate records explicitly require human review; acceptance does not establish objective truth.

## 7. Compatibility and application behavior

- [ ] v0.4 workspace local-storage layout remains loadable.
- [ ] Existing `claims` remain available as a compatibility projection.
- [ ] New records include `semanticModel` and `semanticValidation`.
- [ ] Batch export uses schema `1.3` and semantic schema version `0.5.1`.
- [ ] Meaning, Structure, Evidence, and JSON views render the canonical graph and unresolved items.
- [ ] `GET /api/health` returns version `0.5.1`.
- [ ] Root UI, `/app.js`, and `/semantic-core.js` return HTTP 200.

## 8. Live model evaluation (must be run on the user's PC)

Use the same installed Ollama model versions and settings for both model runs. Do not edit exported files and do not accept test records into the knowledge base.

```text
The customer does not dislike the tool.
The customer might not need the tool.
The customer needs the tool, but does not need it.
If prices increase, the customer will stop using the tool.
Unless prices increase, the customer does not need the tool.
When prices increase, the customer stops using the tool.
Although prices increased, the customer stopped using the tool.
The customer stopped using the tool because it failed.
The customer bought a tool. He uses it every day.
The customer needs the tool or wants a refund.
Not every customer needs the tool.
No customer needs the tool.
The customer is expected to need the tool.
Prices were different.
```

- [ ] Run the entire batch with Qwen.
- [ ] Run the identical batch with Gemma, if installed.
- [ ] Export both JSON files.
- [ ] Inspect raw proposal, compatibility claims, canonical graph, validation, unresolved items, and source spans.
- [ ] Report false splits, false merges, wrong scope, missing relations, and invented propositions.

## 9. Human-labelled unseen-sentence benchmark

- [ ] Prepare a separate test set not used to write extraction patterns or prompts.
- [ ] Have a human label proposition boundaries, entities, predicate, argument roles, polarity, scope, modality, tense/time, clause relations, coreference, and unresolved information.
- [ ] Score each field separately (precision/recall/F1 where applicable, exact-match for scoped structures, and error counts for invented/omitted propositions).
- [ ] Include ambiguity and genuinely underspecified examples; expected output may be unresolved.
- [ ] Compare Qwen and Gemma with identical prompts/settings.
- [ ] Set release acceptance thresholds before inspecting test scores to avoid tuning the benchmark after seeing results.

## 10. Milestone 1 exit decision

Milestone 1 is **not certified complete** until:

1. automated and schema tests pass;
2. live model batches are reviewed;
3. the human-labelled unseen-sentence benchmark is scored;
4. supported/unsupported coverage is documented;
5. critical regressions are fixed and the full suite passes again.
