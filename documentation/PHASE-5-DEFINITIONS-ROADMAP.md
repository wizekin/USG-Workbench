# USG Phase 5 — Definitions and Roadmap

**Status:** IN PROGRESS — Steps 5.1 and 5.2 accepted; Step 5.3 lexical and morphology resources under implementation.  
**Target interpretation contract:** `USG-INTERPRET/0.2.0` (independent of the semantic interchange profile).  
**Current accepted baseline:** `USG-INTERPRET/0.1.0`, bounded offline demonstrator.  
**Normative semantic interchange:** `USG-SEM/1.0` remains unchanged unless a separately versioned profile is justified by a demonstrated representation gap.  
**Canonical persistence:** Phase 3 SQLite store remains authoritative.  
**Prerequisites:** Phase 1–4 accepted contracts and regression suites.  
**Primary objective:** evolve the tiny Phase 4 demonstrator into a broader, compositional, source-grounded interpreter for explicitly tested English and Modern Standard Arabic constructions.

## 1. Purpose and transition from Phase 4

Phase 4 established a working end-to-end boundary from raw text to a source-preserving USG semantic document. Its accepted scope is intentionally narrow: a tiny injected lexicon, one three-word clause, English SVO and MSA Arabic SVO/VSO patterns, a small set of predicate frames, conservative mention/discourse handling, and SQLite persistence.

Phase 5 expands that foundation in controlled, measurable increments. It is not a rewrite of the accepted pipeline and is not a claim of unrestricted natural-language understanding. The goal is to increase the number and complexity of constructions USG can interpret while preserving exact source evidence, explicit uncertainty, semantic roles, operator scope, and deterministic validation.

The main capability gaps carried forward from Phase 4 are:

- tiny lexical coverage and minimal morphology;
- one-clause-only composition;
- no nested or multi-clause syntax;
- no enabled negation, modality, quantifier, tense, or aspect scope;
- no enabled coordination;
- no general cross-sentence reference/coreference;
- discourse markers are detected, but their full semantic scope and relations are not composed;
- lexical, grammar, frame, and association resources are mostly injected or in-memory rather than managed as a durable, reproducible resource catalogue;
- the six-case Phase 4 benchmark is a smoke/acceptance corpus, not a broad capability evaluation.

Phase 5 must address these gaps without weakening the conservative interpretation policy.

## 2. Phase 5 goals

1. Expand lexical and morphological coverage using versioned, inspectable resources for English and MSA Arabic.
2. Support sentence-internal clause structure, nested constructions, and multiple semantic propositions.
3. Represent negation, modality, tense, aspect, quantification, and coordination with explicit operators and scope.
4. Compose supported multi-sentence documents while retaining source boundaries, attribution, discourse links, and unresolved references.
5. Turn semantic resources into reproducible, versioned assets with provenance and deterministic retrieval/update behavior.
6. Make the expanded pipeline observable and testable through the existing local API and Kernel Lab.
7. Establish a substantially stronger benchmark with per-language, per-construction metrics and adversarial negative cases.

## 3. Non-goals and exclusions

Phase 5 does not attempt to deliver:

- unrestricted English or Arabic understanding, dialectal Arabic, arbitrary code-switching, or universal language coverage;
- objective truth determination, external fact verification, or source credibility scoring;
- identity resolution from repeated names, lexical similarity, embeddings, or association strength alone;
- automatic invention or silent promotion of canonical concepts, definitions, or rules;
- unrestricted metaphor, sarcasm, humor, cultural or pragmatic inference without a dedicated tested construction profile;
- a mandatory LLM, paid API, cloud service, or network dependency;
- distributed multi-controller execution or a public multi-user service;
- a replacement for the JavaScript Workbench v0.5.4 or historical Python packages;
- runtime human review, manual approval queues, or human intervention as an acceptance prerequisite.

Model-assisted components may propose candidates through the existing replaceable adapter, but the deterministic contracts, provenance checks, and validators remain authoritative.

## 4. Frozen architectural decisions

### 4.1 Preserve the semantic interchange contract

- Continue emitting `USG-SEM/1.0` wherever its existing structures can represent the result.
- Keep pipeline stages, alternatives, diagnostics, processing revisions, and completion statuses in the interpretation envelope or versioned extensions, not as unreviewed changes to the normative schema.
- If a genuine semantic representation gap is discovered, document it with concrete examples and propose a separate profile/version with migration and conformance tests. Do not quietly alter USG-SEM/1.0.

### 4.2 Preserve SQLite as the canonical persistence authority

- SQLite remains the only authoritative persistence backend for canonical semantic documents and immutable document revisions.
- Any persistent lexical/grammar/frame/association catalogue introduced in Phase 5 must have explicit versioning, provenance, integrity checks, and deterministic rebuild/migration behavior.
- Search indexes, caches, candidate rankings, and activation scores are derived/rebuildable data; they cannot become a second semantic source of truth.
- No alternative database migration is part of this roadmap.

### 4.3 Additive versioned implementation

- Introduce `USG-INTERPRET/0.2.0` as a new pipeline contract; preserve the `0.1.0` behavior and fixtures as a regression baseline.
- Add new versioned packages/resources rather than mutating archived or historical releases.
- Keep the JavaScript Workbench and Python kernel as distinct implementation lines. Interoperability must remain explicit and tested.

### 4.4 Source fidelity and provenance

- Preserve the exact input string, Unicode code-point offsets, source digest, and original sentence/clause boundaries.
- Every emitted span must satisfy exact source-slice alignment.
- Every semantic node must trace to the lexical/syntactic candidates and source spans that licensed it.
- Derived text, normalization, lemmas, morphology, and transliteration remain separate artifacts with mappings to the original source.
- Reprocessing creates a new processing result/revision; it never overwrites the original source snapshot or silently erases prior alternatives.

### 4.5 Conservative interpretation

- Unknown words, unsupported constructions, ambiguous syntax, unresolved references, and resource-budget interruptions remain explicit.
- A construction is enabled only after its positive, negative, ambiguous, boundary, and adversarial fixtures pass its acceptance threshold.
- Candidate rank, model confidence, frequency, context, and association weight are not truth, identity, entailment, or calibrated probability.
- A partial result must never be labelled complete merely because the pipeline finished.

## 5. Target Phase 5 architecture

```text
Immutable source snapshot
        |
        v
Document / sentence / clause segmentation
        |
        v
Expanded lexical + morphology candidates
        |
        v
Constituent / dependency / construction candidates
        |
        v
Nested compositional semantic graph
        |
        +------> scoped operators (NOT, modality, tense, aspect, quantifiers)
        |
        +------> coordination and multi-clause composition
        |
        +------> mention / referent candidates
        |
        v
Multi-sentence discourse and context composition
        |
        v
Assertion / attribution / evidence projection
        |
        v
USG-SEM validation + explicit diagnostics / alternatives
        |
        v
Canonical SQLite persistence, query, export, Kernel Lab
```

This is a logical pipeline, not a requirement for one process or one model per stage. Stages may iterate when downstream constraints expose an upstream ambiguity, but every candidate and resolution path must remain traceable.

## 6. Ordered Phase 5 roadmap

Steps are sequential acceptance gates. Each step receives a dedicated definition, implementation, tests, and pull request. A later step may not bypass an earlier failed contract. Automatic merge is permitted only when the exact PR head passes all required checks and compatibility gates.

| Step | Name | Main deliverable | Exit condition |
|---|---|---|---|
| **5.1** | Phase 5 interpretation expansion contract | Freeze target constructions, status behavior, resource boundaries, compatibility rules, and acceptance metrics | Contract is explicit and reviewed against Phase 4 code and USG-SEM/1.0; no implementation begins before merge. |
| **5.2** | Expanded benchmark corpus and evaluator foundation | Versioned English/MSA Arabic corpus, partial/gold annotations, negative and adversarial fixtures, per-construction evaluator | Corpus distinguishes supported, ambiguous, unsupported, and unresolved cases; reports per-language and per-construction results; Phase 4 six-case baseline remains immutable. |
| **5.3** | Versioned lexical and morphology resources | Replace demo-only lexical coverage with modular, provenance-bearing lexical resources and explicit morphology candidates | Unknown forms remain unresolved; ambiguous senses remain alternatives; morphology and token spans are source-aligned; resource versions/digests are reproducible. |
| **5.4** | Clause segmentation and richer syntactic analysis | Sentence-internal clause segmentation, constituent/dependency candidates, attachments, and syntax alternatives | Nested and multi-clause fixtures preserve exact spans, clause boundaries, role candidates, and ambiguity without flattening or guessing. |
| **5.5** | Nested compositional semantic construction | Recursive composition of supported clauses, predicates, arguments, modifiers, and embedded propositions into typed USG expression graphs | Role identity, operand order, nesting, graph references, and provenance validate; unsupported structures remain explicit. |
| **5.6** | Scoped operators and grammatical features | Explicit negation, modality, tense, aspect, and quantifier operators with language-specific realization mappings | Minimal pairs and scope adversarial fixtures distinguish operator attachment and scope; no keyword-only or sentence-wide scope shortcuts. |
| **5.7** | Coordination and multi-clause composition | Composition of supported conjunction/disjunction and coordinated predicates/arguments/clauses | Every conjunct/disjunct is retained with correct grouping and scope; mixed or ambiguous coordination abstains rather than dropping branches. |
| **5.8** | Multi-sentence discourse and reference | Sentence-to-sentence proposition links, attribution, temporal/conditional/contrast relations, and conservative pronoun/reference candidates | Links identify source and target spans/sentences; candidate identity is distinct from resolved identity; unresolved antecedents remain unresolved. |
| **5.9** | Persistent semantic resource catalogue and association retrieval | Versioned SQLite-backed resource manifests/catalogue for lexical, grammar, frame, discourse, and provisional association assets; deterministic active/secondary retrieval | Resource snapshots are reproducible and integrity-checked; activation/ranking is derived metadata; updates cannot rewrite canonical definitions or semantic history. |
| **5.10** | Integrated API, CLI, and Kernel Lab expansion | Expose stage artifacts, alternatives, diagnostics, resource versions, and document composition through the existing local application and UI | API, CLI, and UI share the same application services and SQLite store; export/replay is deterministic; no parallel browser database is introduced. |
| **5.11** | Expanded benchmark, performance, and integrated exit acceptance | Frozen end-to-end evaluation, resource-limit tests, Phase 1–4 regression, packaging, and published limitations | Every enabled construction passes per-language thresholds on the exact merged main commit; disabled constructions remain explicitly unsupported. |

### 6.1 Dependency and sequencing notes

- Step 5.2 comes before capability expansion so new grammar is benchmark-driven rather than selected after observing implementation behavior.
- Step 5.3 supplies the lexical candidates needed by syntax and semantic composition.
- Steps 5.4–5.5 establish clause structure and recursive composition before operators or coordination are enabled.
- Step 5.6 depends on nested composition because scope cannot be validated over a flat representation.
- Step 5.7 depends on the same explicit grouping and scope model.
- Step 5.8 depends on stable sentence/clause propositions and reference candidate contracts.
- Step 5.9 can be designed early but must not change SQLite canonical document semantics or introduce a competing backend.
- Step 5.10 integrates only capabilities already accepted by their own tests.
- Step 5.11 is the final gate; passing schema validation alone is insufficient.

## 7. Benchmark and acceptance policy

The Phase 4 six-case corpus remains frozen as a historical baseline. Phase 5 adds a new versioned benchmark; it does not rewrite old fixtures or thresholds.

### 7.1 Required fixture families

For every proposed enabled construction and each language independently, include:

- positive examples;
- negative and adversarial minimal pairs;
- ambiguous and underspecified examples;
- boundary cases, fragments, malformed/noisy inputs, and out-of-profile cases;
- nested and multi-clause cases where relevant;
- exact-span edge cases: Unicode supplementary characters, combining marks, Arabic diacritics, punctuation, tabs, CRLF/LF, repeated whitespace, and mixed-direction text;
- examples that distinguish syntactic form from semantic role, operator scope, attribution, and discourse relation.

As a planning minimum, target at least 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary fixtures per enabled construction per language. If a construction cannot reach a defensible fixture count, report the metric as insufficiently measured and keep the construction disabled; do not report an empty denominator as 100%.

### 7.2 Required metrics

Report separately by language, construction, and relevant stage:

1. exact source preservation and span alignment;
2. segmentation and tokenization precision/recall;
3. lexical candidate and morphology quality;
4. syntactic structure, attachment, and role accuracy;
5. semantic expression, operand, and role-binding accuracy;
6. operator attachment and scope accuracy;
7. coordination grouping and completeness;
8. mention detection and reference-link accuracy;
9. discourse and attribution accuracy;
10. ambiguity retention and abstention quality;
11. schema/reference validity and lossless round-trip;
12. unsupported inference and false assertion rates;
13. runtime, memory, resource-limit behavior, and deterministic replay.

### 7.3 Initial quality gates

- exact source preservation: **100%**;
- validity of every emitted source span: **100%**;
- structural/schema/reference validity of accepted documents: **100%**;
- silent source or semantic loss: **0**;
- accepted unsupported inference in the frozen adversarial corpus: **0**;
- per enabled construction and language: precision **>= 0.95**, recall **>= 0.90**, unless a stricter existing contract applies;
- ambiguous/out-of-profile fixtures: **100%** must retain ambiguity or return an explicit partial/unsupported result rather than an unjustified unique interpretation;
- Phase 1–4 regression and frozen baseline checks: **100%** pass.

A construction that fails remains disabled. Thresholds must not be weakened to obtain a passing release. Precision, recall, fixture counts, and denominators must be published; aggregate scores must not hide a critical failure in one language or construction.

## 8. Resource and association lifecycle

The semantic resource system must keep distinct:

- **canonical definitions:** stable concept/frame/role/relation meanings with explicit versions and provenance;
- **lexical realizations:** language-specific forms, lemmas, morphology, and sense candidates;
- **grammar patterns:** language-specific constructions and their typed semantic mappings;
- **associations:** provisional co-occurrence, functional, and contextual links;
- **retrieval metadata:** usage counts, recency/decay, activation, ranking, and cache state.

Association activity may prioritize retrieval, but it cannot create definitions, merge concept identities, prove coreference, or establish entailment. Any promotion from a provisional association to a canonical resource requires a separately specified deterministic validation rule and immutable versioned result. No learned update may delete or rewrite a canonical definition.

## 9. Compatibility and preservation checklist

Every Phase 5 implementation PR must verify:

- `specifications/USG-SEM-1.0.md` and its schema remain unchanged unless a separately approved major-profile proposal explicitly says otherwise;
- Phase 1–4 contracts and acceptance artifacts remain intact;
- Phase 4 `USG-INTERPRET/0.1.0` fixtures and expected behavior remain regression-protected;
- SQLite remains the sole canonical persistence backend;
- archived ZIPs and historical version directories remain unchanged;
- the JavaScript Workbench and Python kernel remain separate implementation lines;
- no paid model/API or network access is required for deterministic baseline tests;
- no runtime human review or manual approval is introduced;
- documentation accurately states enabled and disabled construction coverage.

## 10. Phase 5 exit criteria

Phase 5 is complete only when:

1. All 5.1–5.11 steps are merged and their exact-head workflows pass.
2. The new interpretation contract and benchmark versions are published.
3. Every enabled construction passes the frozen per-language/per-construction thresholds.
4. Nested, operator, coordination, and multi-sentence structures preserve exact source provenance and semantic scope.
5. Unknown, ambiguous, unsupported, and resource-limited cases remain explicit and lossless.
6. The persistent resource catalogue is deterministic, integrity-checked, and subordinate to SQLite canonical document storage.
7. The integrated Kernel Lab can inspect, persist, query, replay, and export the expanded interpretation artifacts.
8. All Phase 1–4 regressions, package checks, and historical compatibility checks pass.
9. A completion record lists actual enabled constructions, benchmark counts/results, known limitations, and the exact accepted main commit.

Phase 5 completion will mean a broader, benchmarked interpreter for the explicitly enabled English and MSA Arabic constructions. It will not mean unrestricted language understanding, objective truth determination, human-equivalent reasoning, or AGI.

## 11. Immediate next implementation step

**Steps 5.1 and 5.2 are accepted.** Their frozen contract and benchmark foundation are documented in [Step 5.1](PHASE-5-STEP-5.1-INTERPRETATION-EXPANSION-CONTRACT.md) and [Step 5.2](PHASE-5-STEP-5.2-BENCHMARK-FOUNDATION.md). Step 5.3 is implementing the first provenance-bearing lexical and morphology resources. The benchmark gold annotations remain evaluation targets, not claims of runtime support.
