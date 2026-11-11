# Phase 6 — Step 6.3: Typed Semantic Roles, Predicate Frames, and Valency

**Status:** CANDIDATE RESOURCE FOUNDATION — not runtime-enabled  
**Registry:** `USG-FRAME-REGISTRY/0.3.0`  
**Contract:** `USG-INTERPRET/0.3.0`  
**Schema:** `specifications/usg-frame-registry-0.3.0.schema.json`  
**Resource:** `resources/semantic-frames/v0.3.0/registry.json`  
**Next gate:** Step 6.4 — expanded lexical and morphology resources

## 1. Purpose

Define a language-independent semantic-role vocabulary and typed predicate-frame/valency representation before grammar implementation. The registry is a candidate resource foundation. It does not enable the four construction families in the Step 6.2 corpus and does not claim that the current runtime can select these frames.

## 2. Semantic roles are not syntax or predicate heads

A semantic role identifies the meaning-bearing participation relation between a filler and a predicate frame. It is not a token position, dependency label, surface subject/object, or verb form. Predicate heads and grammatical markers are separately evidenced spans; they MUST NOT be inserted into participant-role bindings.

Examples:
- `AGENT`: event initiator;
- `PATIENT`: affected entity;
- `THEME`: transferred/moved/perceived entity;
- `RECIPIENT`: receiver;
- `EXPERIENCER`: entity undergoing a state/experience;
- `ENTITY` and `ATTRIBUTE`: the two sides of a property predication;
- `LOCATION`: place associated with an event or entity.

The registry defines stable role IDs and definitions. Frame-specific slots refer to these IDs; labels are display text only. No consumer may infer identity or role semantics from the label string.

## 3. Predicate-frame model

Each frame has:
- an opaque stable `frameId` and explicit `frameVersion`;
- a semantic class (`EVENT`, `STATE`, `RELATION`, or `PROPERTY`);
- a predicate-sense reference;
- typed valency slots;
- independent language-specific construction bindings;
- independent lexical realizations and resource references.

Each slot defines its semantic role, minimum and maximum filler cardinality, allowed filler sorts, and source-grounding policy. A missing required filler cannot be guessed. A frame is incomplete or unresolved until all required slots are licensed by source evidence and deterministic constraints.

Lexical realizations are not definitions. The same semantic frame may have multiple lexical realizations in a language, and equivalent realizations may differ across English and MSA Arabic. Lexical entries must point to a sense/frame candidate; the lemma alone does not prove a frame.

## 4. Initial candidate frames

The candidate registry contains four frame families aligned to the four Step 6.2 benchmark targets:
- intransitive event;
- transfer/ditransitive event;
- copular property predication;
- spatial/location relation.

All role definitions, frames, lexical realizations, and construction bindings remain `CANDIDATE`. The registry-level status is also `CANDIDATE`. Benchmark inventory entries remain disabled.

## 5. Role binding and ambiguity policy

- Surface order alone never determines semantic roles.
- Syntactic function, morphological case/agreement, lexical valency, construction constraints, and source spans are distinct evidence channels.
- A binding must cite its frame slot, filler node, and derivation/source evidence.
- Multiple fillers are allowed only where the slot's cardinality permits them.
- Unknown or incompatible fillers remain unresolved; they are not coerced into a compatible sort.
- Competing frame/role assignments remain alternatives. Ranking metadata is not calibrated probability.
- A frame with unmet required slots cannot be reported as a complete predicate interpretation.
- Resource frequency or association strength cannot promote a candidate to an approved definition.

## 6. Cross-reference validation

JSON Schema validation is necessary but not sufficient. The validator also checks:
- unique role IDs, frame IDs, slot IDs, and construction bindings;
- every slot role reference resolves to a declared role;
- slot filler sorts are compatible with the referenced role definition;
- every frame has language realizations and construction bindings for both initial profiles;
- language tags and profile IDs agree;
- min/max cardinality is consistent;
- candidate-only state is preserved (no accidental promotion);
- each construction binding corresponds to a Step 6.2 benchmark construction ID.

## 7. Acceptance and limits

Step 6.3 acceptance validates the schema, candidate registry, cross-references, and invariants. It does not implement parsing, role assignment, or frame selection. Those runtime behaviors are introduced only in later construction steps and must pass the Step 6.2 evaluator.

The current Step 6.2 corpus uses the role field for predicate-head annotations in some legacy fixtures. Such predicate-head/grammatical-marker spans are not semantic participant roles and MUST NOT be loaded into this registry as role definitions. A benchmark annotation migration must separate predicate spans from semantic-role bindings before full Step 6.14 scoring. The frozen v0.3.0 corpus remains unchanged; the correction must be published as a separately versioned additive corpus revision.

**Next step:** Step 6.4 — add only the provenance-bearing English/MSA Arabic lexical and morphology resources needed by the frozen construction fixtures.
