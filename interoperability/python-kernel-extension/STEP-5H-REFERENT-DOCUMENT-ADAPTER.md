# Phase 1 Step 5H — USG-SEM/1.0 ↔ Python identity model v0.6.0 document adapter

**Target model:** `usg_identity_v06` 0.6.0  
**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Previous adapter:** Python kernel v0.5.0 document adapter (unchanged)

## Objective

Add a separate document boundary that projects USG-SEM Referent records into the versioned v0.6.0 identity model while retaining the complete canonical document as the authoritative envelope. This step does not change the v0.5.0 adapter or claim that every Referent field has a native equivalent.

## Public API

- `document_to_kernel_v06(document, validate=True)`: import and project supported Referents.
- `kernel_v06_document_to_contract(imported, validate=True)`: merge current native Referent edits into the retained canonical document.
- `KernelV06Document`: holds the canonical snapshot, native Referent projections, per-record snapshots, mapping report, and diagnostics.

The APIs are exported from `interoperability.python_adapter`.

## Exact native projections

The adapter uses opaque external IDs and typed references. It projects the following fields only when their target and value are exact:

- Referent ID and display label; labels and aliases never establish identity.
- `semanticKind`, `number`, and `genericity` only for recognized contract enum values.
- `conceptRefs` as typed CONCEPT references only when each ID resolves to a declared concept definition.
- `identity.status` and `identity.scope` as independent optional axes.
- `identity.equivalenceRefs` as ordered REFERENT references only when each target exists. No symmetry, transitivity, or record merging is inferred.
- `identity.basis` as descriptive metadata.
- `introducedIn` WORLD without a context reference, or a supported non-WORLD kind with an explicit context reference that resolves to an expression NODE. Other target types remain canonical-only; the adapter does not guess a reference space.
- `sourceRef` as SOURCE and `sourceSpan` only when it refers to the same mapped source and its Unicode code-point offsets are within the exact source text.

## Partial mappings and preservation

- Each Referent has a `LOSSLESS` or `PARTIAL` status, a list of mapped field paths, and exact unsupported field paths.
- Unknown/additional fields, unsupported enum values, dangling references, and untyped introduction contexts remain in the canonical Referent and are listed as unmapped.
- Extra fields such as `cardinality`, `nativeId`, and `nativeType` are not coerced into unrelated v0.6.0 fields.
- All Sources, Mentions, expressions, assertions, evidence, contexts, definitions, relations, unresolved items, derivations, and document metadata remain in the canonical envelope in this step.
- Mention records and antecedent fields are never rewritten or inferred.

## Export and validation

- Export rejects mutation of the retained canonical snapshot.
- Native edits are merged into only the corresponding Referent records; unchanged fields retain their original representation, including omitted optional fields and unknown sidecar data.
- Export revalidates the complete USG-SEM/1.0 document. A source-span edit that exceeds the referenced source text is rejected.
- No dependent Mention, Evidence, or other record is silently shifted when a Referent label or span changes.

## Conformance

`tests/test_python_kernel_v06_document_adapter.py` covers exact identity projection, independent status/scope, explicit equivalence links, typed concept references, introduction-context typing, Unicode source spans, unsupported fields, dangling references, partial mapping, native edits, unchanged Mentions, absent-field preservation, stale snapshots, and full-document validation.

Run:

```bash
python -m pip install "jsonschema>=4.18,<5"
PYTHONPATH=implementations/python-kernel/v0.6.0 python -m unittest discover -s implementations/python-kernel/v0.6.0/tests -v
PYTHONPATH=implementations/python-kernel/v0.6.0 python -m unittest discover -s tests -p "test_python_kernel_v06_document_adapter.py" -v
```

## Scope exclusions

No changes to USG-SEM/1.0, Workbench v0.5.4, Python kernel v0.5.0, archives, immutable implementation baselines, or existing Node.js workflow/action versions. No human-review gate or arbitrary semantic complexity limit is introduced.
