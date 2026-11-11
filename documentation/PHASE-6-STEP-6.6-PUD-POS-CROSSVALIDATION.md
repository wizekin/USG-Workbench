# Phase 6 Step 6.6 — PUD POS Lexicon Cross-Validation v0.2

**Status:** diagnostic lexical-generalization experiment; not semantic acceptance.

The v0.1 external audit found that the existing closed candidate lexicon did
not cover any complete PUD structural phrase. This experiment tests whether
a generic, exact-form POS candidate inventory derived from the external corpus
could provide a better lexical starting point.

## Method

- Download the same pinned English and Arabic PUD snapshots, verifying Git blob
  SHA-1 values before use.
- Divide each language's 1,000 sentences deterministically into ten folds by
  a stable SHA-256 hash of each sentence ID.
- For each fold, build a form-to-UPOS candidate dictionary from the other nine
  folds and evaluate on the held-out fold.
- Report exact-form OOV rate, token coverage, candidate-set tag recall,
  ambiguity, and per-UPOS coverage.
- Do not persist source text or the derived lexical dictionary in the repository.

## Interpretation boundary

This experiment measures only whether a held-out token's gold UPOS tag is
among the tags observed for that exact surface form in the other folds. It is
not contextual disambiguation, a POS tagger, syntactic parsing, semantic-role
annotation, or a USG runtime capability. A high candidate-set hit rate would
justify a separate prototype, not automatic promotion of lexical senses.

PUD is released under CC BY-SA 3.0. Attribution belongs to the Universal
Dependencies PUD contributors; the pinned source repositories and licenses
are documented in the v0.1 audit report. The dataset is downloaded at test
time and not redistributed by this repository.

All constructions remain candidate-only. Step 6.6 remains unaccepted and
Step 6.7 remains blocked.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_crossval.py' -v
python -m tools.phase6_external_pud_v0_2.crossval
```

## Observed ten-fold run

Each language was evaluated across ten stable sentence-ID-hash folds. The
results below are lexical candidate-set measurements, not POS tagging accuracy.

| Measure | English PUD | Arabic PUD |
|---|---:|---:|
| Tokens | 21,180 | 20,747 |
| Exact-form token coverage | 82.6% | 75.5% |
| Content-token coverage (NOUN/PROPN/VERB/ADJ/ADV) | 66.2% | 57.5% |
| Gold UPOS included in candidate set, all tokens | 80.9% | 74.0% |
| Gold UPOS included, content tokens | 62.9% | 54.9% |
| Ambiguous candidate sets among seen tokens | 34.2% | 29.2% |

The conditional gold-tag inclusion rate among seen tokens was 97.9% for
English and 98.0% for Arabic. This is **not POS accuracy**: a token can have
multiple candidate tags, and the gold tag merely being one of them does not
disambiguate it. OOV and ambiguity rates remain substantial, especially for
content words.

This supports investigating a separate, context-sensitive POS candidate
module with explicit OOV and ambiguity handling. It does not justify using
the fold-derived dictionary as a production lexicon, and it does not solve
the semantic-role evaluation gap. The experiment receives no Step 6.6
acceptance credit. Step 6.7 remains blocked.

Report artifact:
[workflow run 42988191529](https://github.com/wizekin/USG-Workbench/actions/runs/42988191529).
