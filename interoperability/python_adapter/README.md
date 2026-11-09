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
