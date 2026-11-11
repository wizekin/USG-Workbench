# Phase 6 Step 6.6 — spaCy-to-USG Nominal End-to-End Evaluation v0.1

**Status:** candidate-only end-to-end structural evaluation; not semantic acceptance.

## Purpose

The UD nominal adapter works when supplied with gold dependency trees. This
experiment measures the errors introduced when the graph comes from a
pretrained English parser instead.

## Pipeline

1. Run en_core_web_sm 3.8.0 on PUD's gold pre-tokenized word sequence.
2. Normalize common spaCy/ClearNLP head conventions for prepositions and
   coordination into UD-style head arcs.
3. Map selected relation labels (including prep/pobj, poss, dobj, passive
   subject/auxiliary, and temporal npadvmod) into the UD labels consumed by
   the nominal adapter.
4. Run the same dependency-driven USG candidate adapter on predicted and gold
   graphs.
5. Compare construction, head/dependent token IDs, role spans, and marker
   spans; report structural precision/recall/F1 and exact-span agreement.

## Interpretation limits

The reference is the gold UD graph projected through the same adapter. This
measures parser-plus-adapter structural extraction, not semantic truth.
The spaCy-to-UD mapping is partial; no dependency LAS or semantic-role F1 is
claimed. PUD is a news/wiki evaluation set, and training-data overlap cannot
be ruled out. All outputs remain candidate-only.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_spacy_nominal_e2e.py' -v
python -m tools.phase6_spacy_nominal_e2e_v0_1.evaluation
```
