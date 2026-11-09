# Predicate-to-frame registry 1.0.0

**Registry ID:** `USG-PFR/1.0`  
**Status:** Initial evidence-backed baseline  
**Baseline pair:** Semantic Workbench 0.5.4 → Python reference kernel 0.4.0

## Purpose

This registry is the first Phase 1 crosswalk between Workbench predicate identifiers and Python kernel frames. It is intentionally separate from both implementation packages. It does not modify either baseline and does not claim full interoperability.

A mapping is approved only when the target frame's meaning, role structure, role kinds, required roles, and source argument structure are compatible. Lexical resemblance is not evidence of semantic equivalence.

## Audit result

The first audit produced **one conditional exact mapping**:

| Workbench predicate | Python frame | Status | Conditions |
|---|---|---|---|
| `CLOSES`, `CLOSED` | `CLOSE@1` | Conditional exact | Explicit active transitive subject/object; subject satisfies `Agent`; object satisfies `Artifact`; no material source argument is discarded |

The mapping is:

- `subject → AGENT`
- `object → UNDERGOER`

This is grounded in the actual frame declarations. Python `CLOSE@1` specializes `STATE_CHANGE@1`, inherits its `AGENT` role, requires `UNDERGOER`, narrows `UNDERGOER` to `Artifact`, and pins the dimension/direction/target to openness/decrease/closed state. Workbench 0.5.4 classifies `CLOSES` and `CLOSED` as event predicates and includes them in its transitive argument vocabulary.

It is **conditional**, not universally exact: Workbench's common entity representation can have unknown types. Unknown types cannot satisfy the Python role constraints merely by assumption. In addition, this mapping covers only the predicate frame and its two arguments; tense, aspect, negation, modality, quantification, attribution, temporal scope, evidence, and provenance need their own mappings.

## Why other plausible matches are not approved

The registry records explicit non-mapping dispositions, including:

- `WANTS/WANT`: Python `WANT@1` requires event-valued `CONTENT`; the Workbench object slot is an entity referent.
- `KNOWS/BELIEVES`: Python frames require proposition-valued `CONTENT`; the current Workbench object slot is not an embedded proposition.
- Buying/selling: Python `COMMERCIAL_TRANSACTION@1` requires `BUYER`, `SELLER`, and `GOODS`; the ordinary Workbench subject/object form does not provide all required parties.
- Receiving: Python `GIVE@1` requires transfer roles that a receive predication does not fully supply.
- Increasing/reducing/breaking: a generic `STATE_CHANGE@1` conversion would need exact dimension and state/target information that the source predicate does not reliably provide.
- Relation predicates such as `SUBCLASS_OF`, `PART_OF`, and `CAUSES` are not treated as frame mappings. They require a separate relation/operator crosswalk.

The registry deliberately distinguishes `CLOSES/CLOSED` from the bare source identifier `CLOSE`: the latter appears in the Workbench transitive-role vocabulary but is not classified as an event predicate in the same source file.

## Conversion behavior

1. Exact mapping conditions satisfied → eligible for `APPLY(CLOSE@1, ...)`.
2. Known predicate but one or more applicability conditions unknown or unmet → `PARTIAL` or `UNRESOLVED`, with the failed conditions recorded.
3. Predicate explicitly listed as non-mapped → retain the source representation and return its recorded disposition.
4. Predicate absent from this registry → `UNSUPPORTED`; never choose a frame by name similarity.

No argument may be invented, dropped, or coerced to a different semantic kind to force a complete result.

## Evidence sources

All evidence is tied to the immutable repository baselines:

- Workbench predicate vocabulary and graph construction: `implementations/semantic-workbench-js/v0.5.4/semantic-core.js`
- Workbench source-composer verb vocabulary: `implementations/semantic-workbench-js/v0.5.4/semantic-composer.js`
- Python frame definitions: `implementations/python-kernel/v0.4.0/usg/foundation/frames.py`
- Python frame inheritance/resolution: `implementations/python-kernel/v0.4.0/usg/model/frames.py`
- Python expression operator signatures: `implementations/python-kernel/v0.4.0/usg/grammar/node.py`

The matching schema is `specifications/predicate-frame-registry-1.0.schema.json`. Automated source-backed checks live in `tests/test_predicate_frame_registry.py`.

## Scope boundary and next work

This is **Phase 1, Step 1** only. It establishes the predicate-to-frame evidence baseline. It does not implement a document adapter or claim round-trip interoperability.

The next registry expansion should be driven by the remaining contract layers: exact relation mappings; operators and scopes; nested proposition arguments; and explicit compatibility reporting. The full document adapter should consume this registry rather than introducing its own guessed mappings.

## Versioning

Published registry versions are immutable. Any mapping change must update the version and include source evidence and automated tests. A new Python or Workbench release requires a compatibility review; this registry must not silently continue to claim applicability to a different baseline.
