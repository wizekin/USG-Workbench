# Phase 6 Step 6.4 — spaCy English Morphology/POS Evaluation v0.7

**Status:** optional external baseline; not integrated into the USG runtime.

## Purpose

The rule-induced English morphology experiment improved lemma/POS candidate
recall by only 2.03 percentage points over its exact-form baseline. This
experiment measures an existing compact English pipeline as an external
reference for lemma and UPOS prediction.

## Model and licensing

- spaCy: 3.8.18.
- Pipeline: en_core_web_sm 3.8.0 (approximately 12 MB).
- Published model package license: MIT.
- Published training sources include OntoNotes 5 and WordNet 3.0. The
  benchmark does not redistribute training corpora.
- The model is installed only in the ephemeral CI runner and is not copied
  into USG resources or runtime distributions.

References:
- https://spacy.io/models/en
- https://spacy.io/usage/models
- https://huggingface.co/spacy/en_core_web_sm

## Evaluation method

- Use the pinned English PUD treebank and its gold sentence/token boundaries.
- Construct spaCy Docs from the PUD token sequence so the pipeline does not
  receive credit or incur errors from a different tokenizer.
- Run the pretrained pipeline without fine-tuning.
- Compare lemma, UPOS, and joint lemma+UPOS exact accuracy, including
  per-UPOS breakdowns.
- Preserve the source PUD snapshot and license metadata; do not store corpus
  text in the repository.

## Interpretation limits

This is an English-only baseline. The model's training-data overlap with PUD
is not claimed to be impossible. It produces one prediction per token and
does not expose candidate ambiguity. It does not evaluate semantic roles,
USG frames, or multilingual generalization.

No result from this experiment enables a USG construction or grants semantic
acceptance credit. Any future integration must remain an optional lexical/POS
provider and pass independent held-out evaluation.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_spacy_english.py' -v
python -m tools.phase6_external_pud_v0_7.spacy_english
```
