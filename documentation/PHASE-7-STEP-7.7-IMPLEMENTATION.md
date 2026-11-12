# Phase 7 Step 7.7 — Contextual Retrieval and Association Ranking

**Status:** implementation submitted for exact-head CI; acceptance is pending.  
**Policy:** `usg-knowledge-retrieval/0.1.0`  
**Output:** `USG-KNOWLEDGE-RETRIEVAL/0.1.0`

## Deliverables

- Deterministic retrieval across one or more `USG-KNOWLEDGE/0.1.0` bundles.
- Exact lexical-form and lemma matching, followed only by explicit record links to senses, mappings, and declared typed relations.
- Optional exact language-profile and typed-context filters.
- Explainable score components and stable ordering.
- Primary/secondary retrieval bands derived from lifecycle state; unresolved and candidate records remain secondary.
- Tie reporting that preserves ambiguity instead of forcing a unique result.
- Explicit output flags that scores are neither probabilities nor truth values and retrieval performs no inference.

## Ranking policy

The initial policy uses fixed ranking units for exact lexical forms, exact lemmas, explicitly linked senses, unresolved mapping targets, and directly connected relation endpoints. A declared language match and exact context match add deterministic ranking units. Lifecycle state affects ordering only; it does not alter the record's state or acceptance.

The score is not calibrated and must not be interpreted as probability, truth, confidence, entailment, or semantic correctness. No fuzzy string matching, translation inference, embedding matching, inverse relation, or transitive closure is performed.

## Acceptance tests

`python -m unittest discover -s tests -p 'test_phase7_knowledge_retrieval.py' -v`

The suite covers explicit language/domain filters, linked sense and mapping retrieval, unresolved candidate preservation, deterministic explanation, tie reporting, non-probabilistic scoring, and state filtering.

## Limitations

This implementation is a deterministic lexical-entry retrieval baseline, not general semantic search. It requires explicit links in the knowledge bundle and currently uses exact form/lemma matching. It does not yet implement fuzzy morphology, embeddings, query understanding, learned activation, or a calibrated ranking model. These remain future additions subject to separate evaluation.
