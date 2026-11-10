# Phase 1 Step 5V — Derivation document adapter v1.3.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python Derivation v1.3.0  
**Scope:** Document projection, mapping diagnostics, loss-preserving export, and conformance tests.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v13,
    kernel_v13_document_to_contract,
)
native_document = document_to_kernel_v13(contract_document)
updated_document = kernel_v13_document_to_contract(native_document)
```

## Mapping behavior

- Projects records with recognized method/status enums, required ordered input/output references, and supported optional fields.
- Input/output/rule references remain opaque because they may identify heterogeneous record families or rule resources not modeled in USG-SEM/1.0.
- Model provider/name/revision fields are projected; unknown model metadata is preserved in the native model's descriptive metadata.
- Unknown derivation properties remain canonical-only and produce PARTIAL diagnostics.
- Unsupported required enums or malformed required fields keep the complete record canonical-only.
- Native edits merge only into derivations; all other record families, unknown fields, and sidecars remain canonical.
- Stale canonical snapshots are rejected.

## Semantic safeguards

1. Derivation method and status are independent.
2. MODEL_PROPOSAL does not imply VALIDATED.
3. Input/output/rule IDs are not assigned guessed reference spaces.
4. Provenance does not establish truth, entailment, or correctness.
5. No inference, verification, or automatic status transition is performed.
6. Unknown fields are preserved rather than silently discarded.

All non-Derivation record families remain canonical-only in this adapter. It does not implement a derivation executor or reasoning engine.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.3.0 python -m unittest discover -s tests -p "test_python_kernel_v13_document_adapter.py" -v
```
