# Phase 5 — Step 5.3: Versioned Lexical and Morphology Resources

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Interpreter contract:** `USG-INTERPRET/0.2.0`  
**Lexical analysis:** `lexical-analysis/0.2.0`  
**Morphology rules:** `morphology-rules/0.1.0`  
**Bundled resource:** `usg-en-msa-foundation-lexicon@0.1.0`

## 1. Deliverable

Step 5.3 introduces a new versioned Python package, `tools/usg_interpretation_v0_2_0`, with immutable lexical entries, explicit morphology rules, a provenance-bearing bilingual resource, deterministic content digests, and conservative candidate generation.

The initial resource is project-authored for the benchmark's simple English SVO and MSA Arabic VSO examples. It is intentionally a small foundation lexicon, not a general-purpose dictionary or broad coverage claim. No third-party dictionary data is imported.

## 2. Resource contents

- English proper names, base verb lemmas, and nominal lemmas used by the 20 positive benchmark cases.
- English regular third-person singular `-s` and regular plural `-s` rules, applied only when the resulting stem is an explicitly registered lexical entry of the required part of speech.
- MSA Arabic verb and noun lemmas remain in Arabic script, with explicit past/third-person/masculine/singular verb features and native-script nominal lemmas.
- MSA Arabic nominal lemmas and a registered definite-article `ال` prefix rule that preserves the original source token span.
- Deliberately ambiguous senses for English `bank` and Arabic `عين`; these remain multiple candidates.
- Unknown words remain unresolved. No edit-distance, semantic similarity, language-model guess, or unconstrained suffix stripping is used.

## 3. Provenance and reproducibility

Every resource has an ID, semantic version, provenance statement, and deterministic SHA-256 digest over canonical JSON content. The manifest records the analyzer and morphology ruleset versions. Duplicate lexical identities and duplicate morphology rule IDs are rejected. Updating a resource requires a new version and digest; the old resource object remains immutable.

The bundled resource is authored in-repository for test fixtures. Its provenance does not imply external lexical authority or validated linguistic completeness.

## 4. Source compatibility

For this step only, v0.2 lexical analysis explicitly reuses the immutable `SourceSnapshot` and Unicode tokenizer from `tools/usg_interpretation_v0_1_0`. This reuses exact source offsets without changing or extending the Phase 4 pipeline. The new lexical result identifies its own v0.2 analyzer, resource version, and digest. A future v0.2 pipeline stage must retain this compatibility boundary through explicit tests.

## 5. Acceptance tests

- All 40 positive benchmark examples have lexical candidates for every word.
- English verb/noun inflections are derived only from registered base lemmas and explicit rules.
- Arabic definite-article forms retain exact surface text and source offsets.
- Ambiguous senses remain ambiguous; unknown and cross-language forms remain unresolved.
- Resource identity, provenance, digest stability, duplicate rejection, and exact Unicode span alignment are tested.
- The Phase 4 test suite remains unchanged and passes.

## 6. Explicit limits

This resource does not yet implement irregular English morphology, broad derivation, Arabic root-pattern analysis, clitic segmentation, dialects, transliteration, general named-entity recognition, or contextual word-sense disambiguation. No unsupported form is silently normalized into a known word.

## 7. Next step

Step 5.4 introduces v0.2 sentence-internal clause segmentation and richer syntactic candidates. It must consume the lexical candidates and preserve ambiguity rather than selecting a sense by frequency or rank alone.
