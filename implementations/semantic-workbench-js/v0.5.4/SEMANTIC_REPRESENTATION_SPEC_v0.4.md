# USG Semantic Representation Specification v0.4.0

**Profile:** `USG-SR/0.4`  
**Record schema:** `USG-SEMANTIC-RECORD` / `0.4.0`  
**Status:** implemented prototype specification; not a complete natural-language semantics standard.

## 1. Purpose and boundary

USG-SR/0.4 defines a structured, inspectable representation for propositions expressed by a source text. It separates the proposition's arguments and predicate from polarity, tense, modality, quantification, conditions, discourse references, event attributes, evidence, provenance, and relations to other propositions.

A semantic record is a **candidate interpretation of a source**, not automatically a true fact. A source may assert an incorrect statement. A `CAUSE` relation with `attribution: "source_asserted"` records that the text presents one proposition as the reason for another; it does not establish objective causality. An exact evidence span verifies quotation alignment only, not entailment.

The local LLM is a proposal generator. USG normalization and validation add structure and warnings, but do not guarantee correctness. Human review remains mandatory before claims enter the accepted knowledge base.

## 2. Processing layers

1. **Source capture:** retain the exact sentence or discourse text.
2. **Candidate extraction:** local rules or a local LLM propose one or more propositions.
3. **Normalization:** normalize entity labels, predicate identifiers, polarity, tense, modality, nested propositions, references, and event attributes.
4. **Validation:** check structure, source alignment, missing roles, unresolved clauses, and scope conflicts.
5. **Review:** display candidate meaning, structure, evidence, warnings, and provenance. Nothing is silently accepted.
6. **Reasoning:** only explicitly supported rule inputs are used by the current inference engine; unsupported logical forms are stored but excluded from simple inference.

## 3. Top-level record

| Field | Meaning |
|---|---|
| `schema` | Constant `USG-SEMANTIC-RECORD`. |
| `schemaVersion` | Semantic record version `0.4.0`; independent of browser storage version. |
| `representationProfile` | Constant `USG-SR/0.4`. |
| `sourceText` | Original source text from which claims were proposed. |
| `claims` | Array of proposition candidates. |
| `entities` | Registry of normalized entities found in claims and nested propositions. |
| `mentions` | Surface mentions linked to canonical entity IDs; pronouns retain their surface form. |
| `claimRelations` | Relations between claims, including contradiction candidates. |
| `explanations` | Source-level explanation links, such as causal links. |
| `unresolved` / `warnings` | Unparsed or questionable content and explicit normalization warnings. |
| `validation` | Aggregate status and counts. `allClaimsRequireReview` is always true. |

The machine-readable contract is `schemas/usg-semantic-record-v0.4.schema.json` (JSON Schema Draft 2020-12).

## 4. Proposition and entity model

Each claim has a `subject`, `predicate`, and `object`. A subject and non-null object are entity records:

```json
{
  "text": "customer",
  "canonicalText": "customer",
  "surfaceText": "The customer",
  "type": "agent_or_topic",
  "reference": "definite",
  "entityId": "e_customer"
}
```

- `text` is the normalized display label.
- `canonicalText` is the stable canonical label used for matching.
- `surfaceText` preserves the source mention, including articles or pronouns where available.
- `type` is provisional; use `unknown` when the type is not established.
- `reference` is `definite`, `indefinite`, `unmarked`, `unknown`, or `resolved_pronoun`.
- `entityId` links mentions to the entity registry; null means no stable ID was assigned.

`object` may be null when the predicate is intransitive or the source omits an argument. Null must not be converted into the literal string `"null"` or `"[object Object]"`.

The prototype predicate vocabulary includes `SUBCLASS_OF`, `INSTANCE_OF`, `MEASURES`, `NEEDS`, `LIKE`, `DISLIKE`, `PART_OF`, `CAUSES`, `HAS_PROPERTY`, `DIFFER`, `CHANGE`, `INCREASE`, `STOP_USING`, `USES`, `BOUGHT`, and `FAILS`. This is an extensible vocabulary, not a closed ontology.

## 5. Polarity, tense, modality, and time

### 5.1 Polarity

`polarity` is `positive`, `negative`, or `unknown`. Predicate identity remains unchanged by negation. For example, “does not like” is `LIKE` with negative polarity; it is not a different positive predicate. “Does not dislike” is represented as `DISLIKE` with negative polarity and is **not** upgraded to positive `LIKE`.

### 5.2 Tense

Legacy-compatible `tense` is `past`, `present`, `future`, or `unknown`. Tense is assigned per clause where the source provides enough evidence. A future consequent must not overwrite the present grammatical tense of an IF antecedent.

### 5.3 Modality and scope

Legacy-compatible `modality` is one of `asserted`, `possible`, `necessary`, `obligatory`, `possible_or_ability`, or `unknown`. `modalScope` records the operator, force, scope, and source surface marker, for example:

```json
{"operator":"MIGHT","force":"possible","scope":"proposition","surfaceText":"might"}
```

A modal proposition is not an unqualified asserted fact. `must` may be ambiguous between necessity and obligation; the prototype flags this by using a descriptive force rather than pretending the distinction has been fully resolved.

### 5.4 Time frame

`time` supplements `tense` with `grammaticalTense`, `aspect`, `referenceTime`, `sourceTense`, `clauseEvidence`, and `temporalAdverbials`. Grammatical tense and temporal reference are kept distinct; when the source does not make reference time clear, it remains `unspecified` rather than being copied from tense. It is a lightweight representation, not a full temporal logic or event calculus. A change from “needed” (past) to “no longer needs” (present) is stored as two time-distinct claims, not as a same-time contradiction.

## 6. Quantifier scope

`quantifierScope` is a structured operator over a restrictor class and the claim proposition. The prototype recognizes two intentionally distinct forms:

- “Not every customer needs the tool” → `NOT(FORALL x: Customer(x) -> NEEDS(x, tool))`.
- “No customer needs the tool” → `FORALL x: Customer(x) -> NOT(NEEDS(x, tool))`.

The first does not entail that no customer needs the tool. The second says the negative predicate applies to each customer. Negation represented in `quantifierScope` is kept separate from the claim's lexical predicate polarity, avoiding double-negation artifacts from model output.

## 7. Conditions and nested propositions

A condition contains its own `proposition`, independent tense/modality/time, marker, scope, effect, consequence, evidence, and `logicalStatus`. If the condition has an exact source phrase, USG checks that phrase for an explicit modal operator and clause tense, correcting a model-proposed value when the source clearly disagrees. The conditional clause can use present grammatical tense while referring to a future situation; the two fields must not be conflated.

```json
{
  "marker": "if",
  "scope": "claim",
  "effect": "condition_for_assertion",
  "proposition": {
    "subject": {"text":"prices","canonicalText":"prices","surfaceText":"prices","type":"unknown","reference":"unmarked","entityId":"e_prices"},
    "predicate": "INCREASE",
    "object": null,
    "polarity": "positive",
    "tense": "present",
    "modality": "asserted"
  },
  "consequence": "The effect proposition applies only when the antecedent holds.",
  "logicalStatus": "conditional_not_asserted"
}
```

`conditional_not_asserted` means the antecedent is not represented as an observed fact merely because it appears in the condition. If an LLM supplies a malformed or serialized proposition, USG preserves the condition as unresolved and does not stringify an object into entity text.

`unless` is represented as an exception marker. The prototype does not invent the outcome in the exception case.

## 8. Discourse entities and mentions

`entities` stores canonical entity identities; `mentions` records surface mentions and their target IDs. A conservative resolver can connect “He” to an earlier subject and “it” to an earlier object in a narrow supported two-sentence purchase/use pattern, resolve “it” in the paired NEEDS pattern, and link “it” to “the tool” in the explicit stop-using/because-failure pattern. The resolver is applied to both local-rule and LLM-proposed claims.

This is not general anaphora resolution. Ambiguous pronouns, competing antecedents, broad discourse contexts, and most multi-sentence forms must remain unresolved or be reviewed. A mention's presence is not proof that the proposed antecedent is correct.

## 9. Event attributes

`eventAttributes` stores modifiers that belong to an event rather than an entity argument. For example, “uses it every day” stores frequency `every day` as an event attribute with normalized value `P1D` (one-day period). The prototype recognizes selected frequencies (`P1D`, `P1W`, `P1M`, `P1Y`). It does not yet implement full temporal interval arithmetic.

## 10. Comparison frames and completeness

A `DIFFER` proposition may be interpretable even when it lacks an explicit comparison reference. In that case:

```json
{"reference":null,"comparisonSet":null,"status":"context_dependent"}
```

The claim can remain sentence-level `complete`, while tasks such as pairwise comparison or difference calculation require the missing comparison reference. This prevents USG from conflating **sentence interpretation** with **task-specific data sufficiency**.

Other predicates may use `completeness.status` = `complete`, `underspecified`, `unresolved`, or `not_applicable`, with `missingRoles` and a note. Batch status accounts for unresolved content and genuinely underspecified required roles.

## 11. Relations between claims

`claimRelations` contains claim-to-claim links. In v0.4 the implemented relation is `CONTRADICTS` with status `candidate`. A candidate is generated only when subject, predicate, object, time frame (including temporal adverbials), modal operator, quantifier scope, event attributes, and semantic conditions match while polarity differs. Different time frames, operators, or frequency frames do not count as a direct contradiction. These are review cues, not a theorem prover and not a contradiction-resolution policy.

Causal links use `CAUSE` and `attribution: "source_asserted"`. This means the source presents a cause/effect explanation. It is not a claim that USG independently verified that causal relationship.

## 12. Evidence, provenance, and confidence

`evidence.quote` is the stored source span. `start` and `end` are offsets into `sourceText` using JavaScript string indexing. `verified: true` means the quote matches that exact source slice. `modelQuote` and `modelQuoteVerified` separately retain the model's proposed evidence quote and exact-match check. Neither field proves semantic entailment.

`provenance` distinguishes sources such as `local_llm_proposal`, `local_rule`, and `demo_seed`. `ruleId` identifies a rule when applicable. `confidence` is an informal numeric estimate and is not calibrated probability. `sourceKind` records the kind of source record.

## 13. Validation and review boundary

`validation.status` is:
- `candidate`: at least one claim exists and there are no known unresolved/underspecified components;
- `partial`: claims exist, but unresolved content or underspecified roles remain;
- `unresolved`: no usable claim was produced.

`allClaimsRequireReview: true` is mandatory. A validation status of `candidate` does not imply objective truth or semantic certainty.

## 14. Reasoning policy in v0.4

The current symbolic engine still implements only subclass transitivity and instance inheritance. It uses a conservative filter: only positive, asserted premises with an explicitly present temporal reference that are unconditional and non-quantified are eligible for those simple rules. Conditional, negative, modal, quantified, or temporal-change claims can be stored and inspected but are not fed into those rules. This intentionally limits inference rather than treating richer logical forms as plain facts.

## 15. Implemented coverage and known limitations

- The language coverage remains English and limited.
- Deterministic local patterns support a small set of sentence forms, including the ten advanced regression cases used during v0.4 development.
- The optional local LLM may still collapse clauses, misidentify scope, or resolve references incorrectly. USG normalization can catch only errors covered by explicit validation/source rules.
- Coreference support is narrow; the system is not a discourse parser.
- Quantifier support is limited to selected `not every` and `no` constructions; quantifier logic is not generally compositional.
- No complete ontology, predicate registry, event calculus, temporal logic, defeasible logic, or general-purpose theorem prover is included.
- Contradiction candidates are pairwise heuristics; they are not logical proofs or resolution outcomes.
- Confidence is not calibrated and no broad benchmark score is claimed.

## 16. Compatibility and versioning

The browser's saved knowledge-base storage remains on its existing internal `schemaVersion: 2` for compatibility. Exported semantic records use `schemaVersion: "0.4.0"`. Batch exports use `schemaVersion: "1.2"` and `semanticSchemaVersion: "0.4.0"`. A batch run does not silently accept claims into the knowledge base.
