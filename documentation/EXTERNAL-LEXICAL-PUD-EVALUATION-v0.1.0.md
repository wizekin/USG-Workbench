# External Lexical Crawl — Independent PUD Evaluation v0.1.0

## Purpose

Measure how much of the independently annotated English PUD corpus is covered by the actual candidate lexical records produced by the scheduled external crawler. This is deliberately separate from the existing PUD experiments that build a POS dictionary from PUD training folds: here, the candidate inventory comes from the crawler's durable Wiktionary-derived shards, while the gold UPOS labels come from pinned PUD annotations.

## Method

1. Read all compressed JSONL shards in the checked-out `usg-external-lexical-data` branch.
2. Build a surface-form-to-UPOS-candidate index from each crawler entry's lemma and explicitly observed forms. No inflection is generated.
3. Map a conservative set of dictionary POS labels to UD UPOS labels.
4. Compare exact normalized forms with the English PUD test treebank, pinned by the existing v0.1 dataset commit and Git blob hash.
5. Report total and content-token coverage, OOV rate, gold UPOS candidate recall, ambiguity among covered forms, and per-UPOS metrics.

English forms are NFC-normalized and case-folded. The source shards remain untouched. PUD text is downloaded at evaluation time, hash-verified by the existing PUD loader, and is not persisted in the repository.

## Interpretation boundaries

- This measures lexical candidate coverage, not contextual POS tagging or semantic correctness.
- A gold POS tag appearing in a candidate set is not a disambiguated prediction.
- It does not measure precision, sense accuracy, morphology accuracy, or grammar performance.
- The crawler is still partial (602 processed headwords at the first accepted production run); low coverage is expected and must not be mistaken for final dictionary quality.
- No result can promote data into the active USG lexicon, syntax, semantics, or interpreter.
- The report is an evaluation snapshot tied to the current data-branch contents and PUD commit.

## Automation

Workflow: `.github/workflows/external-lexical-pud-evaluation.yml`

It runs after a successful crawler workflow completion or by manual dispatch. It checks out the main code and the separate lexical-data branch, runs unit tests, evaluates the current shard inventory, and uploads a JSON report artifact. Failed crawl runs do not trigger an evaluation.

## Run locally

```bash
python -m unittest discover -s tests -p 'test_external_lexical_pud_evaluation.py' -v
python -m tools.usg_external_lexical_v0_1_0.pud_evaluation --data-dir path/to/shards
```
