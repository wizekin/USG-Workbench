# USG Workbench

**Universal Semantic Grammar — research, implementation, evaluation, and development workbench**

[![Repository](https://img.shields.io/badge/GitHub-wizekin%2FUSG--Workbench-181717?logo=github)](https://github.com/wizekin/USG-Workbench)
[![Default branch](https://img.shields.io/badge/branch-main-blue)](https://github.com/wizekin/USG-Workbench/tree/main)
[![Phase 7](https://img.shields.io/badge/Phase%207-Steps%207.1--7.5%20merged-success)](documentation/PHASE-7-DEFINITIONS-ROADMAP.md)

> **Status snapshot:** 12 November 2026 · Main branch baseline reviewed at [`2bd0151`](https://github.com/wizekin/USG-Workbench/commit/2bd0151aed762bc8cff4a01015b3504d507fe4c9). Live workflow and campaign links below take precedence over this dated snapshot.

---

## Navigation

Start here — jump directly to any major section:

| | Section | |
|---|---|---|
| 1 | [USG Workbench definition](#usg-workbench-definition) | What this project is and what it is not |
| 2 | [Central documentation hub](documentation/README.md) | One index for all USG documentation across the repository |
| 3 | [Documentation and maintenance policy](#documentation-and-maintenance-policy) | How technical documentation is organized and kept current |
| 4 | [Current running tasks](#current-running-tasks) | Active and scheduled GitHub Actions work |
| 5 | [Complete major tasks](#complete-major-tasks) | Accepted phases and implemented foundations |
| 6 | [Incomplete major tasks](#incomplete-major-tasks) | Remaining work and current blockers |
| 7 | [Architecture and reliability rules](#architecture-and-reliability-rules) | Contracts, data, uncertainty, and evidence boundaries |
| 8 | [How to explore and test USG](#how-to-explore-and-test-usg) | Start the interface and find tests |
| 9 | [Repository structure](#repository-structure) | Where code, specifications, evidence, and data are stored |
| 10 | [Phase 7 definitions roadmap](documentation/PHASE-7-DEFINITIONS-ROADMAP.md) | Semantic knowledge integration; Steps 7.1–7.5 merged; Step 7.6 next |

---

## USG Workbench definition

**USG (Universal Semantic Grammar) Workbench** is a modular, versioned research and engineering project for representing the meaning expressed by language in explicit, inspectable, source-grounded structures. It brings together semantic models, interpretation pipelines, lexical and grammatical resources, symbolic reasoning services, persistent storage, evaluation tools, and development interfaces.

The intended processing path is:

1. Preserve the original source text and its provenance.
2. Segment the source into sentences, clauses, and other relevant units.
3. produce lexical and morphological candidates while retaining unknown forms and ambiguity.
4. Build syntactic, construction, and attachment candidates.
5. Compose typed predicates, arguments, semantic roles, operators, relations, and discourse structures.
6. Validate structures and preserve evidence, derivations, resource versions, and unresolved content.
7. Store, query, replay, inspect, and export supported results.
8. Apply only the reasoning rules and operations that have explicit contracts and adequate evidence.

The architecture is modular: these stages are implemented at different maturity levels and are not all enabled for every input or language.

### What the Workbench is — and is not

- It is a research workbench and a collection of versioned implementations and services, not one unified general-purpose chatbot.
- It is designed to complement language models with explicit semantic structures, deterministic validation, provenance, and bounded symbolic reasoning.
- It does **not** yet provide unrestricted English or Arabic understanding, universal semantic coverage, objective truth verification, human-equivalent reasoning, or AGI.
- A schema-valid graph is not automatically a correct interpretation. A successful workflow is not automatically evidence of semantic accuracy.
- The JavaScript Semantic Workbench, Python reference kernels, Python interpretation pipelines, native model packages, and adapters remain distinct implementation lines until common conformance tests demonstrate otherwise.

The long-term objective is a reusable semantic representation and reasoning architecture that can grow through explicit, traceable, independently evaluated capabilities.

---

## Central documentation hub

**[Open the USG Documentation Hub →](documentation/README.md)**

This is the single navigation page for the repository's documentation. It indexes the documentation across all USG system areas, including architecture, semantic models, specifications and schemas, every development phase and step, implementations and versions, lexical and morphology resources, interpretation pipelines, reasoning, persistence, APIs, Kernel Lab, interoperability, tests, benchmarks, Open-World evaluation, automation, governance, and archived baselines.

Use the hub to reach the detailed document you need without searching through repository folders. New documentation must be added to the hub in the same pull request that introduces or changes the feature.

## Documentation and maintenance policy

Documentation is part of the implementation, not an optional activity after coding. It must explain the Workbench's architecture, contracts, modules, interfaces, data, evaluation, operation, limitations, and current development state.

### Documentation rule for every feature

**Every new feature or meaningful change must update its relevant detailed documentation in the same pull request.** Documentation must be updated as soon as the feature is implemented and before that change is considered complete.

A feature's documentation should explain, where applicable:

- its purpose and the problem it solves;
- its place in the USG architecture and its dependencies;
- its inputs, outputs, data structures, and processing behavior;
- relevant schemas, contracts, versions, and compatibility constraints;
- resource, storage, caching, and provenance behavior;
- how to run, configure, inspect, and test it;
- tests, benchmark results, acceptance criteria, and reproducibility instructions;
- failure behavior, uncertainty, unsupported cases, security boundaries, and known limitations.

### README update rule

Update this README in the same change whenever a feature affects the project's major architecture, user entry points, roadmap, running automations, accepted milestones, or incomplete-task list. Routine internal fixes do not need a README rewrite when they do not change the project overview or status.

Before a feature pull request is merged:

1. Update the relevant detailed documentation.
2. Update this README if the project overview, navigation, current-task status, or milestone/backlog status changes.
3. Add or update tests and acceptance evidence.
4. Change a task to **complete** only after its required implementation is merged and its stated acceptance checks pass.
5. Keep limitations visible; do not promote candidate-only or unverified capabilities to accepted status.

When a workflow, campaign, or scheduled task changes, update the corresponding documentation and the **Current running tasks** section. When a task is completed, move it from **Incomplete major tasks** to **Complete major tasks** and link the completion evidence.

### Documentation index

| Documentation area | Main entry point |
|---|---|
| Documentation index | [documentation/README.md](documentation/README.md) |
| Normative specifications and schemas | [specifications/README.md](specifications/README.md) |
| Archived implementation inventory and baseline evidence | [ARCHIVE_INVENTORY.md](ARCHIVE_INVENTORY.md) |
| Implementation line index | [implementations/README.md](implementations/README.md) |
| Interoperability and adapters | [interoperability/README.md](interoperability/README.md) |
| Local testing interface | [USG Kernel Lab guide](tools/usg-kernel-lab/README.md) |
| System-wide capability assessment | [Assessment — 12 November 2026](documentation/USG-SYSTEM-WIDE-CAPABILITY-ASSESSMENT-2026-11-12.md) |
| Prioritized improvement backlog | [System improvement backlog](documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md) |
| Cross-implementation status | [Cross-implementation conformance matrix](documentation/USG-CROSS-IMPLEMENTATION-CONFORMANCE-MATRIX.md) |
| Phase 7 roadmap | [Phase 7 definitions roadmap](documentation/PHASE-7-DEFINITIONS-ROADMAP.md) |
| Phase 6 continuation | [Phase 6 Continuation Tracker](documentation/PHASE-6-CONTINUATION-TRACKER.md) |

The phase roadmaps and implementation-specific documents are the detailed sources of truth for their respective components. The README is the high-level navigation and status dashboard; it must not replace those documents.

---

## Current running tasks

This section distinguishes a workflow that was observed running from workflows that are configured to run on a schedule or event. **GitHub Actions is the live source of execution status**; a scheduled task is not necessarily running at this moment.

| Task | Trigger / cadence | Last verified state and purpose |
|---|---|---|
| [External lexical incremental crawl](https://github.com/wizekin/USG-Workbench/actions/workflows/usg-external-lexical-crawl.yml) | Every 6 hours (`23 */6 * * *`) | **Running at last check.** [Run 43177652622](https://github.com/wizekin/USG-Workbench/actions/runs/43177652622) had its resumable crawl step in progress on 12 Nov 2026. It writes compressed, source-linked candidate evidence and a checkpoint to the separate `usg-external-lexical-data` branch. |
| [Open-World continuous exploration](https://github.com/wizekin/USG-Workbench/actions/workflows/open-world-continuous.yml) | Daily at 02:15 UTC; weekly deep campaign Monday at 03:30 UTC; also release and manual triggers | **Scheduled.** Generates reproducible randomized campaigns, runs registered targets, scores outcomes, analyzes failures, and publishes append-only evidence. |
| [Evidence-driven growth planner](https://github.com/wizekin/USG-Workbench/actions/workflows/usg-evidence-driven-growth-controller.yml) | Daily at 04:45 UTC; also manual | **Scheduled.** Reviews recent Open-World evidence and publishes a ranked growth plan. It plans improvements; it does not modify or promote runtime semantic rules. |
| [Bilingual naturalistic PUD pilot](https://github.com/wizekin/USG-Workbench/actions/workflows/open-world-naturalistic-pud-pilot.yml) | Weekly Monday at 04:00 UTC; also manual | **Scheduled; full campaign result not yet verified.** The source/sample validation passed. The default campaign samples 50 English and 50 Arabic sentences and evaluates the registered bounded targets. Arabic PUD is translated text, not a representative native-Arabic or conversational corpus. |
| [Phase 6 Continuation Tracker](https://github.com/wizekin/USG-Workbench/actions/workflows/phase6-continuation-tracker.yml) | Daily at 05:30 UTC; also manual | **Configured; read-only and non-blocking.** Discovers linked Phase 6 PRs, records PR/check-run observations, and uploads a separate status snapshot. It does not gate Phase 7 or modify semantic resources. |
| [External lexical PUD evaluation](https://github.com/wizekin/USG-Workbench/actions/workflows/external-lexical-pud-evaluation.yml) | After successful crawler runs, relevant pushes, or manual dispatch | **Event-driven.** Measures external lexical candidate coverage against pinned English PUD data. It is an inventory diagnostic, not an accuracy score for contextual interpretation. |

Useful live views:

- [All repository Actions runs](https://github.com/wizekin/USG-Workbench/actions)
- [All workflows](https://github.com/wizekin/USG-Workbench/actions/workflows)
- [External lexical data branch](https://github.com/wizekin/USG-Workbench/tree/usg-external-lexical-data)
- [Open-World campaign reports](evaluations/open-world/campaigns/)

**Operational note:** the lexical crawler uses resumable batches and pauses before the GitHub Actions job timeout. Its checkpoint, manifest, and compressed shards are stored on `usg-external-lexical-data`, not in the main source tree. The initial cumulative shard-storage budget is 700 MiB.

---

## Complete major tasks

The following work is accepted or implemented for its explicitly documented scope. Completion does not imply unrestricted language understanding.

### Accepted development phases

| Phase | Accepted scope | Main documentation |
|---|---|---|
| **Phase 1** | Normative semantic contract and initial interoperability acceptance | [Phase 1 exit acceptance](interoperability/PHASE-1-EXIT-ACCEPTANCE.md) |
| **Phase 2** | Evidence-grounded, rule-governed semantic reasoning foundation; steps 2.1–2.10 accepted | [Phase 2 roadmap](documentation/PHASE-2-ROADMAP.md) · [Step 2.10 exit acceptance](documentation/PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md) |
| **Phase 3** | Persistent semantic graph, SQLite-backed workspace, queries, API/CLI, and Kernel Lab integration; steps 3.1–3.9 accepted | [Phase 3 roadmap](documentation/PHASE-3-ROADMAP.md) · [Completion record](documentation/PHASE-3-COMPLETION-RECORD.md) |
| **Phase 4** | Bounded offline raw-text interpretation demonstrator; steps 4.1–4.13 accepted | [Phase 4 roadmap](documentation/PHASE-4-DEFINITIONS-ROADMAP.md) · [Completion record](documentation/PHASE-4-COMPLETION-RECORD.md) |
| **Phase 5** | Bounded bilingual interpretation pipeline, resource catalogue, immutable run persistence/replay, API/CLI, and Kernel Lab integration; steps 5.1–5.11 accepted | [Phase 5 roadmap](documentation/PHASE-5-DEFINITIONS-ROADMAP.md) · [Completion record](documentation/PHASE-5-COMPLETION-RECORD.md) · [Step 5.11 benchmark acceptance](documentation/PHASE-5-STEP-5.11-BENCHMARK-EXIT-ACCEPTANCE.md) |
| **Phase 6** | Bounded automatic exit accepted for registered bilingual profiles and service-integration scope; broader research remains candidate-only or open | [Phase 6 roadmap](documentation/PHASE-6-DEFINITIONS-ROADMAP.md) · [Bounded acceptance record](documentation/PHASE-6-BOUNDED-AUTOMATIC-ACCEPTANCE-RECORD.md) · [Continuation tracker](documentation/PHASE-6-CONTINUATION-TRACKER.md) |

Phase 5's accepted benchmark demonstrated its stated simple-transitive English and MSA Arabic constructions. Its results must not be generalized to arbitrary English or Arabic input.

### Other completed or implemented foundations

- **Canonical semantic interchange:** the versioned `USG-SEM/1.0` contract and schema are preserved as the canonical interchange boundary.
- **Persistent workspace:** Phase 3 SQLite remains the authoritative canonical persistence backend for the Kernel Lab workspace.
- **Kernel Lab:** local interface for inspecting structured semantic documents, running bounded Phase 4/5 interpretation, viewing stage evidence, managing versioned resources, querying, replaying, and exporting.
- **Lexical candidate adapter:** versioned `USG-LEXICAL-CANDIDATES/0.1.0` contract and read-only adapter preserve source provenance and ambiguity. Candidate evidence is not automatically promoted into active runtime resources.
- **OOV and ambiguity regressions:** English unknown-word and polysemy cases, plus Arabic OOV cases, have explicit regression coverage.
- **Open-World foundation:** repository inventory, evaluation protocol, randomized scenario generator, isolated execution, scoring, campaign reporting, continuous exploration, adaptive discovery, and a coverage ledger are implemented as versioned components.
- **Execution diagnostics:** case/target/attempt accounting and dependency-aware first-blocker attribution are implemented for registered Phase 4/5 profiles.
- **JavaScript Workbench browser adapter:** real Chromium/Playwright execution is implemented for the tested English browser path. It does not establish Arabic support or semantic correctness.
- **Phase 5 Kernel Lab explanations:** per-stage explanations and expandable stage evidence are available for the Phase 5 interpretation pipeline.
- **Evidence-driven growth planner:** daily evidence aggregation and ranked improvement-plan generation are implemented; automated code repair and semantic-rule promotion are not.

Related evidence: [system improvement backlog](documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md), [Open-World documentation](documentation/USG-OPEN-WORLD-RANDOMIZED-EVALUATION-PLAN.md), and [cross-implementation matrix](documentation/USG-CROSS-IMPLEMENTATION-CONFORMANCE-MATRIX.md).

---

## Incomplete major tasks

These are the major open workstreams. Detailed step definitions, dependencies, and acceptance criteria remain in the linked roadmaps and backlog.

### 1. Phase 7 — semantic knowledge integration and contextual knowledge layer

**Status: STEPS 7.1–7.7 MERGED; STEP 7.8 IMPLEMENTED ON REVIEW BRANCH, CI PENDING.** Phase 7 builds a reusable knowledge layer for lexical forms, senses, concepts, typed relations, provenance, context, and controlled retrieval on top of accepted Phase 1–5 foundations. It does not wait for the broader Phase 6 research queue. The additive `USG-KNOWLEDGE/0.1.0` contract and SQLite knowledge repository are in place; `USG-SEM/1.0` remains unchanged.

The initial roadmap defines ten ordered steps: knowledge contract/inventory; typed lexical-sense and concept model; persistent repository; source adapters and incremental acquisition; cross-language alignment; typed relations and reconciliation; contextual retrieval; read-only integration with reasoning/interpreters; API/CLI/Kernel Lab inspection; and profile-specific evaluation/exit acceptance.

Reference: [Phase 7 Definitions Roadmap](documentation/PHASE-7-DEFINITIONS-ROADMAP.md).

### 2. Phase 6 — bounded exit accepted; continuation tracked separately

**Status: BOUNDED AUTOMATIC EXIT ACCEPTED for the registered scopes.** The Phase 6 acceptance record remains valid. Broader construction coverage, naturalistic evaluation, and canonical semantic-assertion projection continue as separate research workstreams. They do not block Phase 7.

The [Phase 6 Continuation Tracker](documentation/PHASE-6-CONTINUATION-TRACKER.md) records the open workstreams, stable PR markers, separate daily GitHub Actions monitoring, and acceptance boundaries. Its workflow is read-only, does not modify runtime knowledge, and is not a required Phase 7 gate.



**Acceptance evidence:** Steps 6.7–6.14 passed the graph-first synthetic acceptance suite on the exact PR head; runtime outputs remain candidate-only. The Phase 6 Automatic Acceptance Factory evaluated 500 generated English/MSA Arabic cases across ten language/construction profiles, each with 20 positive, 20 negative, and 10 ambiguous cases. Every profile passed its precision, recall, exact-span, negative-abstention, and ambiguity-preservation gates. API, CLI, Kernel Lab regression, SQLite persistence, deterministic replay, and OPAQUE preservation checks also passed. This is acceptance of the registered synthetic profiles, not unrestricted language understanding or naturalistic semantic accuracy. Step 6.12 is accepted for OPAQUE preservation only; canonical semantic-assertion projection remains blocked.

| Step | Capability | Current status |
|---|---|---|
| **6.6** | Nominal, property, possession, and modifier semantics | **Accepted for bounded graph-first synthetic reference (500 cases / 10 profiles); runtime remains candidate-only** |
| **6.7** | Intra-clause coordination and shared arguments | **Accepted for tested shared-subject/predicate/patient profile; runtime remains candidate-only** |
| **6.8** | Embedded and subordinate clauses | **Accepted for tested causal and ambiguous causal/temporal attachment profiles; broader attachment remains open** |
| **6.9** | Voice and speech-act structures | **Accepted for registered passive-question profile; general active/passive, imperative, and request coverage remains open** |
| **6.10** | Cross-construction operator and quantifier scope | **Accepted for registered modality/negation and unresolved nested-scope profiles; broader quantifier scope remains open** |
| **6.11** | Bounded discourse-reference resolution | **Accepted for single- and multiple-antecedent candidate preservation; identity remains unresolved** |
| **6.12** | Loss-aware projection to canonical semantic documents | **Accepted for lossless OPAQUE preservation only; semantic assertion projection remains blocked** |
| **6.13** | API, CLI, resource lifecycle, and Kernel Lab integration | **Accepted: API, executable CLI, Kernel Lab regression, SQLite persistence, and deterministic replay** |
| **6.14** | Full Phase 6 benchmark and integrated exit acceptance | **Accepted for the registered 500-case bilingual synthetic profile suite; naturalistic expansion remains open** |

Step 6.6 now uses a deterministic graph-first bilingual synthetic reference benchmark: 500 cases across ten English/MSA construction profiles, with 20 positive, 20 negative, and 10 ambiguous cases per profile. It uses no human annotations, model-generated labels, external corpus, development fixtures, or candidate lexicon to create its reference cases. All ten synthetic profile gates pass. This is controlled conformance evidence only—not a naturalistic semantic-accuracy claim—and all runtime constructions remain candidate-only.

The [Phase 6 Automatic Acceptance Factory](documentation/PHASE-6-AUTOMATIC-ACCEPTANCE-FACTORY.md) generated 500 bilingual cases for Steps 6.7–6.11 and evaluated the actual integrated API. Its latest accepted report records 10/10 language profiles passing, 100% per-profile precision, recall, exact role-span accuracy, negative abstention, and ambiguity preservation, zero false unique outcomes, 500/500 OPAQUE preservation checks, and successful bilingual API/CLI, SQLite, and replay integration. These results apply only to the registered synthetic profiles; unregistered constructions and naturalistic accuracy remain outside the acceptance claim.

References: [Phase 6 roadmap](documentation/PHASE-6-DEFINITIONS-ROADMAP.md) · [Integrated interpreter and bridge validation](documentation/PHASE-6-INTEGRATED-INTERPRETER-AND-BRIDGE-VALIDATION.md) · [Steps 6.7–6.14 implementation record](documentation/PHASE-6-STEPS-6.7-6.14-COMPLETION-IMPLEMENTATION.md) · [Automatic synthetic-reference protocol](documentation/PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md) · [Historical external dataset feasibility audit](documentation/PHASE-6-STEP-6.6-INDEPENDENT-GOLD-DATASET-AUDIT.md) · [Historical independent-gold protocol](documentation/PHASE-6-STEP-6.6-INDEPENDENT-GOLD-ACCEPTANCE-PROTOCOL.md).

### 3. External lexical knowledge — crawl, evaluate, and safely integrate

**Status: IMPLEMENTED FOUNDATION; DATA COLLECTION AND RUNTIME INTEGRATION IN PROGRESS.**

The crawler, recovery, state reconciliation, structured analysis, evaluation, and candidate adapter are implemented. The full upstream headword snapshot has not been crawled. Candidate entries must remain separate from accepted runtime lexical resources until their quality, provenance, licensing, and integration criteria are satisfied.

Remaining work includes:

- continue the resumable six-hour crawl and verify checkpoint/manifest/shard consistency;
- evaluate the current durable inventory against pinned external data and track coverage changes;
- improve candidate coverage, sense ambiguity, morphology, and relation evidence using measured gaps;
- define and implement a controlled acceptance and runtime-integration path;
- preserve provenance, source-specific rights, versioning, and reproducibility throughout.

References: [External retrieval and incremental analysis](documentation/EXTERNAL-LEXICAL-RETRIEVAL-AND-INCREMENTAL-LEARNING-v0.1.0.md) · [Scheduled crawler](documentation/USG-EXTERNAL-LEXICAL-SCHEDULED-CRAWLER-v0.1.0.md) · [External lexical PUD evaluation](documentation/EXTERNAL-LEXICAL-PUD-EVALUATION-v0.1.0.md).

### 4. Open-World coverage and naturalistic evaluation

**Status: PARTIALLY IMPLEMENTED; COVERAGE AND CAMPAIGNS STILL EXPANDING.**

The evaluation framework is substantial, but its results must remain separated by population and claim type. Outstanding work includes:

- complete and review the first full bilingual naturalistic PUD campaign;
- expand executable target coverage across the remaining native models, kernel versions, adapters, Phase 2/3/6 services, and interfaces;
- keep operation-level contract checks separate from randomized language-input outcomes;
- maintain reliable replay of accepted failure cases and regressions;
- add new naturalistic sources only after their licenses, provenance, attribution, and privacy boundaries are verified.

The PUD pilot is news/Wikipedia text, not conversational user requests. Arabic PUD is translated and is not representative of the full native MSA distribution. It supplies no USG semantic gold.

References: [Naturalistic PUD pilot](documentation/USG-NATURALISTIC-PUD-PILOT.md) · [Continuous Open-World exploration](documentation/USG-OPEN-WORLD-CONTINUOUS-EXPLORATION.md) · [Expanding coverage ledger](documentation/USG-OPEN-WORLD-EXPANDING-COVERAGE.md).

### 5. Cross-implementation conformance

**Status: INVENTORY PUBLISHED; COMMON CONFORMANCE GATES NOT YET DEMONSTRATED.**

The JavaScript Workbench, Python reference kernel, Python Phase 4/5 interpreters, Phase 6 candidate modules, native models, and adapters need to be tested against common, frozen inputs and independently authored expected outputs.

The remaining gates are:

1. CIC-01 — define the shared fixture and expected-output contract.
2. CIC-02 — execute each implementation independently on the same supported cases.
3. CIC-03 — compare normalized spans, candidates, roles, ambiguity, abstention, and diagnostics.
4. CIC-04 — publish language-specific and construction-specific agreements and disagreements.
5. CIC-05 — use independent semantic gold before making semantic-correctness claims.

Reference: [Cross-implementation conformance matrix](documentation/USG-CROSS-IMPLEMENTATION-CONFORMANCE-MATRIX.md).

### 6. Governed autonomous improvement

**Status: PLANNER IMPLEMENTED; AUTOMATIC REPAIR AND CANDIDATE GROWTH NOT COMPLETE.**

- **SYS-14:** extend pinned deterministic replay from the initial smoke implementation to the accepted failure corpus and every accepted repair.
- **SYS-16:** implement a bounded automatic repair executor for deterministic tests, reports, schemas, and evaluation infrastructure. Repairs must use isolated branches, tests, replay, and reviewable pull requests.
- **SYS-17:** implement a candidate semantic and lexical growth loop that derives proposals from measured failures, evaluates them independently, preserves held-out data, and promotes only accepted candidates.

The growth planner does not currently modify runtime rules or automatically promote lexical/semantic knowledge. Human-governed acceptance and explicit validation boundaries must remain intact.

Reference: [System improvement backlog](documentation/USG-SYSTEM-IMPROVEMENT-BACKLOG.md) · [Autonomous growth and governance](documentation/USG-AUTONOMOUS-GROWTH-AND-GOVERNANCE.md).

---

## Architecture and reliability rules

These rules apply across implementation lines and future features.

1. **Versioned contracts:** schemas, interpretation contracts, resources, and adapters must be versioned. Do not silently change an accepted contract to fit a new implementation.
2. **One canonical persistence authority:** SQLite remains the authoritative canonical document store for the Kernel Lab workspace. Caches, indexes, and candidate inventories are not competing semantic sources of truth.
3. **Preserve the source:** retain exact original text, source digests, source spans, provenance, and the rules/resources that produced each interpretation.
4. **Keep uncertainty explicit:** unknown words, ambiguous senses, competing parses, unsupported constructions, unresolved references, and resource limits must not be turned into unjustified unique interpretations.
5. **Candidate data is not accepted knowledge:** external lexical evidence, provisional associations, parser output, and model proposals cannot modify canonical semantic resources without their explicit acceptance process.
6. **Separate testing from correctness:** schema validity, passing unit tests, import success, browser execution, and cross-implementation agreement each support different claims. None alone proves broad semantic correctness.
7. **Protect accepted baselines:** preserve archives, historical implementations, Phase 1–5 contracts, frozen corpora, and their regression gates.
8. **No hidden scope expansion:** list unsupported languages, constructions, interfaces, and evaluation gaps rather than implying that an untested component is complete.

---

## How to explore and test USG

### Start with the Kernel Lab

The [USG Kernel Lab README](tools/usg-kernel-lab/README.md) explains how to launch the local browser interface, use the interpretation panels, inspect stage diagnostics and structured records, query stored documents, and export results.

The Kernel Lab currently provides the local interface for the Python v0.7.0 Mention adapter and Phase 3 SQLite-backed semantic workspace, with bounded Phase 4 and Phase 5 interpretation panels. It is not a unified runtime for every implementation in this repository.

### Where to find tests and evaluation evidence

- [Tests README](tests/README.md) — test organization and running guidance.
- [Phase roadmaps](documentation/README.md) — phase-specific implementation and acceptance documents.
- [Open-World campaign bundles](evaluations/open-world/campaigns/) — immutable campaign inputs, results, and reports.
- [System assessment snapshot](evaluations/system-wide/2026-11-12/assessment.json) — machine-readable assessment evidence.
- [GitHub Actions](https://github.com/wizekin/USG-Workbench/actions) — live CI, scheduled jobs, artifacts, and workflow results.

Run the version-specific test commands documented with each implementation. Do not assume one test command or one Python environment covers every versioned package.

---

## Repository structure

| Path | Purpose |
|---|---|
| `archives/` | Original checksum-verified release archives; preserve unchanged. |
| `implementations/semantic-workbench-js/` | JavaScript/browser Semantic Workbench releases. |
| `implementations/python-kernel/` | Versioned Python reference-kernel releases and native semantic models. |
| `specifications/` | Normative semantic contracts and JSON Schemas. |
| `resources/` | Bundled, versioned lexical, morphology, and operator resources. |
| `tools/usg_interpretation_*/` | Versioned Python interpretation pipelines. |
| `tools/usg-kernel-lab/` | Local Kernel Lab application and interface. |
| `tools/usg_external_lexical_*/` | External lexical retrieval, analysis, crawling, and candidate adapters. |
| `tools/open_world_evaluation/` | Randomized evaluation, target adapters, execution, scoring, replay, reporting, and growth planning. |
| `interoperability/` | Versioned adapters and cross-implementation conformance work. |
| `benchmarks/` and `evaluations/` | Frozen benchmark fixtures, reports, and reproducible evaluation outputs. |
| `documentation/` | Architecture, roadmaps, implementation guides, acceptance records, and project status. |
| `tests/` | Regression, contract, adapter, benchmark, and workflow-support tests. |
| `.github/workflows/` | CI validation, scheduled crawlers, evaluation campaigns, and growth-planning automation. |
| `ARCHIVE_INVENTORY.md` | Archive hashes, baseline inspection, test evidence, and limitations. |

---

## Status and evidence conventions

Use these meanings consistently in documentation, workflow summaries, and future status updates:

- **Complete / accepted:** implementation is merged and its defined acceptance criteria passed.
- **Implemented:** code exists, but the required integrated or independent acceptance may still be outstanding.
- **In progress:** active implementation, scheduled execution, evaluation, or integration remains.
- **Blocked:** a stated dependency, rights issue, missing corpus, or required acceptance gate prevents progress.
- **Candidate-only:** evidence or proposed structures are preserved but are not accepted runtime knowledge.
- **Not assessed / not tested:** no adequate evidence exists; do not infer success or failure.

A task is not complete merely because its workflow file exists, a pull request was created, a component imports successfully, or a report was generated. Always link status claims to the implementation, test, benchmark, or acceptance evidence that supports them.
