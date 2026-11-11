# USG Interpretation Gold Benchmark v0.3.0

**Contract:** `USG-INTERPRET/0.3.0`  
**Gold profile:** `USG-INTERPRET-GOLD/0.3.0`  
**Status:** frozen foundation; all four construction families remain disabled pending implementation and measured acceptance.

## Coverage

The corpus contains 400 fixtures: four construction families per language, each with 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary cases.

| Language | Construction | Positive | Negative | Ambiguous |
|---|---|---:|---:|---:|
| English | intransitive | 20 | 20 | 10 |
| English | ditransitive | 20 | 20 | 10 |
| English | copular predication | 20 | 20 | 10 |
| English | prepositional/location | 20 | 20 | 10 |
| MSA Arabic | intransitive | 20 | 20 | 10 |
| MSA Arabic | ditransitive | 20 | 20 | 10 |
| MSA Arabic | copular predication | 20 | 20 | 10 |
| MSA Arabic | prepositional/location | 20 | 20 | 10 |

## Annotation policy

- Positive cases provide exact semantic-role bindings and Unicode code-point source spans.
- Negative and ambiguous cases do not provide a unique target graph.
- Whole-pipeline completion status is scored only for positive target cases; a negative target label does not force the pipeline to return `UNSUPPORTED`.
- All fixture IDs are unique. Gold spans must satisfy the exact source slice.
- Ambiguous fixtures include an explicit reason and must be abstained from for the target construction.

## Run

```bash
python -m pip install "jsonschema==4.23.0"
python -m tools.phase6_interpretation_benchmark_v0_3_0.run
python -m unittest discover -s tests -p "test_phase6_step_6_2_benchmark.py" -v
```

The evaluator scores each language/construction pair independently. It rejects empty denominators and does not treat missing predictions as removed cases. The real Phase 6 interpreter is not yet connected; Step 6.14 will execute it against this frozen corpus.

## Scope limitation

This corpus measures only the four listed predicate-frame families. Nominal possession/modification, coordination, embedded clauses, voice/speech acts, operator scope, and discourse reference remain unmeasured and disabled until adequate per-language fixtures are added in a versioned benchmark extension.
