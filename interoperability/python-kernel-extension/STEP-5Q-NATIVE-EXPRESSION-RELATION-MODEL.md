# Phase 1 Step 5Q — Native ExpressionRelation model v1.1.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_expression_relation_v11` 1.1.0  
**Scope:** Native expression-relation model and conformance tests only. The document adapter is a separate subsequent step.

## Native fields

- Opaque relation ID.
- Required relation type: CAUSE, CONTRADICTS, SUPPORTS, ATTACKS, RELATED_TO, PRECEDES, OVERLAPS, COREFERS, or OTHER.
- Required typed source and target Expression references.
- Required verification status: NOT_INDEPENDENTLY_VERIFIED, RULE_SUPPORTED, CORROBORATED, DISPUTED, or UNKNOWN.
- Ordered Evidence references, preserving order and repetition.
- Optional attribution object retained as descriptive structured metadata.

## Governing invariants

1. Relation identity is its opaque ID.
2. Source and target are directed Expression references; their order is preserved.
3. Relation type names do not create inverse, symmetric, transitive, causal, temporal, or coreference conclusions.
4. Verification status is explicit and never inferred from relation type or Evidence presence.
5. UNKNOWN, DISPUTED, and NOT_INDEPENDENTLY_VERIFIED remain distinct.
6. Evidence links are typed and ordered; no evidence is inferred or deduplicated.
7. Attribution remains metadata and does not convert attributed content into an independently asserted fact.
8. The model does not evaluate truth, causality, contradiction, entailment, temporal ordering, or coreference.
9. Reference resolution is the responsibility of the document adapter.
10. No arbitrary semantic graph-size limits are introduced.

## Compatibility boundary

Python v0.4.0–v1.0.0, USG-SEM/1.0, Workbench v0.5.4, archives, and existing Node.js workflows remain unchanged. This is model-only; no document projection or relation reasoning is claimed.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.1.0 python -m unittest discover -s implementations/python-kernel/v1.1.0/tests -v
```
