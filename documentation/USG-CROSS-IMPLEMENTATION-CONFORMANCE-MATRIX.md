# USG Cross-Implementation Conformance Matrix

**Contract:** `USG-CROSS-IMPLEMENTATION-MATRIX/0.1.0`  
**Snapshot:** 2026-11-12  
**Status:** inventory published; shared cross-runtime conformance has not yet been demonstrated.

## Why this matrix exists

USG contains several implementations and subsystems. Passing each component's own tests does not prove that the implementations interpret the same input in equivalent ways. This matrix therefore separates:

- **Component-tested:** a subsystem passes its own bounded tests.
- **Not established:** the evidence does not justify the capability claim.
- **Not tested:** no common cross-implementation comparison exists.
- **Blocked:** a required execution adapter or external prerequisite is missing.

The machine-readable source of truth is `evaluations/system-wide/cross-implementation-matrix-2026-11-12.json`.

## Current findings

| Implementation | Demonstrated component scope | Important limit |
|---|---|---|
| JavaScript Semantic Workbench v0.5.4 | Browser workbench and its own semantic-model tests | Its v0.5 record schema is not proof of USG-SEM/1.0 interchange; Open-World browser execution is still missing |
| Python kernel v0.7.0 | USG-SEM/1.0 document adapter and native Mention model | No shared frozen test currently proves semantic equivalence with JavaScript |
| Python Phase 5 interpreter USG-INTERPRET/0.2.0 | Bounded bilingual lexical-to-discourse pipeline and stage diagnostics | Bounded construction benchmarks do not establish broad language understanding or equivalence with JS |
| External lexical candidate adapter | Provenance-preserving candidate package and candidate-only validation | It is deliberately not a runtime lexicon and cannot promote candidate data |

## Required cross-implementation gates

1. Freeze common source inputs and independently authored canonical expected outputs.
2. Run each implementation separately against exactly the same cases, recording code and resource versions.
3. Compare normalized spans, lexical candidates, construction/role structures, ambiguity, abstention, and diagnostics. Do not compare run-specific internal IDs.
4. Publish disagreement examples and per-language/per-construction results.
5. Keep semantic correctness claims behind independent gold, not implementation agreement alone.

## Guardrails

- Component test success is not cross-implementation conformance.
- Cross-implementation agreement is not automatically semantic correctness; implementations can share the same mistake.
- No accepted runtime contract or lexical resource is changed by this inventory.
- Candidate lexical data remains candidate-only.

## Next implementation

The next safe step is CIC-01: define a compact common fixture contract and choose cases that are already supported by more than one implementation. Unsupported features must remain explicitly out of scope until independently implemented and tested.
