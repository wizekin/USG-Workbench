# Phase 6 Step 6.4 — spaCy English Dependency Evaluation v0.8

**Status:** optional external syntactic baseline; not integrated into USG runtime.

## Purpose

The spaCy English pipeline already supplies a dependency parse in addition to
lemma and UPOS predictions. This experiment measures unlabeled head attachment
against the pinned English PUD treebank.

## Method

- Preserve PUD's gold tokenization by constructing pre-tokenized spaCy Docs.
- Run en_core_web_sm 3.8.0 without PUD fine-tuning.
- Compare predicted head token indices with PUD HEAD indices.
- Report UAS overall, excluding punctuation, on content words, by UPOS, by
  gold dependency relation, and for root attachments.
- Do not score raw dependency relation labels as LAS: spaCy's ClearNLP-derived
  relation scheme is not the Universal Dependencies relation inventory.

## Interpretation limits

UAS measures only whether the parser attached a token to the correct head. It
does not validate the relation label, semantic role, predicate-argument
structure, or USG semantic interpretation. A syntactic dependency tree is not
a semantic graph.

The model's published training sources include OntoNotes 5; training-data
overlap with PUD is not claimed to be impossible. The model package is MIT
licensed, but it remains an optional benchmark dependency, not a required
runtime component.

No semantic acceptance credit or construction promotion is permitted.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_spacy_dependencies.py' -v
python -m tools.phase6_external_pud_v0_8.spacy_dependencies
```
