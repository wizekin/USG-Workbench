# Phase 6 Steps 6.7–6.14 — Integrated Candidate Interpreter and Exit Record

**Status:** integrated implementation path added; construction families remain candidate-only and the final Phase 6 acceptance gate remains open.  
**Interpretation contract:** \`USG-INTERPRET/0.3.0\`.  
**Canonical semantic interchange:** \`USG-SEM/1.0\` is unchanged.  
**Persistence:** Phase 6 candidate runs use the existing SQLite store-owned connection and append-only run table.

## Integrated execution path

The implementation is no longer limited to separately supplied graphs or one strict-template button. The new \`Phase6IntegratedInterpreter\` executes the existing bilingual Phase 5 pipeline and carries its outputs into a shared Phase 6 graph:

1. Versioned lexical analysis and morphology.
2. Sentence and clause segmentation with explicit conjunction/subordinator boundaries.
3. Syntax and predicate/argument candidate generation.
4. Operator candidates with explicit target and scope.
5. Discourse mentions and possible antecedents, without identity resolution.
6. Phase 6 graph composition and source-span validation.
7. Strict Phase 6 template fallback only when Phase 5 did not emit a predicate candidate.
8. Optional append-only run persistence and deterministic replay.

The new route is \`POST /v3/phase6/interpret\`. It returns the Phase 5 stage envelope, Phase 6 graph, candidate status, diagnostics, and a canonical preservation preview. The same service is used by the \`phase6-interpret\` CLI command and the new integrated operation in Kernel Lab.

## Steps 6.7–6.11: integrated construction candidates

- **6.7 Coordination:** clause-level AND/OR/CONTRAST candidates are carried from explicit Phase 5 segmentation boundaries. Strict bilingual fallback templates cover one bounded coordinated-subject pattern in each language. Shared-argument behavior is retained only where the underlying stage emits it; the current integration does not claim general phrase-level coordination coverage.
- **6.8 Embedded/subordinate clauses:** clause boundaries are preserved with parent/child clause links. COMPLEMENT, CAUSAL, CONDITIONAL, and TEMPORAL markers are attached as typed candidate relations when both clauses have predicate candidates. Unsupported or unlicensed attachments remain diagnostics.
- **6.9 Voice/speech acts:** the bounded passive-question templates remain available as candidate fallback. The general Phase 5 stage does not yet provide a full passive/imperative recognizer; those constructions are not benchmark-enabled.
- **6.10 Operators:** existing Phase 5 negation, modality, tense, aspect, and quantifier candidates are projected into the Phase 6 graph with exact marker spans and explicit local targets. Scope ambiguity and unsupported targets remain visible; no sentence-wide scope is guessed.
- **6.11 Discourse:** Phase 5 mention and antecedent alternatives are copied into the Phase 6 graph. Candidate links never become resolved referent identity. Missing or competing antecedents remain unresolved.

Every generated node and relation uses exact Unicode code-point spans into the original source. The Phase 6 composition engine checks references, relation types, operator targets, clause-parent cycles, and source evidence.

## Step 6.12: preservation projection versus semantic projection

The previous semantic projection guard remains in place: Phase 6 candidate relations are not silently converted into canonical assertions.

A new **lossless preservation projection** creates a valid \`USG-SEM/1.0\` document containing:
- the exact source and SHA-256 digest;
- one \`OPAQUE\` expression marked \`UNRESOLVED\`;
- the complete candidate graph, feature list, provenance, and safety metadata in a namespaced extension and the OPAQUE payload;
- exact source evidence with \`semanticSupportStatus=NOT_ESTABLISHED\`;
- an unresolved-item record and a proposed derivation;
- no referents and no assertions.

This preserves the complete candidate payload in the canonical document format without pretending it is a canonical semantic interpretation. The API validates the document through the existing canonical store validator before returning it. This is not a lossless semantic-meaning projection and does not enable candidate assertions.

## Step 6.13: integrated interfaces and persistence

- API: \`POST /v3/phase6/interpret\` plus the existing compose, extract, list, get, and replay endpoints.
- CLI: \`usg-workbench phase6-interpret source.txt --language en|ar [--db PATH] [--no-persist] [--output PATH]\`.
- Kernel Lab: one integrated Phase 6 action runs the pipeline and displays the resulting graph and all diagnostics; lower-level extract/compose tools remain available for debugging.
- Persistence: Phase 6 run records still use the existing store-owned SQLite connection, immutable triggers, content digests, and replay path. The canonical OPAQUE preservation preview is not automatically committed as a canonical assertion/document revision.

## Step 6.14: integrated bridge regression

The new \`tools/phase6_broader_semantics_v0_1/integrated_benchmark.py\` runs the integrated Phase 6 graph builder over every case in the frozen 100-case Phase 5 v0.2.1 bilingual corpus. It checks whether the Phase 6 graph preserves the Phase 5 benchmark's uniquely licensed construction, AGENT/ACTION/PATIENT role values, exact spans, and abstention on negative/ambiguous target cases.

This is a bridge-regression benchmark. It demonstrates that the new graph and interfaces carry accepted Phase 5 results without loss; it is not new naturalistic accuracy evidence for Phase 6 Steps 6.7–6.11. The workflow also runs the Phase 6 graph contract tests, the integrated API/projection/replay tests, Step 6.5 regression, and prior protected-path checks.

## Current acceptance boundary

The following are implemented and regression-tested as candidate behavior:
- integrated bilingual pipeline composition and Phase 5 stage reuse;
- explicit clause boundaries and typed clause relation candidates;
- operator target/scope transfer;
- unresolved discourse candidate transfer;
- strict-template fallback for the ten existing English/MSA patterns;
- lossless OPAQUE preservation into the unchanged canonical schema;
- API, CLI, Kernel Lab, append-only SQLite run storage, and replay;
- frozen Phase 5 to Phase 6 graph-bridge regression.

The following remain **not accepted as general Phase 6 semantic capabilities**:
- productive coordination and shared-argument extraction beyond the narrow registered cases;
- broad complement, relative, causal, conditional, temporal, and argument-gap attachment;
- general active/passive, question, command, and request interpretation;
- cross-construction operator scope beyond current Phase 5 candidate behavior;
- unique discourse-reference resolution;
- semantic projection of candidate graphs into canonical assertions;
- per-construction naturalistic Phase 6 accuracy and final full exit acceptance.

No human annotation step, manual runtime review, or unverified bilingual gold dataset is introduced by this increment. Runtime output stays \`CANDIDATE_ONLY\`; unsupported text abstains. The Phase 6 roadmap stays IN PROGRESS until each construction has independent per-language evidence and the exact integrated exit gate passes.
