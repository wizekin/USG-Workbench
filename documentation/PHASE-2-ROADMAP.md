# USG Phase 2 — Semantic Reasoning Roadmap

**Phase:** 2 — Evidence-grounded, rule-governed semantic reasoning  
**Status:** Steps 2.1–2.7 complete; deterministic inference and conservative evidence/conflict assessment layers implemented; query/explanation and interactive Kernel Lab layers remain pending  
**Prerequisite:** Phase 1 exit accepted (USG-SEM/1.0 and composed adapter v1.5.1)  
**Normative Phase 1 record:** [Phase 1 exit acceptance](../interoperability/PHASE-1-EXIT-ACCEPTANCE.md)

## 1. Purpose

Phase 1 established a versioned semantic interchange contract, explicit native record families, loss-preserving adapters, and reproducible conformance boundaries. Phase 2 builds on that foundation to reason over represented semantic structures in a controlled and testable way.

The Phase 2 target is **scoped semantic reasoning over explicit USG representations and explicit, versioned rules**. It is not a claim of unrestricted natural-language understanding, a human-like general reasoner, or a system that can determine objective truth from text alone.

The governing objective is:

> A conclusion may be produced only when its input structures, definitions, scope, context, and rule preconditions are explicit and validated. Every conclusion must have a reproducible derivation trace. When those conditions are not met, USG must preserve the uncertainty or incompleteness instead of guessing.

## 2. Phase 2 objectives

1. Define a formal boundary between interpretation, structural validation, rule-based inference, evidence assessment, and external verification.
2. Establish a benchmark that measures correct reasoning and, especially, prevents unsupported conclusions.
3. Introduce versioned, inspectable rules with explicit premises, constraints, scope, context, and conclusion templates.
4. Resolve definitions and references only through explicit identity and versioned mappings.
5. Execute deterministic rules over eligible semantic structures and record complete derivation provenance.
6. Represent support, conflict, and unresolved outcomes without collapsing them into one confidence or truth flag.
7. Expose reasoning inputs, outputs, and explanations through a testable interface after the underlying contracts are stable.

## 3. Governing principles

These principles carry forward the Phase 1 invariants and govern every Phase 2 step.

### 3.1 Preserve the canonical boundary

- USG-SEM/1.0 remains normative and unchanged during the initial Phase 2 foundation work.
- No existing Workbench v0.5.4, Python kernel baseline, archived release, adapter contract, or Phase 1 registry is silently redefined.
- Any required canonical change must be proposed separately, versioned, migrated, and tested. A new reasoning capability must not be smuggled into an old field or enum.
- Native packages and semantic profile versions remain independently versioned.

### 3.2 Structure before prose

- The semantic graph, typed references, ordered operands, definitions, contexts, assertions, evidence, and unresolved records are the reasoning inputs.
- Text summaries and natural-language explanations are generated views of structured results, not the authoritative result.
- A model-generated sentence is not a valid derivation merely because it sounds plausible.

### 3.3 Keep the semantic status axes independent

Interpretation, validation, assertion epistemic status, evidence alignment, evidence support, relation verification, and derivation status answer different questions. They must remain separate.

In particular:
- a valid document is not necessarily a correct interpretation;
- a resolved expression is not necessarily asserted;
- a source assertion is not necessarily true;
- an exact quote is not semantic entailment;
- a SUPPORTS or CONTRADICTS relation label is not proof that the relation holds;
- a derivation trace records how a result was produced; it does not certify truth;
- model confidence is not a semantic status.

### 3.4 Rules must be explicit and versioned

- A rule must have an identifiable version, a defined applicability domain, explicit premises and constraints, and a precisely defined conclusion effect.
- Rule matching must respect typed identity, semantic kind, expression sort, operand order, role bindings, context, attribution, polarity, modality, quantifier scope, and temporal scope where relevant.
- A rule must not be inferred from a label alone. Relation names do not silently imply symmetry, inverses, transitivity, causality, or other closure properties.
- An unregistered, ambiguous, incompatible, or untested rule is not executable.
- The first rule engine is deterministic. Generative models may propose candidate interpretations or rules later, but proposals cannot bypass formal validation and benchmark gates.

### 3.5 Evidence must not be overstated

- Source-span alignment, semantic support, entailment under a rule system, corroboration by independent sources, and external verification are distinct assessments.
- Evidence can be aligned but irrelevant, supportive without being conclusive, conflicting, or insufficient.
- Repeated quotations from the same underlying source are not automatically independent corroboration.
- No truth or verification status is promoted merely because an inference completed successfully.

### 3.6 Open-world caution and explicit incompleteness

- Absence of a record is not evidence of its negation unless a specific, validated closed-world rule applies to a declared data domain.
- Unknown, unresolved, ambiguous, unsupported, conflicting, and incomplete remain distinct.
- A result may be partial. It must say what was established, what was not established, and why.
- Resource budgets may be used as execution controls, but never as semantic complexity limits. A resource stop must produce an explicit incomplete result and diagnostics; it must not silently truncate semantic operands, nodes, candidate meanings, or conclusions.

### 3.7 Reproducibility and auditability

Every rule execution must be reproducible from the recorded input snapshot, rule and registry versions, configuration, and deterministic execution semantics. Each produced conclusion must link to the derivation that generated it. Ordering and repetition in provenance must be preserved where meaningful.

No human-review gate is required by this roadmap. Automated validation, deterministic tests, benchmark evaluation, and explicit machine-readable diagnostics are the acceptance mechanisms.

## 4. Core terminology

The following terms are used consistently in Phase 2 documents. These definitions constrain design; they do not add new USG-SEM/1.0 enum values.

| Term | Phase 2 meaning |
|---|---|
| **Interpretation** | A proposed or established mapping from source material into USG semantic structures. It may be resolved, ambiguous, unresolved, or partial. |
| **Expression** | A compositional representation of semantic content. An expression alone does not assert that its content holds. |
| **Assertion** | A record that presents an expression as a claim, with its origin, epistemic status, commitment, context, and provenance. |
| **Structural validation** | Deterministic checks that a document, reference graph, constructor, or record conforms to its declared contract. It does not establish semantic truth. |
| **Definition grounding** | Resolving a concept, frame, role, or relation reference to an exact registered identity and version. A label match alone is insufficient. |
| **Rule** | A versioned formal transformation with explicit premises, applicability constraints, and conclusion behavior. |
| **Inference** | Applying an enabled rule to eligible structures to produce a new structured result. An inference is a derivation, not a truth certificate. |
| **Derivation** | The provenance record linking inputs, outputs, rule identifiers, method, status, and diagnostics. |
| **Evidence alignment** | Whether a quote matches the exact declared source span. |
| **Semantic support** | An assessment of whether evidence supports a particular semantic expression or assertion under a stated method. |
| **Entailment** | A rule-system-relative relation: a conclusion follows from premises under a specified set of formal rules and assumptions. It does not establish that the premises are objectively true. |
| **Corroboration** | Independent evidence support from sources or observations whose independence has been established under an explicit policy. |
| **Verification** | A separate governed evaluation against an identified verification procedure or trusted external source. Ordinary rule execution does not perform verification. |
| **Conflict** | Two or more represented items or assessments that cannot all be accepted together under a specified comparison policy. Conflict is not automatically resolved by choosing the newest, most frequent, or highest-scored item. |
| **Unknown / unresolved / incomplete** | Unknown means the value or fact is not known; unresolved means a required interpretation or reference has not been resolved; incomplete means processing did not finish or required inputs were missing. They are not interchangeable. |

## 5. Proposed reasoning architecture

The following is the target logical architecture. It is a design boundary, not a claim that these modules already exist or that their final APIs have been frozen.

1. **Canonical document boundary** — accept and preserve a USG-SEM document; identify its profile, source snapshot, definitions, assertions, evidence, contexts, relations, unresolved items, and derivations.
2. **Structural and reference validator** — verify schema, IDs, reference target types, graph integrity, constructor rules, source offsets, and adapter coverage. Reject invalid inputs or return explicit diagnostics.
3. **Reasoning eligibility gate** — identify which expressions and assertions are eligible for a specific rule. Opaque, unresolved, ambiguous, malformed, or incompatible structures are not silently treated as complete premises.
4. **Definition and scope resolver** — resolve exact versioned definitions and validate variable binding, role binding, operator scope, context ancestry, attribution, and other rule-relevant boundaries.
5. **Versioned rule registry** — provide explicit rule identities, versions, definitions, applicability requirements, and test coverage. Registry data is distinct from semantic facts.
6. **Rule matcher and inference executor** — match premises and execute deterministic, registered rule behavior. It must not invent rules or coerce mismatched structures.
7. **Evidence and relation assessor** — evaluate only declared evidence/relation policies and keep alignment, support, contradiction, corroboration, and verification distinct.
8. **Derivation and result ledger** — preserve input/output references, rule versions, ordered provenance, execution configuration, diagnostics, and incomplete states.
9. **Query and explanation layer** — accept explicit reasoning goals and return structured answers with derivation paths, assumptions, evidence references, unresolved questions, and unsupported portions.
10. **Benchmark and regression harness** — evaluate each capability against frozen fixtures and negative/adversarial examples before it is enabled.

### 5.1 Processing boundary

The intended processing sequence is:

**validate → determine eligibility → ground definitions/scope/context → match rules → execute → validate outputs → record derivations → assess evidence/conflict under separate policies → render explanation**

A system component may short-circuit this sequence when a required condition fails. It must then return a diagnosable partial or unresolved result, not silently continue with an assumed value.

### 5.2 Reference implementation strategy

The Python kernel is the first reference implementation target because Phase 1 identifies it as the intended authoritative validation/storage target. This does not make Python package versions interchangeable or authorize changing historical versions. New capabilities must use additive, separately versioned packages and adapters.

The JavaScript Semantic Workbench remains a distinct frontend/implementation line. Integration is explicit and contract-driven; it is not assumed from shared repository location.

## 6. Phase 2 work sequence

Steps are sequential gates. A later step may be split into smaller implementation PRs, but it cannot bypass the preceding contract and evaluation requirements.

| Step | Name | Main deliverable | Exit condition |
|---|---|---|---|
| **2.1** | Semantic reasoning definitions and architecture | This foundation document and the detailed Step 2.1 definition | Terms, scope, status boundaries, architecture, and measurable evaluation strategy are documented and internally consistent. |
| **2.2** | Benchmark corpus and evaluator | Versioned positive, negative, adversarial, and incomplete-case fixtures; executable scoring/reporting harness | The corpus and evaluator validate reproducibly; scoring metrics and acceptance thresholds are fixed before any inference implementation. |
| **2.3** | Rule model and registry | Typed, versioned rule representation and registry format | Rule identity, versioning, variables, premises, constraints, scope/context conditions, conclusions, and test metadata are validated. |
| **2.4** | Rule semantics and safety contract | Formal execution semantics and rule eligibility policy | Applicability, matching, binding, conflict behavior, non-applicability, and failure outcomes have precise definitions and tests. |
| **2.5** | Definition, reference, scope, and context grounding | Deterministic resolver services | Exact identity/version resolution works; ambiguity, missing references, and scope mismatch remain explicit. |
| **2.6** | Deterministic inference executor | First executable reasoning engine and derivation ledger | Only enabled rules execute; every conclusion is traceable and reproducible; unsupported inferences are rejected or left unresolved. |
| **2.7** | Evidence support and conflict assessment | Separate evidence/relation evaluation policies | Alignment, support, contradiction, corroboration, and verification remain independent; no automatic truth promotion occurs. |
| **2.8** | Query and explanation interface | Structured query API and explainable result projection | Queries return grounded results, assumptions, derivations, evidence, conflicts, and unresolved items without inventing conclusions. |
| **2.9** | Kernel Lab reasoning interface | Interactive testing workflow for the new reasoning capabilities | Users can load fixtures, run declared reasoning tasks, inspect full traces, compare expected outcomes, and export results. |
| **2.10** | Phase 2 exit acceptance | Complete regression, benchmark, compatibility, and documentation gate | All declared Phase 2 capabilities pass their frozen acceptance suite; unsupported capabilities remain explicitly out of scope. |

## 7. Evaluation strategy

Evaluation must begin before the inference engine. The benchmark corpus in Step 2.2 will include at least these categories:

- **Representation and identity:** distinct mentions sharing an explicit referent; identical labels with different IDs; exact and mismatched typed references; unknown definition versions.
- **Scope and logic:** nested negation, quantifier scope, directed implication, conditionals, unless, concessive constructions, modality, attribution, temporal scope, and multiple roots.
- **Context:** actual-world versus hypothetical, fictional, conditional, negated, attributed-belief, and domain-model contexts.
- **Evidence:** exact and mismatched spans, Unicode offsets, aligned but irrelevant quotes, rule-supported evidence, conflicting evidence, repeated same-source evidence, and unknown support.
- **Inference:** valid rule applications, invalid premises, wrong variable bindings, missing premises, incompatible semantic kinds, unsupported closure assumptions, cycles, and duplicate derivation paths.
- **Partiality and failure:** ambiguous inputs, opaque constructors, unresolved references, unknown values, malformed records, interrupted execution, and resource exhaustion.
- **Adversarial cases:** tempting lexical overlaps, plausible but unlicensed conclusions, missing facts incorrectly treated as negation, and model proposals that conflict with the represented graph.

### 7.1 Required evaluation measures

The evaluator must report separate measures rather than hiding trade-offs in one aggregate score:

- **Inference soundness / precision:** proportion of emitted conclusions that are licensed by the declared premises and rules.
- **Supported-case coverage / recall:** proportion of benchmark conclusions that the implemented, enabled rule subset is expected to derive.
- **False-inference rate:** conclusions emitted when one or more required conditions are absent or contradicted.
- **Scope and binding accuracy:** correct handling of operator scope, argument roles, variables, contexts, and attribution.
- **Evidence-assessment accuracy:** correct distinction among alignment, support, dispute, corroboration, and unknown.
- **Provenance completeness:** each conclusion has a valid, reproducible derivation path and exact rule versions.
- **Preservation and partiality:** unsupported or unresolved content remains represented and is not silently discarded or upgraded.
- **Determinism:** identical input snapshots, rule versions, and configurations produce equivalent structured outputs and provenance, apart from explicitly non-semantic timestamps/IDs.
- **Resource behavior:** resource interruption is explicit and does not appear as a complete result.

Numerical thresholds will be set in Step 2.2 after the benchmark categories and scoring rules are specified. They must be fixed before enabling the inference executor; they must not be relaxed after a failed run merely to make a model or implementation pass.

## 8. Phase 2 acceptance conditions

Phase 2 cannot be declared complete solely because an engine or interface exists. The final gate must establish all of the following:

1. Every enabled rule is identified, versioned, documented, and covered by positive and negative tests.
2. No conclusion is emitted without valid input references, a matching rule version, satisfied premises, and applicable scope/context conditions.
3. Every conclusion has a complete derivation path; unsupported outputs are not presented as established results.
4. The benchmark meets thresholds fixed before implementation acceptance, including a strict false-inference gate.
5. Evidence alignment is never treated as entailment; rule support is never treated as objective truth; corroboration requires an explicit independence policy.
6. Ambiguous, unknown, unresolved, conflicting, unsupported, and incomplete cases remain distinguishable.
7. No silent semantic truncation or coercion occurs, including under resource interruption.
8. Existing Phase 1 contract, adapter, archive, and implementation-baseline regressions continue to pass.
9. The Kernel Lab, if included in the shipped scope, exposes traces and diagnostics rather than only a prose answer.
10. Documentation states exactly which reasoning rules and domains are supported and which remain unsupported.

## 9. Explicitly deferred capabilities

The following are not implied by establishing this roadmap and will not be claimed without separate specifications and evidence:

- unrestricted open-domain semantic accuracy or a generalized reasoner;
- objective truth determination from text alone;
- general-purpose natural-language entailment beyond explicitly tested rule subsets;
- autonomous ontology or rule learning and automatic promotion of learned definitions;
- distributed execution;
- multilingual semantic coverage;
- production readiness, security certification, or operational guarantees.

These may be considered in later phases only after Phase 2 produces a measurable, auditable reasoning foundation.

## 10. Compatibility and change control

- Phase 1 remains a completed baseline; Phase 2 work must not rewrite its completion record.
- USG-SEM/1.0 and its JSON Schema remain unchanged for this roadmap step.
- Existing model-only records (including Evidence, Context, ExpressionRelation, Definitions, and Derivation) are data models, not active reasoning engines.
- Rule IDs in current Evidence and Derivation records are opaque references. Phase 2 must not infer rule semantics from them. A first-class rule collection or new reference space requires its own versioned contract decision.
- Any new result status, rule reference type, provenance field, or reasoning output schema must be introduced through a separate versioned specification and migration plan.
- Existing Node.js action/runtime versions and immutable implementation baselines remain unchanged unless a future step explicitly requires and justifies a separate change.
- Each implementation step must have dedicated tests and a PR. Merge only after every required check on that exact PR head succeeds.

## 11. Current status

Steps 2.1–2.5 established the definitions, benchmark/evaluator, versioned rule model, formal rule semantics, and deterministic grounding services. Step 2.6 is merged and implements the first narrow deterministic execution subset: exact Modus Ponens and left conjunction elimination. A separate activation manifest enables only those handlers; the declarative registry and semantics contract remain unchanged, with registry-level execution disabled and rules still marked `SPECIFIED_NOT_EXECUTABLE`.

Step 2.7 is merged and adds the separate `USG-EVIDENCE-ASSESSMENT/1.0.0` ledger. It computes exact source-span alignment, detects only direct opposite-polarity conflicts under exact context/commitment/attribution scope, and preserves semantic-support and relation labels as declarations rather than proof. Multiple source records do not imply independence; corroboration remains NOT_ESTABLISHED without proven independence; external verification declarations remain DECLARED_UNVERIFIED unless a trusted verifier and procedure are actually bound and run. No truth promotion or conflict winner selection occurs.

**Next implementation step:** Phase 2 Step 2.8 — query and explanation interface. It must accept explicit structured goals, return grounded candidates with complete derivation and evidence/conflict projections, distinguish established results from declared/unverified information, and expose unresolved, unsupported, ambiguous, and incomplete outcomes without generating unlicensed conclusions.
