# USG Documentation Hub

> **The central navigation page for the entire USG Workbench repository.** Use this page to find documentation for every major system area, implementation, contract, workflow, evaluation program, and development phase. Detailed documents remain in their relevant folders; this hub is the single directory to reach them.

**Repository:** [wizekin/USG-Workbench](https://github.com/wizekin/USG-Workbench) · **Primary branch:** `main`

## Start here

1. [Main repository README](../README.md) — project definition, current status, active tasks, milestones, and limitations.
2. [System-wide capability assessment](USG-SYSTEM-WIDE-CAPABILITY-ASSESSMENT-2026-11-12.md) — what is implemented, what has evidence, and what remains unverified.
3. [System improvement backlog](USG-SYSTEM-IMPROVEMENT-BACKLOG.md) — prioritized engineering gaps and next work.
4. [Normative specifications](../specifications/README.md) — versioned contracts and schemas.
5. [Implementation index](../implementations/README.md) — distinct implementation lines and baselines.
6. [Interoperability index](../interoperability/README.md) — adapters, registries, and conformance work.
7. [Kernel Lab guide](../tools/usg-kernel-lab/README.md) — how to run and explore the local interface.
8. [Tests index](../tests/README.md) — cross-implementation test suites and commands.

## Navigation

| Documentation area | What it covers |
|---|---|
| [Project-wide architecture, status, governance](#project-wide-documentation-and-system-status) | System assessments, backlog, growth policy, storage, external lexical and cross-runtime topics |
| [Phase 2](#phase-2--semantic-reasoning-foundation) | Semantic reasoning definitions, rules, grounding, evidence, query/explanation, acceptance |
| [Phase 3](#phase-3--persistent-semantic-graph-and-workspace) | Canonical graph store, SQLite persistence, queries, APIs, Kernel Lab integration |
| [Phase 4](#phase-4--bounded-raw-text-interpretation) | Interpretation contract and pipeline stages |
| [Phase 5](#phase-5--bilingual-interpretation-pipeline) | Bilingual interpretation, morphology, syntax, composition, operators, discourse, resources |
| [Phase 5 lexical foundation](#phase-5--lexical-foundation-history) | Lexical resource baselines and evolution |
| [Phase 6](#phase-6--expanded-semantic-interpretation) | Bounded acceptance, continuation workstreams, and independent tracker |
| [Phase 7](#phase-7--semantic-knowledge-integration-and-contextual-knowledge-layer) | Semantic knowledge integration, concept alignment, contextual retrieval, and provenance |
| [Open-World evaluation](#open-world-randomized-evaluation) | Random scenario generation, execution, scoring, coverage, adaptive discovery, naturalistic pilot |
| [Specifications and schemas](#normative-specifications-and-schemas) | Canonical interchange and versioned contracts |
| [Implementations](#implementations-and-versioned-baselines) | JavaScript Workbench, Python kernels, interpreter implementations |
| [Interoperability](#interoperability-adapters-and-registries) | USG-SEM adapters, model families, registries, round-trip tests |
| [Tools and interfaces](#kernel-lab-and-developer-tools) | Kernel Lab and supporting developer tools |
| [Tests](#tests-and-test-guidance) | Test suites and test instructions |
| [Benchmarks](#benchmarks-and-semantic-reasoning-suites) | Frozen datasets, evaluators, benchmark packages |
| [Rules](#rules-and-reasoning-contracts) | Semantic rule definitions, execution, query, and safety contracts |
| [Examples and archives](#examples-and-archived-material) | Examples, historical packages, archive inventories |

## How to use this hub

- Start with the **area entry point** (usually its `README.md`) when one exists.
- Use the phase roadmap for the overall objective and ordered dependencies; use its step documents for the detailed contract and implementation.
- Use specifications as normative contracts. A candidate schema or implementation document does not by itself mean that a capability is accepted or active.
- Use assessments and benchmark reports for evidence. Read their stated population, language, version, and limitations before interpreting a score.
- Treat archived documentation and immutable release baselines as historical; do not assume they describe the current main-branch runtime.
- If a link is missing or a document is added, update this hub in the same pull request.

## Documentation map

### Project-wide documentation and system status

- [EXTERNAL LEXICAL PUD EVALUATION V0.1.0](EXTERNAL-LEXICAL-PUD-EVALUATION-v0.1.0.md) — Evaluation design, results, fixtures, or limitations.
- [EXTERNAL LEXICAL RETRIEVAL AND INCREMENTAL LEARNING V0.1.0](EXTERNAL-LEXICAL-RETRIEVAL-AND-INCREMENTAL-LEARNING-v0.1.0.md) — Lexical resources, morphology, retrieval, or analysis.
- [OW 10 COMPONENT ADAPTER EXPANSION](OW-10-COMPONENT-ADAPTER-EXPANSION.md) — Mapping, interoperability, and conformance behavior.
- [OW 11 OPERATION LEVEL EVALUATION](OW-11-OPERATION-LEVEL-EVALUATION.md) — Evaluation design, results, fixtures, or limitations.
- [OW 12 NATIVE AND BROWSER ORACLES](OW-12-NATIVE-AND-BROWSER-ORACLES.md) — Randomized evaluation design, execution, coverage, or reporting.
- [OW 13 FULL GENERATION AND REASONING COVERAGE](OW-13-FULL-GENERATION-AND-REASONING-COVERAGE.md) — Randomized evaluation design, execution, coverage, or reporting.
- [OW 14 LOCAL API AND WORKBENCH ADAPTERS](OW-14-LOCAL-API-AND-WORKBENCH-ADAPTERS.md) — Mapping, interoperability, and conformance behavior.
- [OW 15 PHASE4 PHASE5 INTERPRETER ORACLES](OW-15-PHASE4-PHASE5-INTERPRETER-ORACLES.md) — Randomized evaluation design, execution, coverage, or reporting.
- [OW 16 REFERENCE KERNEL AND JS SUITE](OW-16-REFERENCE-KERNEL-AND-JS-SUITE.md) — Randomized evaluation design, execution, coverage, or reporting.
- [README](README.md) — Area entry point and local navigation.
- [STORAGE BACKEND EVALUATIONS](STORAGE-BACKEND-EVALUATIONS.md) — Evaluation design, results, fixtures, or limitations.
- [USG AUTONOMOUS GROWTH AND GOVERNANCE](USG-AUTONOMOUS-GROWTH-AND-GOVERNANCE.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG CROSS IMPLEMENTATION CONFORMANCE MATRIX](USG-CROSS-IMPLEMENTATION-CONFORMANCE-MATRIX.md) — Mapping, interoperability, and conformance behavior.
- [USG EXTERNAL LEXICAL SCHEDULED CRAWLER V0.1.0](USG-EXTERNAL-LEXICAL-SCHEDULED-CRAWLER-v0.1.0.md) — Lexical resources, morphology, retrieval, or analysis.
- [USG GROWTH POLICY AND AUTONOMY](USG-GROWTH-POLICY-AND-AUTONOMY.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG NATURALISTIC PUD PILOT](USG-NATURALISTIC-PUD-PILOT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG OPEN WORLD ADAPTIVE DISCOVERY](USG-OPEN-WORLD-ADAPTIVE-DISCOVERY.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD CAMPAIGN REPORTING](USG-OPEN-WORLD-CAMPAIGN-REPORTING.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD CONTINUOUS EXPLORATION](USG-OPEN-WORLD-CONTINUOUS-EXPLORATION.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD EVALUATION PROTOCOL](USG-OPEN-WORLD-EVALUATION-PROTOCOL.md) — Evaluation design, results, fixtures, or limitations.
- [USG OPEN WORLD EXECUTION RUNNER](USG-OPEN-WORLD-EXECUTION-RUNNER.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD EXPANDING COVERAGE](USG-OPEN-WORLD-EXPANDING-COVERAGE.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD FIRST PILOT](USG-OPEN-WORLD-FIRST-PILOT.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD RANDOM SCENARIO GENERATOR](USG-OPEN-WORLD-RANDOM-SCENARIO-GENERATOR.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD RANDOMIZED EVALUATION PLAN](USG-OPEN-WORLD-RANDOMIZED-EVALUATION-PLAN.md) — Evaluation design, results, fixtures, or limitations.
- [USG OPEN WORLD REPOSITORY INVENTORY](USG-OPEN-WORLD-REPOSITORY-INVENTORY.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG OPEN WORLD SCORING AND VALIDATION](USG-OPEN-WORLD-SCORING-AND-VALIDATION.md) — Randomized evaluation design, execution, coverage, or reporting.
- [USG SYSTEM IMPROVEMENT BACKLOG](USG-SYSTEM-IMPROVEMENT-BACKLOG.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SYSTEM WIDE CAPABILITY ASSESSMENT 2026 11 12](USG-SYSTEM-WIDE-CAPABILITY-ASSESSMENT-2026-11-12.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Phase 2 — semantic reasoning foundation

- [PHASE 2 ROADMAP](PHASE-2-ROADMAP.md) — Scope, sequence, dependencies, and acceptance criteria.
- [PHASE 2 STEP 2.1 SEMANTIC REASONING DEFINITIONS](PHASE-2-STEP-2.1-SEMANTIC-REASONING-DEFINITIONS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 2 STEP 2.10 EXIT ACCEPTANCE](PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md) — Completion or acceptance evidence and boundaries.
- [PHASE 2 STEP 2.2 BENCHMARK CORPUS AND EVALUATOR](PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 2 STEP 2.3 RULE MODEL AND REGISTRY](PHASE-2-STEP-2.3-RULE-MODEL-AND-REGISTRY.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 2 STEP 2.4 RULE SEMANTICS AND SAFETY CONTRACT](PHASE-2-STEP-2.4-RULE-SEMANTICS-AND-SAFETY-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 2 STEP 2.5 DETERMINISTIC GROUNDING SERVICES](PHASE-2-STEP-2.5-DETERMINISTIC-GROUNDING-SERVICES.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 2 STEP 2.6 DETERMINISTIC INFERENCE EXECUTOR](PHASE-2-STEP-2.6-DETERMINISTIC-INFERENCE-EXECUTOR.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 2 STEP 2.7 EVIDENCE SUPPORT AND CONFLICT ASSESSMENT](PHASE-2-STEP-2.7-EVIDENCE-SUPPORT-AND-CONFLICT-ASSESSMENT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 2 STEP 2.8 QUERY EXPLANATION INTERFACE](PHASE-2-STEP-2.8-QUERY-EXPLANATION-INTERFACE.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Phase 3 — persistent semantic graph and workspace

- [PHASE 3 COMPLETION RECORD](PHASE-3-COMPLETION-RECORD.md) — Completion or acceptance evidence and boundaries.
- [PHASE 3 ROADMAP](PHASE-3-ROADMAP.md) — Scope, sequence, dependencies, and acceptance criteria.
- [PHASE 3 STEP 3.1 CANONICAL GRAPH STORE CONTRACT](PHASE-3-STEP-3.1-CANONICAL-GRAPH-STORE-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.2 SQLITE CANONICAL STORE](PHASE-3-STEP-3.2-SQLITE-CANONICAL-STORE.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.3 PERSISTENT QUERY](PHASE-3-STEP-3.3-PERSISTENT-QUERY.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.4 SCOPE AWARE RULES](PHASE-3-STEP-3.4-SCOPE-AWARE-RULES.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.5 CONDITIONS CONTRADICTIONS](PHASE-3-STEP-3.5-CONDITIONS-CONTRADICTIONS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.6 LOCAL API CLI](PHASE-3-STEP-3.6-LOCAL-API-CLI.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.7 KERNEL LAB INTEGRATION](PHASE-3-STEP-3.7-KERNEL-LAB-INTEGRATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.8 PACKAGING DEMO](PHASE-3-STEP-3.8-PACKAGING-DEMO.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 3 STEP 3.9 EXIT ACCEPTANCE](PHASE-3-STEP-3.9-EXIT-ACCEPTANCE.md) — Completion or acceptance evidence and boundaries.

### Phase 4 — bounded raw-text interpretation

- [PHASE 4 COMPLETION RECORD](PHASE-4-COMPLETION-RECORD.md) — Completion or acceptance evidence and boundaries.
- [PHASE 4 DEFINITIONS ROADMAP](PHASE-4-DEFINITIONS-ROADMAP.md) — Scope, sequence, dependencies, and acceptance criteria.
- [PHASE 4 STEP 4.1 INTERPRETATION CONTRACT](PHASE-4-STEP-4.1-INTERPRETATION-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.10 MODEL ADAPTER](PHASE-4-STEP-4.10-MODEL-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [PHASE 4 STEP 4.11 INTEGRATED API](PHASE-4-STEP-4.11-INTEGRATED-API.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.12 BENCHMARK](PHASE-4-STEP-4.12-BENCHMARK.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 4 STEP 4.13 EXIT ACCEPTANCE](PHASE-4-STEP-4.13-EXIT-ACCEPTANCE.md) — Completion or acceptance evidence and boundaries.
- [PHASE 4 STEP 4.2 SOURCE INGESTION SEGMENTATION](PHASE-4-STEP-4.2-SOURCE-INGESTION-SEGMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.3 LEXICAL ANALYSIS](PHASE-4-STEP-4.3-LEXICAL-ANALYSIS.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE 4 STEP 4.4 SYNTAX ANALYSIS](PHASE-4-STEP-4.4-SYNTAX-ANALYSIS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.5 SEMANTIC COMPOSITION](PHASE-4-STEP-4.5-SEMANTIC-COMPOSITION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.6 MENTIONS REFERENCE](PHASE-4-STEP-4.6-MENTIONS-REFERENCE.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.7 DISCOURSE CONTEXT](PHASE-4-STEP-4.7-DISCOURSE-CONTEXT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.8 ASSERTION EVIDENCE](PHASE-4-STEP-4.8-ASSERTION-EVIDENCE.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 4 STEP 4.9 RESOURCE REGISTRY](PHASE-4-STEP-4.9-RESOURCE-REGISTRY.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Phase 5 — bilingual interpretation pipeline

- [PHASE 5 COMPLETION RECORD](PHASE-5-COMPLETION-RECORD.md) — Completion or acceptance evidence and boundaries.
- [PHASE 5 DEFINITIONS ROADMAP](PHASE-5-DEFINITIONS-ROADMAP.md) — Scope, sequence, dependencies, and acceptance criteria.
- [PHASE 5 STEP 5.1 INTERPRETATION EXPANSION CONTRACT](PHASE-5-STEP-5.1-INTERPRETATION-EXPANSION-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.10 API CLI KERNEL LAB](PHASE-5-STEP-5.10-API-CLI-KERNEL-LAB.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.11 BENCHMARK EXIT ACCEPTANCE](PHASE-5-STEP-5.11-BENCHMARK-EXIT-ACCEPTANCE.md) — Completion or acceptance evidence and boundaries.
- [PHASE 5 STEP 5.2 BENCHMARK FOUNDATION](PHASE-5-STEP-5.2-BENCHMARK-FOUNDATION.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 5 STEP 5.3 LEXICAL MORPHOLOGY RESOURCES](PHASE-5-STEP-5.3-LEXICAL-MORPHOLOGY-RESOURCES.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE 5 STEP 5.4 CLAUSE SEGMENTATION SYNTAX](PHASE-5-STEP-5.4-CLAUSE-SEGMENTATION-SYNTAX.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.5 NESTED SEMANTIC COMPOSITION](PHASE-5-STEP-5.5-NESTED-SEMANTIC-COMPOSITION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.6 SCOPED OPERATORS](PHASE-5-STEP-5.6-SCOPED-OPERATORS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.7 COORDINATION](PHASE-5-STEP-5.7-COORDINATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.8 DISCOURSE REFERENCE](PHASE-5-STEP-5.8-DISCOURSE-REFERENCE.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 5 STEP 5.9 RESOURCE CATALOGUE](PHASE-5-STEP-5.9-RESOURCE-CATALOGUE.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Phase 5 — lexical foundation history

- [PHASE5 LEXICAL FOUNDATION BASELINE](PHASE5-LEXICAL-FOUNDATION-BASELINE.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE5 LEXICAL FOUNDATION V0.4.0](PHASE5-LEXICAL-FOUNDATION-v0.4.0.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE5 LEXICAL FOUNDATION V0.5.0](PHASE5-LEXICAL-FOUNDATION-v0.5.0.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE5 LEXICAL FOUNDATION V0.6.0](PHASE5-LEXICAL-FOUNDATION-v0.6.0.md) — Lexical resources, morphology, retrieval, or analysis.

### Phase 6 — expanded semantic interpretation
- [PHASE 6 STEP 6.6 AUTOMATIC SYNTHETIC REFERENCE PROTOCOL](PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md) — Automatic bilingual semantic reference generation, acceptance gates, benchmark scope, and limits.

- [PHASE 6 BENCHMARK ANNOTATION CORRECTION 0.3.1](PHASE-6-BENCHMARK-ANNOTATION-CORRECTION-0.3.1.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 6 BENCHMARK ANNOTATION CORRECTION 0.3.2](PHASE-6-BENCHMARK-ANNOTATION-CORRECTION-0.3.2.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 6 DEFINITIONS ROADMAP](PHASE-6-DEFINITIONS-ROADMAP.md) — Bounded exit scope, accepted steps, dependencies, and remaining limitations.
- [PHASE 6 CONTINUATION TRACKER](PHASE-6-CONTINUATION-TRACKER.md) — Independent non-blocking workstream ledger and scheduled PR/check monitoring.
- [PHASE 6 AUTOMATIC ACCEPTANCE FACTORY](PHASE-6-AUTOMATIC-ACCEPTANCE-FACTORY.md) — Graph-first bilingual corpus generation, end-to-end scoring, preservation and integration checks, and report interpretation.
- [PHASE 6 BOUNDED AUTOMATIC ACCEPTANCE RECORD](PHASE-6-BOUNDED-AUTOMATIC-ACCEPTANCE-RECORD.md) — Accepted registered-profile results, exact corpus digest, per-profile metrics, and explicit limitations for Steps 6.7–6.14.
- [PHASE 6 STEPS 6.7–6.14 CANDIDATE INTEGRATION](PHASE-6-STEPS-6.7-6.14-COMPLETION-IMPLEMENTATION.md) — Candidate composition, strict-template extraction, API/CLI/Kernel Lab integration, SQLite replay, and capability limitations.
- [PHASE 6 INTEGRATED INTERPRETER AND BRIDGE VALIDATION](PHASE-6-INTEGRATED-INTERPRETER-AND-BRIDGE-VALIDATION.md) — Shared bilingual execution path, candidate graph conversion, canonical OPAQUE preservation, and bridge-regression scope.
- [PHASE 6 STEP 6.1 INTERPRETATION AND PROJECTION CONTRACT](PHASE-6-STEP-6.1-INTERPRETATION-AND-PROJECTION-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.2 EXPANDED BENCHMARK AND EVALUATOR](PHASE-6-STEP-6.2-EXPANDED-BENCHMARK-AND-EVALUATOR.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 6 STEP 6.3 TYPED ROLES FRAMES VALENCY](PHASE-6-STEP-6.3-TYPED-ROLES-FRAMES-VALENCY.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.4 CAMEL MSA MORPHOLOGY](PHASE-6-STEP-6.4-CAMEL-MSA-MORPHOLOGY.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE 6 STEP 6.4 CONTEXTUAL MSA DISAMBIGUATION](PHASE-6-STEP-6.4-CONTEXTUAL-MSA-DISAMBIGUATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.4 LEXICAL MORPHOLOGY RESOURCES](PHASE-6-STEP-6.4-LEXICAL-MORPHOLOGY-RESOURCES.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE 6 STEP 6.4 PUD MORPHOLOGY](PHASE-6-STEP-6.4-PUD-MORPHOLOGY.md) — Lexical resources, morphology, retrieval, or analysis.
- [PHASE 6 STEP 6.4 SPACY DEPENDENCIES](PHASE-6-STEP-6.4-SPACY-DEPENDENCIES.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.4 SPACY ENGLISH](PHASE-6-STEP-6.4-SPACY-ENGLISH.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.5 ACCEPTANCE](PHASE-6-STEP-6.5-ACCEPTANCE.md) — Completion or acceptance evidence and boundaries.
- [PHASE 6 STEP 6.5 PREDICATE ARGUMENT STRUCTURES](PHASE-6-STEP-6.5-PREDICATE-ARGUMENT-STRUCTURES.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 BENCHMARK V0.4.0](PHASE-6-STEP-6.6-BENCHMARK-V0.4.0.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 6 STEP 6.6 BENCHMARK V0.4.1](PHASE-6-STEP-6.6-BENCHMARK-V0.4.1.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 6 STEP 6.6 BENCHMARK V0.4.2](PHASE-6-STEP-6.6-BENCHMARK-V0.4.2.md) — Evaluation design, results, fixtures, or limitations.
- [PHASE 6 STEP 6.6 CANDIDATE INTERPRETER](PHASE-6-STEP-6.6-CANDIDATE-INTERPRETER.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 EXTERNAL PUD AUDIT](PHASE-6-STEP-6.6-EXTERNAL-PUD-AUDIT.md) — Evidence audit, feasibility review, or data-quality assessment.
- [PHASE 6 STEP 6.6 HELDOUT V0.4.3](PHASE-6-STEP-6.6-HELDOUT-V0.4.3.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 INDEPENDENT GOLD DATASET AUDIT](PHASE-6-STEP-6.6-INDEPENDENT-GOLD-DATASET-AUDIT.md) — Evidence audit, feasibility review, or data-quality assessment.
- [PHASE 6 STEP 6.6 INDEPENDENT GOLD ACCEPTANCE PROTOCOL](PHASE-6-STEP-6.6-INDEPENDENT-GOLD-ACCEPTANCE-PROTOCOL.md) — Independent annotation, rights, leakage, and acceptance requirements.
- [PHASE 6 STEP 6.6 NOMINAL MODIFIER SEMANTICS](PHASE-6-STEP-6.6-NOMINAL-MODIFIER-SEMANTICS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 PUD CONTEXTUAL POS](PHASE-6-STEP-6.6-PUD-CONTEXTUAL-POS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 PUD POS CROSSVALIDATION](PHASE-6-STEP-6.6-PUD-POS-CROSSVALIDATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 SPACY NOMINAL E2E](PHASE-6-STEP-6.6-SPACY-NOMINAL-E2E.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 STANZA ARABIC E2E](PHASE-6-STEP-6.6-STANZA-ARABIC-E2E.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [PHASE 6 STEP 6.6 UD NOMINAL ADAPTER](PHASE-6-STEP-6.6-UD-NOMINAL-ADAPTER.md) — Mapping, interoperability, and conformance behavior.

### Phase 7 — semantic knowledge integration and contextual knowledge layer

- [Phase 7 evaluation and exit acceptance](PHASE-7-STEP-7.10-IMPLEMENTATION.md) — Frozen bilingual positive/negative retrieval cases, polysemy, unresolved mapping, rights, provenance, conflict, and replay gates.
- [Phase 7 knowledge inspection API, CLI, and Kernel Lab](PHASE-7-STEP-7.9-IMPLEMENTATION.md) — Shared read-only inspection service, provenance/conflict views, CLI, and local browser panel.
- [Phase 7 read-only reasoning and interpretation integration](PHASE-7-STEP-7.8-IMPLEMENTATION.md) — Consumer-specific visibility and candidate-only Phase 6 boundary.
- [Phase 7 contextual retrieval and ranking](PHASE-7-STEP-7.7-IMPLEMENTATION.md) — Deterministic exact lexical lookup with language/domain filters, explainable ranking, and ambiguity preservation.
- [Phase 7 typed relations and reconciliation](PHASE-7-STEP-7.6-IMPLEMENTATION.md) — Versioned predicate registry, domain/range validation, and evidence-preserving provider-conflict ledger.
- [Phase 7 bilingual alignment proposals](../tools/phase7_knowledge_alignment/proposals.py) — Candidate-only English/MSA Arabic sense-to-concept grouping with explicit unresolved status.

- [Phase 7 rights-aware source adapters](../tools/phase7_knowledge_sources/adapters.py) — External lexical candidate and validated USG-SEM/1.0 document adapters with explicit rights gating.


- [SQLite knowledge repository](../tools/phase7_knowledge_repository/repository.py) — Append-only snapshots and typed indexes on the existing canonical SQLite connection.

- [USG-KNOWLEDGE/0.1.0 contract](../specifications/USG-KNOWLEDGE-0.1.0.md) — Normative knowledge bundle contract.
- [Knowledge record-kinds registry](../specifications/USG-KNOWLEDGE-RECORD-KINDS-0.1.0.md) — Typed forms, lemmas, senses, concepts, classes, and frames.
- [Phase 7 contract validator](../tools/phase7_knowledge_contract/validate.py) — Structural and cross-reference validation.


- [PHASE 7 DEFINITIONS ROADMAP](PHASE-7-DEFINITIONS-ROADMAP.md) — The next mainline development phase: typed concepts and lexical senses, provenance-bearing knowledge, cross-language mappings, contextual retrieval, source reconciliation, and read-only integration with existing reasoning/interpreters.

### Open-World randomized evaluation

- [Campaign Report](../evaluations/open-world/campaigns/OWC-OW6-43015126807-1/campaign-report.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Normative specifications and schemas

- [Phase 6 independent semantic-gold manifest schema 1.0](../specifications/phase6-independent-gold-manifest-1.0.schema.json) — Machine-readable rights, provenance, annotation independence, ten-profile coverage, and leakage requirements.

- [README](../specifications/README.md) — Area entry point and local navigation.
- [USG SEM 1.0](../specifications/USG-SEM-1.0.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Implementations and versioned baselines

- [README](../implementations/README.md) — Area entry point and local navigation.
- [README](../implementations/python-kernel/README.md) — Area entry point and local navigation.
- [DESIGN](../implementations/python-kernel/v0.4.0/DESIGN.md) — Architecture and design rationale.
- [IMPLEMENTATION V03](../implementations/python-kernel/v0.4.0/IMPLEMENTATION-v03.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [IMPLEMENTATION V04](../implementations/python-kernel/v0.4.0/IMPLEMENTATION-v04.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [IMPLEMENTATION](../implementations/python-kernel/v0.4.0/IMPLEMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [README](../implementations/python-kernel/v0.4.0/README.md) — Area entry point and local navigation.
- [SEMANTIC KERNEL KIND FIX](../implementations/python-kernel/v0.4.0/SEMANTIC-KERNEL-KIND-FIX.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [SPECIFICATION](../implementations/python-kernel/v0.4.0/SPECIFICATION.md) — Contract, schema, or normative technical definition.
- [VERIFICATION V03](../implementations/python-kernel/v0.4.0/VERIFICATION-v03.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [VERIFICATION V04](../implementations/python-kernel/v0.4.0/VERIFICATION-v04.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [VERIFICATION](../implementations/python-kernel/v0.4.0/VERIFICATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [INITIAL DESIGN](../implementations/python-kernel/v0.4.0/docs/INITIAL-DESIGN.md) — Architecture and design rationale.
- [DESIGN](../implementations/python-kernel/v0.5.0/DESIGN.md) — Architecture and design rationale.
- [IMPLEMENTATION V03](../implementations/python-kernel/v0.5.0/IMPLEMENTATION-v03.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [IMPLEMENTATION V04](../implementations/python-kernel/v0.5.0/IMPLEMENTATION-v04.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [IMPLEMENTATION](../implementations/python-kernel/v0.5.0/IMPLEMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [README](../implementations/python-kernel/v0.5.0/README.md) — Area entry point and local navigation.
- [SEMANTIC KERNEL KIND FIX](../implementations/python-kernel/v0.5.0/SEMANTIC-KERNEL-KIND-FIX.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [SPECIFICATION](../implementations/python-kernel/v0.5.0/SPECIFICATION.md) — Contract, schema, or normative technical definition.
- [VERIFICATION V03](../implementations/python-kernel/v0.5.0/VERIFICATION-v03.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [VERIFICATION V04](../implementations/python-kernel/v0.5.0/VERIFICATION-v04.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [VERIFICATION](../implementations/python-kernel/v0.5.0/VERIFICATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [INITIAL DESIGN](../implementations/python-kernel/v0.5.0/docs/INITIAL-DESIGN.md) — Architecture and design rationale.
- [README](../implementations/semantic-workbench-js/README.md) — Area entry point and local navigation.
- [ARCHITECTURE](../implementations/semantic-workbench-js/v0.5.4/ARCHITECTURE.md) — Architecture and design rationale.
- [CHANGELOG](../implementations/semantic-workbench-js/v0.5.4/CHANGELOG.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [KAGGLE RUNTIME VALIDATION](../implementations/semantic-workbench-js/v0.5.4/KAGGLE_RUNTIME_VALIDATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [MIGRATION FROM V0.4 TO V0.5](../implementations/semantic-workbench-js/v0.5.4/MIGRATION_FROM_v0.4_TO_v0.5.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [MIGRATION FROM V0.5.0 TO V0.5.1](../implementations/semantic-workbench-js/v0.5.4/MIGRATION_FROM_v0.5.0_TO_v0.5.1.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [MIGRATION FROM V0.5.1 TO V0.5.2](../implementations/semantic-workbench-js/v0.5.4/MIGRATION_FROM_v0.5.1_TO_v0.5.2.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [MIGRATION FROM V0.5.2 TO V0.5.3](../implementations/semantic-workbench-js/v0.5.4/MIGRATION_FROM_v0.5.2_TO_v0.5.3.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [MIGRATION FROM V0.5.3 TO V0.5.4](../implementations/semantic-workbench-js/v0.5.4/MIGRATION_FROM_v0.5.3_TO_v0.5.4.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [MILESTONE 1 STATUS](../implementations/semantic-workbench-js/v0.5.4/MILESTONE_1_STATUS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [OLLAMA KAGGLE CONCURRENT SETUP](../implementations/semantic-workbench-js/v0.5.4/OLLAMA_KAGGLE_CONCURRENT_SETUP.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [README](../implementations/semantic-workbench-js/v0.5.4/README.md) — Area entry point and local navigation.
- [SEMANTIC REPRESENTATION SPEC V0.4](../implementations/semantic-workbench-js/v0.5.4/SEMANTIC_REPRESENTATION_SPEC_v0.4.md) — Contract, schema, or normative technical definition.
- [SEMANTIC REPRESENTATION SPEC V0.5](../implementations/semantic-workbench-js/v0.5.4/SEMANTIC_REPRESENTATION_SPEC_v0.5.md) — Contract, schema, or normative technical definition.
- [SEMANTIC SCHEMA](../implementations/semantic-workbench-js/v0.5.4/SEMANTIC_SCHEMA.md) — Contract, schema, or normative technical definition.
- [TEST PLAN](../implementations/semantic-workbench-js/v0.5.4/TEST_PLAN.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [TEST RESULTS](../implementations/semantic-workbench-js/v0.5.4/TEST_RESULTS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG KAGGLE CONCURRENT SETUP](../implementations/semantic-workbench-js/v0.5.4/USG_KAGGLE_CONCURRENT_SETUP.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC COMPOSITION SPEC V0.5.1](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_COMPOSITION_SPEC_v0.5.1.md) — Contract, schema, or normative technical definition.
- [USG SEMANTIC WORKBENCH V0.4.0 FULL DOCUMENTATION](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.4.0_FULL_DOCUMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.0 FULL DOCUMENTATION](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.0_FULL_DOCUMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.1 CHANGE REPORT](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.1_CHANGE_REPORT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.1 FULL DOCUMENTATION](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.1_FULL_DOCUMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.2 CHANGE REPORT](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.2_CHANGE_REPORT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.2 FULL DOCUMENTATION](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.2_FULL_DOCUMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.3 CHANGE REPORT](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.3_CHANGE_REPORT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.3 FULL DOCUMENTATION](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.3_FULL_DOCUMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.4 CHANGE REPORT](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.4_CHANGE_REPORT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG SEMANTIC WORKBENCH V0.5.4 FULL DOCUMENTATION](../implementations/semantic-workbench-js/v0.5.4/USG_SEMANTIC_WORKBENCH_v0.5.4_FULL_DOCUMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [USG V0.5 SEMANTIC FOUNDATION BLUEPRINT](../implementations/semantic-workbench-js/v0.5.4/USG_V0.5_SEMANTIC_FOUNDATION_BLUEPRINT.md) — Detailed technical documentation, implementation notes, or supporting evidence.

### Interoperability, adapters, and registries

- [PHASE 1 EXIT ACCEPTANCE](../interoperability/PHASE-1-EXIT-ACCEPTANCE.md) — Completion or acceptance evidence and boundaries.
- [README](../interoperability/README.md) — Area entry point and local navigation.
- [README](../interoperability/operator-scope-registry/README.md) — Area entry point and local navigation.
- [README](../interoperability/predicate-frame-registry/README.md) — Area entry point and local navigation.
- [STEP 5A CONTRACT](../interoperability/python-kernel-extension/STEP-5A-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5B IMPLEMENTATION](../interoperability/python-kernel-extension/STEP-5B-IMPLEMENTATION.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5C ADAPTER](../interoperability/python-kernel-extension/STEP-5C-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5D DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5D-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5E SOURCE RECORDS](../interoperability/python-kernel-extension/STEP-5E-SOURCE-RECORDS.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5F REFERENT CONTRACT](../interoperability/python-kernel-extension/STEP-5F-REFERENT-CONTRACT.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5G REFERENT IDENTITY MODEL](../interoperability/python-kernel-extension/STEP-5G-REFERENT-IDENTITY-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5H REFERENT DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5H-REFERENT-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5I NATIVE MENTION MODEL](../interoperability/python-kernel-extension/STEP-5I-NATIVE-MENTION-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5J MENTION DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5J-MENTION-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5K NATIVE ASSERTION MODEL](../interoperability/python-kernel-extension/STEP-5K-NATIVE-ASSERTION-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5L ASSERTION DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5L-ASSERTION-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5M NATIVE EVIDENCE MODEL](../interoperability/python-kernel-extension/STEP-5M-NATIVE-EVIDENCE-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5N EVIDENCE DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5N-EVIDENCE-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5O NATIVE CONTEXT MODEL](../interoperability/python-kernel-extension/STEP-5O-NATIVE-CONTEXT-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5P CONTEXT DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5P-CONTEXT-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5Q NATIVE EXPRESSION RELATION MODEL](../interoperability/python-kernel-extension/STEP-5Q-NATIVE-EXPRESSION-RELATION-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5R EXPRESSION RELATION DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5R-EXPRESSION-RELATION-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5S NATIVE UNRESOLVED ITEM MODEL](../interoperability/python-kernel-extension/STEP-5S-NATIVE-UNRESOLVED-ITEM-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5T UNRESOLVED ITEM DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5T-UNRESOLVED-ITEM-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5T1 TYPED UNRESOLVED REFERENCES](../interoperability/python-kernel-extension/STEP-5T1-TYPED-UNRESOLVED-REFERENCES.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5U NATIVE DERIVATION MODEL](../interoperability/python-kernel-extension/STEP-5U-NATIVE-DERIVATION-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5V DERIVATION DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5V-DERIVATION-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5W NATIVE DEFINITIONS MODEL](../interoperability/python-kernel-extension/STEP-5W-NATIVE-DEFINITIONS-MODEL.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [STEP 5X DEFINITIONS DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5X-DEFINITIONS-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5Y COMPLETE DOCUMENT ADAPTER](../interoperability/python-kernel-extension/STEP-5Y-COMPLETE-DOCUMENT-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [STEP 5Y1 COMPOSE TYPED UNRESOLVED ADAPTER](../interoperability/python-kernel-extension/STEP-5Y1-COMPOSE-TYPED-UNRESOLVED-ADAPTER.md) — Mapping, interoperability, and conformance behavior.
- [README](../interoperability/python_adapter/README.md) — Area entry point and local navigation.
- [README](../interoperability/round-trip-conformance/README.md) — Area entry point and local navigation.
- [README](../interoperability/workbench_adapter/README.md) — Area entry point and local navigation.

### Kernel Lab and developer tools

- [README](../tools/semantic_grounding_v1_0_0/README.md) — Area entry point and local navigation.
- [README](../tools/usg-kernel-lab/README.md) — Area entry point and local navigation.

### Tests and test guidance

- [README](../tests/README.md) — Area entry point and local navigation.

### Benchmarks and semantic reasoning suites

- [README](../benchmarks/phase5-interpretation-v0.2.1/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase5-interpretation/v0.2.0/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase6-interpretation-v0.3.0/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase6-interpretation-v0.3.1/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase6-interpretation-v0.3.2/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase6-interpretation-v0.4.0/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase6-interpretation-v0.4.1/README.md) — Area entry point and local navigation.
- [README](../benchmarks/phase6-interpretation-v0.4.2/README.md) — Area entry point and local navigation.
- [README](../benchmarks/semantic-reasoning/evidence-v1.0.0/README.md) — Area entry point and local navigation.
- [README](../benchmarks/semantic-reasoning/executor-v1.0.0/README.md) — Area entry point and local navigation.
- [README](../benchmarks/semantic-reasoning/query-v1.0.0/README.md) — Area entry point and local navigation.
- [README](../benchmarks/semantic-reasoning/v1.0.0/README.md) — Area entry point and local navigation.

### Rules and reasoning contracts

- [README](../rules/semantic-reasoning/execution/v1.0.0/README.md) — Area entry point and local navigation.
- [README](../rules/semantic-reasoning/query/v1.0.0/README.md) — Area entry point and local navigation.
- [README](../rules/semantic-reasoning/semantics/v1.0.0/README.md) — Area entry point and local navigation.
- [README](../rules/semantic-reasoning/v1.0.0/README.md) — Area entry point and local navigation.

### Examples and archived material

- [ARCHIVE INVENTORY](../ARCHIVE_INVENTORY.md) — Detailed technical documentation, implementation notes, or supporting evidence.
- [README](../archives/README.md) — Area entry point and local navigation.
- [README](../archives/python-kernel/README.md) — Area entry point and local navigation.
- [README](../archives/workbench/README.md) — Area entry point and local navigation.
- [README](../examples/phase3/README.md) — Area entry point and local navigation.

---

## Maintenance and completeness policy

This page is the repository-wide documentation directory. It is intentionally a navigation hub, not a replacement for detailed technical specifications.

For every new feature or meaningful change:

1. Update the detailed documentation for the affected component in the same pull request.
2. Add the document to the appropriate section of this hub, with a useful description.
3. Update the relevant roadmap, backlog, assessment, or acceptance record when status changes.
4. Update the main [repository README](../README.md) when project-level status, major architecture, user entry points, active workflows, or milestones change.
5. Keep implementation status, evidence status, and semantic capability claims distinct.

**Current coverage:** this index was generated from the Markdown files present in the repository tree on the update date. It links to the repository's existing Markdown documentation; it does not imply that every component is complete, integrated, or independently validated.
