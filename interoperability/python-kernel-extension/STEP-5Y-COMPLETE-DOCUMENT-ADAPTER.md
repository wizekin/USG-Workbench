# Phase 1 Step 5Y — Complete USG-SEM/1.0 document adapter v1.5.1

**Canonical contract:** USG-SEM/1.0  
**Composed adapter:** Python kernel interoperability v1.5.0  
**Scope:** One public document boundary composed from all existing family-specific adapters.

## API

```python
from interoperability.python_adapter import (
    document_to_kernel_v15,
    kernel_v15_document_to_contract,
)

native_document = document_to_kernel_v15(contract_document)
coverage = native_document.mapping_report
updated_document = kernel_v15_document_to_contract(native_document)
```

## Composition

The composed adapter delegates to the existing, separately versioned family adapters:

| Canonical family | Native adapter |
|---|---|
| Sources and expression graphs | Python kernel v0.5.0 |
| Referents | Identity model v0.6.0 |
| Mentions | Discourse model v0.7.0 |
| Assertions | Assertion model v0.8.0 |
| Evidence | Evidence model v0.9.0 |
| Contexts | Context model v1.0.0 |
| Expression relations | Relation model v1.1.0 |
| Unresolved items | Typed UnresolvedItem model v1.2.1 |
| Derivations | Derivation model v1.3.0 |
| Definitions (Concepts, Frames, Roles, Relations) | Definitions model v1.4.0 |

The composed API does not collapse the independently versioned models into one schema or silently upgrade any earlier model. It keeps each family adapter's own native representation and mapping report.

## Merge and preservation rules

- Every family adapter receives the same immutable canonical snapshot.
- Export asks each adapter to serialize its current native state, then merges only the collection(s) owned by that adapter.
- A family adapter cannot overwrite another family's native edits.
- Validation, mapping metadata, extensions, unsupported records, and unknown fields remain in the canonical envelope.
- A stale top-level snapshot is rejected before composition.
- The final document is schema-validated once after all family edits have been merged.

## Cross-family validation

After composition, source-linked spans are checked against the final Source records using zero-based, end-exclusive Unicode code-point offsets. Mention surface text must align exactly with its span. Evidence with EXACT alignment must quote the exact source slice; non-EXACT evidence statuses remain distinct and are not promoted.

## Coverage semantics

The top-level mapping report aggregates the family-specific coverage reports. LOSSLESS means all tested family records have exact native projections. PARTIAL means at least one record remains canonical-only or has unsupported fields. PARTIAL does not mean the canonical document has been discarded.

## Non-goals

This step does not introduce a new ontology, truth engine, entailment engine, general relation reasoner, candidate resolver, autonomous definition learner, or new semantic complexity cap. It does not change USG-SEM/1.0, the Workbench v0.5.4 baseline, Python v0.4.0, or earlier versioned model packages.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v0.5.0 python -m unittest discover -s tests -p "test_python_kernel_v15_document_adapter.py" -v
```
