# Phase 5 — Step 5.5: Nested Compositional Semantic Construction

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Contract:** `USG-INTERPRET/0.2.0`  
**Composer:** `semantic-composition/0.2.0`  
**Expression graph schema:** `USG-INTERPRET-EXPRESSION-GRAPH/0.2.0`

## 1. Deliverables

Step 5.5 composes accepted clause syntax candidates into typed, source-grounded semantic expression graphs. It introduces versioned transitive predicate frames, entity-reference nodes, predicate nodes, and nested clause-group nodes. It retains lexical/syntax alternatives and does not promote source descriptions into truth assertions.

## 2. Typed expression model

- `REF / ENTITY`: source-grounded AGENT or PATIENT reference with surface form, lexical sense, concept reference, morphology features, source span, and derivation references.
- `PREDICATE / PROPOSITION`: typed predicate frame with ordered entity operands and explicit AGENT/PATIENT role bindings.
- `CLAUSE_GROUP / PROPOSITION_SET`: nested grouping of multiple clause propositions. It preserves the clause roots and inter-clause attachment candidates without claiming that the connective's discourse semantics are fully resolved.

The graph is separate from USG-SEM/1.0. Its versioned schema is an interpretation-internal artifact; it does not modify the normative semantic interchange profile or SQLite document schema.

## 3. Predicate frames

The initial frame registry maps the explicitly registered English and MSA Arabic predicate senses for write, read, build, test, and examine to typed transitive frames. Each frame requires AGENT and PATIENT. Unknown predicate senses do not receive guessed frames and remain unsupported.

## 4. Ambiguity and partial results

Every syntax candidate combination produces a separate semantic graph candidate. Ambiguous lexical senses therefore remain distinct graph alternatives. Unsupported clauses are listed in `unresolved_clause_refs`; supported clauses can still be retained in a partial graph. Candidate-budget exhaustion returns `INCOMPLETE_RESOURCE_LIMIT` and preserves generated candidates.

## 5. Provenance and validation

Every node contains source spans and derivation references. REF nodes point to exact lexical token spans; PREDICATE nodes point to the action token; CLAUSE_GROUP nodes span the composed clause range and retain connective marker spans. Graph validation checks unique node IDs, root/operand references, clause roots, typed operations/sorts, and Unicode code-point spans. A dedicated JSON Schema validates the serialized graph candidate.

## 6. Acceptance tests

Tests cover English and Arabic transitive composition, VSO/SVO equivalence at the frame level, nested multi-clause grouping, attachment evidence, lexical ambiguity alternatives, unknown/unsupported abstention, candidate budgets, source identity/digest mismatch, and node-level provenance. Phase 4 and Phase 5 Steps 5.2–5.4 regressions must pass.

## 7. Explicit limitations

This step composes the currently enabled transitive frame family and clause groups. It does not yet enable negation, modality, tense/aspect scope operators, quantification, semantic coordination truth conditions, or broad modifier composition. Those remain later Phase 5 steps.
