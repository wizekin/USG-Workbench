# Phase 6 Step 6.6 — Held-Out Combination Evaluation v0.4.3

**Status:** candidate evaluation only; no construction is enabled.

The v0.4.3 split tests 500 generated cases: 20 positive, 20 negative, and 10 ambiguous/out-of-profile cases for each of five construction families in English and MSA Arabic. Positive role-binding combinations are excluded from the v0.4.2 development corpus. The same closed candidate lexicon is used, so this measures recombination of known lexical entries rather than unseen vocabulary. Cases are generated deterministically from versioned resources and exact gold-role constraints; it is not an independently annotated linguistic test set.

The evaluator measures exact candidate selection, role bindings, source spans, grammatical markers, predicate spans, relation labels, and abstention. All outputs remain CANDIDATE; this benchmark cannot promote any construction to COMPLETE or benchmark-enabled.

Run: `python -m tools.phase6_nominal_candidate_v0_4_1.holdout`

The generated corpus is written to `benchmarks/phase6-interpretation-v0.4.3-heldout/corpus.json`; the per-profile report is written to `artifacts/phase6-step-6.6-heldout-report.json`. A failure blocks Step 6.6 acceptance and all downstream Step 6.7 work.
