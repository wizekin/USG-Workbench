# Phase 1 Step 5R — ExpressionRelation document adapter v1.1.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python ExpressionRelation v1.1.0  
**Scope:** Document projection, typed reference validation, mapping diagnostics, loss-preserving export, and conformance tests.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v11,
    kernel_v11_document_to_contract,
)
native_document = document_to_kernel_v11(contract_document)
updated_document = kernel_v11_document_to_contract(native_document)
```

The adapter is lazy-exported to avoid imposing v1.1.0 requirements on earlier adapter generations.

## Mapping behavior

- Projects only records with recognized relation and verification enums and resolvable source/target Expression references.
- Every Evidence reference must resolve in the canonical Evidence collection; order and repetition are retained.
- Optional attribution is preserved as structured descriptive metadata.
- Unknown properties remain canonical-only and produce PARTIAL diagnostics.
- Unsupported required enum values, malformed reference lists, and dangling required references keep the complete relation canonical-only.
- Native edits merge only into expressionRelations. Other record families, unknown properties, and sidecars remain canonical.
- Stale canonical snapshots and invalid changed references are rejected.

## Semantic safeguards

1. Source/target direction is preserved exactly.
2. Evidence references remain ordered and repeated.
3. Relation type and verification status are independent.
4. No inverse, symmetric, transitive, causal, temporal, contradiction, entailment, or coreference inference is performed.
5. Attribution does not promote an attributed proposition to an independent assertion.
6. Unsupported and dangling fields are never silently dropped, defaulted, or coerced.

All non-expressionRelation record families remain canonical-only in this adapter. It does not claim full document interoperability or relation reasoning.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.1.0 python -m unittest discover -s tests -p "test_python_kernel_v11_document_adapter.py" -v
```
