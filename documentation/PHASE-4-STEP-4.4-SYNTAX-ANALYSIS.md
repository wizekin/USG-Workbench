# Phase 4 — Step 4.4: Grammar and Syntactic Analysis

**Status:** ACCEPTED — included in bounded v0.1.0 demonstrator  
**Analyzer:** `syntax-analysis/0.1.0`

## Contract

- Grammar is an explicit, versioned registry of language-specific POS slot patterns and role bindings.
- The first deterministic analyzer matches complete word-token sequences only. Punctuation remains in lexical output and is not treated as a word slot.
- A unique matching pattern yields `PARSED`; multiple matches yield `AMBIGUOUS`; a fully known but unregistered shape yields `UNSUPPORTED`; unresolved lexical items yield `INCOMPLETE`.
- Every candidate retains token IDs and a source envelope. Grammatical roles are syntactic bindings, not semantic truth or event assertions.
- No grammar is guessed from a language model and no unknown lexical form is coerced into a POS category.

## Initial coverage

The initial registry contains a bounded English SVO pattern and Modern Standard Arabic SVO and VSO patterns. These are deliberately small fixture-grade patterns, not general parsers. Patterns are expanded only with explicit benchmark evidence.

## Tests and limitations

Tests cover English SVO, Arabic VSO, unknown words, unsupported shapes, and duplicate registry IDs. This step does not parse nested phrases, auxiliaries, agreement, coordination, subordinate clauses, or arbitrary word order. Such inputs remain unsupported/incomplete rather than receiving a guessed parse.
