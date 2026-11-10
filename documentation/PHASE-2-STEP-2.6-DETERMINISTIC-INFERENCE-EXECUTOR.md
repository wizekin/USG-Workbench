# Phase 2 Step 2.6 — Deterministic Inference Executor

**Status:** COMPLETE — merged as PR #44. The integrated implementation and regression scope are recorded in the Phase 2 roadmap.

## Scope

Step 2.6 adds an additive Python package, `USG-INFERENCE/1.0.0`, that consumes
complete, schema-valid USG-SEM/1.0 documents and explicit task objects. It does
not parse prose, alter the canonical profile, or reinterpret the Phase 1
adapter contract.

The first executable subset contains exactly:
1. `benchmark-rule:modus-ponens@1.0.0`
2. `benchmark-rule:and-elimination-left@1.0.0`

A separately versioned activation manifest enables these handlers. The
declarative registry remains unchanged, `execution_enabled=false`, and every
declarative rule remains `SPECIFIED_NOT_EXECUTABLE`.

## Eligibility and matching

Only `SOURCE_ASSERTED` assertions with resolved PROP-sorted expressions,
valid origins, exact contexts, and preserved commitment/attribution bindings
are eligible. DISPUTED and UNKNOWN remain distinct; ambiguous, unresolved,
invalid, and unsupported structures do not become premises. Constructors,
operand order, typed references, and rule versions are matched exactly.

Modus Ponens requires a source assertion of the exact antecedent and a source
assertion of the exact directed IMPLIES expression in the same context and
attribution binding. Conjunction elimination derives only the left operand of
the exact binary AND expression. No converse, transitivity, lexical matching,
or implicit closure is performed.

## Result and provenance

Derived candidates are returned outside the canonical assertion collection
with epistemic effect `DERIVED_NOT_VERIFIED`. Each derivation records exact
input references, deterministic IDs, input document SHA-256, rule/version,
registry, semantics, activation, and grounding resolver versions. Repeated
derivations remain individually represented while candidate identity is
deduplicated by exact conclusion expression and context.

No inferred candidate is eligible as a premise in the same execution.
Evidence assessment, conflict winner selection, verification, and truth
promotion are out of scope.

## Resource behavior

An optional task-level rule-application budget is an execution control, not a
semantic complexity limit. Exhaustion returns `INCOMPLETE`, preserves all
input record IDs, lists pending work, and never truncates expressions,
operands, semantic candidates, or canonical input content.

## Acceptance

The Step 2.6 PR must pass the canonical USG-SEM/1.0 schema checks, activation
and task schema checks, existing registry/semantics/grounding/benchmark
regressions, and the new executor suite. The false-inference gate remains
strict. The frozen compact Step 2.2 benchmark and all Phase 1 baselines remain
unchanged. No Node.js runtime/action upgrade is included.
