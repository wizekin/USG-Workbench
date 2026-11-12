# Phase 6 Step 6.6 — Independent Bilingual Semantic-Gold Acceptance Protocol

**Purpose:** establish a reproducible, auditable path to the missing independent semantic-gold gate.  
**Status:** protocol defined; no qualifying independent bilingual dataset is currently available in this repository.  
**Runtime status:** all ten Step 6.6 profiles remain candidate-only and disabled.

## 1. Why this gate exists

The current v0.4.0–v0.4.3 work is useful engineering evidence, but it does not constitute independent linguistic validation:

- v0.4.0–v0.4.2 fixtures are authored for the USG development work and include patterns used to derive the candidate lexicon.
- v0.4.3 held-out combinations exclude selected role-binding combinations, but reuse the same closed lexicon and programmatically generated examples.
- English/Arabic PUD, spaCy, Stanza, UD adapters, and morphology experiments provide syntactic or structural diagnostics. They do not independently annotate the five USG nominal/modifier semantic relations.
- SemEval-2007 Task 4, Pilot Arabic PropBank, and WojoodRelations have different annotation units, coverage, or access/licensing limitations. A source is not acceptable merely because its labels sound similar to USG labels.

These datasets may remain useful diagnostics. They must not be counted as independent gold unless a case-by-case mapping demonstrates equivalent annotation units and semantics.

## 2. Required ten-profile coverage

The acceptance set must cover every profile separately. No profile can borrow another profile's denominator or pass on an aggregate score.

| Language | Profile | Core distinctions |
|---|---|---|
| English | adjective modifier | adjective modifying a noun vs adjective predication |
| English | genitive/of relation | head/dependent identification without assuming ownership |
| English | noun compound | lexicalized compound vs independent noun sequence |
| English | prepositional nominal modifier | nominal vs clause attachment; complement vs relation |
| English | temporal/adverbial modifier | event, clause, and proposition scope |
| MSA Arabic | adjective modifier | noun/adjective agreement and adjective predication |
| MSA Arabic | iḍāfa/genitive | construct-state/genitive structure without assuming ownership |
| MSA Arabic | lexicalized compound | lexicalized compound vs productive iḍāfa |
| MSA Arabic | prepositional nominal modifier | head attachment and prepositional relation |
| MSA Arabic | temporal/adverbial modifier | event, clause, and proposition scope |

For **each** profile, require at least 20 positive, 20 negative/adversarial, and 10 ambiguous/boundary examples. The minimum complete set is therefore 500 examples (250 per language).

## 3. Independence requirements

A qualifying gold set must satisfy all of the following:

1. **External provenance:** the source dataset, release, source item identifiers, and acquisition method are pinned.
2. **Public-use rights:** the exact source text and annotations may be redistributed in this public repository and used in automated evaluation. A paper's publication license does not license its underlying dataset.
3. **Independent human annotation:** at least two annotators label each case independently before seeing one another's labels, the USG prediction, or the development fixture label.
4. **Adjudication:** disagreements are recorded and resolved by a separately identified adjudicator or a documented adjudication protocol. The original independent labels remain preserved.
5. **No model-generated gold:** LLM output, parser output, projected labels, synthetic examples, or USG candidate output may not be presented as human gold.
6. **No development leakage:** cases and labels are not copied from the Phase 6 development corpora or the candidate lexicon. Exact text/ID overlap is screened and reported.
7. **Annotation guideline:** the versioned guide defines annotation units, relation meanings, span boundaries, uncertainty, and negative/ambiguous labels before annotation begins.
8. **Reproducibility:** each case has a stable source reference, language profile, source span, annotation version, and provenance record.

If any requirement is unknown, the dataset is **not eligible** for the acceptance denominator.

## 4. Annotation rules

### 4.1 General

- Annotate the smallest complete phrase/construction needed to distinguish the target relation.
- Record exact Unicode code-point offsets against the exact source string; verify every span by slicing the source.
- Distinguish surface syntax from semantic interpretation. Do not infer ownership, authorship, kinship, location, instrument, or other relation from adjacency or a preposition alone.
- Use explicit `AMBIGUOUS` when two or more readings remain licensed by the source.
- Use `NEGATIVE` when the target construction is absent, even if another construction is present.
- Preserve alternative attachments and scopes rather than choosing the nearest noun or widest scope by default.

### 4.2 Adjective modifiers

Annotate the nominal head and adjective modifier separately. Include minimal pairs contrasting attributive adjectives (for example, “the blue notebook”) with predicative adjectives (“the notebook is blue”). In MSA Arabic, record observable gender, number, and definiteness agreement; do not invent unmarked morphology.

### 4.3 Genitive and possession

Record genitive head and dependent separately. Use `GENITIVE_UNSPECIFIED` unless independent lexical or construction evidence licenses a more specific relation. Genitive form alone does not entail ownership, authorship, kinship, control, or part-whole.

### 4.4 Noun compounds

Require evidence for a lexicalized compound reading. Keep a bare noun sequence or MSA iḍāfa ambiguous when compound and compositional genitive readings cannot be distinguished. Do not use the same form's presence in the USG candidate lexicon as gold evidence.

### 4.5 Prepositional nominal modifiers

Record the nominal head, preposition, complement, and attachment target independently. Use a generic prepositional-complement label unless the source and annotation guideline license a more specific semantic relation. Include minimal pairs where the phrase can attach to a noun or a clause.

### 4.6 Temporal and adverbial modifiers

Record the modifier span and the event/proposition it scopes over. Distinguish event-time, clause-time, and proposition-level scope. A temporal adverb's position alone does not determine scope.

## 5. Annotation and adjudication record

For each case, retain:

- source dataset/release/item ID and exact source text (only where redistribution is permitted);
- language profile, target construction, gold class, and exact span/role graph;
- independent annotation from annotator A and annotator B;
- disagreement categories and adjudicated result;
- guideline version, annotation timestamps, and provenance;
- source license/attribution information.

Annotator identifiers may be pseudonymous in the public manifest, but the project must retain a private audit trail sufficient to verify independence. Do not publish personal contact information.

## 6. Acceptance procedure

1. Pin candidate source datasets and verify their data-specific licenses and redistribution rights.
2. Freeze the annotation guide and manifest before annotators see model predictions.
3. Annotate the ten profiles independently; retain both raw annotations.
4. Adjudicate disagreements and calculate agreement per profile and label family.
5. Run the independent-gold manifest validator and the exact-span/leakage checks.
6. Freeze the resulting dataset revision and SHA-256 digest.
7. Evaluate the candidate interpreter without tuning on the held-out gold.
8. Publish per-language/per-profile denominators, precision, recall, exact role/span/attachment/scope accuracy, negative abstention, ambiguous abstention, false-unique rate, and confidence intervals where sample size permits.
9. Enable a construction only if it meets the Phase 6 roadmap gates independently for that language and profile.

A pass on one profile does not enable the other nine. A diagnostic-only dataset does not count toward this gate.

## 7. Current decision

**Step 6.6 remains blocked at independent semantic-gold acceptance.** The current candidate recognizer, lexical inventory, v0.4.2 development corpus, v0.4.3 combinatorial holdout, and external parser audits remain useful candidate/structural evidence. They do not satisfy independent human semantic-gold requirements.

This protocol makes the missing work executable and auditable; it does not fabricate the missing annotations or change any construction's disabled state.

## Related records

- [Step 6.6 definition and construction inventory](PHASE-6-STEP-6.6-NOMINAL-MODIFIER-SEMANTICS.md)
- [Independent dataset feasibility audit](PHASE-6-STEP-6.6-INDEPENDENT-GOLD-DATASET-AUDIT.md)
- [Held-out v0.4.3 evaluation](PHASE-6-STEP-6.6-HELDOUT-V0.4.3.md)
- [Phase 6 roadmap](PHASE-6-DEFINITIONS-ROADMAP.md)
