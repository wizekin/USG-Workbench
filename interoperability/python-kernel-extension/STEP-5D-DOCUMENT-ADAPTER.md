# Phase 1 Step 5D — kernel v0.5.0 document-level boundary

**Status:** implementation candidate; automated conformance pending  
**Kernel:** Python 0.5.0  
**Interchange:** USG-SEM/1.0 (unchanged)  
**Legacy boundary:** v0.4.0 document adapter and reverse serializer remain unchanged

## Objective

Integrate the Step 5C expression-graph adapter into a complete USG-SEM/1.0 document import/export boundary. This step makes a full canonical document available alongside native v0.5.0 expression roots. It does not claim that the remaining document record families have native v0.5.0 equivalents.

## Public API

```python
from interoperability.python_adapter import (
    document_to_kernel_v05,
    kernel_v05_document_to_contract,
)

imported = document_to_kernel_v05(contract_document)
native_roots = imported.expression_roots
report = imported.mapping_report
updated_contract = kernel_v05_document_to_contract(imported)
```

- `document_to_kernel_v05(document, validate=True, schema_path=...)` validates the canonical document, verifies that the active `usg` package is exactly 0.5.0, and projects the declared `rootExpressionRefs` through the Step 5C adapter.
- `KernelV05Document` retains the complete canonical document, its digest, the native graph, per-record-family coverage, and diagnostics.
- `kernel_v05_document_to_contract(imported, validate=True, schema_path=...)` serializes the current native expression graph and reconstructs the full document envelope.

## Native and canonical-only boundaries

**Native in this step:** supported expression roots and their reachable expression DAG nodes, including native `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER` constructors.

**Canonical-only and explicitly reported:** sources, referents, mentions, assertions, evidence, contexts, definitions, expression relations, unresolved items, derivations, validation records, mapping metadata, and extensions. This is deliberate: Step 5D does not invent v0.5.0 record adapters or assume that v0.4.0 record behavior is automatically a v0.5.0 contract.

Expressions that are not reachable from `rootExpressionRefs` remain canonical-only. Unknown operators represented as `OPAQUE` are preservation projections and remain PARTIAL/inference-ineligible. Invalid known constructions remain canonical-only and are reported; they are not relabelled as OPAQUE.

## Reverse serialization and identity

- Current native Nodes are serialized; the input graph is not blindly replayed as a substitute for native serialization.
- Original expression IDs are retained only for unchanged native object identities.
- Edited/replaced/new native nodes receive fresh deterministic `py05:node:n` IDs. The original canonical record remains preserved if it is no longer represented by a native object.
- Shared DAG identity and operand ordering are preserved by the Step 5C graph serializer.
- All non-expression document collections, document metadata, and canonical-only expressions are retained.
- Export rejects a mutated canonical snapshot rather than silently merging potentially stale record data.
- Optional schema/cross-record validation runs after serialization.

## Mapping report

The document-level report identifies target version 0.5.0, aggregates unmapped/partial references, and provides per-collection status. A record may be preserved losslessly in the canonical envelope while remaining UNMAPPED as a native kernel record. Those are separate claims.

## Compatibility and non-goals

- USG-SEM/1.0 and its JSON Schema are unchanged.
- Workbench v0.5.4, Python kernel v0.4.0, archives, and historical implementation baselines are unchanged.
- Existing v0.4.0 document import/export APIs and tests remain unchanged.
- No guessed native source/assertion/context/evidence/definition adapters.
- No arbitrary semantic item/depth/operand caps.
- No human-review gate.
- No Node.js workflow/action version changes.

## Automated conformance

The Step 5D suite covers complete-document import/export, v0.5.0 expression projection, canonical-only record preservation, native graph edits, immutable snapshot enforcement, unreachable expression preservation, and invalid-document rejection. Existing Step 5C graph tests, v0.4.0 document/reverse tests, round-trip conformance, and the complete v0.5.0 kernel suite continue to run.
