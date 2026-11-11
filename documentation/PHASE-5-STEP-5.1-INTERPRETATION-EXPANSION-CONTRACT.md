# Phase 5 — Step 5.1: Interpretation Expansion Contract

**Status:** FROZEN FOR IMPLEMENTATION  
**Contract:** `USG-INTERPRET/0.2.0`  
**Previous contract:** `USG-INTERPRET/0.1.0` remains immutable and regression-protected  
**Semantic interchange:** `USG-SEM/1.0` remains normative and unchanged  
**Canonical persistence:** the existing Phase 3 SQLite store remains the only canonical document store  
**Language profiles:** standard written English (`en`) and Modern Standard Arabic (`ar`), independently evaluated  
**Execution:** deterministic, offline baseline; optional model adapters cannot bypass validation  
**Acceptance:** automated tests and frozen benchmark fixtures; no runtime human-review gate

## 1. Decision and compatibility boundary

Phase 5 creates an additive interpretation line. The existing `tools/usg_interpretation_v0_1_0` package, its fixtures, and the six-case Phase 4 benchmark are frozen. The new implementation MUST use a separate versioned package, `tools/usg_interpretation_v0_2_0`, and MUST identify its output as `USG-INTERPRET/0.2.0`.

The contract version is independent of the USG-SEM profile and Python package version. A new interpretation capability does not justify changing `USG-SEM/1.0`. If an output cannot be represented without loss, the interpreter MUST preserve it in a versioned interpretation envelope and return a partial/unsupported result; a schema/profile proposal requires a separate decision and conformance suite.

The Phase 5A–5Y native Python model/document-adapter work is a distinct implementation stream. Its existing packages, versions, fixtures, and workflows MUST remain intact. Phase 5 interpretation work may reuse stable public APIs only through explicit imports and tests; it MUST NOT silently rewrite, rename, or conflate those releases with the new interpretation contract.

## 2. Scope

Phase 5 incrementally expands the bounded Phase 4 interpreter for explicitly enumerated English and MSA Arabic constructions. The initial implementation target is not unrestricted natural-language understanding. A construction is enabled only after its benchmark and adversarial acceptance tests pass.

The ordered capability families are:

1. Versioned lexical entries, lexical sense candidates, and explicit morphology analyses.
2. Sentence-internal clause segmentation and richer syntactic candidates.
3. Recursive semantic composition for supported nested clauses, predicates, arguments, and modifiers.
4. Explicitly scoped negation, modality, tense, aspect, and quantifier operators.
5. Group-preserving coordination of supported predicates, arguments, and clauses.
6. Multi-sentence proposition, attribution, discourse, and conservative reference-candidate links.
7. Persistent, versioned resource manifests and deterministic retrieval backed by SQLite.
8. API, CLI, and Kernel Lab inspection, persistence, replay, and export of accepted artifacts.

The list defines implementation targets, not current support. Each construction remains disabled until the relevant step passes.

## 3. Explicit exclusions

The following are not Phase 5 acceptance claims:

- unrestricted English/Arabic parsing, dialectal Arabic, arbitrary code-switching, or universal language coverage;
- objective truth determination, external fact verification, or source credibility scoring;
- identity resolution based solely on repeated names, lexical similarity, embeddings, or association strength;
- automatic creation, merging, or silent promotion of canonical concepts, definitions, frames, or rules;
- unbounded metaphor, sarcasm, humor, idiom, cultural inference, or pragmatic interpretation without a separately tested construction profile;
- mandatory LLMs, paid APIs, cloud services, or network access;
- distributed multi-controller execution or a public multi-user service;
- modification of archived releases, historical package directories, the JavaScript Semantic Workbench line, or the Phase 5A–5Y native model stream;
- runtime human review, manual approval queues, or human intervention as a required acceptance step.

## 4. Interpretation envelope

The pipeline result is separate from the USG-SEM/1.0 document. Every result MUST include:

- `pipeline_contract`: exactly `USG-INTERPRET/0.2.0`;
- `pipeline_version`: implementation package version;
- `language_profile`: versioned language profile identifier;
- `completion_status`: one of the statuses below;
- `source_ref`: immutable source snapshot identifier;
- `document`: complete or partial USG-SEM/1.0 document when representable;
- `stages`: ordered stage outcomes, implementation versions, and resource identifiers/digests;
- `diagnostics`: stable machine-readable codes, explanations, and source spans where applicable;
- `alternatives`: retained candidates with ranking metadata that is never described as calibrated probability;
- `resource_limits`: declared budgets and explicit interruption state.

### 4.1 Completion statuses

| Status | Normative meaning |
|---|---|
| `COMPLETE` | All source content is covered by enabled constructions and assembled without unresolved semantic content. |
| `PARTIAL` | Some content is interpreted, while one or more spans or structures remain unresolved/unsupported. |
| `AMBIGUOUS` | Multiple materially distinct candidates remain; no unique canonical reading is justified. |
| `UNSUPPORTED` | Input is valid but outside the enabled language/construction profile. |
| `INVALID_INPUT` | Request or source envelope violates input requirements. |
| `INCOMPLETE_RESOURCE_LIMIT` | A declared time, memory, or candidate budget interrupted processing; partial artifacts are retained. |
| `FAILED_VALIDATION` | Candidate output failed deterministic validation and MUST NOT be persisted as accepted semantic output. |

The top-level status MUST be conservative. A pipeline finishing successfully does not imply semantic completeness. A downstream stage MUST NOT upgrade a partial, ambiguous, or unsupported upstream result without a documented resolution rule and source-grounded evidence.

## 5. Stage and artifact contracts

Each stage consumes immutable, versioned input artifacts and emits a versioned result with status, diagnostics, provenance, and alternatives. The logical order is:

1. Source ingestion and immutable snapshot.
2. Document, paragraph, sentence, and clause segmentation.
3. Lexical and morphology candidate generation.
4. Constituent/dependency/construction candidate generation.
5. Recursive semantic composition.
6. Operator-scope and coordination composition.
7. Mention and referent-candidate analysis.
8. Discourse and attribution composition.
9. Assertion/evidence projection.
10. Validation, envelope assembly, and optional canonical persistence.

Stages MAY expose candidate alternatives and MAY abstain. They MUST NOT fabricate missing words, silently drop input spans, flatten nested scope, or infer truth. Downstream constraints may request bounded reconsideration of upstream candidates, but every candidate and derivation must remain inspectable.

## 6. Source fidelity and provenance

1. Preserve the exact input string before normalization, tokenization, or model processing.
2. Offsets are zero-based, end-exclusive Unicode code-point offsets into that exact string.
3. For every exact source span, enforce `source[start:end] == surface_text`.
4. Normalized strings, case-folded forms, lemmas, morphology, transliterations, and parser-internal strings are derived values with explicit source mappings; they never replace the original.
5. Every semantic node MUST identify the lexical/syntactic candidate and source spans that licensed it.
6. Reprocessing creates a new result/revision; it never overwrites the immutable source snapshot or erases prior alternatives.
7. Unicode combining marks, supplementary code points, Arabic diacritics, punctuation, bidirectional text, CRLF/LF, and repeated whitespace MUST be covered by boundary tests.

## 7. Semantic composition and operator scope

- Semantic expressions are typed and graph-referenced; operands retain order where the relation is order-sensitive.
- Named semantic roles MUST remain distinct from syntactic positions.
- Nested clauses and modifiers MUST remain nested; flattening into keyword lists is forbidden.
- Negation, modality, tense, aspect, and quantification MUST be represented as explicit operators or typed features with explicit scope/attachment references.
- A surface keyword alone does not establish an operator or its scope.
- Coordination MUST preserve every conjunct/disjunct and grouping. If grouping is ambiguous, retain alternatives or abstain; never discard a branch.
- Candidate ranking, frequency, context, activation, and association weight are retrieval metadata, not truth, identity, entailment, modality, or calibrated probability.

## 8. Reference, discourse, and attribution policy

Mention detection, referent candidates, resolved referents, discourse links, and attribution are separate states. Repeated surface forms or lexical similarity may produce retrieval candidates only. A resolved identity requires a deterministic, construction-specific rule that passes adversarial fixtures. Unresolved antecedents remain unresolved. Discourse markers are not themselves proof of causal, temporal, conditional, or contrastive relations; relation scope and endpoints must be represented and source-grounded. Quoted content and speaker attribution MUST remain distinct from author commitment and truth.

## 9. Resource lifecycle and persistence

- SQLite remains the sole authoritative store for canonical semantic documents and immutable revisions.
- Resource catalogues may be persisted in SQLite with explicit resource IDs, versions, digests, provenance, and integrity checks.
- Canonical definitions, lexical realizations, grammar patterns, semantic frames, discourse resources, provisional associations, and retrieval metadata MUST be distinct resource classes.
- Search indexes, caches, rankings, activation scores, and usage counts are derived/rebuildable data and cannot become a second semantic source of truth.
- Association activation can prioritize retrieval but cannot create definitions, merge concept identity, prove coreference, or establish entailment.
- Resource updates are additive and versioned. Existing canonical definitions and historical document revisions are immutable.
- A resource snapshot MUST be reproducible from its manifest and content digest.

## 10. Benchmark policy and quality gates

Step 5.2 establishes the versioned corpus and evaluator before capability expansion. For each enabled construction and each language independently, the planning minimum is 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary fixtures. An insufficient denominator MUST be reported as insufficiently measured, never as a perfect score.

Required metrics are reported by language, construction, and stage: source preservation/span alignment; segmentation; lexical/morphology; syntax/roles; semantic graph/operand binding; operator scope; coordination grouping; mention/reference; discourse/attribution; ambiguity retention/abstention; schema/reference validity; unsupported inference/false assertion; deterministic replay; runtime/memory/resource-limit behavior.

Initial acceptance thresholds:

- exact source preservation: 100%;
- validity of every emitted source span: 100%;
- structural/schema/reference validity of accepted documents: 100%;
- silent source or semantic loss: zero;
- unsupported inference in frozen adversarial fixtures: zero;
- enabled construction precision: at least 0.95 per language;
- enabled construction recall: at least 0.90 per language;
- ambiguous/out-of-profile fixtures: 100% retain ambiguity or explicit partial/unsupported status;
- Phase 1–4 and Phase 5A–5Y compatibility regressions: 100% pass.

A construction that fails remains disabled. Thresholds MUST NOT be weakened to make a release pass. Aggregate scores MUST NOT hide a critical per-language or per-construction failure.

## 11. Determinism, resource budgets, and security

The deterministic baseline MUST run offline with pinned test dependencies. Resource budgets must be explicit and tested. Exceeding a budget returns `INCOMPLETE_RESOURCE_LIMIT` with preserved partial artifacts and diagnostics. No untrusted text, model output, or resource content is executed as code. Resource parsing and imports must be bounded and validate types, sizes, identifiers, digests, and references before use.

## 12. Compatibility requirements for every Phase 5 PR

Every implementation PR MUST:

- preserve `specifications/USG-SEM-1.0.md` and `specifications/usg-sem-1.0.schema.json`;
- preserve Phase 1–4 contracts, tests, fixtures, and exit reports;
- preserve `tools/usg_interpretation_v0_1_0` and its expected behavior;
- preserve Phase 5A–5Y native model/document-adapter packages, workflows, and fixtures;
- preserve archives and historical Python/JavaScript implementation directories;
- keep SQLite as the sole canonical document store;
- avoid mandatory paid/network model dependencies and runtime human-review gates;
- publish explicit enabled/disabled construction coverage and reproducible test commands.

## 13. Step 5.1 acceptance checklist

Step 5.1 is accepted when all are true:

1. This contract is merged and identified as frozen.
2. The new `USG-INTERPRET/0.2.0` package boundary is explicit and does not modify 0.1.0.
3. USG-SEM/1.0 and SQLite decisions are explicit.
4. Phase 5A–5Y compatibility is explicitly protected.
5. Completion statuses, source fidelity, composition, scope, references, resources, and benchmark gates are normative.
6. A contract regression test verifies the frozen version and critical invariants.
7. The Step 5.1 workflow and Phase 4 regression workflow pass on the exact PR head.

## 14. Next step

After Step 5.1 merges, begin **Step 5.2 — Expanded Benchmark Corpus and Evaluator Foundation**. Freeze the corpus, annotation format, scoring definitions, denominators, and baseline report before implementing additional interpretation capabilities.
