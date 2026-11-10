# Phase 4 — Step 4.5: Compositional Semantic Construction

**Status:** ACCEPTED — included in bounded v0.1.0 demonstrator  
**Composer:** `semantic-composition/0.1.0`

## Contract

- Semantic composition consumes an accepted lexical result and a unique registered syntax candidate.
- Predicate meanings are resolved only through a versioned semantic-frame registry keyed by language, lemma, and lexical sense ID.
- Argument slots become distinct `REF` / `TERM` nodes. The predicate becomes a `PREDICATE_APP` / `PROP` node whose ordered operands and explicit role bindings preserve argument structure.
- Each node retains the exact source token IDs and code-point span that licensed it.
- Multiple frame matches remain ambiguous. Missing frames are unsupported; unresolved syntax/lexical input remains unresolved.
- The registry maps explicit semantic IDs; it does not create canonical definitions or assert that a described event occurred.

## Initial coverage

The first registry contains only the fixture-backed English `write` and MSA Arabic `كتب` frames with subject/object roles. It is a compositional proof of concept, not a broad verb lexicon or complete USG document builder.

## Tests and limitations

Tests cover English SVO and Arabic VSO role ordering, typed node sorts/operators, provenance, missing-frame abstention, and unknown-word abstention. Nested operator scope, tense/aspect, negation, modality, quantification, coordination, and multiword predicates remain disabled until dedicated grammar/frame fixtures are implemented.
