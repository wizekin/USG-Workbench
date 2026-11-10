# Phase 1 Step 5U — Native Derivation model v1.3.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_derivation_v13` 1.3.0  
**Scope:** Native Derivation record model and conformance tests only. Document adapter is a separate subsequent step.

## Native fields

- Opaque Derivation ID.
- Required method: DETERMINISTIC_RULE, MODEL_PROPOSAL, IMPORT, INFERENCE, COMPOSITION, or UNKNOWN.
- Ordered input/output reference strings and rule IDs, preserving repetition.
- Required status: PROPOSED, VALIDATED, REJECTED, INCOMPLETE, or UNKNOWN.
- Optional component, model identity/metadata, timestamp string, and ordered diagnostics.

## Governing invariants

1. Derivation identity is its opaque ID.
2. Input/output references are heterogeneous opaque IDs; no target record space is guessed.
3. Rule IDs remain opaque because the contract does not define a first-class rule-record collection.
4. Input, output, rule, and diagnostic order and repetition are preserved.
5. MODEL_PROPOSAL is not VALIDATED; a model name or timestamp does not certify correctness.
6. UNKNOWN, INCOMPLETE, REJECTED, PROPOSED, and VALIDATED remain distinct.
7. Timestamp is retained exactly; no timezone normalization is performed.
8. Derivation provenance does not establish truth or entailment.
9. The model performs no inference, verification, or automatic status transition.
10. No arbitrary derivation-count limits are introduced.

## Compatibility boundary

Python v0.4.0–v1.2.0, USG-SEM/1.0, Workbench v0.5.4, archives, and existing Node.js workflows remain unchanged. Model-only; no derivation execution engine is claimed.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.3.0 python -m unittest discover -s implementations/python-kernel/v1.3.0/tests -v
```
