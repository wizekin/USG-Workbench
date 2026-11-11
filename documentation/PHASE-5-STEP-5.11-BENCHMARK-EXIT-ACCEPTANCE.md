# Phase 5 Step 5.11 — Full Interpreter Benchmark and Exit Acceptance

**Status:** IMPLEMENTATION CANDIDATE — full-corpus execution and CI measurement pending.

## Objective

Execute the actual deterministic `USG-INTERPRET/0.2.0` service against every frozen fixture in `benchmarks/phase5-interpretation-v0.2.1/corpus.json`. The benchmark must not synthesize predictions from gold labels or count corpus fixture validation as model performance.

## Execution

From the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
py -m tools.phase5_interpretation_benchmark_v0_2_0.run --run-pipeline --output benchmark-report.json
py -m unittest discover -s tests -p "test_phase5_step_5_11_benchmark.py" -v
```

The runner invokes `Phase5InterpretationService` once per fixture and derives a unique construction/role prediction only when the service returns one complete semantic candidate and one syntax candidate. It otherwise abstains; it does not infer a missing role graph from the expected labels.

## Required report

- Separate English and MSA Arabic construction precision and recall.
- Exact AGENT/ACTION/PATIENT role-binding accuracy.
- Exact, source-slice-valid role-span accuracy using Unicode code-point offsets.
- Positive-case completion-status accuracy and missing prediction count; nonpositive whole-pipeline statuses are not forced to one label.
- False unique constructions on negative and ambiguous fixtures.
- Negative and ambiguous abstention rates.
- Total, mean, median, and p95 per-case latency.
- Peak traced Python allocation during the corpus run (explicitly not an OS RSS measurement).
- SHA-256 identity of both the bundled resource descriptor manifest and canonicalized gold corpus used for the run.
- The enabled target constructions observed in the run.
- Per-case outcomes so regressions can be diagnosed rather than hidden by aggregate scores.

## Acceptance gates

1. All 100 gold fixtures validate; each language has at least 20 positive, 20 negative, and 10 ambiguous fixtures.
2. Every positive construction meets the Phase 5 roadmap thresholds independently per language: precision >= 0.95 and recall >= 0.90.
3. Every emitted role span is valid against the exact source; exact role and span accuracy must be reported independently for each language.
4. Negative and ambiguous target-class fixtures must not receive a guessed unique target-construction graph. Their overall pipeline status is not forced to UNSUPPORTED/AMBIGUOUS: supported multi-clause content may complete, while out-of-profile or unresolved content may be partial or unsupported. Any false unique construction is a release blocker until explained and corrected.
5. Ambiguous fixtures must remain ambiguous or explicitly abstain; no unjustified unique construction may be emitted.
6. No resource, memory, or candidate budget may silently truncate or fabricate an interpretation.
7. All Phase 1–4 regressions, Step 5.10 integrated API/CLI/Kernel Lab tests, clean-wheel packaging, SQLite integrity, and deterministic replay checks pass.
8. Publish the exact commit, frozen corpus digest, resource-manifest digest, full JSON report, enabled construction list, and known limitations.

## Benchmark interpretation boundaries

The frozen v0.2.0 corpus is retained unchanged. The additive v0.2.1 100-case corpus measures simple transitive English SVO and MSA Arabic VSO/SVO, with the Arabic SVO example explicitly annotated by surface grammatical order. Negative fixtures may include structures that later Phase 5 steps partially or fully support (for example coordination). The report distinguishes “not a single-clause target construction” from “the whole v0.2 pipeline cannot interpret this input.” The v0.2.1 corpus therefore scores whole-pipeline completion status only for positive target-construction cases; negative and ambiguous cases are evaluated by abstention and false-assertion metrics. A supported multi-clause result is not called unsupported merely because it is outside the single-clause construction metric.

The performance profile is a reproducible CI baseline, not a hardware-independent speed guarantee. It measures one process and Python traced allocations; it does not claim native-memory or production concurrency coverage.

Step 5.11 is accepted only after the automated per-language quality gate passes and the full integrated compatibility matrix passes. A benchmark report with failing metrics is diagnostic evidence, not a passing acceptance.
