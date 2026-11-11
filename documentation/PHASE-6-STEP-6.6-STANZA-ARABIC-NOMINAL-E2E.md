# Phase 6 Step 6.6 — Stanza Arabic Parser-to-USG Nominal Evaluation v0.1

**Status:** research-only parser diagnostic; candidate-only USG output; not Step 6.6 acceptance.

## Purpose

The dependency-driven nominal adapter already works with Arabic gold UD
syntax. This experiment tests a real Arabic dependency parser before passing
its predicted graph into the same adapter.

## Model

- Stanza 1.15.0.
- Arabic PADT no-character-language-model POS and dependency parser.
- Resource manifest pinned to 1.15.0; model files are checksum-verified by
  Stanza during download.
- PUD gold tokenization is supplied to isolate POS/dependency parsing from
  tokenization and multiword-token segmentation.

## Licensing restriction

The Stanza software and published model package are Apache-2.0, but the
selected parser is trained on UD Arabic-PADT, whose treebank license is
CC BY-NC-SA 3.0. This experiment is therefore research-only. Do not bundle,
redistribute, or integrate these weights into a commercial USG product unless
the training-data/model rights are separately cleared. No model weights or
treebank text are committed to this repository.

## Evaluation

The run reports POS accuracy, UAS, content-word POS/UAS, root attachment,
source-span alignment, and nominal candidate precision/recall/F1 against
candidate structures projected from Arabic PUD gold dependencies.

## Interpretation limits

- PUD is not used for training or fine-tuning.
- Gold PUD tokenization is supplied, so tokenizer/MWT quality is not measured.
- The gold candidate reference is a UD syntactic projection, not independent
  semantic-role adjudication.
- All USG outputs remain candidate-only; unmarked nmod alternatives remain
  ambiguous.
- The non-commercial PADT license prevents treating this as a deployable
  commercial component.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_stanza_arabic_nominal_e2e.py' -v
python -m tools.phase6_stanza_nominal_e2e_v0_1.evaluation
```
