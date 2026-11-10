# USG project documentation

This directory is for architecture decisions, roadmap records, design rationale, implementation comparisons, and release documentation that applies across more than one implementation.

Record evidence and version scope explicitly. Distinguish verified behavior from proposals and future work.

## Phase 2 — Semantic reasoning

- [Phase 2 roadmap](PHASE-2-ROADMAP.md) — phase objectives, non-negotiable principles, architecture, implementation sequence, evaluation strategy, exit criteria, and deferred capabilities.
- [Phase 2 Step 2.1 — Semantic reasoning definitions and architecture](PHASE-2-STEP-2.1-SEMANTIC-REASONING-DEFINITIONS.md) — formal terminology, reasoning layers, rule requirements, evidence boundaries, and outcome distinctions.
- [Phase 2 Step 2.2 — Benchmark corpus and evaluator](PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md) — 35 versioned fixtures, candidate-result contract, scoring measures, and pre-inference acceptance thresholds.
- [Phase 2 Step 2.3 — Rule model and registry](PHASE-2-STEP-2.3-RULE-MODEL-AND-REGISTRY.md) — typed declarative rule model, disabled reference registry, schema, static validator, and benchmark cross-links.
- [Phase 2 Step 2.4 — Rule semantics and safety contract](PHASE-2-STEP-2.4-RULE-SEMANTICS-AND-SAFETY-CONTRACT.md) — exact matching, eligibility, scope, conflicts, outcomes, determinism, and interruption semantics.
- [Phase 2 Step 2.5 — Deterministic grounding services](PHASE-2-STEP-2.5-DETERMINISTIC-GROUNDING-SERVICES.md) — typed references, exact definition versions, Mention-to-Referent links, Context paths, expression scope paths, and compact-fixture compatibility checks.
- [Phase 2 Step 2.6 — Deterministic inference executor](PHASE-2-STEP-2.6-DETERMINISTIC-INFERENCE-EXECUTOR.md) — narrow enabled rule subset, explicit activation, derivation provenance, and interruption behavior.
- [Phase 2 Step 2.7 — Evidence support and conflict assessment](PHASE-2-STEP-2.7-EVIDENCE-SUPPORT-AND-CONFLICT-ASSESSMENT.md) — independent quote alignment, support declarations, relation claims, exact-scope conflicts, source independence, corroboration, and external verification.
- [Phase 2 Step 2.8 — Query and explanation interface](PHASE-2-STEP-2.8-QUERY-EXPLANATION-INTERFACE.md) — exact-reference query contract, conflict-aware derivation projection, and structured explanations.
- [Phase 2 Step 2.10 — Final exit acceptance](PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md) — integrated regression gate and machine-readable acceptance report.

**Phase 2 is COMPLETE.** Steps 2.1–2.10 are implemented, merged, and accepted for their documented scope. The [final merged-main acceptance run](https://github.com/wizekin/USG-Workbench/actions/runs/42811673922) passed and uploaded its machine-readable report. The completion record was merged in [PR #53](https://github.com/wizekin/USG-Workbench/pull/53).

## Phase 3 — Persistent semantic graph and bounded product core

- [Phase 3 roadmap](PHASE-3-ROADMAP.md) — ordered steps 3.1–3.9, invariants, architecture, first product scope, exclusions, and exit criteria.
- [Phase 3 Step 3.1 — Canonical graph-store contract](PHASE-3-STEP-3.1-CANONICAL-GRAPH-STORE-CONTRACT.md) — canonical snapshot authority, immutable revisions, canonical JSON/hash, SQLite indexing, atomic writes, integrity checks, and required Step 3.2 tests.

**Current step:** 3.1 contract defined; Step 3.2 is the SQLite canonical document store implementation. Phase 3 remains in progress until its integrated exit gate passes.
