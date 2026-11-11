# Phase 6 Step 6.6 — Benchmark v0.4.0

**Status:** candidate gold corpus; linguistic adjudication and runtime acceptance pending.

The additive v0.4.0 corpus has 500 fixtures across ten English/MSA Arabic profiles, each with 20 positive, 20 negative, and 10 ambiguous cases. It separates role, predicate, and grammatical-marker spans and validates exact Unicode code-point offsets.

**Important limitation:** this first candidate set is not a fully adjudicated linguistic gold standard. English *of* phrases can express more than possession; Arabic iḍāfa and lexicalized compounds can overlap; and the negative/ambiguous sets are screening candidates. Do not claim model accuracy from this corpus until its labels and coverage are independently adjudicated. No construction is enabled by this PR. Earlier benchmark versions remain unchanged.


## Corpus correction note

The initial v0.4.0 corpus commit contained an MSA Arabic iḍāfa positive-fixture constituent-order error. The follow-up correction changes those 20 examples to possessed-noun + possessor order and recalculates exact Unicode spans. The original commit is superseded by this corrected version. The corpus remains candidate-only; no accuracy or runtime-support claim is made.


## Negative-fixture correction

The original negative pool reused nominal/modifier-positive examples from other profiles, which could create false-negative gold labels. The corrected corpus replaces all negative rows with simple intransitive clauses lacking nominal modification, possession, compounds, nominal prepositional attachment, or temporal modifiers. This correction improves target-specific negative validity but does not replace independent linguistic adjudication of positive and ambiguous examples.
