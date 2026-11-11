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
- Report raw UAS overall, excluding punctuation, on content words, by UPOS,
  by gold dependency relation, and for root attachments.
- Also report a limited UD-head-convention-normalized UAS after reattaching
  spaCy prep/agent + pobj/pcomp arcs and coordination cc arcs.
- Do not score dependency relation labels as LAS: spaCy's ClearNLP-derived
  relation scheme is not the Universal Dependencies relation inventory.

## Interpretation limits

UAS measures only whether the parser attached a token to the correct head. The
partial normalization handles two common head-convention differences but is
not a complete ClearNLP-to-UD conversion. Neither raw nor normalized UAS
validates dependency labels, semantic roles, predicate-argument structure, or
USG semantic interpretation. A syntactic dependency tree is not a semantic
graph.

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

## Observed English PUD results (2026-11-11)

The run evaluated 21,180 dependency-annotated tokens:

| Measure | Raw spaCy heads | Partial UD-head normalization |
|---|---:|---:|
| Overall UAS | 57.09% | 78.41% |
| Non-punctuation UAS | 57.42% | 81.52% |
| Content-word UAS | 61.42% | 78.38% |
| Root attachment accuracy | 76.70% | 76.70% |

The largest changes occur where the two treebank conventions differ:

| UPOS | Raw UAS | Normalized UAS |
|---|---:|---:|
| ADP | 4.50% | 89.59% |
| CCONJ | 5.04% | 79.13% |
| NOUN | 47.98% | 79.24% |
| PROPN | 42.72% | 65.42% |
| VERB | 78.11% | 82.02% |

The raw score substantially underestimates the parser because spaCy's
preposition/object and coordination head conventions differ from UD. The
limited conversion reattaches nominal objects to the governing predicate and
adpositions to their nominal, and attaches coordinating conjunctions to the
following conjunct. The normalized score is therefore a better structural
comparison, but it is still not LAS and is not a complete dependency-scheme
conversion.

**Decision:** the compact spaCy parser is a useful English syntax candidate
after explicit head-convention normalization. Before any runtime integration,
the same conversion must be tested on another independently annotated UD
English treebank, and a complete relation-label mapping must be specified.
This UAS result does not establish semantic roles or USG interpretation.

Report artifact:
[workflow run 42993728381](https://github.com/wizekin/USG-Workbench/actions/runs/42993728381).
