# USG Phase 7 — Semantic Knowledge Integration and Contextual Knowledge Layer

**Phase:** 7 — Semantic knowledge integration and contextual knowledge retrieval  
**Status:** DEFINITIONS ROADMAP — proposed scope; implementation and acceptance have not yet begun.  
**Primary objective:** build a governed, persistent semantic knowledge layer that connects lexical forms, lexical senses, language-neutral concepts, semantic classes, typed relations, source evidence, contexts, and validated canonical documents.  
**Prerequisites:** accepted Phase 1–5 foundations; Phase 6 bounded automatic exit accepted for its registered scope.  
**Non-blocking parallel work:** Phase 6 construction expansion continues through the [Phase 6 Continuation Tracker](PHASE-6-CONTINUATION-TRACKER.md). No unfinished Phase 6 continuation item is a prerequisite for Phase 7 unless a specific Phase 7 step explicitly adopts it.  
**Canonical interchange:** `USG-SEM/1.0` remains unchanged.  
**Canonical persistence:** the existing Phase 3 SQLite authority remains the only canonical document store.  
**Proposed knowledge contract:** `USG-KNOWLEDGE/0.1.0` (to be frozen in Step 7.1 before implementation).

---

## 1. Purpose and transition from Phase 6

Phases 1–3 established a canonical semantic interchange contract, bounded evidence-grounded reasoning, and persistent semantic documents. Phases 4–6 established increasingly capable but deliberately bounded raw-text interpretation pipelines. The repository also contains a versioned lexical-candidate adapter and external lexical retrieval/analysis work.

The next development problem is not simply to add more grammar patterns. USG needs a reusable layer that can organize and retrieve semantic knowledge across resources, languages, documents, and contexts without confusing words with senses, senses with concepts, candidate relations with accepted knowledge, or repeated evidence with independent support.

**Phase 7 builds the Semantic Knowledge Integration and Contextual Knowledge Layer.** Its purpose is to make knowledge reusable by multiple interpreters and reasoning services:

1. Represent lexical forms, lexical senses, semantic concepts, classes, predicates, and typed relations as distinct objects.
2. Preserve mappings between language-specific expressions and language-neutral concepts without assuming that translations are identical.
3. ingest provenance-bearing lexical candidates and validated canonical semantic documents through explicit adapters.
4. Reconcile multiple sources by retaining agreement, disagreement, missing data, and ambiguity rather than silently selecting a winner.
5. Retrieve candidate concepts and relations using explicit context and typed associations.
6. Expose the knowledge layer to existing interpretation and reasoning services through read-only, versioned interfaces.
7. Keep every accepted or candidate knowledge item traceable to its sources, rights, transformations, versions, and validation results.

Phase 7 is not a requirement to finish all of Phase 6 first. It can begin using Phase 1–5 accepted contracts, the existing Phase 3 store, and the versioned lexical-candidate interface. Phase 6 outputs may be consumed only through an explicit adapter that preserves their candidate-only status.

## 2. Definition of the Phase 7 knowledge layer

For this roadmap, a **semantic knowledge layer** is a versioned collection of typed, provenance-bearing records and relations that can be searched, compared, and supplied as candidate evidence to interpretation or reasoning services.

It must distinguish at least:

- **Lexical form:** a spelling or surface form in a declared language profile.
- **Lemma:** a normalized lexical unit, distinct from the original source form.
- **Lexical sense:** a source- and language-linked meaning candidate for a lemma.
- **Semantic concept:** a reusable conceptual identifier that may be expressed by multiple lexical senses, subject to explicit mapping evidence.
- **Semantic class:** a typed category used to constrain concepts, entities, events, states, properties, and relations.
- **Predicate/frame:** a versioned description of a relation or event pattern and its role constraints.
- **Knowledge relation:** a directed, typed link between knowledge records with explicit semantics, evidence, and scope.
- **Context:** the language, domain, discourse, time, source, or task conditions under which a candidate is relevant.
- **Evidence/provenance:** the source record, exact locator or span where available, retrieval time, license/rights metadata, transformation history, and integrity digest.
- **Knowledge state:** candidate, validated-for-profile, accepted, deprecated, rejected, or unresolved. State changes must be versioned and auditable.

A knowledge record is not automatically true because it is well-formed, frequent, repeated, retrieved from multiple websites, or accepted by a schema validator. The system must not collapse structural validity, lexical evidence, semantic support, corroboration, entailment, and external verification into one confidence or truth field.

## 3. Goals

1. Establish one explicit, versioned contract for knowledge records, concept mappings, relation types, source evidence, contexts, and lifecycle states.
2. Preserve the distinction between words, lexical senses, concepts, semantic classes, instances, and assertions.
3. Support many-to-many and ambiguous mappings across English, MSA Arabic, and future language profiles.
4. Reuse the existing lexical-candidate adapter and external retrieval outputs without promoting candidate data into canonical runtime resources.
5. Store canonical knowledge snapshots and lifecycle records through the existing SQLite authority; keep indexes and caches rebuildable.
6. Make retrieval context-sensitive while retaining alternatives and explaining the evidence used for ranking.
7. Compare source definitions and relation candidates without inventing synonymy, inheritance, causality, possession, or identity.
8. Allow Phase 2 reasoning and Phase 4–6 interpretation services to consume accepted knowledge through stable, read-only adapters.
9. Provide inspectable API/CLI and Kernel Lab views for concept lookup, sense alternatives, provenance, source conflict, and candidate lifecycle.
10. Establish reproducible evaluation that measures retrieval quality, ambiguity preservation, false merges, provenance integrity, language coverage, and safe abstention separately.

## 4. Non-goals and exclusions

Phase 7 does not attempt to deliver:

- unrestricted natural-language understanding or unrestricted semantic construction;
- automatic truth determination, fact checking, or universal ontology completion;
- automatic identity merging from spelling, translation, embeddings, frequency, co-occurrence, or similarity alone;
- a one-to-one English–Arabic dictionary or a claim that translation proves conceptual identity;
- automatic promotion of external lexical candidates into accepted runtime resources;
- automatic conversion of Phase 6 candidate graphs into canonical assertions;
- unrestricted causal, taxonomic, part-whole, possession, or entailment closure;
- a second canonical database or a replacement for SQLite;
- silent changes to `USG-SEM/1.0`, Phase 1–6 contracts, or archived implementation baselines;
- an obligatory paid service, remote language model, or network dependency for deterministic lookup and validation;
- a requirement that all Phase 6 continuation tasks finish before Phase 7 can be accepted;
- a claim of AGI, human-equivalent knowledge, or complete world knowledge.

## 5. Architectural invariants

### 5.1 Canonical and candidate boundaries

- Validated `USG-SEM/1.0` documents remain the canonical semantic-document representation.
- The proposed `USG-KNOWLEDGE/0.1.0` contract is additive and does not silently extend or reinterpret `USG-SEM/1.0`.
- Lexical retrieval, external dictionaries, parser outputs, model proposals, and Phase 6 graphs enter as candidate evidence unless a separate acceptance gate explicitly permits a more advanced state.
- Candidate records cannot be queried as accepted knowledge unless the caller explicitly requests candidate evidence and the result labels its state.

### 5.2 Identity and translation safety

- A lexical form is not a sense; a sense is not a concept; a concept is not a real-world entity.
- Equal spellings across languages do not establish equal meaning.
- Translations may map to equivalent, overlapping, narrower, broader, related, or unresolved concepts. The relation must be explicit and evidence-bearing.
- Ambiguous mappings remain many-to-many. No default one-to-one merge is permitted.
- A concept identifier is stable only within its declared namespace and versioning policy.

### 5.3 Relations are typed and non-automatic

- Each relation type declares direction, domain/range constraints, symmetry or transitivity only where explicitly defined, and applicable context.
- No inverse, transitive, causal, equivalence, possession, or inheritance relation is inferred merely from a label or association score.
- Definitions and examples are source records, not automatically executable inference rules.
- Usage frequency and association activity may support retrieval ordering but are not truth, entailment, or semantic certainty.

### 5.4 Provenance, rights, and reproducibility

- Every external item retains provider identity, source locator, retrieval date, attribution, known license, rights status, transformation record, and content digest where available.
- Unknown redistribution or automated-evaluation rights remain unknown; the pipeline must not fill legal gaps by assumption.
- Identical source snapshots, adapter versions, mapping rules, and configuration produce deterministic normalized records and replayable reports.
- Conflicting providers remain independently inspectable.

### 5.5 Persistence and compatibility

- The existing Phase 3 SQLite store remains the canonical persistence authority.
- New knowledge tables or packages must use the store-owned connection and documented migration lifecycle.
- Search indexes, embeddings, caches, activation scores, and association rankings are derived and rebuildable.
- Phase 1–6 contracts, accepted corpora, historical releases, and canonical schema remain protected by regression tests.

### 5.6 Conservative retrieval and reasoning

- Context may rank or filter candidates only under explicit, inspectable rules.
- Tied or insufficiently supported candidates remain ambiguous or unresolved.
- A retrieval score is not a calibrated probability or semantic truth value.
- A knowledge item may be useful for search without being eligible for inference.
- Phase 2 rules remain the authority for deterministic inference; Phase 7 supplies typed knowledge and evidence rather than silently inventing new inference rules.

## 6. Target architecture

```text
External lexical sources       Validated USG-SEM documents
          |                              |
          v                              v
  Rights/provenance adapters     Canonical document adapter
          |                              |
          +---------------+--------------+
                          |
                          v
             Normalized candidate evidence
                          |
                          v
          Lexical form / sense / concept mapping
                          |
                          v
           Typed semantic knowledge records
                          |
              +-----------+-----------+
              |                       |
              v                       v
      Source reconciliation     Contextual retrieval
      and conflict ledger       and candidate ranking
              |                       |
              +-----------+-----------+
                          |
                          v
           Versioned knowledge repository
             (existing SQLite authority)
                          |
              +-----------+-----------+
              |                       |
              v                       v
       Phase 2 reasoning       Phase 4–6 interpretation
       read-only knowledge     read-only candidate/accepted
       and evidence adapter    knowledge adapter
              |                       |
              +-----------+-----------+
                          |
                          v
              API / CLI / Kernel Lab
              inspection and replay
```

This is a logical architecture. It does not prescribe a new process, a new database, a vector store, or a mandatory model. A vector or text index may later be used as a rebuildable retrieval accelerator, never as the source of semantic truth.

## 7. Ordered Phase 7 definitions and roadmap

The steps are ordered by contract and data dependencies. Steps explicitly marked independent may be developed in parallel after their shared contracts are frozen.

| Step | Name | Main deliverable | Exit condition |
|---|---|---|---|
| **7.1** | Knowledge integration contract and inventory | Freeze `USG-KNOWLEDGE/0.1.0`, lifecycle states, source/rights metadata, context fields, relation semantics, and adapter boundaries | Contract and inventory are versioned, machine-validated, and protected by tests; no mutation to `USG-SEM/1.0` or Phase 1–6 contracts. |
| **7.2** | Typed lexical-sense and concept model | Distinct schemas for forms, lemmas, senses, concepts, classes, frames, mappings, and relation evidence | Identity, cardinality, direction, language, version, ambiguity, and unresolved cases validate; false implicit merges are rejected. |
| **7.3** | Persistent knowledge repository | Additive repository/catalogue integrated with the existing SQLite store, append-only versions, provenance records, and rebuildable indexes | Round-trip, integrity, migration, atomicity, replay, and no-second-authority tests pass. |
| **7.4** | Source adapters and incremental acquisition | Read-only ingestion from the external lexical candidate adapter and validated canonical documents, with rights-aware manifests | Source records retain attribution, rights status, digest, provider disagreements, transformations, and candidate state; prohibited or unknown rights are not silently accepted. |
| **7.5** | Cross-language sense and concept alignment | Many-to-many mappings between English/MSA lexical senses and semantic concepts, with explicit equivalence/relatedness distinctions | Ambiguous, overlapping, narrower, broader, and unresolved mappings remain separate; translation and spelling alone never create identity. |
| **7.6** | Typed semantic relations and source reconciliation | Relation registry, domain/range validation, evidence aggregation, and provider-conflict ledger | Every relation has declared semantics and evidence; disagreements remain visible; no unsupported inverse/transitive/causal closure occurs. |
| **7.7** | Contextual retrieval and association ranking | Deterministic lookup across active and secondary candidates using explicit language/domain/context features | Retrieval is reproducible and explainable; ties and insufficient evidence preserve ambiguity; usage/activity never becomes truth or entailment. |
| **7.8** | Read-only integration with interpretation and reasoning | Versioned adapters for Phase 2 rule services and Phase 4/5 interpreters; optional Phase 6 adapter preserves candidate-only labels | Existing services can query declared knowledge without runtime mutation; unaccepted Phase 6 outputs cannot be promoted; protected regressions pass. |
| **7.9** | Knowledge inspection API, CLI, and Kernel Lab | Query concepts/senses/relations, inspect provenance/conflicts, compare alternatives, and replay an acquisition run | API, CLI, and UI share the same application/repository services; every result shows source, state, version, context, and unresolved alternatives. |
| **7.10** | Evaluation, performance, and Phase 7 exit acceptance | Frozen multilingual retrieval/mapping/reconciliation suite, adversarial negatives, rights/provenance checks, replay, and integrated regressions | Each enabled language/source/relation profile passes its own gates; false merges and unsupported promotion are zero in the acceptance set; limitations and unsupported profiles are published. |

## 8. Dependencies and parallelism

### Required before Phase 7 implementation

- Phase 1 semantic interchange and adapter acceptance.
- Phase 2 explicit rule model, deterministic inference, evidence boundaries, and derivation traces.
- Phase 3 canonical SQLite store and query/application services.
- Phase 5 versioned lexical-candidate adapter contract and bounded interpreter baseline.
- Phase 6 bounded automatic exit record, used only within its registered scope.

### Explicitly not required

- Completion of productive coordination or all broader Phase 6 grammar families.
- Naturalistic semantic accuracy for every Phase 6 profile.
- Unique discourse identity resolution.
- Candidate-to-canonical semantic assertion projection.
- Completion of all external lexical crawling or full upstream dictionary coverage.

### Parallel work policy

- Phase 6 continuation items are managed separately in the tracker; they may continue while Phase 7 progresses.
- Phase 7 steps 7.4 and 7.5 may begin in parallel after 7.1–7.3 contracts are stable.
- Step 7.6 can begin after the relation registry in 7.2 is stable and can use fixture data before the full source ingestion path exists.
- Step 7.7 depends on the typed model and initial records, not on completion of every source adapter.
- Step 7.8 must be read-only first; write/promotion behavior is outside its initial scope.
- Step 7.9 integrates only operations with stable contracts.
- Step 7.10 is the final gate and may not be passed by aggregate-only results.

## 9. Evaluation and acceptance policy

Evaluate each dimension independently and report by language profile, provider, relation family, and knowledge state:

1. **Identity safety:** false concept merges, false equivalence mappings, and unresolved identity preservation.
2. **Retrieval:** lexical-form and sense candidate precision/recall, ranking stability, and context-specific retrieval.
3. **Ambiguity:** alternative preservation, tie handling, and abstention when evidence is insufficient.
4. **Relation correctness:** exact relation type, direction, domain/range, and forbidden closure behavior.
5. **Evidence quality:** provenance completeness, source locator validity, digest integrity, attribution, and rights-state handling.
6. **Conflict handling:** source disagreement is surfaced without silent source winner selection.
7. **Persistence:** immutable versions, deterministic replay, migration integrity, and canonical SQLite authority.
8. **Integration:** Phase 2 and Phase 4/5 compatibility; Phase 6 candidate-only boundary preservation.
9. **Operational behavior:** clean installation, API/CLI/UI consistency, latency, resource use, and explicit incomplete outcomes.

A successful import, schema validation, high retrieval score, or workflow run is not by itself semantic acceptance. Every acceptance report must identify its population, source licenses, language profile, version pins, denominator, thresholds, failed cases, and non-claims. Naturalistic, synthetic, controlled, and operational populations must remain separate.

## 10. Deliverables and governance

Every Phase 7 implementation PR must include:

- the corresponding step/contract change;
- implementation and regression tests;
- source and rights metadata when external data is involved;
- reproducible fixtures/reports and exact code/resource versions;
- updates to this roadmap and the central documentation hub when status or navigation changes;
- a clear statement of whether outputs are candidate, validated, or accepted;
- proof that Phase 1–6 protected contracts and baselines remain unchanged.

No Phase 7 task may rewrite a previously accepted phase's meaning or make that phase's remaining research queue a prerequisite for forward progress. The Phase 6 Continuation Tracker is the independent status source for its open construction and evaluation work.

## 11. Initial implementation sequence

1. Implement Step 7.1: freeze the knowledge integration contract and inventory.
2. Implement Step 7.2: define lexical-sense, concept, class, frame, mapping, and relation schemas.
3. Implement Step 7.3: add the SQLite-integrated repository with immutable versions and rebuildable indexes.
4. Start source adapters and cross-language mapping as parallel Step 7.4/7.5 work.
5. Add relation reconciliation and contextual retrieval before exposing write-capable integration.
6. Integrate read-only adapters and inspection interfaces.
7. Close Phase 7 with profile-specific tests, reproducible reports, and protected baseline regressions.

**Phase 7 is ready to begin at Step 7.1.** This is a roadmap definition, not a claim that the Phase 7 implementation has already been completed.
