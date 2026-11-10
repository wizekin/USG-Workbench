# Phase 1 Step 5T — UnresolvedItem document adapter v1.2.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python UnresolvedItem v1.2.0  
**Scope:** Document projection, Evidence-reference validation, mapping diagnostics, loss-preserving export, and conformance tests.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v12,
    kernel_v12_document_to_contract,
)
native_document = document_to_kernel_v12(contract_document)
updated_document = kernel_v12_document_to_contract(native_document)
```

## Mapping behavior

- Projects records with recognized status, required reason, and exact supported optional string fields.
- Explicit Evidence references must resolve in the canonical Evidence collection; order and repetition are preserved.
- Scope and candidate references remain opaque because USG-SEM/1.0 does not define a single target space for them.
- Unknown record properties remain canonical-only and produce PARTIAL diagnostics.
- Unsupported statuses, malformed fields, and dangling Evidence references keep the complete item canonical-only.
- Native edits merge only into unresolvedItems; all other record families, unknown properties, and sidecars remain canonical.
- Stale snapshots and changed dangling Evidence references are rejected.

## Semantic safeguards

1. UNKNOWN, AMBIGUOUS, UNSUPPORTED, INCOMPLETE, CONFLICTING, RESOURCE_INTERRUPTED, and UNRESOLVED remain distinct.
2. No scope resolution, candidate ranking, antecedent resolution, or semantic completion is inferred.
3. Opaque candidate/scope references are not guessed into record types.
4. Resource interruption is not treated as evidence for a semantic reading.
5. Unresolved status is not a negative truth judgment.
6. Unsupported information is never silently discarded or defaulted.

All non-UnresolvedItem record families remain canonical-only in this adapter. No resolver or inference engine is implemented.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.2.0 python -m unittest discover -s tests -p "test_python_kernel_v12_document_adapter.py" -v
```


> **Contract-alignment note:** The initial v1.2.0 model/adapter is retained as historical. Step 5T1 introduces v1.2.1, where `scopeRef` is a typed Expression reference and `evidenceRefs` are typed Evidence references, matching the canonical document validator. Use v1.2.1 for current composed interoperability.
