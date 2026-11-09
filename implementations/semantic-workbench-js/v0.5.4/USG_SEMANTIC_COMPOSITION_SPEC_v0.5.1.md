# USG Semantic Composition Specification v0.5.1

**Module:** `semantic-composer.js`  
**Composer version:** `0.2.0`  
**Workbench version:** `0.5.1`  
**Profile:** `USG-SR/0.5.1`

## 1. Purpose and boundary

The composer converts supported source text into clause-level propositions and explicit relationships between those propositions. It separates **clause parsing** from **composition**: clause frames are parsed independently, and a connective/operator structure is then constructed from them.

It is a finite, conservative English grammar, not an unrestricted parser. It should return no complete parse when an input cannot be represented safely. It does not prove entailment, truth, or the intended reading of ambiguous text.

## 2. Output model

`composeSourceText(sourceText)` returns either `null` (unsupported, incomplete, or unsafe to parse) or:

```json
{
  "parser": "USG-SRC",
  "parserVersion": "0.2.0",
  "complete": true,
  "claims": [],
  "explanations": [],
  "semanticComposition": {},
  "unresolved": [],
  "clauseCount": 1,
  "compositionType": "ATOMIC"
}
```

Each clause claim contains a proposition predicate, arguments, polarity, grammatical tense, modality/scope, quantifier scope when overt, temporal frame, event attributes, conditions if embedded, source clause text, source evidence span, and a local rule/provenance marker.

The app adapter converts these clause frames into compatibility claims. The canonical semantic core then builds entity, mention, evidence, proposition, operator, connective, relation, root, and unresolved registries.

## 3. Clause-frame layer

A clause frame is a predication with a subject and predicate, plus an object when the recognized predicate frame requires one. The predicate vocabulary is independent from connective rules. Current vocabulary includes selected forms of:

- NEED, LIKE, DISLIKE, WANT;
- USE and STOP USING;
- BUY/PURCHASE/ACQUIRE;
- INCREASE, DECREASE, REDUCE;
- FAIL, SELL, PRODUCE, RECEIVE, BREAK, START, CLOSE, MEASURE;
- copular DIFFER.

This is a small, explicit lexicon, not an exhaustive English valency dictionary. Verb senses and alternate argument structures may require additions. An input such as `The customer needs.` is rejected by the source composer as incomplete rather than declared a complete source parse.

## 4. Operators

### 4.1 Negation

Negation is represented as an operator over the proposition it scopes over:

```text
NOT
  └─ NEEDS(customer, tool)
```

### 4.2 Modality

Supported operators include MIGHT, MAY, COULD, CAN, MUST, SHOULD, WILL, WOULD, and EXPECTED. `EXPECTED` is an epistemic expectation operator, not automatically deontic obligation.

For example:

```text
MIGHT
  └─ NOT
      └─ NEEDS(customer, tool)
```

This ordering is significant and must not be flattened into a single modality/polarity flag.

### 4.3 Quantifiers

Current source extraction supports selected `not every` and `no` constructions:

- `not every` → `NOT(FORALL x: class(x) -> P(x))`
- `no` → `FORALL x: class(x) -> NOT(P(x))`

Empty model-provided quantifier objects do not count as quantifier information. Unsupported but meaningful quantifier content remains unresolved instead of being silently flattened.

## 5. Connective and relation composition

### IF

`IF P, Q` becomes a directed `CONDITIONAL` connective. P is embedded as an antecedent and is not asserted as an observed fact. Main-clause and antecedent tense are represented independently.

### UNLESS

`UNLESS P, Q` becomes an `EXCEPTION` connective. Its antecedent is explicitly represented as `NOT(P)`, equivalent to the ordinary conditional reading `IF NOT P THEN Q`, while the original `unless` marker remains visible.

### WHEN

`WHEN P, Q` becomes a `WHEN` connective, distinct from IF. The antecedent is not promoted to an independently asserted fact. This release does not attempt a complete distinction among all habitual, temporal, and conditional readings of WHEN.

### ALTHOUGH

The concessive clause and matrix clause remain separate propositions joined by a `CONCESSIVE` connective. No causal relationship is inferred from concessive wording alone.

### BECAUSE

The cause and effect clauses remain separate propositions linked by a typed `CAUSE` relation. Its attribution is `source_asserted`; verification is `not_independently_verified`.

### BUT, OR, AND

Each side is parsed as a separate proposition. BUT produces `CONTRAST`; OR produces `OR` with `inclusive_or_unspecified` semantics; AND produces `AND`.

## 6. Discourse references and event attributes

The composer supports limited pattern-grounded reference resolution, including HE/SHE/THEY to a previously introduced discourse subject and IT/THEM to a previously introduced discourse object. Resolved mention surface text is retained in the canonical graph.

Recognized frequency phrases (for example, `every day`, `daily`, `every week`) are attached to appropriate event frames, not appended to object text. Unsupported/placeholder attributes such as `...` or `exact source phrase` are rejected unless a real source phrase is present and its value/type is supported.

## 7. Clause order and coverage

Current deterministic coverage includes selected leading and trailing IF/UNLESS/WHEN/ALTHOUGH/BECAUSE clauses, one top-level BUT/OR/AND connective, and short multi-sentence discourse. It supports selected modal/negation combinations and the listed predicate vocabulary.

The following remain outside guaranteed source-composition coverage:

- arbitrary nested/multiple connectives in one sentence;
- relative clauses and reported speech/attitude complements;
- unrestricted passive voice and complex voice alternations;
- unrestricted ellipsis and long-distance coreference;
- broad polysemy, idioms, attachment ambiguity, and lexical valency;
- all tense/aspect/modal interactions and quantifier constructions.

If the source cannot be parsed completely under the supported grammar, `composeSourceText` returns `null`. The application then keeps the regular model/normalization path and preserves unresolved material. It must not claim the unsupported source was compositionaly parsed.

## 8. Validation and epistemic boundary

A valid semantic graph means its implemented structure/reference constraints pass. It does not mean the source entails the graph or the graph is objectively true. Every candidate still requires human review before knowledge-base acceptance.
