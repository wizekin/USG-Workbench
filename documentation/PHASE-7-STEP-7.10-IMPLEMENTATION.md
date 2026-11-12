# Phase 7 Step 7.10 — Evaluation, Performance, and Exit Acceptance

**Status:** implementation submitted for exact-head CI; acceptance is pending.  
**Evaluator:** `USG-PHASE7-ACCEPTANCE-REPORT/0.1.0`

## Frozen evaluation population

The acceptance fixture pins the project-authored `usg-en-ar-discourse-lexicon@0.3.0` resource by its Git blob SHA. It contains 48 resource entries, 46 unique language/form pairs, and 43 unique lexical senses.

The suite generates:
- 46 exact-form positive retrieval cases across English and MSA Arabic;
- 46 wrong-language adversarial negatives;
- 10 out-of-vocabulary negatives;
- 2 explicit polysemy checks (English `bank`, Arabic `عين`);
- unresolved mapping, provenance, rights/lifecycle, conflict-retention, deterministic replay, and SQLite snapshot round-trip gates.

No human annotations, model-generated labels, external lexical data, or assumed translation equivalences are used.

## Acceptance command

```bash
python -m unittest discover -s tests -p 'test_phase7_knowledge_evaluation.py' -v
python -m tools.phase7_knowledge_evaluation.evaluate --output phase7-acceptance-report.json
```

The Phase 7 GitHub Actions workflow runs the evaluator, stores the machine-readable report as an artifact, and retains prior semantic/interpretation regression checks.

## Exit gates

- Every frozen exact-form case retrieves its declared form and expected sense candidates.
- Wrong-language and OOV negatives return no lexical-form match.
- Polysemous forms retain all expected sense alternatives.
- Every cross-language mapping proposal remains `UNRESOLVED`.
- Source attribution, locator, digest, and rights/lifecycle metadata remain present.
- Contradictory provider evidence remains visible with no winner selection.
- Identical inputs replay to the same canonical bundle digest.
- SQLite snapshot storage and retrieval preserve the canonical digest.
- False merges and unsupported promotions remain zero in this acceptance population.

## Acceptance boundary and limitations

A passing report accepts only this frozen project-authored bilingual lexical retrieval/mapping/reconciliation profile and the listed integration regressions. It does not establish general semantic accuracy, broad naturalistic coverage, unrestricted morphology, truth adjudication, unrestricted knowledge retrieval, or AGI. The provider conflict is synthetic; external rights-policy behavior is additionally covered by the dedicated rights-aware adapter tests. Broader naturalistic corpora and additional relation/source profiles remain future work.
