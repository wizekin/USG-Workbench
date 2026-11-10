# Python document adapters — USG-SEM/1.0

This package contains separate, versioned adapters for the canonical USG-SEM/1.0 document and Python kernel model generations. Each adapter retains the complete canonical document as the authoritative preservation envelope. A family-specific adapter projects only the records and fields its native model can represent exactly.

## Existing v0.4.0 adapter

The original adapter projects supported Sources, SemIR expression roots, and Assertions that have exact Python kernel 0.4.0 equivalents. It retains unsupported record families in the canonical envelope and exposes the original import/export boundary. See the legacy API and tests below.

## Versioned adapters

### Python kernel v0.5.0

- Expression graph and document APIs: `document_to_kernel_v05()`, `kernel_v05_document_to_contract()`.
- Preserves graph identity, root structure, operand order, and unsupported canonical records.

### Python Referent identity v0.6.0

- APIs: `document_to_kernel_v06()`, `kernel_v06_document_to_contract()`.
- Projects exact Referent identity fields and reports unsupported identity details per record/field.

### Python Mention v0.7.0

- APIs: `document_to_kernel_v07()`, `kernel_v07_document_to_contract()`.
- Projects Mention occurrence records without inferring coreference or antecedents.

### Python Assertion v0.8.0

- APIs: `document_to_kernel_v08()`, `kernel_v08_document_to_contract()`.
- Projects exact Assertion fields and resolvable typed references; provides per-Assertion/per-field mapping coverage.
- Preserves the independent origin, epistemic status, commitment, evaluation-context, and lifecycle axes.
- Keeps Alternative Group references canonical-only because USG-SEM/1.0 has no corresponding first-class record collection.
- Native edits merge only into Assertion records; all other families and unsupported fields remain in the canonical envelope.

All versioned adapter exports are lazy where required so earlier adapter workflows do not acquire new PYTHONPATH requirements merely because later models exist.

## Loss-preservation rules

- Unsupported, unknown, and dangling fields are retained in the canonical envelope and reported; they are not silently coerced or dropped.
- Required native fields that cannot be represented exactly keep that record canonical-only.
- A changed native reference must have the expected explicit reference space and resolve in the matching canonical collection.
- Ordered references and repeated references remain ordered and repeated.
- Export rejects a modified canonical snapshot rather than merging native edits into stale data.
- A PARTIAL adapter report does not mean the canonical document itself has been lost; the full canonical payload remains available.

## Validation

Install `jsonschema>=4.18,<5` for full USG-SEM/1.0 schema validation.

Run the v0.8.0 Assertion and v0.9.0 Evidence model and adapter suites:

```bash
PYTHONPATH=implementations/python-kernel/v0.8.0 python -m unittest discover -s implementations/python-kernel/v0.8.0/tests -v
PYTHONPATH=implementations/python-kernel/v0.8.0 python -m unittest discover -s tests -p "test_python_kernel_v08_document_adapter.py" -v
PYTHONPATH=implementations/python-kernel/v0.9.0 python -m unittest discover -s implementations/python-kernel/v0.9.0/tests -v
PYTHONPATH=implementations/python-kernel/v0.9.0 python -m unittest discover -s tests -p "test_python_kernel_v09_document_adapter.py" -v
```

The canonical schema is `specifications/usg-sem-1.0.schema.json`.


### Python kernel v1.0.0–v1.4.0

- Context v1.0.0: `document_to_kernel_v10()`, `kernel_v10_document_to_contract()`.
- ExpressionRelation v1.1.0: `document_to_kernel_v11()`, `kernel_v11_document_to_contract()`.
- UnresolvedItem v1.2.0: `document_to_kernel_v12()`, `kernel_v12_document_to_contract()`.
- Derivation v1.3.0: `document_to_kernel_v13()`, `kernel_v13_document_to_contract()`.
- Definitions v1.4.0: `document_to_kernel_v14()`, `kernel_v14_document_to_contract()`.

### Composed adapter v1.5.1

- APIs: `document_to_kernel_v15()`, `kernel_v15_document_to_contract()`.
- Uses the corrected UnresolvedItem v1.2.1 adapter with typed Expression `scopeRef` and typed Evidence references.
- Composes the v0.5.0–v1.4.0 family-specific adapters over one immutable canonical snapshot.
- Merges only the collections owned by each adapter, preventing cross-family edits from overwriting one another.
- Aggregates per-family mapping coverage and performs final cross-family span checks after composition.
- The composed adapter does not replace or renumber any of the individual model packages.
