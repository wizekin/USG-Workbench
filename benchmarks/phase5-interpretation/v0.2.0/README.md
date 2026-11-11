# Phase 5 Interpretation Benchmark v0.2.0

This is the versioned gold-corpus foundation for `USG-INTERPRET/0.2.0`. It is independent of and does not modify the frozen six-case Phase 4 v0.1.0 benchmark.

## Scope

The initial measured construction family is simple transitive declaratives:
- English: explicit subject–verb–object (SVO).
- Modern Standard Arabic: explicit verb–subject–object (VSO).

The corpus contains 100 cases: 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary cases for each language. Positive cases annotate AGENT, ACTION, and PATIENT with exact source spans. Negative and ambiguous cases deliberately do not invent a unique semantic role graph.

These are gold evaluation fixtures, not a claim that the current v0.1.0 interpreter supports all 40 positive examples. The benchmark runner can now execute the actual `USG-INTERPRET/0.2.0` service over every fixture with `--run-pipeline`; the report includes real per-language metrics and a resource-pinned runtime/memory profile. No synthetic or gold-derived predictions are used. Synthetic perfect predictions in unit tests verify evaluator arithmetic only and MUST NOT be reported as model performance.

## Run

From the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
py -m tools.phase5_interpretation_benchmark_v0_2_0.run
py -m unittest discover -s tests -p "test_phase5_benchmark.py" -v
```

Evaluate a prediction file using `--predictions path/to/predictions.json`; optionally use `--output report.json`.

## Prediction shape

Each row in the top-level `predictions` array has `case_id`, `completion_status`, `construction_id` (null when no unique construction is emitted), `role_bindings`, and `role_spans`. A role span is an object with zero-based, end-exclusive Unicode code-point offsets and the exact `surface` slice. Unknown case IDs and duplicate prediction rows are rejected. Missing predictions are counted and do not receive credit.

## Metrics

The evaluator reports per-language construction precision/recall, completion-status accuracy, exact role-binding accuracy, exact and source-valid role-span accuracy, false unique constructions on negative/ambiguous cases, abstention rates, confusion counts, and missing predictions. The real pipeline run additionally reports total/mean/median/p95 latency, peak traced Python memory, and the exact resource-manifest digest. Corpus fixture counts and gold span validity are checked before scoring.

No aggregate metric substitutes for per-language results. An empty prediction set is not interpreted as 100% accuracy. A construction must remain disabled until the benchmark and its adversarial acceptance gate pass.
