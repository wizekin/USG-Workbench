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

- [USG Kernel Lab](tools/usg-kernel-lab/README.md) is a local browser interface for testing the Python v0.7.0 Mention model, its USG-SEM/1.0 adapter, and the Phase 2 structured query/reasoning pipeline (Steps 2.6–2.8).
- It is intentionally separate from the JavaScript Semantic Workbench v0.5.4. It does not yet provide natural-language generation or a unified runtime for every USG module.
- Native Assertion model v0.8.0 and its document adapter are available as Python APIs; Native Evidence model v0.9.0 is available as a model-only Python API.

## Current phase

- **Phase 1:** COMPLETE. See [Phase 1 exit acceptance](interoperability/PHASE-1-EXIT-ACCEPTANCE.md).
- **Phase 2:** COMPLETE for the implemented and tested scope. Steps 2.1–2.10 are merged and the final integrated acceptance gate passed on the exact merged main commit. See the [Phase 2 roadmap](documentation/PHASE-2-ROADMAP.md), [Step 2.10 acceptance record](documentation/PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md), and [successful merged-main workflow](https://github.com/wizekin/USG-Workbench/actions/runs/42811673922). Deferred capabilities remain explicitly out of scope.
- **Phase 3:** IN PROGRESS. The [Phase 3 roadmap](documentation/PHASE-3-ROADMAP.md) defines the next ordered work: canonical graph persistence, persistent query integration, scope-aware rule expansion, conditions/contradiction services, local API/CLI, Kernel Lab integration, packaging, and final acceptance. The [Step 3.1 store contract](documentation/PHASE-3-STEP-3.1-CANONICAL-GRAPH-STORE-CONTRACT.md) is defined; implementation starts at Step 3.2.
