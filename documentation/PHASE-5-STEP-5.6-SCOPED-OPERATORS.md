# Phase 5 — Step 5.6: Scoped Operators and Grammatical Features

**Status:** IMPLEMENTED CANDIDATE — acceptance pending CI  
**Operator analyzer:** `operator-scope-analysis/0.1.0`  
**Semantic composer:** `semantic-composition/0.2.0`  
**Operator inventory:** `usg-en-ar-scope-operators@0.1.0`  
**Expanded lexical resource:** `usg-en-ar-operator-lexicon@0.2.0`

## 1. Scope

This step adds a closed, explicitly registered inventory for negation, modality, tense, aspect, and quantification in the currently supported English and MSA Arabic construction profile. It does not claim general grammatical-feature recognition.

## 2. Registered operator families

- **Negation:** English `not`; MSA Arabic `لا`, `لم`, `لن`.
- **Modality:** English `may` (possibility) and `must` (necessity).
- **Tense:** English `will` and MSA Arabic `سوف` (future).
- **Aspect:** English `has` + a registered past participle (perfect).
- **Quantification:** English `every`, `some`; MSA Arabic `كل`, `بعض`.
- **Auxiliary support:** English `does` is recognized only as a non-semantic do-support token so that negation can be scoped without treating the auxiliary as the predicate.

The v0.2.0 lexical resource adds the minimal registered entries needed for these examples, including English `student`/`written` and MSA Arabic imperfect verb forms. The earlier v0.1.0 lexical resource remains immutable.

## 3. Scope attachment

Predicate operators attach only to the nearest following registered VERB in the same clause. Quantifiers attach only to the nearest following registered nominal argument. The English perfect operator requires a following verb candidate explicitly marked `VerbForm=Participle`. An operator without a valid target remains INCOMPLETE; it is never silently ignored.

The syntax analyzer filters only operator tokens that the operator analyzer has explicitly recognized, and it verifies the operator artifact's source ID and digest. The semantic composer emits typed `OPERATOR` nodes with an operand pointing to the scoped proposition, a `scopeTargetRef`, operator type/value, exact operator span, target span, and derivation references.

## 4. Multiple operators and ambiguity

When more than one semantic operator targets a clause, all bounded surface-order permutations are retained as distinct scope alternatives (up to the configured operator budget). For example, `may not` is not forced into one reading: both nesting orders are retained. The result is AMBIGUOUS until a later, independently justified rule can disambiguate it.

## 5. Acceptance tests

Tests cover English negation, modality, future tense, perfect aspect, universal quantification, Arabic negation/future/quantification, ambiguous multi-operator scope, invalid scope targets, source identity, and unchanged plain-clause composition. The expression-graph schema admits OPERATOR nodes and graph integrity checks require scope references to resolve to existing nodes. Phase 4 and Phase 5 Steps 5.2–5.5 regressions must pass.

## 6. Explicit limitations

This is a small operator inventory. It does not implement unrestricted tense/aspect morphology, all English auxiliaries, Arabic root-pattern morphology, all modal particles, quantifier raising, scope across arbitrary clause boundaries, or truth-conditional quantifier logic. The output is an explicit operator/scope representation, not a proof of the sentence's truth.
