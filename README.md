# USG Workbench Repository

This repository preserves the distinct implementation baselines and the specifications/documentation used to evolve the Universal Semantic Grammar (USG) project.

## Repository structure

- archives/: original, checksum-verified release ZIPs; preserved unchanged.
- implementations/semantic-workbench-js/: JavaScript/browser Semantic Workbench releases.
- implementations/python-kernel/: Python reference kernel releases.
- specifications/: normative semantic contracts and schemas.
- documentation/: architecture decisions, design notes, and project documentation.
- interoperability/: adapters and conformance work connecting implementations through explicit contracts.
- tests/: cross-implementation fixtures and conformance tests.
- ARCHIVE_INVENTORY.md: archive hashes, baseline inspection, test evidence, and limitations.

## Important architecture boundary

The JavaScript Semantic Workbench and Python reference kernel are separate implementation lines. Their versions and internal representations are not interchangeable. A feature present in one must not be assumed to exist in the other. Interoperability must be explicit, versioned, and tested; unsupported mappings must be reported rather than silently coerced or discarded.

## Baseline status

The archive inventory records fresh tests and limitations for the original packages. Passing package tests do not establish unrestricted natural-language understanding or general semantic correctness.

## Interactive testing interface

- [USG Kernel Lab](tools/usg-kernel-lab/README.md) is a local browser interface for testing the Python v0.7.0 Mention model and its USG-SEM/1.0 adapter.
- It is intentionally separate from the JavaScript Semantic Workbench v0.5.4. It does not yet provide natural-language generation or a unified runtime for every USG module.
- Native Assertion model v0.8.0 and its document adapter are available as Python APIs; Native Evidence model v0.9.0 is available as a model-only Python API. The current Kernel Lab interface does not yet expose these models.

## Current phase

- **Phase 1:** COMPLETE. See [Phase 1 exit acceptance](interoperability/PHASE-1-EXIT-ACCEPTANCE.md).
- **Phase 2:** REASONING CONTRACTS COMPLETE THROUGH STEP 2.4. The [Phase 2 roadmap](documentation/PHASE-2-ROADMAP.md), [Step 2.1 definitions](documentation/PHASE-2-STEP-2.1-SEMANTIC-REASONING-DEFINITIONS.md), [Step 2.2 benchmark/evaluator](documentation/PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md), [Step 2.3 rule model/registry](documentation/PHASE-2-STEP-2.3-RULE-MODEL-AND-REGISTRY.md), and [Step 2.4 rule semantics/safety contract](documentation/PHASE-2-STEP-2.4-RULE-SEMANTICS-AND-SAFETY-CONTRACT.md) define the frozen evaluation and declarative reasoning contracts. The four reference rules remain disabled; no grounding service or inference engine is implemented yet.
