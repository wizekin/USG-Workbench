# USG Cross-Implementation Conformance Matrix

**Contract:** `USG-CROSS-IMPLEMENTATION-MATRIX/0.1.0`  
**Snapshot:** 2026-11-16  
**Status:** component inventory updated; shared cross-runtime conformance has not yet been demonstrated.

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
| JavaScript Semantic Workbench v0.5.4 | Browser workbench, its own semantic-model tests, and English Open-World/PUD execution through the Playwright adapter | Its v0.5 record schema is not proof of USG-SEM/1.0 interchange. The deterministic local rule fallback proves UI execution and structured output only; it does not establish semantic correctness or cross-runtime equivalence. The JS target remains English-only. |
| Python kernel v0.7.0 | USG-SEM/1.0 document adapter and native Mention model | No shared frozen test currently proves semantic equivalence with JavaScript |
| Python Phase 5 interpreter USG-INTERPRET/0.2.0 | Bounded bilingual lexical-to-discourse pipeline and stage diagnostics | Naturalistic PUD first blockers expose lexical and syntax gaps; PUD has no independent USG semantic gold. Bounded construction benchmarks do not establish broad language understanding or equivalence with JS. |
| External lexical candidate adapter | Provenance-preserving candidate package and candidate-only validation | It is deliberately not a runtime lexicon and cannot promote candidate data |

### Browser evidence refresh — 2026-11-16

Two newer campaigns confirm that the browser adapter is actually exercised inside the campaign runner:

- [OWC-OW7 run 43807165809](https://github.com/wizekin/USG-Workbench/actions/runs/43807165809): 100 JS target records. The 68 English cases were 2 completed and 66 partial; the 32 mixed/Arabic cases were unsupported.
- [Naturalistic PUD run 43810018720](https://github.com/wizekin/USG-Workbench/actions/runs/43810018720): 100 JS target records. The 50 English cases were 4 completed and 46 partial; all 50 Arabic cases were unsupported.

Browser-backed records identify Playwright adapter v0.1.0 and Chromium 159.0.8154.6, with loopback-only networking, deterministic local rule fallback, no Ollama request, and no recorded page/console errors in those records. A separate conditional browser job may be skipped while the campaign runner still executes its JS target; do not confuse the job status with the per-case adapter evidence.

The JavaScript target remains English-only. These runs prove browser/UI execution and structured output only, not semantic correctness, Arabic support, canonical USG-SEM/1.0 interchange, or cross-runtime equivalence.

### Naturalistic evidence boundary

PUD is news/Wikipedia text, not conversational user requests. The Arabic PUD sample is translated and is not a representative native-MSA distribution. The first campaign ran 300 actual attempts, with 4 completed, 245 partial, and 51 unsupported; it had no independent semantic gold and no semantic-scored attempts. UD POS/dependency labels are syntactic proxies, not USG semantic roles or frames. The campaign report is on an unmerged report branch because Actions PR creation was denied; it is not yet part of main's committed campaign history.

## Required cross-implementation gates

1. Freeze common source inputs and independently authored canonical expected outputs.
2. Run each implementation separately against exactly the same cases, recording code and resource versions.
3. Compare normalized spans, lexical candidates, construction/role structures, ambiguity, abstention, and diagnostics. Do not compare run-specific internal IDs.
4. Publish disagreement examples and per-language/per-construction results.
5. Keep semantic correctness claims behind independent gold, not implementation agreement alone.

All five CIC gates remain `not_started`.

## Guardrails

- Component test success is not cross-implementation conformance.
- Cross-implementation agreement is not automatically semantic correctness; implementations can share the same mistake.
- No accepted runtime contract or lexical resource is changed by this inventory.
- Candidate lexical data remains candidate-only.

## Next implementation

The next safe step is CIC-01: define a compact common fixture contract and choose cases that are already supported by more than one implementation. Unsupported features must remain explicitly out of scope until independently implemented and tested.
