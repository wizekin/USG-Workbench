# USG Knowledge Record-Kinds Registry 0.1.0

This registry defines the minimum payload keys for each `USG-KNOWLEDGE/0.1.0` record kind. Payload content remains evidence-bearing candidate data unless a separate acceptance policy says otherwise.

| Kind | Required payload keys | Meaning |
|---|---|---|
| `LEXICAL_FORM` | `form`, `language`, `script` | An observed surface form; not a sense or concept. |
| `LEMMA` | `lemma`, `language`, `part_of_speech` | A normalized lexical unit. |
| `LEXICAL_SENSE` | `lemma_record_id`, `language`, `definition`, `sense_source_id` | A source-linked meaning candidate for a lemma. |
| `CONCEPT` | `concept_type`, `namespace`, `label` | A namespace-scoped abstract concept identifier. |
| `SEMANTIC_CLASS` | `class_key`, `definition` | A typed category with an explicit definition. |
| `PREDICATE_FRAME` | `frame_key`, `version`, `roles` | A predicate/frame with explicit role constraints. |

## Required invariants

- Record IDs are unique within a bundle and stable only within the declared namespace and versioning policy.
- Lexical form and lemma language values use declared BCP-47 tags or repository language-profile identifiers (for example `en` and `ar`).
- A lexical sense references a lemma record; a lemma may have zero or more senses.
- A concept does not identify a real-world entity. Entity identity and discourse coreference remain separate concerns.
- A sense-to-concept mapping is a separate object with evidence. Multiple senses may map to multiple concepts and vice versa.
- Class membership is not identity, and class inheritance is not implied.
- Frame roles declare role key, direction/position, and optional semantic-class constraints. A role label does not itself establish a fact.
- A record may have multiple source/evidence/context links; links do not count as independent corroboration unless source independence is assessed separately.

## Examples

- The English form `bank` may connect to multiple lemma/sense records.
- A sense of `bank` meaning a financial institution and a sense meaning a river edge must not share a concept merely because the spelling is the same.
- Arabic `عين` may have several lexical senses and concept mappings. Translation or shared form does not collapse them.
- `EQUIVALENT` requires explicit supporting evidence and scope; overlapping or related meanings must use their own mapping type.
