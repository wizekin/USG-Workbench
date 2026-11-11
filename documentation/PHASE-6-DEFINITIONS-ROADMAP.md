# USG Phase 6 — Definitions and Roadmap

**Status:** IN PROGRESS — Steps 6.1–6.5 accepted for their bounded, benchmarked scope; broader grammar and unified integration remain pending.  
**Proposed interpretation contract:** `USG-INTERPRET/0.3.0`, additive to the accepted Phase 5 contract.  
**Accepted starting point:** Phase 5 `USG-INTERPRET/0.2.0`.  
**Canonical semantic interchange:** `USG-SEM/1.0` remains unchanged.  
**Canonical persistence:** the existing Phase 3 SQLite store remains authoritative.  
**Initial language profiles:** English and Modern Standard Arabic (MSA).  
**Next gate:** Step 6.6 — nominal, property, possession, and modifier semantics; definition inventory added, benchmark and implementation acceptance pending.

## 1. Purpose and transition from Phase 5

Phase 5 established a deterministic, source-grounded interpretation pipeline, a persistent resource catalogue, immutable interpretation runs, deterministic replay, and the Kernel Lab integration. Its accepted v0.2.1 benchmark contains 100 English/MSA Arabic fixtures. The measured target constructions are:

- English simple transitive SVO: `en.simple_transitive.svo`.
- MSA Arabic simple transitive VSO: `ar.simple_transitive.vso`.
- MSA Arabic simple transitive SVO: `ar.simple_transitive.svo`.

On the accepted Step 5.11 run, both languages achieved 100% construction precision and recall, positive completion-status accuracy, exact role-binding accuracy, exact valid source-span accuracy, and negative/ambiguous target abstention, with zero false unique constructions. The run processed 100 fixtures in 685.388 ms total on its GitHub Actions runner; this is a CI baseline, not a hardware-independent or production-concurrency guarantee. See the [Phase 5 completion record](PHASE-5-COMPLETION-RECORD.md), [Step 5.11 acceptance report](PHASE-5-STEP-5.11-BENCHMARK-EXIT-ACCEPTANCE.md), and [benchmark artifact](https://github.com/wizekin/USG-Workbench/actions/runs/42965506600/artifacts/13830553681).

These results are deliberately narrow. They prove the measured simple-transitive cases, not broad English or Arabic understanding. The v0.2.1 benchmark also corrected an important evaluation distinction: a fixture can be outside the target simple-transitive construction while still containing clauses that the overall pipeline can interpret. Target-construction labels must not be confused with whole-pipeline completion statuses.

Phase 6 therefore expands the *measured semantic construction coverage* of USG. It will move from the narrow simple-transitive foundation toward richer predicate/argument structures, nominal and property semantics, intra-clause coordination, embedded clauses, voice and speech acts, operator scope, and bounded discourse-reference handling. It will also define a safe path from complete interpretation graphs into canonical USG semantic documents.

This remains a controlled, benchmark-gated expansion. A feature is not considered supported merely because a parser emits a node or a unit test passes. Each enabled construction must have a frozen gold corpus, per-language measurements, negative and ambiguous fixtures, source-grounded evidence, and explicit abstention behavior.

## 2. Phase 6 goals

1. Expand the construction inventory beyond simple transitive SVO/VSO patterns while preserving exact source text, code-point spans, and derivation provenance.
2. Introduce a reusable, language-independent predicate-frame and semantic-role model, with language-specific lexical and grammatical realization resources.
3. Support additional argument structures, predication, nominal properties, modifiers, and controlled forms of complex clause composition.
4. Close known Phase 5 boundaries in a measured way: coordinated predicates/arguments inside a clause, richer subordination, and conservative reference resolution.
5. Apply operators across the expanded graph without shortcutting scope or discarding ambiguity.
6. Define a loss-aware projection from complete interpretation graphs to `USG-SEM/1.0` documents wherever that existing contract can represent the result.
7. Keep resources, interpretation runs, replay, API/CLI, and Kernel Lab behavior deterministic and backed by the existing SQLite authority.
8. Publish a new benchmark and a clear list of enabled, disabled, partially supported, and insufficiently measured constructions.

## 3. Non-goals and exclusions

Phase 6 does not attempt to deliver:

- unrestricted English or Arabic understanding, dialectal Arabic, arbitrary code-switching, or universal language coverage;
- automatic truth determination, fact checking, source credibility evaluation, or unrestricted entailment;
- real-world identity resolution from matching names, lexical similarity, embeddings, or association strength alone;
- unrestricted metaphor, sarcasm, humor, cultural inference, or pragmatic intent inference without separately defined constructions and tests;
- automatic invention, silent promotion, or untraceable rewriting of canonical concepts, definitions, frames, or grammar rules;
- mandatory LLMs, paid APIs, cloud inference, network access, or downloaded models for the deterministic baseline;
- distributed multi-controller execution, a public multi-user service, or an autonomous self-modifying architecture;
- replacing SQLite or introducing a second canonical database;
- changing historical archives, the JavaScript Workbench implementation line, or accepted Phase 1–5 behavior;
- runtime human review, manual approval queues, or a human intervention requirement;
- an AGI claim.

Model-assisted candidate generation may remain optional and replaceable. It cannot override deterministic validators, source checks, resource provenance, or explicit ambiguity/abstention rules.

## 4. Frozen architectural decisions

### 4.1 Versioned interpretation; preserve accepted contracts

- Define Phase 6 as an additive `USG-INTERPRET/0.3.0` line.
- Keep `USG-INTERPRET/0.2.0`, its schemas, resources, frozen corpora, expected behavior, and Phase 5 implementation protected by regression tests.
- Keep the Phase 4 `USG-INTERPRET/0.1.0` baseline and all Phase 1–4 contracts unchanged.
- Do not change `USG-SEM/1.0` to accommodate a new construction. If an actual representation gap is found, document concrete examples and propose a separate, versioned semantic profile with migration and conformance tests. That proposal is not silently bundled into Phase 6.

### 4.2 SQLite remains the sole canonical persistence authority

- Continue using the existing store-owned SQLite connection and transaction lifecycle.
- Store new resource versions, manifests, and interpretation-run artifacts through the existing catalogue/application boundaries.
- Keep caches, activation scores, search indexes, and candidate rankings as derived and rebuildable data.
- Do not add another SQLite connection owner, another canonical database, or a replacement backend.

### 4.3 Source fidelity and traceable derivations

- Preserve the exact original input string, source digest, Unicode code-point offsets, and sentence/clause boundaries.
- Every emitted span must match the exact source slice.
- Every semantic frame, role, operator, modifier, discourse link, and projected document assertion must trace to the source evidence and the rules/resources that licensed it.
- Normalized text, lemmas, morphology, transliteration, and inferred structure remain separate artifacts linked to the unmodified source.
- Reprocessing creates a new immutable run. It must not overwrite the source snapshot, erase alternatives, or rewrite prior accepted results.

### 4.4 Explicit capability states

The contract and reports must distinguish at least:

- **implemented:** code exists;
- **regression-tested:** deterministic tests cover the behavior;
- **benchmark-enabled:** a frozen per-language construction set passes the applicable quality gates;
- **partial/candidate-only:** evidence or structure is retained, but a unique semantic interpretation is not licensed;
- **disabled/unsupported:** no accepted construction mapping exists.

Only **benchmark-enabled** constructions may be advertised as supported Phase 6 capabilities. A passing general workflow or a high aggregate score cannot promote an unmeasured construction.

### 4.5 Conservative interpretation and projection

- Unknown words, ambiguous lexical senses, competing parses, unsupported constructions, unresolved references, and resource-budget interruptions remain explicit.
- Candidate ranking, usage frequency, model confidence, context activation, and association weight are not truth, identity, entailment, or calibrated probability.
- A partial processing result must not be labelled complete merely because execution finished.
- A graph may be projected to a canonical semantic document only when every required meaning and relation is represented without silent loss. Otherwise retain the interpretation artifact and report the projection limitation.

## 5. Target Phase 6 architecture

    Immutable source snapshot
            |
            v
    Document / sentence / clause segmentation
            |
            v
    Versioned lexical + morphology candidates
            |
            v
    Syntax / construction / attachment candidates
            |
            v
    Predicate frames, valency, and typed semantic roles
            |
            v
    Recursive semantic composition
            |
            +------> nominal properties and modifiers
            +------> intra-clause and clause-level coordination
            +------> embedded / subordinate propositions
            +------> voice and speech-act structure
            +------> scoped operators and quantifiers
            +------> bounded discourse/reference candidates
            |
            v
    Validated, source-grounded interpretation graph
            |
            +------> lossless projection where USG-SEM/1.0 permits
            |
            v
    Existing SQLite persistence, queries, export, replay, and Kernel Lab

This is a logical architecture, not a mandate for a new process, model, or database. A stage may revisit earlier candidates when later constraints reveal ambiguity, but all alternatives and derivation paths must remain inspectable and reproducible.

## 6. Ordered Phase 6 definitions and implementation roadmap

Each step is a separate contract/implementation/acceptance gate. The sequence is intentional: define the version and benchmark before expanding grammar; define the frame and lexical foundations before adding construction families; integrate only capabilities that have passed their own tests. A later step may not silently bypass an earlier failed gate.

| Step | Name | Main deliverable | Exit condition |
|---|---|---|---|
| **6.1** | Phase 6 interpretation and projection contract | Freeze `USG-INTERPRET/0.3.0`, capability states, source/provenance rules, role/frame boundaries, projection policy, and compatibility protections | Contract and protected-path tests are merged before implementation begins; no Phase 5 or `USG-SEM/1.0` mutation. |
| **6.2** | Expanded benchmark corpus and evaluator | Frozen bilingual v0.3.0 corpus, construction taxonomy, gold semantic graphs/spans, adversarial negatives, ambiguity cases, per-language/per-construction evaluator | Corpus and evaluator validate independently; no empty denominator is treated as a passing score; Phase 5 corpora remain unchanged. |
| **6.3** | Typed semantic roles, predicate frames, and valency model | Versioned frame/role schema with required/optional slots, constraints, lexical-sense links, and language-neutral semantic roles | Frame selection, slot binding, role constraints, provenance, and graph references pass schema and adversarial tests. |
| **6.4** | Expanded lexical and morphology resources | Provenance-bearing English/MSA Arabic resources needed by the frozen construction fixtures, including only explicitly supported inflectional and clitic patterns | Exact spans and source mappings are preserved; unknown/ambiguous forms remain candidates; resource digests and replay are deterministic. |
| **6.5** | Expanded predicate and argument structures | Intransitive, ditransitive, copular, and selected prepositional predicate frames with explicit semantic roles | Each enabled frame family passes independent positive, negative, ambiguous, and boundary tests in each language; word order alone cannot determine semantic role. |
| **6.6** | Nominal, property, possession, and modifier semantics | Typed noun/adjective predication, possessive relations, noun compounds, prepositional modifiers, and selected adverbial/temporal modifiers | Head/modifier/possessor/attribute/value links remain explicit, source-grounded, and correctly scoped; attachment ambiguity is retained. |
| **6.7** | Intra-clause coordination and shared arguments | Coordinated subjects, objects, predicates, and other explicitly supported phrase-level structures | Shared arguments and coordinated predicates are represented without duplication, flattening, or invented bindings; AND/OR/CONTRAST evidence is exact. |
| **6.8** | Embedded and subordinate clause composition | Complement, relative, temporal, causal, and conditional clause structures with typed attachment/relation nodes | Parent/child proposition links, argument gaps where licensed, relation scope, and source spans validate; unsupported attachment remains explicit. |
| **6.9** | Voice and speech-act structures | Bounded active/passive mappings plus interrogative and imperative construction records | Passive role mapping is distinguished from surface order; questions and commands are not projected as ordinary factual assertions. |
| **6.10** | Cross-construction operator and quantifier scope | Compose Phase 5 negation/modality/tense/aspect/quantifier operators over the new frames, modifiers, and embedded structures | Scope minimal pairs and nesting adversaries pass; unresolved scope preserves alternatives; no keyword-only or sentence-wide shortcuts. |
| **6.11** | Bounded discourse-reference resolution | Conservative antecedent selection over the Phase 5 mention/reference candidates, with explicit context boundaries and unresolved alternatives | Resolve only when the frozen deterministic criteria identify a unique licensed antecedent; ambiguity and unknown identity remain explicit; no entity identity is merged by association strength alone. |
| **6.12** | Loss-aware projection to canonical semantic documents | Adapter from complete Phase 6 interpretation graphs to `USG-SEM/1.0` where the mapping is lossless; explicit projection diagnostics otherwise | Every projected document passes the unchanged schema and source/evidence constraints; unsupported or lossy graph features are never silently dropped. |
| **6.13** | API, CLI, resource lifecycle, and Kernel Lab integration | Expose accepted construction/frame diagnostics, alternatives, projection results, immutable run/replay, and exports through existing application services | API, CLI, and UI use the same services and store-owned SQLite connection; wheel/install, deterministic replay, and UI/API integration tests pass. |
| **6.14** | Full Phase 6 benchmark and integrated exit acceptance | Execute the real v0.3.0 interpreter over the frozen corpus; run Phase 1–5 regressions, packaging, storage, projection, and performance checks | Every advertised construction passes its independent language-specific gates on the exact accepted commit; enabled/disabled scope and limitations are published. |

### 6.1 Dependency and sequencing notes

- Step 6.1 freezes the new interpretation boundary and protects the accepted versions.
- Step 6.2 must precede grammar implementation so feature selection and quality thresholds are not chosen after observing model output.
- Step 6.3 defines the semantic role/frame vocabulary required by the later construction families.
- Step 6.4 adds only the lexical/morphological evidence demanded by the frozen benchmark and accepted construction plan. The additive gold profiles v0.3.1 and v0.3.2 separate predicate/marker spans and repair repeated participant mention offsets; v0.3.2 is the scoring baseline for Steps 6.5 and 6.14.
- Steps 6.5–6.6 expand clause and phrase semantics using the role/frame model.
- Steps 6.7–6.8 close important Phase 5 composition gaps after the underlying argument and modifier representations are stable.
- Step 6.9 separates grammatical voice and communicative form from semantic assertion.
- Step 6.10 composes the already explicit operator model over the larger expression graph.
- Step 6.11 depends on stable mention, proposition, and discourse structures; it must prefer abstention over forced identity.
- Step 6.12 depends on stable graph semantics and defines the boundary between processing artifacts and canonical semantic documents.
- Step 6.13 integrates only previously accepted services; it does not introduce a second implementation of semantic logic in the browser.
- Step 6.14 is the final gate. Schema validation, unit tests, or aggregate-only accuracy are insufficient on their own.

## 7. Benchmark and acceptance policy

The Phase 4 and Phase 5 corpora remain frozen. Phase 6 introduces a new additive, versioned corpus; it never edits earlier gold fixtures or retroactively changes accepted metrics.

### 7.1 Fixture requirements

For every proposed enabled construction and each language independently, target at least:

- 20 positive fixtures;
- 20 negative/adversarial fixtures;
- 10 ambiguous/boundary fixtures.

The corpus must include minimal pairs that distinguish semantic roles from surface order; alternative predicate senses; complement versus adjunct attachment; shared versus independent coordinated arguments; active versus passive mappings; operator scope; embedded-clause attachment; pronoun/reference ambiguity; and out-of-profile structures. It must also include exact-span edge cases such as Arabic diacritics, combining marks, punctuation, repeated whitespace, tabs, CRLF/LF, supplementary Unicode characters, and mixed-direction text.

Gold annotations must cover the intended construction class, full-pipeline completion separately, semantic frame/role links, operator and clause scope, source spans, and expected abstention behavior. A negative target-construction fixture may still contain a different supported construction. Its target label must not force the overall pipeline to report `UNSUPPORTED`.

If a construction cannot reach a defensible fixture count, report it as insufficiently measured and keep it disabled. An empty denominator must never produce a 100% score.

### 7.2 Required metrics

Report independently by language, construction, and relevant pipeline stage:

1. exact source preservation and source-span alignment;
2. segmentation, lexical/morphology, and construction precision/recall;
3. predicate-frame selection and valency-slot accuracy;
4. semantic-role, argument, modifier, and attachment accuracy;
5. composition, nesting, and coordination completeness;
6. voice and speech-act classification;
7. operator attachment, quantifier interpretation, and scope accuracy;
8. mention/reference candidate and antecedent-selection accuracy;
9. ambiguity retention, negative abstention, and false unique interpretation rates;
10. graph/schema/reference validity and lossless round-trip;
11. canonical-document projection coverage and correctness;
12. unsupported inference, false assertion, and silent-loss rates;
13. runtime percentiles, peak memory with a clearly named measurement method, resource budgets, and deterministic replay.

### 7.3 Initial quality gates

- Exact source preservation: **100%**.
- Validity of every emitted source span: **100%**.
- Validity of every accepted graph and projected document: **100%**.
- Silent source/role/relation loss: **0**.
- False unique target constructions on frozen negative or ambiguous fixtures: **0**.
- Ambiguous/out-of-profile fixtures: **100%** must retain ambiguity or explicitly abstain rather than emit an unjustified unique interpretation.
- Per enabled construction and language: precision **>= 0.95** and recall **>= 0.90**, unless the Step 6.1 contract sets a stricter threshold.
- Any role/frame/scope/projection metric below its frozen threshold disables that construction or projection path; thresholds are not weakened to obtain a passing release.
- Phase 1–5 regressions, immutable corpus checks, package tests, SQLite integrity, and deterministic replay: **100%** pass.

Publish each denominator, exact corpus and resource-manifest digests, per-case outcomes, enabled construction IDs, disabled construction IDs, and the exact accepted main commit. Aggregate scores must not conceal a failed language, role family, construction, or scope category.

## 8. Resource and knowledge lifecycle

Keep the following resource classes distinct:

- **Canonical semantic definitions:** stable concept, predicate, role, and relation meanings with explicit versions and provenance.
- **Lexical realizations:** English/MSA Arabic surface forms, lemmas, morphology, and sense candidates.
- **Construction resources:** grammar patterns, valency frames, attachment constraints, and typed semantic mappings.
- **Discourse resources:** mention features, reference constraints, and relation markers.
- **Provisional associations:** usage/context/co-occurrence links that may help retrieval but do not define meaning.
- **Derived retrieval metadata:** activity, recency/decay, ranking, caches, and indexes.

New resources must be immutable/versioned and registered through the existing SQLite catalogue. Association activity may prioritize retrieval; it cannot create definitions, merge identities, prove coreference, or establish entailment. A candidate-to-canonical promotion mechanism, if ever required, needs its own deterministic validation contract and immutable result. Phase 6 does not authorize unsupervised self-editing of the semantic system.

## 9. Compatibility and preservation checklist

Every Phase 6 implementation PR must verify:

- `specifications/USG-SEM-1.0.md` and its schema are unchanged;
- Phase 1–5 contracts, acceptance records, fixtures, and benchmark digests remain protected;
- Phase 4 `USG-INTERPRET/0.1.0` and Phase 5 `USG-INTERPRET/0.2.0` behavior remains regression-tested;
- SQLite remains the only canonical persistence backend and the existing store remains the connection owner;
- archives and historical implementation directories remain unchanged;
- the JavaScript Workbench and Python kernel remain separate implementation lines;
- deterministic baseline tests do not require paid models, cloud services, or network access;
- no human review or manual approval is a runtime acceptance prerequisite;
- all capability claims match the measured enabled-construction list.

## 10. Phase 6 exit criteria

Phase 6 is complete only when:

1. Steps 6.1–6.14 are merged and the exact-head acceptance workflows pass.
2. The `USG-INTERPRET/0.3.0` contract and frozen benchmark are published.
3. Every advertised construction passes the per-language/per-construction thresholds.
4. Expanded predicate frames, argument structures, modifiers, coordination, embedded clauses, voice/speech acts, operators, and bounded discourse links retain exact source provenance and explicit uncertainty.
5. Unknown, ambiguous, unsupported, and resource-limited input remains explicit and lossless.
6. Only losslessly representable complete graphs are projected to the unchanged `USG-SEM/1.0` contract; all other results remain inspectable as interpretation artifacts with projection diagnostics.
7. Resource manifests, interpretation snapshots, and deterministic replay remain reproducible through the existing SQLite store.
8. Kernel Lab, API, and CLI expose the same accepted services and clearly distinguish complete, partial, ambiguous, unsupported, and projection-failed results.
9. Phase 1–5 regressions, packaging, compatibility, and protected-path checks pass.
10. A completion record publishes measured construction coverage, corpus/resource digests, performance profile, known limitations, and the exact accepted main commit.

## 11. What Phase 6 completion will mean

Phase 6 completion will mean a substantially broader, benchmarked English/MSA Arabic semantic interpreter with explicit predicate frames, richer compositional structures, bounded discourse handling, and a safe semantic-document projection boundary for the constructions that pass acceptance.

It will not mean unrestricted language understanding, universal semantic coverage, objective truth determination, autonomous knowledge creation, human-equivalent reasoning, or AGI. Broader inference, knowledge consolidation, autonomous resource learning, additional languages, and distributed multi-controller architecture remain separate future research phases requiring their own contracts and evidence.

## 12. Phase 6 starting point

Steps 6.1–6.5 are accepted for their bounded scope. Proceed with **Step 6.6 only**. Do not broaden a construction beyond its measured evidence. Each later step follows the same sequence used in Phase 5: define the contract, implement one bounded capability, run its focused and compatibility tests, publish its evidence, and merge only after the exact pull-request head passes the required checks.
