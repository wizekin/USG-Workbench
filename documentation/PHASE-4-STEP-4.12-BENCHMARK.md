# Phase 4 — Step 4.12: Frozen Benchmark and Adversarial Evaluation

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Corpus:** `usg-interpretation-v0.1.0`

The frozen corpus contains six cases: English SVO and Arabic VSO supported examples, unknown lexical material, multiple sentences, a known but unregistered word order, and empty input. It measures completion-status accuracy, exact source preservation, evidence span alignment, canonical USG-SEM/1.0 SQLite validation, unresolved items, unsupported inputs, and truth-policy violations.

Acceptance requires 100% on the six explicitly bounded fixtures, 100% exact source preservation, 100% exact evidence alignment, 100% canonical document validation, and zero truth-policy violations. These thresholds apply only to this small frozen demonstrator corpus; they are not a claim of broad English/Arabic coverage or general language understanding.

Run:

```bash
python -m tools.phase4_interpretation_benchmark_v0_1_0.run --output phase4-benchmark-report.json
```

The machine-readable report records per-case outcomes and aggregate metrics. New fixtures require a benchmark version increment rather than silently changing the frozen baseline.
