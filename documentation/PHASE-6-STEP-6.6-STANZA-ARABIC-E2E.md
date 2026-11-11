# Phase 6 Step 6.6 — Stanza-to-USG Arabic Nominal End-to-End Evaluation v0.1

**Status:** candidate-only parser/adapter structural evaluation; not semantic acceptance.

## Purpose

The dependency-driven nominal adapter has been evaluated on gold English and
Arabic PUD dependency graphs. The English spaCy experiment measures parser
errors for English. This experiment adds an independent pretrained Arabic
parser and measures parser-plus-adapter extraction on Arabic PUD.

## Pipeline

1. Download the pinned Arabic PUD test file and verify its Git blob SHA-1.
2. Download Stanza 1.11.0's Arabic `padt` model using the pinned
   `stanza-resources` manifest commit. Stanza's model files are validated
   against the manifest's MD5 checksums.
3. Supply PUD's gold word segmentation to the parser. This intentionally
   isolates POS/dependency parsing and prevents tokenization errors from
   shifting token indices.
4. Predict UPOS tags and dependency heads/relations with the pretrained
   Arabic PADT pipeline.
5. Convert predictions to the dependency graph shape consumed by the
   language-neutral USG nominal adapter.
6. Run the adapter on predicted and gold graphs, then compare construction,
   head/dependent token IDs, role spans, and marker spans.

## Evaluation boundary

The gold reference is the external PUD dependency graph projected through
the same USG adapter. This measures parser-plus-adapter structural extraction,
not semantic truth or independent semantic-role annotation. The model is
trained on the Arabic PADT treebank and evaluated on Arabic PUD; source or
training-data overlap cannot be ruled out.

PUD gold tokenization is supplied to the parser, so this does not evaluate raw
text segmentation or Arabic clitic tokenization. Any parser token-count or
token-form mismatch causes that sentence's predicted graph to abstain rather
than comparing misaligned token IDs.

No Arabic lexicalized-compound semantic inference is added. Unmarked genitive
and nominal attachments remain governed by the existing ambiguity rules.
All outputs remain candidate-only; no construction is promoted or integrated
into the USG runtime.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_stanza_nominal_e2e.py' -v
python -m tools.phase6_stanza_nominal_e2e_v0_1.evaluation
```

The report is written to
`artifacts/phase6-step-6-6-stanza-arabic-nominal-e2e.json`. The source corpus
and model are downloaded into the ephemeral CI environment and are not
committed or bundled with USG.
