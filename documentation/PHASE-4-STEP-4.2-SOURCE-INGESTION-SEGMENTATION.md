# Phase 4 — Step 4.2: Source Ingestion and Span-Preserving Segmentation

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Package:** `tools.usg_interpretation_v0_1_0`  
**Pipeline contract:** `USG-INTERPRET/0.1.0`  
**Segmentation version:** `source-segmentation/0.1.0`

## Deliverables

- Immutable `SourceSnapshot` with caller-supplied or generated opaque source ID, declared `en`/`ar` profile, exact UTF-8 SHA-256 digest, and unchanged source string.
- Ordered, nested paragraph, sentence, and conservative clause-candidate spans.
- Zero-based, end-exclusive Python Unicode code-point offsets, matching USG-SEM/1.0.
- Parent references from sentence to paragraph and clause to sentence.
- Pure standard-library implementation; no network, model, or database dependency.

## Segmentation policy

- Blank lines delimit paragraph candidates; single line breaks remain within a paragraph.
- Sentence boundaries use terminal punctuation from the first profile's English/Arabic set. Punctuation and closing quotation/bracket characters remain attached to the preceding sentence.
- Unpunctuated fragments are retained as sentence candidates.
- Clause candidates split only at explicit semicolon-family separators. Commas and conjunctions are not guessed as clause boundaries.
- Boundary segmentation is deliberately conservative. It does not establish syntactic correctness or semantic interpretation.
- Whitespace outside a segment's trimmed boundaries remains in the immutable source snapshot; no source character is deleted or rewritten.

## Tests

The Step 4.2 suite covers exact source/hash preservation, language validation, tamper detection, empty input, CRLF/LF, tabs, punctuation, combining marks, supplementary Unicode characters, Arabic text, fragments, exact span slicing, and parent-link integrity.

## Limitations

This step does not tokenize, lemmatize, parse syntax, or create USG-SEM expressions. It does not yet persist source snapshots in SQLite or expose an HTTP endpoint; those are integrated later through the versioned interpretation application. Sentence boundaries are deterministic candidates, not a claim to resolve abbreviations or every language-specific punctuation convention.
