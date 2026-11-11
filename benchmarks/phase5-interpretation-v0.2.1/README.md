# Phase 5 Interpretation Benchmark v0.2.1

This is an additive, versioned gold-corpus revision for the unchanged `USG-INTERPRET/0.2.0` interpreter contract. The earlier `v0.2.0` corpus and its documentation remain frozen.

## Scope

The target construction family is simple transitive declaratives:
- English: explicit subject–verb–object (SVO).
- Modern Standard Arabic: explicit verb–subject–object (VSO) and subject–verb–object (SVO).

The corpus contains 100 cases: 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary cases per language. Positive cases annotate AGENT, ACTION, and PATIENT with exact source spans. Negative and ambiguous cases do not define a unique target-construction graph.

The v0.2.1 revision corrects the Arabic SVO annotation: `الرسالة كتب الطالب.` is evaluated according to its explicit SVO surface order, not a presumed intended agent/patient reversal. A separate unsupported Arabic prepositional construction preserves the negative fixture count.

## Status annotation policy

`expected_completion_status` is populated only for positive target-construction cases. It is null for negative and ambiguous target-class cases because those labels describe the target construction, not necessarily the completion state of the entire pipeline. For example, a negative target case may contain two clauses that the broader v0.2 pipeline can compose successfully. Negative and ambiguous quality is measured through unique-construction abstention and false-assertion rates, not by forcing every such input to report `UNSUPPORTED` or `AMBIGUOUS`.

## Run

```powershell
py -m pip install "jsonschema>=4.18,<5"
py -m tools.phase5_interpretation_benchmark_v0_2_0.run --run-pipeline --output benchmark-report.json
py -m unittest discover -s tests -p "test_phase5_step_5_11_benchmark.py" -v
```

## Metrics

The evaluator reports per-language construction precision/recall, positive completion-status accuracy, exact role-binding accuracy, exact source-valid role-span accuracy, negative/ambiguous abstention, false unique constructions, and missing predictions. The actual pipeline run additionally reports runtime percentiles, peak traced Python memory, and resource-manifest digest.

The original v0.2.0 corpus remains unchanged and can still be used for historical comparisons. Do not replace or silently rewrite a published corpus version.
