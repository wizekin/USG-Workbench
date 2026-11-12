# Phase 6 Step 6.6 — Automatic Synthetic Semantic Reference Protocol

**Status:** bounded automatic-reference acceptance implemented; naturalistic semantic validation remains a separate future workstream.  
**Benchmark:** `usg-phase6-automatic-synthetic-reference/1.0.0`  
**Contract:** `USG-INTERPRET/0.3.0`

## Decision

Step 6.6 no longer depends on a human-annotated bilingual corpus. The project uses an automatically generated, reproducible semantic-reference benchmark. It is an explicit replacement for the previous human-annotation and external-corpus intake gate.

The benchmark is **not described as human gold or an external natural-language corpus**. Its expected structures are machine-generated from a semantic graph created before text realization. This gives the project a deterministic oracle for a bounded synthetic construction scope without using the candidate interpreter to create or label its own test cases.

## Automatic generation design

The pipeline is:

1. Select a versioned construction scenario and language-specific lexical seed.
2. Construct the reference semantic graph first: typed nodes, semantic relations, attachment target, ambiguity state, and expected roles.
3. Realize the graph as a controlled English or MSA Arabic sentence using an explicit construction template.
4. Derive exact Unicode code-point spans by aligning the graph's role values with the realized sentence.
5. Validate the graph, profile counts, unique case IDs, exact spans, and provenance declarations.
6. Evaluate the candidate recognizer against the generated expected result. Candidate predictions are never consulted during generation or reference-label creation.

The implementation is in `tools/phase6_auto_reference_v1_0/`. The benchmark-only lexical resource is generated separately and injected only during evaluation. It does not replace or mutate the active lexical resource catalogue.

## Dataset scope

The benchmark contains 500 deterministic cases:

| Language | Construction | Positive | Negative | Ambiguous |
|---|---|---:|---:|---:|
| English | adjective modifier | 20 | 20 | 10 |
| English | genitive / of-phrase | 20 | 20 | 10 |
| English | noun compound | 20 | 20 | 10 |
| English | prepositional nominal modifier | 20 | 20 | 10 |
| English | temporal/adverbial modifier | 20 | 20 | 10 |
| MSA Arabic | adjective modifier | 20 | 20 | 10 |
| MSA Arabic | iḍāfa / genitive | 20 | 20 | 10 |
| MSA Arabic | lexicalized compound | 20 | 20 | 10 |
| MSA Arabic | prepositional nominal modifier | 20 | 20 | 10 |
| MSA Arabic | temporal/adverbial modifier | 20 | 20 | 10 |
| **Total** | **10 profiles** | **200** | **200** | **100** |

The lexical seeds are original project-authored strings and names, not dataset annotations. Generated benchmark data, the reference lexicon, and benchmark reports are dedicated under **CC0-1.0**. The benchmark's license is separate from the USG software license.

## Automatic reference and ambiguity policy

- Adjective examples encode an `ATTRIBUTE` edge from a property node to a nominal head.
- Genitive examples encode `GENITIVE_UNSPECIFIED`; the form does not entail ownership, authorship, kinship, or part-whole.
- Compound examples encode a lexicalized component relation only in the positive profile. Boundary cases retain competing compound/genitive or adjective/compound analyses.
- Prepositional examples encode a locative nominal-modifier edge. Multiple-preposition cases are boundary cases and must not be forced into a unique attachment.
- Temporal examples encode an `EVENT_TIME` edge. Multi-event cases preserve scope uncertainty and must not receive a unique event-time attachment.

The benchmark tests exact role bindings, exact source spans, relation candidates, negative abstention, and preservation of ambiguous cases.

## Acceptance result and gate

The automatic evaluator runs all 500 cases separately by profile. Acceptance requires, for every profile:
- at least 95% positive detection, exact role accuracy, exact span accuracy, and relation accuracy;
- 100% abstention on negative cases;
- 100% preservation of the encoded ambiguous/boundary outcomes;
- zero false-unique ambiguity resolutions.

The current candidate implementation passes all ten synthetic profile gates at 100% on the current generated suite. The report includes the full per-profile metrics and SHA-256 digests. CI regenerates the corpus and report from source, runs contract tests, and uploads them as workflow artifacts.

Run locally:

```bash
python -m compileall -q tools/phase6_auto_reference_v1_0 tools/phase6_nominal_candidate_v0_4_1
python -m unittest discover -s tests -p 'test_phase6_auto_reference_v1_0.py' -v
python -m tools.phase6_auto_reference_v1_0.evaluate
```

Workflow: [Phase 6 Step 6.6 Automatic Synthetic Reference Gate](../.github/workflows/phase6-step-6-6-automatic-reference.yml).

## Exact limits of this acceptance

This acceptance establishes **bounded construction-level capability on the generated reference domain only**. It does not establish:
- semantic correctness on naturally occurring English or native MSA text;
- coverage of unseen lexical items, productive morphology, free word order, dialects, discourse, or unrestricted PP/temporal scope;
- that every generated sentence is idiomatic or representative;
- equivalence to an independently human-annotated benchmark;
- runtime readiness or automatic semantic-rule promotion.

The generator and recognizer deliberately share the same versioned construction inventory. That is appropriate for deterministic conformance testing, but it limits independence from design assumptions. Future naturalistic validation can use any legally usable corpus as a separately reported diagnostic; it is no longer a blocker for this bounded Step 6.6 gate.

## Runtime and downstream state

All ten Step 6.6 recognizers remain **CANDIDATE_ONLY**. The new `semantic_relation_candidate` output is an explicit candidate field; the existing `relation_type`, parser behavior, canonical `USG-SEM/1.0`, active lexicon, and Phase 1–5 contracts remain unchanged.

Step 6.6 is accepted for the bounded automatic synthetic-reference scope. Step 6.7 may begin as a candidate-development step. Neither this acceptance nor its test scores authorize production promotion. Any future runtime promotion requires additional naturalistic evidence, separate review, and its own acceptance gate.

## Replaced process

The former [Independent Bilingual Semantic-Gold Acceptance Protocol](PHASE-6-STEP-6.6-INDEPENDENT-GOLD-ACCEPTANCE-PROTOCOL.md) is retained as historical documentation only. Human annotation, adjudication, and external bilingual corpus acquisition are no longer prerequisites for this bounded milestone.
