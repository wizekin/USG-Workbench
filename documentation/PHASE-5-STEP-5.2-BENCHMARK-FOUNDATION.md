# Phase 5 — Step 5.2: Expanded Benchmark Corpus and Evaluator Foundation

**Status:** FROZEN CORPUS AND EVALUATOR FOUNDATION  
**Contract:** `USG-INTERPRET/0.2.0`  
**Corpus:** `usg-interpretation-v0.2.0-foundation`  
**Gold annotation profile:** `USG-INTERPRET-GOLD/0.1.0`  
**Previous benchmark:** Phase 4 `USG-INTERPRET/0.1.0` six-case corpus remains immutable.

## 1. Purpose

This step establishes the benchmark and scoring foundation before enabling new interpretation capabilities. It provides a versioned gold corpus, exact role-span annotations, a schema, a deterministic evaluator, and synthetic evaluator tests. Synthetic predictions test evaluator arithmetic only; they are not interpreter performance results.

## 2. Measured scope and corpus inventory

The first construction family is a simple transitive declarative clause:
- English standard written SVO: `AGENT + ACTION + PATIENT`.
- Modern Standard Arabic VSO: `ACTION + AGENT + PATIENT`.

The v0.2.0 corpus has 100 cases:

| Language | Positive | Negative/adversarial | Ambiguous/boundary | Total |
|---|---:|---:|---:|---:|
| English | 20 | 20 | 10 | 50 |
| MSA Arabic | 20 | 20 | 10 | 50 |
| **Total** | **40** | **40** | **20** | **100** |

Every positive case contains a unique gold construction ID, AGENT/ACTION/PATIENT role values, and exact source spans. Negative and ambiguous cases do not receive fabricated unique role graphs. The Phase 4 six-case corpus and its evaluator are untouched.

The corpus is a future-facing evaluation target. The bounded Phase 4 `0.1.0` interpreter does not support all lexical entries or examples in this corpus; no claim of full coverage is made by creating gold annotations.

## 3. Gold annotation and offsets

- Source offsets are zero-based, end-exclusive Unicode code-point positions.
- Every annotated span must exactly equal the corresponding source slice.
- The initial semantic role inventory is deliberately limited to AGENT, ACTION, and PATIENT for this transitive-clause benchmark.
- `POSITIVE` expects `COMPLETE` plus the language-specific construction ID.
- `NEGATIVE` expects `UNSUPPORTED` and no unique construction or role graph.
- `AMBIGUOUS` expects `AMBIGUOUS` and no unique construction or role graph.
- The corpus schema rejects unknown fields, invalid statuses, malformed role spans, and an undersized corpus.

## 4. Evaluator contract

The evaluator accepts a prediction file keyed by unique `case_id`. It reports independently for each language:
- construction true/false positives and false negatives;
- construction precision and recall;
- completion-status accuracy;
- exact role-binding accuracy on positive gold cases only;
- exact, source-valid role-span accuracy on positive gold cases only;
- missing prediction count.

Unknown or duplicate prediction IDs are rejected. Missing predictions receive no credit. Predictions with source spans that do not slice to the exact surface are invalid for the span metric. The evaluator never fills missing predictions or treats an empty denominator as a perfect score.

Without an actual prediction file, the CLI reports `NOT_EVALUATED_NO_PREDICTIONS_SUPPLIED`. Unit tests use synthetic perfect and deliberately corrupted predictions solely to test metric arithmetic.

## 5. Acceptance criteria

Step 5.2 is accepted when:
1. Corpus schema validation passes.
2. Both languages meet the minimum 20/20/10 fixture counts.
3. Every positive gold role span is source-aligned.
4. Evaluator rejects unknown/duplicate IDs and reports missing predictions.
5. Synthetic perfect predictions yield exact arithmetic of 1.0 for all expected metrics.
6. Synthetic false positives, false negatives, and invalid spans reduce the corresponding metrics.
7. The frozen Phase 4 benchmark/tests and protected USG-SEM/1.0, SQLite, archive, and historical implementation boundaries remain unchanged.

## 6. Next step

After this foundation merges, begin Step 5.3 — Versioned Lexical and Morphology Resources. The initial lexicon must be built from provenance-bearing, licensed/attributed resources or explicitly authored fixtures; benchmark words alone do not authorize claims of broad lexical coverage.
