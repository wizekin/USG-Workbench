# Phase 6 — Step 6.4: Expanded Lexical and Morphology Resources

**Status:** CANDIDATE RESOURCE FOUNDATION — not runtime-enabled  
**Resource:** `phase6.lexicon.bilingual.candidate/0.3.0`  
**Schema:** `specifications/phase6-lexical-resource-0.3.0.schema.json`  
**Next gate:** Step 6.5 — expanded predicate and argument structures

## Scope

This step adds a bounded English/MSA Arabic lexical inventory grounded in the positive fixtures of the frozen `USG-INTERPRET-GOLD/0.3.0` corpus. Each entry records its language profile, surface form, lemma, part of speech, candidate sense link, features, candidate status, and one or more exact source fixture spans. The earlier Phase 5 lexical resource is not modified.

The resource separates lexical realizations from semantic participant roles. Predicate heads and grammatical markers may be lexical entries, but they are not semantic-role definitions. Lexical sense links remain candidates and do not by themselves select a frame. A surface form may have multiple sense-specific entries; the validator preserves rather than collapses these candidates.

## Morphology policy

Only two narrow, explicitly evidenced patterns are recorded:
- English finite present third-person singular `-s`, with listed fixture-observed forms.
- MSA Arabic attached definite article `ال-`, with listed fixture-observed nominal forms.

These are candidate recognition patterns, not productive generators. No unrestricted suffix stripping, Arabic root-pattern inference, clitic segmentation, transliteration, or unseen-form synthesis is enabled. A surface form not listed in the resource remains unknown until independently evidenced. Diacritics and Unicode code-point spans are preserved exactly.

## Validation

The validator checks schema conformance, unique lexical keys, language-profile agreement, exact source-slice equality, evidence fixture existence, morphology evidence language, and candidate-only status. The resource is deterministic JSON derived from the immutable corpus. It does not alter the frozen corpus or runtime behavior.

## Limitations

The inventory covers only lexical forms observed in positive benchmark fixtures. It does not constitute a general dictionary, morphological analyzer, or proof of lexical sense correctness. Some benchmark predicate annotations use legacy labels such as `ACTION`, `COPULA`, and `RELATION`; those are treated only as predicate/marker lexical evidence, not participant roles. The annotation correction remains an additive benchmark revision prerequisite before Step 6.14 scoring; v0.3.0 stays immutable.
