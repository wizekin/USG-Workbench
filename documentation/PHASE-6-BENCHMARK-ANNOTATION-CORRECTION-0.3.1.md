# Phase 6 Benchmark Annotation Correction — v0.3.1

**Status:** Additive corrected gold profile; v0.3.0 remains immutable  
**Corpus:** `USG-INTERPRET-GOLD/0.3.1`  
**Purpose:** Separate semantic participant roles from predicate-head and grammatical-marker spans.

## Why this revision exists

The frozen v0.3.0 fixtures placed some `ACTION`, `RELATION`, and `COPULA` annotations inside `expected_roles`. Those spans are not semantic participant roles. Scoring them as roles would contaminate role accuracy and could incorrectly encourage predicate heads to be modeled as participants.

## Corrected annotation fields

- `expected_roles` and `expected_role_spans`: participant roles only.
- `expected_predicate_span`: the source-grounded predicate head for event/relation predicates, or null when the construction uses no overt predicate head.
- `expected_grammatical_markers`: separately evidenced grammatical markers such as an overt English copula.
- Non-positive and ambiguous fixtures retain no unique role graph, predicate span, or grammatical-marker gold assignment.

## Evaluation

The v0.3.1 evaluator separately measures participant-role accuracy, participant source-span accuracy, predicate-span accuracy, and grammatical-marker accuracy. Construction detection, negative abstention, ambiguity abstention, and false-unique counts remain separate. The 400 fixture texts and construction counts are retained; only annotation semantics and version identifiers change.

This revision is additive. It does not modify v0.3.0, Phase 5 corpora, semantic frame IDs, or runtime behavior. The correction is required before final Phase 6 role-accuracy acceptance.
