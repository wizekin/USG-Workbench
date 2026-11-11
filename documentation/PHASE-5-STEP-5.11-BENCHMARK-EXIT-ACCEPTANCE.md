# Phase 5 Step 5.11 — Full Interpreter Benchmark and Exit Acceptance

**Status:** ACCEPTED — benchmark quality gates and full integrated compatibility matrix passed.

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


## Measured acceptance result

<badge color="success">All Step 5.11 gates passed</badge>

CI run: [Phase 5 Step 5.11 benchmark run #42965506600](https://github.com/wizekin/USG-Workbench/actions/runs/42965506600)

| Metric | English SVO | MSA Arabic VSO/SVO |
|---|---:|---:|
| Positive fixtures | 20/20 | 20/20 |
| Construction precision | 100% | 100% |
| Construction recall | 100% | 100% |
| Positive completion-status accuracy | 100% | 100% |
| Exact role-binding accuracy | 100% | 100% |
| Exact source-span accuracy | 100% | 100% |
| Negative target abstention | 100% | 100% |
| Ambiguous target abstention | 100% | 100% |
| False unique constructions | 0 | 0 |

Performance on the GitHub Actions Ubuntu runner (Python 3.11.18), single-process in-memory run:

- 100 fixtures in **685.388 ms** total.
- Mean **6.854 ms** per case; median **5.724 ms**; p95 **11.082 ms**.
- Peak traced Python allocation: **523,422 bytes** (not OS RSS or native allocator memory).
- Corpus SHA-256: `2eb0bc3d9f0c0b2c7131304c0ebd22b136a2cf71f5e38aa9527969a8bcbd3364`.
- Resource-manifest SHA-256: `d0ea95ed093a9a15a326f2ed06d7463ab1b9272533403e86db2afcff1c56f6cd`.
- Enabled constructions observed: `en.simple_transitive.svo`, `ar.simple_transitive.vso`, `ar.simple_transitive.svo`.

[Download/view the machine-readable benchmark artifact](https://github.com/wizekin/USG-Workbench/actions/runs/42965506600/artifacts/13830553681).

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
