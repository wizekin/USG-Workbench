# Phase 6 Step 6.6 — Candidate Nominal Interpreter

**Status:** IMPLEMENTED — CANDIDATE ONLY; benchmark enablement pending.

The deterministic candidate recognizer implements closed-profile patterns for English/MSA Arabic adjective modification, genitive relations, lexicalized noun compounds, nominal prepositional modifiers, and temporal/adverbial modifiers. It preserves exact Unicode code-point spans, typed structural roles, predicate spans, grammatical markers, and the unspecified semantics of genitive relations.

## Critical evaluation boundary

The lexical resource is extracted from the same v0.4.1 positive fixtures used by the development evaluation. Therefore the reported scores are **in-sample closed-lexicon self-consistency**, not an independent benchmark, generalization test, or evidence of broad language understanding. The analyzer returns `CANDIDATE`, not `COMPLETE`, and no construction is benchmark-enabled. Unknown forms and out-of-profile inputs abstain. No productive morphology is inferred.

## Run

`python -m tools.phase6_nominal_candidate_v0_4_1.run`

The report is written to `artifacts/phase6-step-6.6-development-report.json`. A passing development gate verifies internal consistency only. A separate independent lexical/linguistic test set and full graph integration are required before any construction can be enabled.
