# Phase 1 Step 5N — Evidence document adapter v0.9.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python Evidence v0.9.0  
**Scope:** Document import/projection, mapping diagnostics, loss-preserving export, and adapter conformance tests. The canonical schema and native model are unchanged.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v09,
    kernel_v09_document_to_contract,
)

native_document = document_to_kernel_v09(contract_document)
mapping = native_document.mapping_report
updated_document = kernel_v09_document_to_contract(native_document)
```

The adapter is exported lazily so earlier v0.4.0–v0.8.0 workflows do not acquire a v0.9.0 PYTHONPATH requirement merely because this adapter exists.

## Mapping behavior

- Projects an Evidence record only when its Source reference resolves and its span uses the normative zero-based, end-exclusive Unicode code-point convention with a matching Source reference.
- Requires exact quote text and recognized alignment/support status values. Unknown required status values keep the complete Evidence record canonical-only.
- Projects ordered/repeated supporting-rule references without sorting, deduplication, or interpretation.
- Projects optional native verification meaning as descriptive metadata only.
- Unknown Evidence properties and unknown span properties remain in the canonical envelope and are reported as PARTIAL; malformed optional rule-reference metadata is not coerced.
- A dangling Source reference or invalid required span prevents native projection of that Evidence record.
- Native edits merge field-by-field into Evidence records only. Other record families, unknown fields, and document sidecars remain in the canonical envelope.
- Export rejects a modified canonical snapshot rather than merging native edits into stale data.

## Semantic safeguards

1. Evidence identity remains its opaque Evidence ID.
2. Source alignment and semantic-support status are independent axes.
3. EXACT records textual alignment only; it does not establish entailment, corroboration, or objective truth.
4. The adapter does not recompute, upgrade, or infer either standardized status.
5. Source references are explicitly typed and must resolve in the canonical Sources collection.
6. Span Source must match the Evidence Source. Offsets remain zero-based, end-exclusive Unicode code-point offsets.
7. Rule references remain opaque strings because USG-SEM/1.0 does not define a first-class rule-record collection.
8. Ordered and repeated rule references remain ordered and repeated.
9. Unknown, dangling, or unsupported canonical fields are never silently dropped, defaulted, or coerced.
10. No Evidence entailment engine, truth evaluation, evidence ranking, inference, or automatic status transition is implemented.

## Coverage boundary

Evidence is the only record family projected by this adapter. Sources, Referents, Mentions, Expressions, Assertions, Contexts, Definitions, expression relations, unresolved items, derivations, validation metadata, mapping metadata, and extensions remain canonical-only in this adapter and are preserved in the canonical envelope.

This adapter does not claim a unified runtime or full document-level interoperability across all record families. Existing v0.4.0–v0.8.0 adapters remain separate and unchanged.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v0.9.0 python -m unittest discover -s tests -p "test_python_kernel_v09_document_adapter.py" -v
```
