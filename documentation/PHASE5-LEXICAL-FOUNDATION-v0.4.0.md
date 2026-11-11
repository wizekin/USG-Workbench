# Phase 5 Lexical Foundation v0.4.0

## Purpose

Add a reusable English starter lexicon to the existing Phase 5 lexical analyzer without replacing the existing English/MSA Arabic discourse resource. The starter resource covers selected function words, pronouns, common grammatical forms, general vocabulary, introductory science vocabulary, and conservative suffix-based morphology.

This is a bounded, project-authored starter resource. It is **not** a complete English dictionary, a statistical tagger, or evidence of open-world language understanding.

## Resource architecture

- `usg-en-ar-discourse-lexicon@0.3.0`: existing cumulative project resource; retained unchanged.
- `usg-en-core-starter-lexicon@0.4.0`: new English resource with 165 explicit entries and seven morphology rules.
- `usg-en-ar-composite-lexicon@0.4.0`: deterministic runtime composition consumed by Phase 5.

Composition is deterministic. Exact duplicate entries and morphology rules are retained once. Conflicting records with the same lexical identity or rule ID cause an explicit error; the loader does not silently select a winner.

The Phase 5 lexical stage reports the composite resource ID/version and canonical composite-content digest. The new `resource_sha256_kind` field explicitly labels that digest as `canonical_composite_resource_content`. The resource catalogue separately reports SHA-256 values of the exact raw resource files. These are different digest domains and must not be compared as though they were hashes of identical bytes.

## Recognition behavior

- Exact lexical lookup is attempted first.
- Registered one-affix morphology rules are attempted only when exact lookup has no result.
- Multiple exact senses remain ambiguous; the analyzer does not force a single interpretation.
- Unknown words remain unresolved; no guessed lexical identity is emitted.
- Morphology decisions identify the rule ID used.

The current morphology implementation strips a registered prefix or suffix and looks up the remaining stem. It does not yet implement spelling alternations such as consonant doubling, silent-e deletion, or y-to-ies conversion. Those require explicit rule transformations and separate validation before being claimed as supported.

## Validation

The dedicated GitHub Actions workflow:

1. Validates the v0.4.0 JSON resource against the versioned lexical schema.
2. Compiles the Phase 5 interpreter package.
3. Runs controlled tests for function words, introductory science vocabulary, regular plural and selected suffix derivations.
4. Verifies ambiguity preservation and unknown-word handling.
5. Verifies the integrated Phase 5 service uses the composite resource and reports digest semantics.
6. Runs existing Phase 5 integrated API and packaged-resource regression tests.

## Scope boundary

This release improves coverage for selected English forms and makes the resource composition auditable. It does not claim high coverage of arbitrary English, full POS disambiguation, complete morphology, syntax completion, semantic composition success, or a passed open-world evaluation. Held-out corpora and independent gold annotations remain necessary for those claims.

## Scoped-operator interaction

The existing Phase 5 simple-transitive syntax patterns do not yet represent predicate or argument scope. If operator analysis resolves a semantic operator (for example negation, modality, tense/aspect, or quantification) in a clause, syntax conservatively withholds a bare simple-transitive assertion candidate for that clause. Auxiliary-only markers do not trigger this guard. This avoids deleting an operator token and then misreading the remaining words as an unmodified assertion. Full operator-aware syntactic/semantic composition remains a later integration task.
