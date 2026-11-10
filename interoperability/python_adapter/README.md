# Python document adapter — USG-SEM/1.0 → kernel 0.4.0

This adapter imports a complete USG-SEM/1.0 document while retaining the full
canonical document as the authoritative, loss-preserving interchange payload.

## Native projections

- Sources are projected to Python `Source` records only when their source type,
  trust tier, sensitivity, encoding, hash algorithm and offset convention have
  exact kernel equivalents.
- Supported expression roots are projected to immutable SemIR `Node` objects.
  Multiple roots share one memo, preserving common DAG subexpressions.
- Assertions are projected only when their expression, source, attribution,
  evidence, context, status and lifecycle fields can be represented exactly.

## Preserved canonical-only records

The adapter retains referents, mentions, evidence assessments, contexts,
expression relations, unresolved items, derivations, validation metadata,
definitions and extensions in the original document. It reports them as
unmapped/partial when kernel 0.4.0 has no exact record equivalent. In particular,
a mention is not a referent, a source span is not evidence entailment, and a
contract frame catalogue is not automatically a Python `FrameDef`.

## Round-trip boundary

`ImportedDocument.export_contract_document()` returns an exact copy of the
original document. It refuses export if the snapshot was modified, avoiding a
stale or lossy merge between mutable Python projections and the canonical data.
This step does not write to SQLite, merge stores, or modify kernel 0.4.0.

## Test

From repository root:

```bash
python -m unittest discover -s tests -p "test_document_adapter.py" -v
```

The schema is in `specifications/usg-sem-1.0.schema.json`. Install
`jsonschema>=4.18,<5` for full schema validation.

## Reverse serialization — Python kernel 0.4.0 → USG-SEM/1.0

The reverse boundary is exposed as:

```python
from interoperability.python_adapter import (
    document_to_python,
    python_to_contract_document,
)

imported = document_to_python(contract_document)
updated_contract = python_to_contract_document(imported)
```

The serializer traverses the current immutable SemIR `Node` objects and writes
an explicit USG-SEM expression graph (`id`, `op`, `sort`, ordered
`operandRefs`, `params`). It preserves shared object identity, multiple roots,
and operand order. It serializes the current `Source` and `Assertion`
projections rather than returning the original expression/source/assertion
records as a substitute.

The imported canonical snapshot remains the envelope and preservation source
for record classes that Python kernel 0.4.0 cannot represent natively. Such
records are carried forward unchanged and remain listed in the mapping report.
Unsupported original sources, expressions, assertions, and roots are retained;
they are not silently deleted.

### Annotation source identity

Python `Ann` stores offsets, rules, basis and language features, but does not
store `sourceRef`. The reverse serializer restores span source associations
only when the current offsets exactly match the imported canonical annotation.
If the spans change, it retains the native annotation in the namespaced
`org.usg.python-kernel.v0.4.0` extension and reports the expression as
`PARTIAL`. It never assumes that a span belongs to the primary source.

### Snapshot and scope boundaries

- A modified canonical snapshot is rejected; canonical-only records must not be
  merged from a stale or user-mutated envelope.
- Source genre and native-only assertion metadata are retained only as explicit
  namespaced extension data or reported unsupported.
- The serializer does not invent referents, mentions, evidence, contexts,
  definitions, relations, unresolved records, or derivations.
- `LOSSLESS` is not claimed when canonical-only records remain outside the
  Python kernel projection.
- This is a serialization boundary, not a claim of semantic correctness or the
  completion of the Workbench → Python → Workbench round trip.

Run:

```bash
python -m unittest discover -s tests -p "test_python_reverse_serializer.py" -v
```
