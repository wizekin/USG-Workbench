# Phase 2 Step 2.1 — Semantic reasoning definitions and architecture

**Status:** DEFINITION COMPLETE  
**Implementation status:** No reasoning runtime or rule executor is introduced by this step.  
**Parent roadmap:** [USG Phase 2 — Semantic Reasoning Roadmap](PHASE-2-ROADMAP.md)  
**Phase 1 foundation:** [USG-SEM/1.0](../specifications/USG-SEM-1.0.md) and [Phase 1 exit acceptance](../interoperability/PHASE-1-EXIT-ACCEPTANCE.md)

## 1. Decision

Phase 2 will develop a **deterministic, evidence-aware, rule-governed reasoning capability over explicit USG semantic graphs**. It will not treat natural-language plausibility, lexical similarity, a model score, a relation label, a quote match, or a derivation record as sufficient grounds for a conclusion.

The initial reasoning subset is intentionally explicit and testable. Generalization is earned by adding validated rules and benchmark coverage; it is not assumed from the existence of a general-purpose engine.

## 2. What a reasoning task consists of

A reasoning task must identify:

1. **Input document snapshot** — exact USG profile and document content being reasoned over.
2. **Goal or query** — the requested expression, relation, variable, or result pattern. A future query contract must make its scope and target explicit.
3. **Rule-set snapshot** — exact registry identity and versions enabled for this task.
4. **Execution context** — explicitly selected context, assumptions, and applicable domain.
5. **Execution policy** — deterministic ordering and resource budget, without changing semantic meaning.
6. **Result** — structured conclusion candidates, derivations, evidence assessments, conflicts, unresolved items, and completion diagnostics.

If any required element is absent, the task must either use a documented default that is semantically neutral and safe or report the missing prerequisite. It must not silently invent a source, referent, definition, context, premise, or rule.

## 3. Eligibility before inference

An expression is eligible as a premise only when the relevant checks for that rule succeed. The checks will be defined and implemented in later steps, but the minimum categories are:

- the expression and all required references exist and have the expected target types;
- the constructor is registered and structurally valid;
- required operands, role bindings, variables, and argument ordering are correct;
- the relevant semantic kinds and expression sorts satisfy the rule's declared constraints;
- definitions resolve to the exact required identity and version;
- operator scope, polarity, modality, quantifier binding, temporal scope, attribution, and context match the rule's requirements;
- the premise is available under the rule's declared epistemic/evidence policy;
- the premise is not disqualified by ambiguity, unresolved status, opaque structure, invalidity, or a conflict policy.

Eligibility is rule-specific. A structure may be usable for one operation and ineligible for another. There will be no global coercion that turns every syntactically valid record into an inference-ready fact.

## 4. Four distinct layers of reasoning

### Layer A — Structural validation

Checks whether the document and graph conform to their declared contracts: schema, identifiers, typed references, graph constraints, constructor signatures, source spans, and required fields.

**Output:** validation diagnostics and eligibility inputs.  
**Does not establish:** interpretation correctness, entailment, evidence support, or truth.

### Layer B — Semantic grounding

Resolves exact concepts, frames, roles, relations, referents, and contexts using declared IDs and versions. It checks scope and bindings required by the selected rule.

**Output:** resolved references and explicit unresolved/ambiguous results.  
**Does not establish:** that a grounded assertion is true or that a relation label has an unstated logical property.

### Layer C — Formal inference

Applies an enabled, versioned rule to premises that satisfy all declared conditions. A rule defines which structures it consumes and what result it may produce.

**Output:** a conclusion structure and a Derivation/provenance record.  
**Does not establish:** objective truth, independent corroboration, or external verification.

### Layer D — Evidence and conflict assessment

Evaluates evidence and competing assertions only under a separately specified policy. It must identify the source, target claim, assessment method, independence assumptions, and limits of the assessment.

**Output:** evidence/support/conflict assessments.  
**Does not automatically establish:** objective truth or universal factual correctness.

External verification, where eventually supported, is a separate governed integration and is not implicit in Layer D.

## 5. Existing USG records and their roles

Phase 2 must use the existing record families according to their defined purpose:

| Existing record | Permitted role in Phase 2 | Prohibited shortcut |
|---|---|---|
| Source | Exact source text, identity, language, metadata, and source boundary | Treating a source as trustworthy solely because it is present |
| Expression | Compositional semantic structure and rule-matching subject | Treating an expression as an assertion that its content occurred |
| Assertion | Explicit claim, origin, commitment, epistemic status, attribution, and evaluation context | Treating SOURCE_ASSERTED or INFERRED as objective truth |
| Evidence | Source span, exact quote, alignment status, semantic-support status, and supporting-rule references | Treating an exact span or quote match as entailment |
| Context | Explicit actual-world, hypothetical, fictional, belief, domain, conditional, negated, or other context | Automatically lifting a claim from one context into another |
| Definitions | Versioned concepts, frames, roles, and relations | Inferring identity, equivalence, inheritance, symmetry, inverse, or transitivity from labels |
| ExpressionRelation | Directed typed relationship, verification status, and evidence links | Treating SUPPORTS, CONTRADICTS, CAUSE, or another label as self-verifying |
| UnresolvedItem | Explicit unresolved, unsupported, ambiguous, incomplete, conflicting, resource-interrupted, or unknown state | Forcing a resolution or treating resource interruption as negative evidence |
| Derivation | Ordered provenance linking inputs, outputs, rule IDs, method, status, and diagnostics | Treating the existence of a derivation or its VALIDATED status as a truth certificate |
| Validation / mapping | Structural conformance and adapter-coverage diagnostics | Treating schema validity or LOSSLESS/PARTIAL mapping as semantic correctness |

The record model does not itself activate reasoning. The current Phase 1 models are deliberately passive data structures.

## 6. Rule execution contract — requirements to be specified in Step 2.3 and 2.4

A rule must define, at minimum:

- a stable opaque identifier and explicit version;
- a human-readable purpose and rule category;
- the variables and typed record/constructor patterns it may bind;
- required premises and optional premises, with explicit ordering where relevant;
- semantic-kind, expression-sort, identity, role, and definition constraints;
- context, attribution, polarity, modality, quantifier, and temporal-scope preconditions as applicable;
- the exact conclusion template and any permitted side effects;
- the assumptions and data-closure policy it requires;
- non-applicability conditions and failure/diagnostic behavior;
- references to positive, negative, boundary, and adversarial tests;
- deterministic execution semantics and compatibility information.

Rules are data and executable policy, not semantic facts. A rule registry must not infer its own rules from observed co-occurrence or lexical similarity. Candidate rules proposed by a model remain inactive until separately validated, versioned, and enabled under the acceptance policy.

Because current USG-SEM/1.0 rule references are opaque strings and there is no canonical first-class Rule record collection, the initial registry will be specified separately. Any canonical document-level Rule collection or new typed reference space must be considered through a separate versioned contract change.

## 7. Conclusion and evidence boundaries

A future reasoning API must keep these questions separate:

1. **Was the input structurally valid?**
2. **Was its interpretation resolved sufficiently for this rule?**
3. **Did the declared premises match?**
4. **Did the rule execute successfully?**
5. **What exact conclusion was produced?**
6. **Which inputs and rule versions produced it?**
7. **What source evidence aligns with the conclusion?**
8. **What support or contradiction assessment was actually performed?**
9. **What remains unknown, unresolved, unsupported, disputed, or incomplete?**
10. **Was any independent external verification performed?**

The response must not compress those answers into a single confidence, validity, acceptance, or truth value.

In particular:
- **Derivation success** means a rule ran according to its execution contract.
- **Rule support** means the conclusion is licensed by that specified rule system and its premises.
- **Evidence support** means evidence was assessed under a stated support policy.
- **Corroboration** requires a stated independence policy and is not obtained by duplicating the same source.
- **Verification** requires a separately defined procedure and evidence; it is not inferred from the other four.

## 8. Unknown, unresolved, conflicting, and incomplete outcomes

Phase 2 must preserve distinctions already present in USG:

- **UNKNOWN:** the value or status is not known.
- **UNRESOLVED:** an interpretation, reference, or decision required by the task has not been resolved.
- **AMBIGUOUS:** multiple materially different interpretations remain possible.
- **UNSUPPORTED:** the construction or operation is outside the enabled rule/model subset.
- **CONFLICTING:** relevant records or assessments disagree under a declared comparison policy.
- **INCOMPLETE:** execution did not finish or required input was unavailable.
- **RESOURCE_INTERRUPTED:** a resource budget or execution interruption stopped processing.

These states do not imply one another. The exact result schema and any additional statuses are reserved for later versioned specifications. Phase 2 must not overload an existing status field with a different meaning.

## 9. Safety and semantic limits

The following requirements are mandatory:

- **No silent defaulting:** never assume a missing referent, context, premise, quantifier restrictor, frame, role, or definition version when the rule requires it.
- **No lexical shortcut:** labels and similar words do not prove identity, equivalence, entailment, or relation properties.
- **No unsupported closure:** no transitive, symmetric, inverse, causal, or temporal closure unless a versioned rule explicitly defines and tests it.
- **No closed-world assumption by accident:** absence is not negation unless the task names a closed domain and an explicit completeness policy.
- **No model authority bypass:** a model can propose, but only the declared contracts, rules, and evaluator can authorize execution or classify the result.
- **No confidence laundering:** model scores, ranking, rule execution, evidence alignment, and verification remain independent.
- **No semantic caps:** do not truncate records, operands, candidate interpretations, or derivations to fit an implementation. Report resource interruption as incomplete with diagnostics.
- **No hidden context transfer:** hypothetical, fictional, attributed, belief, conditional, negated, and actual-world content must not be conflated.
- **No silent status promotion:** no automatic transition to VERIFIED, CORROBORATED, or an equivalent stronger state merely because a rule ran.

## 10. Evaluation contract

The benchmark and evaluator are Step 2.2 deliverables. They must be designed before an inference engine is implemented.

Each fixture must record:
- a stable fixture ID and category;
- the exact USG profile and relevant package/adapter versions;
- the input document and exact task/query;
- enabled rule-set versions and relevant execution configuration;
- expected conclusions and acceptable alternative representations, if any;
- expected non-conclusions and prohibited inferences;
- expected provenance/evidence links;
- expected unresolved, conflict, or incomplete diagnostics;
- a rationale for the expected result.

The evaluator must separately measure soundness/precision, supported-case coverage/recall, false-inference rate, scope/binding accuracy, evidence-assessment accuracy, provenance completeness, preservation/partiality, determinism, and resource behavior.

Thresholds must be established before the inference executor is accepted. The false-inference gate must be stricter than a generic language-generation quality score; a fluent but unsupported answer is a failure.

## 11. Implementation and compatibility decisions

- The Python kernel is the initial reference implementation target, in a new additive version line; historical package directories remain immutable.
- The JavaScript Semantic Workbench remains a separate line. Integration is through explicit versioned adapters and conformance tests.
- USG-SEM/1.0, its schema, the Phase 1 registries, and all Phase 1 adapter behavior remain unchanged under this definition step.
- Existing Evidence, Context, Definitions, ExpressionRelation, UnresolvedItem, and Derivation models are not retroactively changed from passive records into active engines.
- Existing Node.js workflow/action versions are not changed by this work.
- No human-review requirement is introduced.
- All future implementation PRs must pass their required checks on the exact PR head before merge.

## 12. Step 2.1 completion checklist

- [x] Phase 2 objective and non-goals defined.
- [x] Interpretation, validation, grounding, inference, derivation, evidence, corroboration, and verification separated.
- [x] Existing USG record-family responsibilities and prohibited shortcuts documented.
- [x] Target architecture and processing boundary documented.
- [x] Rule requirements identified without prematurely freezing an implementation schema.
- [x] Unknown, unresolved, ambiguous, unsupported, conflicting, incomplete, and resource-interrupted outcomes distinguished.
- [x] Evaluation categories, measures, and threshold-setting policy specified.
- [x] Phase 1 compatibility and versioning constraints recorded.

**Step 2.1 exit result:** Definition and architecture work is complete. No inference behavior is yet implemented or claimed.

**Next:** Step 2.2 — build the versioned benchmark corpus and evaluator, then fix measurable acceptance thresholds before creating the rule model or executor.
