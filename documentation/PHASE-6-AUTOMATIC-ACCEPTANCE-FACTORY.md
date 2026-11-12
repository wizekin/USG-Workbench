# Phase 6 Automatic Acceptance Factory

**Version:** 1.0.0  
**Status:** implemented as an automatic evaluation system; runtime capabilities are not promoted by the factory itself.  
**Scope:** bilingual English and Modern Standard Arabic evaluation of the candidate behaviors associated with Steps 6.7–6.11, plus preservation and service integration checks for Steps 6.12–6.14.

## Purpose

The factory gives the remaining Phase 6 work one repeatable, machine-executable evaluation path. It generates a reference corpus, calls the real integrated Phase 6 API for every case, scores the observed graph against the reference, validates preservation and persistence behavior, and writes a versioned report with a separate result for every step and language profile.

It does not equate a successful workflow run with semantic acceptance. The workflow can pass because the factory ran correctly while the report still records one or more Phase 6 steps as `OPEN`.

## Automatic reference generation

Run:

```bash
python -m unittest discover -s tests -p 'test_phase6_acceptance_v1_0.py' -v
python -m tools.phase6_acceptance_v1_0.generate
```

The graph-first generator uses the frozen, accepted Phase 5 v0.2.1 corpus as a seed inventory for supported English/MSA predicate forms and participant values. It constructs a new reference structure before realizing each new multi-clause or transformed sentence. It does not call the Phase 6 interpreter, inspect Phase 6 predictions, reuse Phase 6 development fixtures, consult the runtime candidate lexicon, use model labels, or require human annotations for the generated cases.

The generated corpus contains 500 cases:

| Step/profile family | Languages | Positive | Negative | Ambiguous | Total |
|---|---:|---:|---:|---:|---:|
| 6.7 coordination | English, MSA Arabic | 20 each | 20 each | 10 each | 100 |
| 6.8 embedded/subordinate clauses | English, MSA Arabic | 20 each | 20 each | 10 each | 100 |
| 6.9 voice/speech act | English, MSA Arabic | 20 each | 20 each | 10 each | 100 |
| 6.10 operator scope | English, MSA Arabic | 20 each | 20 each | 10 each | 100 |
| 6.11 discourse reference | English, MSA Arabic | 20 each | 20 each | 10 each | 100 |
| **Total** | **10 language profiles** | **200** | **200** | **100** | **500** |

The generator validates unique IDs, balanced profile sizes, reference metadata, exact Unicode code-point spans, and marker/role source slices. Its seed and canonical corpus SHA-256 make generation reproducible.

### Independence boundary

The generated examples are controlled synthetic compositions based on frozen Phase 5 seed cases. They are not human-adjudicated gold and do not establish naturalistic semantic accuracy. They are useful for testing whether the integrated Phase 6 service recognizes, preserves, or safely abstains on defined construction profiles. The source seed inventory is recorded in every case so results are auditable.

The reference graph is not created by asking the interpreter for an answer. However, the generator and evaluator are still project-authored and must be treated as a controlled synthetic oracle, not as a fully independent external semantic authority.

## End-to-end evaluation

Run:

```bash
python -m tools.phase6_acceptance_v1_0.evaluate
```

The evaluator sends every generated sentence through `USGApplication.dispatch("POST", "/v3/phase6/interpret", ...)`. It does not score a standalone regex/template recognizer in place of the service.

Per-profile measurements include positive detection, construction precision/recall, exact role-span preservation, negative abstention, ambiguity preservation, and false unique/invalid outcomes. It separately checks exact source text and SHA-256 integrity, every observed source span, and the exact marker evidence where a profile requires it.

Ambiguous cases can pass by preserving their alternatives or by a clean abstention. A forced unique interpretation is not accepted. The discourse gate checks preservation of unresolved antecedent candidates rather than requiring identity merging; the current Phase 6 contract deliberately avoids automatic identity resolution without adequate evidence.

## Steps 6.12–6.14

- **6.12:** the factory checks that candidate outputs are preserved in a schema-valid OPAQUE document, that the preserved graph matches the composed graph, and that no canonical assertions are emitted. The report records `PRESERVATION_ONLY`; it does **not** mark semantic-assertion projection accepted.
- **6.13:** the factory runs the integrated API in English and MSA Arabic, stores candidate runs in the existing SQLite store, and checks deterministic replay. The workflow additionally runs the existing Kernel Lab and integrated API regressions.
- **6.14:** the final step is marked accepted only if every preceding factory gate passes. It does not override an open step or turn candidate-only outputs into supported semantic capabilities.

The report is validated against [the versioned report schema](../specifications/phase6-automatic-acceptance-report-1.0.schema.json).

## Machine outputs

- Corpus: `benchmarks/phase6-automatic-acceptance-v1.0/corpus.json`
- Report: `artifacts/phase6-automatic-acceptance-report.json`
- Report schema: `specifications/phase6-automatic-acceptance-report-1.0.schema.json`
- CI workflow: [Phase 6 Automatic Acceptance Factory](../.github/workflows/phase6-automatic-acceptance.yml)

The report includes the corpus digest, each profile's metrics and failed case IDs, per-step status, source/preservation checks, API/SQLite/replay checks, and the explicit capability-claim policy. The generated files are CI artifacts; they are not committed as mutable benchmark fixtures by the workflow.

## Gate policy and interpretation

Initial quality gates are applied separately to each language profile:

- precision at least 0.95 and recall at least 0.90;
- exact source/role spans at 1.00;
- 100% negative abstention and ambiguity preservation;
- zero false unique outcomes;
- all required fixture minimums satisfied.

No language or construction is rescued by an aggregate score. A profile that misses a gate remains open. A successful factory run means only that the generator, evaluator, report validation, and required regressions executed successfully.

The automatic factory does not itself complete missing runtime grammar or verify that a candidate relation is a canonical semantic assertion. It makes those gaps measurable and prevents unsupported capability claims.
