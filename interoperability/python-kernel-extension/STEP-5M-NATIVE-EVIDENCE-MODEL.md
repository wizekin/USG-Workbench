# Phase 1 Step 5M — Native Evidence model v0.9.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_evidence_v09` 0.9.0  
**Scope:** Native data model and conformance tests only. Document-adapter integration is a separate later step.

## Why Evidence is a distinct record family

An Evidence record binds a quoted passage to an explicit Source and source span, while recording separate assessments of textual alignment and semantic support. Evidence is not an Assertion, an Expression, or a truth judgment. An exact quote at the declared span establishes textual alignment only; it does not establish that the quote entails, corroborates, or proves the attached semantic content.

## Native fields

- Opaque Evidence ID.
- Required typed Source reference.
- Required source span with zero-based, end-exclusive Unicode code-point offsets.
- Exact quote string; the model does not normalize or rewrite it.
- Required alignment status: `EXACT`, `MISMATCH`, or `UNVERIFIED`.
- Required semantic-support status: `NOT_ESTABLISHED`, `PROPOSED`, `RULE_SUPPORTED`, `CORROBORATED`, `DISPUTED`, or `UNKNOWN`.
- Ordered supporting-rule reference strings, preserving repetition.
- Optional native verification-meaning string for implementation-specific explanation.

The span's Source reference must match the Evidence record's Source reference. IDs remain opaque; reference target types are explicit and never inferred from ID spelling.

## Governing invariants

1. Evidence identity is its opaque Evidence ID, not its quote, span, or Source.
2. Source alignment and semantic support are independent axes. No status on one axis implies a status on the other.
3. `EXACT` means exact textual alignment only; it is not entailment, corroboration, truth, or objective verification.
4. `NOT_ESTABLISHED` remains the default semantic-support state in the canonical contract; the native model requires an explicit value and does not infer a stronger one.
5. `MISMATCH` and `UNVERIFIED` remain distinct and are never coerced to `EXACT`.
6. Span offsets are zero-based, end-exclusive Unicode code-point offsets; the model checks range shape but cannot validate source bounds or quote alignment without the canonical Source text.
7. Source references use the SOURCE target space. Rule references remain opaque strings because USG-SEM/1.0 does not define a first-class rule-record collection.
8. Supporting-rule reference order and repetition are retained exactly.
9. Optional native verification meaning is descriptive metadata; it cannot override either standardized status axis.
10. No entailment engine, truth evaluation, evidence ranking, inference, corroboration procedure, or automatic status transition is implemented by this model.

## Compatibility boundary

- Python v0.4.0–v0.8.0 packages remain unchanged.
- USG-SEM/1.0 schema and document adapters remain unchanged.
- Workbench v0.5.4, archives, historical baselines, and existing Node.js workflow/action versions remain unchanged.
- This is a model-only step. It does not claim document-level Evidence projection or full Evidence round-trip.
- No human-review gate or arbitrary semantic-complexity cap is introduced.

## Tests

Run from repository root:

```bash
PYTHONPATH=implementations/python-kernel/v0.9.0 python -m unittest discover -s implementations/python-kernel/v0.9.0/tests -v
```

The suite covers identity, typed references, span constraints, exact quote preservation, independent status axes, all standardized enum values, and ordered/repeated supporting-rule references.
