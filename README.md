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
- **Phase 6:** IN PROGRESS. Steps 6.1–6.4 are accepted. Step 6.5 implements bounded English/MSA Arabic predicate/argument patterns; its benchmark gate is pending and broader constructions remain disabled. See the [Phase 6 roadmap](documentation/PHASE-6-DEFINITIONS-ROADMAP.md), [Step 6.1 contract](documentation/PHASE-6-STEP-6.1-INTERPRETATION-AND-PROJECTION-CONTRACT.md), [Step 6.2 benchmark](documentation/PHASE-6-STEP-6.2-EXPANDED-BENCHMARK-AND-EVALUATOR.md), [corrected Phase 6 gold profile v0.3.1](documentation/PHASE-6-BENCHMARK-ANNOTATION-CORRECTION-0.3.1.md), [Step 6.3 frame contract](documentation/PHASE-6-STEP-6.3-TYPED-ROLES-FRAMES-VALENCY.md), and [Step 6.4 lexical resource contract](documentation/PHASE-6-STEP-6.4-LEXICAL-MORPHOLOGY-RESOURCES.md).
