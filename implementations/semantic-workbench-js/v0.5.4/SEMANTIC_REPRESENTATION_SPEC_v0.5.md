# USG Semantic Representation Specification v0.5

**Profile:** `USG-SR/0.5`  
**Workbench release:** `0.5.0`  
**Status:** Experimental semantic-foundation implementation  
**Supersedes:** `USG-SR/0.4` for newly exported records; v0.4 remains a supported import/compatibility format.

## 1. Purpose and scope

USG-SR/0.5 defines a canonical, compositional representation for candidate meanings extracted from source text. Its principal change from v0.4 is the introduction of an explicit semantic expression graph. Operators and connectives point to the expressions they modify or combine. This makes semantic scope inspectable instead of leaving it distributed across unrelated claim fields.

The profile is designed to preserve a distinction between:

1. the source text;
2. an LLM or rule system's proposed interpretation;
3. USG's canonical normalized representation;
4. structural validation of that representation; and
5. any later human acceptance, knowledge storage, or inference.

A structurally valid representation is **not** proof that the interpretation is correct, that the source entails every represented element, or that an assertion is objectively true.

This specification describes the representational contract. It does not claim that the current English extraction heuristics recognize every construction defined here.

## 2. Design principles

### 2.1 Compositionality

Meaning is represented as atomic predications combined or modified by explicit operator and connective nodes. For example, `MIGHT(NOT(P))` is a graph with a modal node whose scope points to a negation node, whose scope points to a predication node.

### 2.2 Predicate identity is independent of polarity

Negation modifies a proposition; it does not automatically replace the proposition's predicate with an antonym.

- “The customer does not like the tool” is `NOT(LIKE(customer, tool))`.
- “The customer does not dislike the tool” is `NOT(DISLIKE(customer, tool))`.

Neither form is automatically equivalent to the positive form of the opposite predicate.

### 2.3 Scope is explicit

Negation, modality, quantification, and subordinate-clause relations must identify the expression within their scope. The order of nested nodes is meaningful and must not be flattened.

### 2.4 Source assertion is not objective truth

The model records what a source states, proposes, or embeds. Source attribution and evidence do not independently establish truth. The semantic model's acceptance boundary must remain:

```json
{
  "requiresHumanReview": true,
  "acceptedIntoKnowledgeBase": false,
  "objectiveTruthEstablished": false
}
```

### 2.5 Missing information remains missing

USG must not invent a generic predicate, entity, antecedent, comparison target, argument, or connective just to make a record appear complete. The missing or unsupported element is represented in `unresolvedItems` or in a proposition's `completeness` field.

### 2.6 Provenance is retained

Every expression can refer to its source claim, method, rule, evidence, and source kind. A later system can therefore distinguish an LLM proposal from a local rule result or a user-provided record.

## 3. Top-level semantic record

A v0.5 semantic record retains the v0.4-compatible fields and adds a mandatory canonical model and its validation result:

```json
{
  "schema": "USG-SEMANTIC-RECORD",
  "schemaVersion": "0.5.0",
  "representationProfile": "USG-SR/0.5",
  "sourceText": "The customer might not need the tool.",
  "claims": [],
  "semanticModel": {},
  "semanticValidation": {}
}
```

`claims` is the compatibility/proposal view used by existing Workbench features. `semanticModel` is the canonical compositional view. New v0.5 consumers should prefer `semanticModel` for scope-aware operations and use `claims` for compatibility, display, and migration until those older views are retired.

## 4. Canonical semantic model

The canonical model contains:

| Field | Purpose |
|---|---|
| `profile` | Must be `USG-SR/0.5`. |
| `version` | Must be `0.5.0`. |
| `canonical` | Indicates this is the canonical semantic graph. |
| `compatibilityView` | Identifies `record.claims` as the compatibility projection. |
| `source` | Original text, language tag, and optional source ID. |
| `entities` | Provisional concept/entity registry for this semantic record. |
| `mentions` | Source-level expressions referring to entities, including pronouns. |
| `evidence` | Exact source spans cited by expressions, operators, connectives, or relations. |
| `expressions` | Predications, operators, and connectives forming the semantic graph. |
| `relations` | Typed links between expression roots, such as source-attributed causation or candidate contradiction. |
| `rootExpressionIds` | Entry points for the sentence's independent proposition or connected construction. |
| `unresolvedItems` | Structured record of unsupported, ambiguous, or missing content. |
| `acceptanceBoundary` | Human-review and truth-establishment safeguards. |
| `buildNotes` | Non-fatal notes from canonical graph construction. |

### 4.1 Entities

An entity represents a participant, concept, class, artifact, event, property, or other referent.

Required fields:

- `id`: identifier within the current semantic graph;
- `canonicalText`: normalized label used by this graph;
- `type`: provisional semantic type;
- `aliases`: source forms linked to this graph entity;
- `identityStatus`: currently `provisional` for automatically built entities unless a trusted review process explicitly establishes a different status.

Entity IDs created by the current builder are graph-local identifiers. They are not proof of identity across documents. Identical normalized labels may be grouped within a graph, but polysemy, homonymy, and cross-document identity require a separate resolution process.

An unresolved pronoun is not created as a new entity merely because its surface form is “it”, “he”, or another pronoun. It remains a mention with a null `entityId` and `resolutionStatus: unresolved` until an antecedent is supported.

### 4.2 Mentions

A mention preserves a source expression and its proposed entity link:

- `id`;
- `entityId` (nullable);
- `surfaceText`;
- `mentionType` (for example, noun phrase or pronoun);
- `resolutionStatus` (`linked`, `resolved`, or `unresolved`);
- `antecedentEntityId` (nullable);
- `sourceSpan` (nullable).

Separate occurrences should remain separate mentions when the source provides separate occurrences. Mention identity is not the same as entity identity.

### 4.3 Evidence

Evidence stores:

- `id`;
- `sourceText`;
- `quote`;
- `start` and `end` offsets;
- `exactSourceMatch`;
- optional model-quote information;
- `verificationMeaning`.

Offsets are zero-based, half-open JavaScript string offsets: `[start, end)`. In the current JavaScript implementation they follow JavaScript string indexing (UTF-16 code units).

`exactSourceMatch: true` means only that the quote matches the source substring at the supplied offsets. It does **not** prove semantic entailment, factual correctness, or that the evidence supports every field in the associated proposition.

### 4.4 Expressions

`expressions` is a graph-node array with three principal node types: `PREDICATION`, `OPERATOR`, and `CONNECTIVE`.

#### 4.4.1 PREDICATION

A predication represents a relation or state involving arguments.

Core fields:

- `id`;
- `type: PREDICATION`;
- `predicate`;
- `arguments`;
- `argumentRequirements`;
- `grammaticalTense`;
- `aspect`;
- `temporalFrame`;
- `eventFrame`;
- `attribution`;
- `provenance`;
- `completeness`;
- `evidenceRefs`;
- `sourceClaimId`.

Argument roles currently include `subject`, `object`, `agent`, `patient`, `instrument`, `recipient`, `location`, `time`, and `other`. A role points to an entity and/or a mention. Quantified argument bindings can additionally include `variableId` and `bindingEntityId`.

`argumentRequirements` identifies the roles required by the current predicate-frame registry and any missing roles. The initial registry is intentionally limited. It currently treats NEEDS, LIKE, DISLIKE, BUY/BOUGHT/PURCHASE/PURCHASED, USE/USES/USED, STOP_USING, and MEASURE/MEASURES as requiring subject and object. This registry is not a universal linguistic valency database; unsupported predicates must be reviewed rather than extrapolated from this list.

`completeness.status` can be `complete`, `underspecified`, `unresolved`, or `not_applicable`. A missing required argument changes the proposition to underspecified or unresolved and adds a structured unresolved item. Intransitive and relation predicates can be complete without an object when the relevant frame permits it.

`grammaticalTense` records grammatical tense independently of `temporalFrame.referenceTime`. Thus a present-tense conditional antecedent can refer to a future scenario without being rewritten as future grammatical tense.

`eventFrame` contains an ID, provisional kind (`event`, `state`, `relation`, or `unknown`), predicate, participants, and attributes such as frequency. The current event/state classification uses a small predicate registry and is not a general event ontology.

#### 4.4.2 OPERATOR

An operator modifies the expression named by `scope.targetId`. Its `scope.scopeKind` states how its target is interpreted.

Supported operator types:

| `operatorType` | Intended use | Example |
|---|---|---|
| `NEGATION` | Explicit negation; operator is `NOT`. | `NOT(LIKE(customer, tool))` |
| `MODAL` | Possibility, necessity, obligation, ability, or unknown modal force. | `MIGHT(P)` |
| `QUANTIFIER` | Quantification over a restrictor class. | `FORALL x: customer(x) -> P(x)` |
| `POLARITY` | Polarity was not determined. Operator is `UNKNOWN`. | `UNKNOWN_POLARITY(P)` |
| `UNRESOLVED_SCOPE` | A scope operator was detected but cannot yet be represented faithfully. The underlying proposition is not treated as an unmodified assertion. | unresolved quantifier over `P` |

Modal operator vocabulary currently includes `MIGHT`, `MAY`, `COULD`, `CAN`, `MUST`, `SHOULD`, `WILL`, `WOULD`, `POSSIBLE`, `NECESSARY`, `OBLIGATORY`, `POSSIBLE_OR_ABILITY`, and `UNKNOWN`.

Quantifier operators currently include `FORALL`, `EXISTS`, `EXACTLY_ONE`, `AT_LEAST_ONE`, and `AT_MOST_ONE`. The current sentence adapter explicitly recognizes only a narrow subset of quantifier constructions (notably “not every” and “no”). Other quantifier meanings must remain unresolved until their extraction and scope logic are implemented and tested.

For quantifiers, `variable`, `restrictor.entityId`, and `variableBinding` must agree. The corresponding argument in the scoped predication is annotated with the bound variable and restrictor entity. This makes the variable link explicit rather than treating the class label itself as the individual variable.

Examples:

```text
NOT(FORALL x: CUSTOMER(x) -> NEEDS(x, TOOL))
FORALL x: CUSTOMER(x) -> NOT(NEEDS(x, TOOL))
```

These encode different meanings and must not be collapsed into one another.

#### 4.4.3 CONNECTIVE

A connective combines propositions or clauses.

| Connective | Current meaning/status |
|---|---|
| `CONDITIONAL` | IF-style antecedent/consequent; antecedent is not an independent observation. |
| `EXCEPTION` | UNLESS-style exception relation; the exception condition is preserved without inventing its outcome. |
| `WHEN` | WHEN-clause kept distinct from a generic IF conditional; the clause itself is not promoted to an observed fact. |
| `AND` | Coordination of multiple expression roots. |
| `OR` | Alternative coordination when represented by separate supported propositions. The current English adapter records `disjunctionSemantics: inclusive_or_unspecified`; it does not assume exclusive choice. |
| `CONTRAST` | Contrastive coordination such as “but”; it is not automatically a logical contradiction. |

Binary connectives use `antecedentId` and `consequentId`; n-ary coordination uses `operandIds`. For `OR`, `disjunctionSemantics` must preserve `inclusive_or_unspecified` unless the source explicitly marks an exclusive alternative. An IF construction must carry `logicalStatus: conditional_not_asserted`; WHEN must carry `when_clause_not_asserted`; EXCEPTION must carry `exception_relation_asserted`.

The current source adapter safely constructs IF, UNLESS, and WHEN connectives when a structured subordinate proposition is available. Other markers (for example, ALTHOUGH or WHILE) are preserved as unresolved rather than automatically mislabeled as IF conditionals.

### 4.5 Relations

Relations connect expression roots rather than embedding unsupported implications into predicate strings.

A `CAUSE` relation created from a “because” construction must retain:

- `attribution.kind: source_asserted`;
- `verification: not_independently_verified`;
- relevant evidence references.

This records that the source presents one clause as the reason for another. It does not claim that an objective causal relation has been experimentally verified.

A `CONTRADICTS` relation is a candidate unless a separate resolution process has established more. Current contradiction generation uses selected frame fields and remains heuristic.

### 4.6 Unresolved items

`unresolvedItems` is a machine-readable list. Each item contains:

- `id`;
- `surfaceText`;
- `reason`;
- `status`: `unresolved`, `unsupported`, or `ambiguous`;
- optional `evidenceRef`;
- optional `scope`.

A record can have a structurally valid graph and still have `semanticValidation.status: partial`. This is intentional: structural consistency and semantic completeness are different questions.

## 5. Operator scope and ordering

The expression graph's links define scope. Operators must not be inferred to commute or be reordered merely because they share a proposition.

Examples:

- `MIGHT(NOT(P))` differs from `NOT(MIGHT(P))`.
- `NOT(FORALL x P(x))` differs from `FORALL x NOT(P(x))`.
- `NOT(DISLIKE(x,y))` does not imply `LIKE(x,y)` without additional assumptions about the predicate ontology and the relevant logical domain.

The current compatibility adapter applies a conservative default nesting order for its supported model fields. It does not yet solve every natural-language scope ambiguity. If the source or model proposal does not provide enough information to choose an operator order safely, the interpretation should remain unresolved or be marked for review rather than presented as uniquely determined.

## 6. Validation semantics

`semanticValidation.valid` means the graph passed implemented structural and reference checks. It does not mean the interpretation is correct.

Statuses:

- `valid`: structural checks passed and no unresolved items were recorded;
- `valid_with_warnings`: structural checks passed with non-fatal warnings;
- `partial`: graph is structurally valid but contains unresolved or unsupported semantic content;
- `invalid`: one or more structural/reference checks failed;
- `unavailable`: canonical semantic core was not loaded.

The validator currently checks:

- supported graph node types and operator/connective vocabulary;
- unique node/entity/mention/evidence identifiers;
- entity, mention, evidence, relation, and expression references;
- source quote/span consistency;
- subject argument availability or an explicit unresolved mention;
- known predicate argument requirements;
- event-frame participant references;
- quantifier variable/restrictor bindings;
- operator and connective scope references;
- expression graph cycles;
- candidate-model acceptance/truth boundaries.

Evidence alignment is not entailment checking. Predicate recognition, entity linking, tense, and clause analysis remain partially heuristic. LLM confidence is not calibrated by this validator.

The Workbench blocks acceptance into the knowledge base when the canonical graph is invalid or partial, or when unresolved items remain. A valid candidate still requires the user's explicit review and acceptance action.

## 7. Compatibility and migration from v0.4

- Existing v0.4 records retain their legacy `claims`, `entities`, `mentions`, `conditions`, `explanations`, and validation fields.
- The Workbench enriches imported/legacy claim records with `semanticModel` and `semanticValidation` when the v0.5 core is loaded.
- New exports use `schemaVersion: 0.5.0` and `representationProfile: USG-SR/0.5`.
- Batch export schema is `1.3` and records `semanticSchemaVersion: 0.5.0`.
- v0.4 schema files and documentation are retained as historical references.
- New consumers should not assume every v0.4 field can be losslessly interpreted as a v0.5 expression. If scope or an argument cannot be inferred from the old record, it must be reported as unresolved.

## 8. Current implementation coverage

The Workbench v0.5.0 implements:

- canonical graph construction from the existing claim proposal/compatibility view;
- scoped NOT, modal, and selected quantifier operators;
- IF, UNLESS, and WHEN connectives for structured nested clauses;
- separate source-attributed causal relations;
- entity and mention registries with provisional identity labels;
- preservation of unresolved pronouns as mentions rather than invented entities;
- event-frame attributes such as supported frequency phrases;
- evidence alignment records and graph reference/cycle validation;
- blocking of acceptance for invalid or partial canonical graphs;
- v0.4 record compatibility through the existing normalization pipeline.

Current extraction limitations include:

- English-focused and pattern-limited clause interpretation;
- narrow quantifier detection;
- limited event/predicate argument-frame registry;
- limited coreference and discourse resolution;
- no general word-sense disambiguation or cross-document entity resolution;
- no full semantic parsing of all adversative, concessive, relative, reported-speech, or nested-clause constructions;
- no comprehensive model-independent semantic-entailment verifier;
- no general inference over all nested operators, quantifiers, or temporal frames;
- no autonomous rule learning in this milestone.

The representation contract is more expressive than the currently implemented source-language extractor. A schema-supported operator or connective is not a promise that every sentence expressing it is already recognized automatically.

## 9. Required acceptance tests

A v0.5 semantic foundation evaluation should include, at minimum:

1. positive and negative versions of the same predicate;
2. double negation and modal-negation scope contrasts;
3. “not every” versus “no”;
4. missing/unsupported quantifier scope;
5. IF, UNLESS, and WHEN constructions;
6. unsupported subordinate markers that must remain unresolved;
7. multi-clause tense separation;
8. unresolved and resolved pronouns;
9. repeated mentions of the same surface label;
10. missing required arguments and missing predicates;
11. causal attribution versus independently verified causation;
12. duplicate or conflicting entity IDs;
13. invalid source spans and dangling graph references;
14. cycles in scope graphs;
15. v0.4 record import and compatibility export.

The automated tests in this release cover a deterministic subset of these requirements. Live Qwen/Gemma evaluation and a human-labelled unseen-sentence benchmark are still required before Milestone 1 can be declared complete.

## 10. Non-goals of v0.5.0

This release does not claim to provide general language understanding, world-model awareness, complete semantic parsing, autonomous knowledge construction, general-purpose symbolic reasoning, factual verification, or self-improving semantic learning. Those remain later milestones and require separate acceptance criteria.
