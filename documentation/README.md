# USG project documentation

This directory is for architecture decisions, roadmap records, design rationale, implementation comparisons, and release documentation that applies across more than one implementation.

Record evidence and version scope explicitly. Distinguish verified behavior from proposals and future work.

## Phase 2 — Semantic reasoning

- [Phase 2 roadmap](PHASE-2-ROADMAP.md) — phase objectives, non-negotiable principles, architecture, implementation sequence, evaluation strategy, exit criteria, and deferred capabilities.
- [Phase 2 Step 2.1 — Semantic reasoning definitions and architecture](PHASE-2-STEP-2.1-SEMANTIC-REASONING-DEFINITIONS.md) — formal terminology, reasoning layers, rule requirements, evidence boundaries, and outcome distinctions.
- [Phase 2 Step 2.2 — Benchmark corpus and evaluator](PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md) — 35 versioned fixtures, candidate-result contract, scoring measures, and pre-inference acceptance thresholds.
- [Phase 2 Step 2.3 — Rule model and registry](PHASE-2-STEP-2.3-RULE-MODEL-AND-REGISTRY.md) — typed declarative rule model, disabled reference registry, schema, static validator, and benchmark cross-links.

Phase 2 has completed its definitions, benchmark, and declarative rule-model foundation. The registry rules remain disabled; no production rule matcher or inference executor has been implemented.
