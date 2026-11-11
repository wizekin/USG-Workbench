# USG Workbench Repository

This repository preserves the distinct implementation baselines and the specifications/documentation used to evolve the Universal Semantic Grammar (USG) project.

## Repository structure

- archives/: original, checksum-verified release ZIPs; preserved unchanged.
- implementations/semantic-workbench-js/: JavaScript/browser Semantic Workbench releases.
- implementations/python-kernel/: Python reference kernel releases.
- specifications/: normative semantic contracts and schemas.
- resources/: bundled, versioned lexical and operator assets packaged with the Python workbench.
- documentation/: architecture decisions, design notes, and project documentation.
- interoperability/: adapters and conformance work connecting implementations through explicit contracts.
- tests/: cross-implementation fixtures and conformance tests.
- ARCHIVE_INVENTORY.md: archive hashes, baseline inspection, test evidence, and limitations.

## Important architecture boundary

The JavaScript Semantic Workbench and Python reference kernel are separate implementation lines. Their versions and internal representations are not interchangeable. A feature present in one must not be assumed to exist in the other. Interoperability must be explicit, versioned, and tested; unsupported mappings must be reported rather than silently coerced or discarded.

## Baseline status

The archive inventory records fresh tests and limitations for the original packages. Passing package tests do not establish unrestricted natural-language understanding or general semantic correctness.

## Interactive testing interface

- [USG Kernel Lab](tools/usg-kernel-lab/README.md) is the local browser interface for the v0.7.0 Mention adapter and Phase 3 SQLite-backed semantic workspace. It includes the bounded Phase 4 raw-text-to-USG-SEM panel and the Phase 5 USG-INTERPRET/0.2.0 multi-stage analysis panel, versioned resource catalogue, provisional association retrieval, immutable run persistence/replay, structured-document inspection, persistent queries, integrity checks, and complete JSON export.
- It remains separate from the JavaScript Semantic Workbench v0.5.4 and does not claim a unified runtime for every USG module.
- Native Assertion model v0.8.0 and its document adapter are available as Python APIs; Native Evidence model v0.9.0 is available as a model-only Python API.

## Current phase

- **Phase 1:** COMPLETE. See [Phase 1 exit acceptance](interoperability/PHASE-1-EXIT-ACCEPTANCE.md).
- **Phase 2:** COMPLETE for the implemented and tested scope. Steps 2.1–2.10 are merged and the final integrated acceptance gate passed. See the [Phase 2 roadmap](documentation/PHASE-2-ROADMAP.md) and [Step 2.10 acceptance record](documentation/PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md). Deferred capabilities remain explicitly out of scope.
- **Phase 3:** COMPLETE for the defined and tested scope. Steps 3.1–3.9 are merged; SQLite remains the sole authoritative canonical backend. See the [Phase 3 roadmap](documentation/PHASE-3-ROADMAP.md), [completion record](documentation/PHASE-3-COMPLETION-RECORD.md), and [storage backend decision](documentation/STORAGE-BACKEND-EVALUATIONS.md).
- **Phase 4:** COMPLETE for the v0.1.0 bounded offline demonstrator. Steps 4.1–4.13 are merged. See the [Phase 4 roadmap](documentation/PHASE-4-DEFINITIONS-ROADMAP.md), [completion record](documentation/PHASE-4-COMPLETION-RECORD.md), and [Step 4.13 exit gate](documentation/PHASE-4-STEP-4.13-EXIT-ACCEPTANCE.md). This is not unrestricted English/Arabic understanding.
- **Phase 5:** COMPLETE for its documented and benchmarked scope. Steps 5.1–5.11 are accepted. The v0.2.1 benchmark measured 100% precision/recall, role/span accuracy, and negative/ambiguous target abstention for the three simple-transitive English/MSA Arabic target constructions; it does not establish broad language coverage. See the [Phase 5 roadmap](documentation/PHASE-5-DEFINITIONS-ROADMAP.md), [completion record](documentation/PHASE-5-COMPLETION-RECORD.md), and [Step 5.11 acceptance report](documentation/PHASE-5-STEP-5.11-BENCHMARK-EXIT-ACCEPTANCE.md).
- **Phase 6:** IN PROGRESS. Steps 6.1–6.5 are accepted for their bounded, benchmarked scope. Step 6.6 remains in progress; the candidate interpreter and external PUD parser baselines do not provide independent semantic-role gold. The [Step 6.6 independent gold dataset audit](documentation/PHASE-6-STEP-6.6-INDEPENDENT-GOLD-DATASET-AUDIT.md) records that SemEval-2007 Task 4 and Task 18 are narrow candidates only: exact data access and redistribution rights remain unverified; WojoodRelations is an additional MSA candidate whose download requires institutional affiliation and whose entity-level relations do not directly annotate internal phrase modifiers. These sources do not cover all internal modifier relations. No external corpus has been imported; Step 6.7 remains blocked pending Step 6.6 acceptance. See the [Phase 6 roadmap](documentation/PHASE-6-DEFINITIONS-ROADMAP.md).

## External lexical retrieval and incremental analysis

- [External lexical retrieval and incremental analysis](documentation/EXTERNAL-LEXICAL-RETRIEVAL-AND-INCREMENTAL-LEARNING-v0.1.0.md) retrieves individual English words from the public providers on demand and caches only requested words locally.
- [Scheduled incremental lexical crawler](documentation/USG-EXTERNAL-LEXICAL-SCHEDULED-CRAWLER-v0.1.0.md) describes the six-hour GitHub Actions worker. Its resumable, pinned-snapshot outputs are stored on the separate usg-external-lexical-data branch, not in main. The crawler stores compact source-linked lexical evidence, not raw definition or example passages, and does not modify the runtime interpreter or LexicalResource.
- The initial persistent shard budget is 700 MiB; reaching it pauses the crawl without deleting previous batches.

## Open-world randomized evaluation

- [USG Open-World Randomized Evaluation Program](documentation/USG-OPEN-WORLD-RANDOMIZED-EVALUATION-PLAN.md) defines a continuously expanding, seed-reproducible test campaign for realistic, unconstrained, adversarial, and diagnostic requests. It separates the evaluation of the harness from claims about USG capability and specifies append-only reports stored in this repository.
- [OW-0 repository inventory](documentation/USG-OPEN-WORLD-REPOSITORY-INVENTORY.md) records the actual implementation and capability boundaries.
- [OW-1 evaluation protocol](documentation/USG-OPEN-WORLD-EVALUATION-PROTOCOL.md) defines versioned scenario, source-provenance, execution-result, and campaign-report contracts.
- [OW-2 randomized scenario generator](documentation/USG-OPEN-WORLD-RANDOM-SCENARIO-GENERATOR.md) creates seeded, protocol-validated cases for the initial real evaluation targets.
- [OW-3 isolated execution runner](documentation/USG-OPEN-WORLD-EXECUTION-RUNNER.md) executes Phase 4 and Phase 5 in fresh child processes and explicitly records targets that are not yet executable.
- [OW-4 scoring and validation](documentation/USG-OPEN-WORLD-SCORING-AND-VALIDATION.md) separates deterministic structural checks from semantic claims requiring independent oracles.
- [OW-5 campaign reporting](documentation/USG-OPEN-WORLD-CAMPAIGN-REPORTING.md) builds validated JSON/Markdown reports, hashes every artifact, clusters failures, optionally minimizes reproducers, and stores write-once campaign bundles.
- [OW-6 first pilot](documentation/USG-OPEN-WORLD-FIRST-PILOT.md) runs a broad seeded random target matrix plus separately annotated Phase 4/5 diagnostic fixtures, and publishes the report with explicit missing-population gaps.
- [OW-7 continuous exploration](documentation/USG-OPEN-WORLD-CONTINUOUS-EXPLORATION.md) schedules bounded daily, weekly, release, and manual campaigns and publishes each report as a new append-only PR.
- [OW-8 adaptive discovery](documentation/USG-OPEN-WORLD-ADAPTIVE-DISCOVERY.md) compares failure clusters with prior campaigns and generates capped formatting-only follow-ups for reproducible structural/runtime failures.
- [OW-9+ expanding coverage ledger](documentation/USG-OPEN-WORLD-EXPANDING-COVERAGE.md) maps evaluated entry points against every inventoried USG component and keeps untested scope visible.
