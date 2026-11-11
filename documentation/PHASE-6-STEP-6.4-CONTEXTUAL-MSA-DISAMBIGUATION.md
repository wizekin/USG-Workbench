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
- Train an averaged structured perceptron on nine folds and evaluate on the
  held-out fold.
- Features include current/neighboring forms, prefixes/suffixes, sentence
  boundaries, candidate UPOS/POS sets, and CAMeL morphological features.
- Predict UPOS from sentence context, then select the highest-ranked CAMeL
  lemma analysis that matches the predicted UPOS.
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
