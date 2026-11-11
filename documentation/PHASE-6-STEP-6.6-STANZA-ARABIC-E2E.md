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

## Observed Arabic PUD results (2026-11-11)

The corrected end-to-end run evaluated all 1,000 Arabic PUD test sentences
with Stanza's pretrained Arabic PADT model. Gold and predicted graphs were
both parsed into the adapter-native graph format; an explicit test and
runtime guard reject an empty gold-candidate denominator.

| Measure | Result |
|---|---:|
| Predicted candidate hypotheses | 6,190 |
| Gold-UD candidate hypotheses | 6,685 |
| Structural edge precision | 76.74% |
| Structural edge recall | 71.05% |
| Structural edge F1 | 73.79% |
| Exact candidate + source-span precision | 76.74% |
| Exact candidate + source-span recall | 71.05% |
| Exact candidate + source-span F1 | 73.79% |
| Exact span agreement given a structural match | 100.00% |
| Token-span alignment failures | 16 |
| Parser token-count/form alignment failures | 0 sentences |

Per-construction exact candidate F1:

| Construction | F1 |
|---|---:|
| Attribute modifier | 83.97% |
| Genitive relation (unspecified semantics) | 74.01% |
| Nominal modifier (unspecified semantics) | 74.01% |
| Prepositional nominal modifier | 56.42% |
| Compound modifier | Not recovered (6 gold candidates) |
| Temporal adverbial | Not recovered (3 gold candidates) |

The parser produced candidate or ambiguous structures in 952 sentences and
abstained in 48. The weakest supported family is the prepositional nominal
modifier. Compound and temporal patterns were too sparse in this PUD-derived
inventory to produce a meaningful F1 score; neither was recovered by the
predicted parser graph.

**Decision:** retain this as a successful Arabic parser-plus-adapter
structural baseline. It does not validate semantic roles: the reference is
UD syntax projected through the same adapter, gold tokenization is supplied,
and genitive semantics remain unspecified. Do not enable constructions,
claim Arabic semantic acceptance, or unblock Step 6.7 from these numbers.

Report artifact:
[workflow run 42999574833](https://github.com/wizekin/USG-Workbench/actions/runs/42999574833).
