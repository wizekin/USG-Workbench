# USG-KNOWLEDGE/0.1.0 — Semantic Knowledge Bundle Contract

**Status:** normative additive contract for Phase 7 Steps 7.1–7.2  
**Schema:** [usg-knowledge-0.1.0.schema.json](usg-knowledge-0.1.0.schema.json)  
**Compatibility:** does not change or extend the meaning of `USG-SEM/1.0`, Phase 1–6 contracts, or the Phase 3 canonical document store.

## 1. Purpose

This contract transports versioned semantic knowledge records with source provenance, evidence, context, explicit mappings, and typed relations. It is a knowledge interchange envelope, not a truth database, an inference engine, or an automatic ontology merger.

## 2. Identity layers

The following are separate record kinds and must never be collapsed by spelling or similarity:

- `LEXICAL_FORM`: an observed surface spelling in a declared language.
- `LEMMA`: a normalized lexical unit; it does not imply a particular meaning.
- `LEXICAL_SENSE`: a language- and source-linked meaning candidate.
- `CONCEPT`: a namespace-scoped conceptual identifier, not a real-world entity.
- `SEMANTIC_CLASS`: a typed category that constrains eligible concepts or instances.
- `PREDICATE_FRAME`: a versioned relation/event description with role constraints.

Payloads are kind-specific and intentionally extensible at this contract version. Their required structure is specified by the record-kind registry in the step documentation; payload validation must not be mistaken for semantic validation.

## 3. Lifecycle

Allowed states are `CANDIDATE`, `VALIDATED_FOR_PROFILE`, `ACCEPTED`, `DEPRECATED`, `REJECTED`, and `UNRESOLVED`. Every state transition creates a new immutable record version or lifecycle event in the eventual repository. Existing versions are not overwritten.

- Candidate means proposed or imported, not trusted.
- Validated-for-profile means passed named, versioned profile checks only.
- Accepted means admitted by an explicit acceptance policy for a declared scope.
- Deprecated means superseded for new use but retained for history.
- Rejected means explicitly disallowed under a recorded decision.
- Unresolved means evidence does not justify a unique mapping or interpretation.

No state implies global truth.

## 4. Provenance and rights

Every source declares provider, source type, retrieval timestamp, rights status, redistribution status, attribution, and optional locator, license, digest, and adapter version. Unknown rights remain unknown. Restricted or prohibited sources must not be redistributed. A record may retain a pointer and digest to restricted material without copying its protected content.

Every evidence item points to exactly one source record and records its evidence type, support/contradiction status, capture time, locator where available, digest, and transformation identifiers. Model suggestions are explicitly typed as such and are not independent corroboration.

## 5. Mapping and relation semantics

Cross-language and intra-language mappings are explicit, directed, evidence-bearing, and many-to-many. Mapping types are `EQUIVALENT`, `OVERLAPPING`, `NARROWER_THAN`, `BROADER_THAN`, `RELATED_TO`, and `UNRESOLVED`. Equivalence is never inferred from translation, shared spelling, embedding proximity, co-occurrence, or frequency alone.

Knowledge relations are directed. A predicate is a registry key, not an instruction to infer its inverse or transitive closure. No symmetry, transitivity, causality, possession, inheritance, or entailment is implied by a relation label. Such behavior requires a separate, versioned rule contract and its own evidence and acceptance gate.

## 6. Context

Context records are typed as language, domain, discourse, time, task, register, region, or source. Context may filter or rank retrieval candidates under explicit deterministic policies. Context/activity scores are not probabilities, truth values, identity evidence, or entailment.

## 7. Validation layers

Implementations must report separately:

1. JSON structural validity;
2. referential integrity (record/source/evidence/context IDs exist);
3. kind-specific payload validity;
4. rights-policy eligibility;
5. semantic evidence assessment;
6. profile-specific acceptance.

A pass at one layer must not be represented as a pass at another. This schema does not authorize automatic promotion to `ACCEPTED`.

## 8. Persistence boundary

The future repository implementation must use the existing Phase 3 SQLite authority and its caller-owned connection/transaction lifecycle. Search indexes, caches, embeddings, association activation, and retrieval ranks are derived and rebuildable. This contract does not authorize a second canonical database or a change to canonical `USG-SEM/1.0` documents.

## 9. Determinism and evolution

The same bundle, validator version, registry versions, and configuration must yield the same validation findings. Unknown fields are rejected at the envelope and typed metadata levels; kind-specific payloads remain namespaced and extensible. Breaking changes require a new contract major version. Additive compatible changes require a new minor version and migration notes.
