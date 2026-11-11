# Phase 6 — Step 6.2: Expanded Benchmark Corpus and Evaluator

**Status:** FROZEN FOR PHASE 6 FOUNDATION; all construction families remain disabled until implemented and benchmark-enabled  
**Benchmark:** `USG-INTERPRET-GOLD/0.3.0`  
**Interpreter contract:** `USG-INTERPRET/0.3.0`  
**Corpus:** `benchmarks/phase6-interpretation-v0.3.0/corpus.json`  
**Evaluator:** `tools/phase6_interpretation_benchmark_v0_3_0/run.py`  
**Languages:** standard written English (`en`) and Modern Standard Arabic (`ar`)  
**Next gate:** Step 6.3 — typed semantic roles, predicate frames, and valency model

## 1. Purpose and compatibility

This step freezes the first Phase 6 gold benchmark and its independent evaluator before new grammar implementation begins. It is additive to the accepted Phase 5 benchmark. The Phase 4 and Phase 5 corpora, schemas, evaluators, outputs, and published digests remain unchanged.

The benchmark contains 400 fixtures: four candidate construction families in each language, with 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary fixtures per language/construction pair. The corpus does not enable any construction. Every inventory entry is explicitly marked `enabled: false` until its implementation and all acceptance gates pass.

## 2. Initial construction inventory

| Family | English ID | MSA Arabic ID |
|---|---|---|
| Intransitive predicate | `en.intransitive.basic` | `ar.intransitive.basic` |
| Ditransitive predicate | `en.ditransitive.basic` | `ar.ditransitive.basic` |
| Copular predication | `en.copular.predicative` | `ar.copular.predicative` |
| Prepositional/location relation | `en.prepositional.location` | `ar.prepositional.location` |

These are benchmark target labels, not claims that the current interpreter supports them. More construction families from the Phase 6 roadmap (nominal possession/modification, coordination, embedded clauses, voice/speech acts, operators, and discourse reference) must receive their own per-language fixture denominators and benchmark additions before being enabled. The evaluator is designed to report every language/construction pair independently.

## 3. Gold annotation rules

- Every fixture has a unique ID, language, target construction, exact source text, and gold class.
- Positive fixtures annotate the exact construction ID, semantic-role bindings, and exact source spans.
- Negative fixtures do not contain a unique instance of the target construction; they carry no gold target graph.
- Ambiguous fixtures deliberately preserve multiple materially distinct readings; they carry no unique gold target graph and include an ambiguity reason.
- `expected_completion_status` is annotated only for positive target cases. Negative/ambiguous target labels do not dictate whole-pipeline completion status.
- Offsets are zero-based, end-exclusive Unicode code-point offsets into the exact original source text. Gold spans must satisfy `text[start:end] == surface`.
- Role labels are semantic roles, not syntactic positions. The benchmark does not equate word order with Agent, Patient, Recipient, Theme, or Location.
- Gold annotations are not automatically extended by a model. New fixtures require a new versioned corpus revision and independently checked source spans.

## 4. Evaluator contract

The evaluator consumes predictions keyed by fixture ID. A missing prediction is a failed positive case and a conservative abstention for a negative/ambiguous target case; it is never silently removed from a denominator. Duplicate or unknown prediction IDs are invalid.

Metrics are reported per language and construction:

1. positive denominator, negative denominator, ambiguous denominator;
2. construction precision and recall;
3. exact semantic-role binding accuracy;
4. exact and source-valid role-span accuracy;
5. negative-target abstention and ambiguous-target abstention;
6. false unique target constructions.

An empty denominator is an error, never a perfect score. A prediction of a different supported construction on a negative target fixture is not automatically a false positive for this target; scoring is target-construction specific.

## 5. Initial quality gates

Each enabled language/construction pair must independently satisfy:

- precision >= 0.95;
- recall >= 0.90;
- exact role accuracy >= 0.95;
- exact source-valid span accuracy >= 0.95;
- negative-target abstention = 1.00;
- ambiguous-target abstention = 1.00;
- false unique target constructions = 0.

No aggregate score may mask a failing language or construction. A construction that misses a threshold remains disabled. These are initial floor thresholds; later contract or step-specific decisions may make them stricter, never weaken them to force a pass.

## 6. Execution

```bash
python -m pip install "jsonschema==4.23.0"
python -m tools.phase6_interpretation_benchmark_v0_3_0.run
python -m unittest discover -s tests -p "test_phase6_step_6_2_benchmark.py" -v
```

The evaluator validates corpus structure, unique IDs, construction inventory references, minimum denominators, role/span agreement, and exact source slices before scoring. It does not call or simulate the interpreter. Step 6.14 will connect this frozen evaluator to the real Phase 6 pipeline after the construction implementation steps are accepted.

## 7. Limitations and next additions

The 400-case corpus is a controlled initial foundation for four predicate-frame families. It is not a complete benchmark for all Phase 6 goals. Nominal, coordination, embedded-clause, voice/speech-act, operator-scope, and discourse-reference families remain unmeasured and disabled until separately represented with adequate positive, negative, and ambiguous fixtures. Do not advertise those capabilities from this corpus.

**Next step:** Step 6.3 — define the typed semantic-role vocabulary, predicate-frame schema, valency slots, constraints, lexical-sense links, and graph-reference validation.
