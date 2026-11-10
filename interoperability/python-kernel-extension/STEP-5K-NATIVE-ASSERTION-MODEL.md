# Phase 1 Step 5K — Native Assertion model v0.8.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_assertion_v08` 0.8.0  
**Scope:** Native data model and conformance tests only; document adapter is a later step.

## Why Assertions are a distinct record family

USG-SEM/1.0 separates an expression describing semantic content from an Assertion that makes a claim about that content. A predicate/event description does not establish that the described event occurred. An Assertion carries provenance, epistemic status, commitment, evaluation context, lifecycle, and links to sources/evidence/definitions/alternatives.

The legacy Python kernel v0.4.0 already has an Assertion record, but its representation cannot preserve every USG-SEM distinction: it has a single evidence reference, no native attributed Referent field mapping in the current adapter, no typed evaluation-context reference, and does not cover all canonical lifecycle values. The old model and adapter remain unchanged. v0.8.0 is additive and independently versioned.

## Native fields

- Opaque Assertion ID.
- Required typed Expression reference.
- Exact contract enums for origin, epistemic status, commitment, evaluation-context kind, and lifecycle stage.
- Optional typed Referent attribution, Source, ordered Evidence references, Definition reference, and Alternative Group reference.
- Evaluation context keeps kind, optional typed Context reference, and optional name.

Reference spaces are explicit: ASSERTION, EXPRESSION, SOURCE, REFERENT, EVIDENCE, CONTEXT, DEFINITION, and ALTERNATIVE_GROUP. IDs are opaque and are never parsed to infer their target type.

## Governing invariants

1. Assertion identity is its opaque Assertion ID, not its expression reference, source, evidence, or text.
2. An Assertion is not the expression it references; the expression alone does not assert occurrence or truth.
3. SOURCE_ASSERTED, INFERRED, VERIFIED, DISPUTED, and UNKNOWN remain distinct. SOURCE_ASSERTED records what a source presents as asserted; it does not establish objective truth. VERIFIED remains a governed evaluation label, not a model confidence score.
4. Origin, epistemic status, commitment, evaluation context, and lifecycle are separate axes. The model does not infer one from another.
5. AUTHOR, ATTRIBUTED, and NONE remain distinct. The model does not require an attribution link solely because commitment is ATTRIBUTED; the canonical schema does not impose that implication.
6. Evidence references are ordered and may repeat; they are not collapsed to one reference or treated as entailment.
7. Evaluation-context references, attribution, source, evidence, definition, and alternative-group references use distinct target spaces.
8. Absent optional values remain absent. No default Source, Referent, Evidence, Context, Definition, or alternative group is invented.
9. Unknown future values and additional canonical properties remain eligible for canonical preservation in the later adapter; they are not coerced into a known enum.
10. No truth evaluation, inference, lifecycle transition policy, evidence entailment, or document-level round-trip is claimed by this model-only step.

## Compatibility boundary

- v0.4.0 and v0.5.0 packages remain immutable.
- v0.6.0 Referent identity and v0.7.0 Mention models remain unchanged.
- USG-SEM/1.0 schema and document adapter remain unchanged.
- This step does not modify Workbench v0.5.4, archives, baseline fixtures, or existing Node.js workflow/action versions.
- No human-review gate or arbitrary semantic complexity limit is introduced.

## Tests

Run from repository root:

```bash
PYTHONPATH=implementations/python-kernel/v0.8.0 python -m unittest discover -s implementations/python-kernel/v0.8.0/tests -v
```

The suite covers typed references, every standardized enum, independent claim metadata axes, multiple ordered evidence links, optional-reference preservation, identity semantics, and rejection of wrong reference spaces.
