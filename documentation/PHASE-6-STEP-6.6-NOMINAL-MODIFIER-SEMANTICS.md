# Phase 6 — Step 6.6: Nominal, Property, Possession, and Modifier Semantics

**Status:** ACCEPTED FOR BOUNDED AUTOMATIC SYNTHETIC-REFERENCE SCOPE — all ten profile gates pass; naturalistic validation is not claimed  
**Contract:** `USG-INTERPRET/0.3.0`  
**Candidate inventory:** `phase6.nominal-modifier-rules.candidate/0.3.0`

## 1. Purpose

Extend semantic interpretation from predicate arguments to noun-centered structure and modifiers. A nominal head, property, possessor, compound component, prepositional complement, and temporal/adverbial modifier must remain distinct nodes/relations with independent source spans and derivations.

## 2. Five construction families

The candidate inventory defines five families for each language (ten profiles total):

1. **Adjective modifiers** — English determiner/adjective/noun and MSA Arabic noun/adjective patterns. Arabic agreement in gender, number, and definiteness is evidence when observable. Do not confuse an adjective modifying a noun with an adjective serving as a copular predicate.
2. **Possession** — English licensed `of` possession and MSA Arabic `iḍāfa` with construct-state/genitive evidence. A preposition or adjacent noun alone does not prove ownership, control, kinship, or any specific possessive relation.
3. **Noun compounds** — English noun–noun compounds and MSA Arabic lexicalized compound senses. A bare Arabic `iḍāfa` must not automatically be treated as a lexicalized compound; possession and lexicalized compounds remain alternatives unless lexical evidence distinguishes them.
4. **Prepositional nominal modifiers** — prepositional phrases attached to a nominal head. The head, preposition, complement, and relation are separate. Attachment to a noun versus a clause must remain ambiguous when the source does not license a unique choice.
5. **Temporal/adverbial modifiers** — event-linked temporal or selected adverbial modifiers. The event frame and time/manner value remain separate; scope over an event, clause, or proposition must be explicit.

## 3. Semantic representation

The initial candidate role/relation labels are `HEAD`, `MODIFIER`, `COMPOUND_MODIFIER`, `POSSESSOR`, `POSSESSED`, `ATTRIBUTE`, `LOCATION`, `TIME`, and `MANNER`. These are typed semantic relations, not surface positions. Frame and role IDs must resolve through versioned registries. Modifier scope and attachment target are first-class graph links.

## 4. Evidence and ambiguity rules

- Every head and modifier has an exact Unicode code-point source span.
- Every relation cites the lexical sense, construction rule, agreement/case evidence where applicable, and source spans that license it.
- Arabic case endings, diacritics, construct-state evidence, and definiteness/agreement are preserved when present; unvocalized text must not be treated as if unobserved case morphology were visible.
- Repeated identical words are distinct mentions when their source offsets differ.
- Possession does not imply real-world ownership or identity.
- A noun–noun sequence is not automatically a compound or possession.
- A prepositional phrase is not attached to the nearest noun by default.
- A temporal adverb is not automatically scoped over the entire sentence.
- If competing head, attachment, or scope analyses remain, preserve alternatives or abstain.

## 5. Benchmark gate

Before implementation is advertised, freeze a new additive Phase 6 benchmark revision with at least 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary fixtures for each of the ten language/construction profiles. Include minimal pairs for adjective predication versus modification, possessive versus lexicalized compound readings, noun versus clause attachment, and event versus proposition temporal scope. Require exact participant/head/modifier spans and independent attachment accuracy.

The existing v0.3.2 gold corpus and Phase 1–5 benchmarks remain immutable. No Step 6.6 construction is enabled by this definition PR.

## 6. Acceptance boundary

This PR accepts definitions and evidence requirements only. It does not add runtime parsing, mutate the Phase 6 frame registry, enable any construction, or integrate with the API/CLI/Kernel Lab. Those require the focused benchmark and implementation acceptance gates.


## Additive genitive semantics refinement

The v0.4.0 candidate benchmark used `POSSESSED`/`POSSESSOR` labels for all English *of*-phrases and MSA Arabic iḍāfa examples. Those forms do not uniquely entail ownership or a single semantic relation. The additive v0.4.1 benchmark therefore uses `GENITIVE_HEAD` and `GENITIVE_DEPENDENT` with `GENITIVE_UNSPECIFIED` semantics. Specific possession, authorship, part-whole, and other relations require independent lexical/construction evidence; they are not inferred from genitive form alone. See [the v0.4.1 refinement record](PHASE-6-STEP-6.6-BENCHMARK-V0.4.1.md).


## 7. Automatic-reference acceptance — 2026-11-12

Step 6.6 now has a deterministic, graph-first automatic reference benchmark. It replaces the previous human-annotation and external bilingual dataset dependency for the defined synthetic acceptance scope.

- Generator and evaluator: `tools/phase6_auto_reference_v1_0/`.
- Frozen profile inventory: 5 construction families in English and 5 in MSA Arabic.
- Per-profile cases: 20 positive, 20 negative, and 10 ambiguous/boundary cases; 500 total.
- Reference labels and exact code-point spans are derived from generated semantic graphs before sentence realization.
- No human annotations, model-produced labels, external corpus, development fixtures, or candidate lexicon are used to create the reference cases.
- Benchmark-only reference lexical data and generated benchmark artifacts use CC0-1.0.
- The evaluator measures construction detection, exact role bindings, exact spans, semantic relation candidates, negative abstention, and ambiguity preservation.

The current candidate recognizer passes all ten synthetic profile gates at 100% for each reported measure. Reproduce with:

```bash
python -m unittest discover -s tests -p 'test_phase6_auto_reference_v1_0.py' -v
python -m tools.phase6_auto_reference_v1_0.evaluate
```

See [the Automatic Synthetic Reference Protocol](PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md) and workflow `.github/workflows/phase6-step-6-6-automatic-reference.yml`.

**Acceptance boundary:** Step 6.6 is accepted only for the controlled synthetic reference domain. This result does not demonstrate naturalistic English/MSA semantic accuracy, unrestricted morphology, unseen lexical generalization, or broad attachment/scope competence. The generated cases and construction templates share an explicit design inventory, so this is deterministic conformance evidence, not independent human linguistic gold.

**Capability state:** all ten construction profiles remain `CANDIDATE_ONLY`; no runtime construction, active lexical resource, canonical `USG-SEM/1.0`, or Phase 1–5 behavior is promoted or mutated. Step 6.7 is unblocked for bounded candidate development only. Production promotion remains separately gated.
