# Phase 6 — Step 6.5: Expanded Predicate and Argument Structures

**Status:** IMPLEMENTED — benchmark acceptance pending  
**Contract:** `USG-INTERPRET/0.3.0`  
**Corrected gold:** `USG-INTERPRET-GOLD/0.3.1`  
**Construction resource:** `phase6.predicate-argument-rules.candidate/0.3.0`

## Scope

Implement bounded, deterministic frame selection and participant-role binding for four predicate families in English and MSA Arabic: intransitive events, ditransitive transfer, copular property predication, and prepositional/location relations. Each rule is explicit, versioned, source-grounded, and linked to a candidate frame and lexical sense. The analyzer emits participant bindings, exact source spans, predicate-head spans, grammatical-marker spans, frame identity, and derivation rule references.

The initial patterns are deliberately narrow and fixture-aligned:
- English: subject–predicate; subject–transfer predicate–recipient–determiner–theme; entity–copula–adjective; entity–spatial predicate–preposition–location phrase.
- MSA Arabic: verb–agent; transfer verb–agent–recipient–theme; verbless entity–attribute predication; spatial verb–entity–preposition–location.

The rules require lexical category and sense evidence in addition to token order. Multiple lexical senses are retained; construction context may license one candidate only when the complete pattern matches. Zero or multiple matches produce abstention or ambiguity.

## Acceptance

The analyzer is evaluated against all 400 corrected v0.3.1 fixtures. Each of the eight language/construction profiles must independently meet the frozen thresholds for precision, recall, participant roles, participant spans, predicate spans, grammatical markers, negative abstention, and ambiguity abstention. A successful unit test alone does not enable a broader grammar.

## Limits

This is not unrestricted syntax. It does not support arbitrary clauses, auxiliaries, passive voice, tense variation beyond listed forms, clausal coordination, free word order, general Arabic morphology, or unseen predicate vocabulary. These are out of scope for Step 6.5 and remain disabled.
