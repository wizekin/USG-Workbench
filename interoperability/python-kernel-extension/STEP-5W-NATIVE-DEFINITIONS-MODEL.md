# Phase 1 Step 5W — Native Definitions catalogue model v1.4.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_definitions_v14` 1.4.0  
**Scope:** Versioned catalogue model and conformance tests for concepts, frames, roles, and relations. Document adapter is a separate subsequent step.

## Native record families

- **Concept:** opaque ID, exact label, required SemanticKind, positive version, optional definition/lifecycle stage, and preserved canonical-only extras.
- **Frame:** opaque ID, exact label, positive version, ordered role-reference strings, optional SemanticKind, and preserved canonical-only extras.
- **Role:** opaque ID, exact label, optional structured constraints, and preserved canonical-only extras.
- **Relation:** opaque ID, exact label, optional structured properties, and preserved canonical-only extras.
- **Catalogue:** ordered groups for concepts, frames, roles, and relations, plus optional grammar version and ontology release identifiers.

All 15 USG-SEM semantic kinds remain distinct. Frame role strings are kept opaque and ordered; no role identity or compatibility is inferred from a label.

## Governing invariants

1. Definition identity is its opaque ID, not its label.
2. SemanticKind is distinct from expression sort and remains explicit.
3. Definition versions are positive integers; no implicit version upgrade occurs.
4. Frame role order and repetition are preserved.
5. Constraints and relation properties are descriptive structured data; they do not activate automatic reasoning.
6. Unknown canonical properties are preserved separately and do not override standardized fields.
7. Grammar and ontology release identifiers remain distinct and exact.
8. No concept equivalence, frame inheritance, role compatibility, relation symmetry, inverse, or transitivity is inferred.
9. The model does not invent definitions or promote candidate definitions into an established ontology.
10. No arbitrary catalogue-size limits are introduced.

## Compatibility boundary

Python v0.4.0–v1.3.0, USG-SEM/1.0, Workbench v0.5.4, archives, and existing Node.js workflows remain unchanged. Model-only; no ontology reasoning or document adapter is claimed.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.4.0 python -m unittest discover -s implementations/python-kernel/v1.4.0/tests -v
```
