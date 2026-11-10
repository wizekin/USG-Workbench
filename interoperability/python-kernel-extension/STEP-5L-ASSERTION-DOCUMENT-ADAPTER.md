# Phase 1 Step 5L — Assertion document adapter v0.8.0

**Canonical contract:** USG-SEM/1.0  
**Native model:** Python Assertion v0.8.0

## API

```python
from interoperability.python_adapter import document_to_kernel_v08, kernel_v08_document_to_contract
native_document = document_to_kernel_v08(contract_document)
mapping = native_document.mapping_report
updated_document = kernel_v08_document_to_contract(native_document)
```

The adapter is exported lazily so existing v0.4.0–v0.7.0 workflows do not require the v0.8.0 package on their import path.

## Mapping behavior

- Projects an Assertion only when its required Expression reference resolves and required origin, epistemic status, commitment, evaluation-context kind, and lifecycle values exactly match v0.8.0.
- Projects optional attribution, Source, Evidence list, Context, and Definition references only when every supplied reference resolves in the correct canonical collection.
- Evidence order and repetition are preserved. A partly resolvable Evidence list is not projected as a subset.
- alternativeGroupRef remains canonical-only: USG-SEM/1.0 has no first-class Alternative Group record collection.
- Unknown required enum values or a dangling required Expression reference keep the entire Assertion canonical-only. Unsupported optional fields make an otherwise representable Assertion PARTIAL.
- Extra evaluation-context properties remain canonical-only and are listed as unmapped.
- The complete canonical document remains authoritative. Native edits merge field-by-field into Assertion records only.

## Semantic safeguards

1. Assertion remains distinct from its referenced Expression.
2. Origin, epistemic status, commitment, evaluation context, and lifecycle are not inferred from one another.
3. SOURCE_ASSERTED is not objective truth; VERIFIED is not a confidence score.
4. Attribution, Source, Evidence, Context, and Definition references are typed and checked against their target collections.
5. A changed native reference must resolve in the correct collection or export fails.
6. No evidence entailment, truth evaluation, inference, automatic lifecycle transition, or Alternative Group interpretation is performed.
7. Unknown, dangling, and unsupported canonical fields are not coerced, dropped, or defaulted.
8. A modified canonical snapshot is rejected before native edits can be merged.

## Coverage boundary

Assertions are the only record family projected by this adapter. Sources, Referents, Mentions, Expressions, Evidence records, Context records, Definitions, expression relations, unresolved items, derivations, validation metadata, mapping metadata, and extensions remain canonical-only in this adapter and are preserved in the canonical envelope.

This does not claim that all records are natively represented or that the full USG runtime is integrated. Existing expression, Referent, and Mention adapters remain separate and unchanged.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v0.8.0 python -m unittest discover -s tests -p "test_python_kernel_v08_document_adapter.py" -v
```
