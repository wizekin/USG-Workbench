# Phase 1 Step 5X — Definitions document adapter v1.4.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python Definitions v1.4.0  
**Scope:** Document projection, per-family diagnostics, loss-preserving export, and conformance tests.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v14,
    kernel_v14_document_to_contract,
)
native_document = document_to_kernel_v14(contract_document)
updated_document = kernel_v14_document_to_contract(native_document)
```

## Mapping behavior

- Projects the four catalogue groups: concepts, frames, roles, and relations.
- Preserves all 15 SemanticKind values, positive concept/frame versions, ordered frame role strings, grammar/ontology release identifiers, and structured constraints/properties.
- Unknown record properties remain canonical-only and produce PARTIAL diagnostics; records with unsupported required fields or unknown SemanticKind remain complete canonical-only records.
- Native edits merge field-by-field into their original group records; canonical-only properties are retained and cannot be modified through the native projection.
- All other document record families and sidecars remain canonical-only.
- Stale canonical snapshots are rejected.

## Semantic safeguards

1. Labels do not establish identity or equivalence.
2. Frame roles remain ordered opaque strings; no role compatibility or identity is inferred.
3. Constraints and relation properties do not trigger reasoning.
4. No ontology equivalence, frame inheritance, inverse/symmetric/transitive relation inference, or definition activation is performed.
5. Unknown definition properties are preserved rather than discarded.
6. No arbitrary catalogue-size limits are introduced.

This adapter does not implement ontology reasoning or automatic definition learning.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.4.0 python -m unittest discover -s tests -p "test_python_kernel_v14_document_adapter.py" -v
```
