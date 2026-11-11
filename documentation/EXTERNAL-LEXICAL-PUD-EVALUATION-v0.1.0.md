# External Lexical Crawl — Independent PUD Evaluation v0.2.0

## Purpose

Measure how much of the independently annotated English UD PUD corpus is covered by candidate lexical evidence produced by the scheduled external crawler. The lexical inventory comes from the crawler's durable Wiktionary-derived shards; gold forms, lemmas, and UPOS labels come from the pinned PUD test annotations.

## Method

1. Read every compressed JSONL shard in the checked-out `usg-external-lexical-data` branch.
2. Build separate indexes for dictionary lemmas, explicitly observed surface forms, and the combined surface-form-to-UPOS candidate inventory. No inflection is generated.
3. Map a conservative set of dictionary POS labels to UD UPOS labels.
4. Compare exact NFC-normalized, English case-folded surface forms and gold lemmas against the candidate indexes.
5. Report token coverage, OOV rate, POS candidate recall, ambiguity, lemma coverage, lemma-plus-UPOS candidate recall, and per-UPOS metrics.
6. Fail closed on missing shards, malformed JSON, invalid entry containers, and unreadable compressed shards.

PUD text is downloaded at evaluation time and verified against the pinned Git blob hash by the existing dataset loader. Source text and lexical shards are not copied into the report.

## Interpretation boundaries

- Surface-form coverage means an exact normalized form exists in the crawled candidate inventory.
- POS candidate recall means the gold UPOS is among the dictionary-derived candidates; it is not a contextual prediction.
- Lemma coverage means the exact normalized PUD gold lemma exists among crawled dictionary lemmas. It does not measure a lemmatizer's ability to infer lemmas from unseen forms.
- Lemma-plus-UPOS candidate recall requires both the gold lemma and gold UPOS to be present in the lemma index.
- Candidate ambiguity is described with candidate-count distributions and per-UPOS rates. The inventory has no ranking or contextual selection, so prediction precision is undefined and is explicitly not measured.
- The observed `plural`, `comparative`, and `superlative` source tags are conservatively mapped to `Number=Plur`, `Degree=Cmp`, and `Degree=Sup`, respectively, and evaluated against pinned PUD `FEATS`. Editorial tags such as `alternative`, `canonical`, `lowercase`, and `uppercase` are not treated as morphology.
- Morphology candidate-pool precision is the fraction of emitted mapped feature labels that match the gold token annotation; it is not contextual morphology prediction precision. Recall is measured over mapped gold feature instances only. Unmapped tags and unsupported features are excluded.
- The separate Phase 6 Step 6.4 PUD morphology cross-validation experiment is a training-fold-derived morphology baseline, not an evaluation of external crawler tags.
- The report does not measure morphology feature accuracy, contextual disambiguation, sense accuracy, or semantic correctness.
- The crawler remains partial. Low coverage is an inventory-coverage result, not a final judgment of dictionary quality.
- No result can promote data into the active USG lexicon, syntax, semantics, or interpreter.

## Automation

Workflow: `.github/workflows/external-lexical-pud-evaluation.yml`. A separate reproducibility gate validates pinned dataset identity, count/ratio invariants, ambiguity accounting, candidate-only boundaries, and morphology metric consistency before upload. These are report-integrity gates, not minimum lexical-quality thresholds.

It runs evaluator tests on pull requests. After evaluator changes are merged to `main`, it evaluates the latest durable lexical-data branch; it also evaluates after successful crawler runs and by manual dispatch. Non-PR runs upload a JSON artifact named `external-lexical-pud-evaluation`.

## Run locally

```bash
python -m unittest discover -s tests -p 'test_external_lexical_pud_evaluation.py' -v
python -m tools.usg_external_lexical_v0_1_0.pud_evaluation --data-dir path/to/shards
```
