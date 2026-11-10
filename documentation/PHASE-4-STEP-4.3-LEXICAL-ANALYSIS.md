# Phase 4 — Step 4.3: Lexical and Morphological Analysis Contract

**Status:** ACCEPTED — included in bounded v0.1.0 demonstrator  
**Package:** `tools.usg_interpretation_v0_1_0`  
**Analyzer version:** `lexical-analysis/0.1.0`

## Deliverables

- Unicode-aware tokenization for the frozen English and Modern Standard Arabic profiles.
- Exact token surface text and zero-based, end-exclusive code-point spans.
- Versioned, injectable lexical resources with language-specific forms, lemmas, parts of speech, sense IDs, optional concept references, and morphology features.
- Explicit per-token statuses: `RESOLVED`, `AMBIGUOUS`, `UNRESOLVED`, and `NOT_APPLICABLE`.
- No inferred lemma, part of speech, sense, or concept for unknown words.

## Conservative behavior

- Whitespace remains untouched in the source and is not emitted as a token.
- Unicode letters and combining marks are retained together; numbers, punctuation, symbols, and other characters have distinct token kinds.
- English lexical lookup is case-folded. Arabic lookup is exact in this version; no source normalization or diacritic stripping is performed.
- Apostrophes surrounded by letters remain inside a token. Hyphens and Arabic clitic segmentation are not inferred.
- Morphology is supplied by explicit, versioned lexical entries. No suffix-stripping or statistical morphology is claimed.
- Multiple senses remain separate candidates; a unique dictionary hit is not evidence of real-world identity or truth.
- Multiword expressions are deferred to the semantic resource/association registry step.

## Tests

The Step 4.3 suite covers English and Arabic tokenization, exact spans, apostrophes, diacritics, Unicode symbols, punctuation, numbers, unknown words, ambiguous senses, morphology preservation, and duplicate resource identities.

## Limitations

This step does not perform syntactic parsing, semantic composition, coreference, or assertion generation. It does not claim comprehensive lexical coverage. Resource entries are explicitly curated/versioned data; missing entries remain unresolved.
