# Phase 6 Step 6.4 — External PUD Morphology Generalization v0.4

**Status:** candidate research track; not a production lexical resource or runtime integration.

## Purpose

The existing Phase 5/6 lexical resources are versioned and provenance-bearing,
but their surface forms are mostly fixture-derived. The external PUD audits
showed that exact-form coverage does not transfer well. This experiment tests
whether bounded prefix/suffix paradigms can generate lemma candidates for
held-out forms without copying the held-out annotations into the rules.

## Method

- Use pinned English and Arabic PUD snapshots (CC BY-SA 3.0); verify the
  upstream Git blob hashes through the existing downloader.
- Split each language into ten stable sentence-ID-hash folds.
- For each fold, induce rules only from the other nine folds' FORM, LEMMA,
  UPOS, and FEATS annotations.
- Support prefix attachment, suffix attachment/replacement, and a constrained
  consonant-doubling pattern. Require at least two training observations for
  each complete rule.
- Apply rules to held-out surface forms and report exact-form coverage, OOV,
  lemma/POS candidate recall, feature-bundle candidate recall, morphology
  rescue, and ambiguity.
- Do not persist PUD text, fold-derived lexicons, or rules as production data.

## Scope and limitations

This is a lexical morphology candidate generator, not a contextual POS tagger,
dependency parser, or semantic interpreter. Rule candidates are not truth.
Internal stem changes and non-concatenative Arabic morphology are not guessed.
UD UPOS/FEATS are external syntactic/morphological labels, not USG semantic
sense annotations.

The output receives no semantic acceptance credit and cannot enable a
construction. It is intended to identify which productive forms can be
handled safely and where additional morphology models/resources are needed.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_morphology.py' -v
python -m tools.phase6_external_pud_v0_4.morphology
```
