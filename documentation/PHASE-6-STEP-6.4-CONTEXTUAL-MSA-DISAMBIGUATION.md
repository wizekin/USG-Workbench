# Phase 6 Step 6.4 — Contextual MSA Morphology Disambiguation v0.6

**Status:** candidate research experiment; not a USG runtime component.

## Purpose

The CAMeL MSA morphology evaluation produced broad candidate coverage but
substantial ambiguity. This experiment tests whether a lightweight contextual
sequence model can select the correct UPOS and then choose a compatible lemma
from the CAMeL candidate analyses.

## Method

- Use the pinned Arabic PUD treebank with ten stable sentence-ID-hash folds.
- Obtain the full morphological candidate set from the CAMeL Analyzer and the
  separate MLE top-1 word-based selection for the baseline.
- Train an averaged structured perceptron for three deterministic epochs on
  nine folds and evaluate on the held-out fold.
- Features include current/neighboring forms, prefixes/suffixes, sentence
  boundaries, candidate UPOS/POS sets, and CAMeL morphological features.
- Decode UPOS with Viterbi while constraining each token to the POS candidates
  licensed by the morphology analyzer (training sentences also retain their
  gold POS so missed candidates can be measured).
- Select the highest-ranked CAMeL lemma analysis that matches the predicted
  UPOS; abstain if no compatible analysis exists.
- Compare against CAMeL MLE top-1, which is a word-based/out-of-context
  baseline, and report the candidate-set upper bound.

## Licensing and runtime boundary

CAMeL Tools code is MIT-licensed. The CALIMA MSA morphology database and MLE
model data packages are GPL-2.0. They are installed only in ephemeral CI and
are not copied into this repository or USG runtime distribution. The model
trained by this experiment is generated transiently and not persisted.

## Interpretation limits

The perceptron predicts POS only; lemma selection is constrained to the
pre-existing CAMeL candidate set. It cannot repair a missing lemma candidate.
PUD is a held-out evaluation corpus, but CAMeL training-data overlap is
unknown. Results are syntactic/morphological only and provide no semantic-role
or construction acceptance credit.

A successful result would justify a separate optional contextual lexical
adapter study, not automatic runtime integration. A failure or lack of
improvement should be retained as a negative result.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_contextual.py' -v
python -m tools.phase6_external_pud_v0_6.contextual
```

## Observed ten-fold results (2026-11-11)

The final run evaluated all 20,747 annotated Arabic PUD tokens. The model used
three epochs per fold and constrained test-time POS decoding to the POS
candidates returned by the morphology analyzer.

| Measure | Result |
|---|---:|
| Full morphology candidate upper-bound lemma/POS recall | 75.32% |
| CAMeL MLE top-1 lemma/POS accuracy (word-based baseline) | 69.49% |
| Contextual structured-perceptron POS accuracy | 77.69% |
| Contextual candidate-selected lemma/POS accuracy | 73.18% |
| Selected accuracy when a candidate was selected | 77.91% |
| Candidate selection coverage | 93.92% |
| Abstention rate | 6.08% |
| Ambiguous candidate rate | 52.23% |

The contextual selector improves exact lemma/POS accuracy by 3.69 percentage
points over CAMeL MLE top-1 overall, recovering 73.18% of tokens against a
75.32% candidate-set upper bound. This indicates that sentence context helps
select among the morphology candidates, but the remaining gap is real.

The improvement is not uniform across parts of speech:

| UPOS | MLE top-1 | Contextual selection |
|---|---:|---:|
| NOUN | 84.14% | 85.72% |
| VERB | 91.51% | 90.48% |
| ADJ | 72.25% | 76.20% |
| PROPN | 32.70% | 33.80% |

Verb selection is slightly worse than the MLE baseline, and proper-name
performance remains poor. The model is therefore not ready for runtime
integration. A separate name/entity pathway and improved lemma ranking are
needed; do not tune per-class rules against this same test set.

**Decision:** retain this as a promising candidate-only contextual baseline.
It demonstrates an overall improvement over the out-of-context MLE baseline,
but is not a validated production disambiguator. The result gives no semantic
role or construction acceptance credit, and Step 6.6 remains unaccepted.

Report artifact:
[workflow run 42992316211](https://github.com/wizekin/USG-Workbench/actions/runs/42992316211).
