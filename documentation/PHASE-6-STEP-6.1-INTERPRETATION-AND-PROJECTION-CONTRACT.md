# Phase 6 — Step 6.1: Interpretation and Projection Contract

**Status:** FROZEN FOR PHASE 6 IMPLEMENTATION  
**Contract:** `USG-INTERPRET/0.3.0`  
**Previous contract:** `USG-INTERPRET/0.2.0` remains immutable and regression-protected  
**Earlier contract:** `USG-INTERPRET/0.1.0` remains immutable and regression-protected  
**Semantic interchange:** `USG-SEM/1.0` remains normative and unchanged  
**Canonical persistence:** the existing Phase 3 SQLite store remains the only canonical semantic-document store  
**Language profiles:** standard written English (`en`) and Modern Standard Arabic (`ar`), independently evaluated  
**Execution:** deterministic, offline baseline; optional model adapters cannot bypass validation  
**Acceptance:** automated contract/schema/compatibility tests; no runtime human-review gate  
**Next gate:** Step 6.2 — frozen expanded benchmark corpus and evaluator

## 1. Decision and compatibility boundary

Phase 6 creates an additive interpretation line, `USG-INTERPRET/0.3.0`. It MUST be implemented in a separate versioned package or module boundary. It MUST NOT mutate, relabel, or silently extend the Phase 5 `USG-INTERPRET/0.2.0` implementation, schemas, resources, fixtures, benchmark results, or immutable run artifacts.

The contract version is independent of the Python package version, resource-manifest versions, and the canonical semantic profile version. A new interpretation capability does not justify changing `USG-SEM/1.0`. If a Phase 6 graph cannot be represented without loss in USG-SEM/1.0, preserve the graph and report a blocked/lossy projection with machine-readable diagnostics. A new semantic profile requires a separate versioned architecture decision and conformance suite; it is not authorized by this contract.

The JavaScript Semantic Workbench, Python reference kernel, Phase 5A–5Y native model/document-adapter stream, and archived releases remain separate implementation lines. Reuse is permitted only through explicit public APIs and conformance tests. This contract does not authorize package renames, historical rewrites, or an assumption that one implementation's internal graph is interchangeable with another's.

## 2. Scope and capability claims

This contract defines the result envelope, source/provenance invariants, interpretation-graph boundary, role/frame attachment rules, uncertainty behavior, and projection policy for Phase 6. It does not declare the Phase 6 construction families implemented.

A construction's state MUST be reported distinctly as one of:

- **implemented** — code exists;
- **regression-tested** — deterministic tests exercise the behavior;
- **benchmark-enabled** — the frozen per-language construction benchmark passes all applicable gates;
- **partial/candidate-only** — evidence or candidate structure is retained, but a unique semantic interpretation is not licensed;
- **disabled/unsupported** — no accepted mapping exists for the construction.

Only benchmark-enabled constructions may be advertised as supported. An implemented or regression-tested construction is not automatically supported. A high aggregate benchmark score MUST NOT conceal a failing or unmeasured language, construction, role, or scope family.

Initial language profiles are standard written English and MSA Arabic. Language profiles are independent: passing one profile does not enable the other. Dialects, arbitrary code-switching, unrestricted language coverage, and any unlisted profile remain out of scope.

## 3. Interpretation result envelope

Every Phase 6 run MUST emit a versioned result envelope conforming to `specifications/usg-interpret-0.3.0.schema.json`. It is a processing artifact, not itself a canonical USG-SEM document.

Required envelope information:

- `pipelineContract`: exactly `USG-INTERPRET/0.3.0`;
- `pipelineVersion`: implementation package version, independent of contract version;
- `languageProfile`: explicit versioned profile identifier;
- `completionStatus`: conservative pipeline completion state;
- `sourceSnapshot`: immutable source reference, exact source text, SHA-256 digest, and offset convention;
- `interpretationGraph`: graph conforming to `specifications/usg-interpret-expression-graph-0.3.0.schema.json`;
- `stages`: ordered stage outcomes, versions, resource IDs/digests, and diagnostics;
- `diagnostics`: stable machine-readable codes and explanations, with source spans where applicable;
- `alternatives`: retained materially distinct candidates and non-probabilistic ranking metadata;
- `resourceLimits`: declared budgets and whether any budget interrupted processing;
- `projection`: explicit projection state, diagnostics, and a canonical document only when the mapping is complete and lossless.

### 3.1 Completion statuses

| Status | Normative meaning |
|---|---|
| `COMPLETE` | All source content is covered by benchmark-enabled constructions and assembled without unresolved semantic content. |
| `PARTIAL` | Some content is interpreted while one or more spans or structures remain unresolved or unsupported. |
| `AMBIGUOUS` | Multiple materially distinct candidates remain; no unique reading is justified. |
| `UNSUPPORTED` | Input is valid but outside the enabled language/construction profile. |
| `INVALID_INPUT` | Request or source envelope violates input requirements. |
| `INCOMPLETE_RESOURCE_LIMIT` | A declared time, memory, or candidate budget interrupted processing; partial artifacts are retained. |
| `FAILED_VALIDATION` | Candidate output failed deterministic validation and MUST NOT be persisted as accepted semantic output. |

A successful process exit does not imply semantic completeness. A downstream stage MUST NOT upgrade a partial, ambiguous, or unsupported result without a documented resolution rule and source-grounded evidence. The overall status is at least as conservative as the least-resolved required content.

## 4. Source fidelity and provenance

1. Preserve the exact original source string before normalization, tokenization, transliteration, or model processing.
2. The source digest is SHA-256 over the exact UTF-8 encoding of that stored source string.
3. All source offsets are zero-based, end-exclusive Unicode code-point offsets into the exact source string.
4. For every emitted exact span, enforce `source[start:end] == surfaceText`.
5. Normalized strings, lemmas, morphology, transliterations, and parser-internal strings are derived artifacts with explicit source mappings; they never replace the source snapshot.
6. Every graph node and edge MUST identify the source evidence and derivation records that licensed it, or explicitly state that it is a non-surface structural node derived from cited child evidence.
7. A derivation record MUST identify the rule/resource IDs and versions used. Resource digests are retained in stage outcomes or immutable manifests.
8. Reprocessing creates a new immutable run. It MUST NOT overwrite a source snapshot, erase alternatives, or rewrite accepted historical results.
9. Tests MUST cover Arabic diacritics, combining marks, supplementary Unicode code points, punctuation, bidirectional text, repeated whitespace, tabs, and CRLF/LF.

## 5. Interpretation graph and semantic role boundaries

The graph schema defines versioned nodes and directed edges. Node and edge identifiers are opaque and unique within a graph. References MUST resolve. Graph validation MUST reject duplicate IDs, dangling references, invalid source spans, invalid roots, and cycles where a construction declares an acyclic relation.

The graph is deliberately more expressive than the current narrow Phase 5 candidate schema. Its node categories include source/lexical evidence, construction candidates, predicate frames, semantic-role bindings, arguments, modifiers, coordination, clauses/propositions, operators, discourse mentions, reference candidates, and derivations. The schema's extensible attributes are data, not an automatic license to claim a construction is supported.

### 5.1 Predicate frames and semantic roles

- A predicate frame is a versioned semantic resource, not a surface word-order template.
- Each frame identifies its predicate/sense basis, frame version, semantic type, and licensed role slots.
- Each role binding identifies a stable role ID, the frame/slot that licenses it, its filler node, and the source/derivation evidence.
- Semantic roles MUST remain distinct from syntactic functions, token positions, and linear order. Subject/object labels or SVO/VSO order alone MUST NOT determine Agent, Patient, Experiencer, Theme, Recipient, Location, or any other semantic role.
- Required, optional, prohibited, and repeatable slots are frame-specific. Missing required evidence prevents a complete frame binding; it MUST NOT be filled by guessing.
- Language-specific lexical and morphology resources may realize a shared semantic frame differently. English and Arabic mappings are separately benchmarked.
- Unknown lexical senses, competing frame assignments, and ambiguous role bindings remain alternatives or abstentions. Similarity, frequency, activation, and model confidence are not role evidence.

Step 6.3 will define the normative typed frame/role registry schema and constraints. Step 6.1 fixes the boundaries above but does not pre-approve any new frame family.

### 5.2 Composition, modifiers, and operators

Semantic composition MUST preserve typed links, operand identity, nesting, and scope. Modifiers MUST attach to an explicit target. Coordination MUST preserve all conjuncts/disjuncts and grouping. Embedded clauses MUST retain proposition boundaries and typed relations. Negation, modality, tense, aspect, quantification, voice, and speech-act structures MUST retain explicit scope/attachment targets. Surface keyword presence alone is insufficient evidence of an operator or its scope.

## 6. Ambiguity, abstention, and resource limits

- Unknown words, ambiguous lexical senses, competing parses, unsupported constructions, unresolved references, and resource-budget interruptions remain explicit.
- Alternatives MUST retain their distinct graph candidates and source evidence. Ranking metadata is ordinal/retrieval metadata, not calibrated probability.
- No stage may fabricate missing words, silently discard input spans, flatten nested scope, or silently choose an unsupported unique reading.
- Candidate count, wall-clock, and memory budgets may stop processing, but a budget stop produces `INCOMPLETE_RESOURCE_LIMIT` or another appropriately conservative status and retains available partial artifacts.
- Candidate ranking, association activation, usage frequency, recency, and model confidence are not truth, identity, entailment, semantic modality, or calibrated probability.
- A validation failure prevents the candidate from being persisted or projected as accepted semantic output.

## 7. Loss-aware projection to USG-SEM/1.0

Projection is a separate, explicit adapter operation. The interpretation graph remains the authoritative Phase 6 processing artifact. A USG-SEM/1.0 document is emitted only if all meaning-bearing content required for the requested projection is represented by the unchanged canonical schema without silent loss.

Projection states are:

- `NOT_ATTEMPTED` — no projection was requested or run;
- `LOSSLESS` — all required graph content was mapped and the resulting document passed the unchanged USG-SEM/1.0 schema and reference validation;
- `BLOCKED` — a safe projection is not currently possible;
- `LOSSY` — a diagnostic classification for a detected non-lossless mapping; no canonical document may be emitted as if it were complete.

A `LOSSLESS` result MUST include a valid canonical document. A `BLOCKED` or `LOSSY` result MUST include machine-readable diagnostics and MUST NOT present a partial document as a complete canonical document. If a partial canonical projection is useful for inspection, it must be clearly marked as a non-canonical preview outside the accepted document field.

Projection MUST preserve source references, exact evidence spans, referent/mention distinctions, expression scope, assertion versus description, epistemic status, derivation provenance, and unresolved items wherever these are present in the source graph. Exact text alignment does not establish semantic support or entailment. A semantic description does not automatically become an assertion. A question or command does not become an ordinary factual assertion.

USG-SEM/1.0 and its schema are frozen inputs to this adapter. This step adds no new canonical operators, sorts, semantic kinds, or fields to that profile.

## 8. Persistence, resources, and execution

- The existing Phase 3 SQLite store remains the only canonical semantic-document persistence authority.
- Phase 6 run envelopes and graph artifacts are persisted through existing store/application boundaries; no second canonical database or new connection owner is introduced.
- Resources are immutable/versioned and carry IDs, provenance, and content digests. Lexical realizations, morphology, construction rules, predicate frames, discourse resources, provisional associations, and derived retrieval metadata remain distinct classes.
- Caches, indexes, activation scores, and rankings are rebuildable derived data.
- The deterministic baseline is offline and requires no paid API, cloud model, or network access.
- Optional model adapters may propose candidates but MUST NOT bypass source checks, deterministic validators, resource provenance, benchmark enablement, or abstention rules.

## 9. Compatibility and protected paths

Every Phase 6 implementation change MUST preserve and regression-test:

- Phase 4 `USG-INTERPRET/0.1.0` and Phase 5 `USG-INTERPRET/0.2.0` contracts, packages, fixtures, resources, and accepted benchmark artifacts;
- `specifications/USG-SEM-1.0.md` and `specifications/usg-sem-1.0.schema.json`;
- Phase 1–5 acceptance records and frozen benchmark corpora/digests;
- the store-owned SQLite connection and transaction lifecycle;
- checksum-verified archives and historical implementation directories;
- the separate JavaScript Workbench and Python kernel implementation lines;
- existing Phase 5 API, CLI, and Kernel Lab behavior.

No Phase 6 step may silently rewrite a historical release or weaken an earlier acceptance gate. No runtime human review or manual approval queue is required.

## 10. Step 6.1 acceptance criteria

Step 6.1 is accepted when all of the following hold on the exact pull-request head:

1. This contract and both v0.3.0 JSON Schemas are present and version identifiers are consistent.
2. Positive and negative schema fixtures validate with a standards-compliant JSON Schema 2020-12 validator.
3. The envelope rejects an incorrect contract ID, an invalid completion/projection state, and a missing source digest.
4. The graph schema rejects invalid span offsets and malformed node/edge structures.
5. Contract tests verify conservative completion states, source immutability, role/frame boundaries, and loss-aware projection rules.
6. `USG-SEM/1.0`, Phase 4/5 contracts and implementation packages, archives, and historical implementation directories are unchanged.
7. Existing Phase 1–5 regression and compatibility workflows pass.
8. The README and specifications index identify Step 6.1 as accepted and Step 6.2 as next; Phase 6 itself remains IN PROGRESS, not complete.

## 11. Explicit non-claims

This contract does not claim unrestricted English or Arabic understanding, truth determination, fact verification, identity resolution, unrestricted entailment, autonomous knowledge creation, universal semantic coverage, human-equivalent reasoning, or AGI. It defines a safe, testable processing boundary for the bounded constructions that later Phase 6 steps may enable.

**Next step:** Step 6.2 — define the expanded benchmark corpus, gold annotation format, evaluator, per-language/per-construction denominators, and frozen quality gates before implementing new grammar.
