# Phase 1 Step 5P — Context document adapter v1.0.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python Context v1.0.0  
**Scope:** Document import/projection, typed reference validation, mapping diagnostics, loss-preserving export, and adapter conformance tests. The canonical schema and native model are unchanged.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v10,
    kernel_v10_document_to_contract,
)

native_document = document_to_kernel_v10(contract_document)
mapping = native_document.mapping_report
updated_document = kernel_v10_document_to_contract(native_document)
```

The adapter is exported lazily so earlier v0.4.0–v0.9.0 workflows do not acquire a v1.0.0 PYTHONPATH requirement merely because this adapter exists.

## Mapping behavior

- Projects Context records only when the required ID/kind are supported and every explicitly supplied parent, Source, or agent reference resolves in its corresponding record collection.
- Parent references target Context; Source references target Source; agent references target Referent. No reference target is inferred from an ID string.
- All nine standardized Context kinds are projected exactly. Unknown future kinds remain canonical-only.
- Optional name and metadata are preserved. Unknown record properties remain in the canonical envelope and produce PARTIAL mapping diagnostics.
- A dangling explicit link or unsupported required kind keeps the complete Context record canonical-only; it is never projected with the invalid link silently removed.
- Native edits merge only into Context records. All other record families, unknown Context fields, and document sidecars remain canonical.
- Export rejects a modified canonical snapshot and validates the complete document when validation is enabled.

## Semantic safeguards

1. Context identity remains its opaque Context ID.
2. Parent, Source, and agent links remain distinct typed reference spaces.
3. UNKNOWN remains distinct from all other Context kinds.
4. Context kind does not establish truth or authorize scope propagation.
5. No context inheritance, transitive closure, attitude interpretation, truth evaluation, or automatic assertion-status transition is performed.
6. Unsupported and dangling canonical fields are never silently dropped, defaulted, or coerced.
7. The adapter does not claim that a Context record makes its expressions true in that Context.
8. All non-Context record families remain canonical-only in this adapter and are preserved in the canonical envelope.

## Coverage boundary

Context is the only record family projected by this adapter. Sources, Referents, Mentions, Expressions, Assertions, Evidence, Definitions, expression relations, unresolved items, derivations, validation metadata, mapping metadata, and extensions remain canonical-only. This adapter does not claim a unified runtime or full document-level interoperability across all record families. Existing v0.4.0–v0.9.0 adapters remain separate and unchanged.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.0.0 python -m unittest discover -s tests -p "test_python_kernel_v10_document_adapter.py" -v
```
