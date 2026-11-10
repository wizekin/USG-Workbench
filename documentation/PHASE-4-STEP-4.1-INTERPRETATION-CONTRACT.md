# Phase 4 — Step 4.1: Interpretation Definitions and Acceptance Contract

**Status:** DEFINITION FROZEN FOR IMPLEMENTATION  
**Contract version:** `USG-INTERPRET/0.1.0` (pipeline contract; not a USG-SEM profile)  
**Semantic interchange:** `USG-SEM/1.0` unchanged  
**Canonical persistence:** Phase 3 SQLite store unchanged  
**Baseline:** Phase 1–3 and all archived releases remain regression-protected

## 1. Decision summary

Step 4.1 freezes the first bounded interpretation profile so that implementation can proceed without claiming unrestricted language understanding.

| Decision | Frozen choice |
|---|---|
| Initial language profiles | Standard written English (`en`) and Modern Standard Arabic (`ar`); separate language-specific analysis resources |
| Initial execution mode | Offline/local, deterministic baseline; no paid service or model is required |
| Pipeline contract | `USG-INTERPRET/0.1.0`, versioned independently of USG-SEM and package releases |
| Canonical output | Complete USG-SEM/1.0 document where representable; otherwise a source-preserving partial result with explicit unresolved/unsupported diagnostics |
| Source offsets | Zero-based, end-exclusive Unicode code-point offsets into the exact preserved source string |
| Persistence | Existing Phase 3 SQLite application and immutable document revisions |
| Model assistance | Optional later adapter only; cannot bypass deterministic validation |
| Acceptance | Frozen, machine-readable fixtures and automated tests; no runtime human-review gate |
| Truth policy | Interpretation describes source content; it never promotes it to objective truth |

The language decision is grounded in the repository's existing v0.4.0/v0.5.0 interpretation module, which explicitly documents an English/Arabic subset, and its lexical-resource contract, which recognizes `en` and `ar`. These are historical implementation assets, not accepted Phase 4 components. They justify selecting these two languages for a measured first profile, but do not justify copying legacy behavior or claiming complete language coverage.

Arabic acceptance is limited to Modern Standard Arabic. Dialects, code-switching, transliteration, and mixed-script normalization are outside the initial profile unless a fixture explicitly tests safe preservation and abstention. English acceptance is limited to standard written English constructions enumerated by the benchmark. Neither profile claims unrestricted parsing.

## 2. Scope and non-goals

### 2.1 In-scope first-profile construction families

The first profile will be built incrementally and only enabled when its step-specific fixtures pass:

1. Plain declarative clauses with supported argument order.
2. Common nominal mentions and simple noun phrases.
3. A bounded set of explicitly registered predicates and their typed roles.
4. Supported present/past tense and simple aspect distinctions where resources establish them.
5. Explicit negation with tested scope.
6. Basic modality only where the relevant operator and scope are represented.
7. Simple coordination only where all conjuncts are retained.
8. Direct quotation/attribution only after the discourse and assertion steps establish their contracts.
9. Pronouns and cross-sentence reference only after the mention/reference step establishes safe candidate-link behavior.
10. Fragments, malformed input, unknown words, unsupported constructions, and ambiguity as first-class abstention cases.

This is a staged coverage list, not a statement that all items are implemented now. Each family is disabled by default until its own acceptance fixtures and adversarial cases pass.

### 2.2 Explicitly out of scope

- unrestricted English or Arabic understanding;
- dialectal Arabic, poetry, transliteration, and arbitrary code-switching;
- reliable sarcasm, humor, metaphor, idiom, cultural implication, or pragmatic inference without dedicated tested profiles;
- unrestricted named-entity linking or identity resolution;
- automatic invention or promotion of canonical definitions;
- truth determination, external fact verification, or source credibility scoring;
- silent repair of malformed or incomplete input;
- any model service as a required dependency;
- changing USG-SEM/1.0 or retroactively changing historical package behavior.

## 3. Interpretation result envelope

The interpretation API returns an envelope separate from the USG-SEM document. This avoids adding pipeline lifecycle statuses to the normative semantic schema.

Required envelope fields:

- `pipeline_contract`: exact pipeline contract identifier;
- `pipeline_version`: exact implementation version;
- `language_profile`: `en-standard-written/0.1.0` or `ar-msa-written/0.1.0`;
- `completion_status`: one of the statuses below;
- `source_ref`: identifier of the immutable source snapshot;
- `document`: complete or partial USG-SEM/1.0 document when one can be assembled;
- `stages`: ordered stage outcomes and version/resource provenance;
- `diagnostics`: structured codes, source spans, and explanations;
- `alternatives`: retained candidate structures with explicit ranking metadata, never mislabelled as probabilities;
- `resource_limits`: configured budget and whether it interrupted processing.

### 3.1 Completion statuses

| Status | Meaning |
|---|---|
| `COMPLETE` | All source content in the declared enabled construction scope was processed and assembled without unresolved semantic content. |
| `PARTIAL` | A valid portion was interpreted, while one or more spans remain unresolved or unsupported. |
| `AMBIGUOUS` | Multiple live interpretations remain and no unique canonical reading is justified. |
| `UNSUPPORTED` | The input is valid source text but the requested language/construction is outside the enabled profile. |
| `INVALID_INPUT` | The request or source envelope violates input requirements; the exact received payload is retained in diagnostics where safe. |
| `INCOMPLETE_RESOURCE_LIMIT` | A declared resource/time budget interrupted processing; partial output is retained and explicitly marked incomplete. |
| `FAILED_VALIDATION` | Candidate structures were generated but failed deterministic structural/profile validation; they are not persisted as accepted semantic output. |

A result may contain more than one diagnostic cause. The top-level status follows the most conservative applicable outcome; it must not hide partial or unresolved spans.

## 4. Stage contracts

Every stage accepts an immutable input artifact and emits a versioned output artifact. It must report its own status, resource version, source-span references, diagnostics, and alternatives. A stage may abstain; it may not fabricate missing information.

| Stage | Input | Required output | Forbidden shortcut |
|---|---|---|---|
| Source ingestion | Raw source string and declared language | Exact source snapshot, digest, source metadata | Unicode/whitespace normalization before snapshot or hashing |
| Segmentation | Exact source snapshot | Ordered document/paragraph/sentence/clause spans | Rewriting source or silently dropping punctuation/fragments |
| Lexical/morphological | Segments and language profile | Token spans, surface forms, lemmas and morphology candidates when supported | Treating unknown words as known concepts |
| Syntax | Tokens and grammar registry | One or more typed syntax candidates, explicit ambiguity | Treating dependency labels as semantic entailment |
| Semantic composition | Syntax candidates and semantic resources | Typed expressions, ordered operands, named roles, operator scope | Flattening roles, operators, or nested scope into keywords |
| Mention/reference | Source spans and semantic candidates | Mention records and candidate referent links | Identity from repeated labels, aliases, or similarity alone |
| Discourse/context | Sentence structures and candidate links | Attributed, temporal, conditional, contrast, and discourse links when supported | Context-only claims without source grounding |
| Assertion/evidence | Expressions, attribution, and source spans | Native assertion/evidence projections with independent alignment/support statuses | Promoting a description or quote alignment to truth |
| Validation/assembly | All stage artifacts | USG-SEM/1.0 document or explicit partial/unresolved result | Dropping unsupported material or mutating USG-SEM/1.0 |

## 5. Provenance and source fidelity

1. The exact original source string is stored unchanged before any processing.
2. Offsets are zero-based and end-exclusive Unicode code-point positions, consistent with USG-SEM/1.0.
3. Every token and span-bearing candidate must satisfy `source[start:end] == surface_text` where the record claims an exact surface match.
4. Normalized forms, case-folded forms, transliterations, lemmas, and parser-internal text are derived artifacts with their own mappings; they never replace source text.
5. Every generated expression must carry traceable provenance to the syntax/lexical candidate and source spans that licensed it.
6. Model output, if introduced later, records model identifier/version and relevant deterministic configuration. Model confidence is diagnostic metadata, never semantic modality or epistemic status.
7. Stage reruns append a new processing revision or artifact; they do not overwrite prior source snapshots or silently erase earlier alternatives.

## 6. Resource and ambiguity policy

- No arbitrary semantic caps or silent truncation.
- Resource budgets may bound wall time, memory, or candidate expansion. Exceeding a budget returns `INCOMPLETE_RESOURCE_LIMIT`, diagnostics, and preserved partial artifacts.
- Ambiguous lexical, syntactic, or referential cases remain ambiguous unless a declared, tested rule resolves them.
- Candidate ordering is not probability unless a separately versioned calibration contract proves that interpretation.
- Context and association scores may prioritize candidate inspection but cannot establish identity, entailment, assertion, or truth.
- Unsupported constructs remain in the source and are represented as unresolved/unsupported; a partial semantic graph must not masquerade as a complete interpretation.

## 7. Acceptance profile and benchmark obligations

The first benchmark identifier is `USG-INTERPRET-BENCHMARK`, initial version `0.1.0`. Step 4.12 will materialize the full corpus and evaluator; this step freezes its required coverage and reporting contract.

The corpus must have separate English and Arabic partitions and include:

- ordinary positive examples for each enabled construction;
- minimal pairs for role reversal, polarity, tense/aspect, and scope;
- nested and ambiguous constructions;
- unknown words and out-of-profile language/construction cases;
- fragments, malformed/noisy input, and multi-sentence cases;
- source-span adversarial cases: CRLF, LF, tabs, repeated spaces, punctuation, supplementary Unicode characters, combining marks, Arabic diacritics, and mixed-direction text;
- negative cases designed to trigger plausible but unsupported conclusions.

Required report dimensions (never hide these behind one aggregate):

1. exact source preservation and span accuracy;
2. segmentation and tokenization precision/recall;
3. lexical/morphological candidate quality;
4. syntax structure/role accuracy;
5. semantic expression and role accuracy;
6. operator and scope accuracy;
7. mention detection and referent-link accuracy;
8. assertion/attribution and evidence-axis accuracy;
9. ambiguity retention and abstention quality;
10. graph/schema/reference validity and round-trip completeness;
11. unsupported-inference and false-assertion rates;
12. runtime, memory, and incomplete-resource behavior.

For each enabled construction, the benchmark must define positive, negative, boundary, ambiguous, and adversarial fixtures. A construction is not enabled merely because its happy-path fixture passes.

### 7.1 Initial acceptance thresholds

Thresholds are per language and per enabled construction, not pooled across languages:

- source round-trip exactness: **100%**;
- source-span validity for emitted span-bearing records: **100%**;
- structural/schema/reference validity of accepted output: **100%**;
- unsupported inference in the frozen adversarial set: **0 accepted unsupported conclusions**;
- silent source/semantic loss: **0**;
- for each enabled construction: precision **>= 0.95** and recall **>= 0.90**, with exact metric definitions and fixture counts published by Step 4.12;
- ambiguity and out-of-profile cases: **100%** must return an explicit ambiguous/unsupported/partial result rather than an unsupported unique assertion;
- Phase 1–3 regression: **100%** of existing required checks pass.

If a construction cannot meet its threshold, it remains disabled and is documented as unsupported; thresholds must not be weakened to make a release pass. Metrics with insufficient fixture counts are reported as not yet measurable, not as 100%.

## 8. Compatibility and package boundaries

- `USG-SEM/1.0` remains unchanged. Pipeline statuses and stage artifacts live in the interpretation API envelope and versioned processing artifacts.
- Existing native models (Mention v0.7.0, Assertion v0.8.0, Evidence v0.9.0, Context v1.0.0, Expression/Relation v1.1.0, Unresolved v1.2.x, Derivation v1.3.0, Definitions v1.4.0) are adapters/resources to inspect and integrate; they are not assumed to constitute a raw-text parser.
- The legacy v0.4.0/v0.5.0 interpreter is historical evidence and a source of test ideas only. Phase 4 must not silently import its behavior into the accepted Phase 3 application.
- New interpretation packages are additive and versioned. The JavaScript Workbench and Python kernel remain separate implementation lines.
- SQLite remains the sole canonical persistence authority. Search indexes, lexical caches, and association accelerators are derived/rebuildable.
- No change to archived ZIPs or prior release directories is permitted.

## 9. Definition-level exit checklist

Step 4.1 is considered defined when all of the following are true:

- [x] Initial language profiles and their limitations are explicit and evidence-based.
- [x] Pipeline versioning and compatibility boundaries are explicit.
- [x] Result statuses distinguish complete, partial, ambiguous, unsupported, invalid, incomplete, and failed-validation outcomes.
- [x] Every logical stage has input/output and forbidden-shortcut requirements.
- [x] Source fidelity, offset convention, and provenance requirements are explicit.
- [x] Resource limits and ambiguity behavior are explicit.
- [x] Benchmark partitions, adversarial coverage, metrics, and thresholds are frozen.
- [x] USG-SEM/1.0, SQLite, and Phase 1–3 regression boundaries are preserved.

**Implementation gate:** Step 4.2 may begin only after this definition is merged. No raw-text interpretation capability is claimed by this document.
