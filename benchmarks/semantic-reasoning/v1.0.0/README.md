# USG Semantic Reasoning Benchmark v1.0.0

This directory contains the frozen Phase 2 Step 2.2 benchmark contract. It defines reference fixtures, candidate-result shape, and acceptance thresholds **before any rule model or inference executor is implemented**.

## Contents

- `fixtures.json` — 35 stable benchmark fixtures.
- `fixtures.schema.json` — Draft 2020-12 schema for fixture metadata and expected outcomes.
- `results.schema.json` — candidate-result schema consumed by the evaluator.
- `thresholds.json` — frozen pre-inference acceptance thresholds and metric definitions.

Every fixture includes a case-specific rationale tied to its task and expected/prohibited outcomes. The fixtures cover 18 semantic domains: identity, typed references, operator scope, conditionals/connectives, roles and semantic kinds, modality/attribution/temporal scope, contexts, evidence, inference, open/closed-world assumptions, corroboration, ambiguity, unresolved content, conflict, unsupported structures, provenance, determinism, and resource interruption.

All nine requested test classes are represented: positive, negative, boundary, adversarial, ambiguous, unresolved, conflicting, unsupported, and incomplete.

## Important boundaries

The input snapshots are synthetic scenario data scoped to the declared `USG-SEM/1.0` profile and listed implementation versions. They are benchmark task inputs, not a replacement for the canonical USG-SEM schema and not a claim that every partial or deliberately invalid fixture is a valid complete semantic document.

Rules embedded in a fixture's `benchmark-reference-policy/1.0.0` are test-only reference policies. They are not a production rule registry, do not change USG-SEM/1.0, and do not activate reasoning in the current kernel.

The evaluator does not parse text, resolve meaning, execute rules, or generate conclusions. It compares a candidate implementation's normalized structured outputs with the fixture expectations.

## Candidate result contract

A candidate must return one result per fixture. The normalizing adapter must express conclusions using stable semantic conclusion keys and supply:

- completion status and conclusion keys;
- diagnostic codes;
- scope/variable/role bindings;
- evidence assessments with alignment and support kept separate;
- derivations with stable IDs, method, exact rule ID/version where applicable, ordered input/output references, and status;
- preserved item IDs;
- at least two repeat-run output snapshots for determinism checks;
- resource interruption/truncation and preservation counts when the fixture requests a resource test.

The first repeat snapshot must match the reported structured result. Comparison ignores only the runtime-only keys listed in `thresholds.json`; list order is retained.

## Run tests

From the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
py -m unittest discover -s tests -p "test_semantic_reasoning_benchmark.py" -v
```

## Score a future candidate

Save a result bundle conforming to `results.schema.json`, then run:

```powershell
py -m tools.semantic_reasoning_benchmark_v1_0_0.evaluator --results path/to/candidate-results.json
```

Exit codes: `0` means every gate passed; `1` means a valid result bundle failed one or more thresholds or coverage requirements; `2` means the input/schema could not be evaluated.

No candidate engine result is bundled at this stage because Step 2.2 builds the evaluator before the inference engine exists.
