# Phase 1 Step 5S — Native UnresolvedItem model v1.2.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_unresolved_v12` 1.2.0  
**Scope:** Native UnresolvedItem model and conformance tests only. Document adapter is a separate subsequent step.

## Native fields

- Opaque item ID, required status, and required reason string.
- Optional exact surface text, opaque scope reference, scope label, and native status.
- Ordered Evidence and candidate reference strings, preserving order and repetition.

## Governing invariants

1. Identity is the opaque UnresolvedItem ID.
2. All seven statuses remain distinct: UNRESOLVED, UNSUPPORTED, AMBIGUOUS, INCOMPLETE, CONFLICTING, RESOURCE_INTERRUPTED, and UNKNOWN.
3. Reason and surface text are preserved exactly; no normalization or paraphrase is performed.
4. Scope references remain opaque because the contract does not declare a single target reference space for them.
5. Candidate references remain opaque because the contract does not define one candidate record family.
6. Evidence and candidate reference order and repetition are retained.
7. UNKNOWN is not a synonym for UNRESOLVED or UNSUPPORTED.
8. Resource interruption is not converted into semantic ambiguity or a negative interpretation.
9. The model performs no candidate ranking, resolution, inference, or automatic status transition.
10. No arbitrary unresolved-item count limits are introduced.

## Compatibility boundary

Python v0.4.0–v1.1.0, USG-SEM/1.0, Workbench v0.5.4, archives, and existing Node.js workflows remain unchanged. Model-only; no document adapter or resolution engine is claimed.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.2.0 python -m unittest discover -s implementations/python-kernel/v1.2.0/tests -v
```


> **Contract-alignment note:** The initial v1.2.0 model/adapter is retained as historical. Step 5T1 introduces v1.2.1, where `scopeRef` is a typed Expression reference and `evidenceRefs` are typed Evidence references, matching the canonical document validator. Use v1.2.1 for current composed interoperability.
