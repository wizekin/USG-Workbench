# Phase 1 Step 5T1 — Typed UnresolvedItem references v1.2.1

**Correction to:** Step 5S/5T UnresolvedItem model and adapter  
**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** Python UnresolvedItem v1.2.1

## Contract correction

The USG-SEM/1.0 document validator defines `scopeRef` as an Expression reference. It must resolve against the document's Expressions collection. The previous v1.2.0 model treated it as an untyped opaque string; that representation was too weak for the canonical contract.

This patch provides the corrected v1.2.1 native model and adapter. It does not rewrite the historical v1.2.0 package.

## Typed fields

- `scopeRef` → typed EXPRESSION reference.
- `evidenceRefs` → ordered/repeated typed EVIDENCE references.
- `candidateRefs` → opaque ordered strings; the canonical contract does not define one candidate record family.

The adapter projects a record only when its explicit scope and Evidence references resolve. Dangling references keep the complete record canonical-only with diagnostics. Native edits are checked against the corresponding target collection before export.

## Compatibility

- Python v1.2.0 remains available as the historical first implementation.
- Python v1.2.1 is the corrected contract-aligned model.
- USG-SEM/1.0, the JSON Schema, Workbench v0.5.4, and earlier packages remain unchanged.
- The composed document adapter is updated separately to use v1.2.1.

## Tests

```bash
PYTHONPATH=implementations/python-kernel/v1.2.1 python -m unittest discover -s implementations/python-kernel/v1.2.1/tests -v
PYTHONPATH=implementations/python-kernel/v1.2.1 python -m unittest discover -s tests -p "test_python_kernel_v121_document_adapter.py" -v
```
