# USG Phase 4 — Definitions and Roadmap

**Status:** Step 4.1 definition frozen; implementation steps 4.2–4.13 remain pending.
**Step 4.1 contract:** [Interpretation definitions and acceptance contract](PHASE-4-STEP-4.1-INTERPRETATION-CONTRACT.md).  
**Prerequisites:** Phase 1, Phase 2, and Phase 3 exit acceptance records.  
**Normative semantic contract:** `USG-SEM/1.0` remains unchanged.  
**Canonical persistence:** Phase 3 SQLite store remains authoritative.  
**Primary objective:** source-grounded interpretation of raw language into complete, explicit, uncertainty-preserving USG semantic documents.

## 1. Purpose

Phases 1–3 established the semantic interchange contract, a bounded deterministic reasoning layer, and a persistent local semantic workbench. Their principal input is already-structured USG-SEM data. The Phase 3 local API deliberately returns an explicit unsupported response for raw-text interpretation.

Phase 4 addresses that missing boundary: how source text is transformed into a structured semantic representation that can be validated, stored, queried, and reasoned over by the accepted system.

The objective is not to make a language model produce plausible summaries and call them semantics. The objective is to construct a source-grounded semantic graph whose parts can be inspected, traced to text, validated against explicit grammar and semantic constraints, and left unresolved when the evidence is insufficient.

Phase 4 is therefore the **interpretation and semantic construction phase**. It must build on, not replace, the contracts and services accepted in Phases 1–3.

## 2. Definition of raw-text interpretation

For this roadmap, *interpretation* means a staged process that proposes and validates mappings from source text into USG-SEM structures.

The process must distinguish at least these activities:

1. **Source ingestion:** preserve the exact input text, declared language, source identity, and processing metadata.
2. **Segmentation:** identify document, paragraph, sentence, clause, and other useful text spans without changing the source.
3. **Lexical analysis:** identify tokens, lemmas, morphology, multiword expressions, and candidate lexical senses where supported.
4. **Syntactic analysis:** propose grammatical relationships and constituent structure while retaining alternatives when the analysis is ambiguous.
5. **Semantic composition:** map lexical and grammatical structures into typed USG expressions, roles, relations, operators, and frames.
6. **Reference interpretation:** identify mentions and propose links to referents without confusing a repeated label with proven identity.
7. **Discourse interpretation:** connect sentence-level representations across context, including attribution, anaphora, temporal relations, conditionals, contrast, and discourse relations where supported.
8. **Assertion and evidence construction:** distinguish described content from asserted content; create source-linked assertions and evidence records only when their conditions are met.
9. **Validation and document assembly:** validate types, references, scopes, source spans, and profile conformance; preserve unresolved or unsupported material.
10. **Evaluation:** measure both successful interpretation and the rate of unsupported or structurally invalid conclusions.

These stages are logically distinct even if an implementation combines some of them internally. A later stage must not conceal uncertainty or manufacture missing output from an earlier stage.

## 3. Core architecture principles

### 3.1 Canonical graph remains authoritative

The output is a complete compositional USG semantic graph. Text summaries, flat claims, search indexes, embeddings, visualizations, and natural-language explanations are derived views. They must not replace the graph or become an alternate source of semantic truth.

USG-SEM/1.0 remains unchanged during the initial Phase 4 work. If interpretation requires a new canonical record or status, that change must be proposed as a separately versioned semantic profile with migration and conformance tests.

### 3.2 Source fidelity and exact provenance

- Preserve the original source text exactly, including Unicode code points, whitespace, punctuation, and line endings.
- Calculate spans against the preserved source using the existing zero-based, end-exclusive Unicode code-point convention.
- Every interpreted item that claims textual grounding must identify its source and exact span or explicitly state why it has no direct span.
- Derived or normalized text may be stored as a separate processing artifact; it must never replace the original source.
- Preserve the relationship between a sentence, clause, token, expression, assertion, and evidence item without assuming they are interchangeable units.

### 3.3 Separate linguistic form from semantic content

A token, word form, lemma, syntactic dependency, semantic role, expression, referent, mention, assertion, and evidence record are different kinds of information. The implementation must not collapse them into a single generic node or label.

Grammar provides constraints and composition patterns; it does not by itself prove that a described event happened or that a source statement is true.

### 3.4 Meaning is compositional and scope-sensitive

Interpretation must preserve operator structure and exact operand/role bindings. Negation, modality, quantification, tense, aspect, conditionals, exceptions, attribution, comparison, and coordination must not be flattened into keywords or unscoped labels.

Nested and ambiguous constructions must retain their structure or explicit alternatives. Unsupported scope must result in an unresolved/unsupported interpretation with diagnostics, not a guessed reading.

### 3.5 Context is evidence, not a license to guess

Local context, paragraph topic, document domain, lexical co-occurrence, semantic associations, and prior discourse may rank candidate interpretations or help resolve a genuinely ambiguous item. They do not independently prove identity, entailment, or truth.

Context signals must be traceable and separable from the evidence in the source. A context model must not override a clear source span merely because a candidate is statistically common.

A future semantic memory may organize concepts, frames, roles, relations, and weighted associations. It must distinguish stable definitions from usage-derived associations, and candidate links from verified identity. Frequency or activation must not silently become a semantic fact.

### 3.6 Ambiguity and incompleteness are first-class results

The interpreter must be able to return:
- one supported candidate;
- multiple retained candidates;
- partial interpretation;
- unresolved reference or sense;
- unsupported construction;
- structurally invalid candidate;
- resource-limited/incomplete processing.

These outcomes must remain distinct. A low-confidence candidate is not automatically false, and a high-scoring candidate is not automatically correct. If alternatives cannot be safely represented in the current profile, the source and the unresolved decision must still be preserved without inventing a canonical interpretation.

### 3.7 Models propose; contracts and tests constrain

Statistical or generative models may be used as candidate generators, rankers, or specialized analyzers. Their output is not authoritative merely because it is fluent or confident.

Any model-assisted path must:
- identify the model and version, prompt/configuration or equivalent reproducibility metadata where applicable;
- validate generated structures against the declared USG profile and type/role/scope constraints;
- preserve source evidence and candidate alternatives;
- reject or abstain on malformed, unsupported, or ungrounded output;
- avoid silently inventing definitions, referents, assertions, or evidence;
- permit deterministic non-model components to inspect and validate the result.

No paid external model service is a required architectural dependency. Offline/local execution remains a supported target. Model use, if any, must be replaceable behind a versioned interface.

### 3.8 No truth promotion

Interpretation produces representations of what the source says or may mean. It does not determine whether those statements are objectively true.

Keep separate:
- source-span alignment;
- linguistic/structural analysis status;
- semantic interpretation support;
- assertion/attribution status;
- rule-based derivation;
- contradiction/conflict;
- source independence and corroboration;
- external verification.

No one score or status may collapse these dimensions.

### 3.9 No silent semantic limits

Do not impose arbitrary caps that silently truncate tokens, candidates, operands, graph nodes, mentions, references, or derivations. Execution budgets are permitted only when interruption is reported as incomplete with diagnostics and preserved partial work.

### 3.10 Historical and current boundaries remain intact

- Do not modify archived releases or silently redefine Workbench v0.5.4, Python kernel 0.4.0/0.5.0, Bridge v0.1, or later versioned packages.
- Do not assume the JavaScript Workbench and Python kernel are one runtime.
- Use additive, versioned interpretation packages and explicit adapters.
- The Phase 3 SQLite store and local API remain the canonical persistence boundary.
- Existing Phase 1/2/3 acceptance suites remain mandatory regression gates.

## 4. Target interpretation pipeline

The target pipeline is shown below. This is a logical architecture; it does not require one process, one model, or one package per stage.

```text
Exact source
    |
    v
Source registry and immutable text snapshot
    |
    v
Segmentation and source-span map
    |
    v
Lexical and morphological candidates
    |
    v
Syntactic candidates and ambiguity set
    |
    v
Compositional semantic construction
    |
    +------> Mention / referent candidates
    |
    +------> Context and discourse links
    |
    v
Assertion, attribution, modality, and evidence construction
    |
    v
USG-SEM validation and diagnostics
    |
    v
Complete canonical document (or explicit partial/unresolved result)
    |
    v
Phase 3 SQLite store, query, analysis, and Kernel Lab
```

The pipeline may iterate when later constraints expose an earlier ambiguity. Iteration must retain candidate provenance and must not overwrite the original source or erase prior unresolved states without recording the resolution path.

## 5. Semantic resources and knowledge organization

Phase 4 may need reusable lexical and semantic resources. They should be layered rather than placed in one unstructured keyword dictionary.

### 5.1 Lexical layer

Stores language-specific word forms, lemmas, morphology, part-of-speech candidates, multiword expressions, lexical senses, and links to semantic concepts. Surface forms and lemmas must remain distinct.

### 5.2 Concept and frame layer

Stores stable concept identities, frame definitions, typed roles, relation definitions, constraints, and versioned mappings. Labels are language-specific names, not identities. Concepts with similar labels must not be merged without explicit identity evidence.

### 5.3 Association and context layer

Stores usage-derived or curated associations such as related concepts, domain indicators, typical co-occurrence, and contextual activation. Associations should carry provenance, scope/domain, strength or rank, usage statistics, and update policy. They are candidate-generation signals, not definitional facts.

If an activation system is adopted, active links may be searched before less active links, and usage may update their retrieval priority. Decay and promotion must be deterministic, inspectable, and prevented from deleting canonical definitions or semantic records.

### 5.4 Grammar and construction layer

Stores reusable language-specific grammar patterns and their mapping to typed semantic constructors. Each pattern must define applicability, required roles, output structure, ambiguity behavior, and unsupported cases. Grammar patterns must be versioned and tested independently from lexical data.

### 5.5 Provenance and lifecycle

Every resource entry must identify its source, version, language/domain scope, and whether it is curated, imported, inferred as a candidate, or validated under an explicit procedure. Candidate associations must not be promoted to canonical definitions merely through repeated model output.

## 6. Language coverage strategy

“Universal” is the long-term design ambition, not an acceptance claim. Phase 4 must not assume that one grammar, parser, embedding model, or lexical resource works equally across languages.

The initial supported language set and construction coverage must be selected in Step 4.1 from the actual frozen benchmark corpus and available local resources. The choice must be documented before implementation. Additional languages require separate fixtures, language-specific grammar/lexical resources, and measured acceptance; translating labels alone does not establish multilingual interpretation.

The architecture should keep language-neutral semantic concepts separate from language-specific lexical and grammatical realization.

## 7. Ordered Phase 4 roadmap

Steps are sequential acceptance gates. A step may be divided into smaller PRs, but later work cannot bypass a failed earlier contract. Each implementation step must have dedicated tests, a dedicated PR, and exact-head CI acceptance before automatic merge.

| Step | Name | Main deliverable | Exit condition |
|---|---|---|---|
| **4.1** | Interpretation definitions and acceptance contract | Freeze terminology, supported initial language/corpus, interpretation status model, target architecture, non-goals, and measurable quality gates | Every interpretation stage and output status has an explicit definition; benchmark scope and forbidden inferences are frozen before implementation. |
| **4.2** | Source ingestion and span-preserving segmentation | Versioned source adapter, immutable text handling, document/paragraph/sentence/clause segmentation interface, offset maps | Exact source round-trip and span integrity pass for Unicode, combining marks, CRLF, punctuation, whitespace, and multi-paragraph inputs. |
| **4.3** | Lexical and morphological analysis contract | Versioned token/lemma/morphology/lexical-candidate representation and replaceable analyzer interface | Token and candidate records map to exact source spans; unsupported morphology and unknown words remain explicit; language-specific tests pass. |
| **4.4** | Grammar and syntactic analysis layer | Versioned grammar-pattern registry and syntax candidate representation, including ambiguity and dependency/constituent relations | Positive, negative, ambiguous, nested, and adversarial grammar fixtures pass; no syntactic relation is silently treated as semantic entailment. |
| **4.5** | Compositional semantic construction | Mapping from lexical/syntactic structures to typed USG expressions, frames, roles, relations, and operators | Constructors preserve role identity, operand order, scope, semantic kind, and source provenance; unsupported mappings abstain. |
| **4.6** | Mention and reference interpretation | Mention extraction and candidate referent linking, including ambiguity and cross-sentence references | Mention/referent distinction and identity constraints pass; repeated labels and similarity never create identity by themselves. |
| **4.7** | Discourse, context, and temporal interpretation | Versioned discourse/context links for supported attribution, anaphora, temporal, conditional, contrast, and connective constructions | Context and discourse links are source-grounded, scoped, and traceable; unsupported cross-sentence inferences remain unresolved. |
| **4.8** | Assertion and evidence construction | Source-grounded assertion/evidence adapter integrating the accepted native models and USG-SEM document adapter | Descriptions are not promoted to assertions; attribution and epistemic status are preserved; quote alignment and semantic support remain separate. |
| **4.9** | Semantic resource and association registry | Versioned lexical/concept/frame/grammar/association stores with provenance and update rules | Definitions are distinct from usage associations; resource updates are reproducible; candidate associations cannot silently become canonical facts. |
| **4.10** | Model-assisted candidate generation (optional adapter) | Replaceable interface for local or external candidate generators, with deterministic validation and explicit provenance | Model output cannot bypass validators; malformed, ungrounded, or unsupported output is rejected/abstained; the core pipeline still works without a model service. |
| **4.11** | Integrated interpretation API and Kernel Lab | Local API/CLI and browser workflow to submit source text, inspect stage outputs/alternatives/diagnostics, and persist complete USG-SEM documents | UI/API use the same Phase 3 application and SQLite store; raw input and complete structured output can be exported and replayed. |
| **4.12** | Frozen benchmark and adversarial evaluation | Versioned corpus, gold/partial annotations, per-stage metrics, negative cases, calibration/abstention metrics, and machine-readable report | Results include precision/recall or suitable task metrics, coverage, ambiguity handling, span accuracy, invalid-output rate, unsupported-inference rate, and per-construction breakdown; no aggregate hides critical failures. |
| **4.13** | Integrated Phase 4 exit acceptance | End-to-end gate across ingestion, interpretation, semantic construction, storage, Phase 1–3 regression, packaging, and reproducibility | Every enabled construction passes frozen acceptance on the exact merged main commit; all unsupported scope and limitations are published. |

### Sequencing note

Steps 4.2–4.5 establish the source-to-composition foundation. Steps 4.6–4.8 add identity, discourse, assertion, and evidence. Step 4.9 provides reusable semantic resources. Step 4.10 is optional and cannot block a fully deterministic baseline unless a later approved acceptance profile explicitly makes a model adapter necessary. Steps 4.11–4.13 integrate and evaluate the complete capability.

The exact implementation order and dependencies may be refined in Step 4.1, but no implementation step may start before its predecessor's acceptance contract is frozen.

## 8. Benchmark and acceptance design

Phase 4 must measure interpretation quality, not just schema validity or whether a model returned JSON.

The frozen evaluation set should include:
- simple and nested sentences;
- varied word order and grammatical constructions within the selected language scope;
- ambiguous words and syntactic attachments;
- multiword expressions and idioms where supported;
- negation, modality, quantification, conditionals, exceptions, tense, and aspect;
- active/passive alternations and role reversals;
- coordination, comparison, and relational constructions;
- coreference, repeated names, pronouns, and ambiguous references;
- attribution, reported speech, quotation, and speaker changes;
- multi-sentence discourse and temporal relations;
- malformed, incomplete, fragmentary, noisy, and out-of-domain input;
- Unicode, punctuation, whitespace, and source-span edge cases;
- adversarial examples designed to trigger plausible but unsupported interpretations.

Measure separately:
1. exact source/span alignment;
2. segmentation and tokenization quality;
3. lexical/morphological candidate quality;
4. syntactic relation/structure quality;
5. semantic constructor and role accuracy;
6. scope and operator accuracy;
7. mention detection and referent-link accuracy;
8. assertion/attribution classification;
9. ambiguity retention and calibrated abstention;
10. graph validity and round-trip completeness;
11. unsupported inference and false assertion rates;
12. latency, memory, and resource-limited incomplete behavior.

Gold annotations may be partial where a construction is genuinely ambiguous. The evaluator must accept a correct unresolved/alternative result when the source does not justify a single reading. It must penalize unsupported certainty more heavily than explicit abstention where the acceptance profile specifies that policy.

No human-review workflow is required at runtime or as a release gate. Annotation fixtures and evaluation labels must be versioned and reproducible; their creation process is documented separately from runtime behavior.

## 9. Explicit exclusions and non-claims

Phase 4 does not automatically deliver:
- unrestricted understanding of every language, dialect, domain, or writing style;
- objective truth determination or independent fact verification;
- a general theorem prover or human-equivalent reasoning;
- autonomous invention of canonical ontologies or unrestricted rule learning;
- identity resolution from names, embeddings, or similarity alone;
- guaranteed interpretation of sarcasm, humor, metaphor, pragmatics, or cultural implication without explicit tested coverage;
- distributed multi-controller execution;
- production/security certification or public multi-user hosting;
- a requirement to use paid APIs or any one specific LLM.

Each capability must be separately specified, benchmarked, and accepted before being claimed.

## 10. Dependencies and preservation rules

- Phase 1: USG-SEM/1.0, schema, registries, adapters, and exit tests remain frozen.
- Phase 2: deterministic rules, grounding, evidence assessment, query contracts, and exit tests remain unchanged unless a separately versioned extension is accepted.
- Phase 3: SQLite canonical storage, immutable revisions, local API, CLI, and Kernel Lab remain the persistence/product boundary.
- Native Assertion and Evidence models remain separately versioned. Phase 4 must inspect their actual contracts before writing adapters; the roadmap does not assume every field is already integrated.
- Existing Workbench and Python kernel lineages remain distinct. New interpretation components must be additive and explicitly versioned.
- The database benchmark decision remains unchanged: SQLite is canonical unless a future complete evaluation justifies a migration.

## 11. Phase 4 definition status

This document establishes the initial Phase 4 definitions and proposed ordered roadmap. It does not mean Step 4.1 or any implementation step has passed acceptance. The next action is a focused Step 4.1 review that checks every definition against the current schemas, native models, adapters, and benchmark fixtures, then freezes the exact initial language/corpus and acceptance contract before implementation begins.
