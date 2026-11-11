# Phase 5 — Step 5.4: Clause Segmentation and Richer Syntax

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Contract:** `USG-INTERPRET/0.2.0`  
**Segmentation:** `document-clause-segmentation/0.2.0`  
**Syntax:** `syntax-analysis/0.2.0`

## 1. Deliverables

- Exact source-preserving sentence and clause segments.
- Explicit clause-boundary records for registered English and MSA Arabic connectives and semicolon-family separators.
- Verb-evidence gating for connective boundaries, reducing false splits inside nominal coordination.
- Clause-level syntax candidates for English SVO and MSA Arabic VSO/SVO.
- Named AGENT/ACTION/PATIENT token-role references and lexical sense references.
- Explicit RESOLVED, AMBIGUOUS, INCOMPLETE, UNSUPPORTED, and resource-limit outcomes.

## 2. Conservative segmentation policy

Sentence boundaries use explicit sentence punctuation. Clause boundaries are introduced only for registered markers (English and/or/but/because/if/when/that/then; MSA Arabic ثم/إذا/لأن/أن) when both sides contain lexically supported verbs, or for explicit semicolon-family separators with content on both sides. A marker is preserved as a separate boundary record with its exact source span and relation label. This is not a complete clause grammar; unregistered connectives and Arabic clitic conjunctions are not guessed.

## 3. Syntax candidate policy

The initial syntax patterns are:
- English: nominal/proper subject + verb + nominal/proper object (SVO).
- MSA Arabic: verb + nominal/proper subject + nominal/proper object (VSO).
- MSA Arabic: nominal/proper subject + verb + nominal/proper object (SVO).

All lexical sense combinations licensed by a pattern are retained. Syntax candidates identify role token references and lexical sense references; they do not create semantic truth or choose among alternatives. Unknown tokens produce INCOMPLETE; known but unregistered structures produce UNSUPPORTED; candidate-budget exhaustion produces INCOMPLETE_RESOURCE_LIMIT.

## 4. Acceptance

Tests cover exact spans, sentence boundaries, English coordination/subordination, Arabic temporal sequencing, semicolon segmentation, SVO/VSO patterns, lexical ambiguity, unknown-token abstention, unsupported word order, candidate budgets, and cross-source artifact rejection. Phase 4 and Phase 5 Steps 5.2–5.3 regressions must pass.

## 5. Explicit limitations

This step does not implement a general dependency parser, unrestricted nested clause grammar, Arabic clitic segmentation, arbitrary modifier attachment, or full syntactic disambiguation. The clause splitter is deterministic and intentionally bounded. Step 5.5 will compose accepted clause structures into nested semantic expressions without flattening them.
