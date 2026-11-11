# Phase 5 Lexical Foundation v0.6.0 — Contextual POS Candidate Ranking

## Purpose

Add an advisory contextual lexical component that ranks already-existing lexical candidates using local grammatical evidence. The component is separate from the base lexical analyzer and does not rewrite its output.

## Supported context cues

The initial bounded rules are:

- A determiner immediately before an ambiguous token supports a noun candidate.
- An adjective immediately before an ambiguous token supports a noun candidate.
- A nominal subject (pronoun, proper noun, or noun) immediately before an ambiguous token supports a verb candidate.
- A nominal object immediately after an ambiguous token supports a transitive verb candidate.
- A verb immediately after an ambiguous token supports a subject-noun candidate.

The ranker uses only candidate POS labels already present in the lexical analysis. It does not create a missing lexical entry, infer a new sense, or convert an unresolved word into a resolved one.

## Ambiguity and evidence policy

- Scores and evidence labels are retained for every candidate.
- A candidate is selected only when it has positive contextual evidence and beats the next candidate by the configured minimum score margin.
- Equal-scoring candidates remain ambiguous.
- Two senses with the same POS remain ambiguous unless a future sense-level evidence model is added.
- Context is restricted to the same segmented clause; evidence never leaks across sentence/clause boundaries.
- The ranker validates that lexical and segmentation artifacts refer to the exact same source snapshot.

The result is advisory and is not yet consumed by syntax or semantic composition. This prevents a new heuristic from silently changing existing pipeline decisions before independent evaluation.

## Validation

The test suite checks determiner-to-noun ranking, pronoun/object-to-verb ranking, preservation of polysemy, unknown-word abstention, clause-local context boundaries, and source-artifact integrity.

## Limitations

This is a small deterministic POS candidate ranker, not a full POS tagger, contextual word-sense disambiguator, dependency parser, or language model. It has not been evaluated on a representative held-out corpus. The rules should not be promoted into the core pipeline until external annotated evaluation establishes precision, recall, and safe abstention rates.
