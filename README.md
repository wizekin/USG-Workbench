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

- [USG Kernel Lab](tools/usg-kernel-lab/README.md) is the local browser interface for the v0.7.0 Mention adapter and Phase 3 SQLite-backed semantic workspace: immutable document revisions, persistent queries, condition/exception maps, exact-scope contradiction inspection, integrity checks, and complete JSON export.
- It remains separate from the JavaScript Semantic Workbench v0.5.4 and does not parse raw text or claim a unified runtime for every USG module.
- Native Assertion model v0.8.0 and its document adapter are available as Python APIs; Native Evidence model v0.9.0 is available as a model-only Python API.

## Current phase

- **Phase 1:** COMPLETE. See [Phase 1 exit acceptance](interoperability/PHASE-1-EXIT-ACCEPTANCE.md).
- **Phase 2:** COMPLETE for the implemented and tested scope. Steps 2.1–2.10 are merged and the final integrated acceptance gate passed on the exact merged main commit. See the [Phase 2 roadmap](documentation/PHASE-2-ROADMAP.md), [Step 2.10 acceptance record](documentation/PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md), and [successful merged-main workflow](https://github.com/wizekin/USG-Workbench/actions/runs/42811673922). Deferred capabilities remain explicitly out of scope.
- **Phase 3:** COMPLETE for the defined and tested scope. Steps 3.1–3.9 are merged, and the integrated exit-acceptance workflow passed on the merged implementation. SQLite remains the sole authoritative canonical backend. The local package launches the browser lab with `usg-workbench lab`; the final acceptance report and release artifacts are available from [CI run 42832132388](https://github.com/wizekin/USG-Workbench/actions/runs/42832132388). This completion does not claim unrestricted natural-language understanding, objective truth determination, distributed execution, multilingual coverage, or production/security certification. See the [Phase 3 roadmap](documentation/PHASE-3-ROADMAP.md), [completion record](documentation/PHASE-3-COMPLETION-RECORD.md), and [storage backend decision](documentation/STORAGE-BACKEND-EVALUATIONS.md).
