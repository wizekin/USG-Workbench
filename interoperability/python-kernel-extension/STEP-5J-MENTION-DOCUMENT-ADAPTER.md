# Phase 1 Step 5J — USG-SEM/1.0 ↔ Python Mention model v0.7.0 document adapter

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_discourse_v07` 0.7.0 (unchanged)  
**Previous identity adapter:** v0.6.0 Referent adapter (unchanged)

## Objective

Add a separate document boundary that projects exact Mention occurrence fields into the independently versioned v0.7.0 model. The complete canonical document remains authoritative, and only Mention records are eligible for native edits.

## Public API

- `document_to_kernel_v07(document, validate=True)`: validate and import the complete document, then project Mentions.
- `kernel_v07_document_to_contract(imported, validate=True)`: merge changed native Mention fields into the retained canonical Mention records and validate the complete result.
- `KernelV07Document`: canonical snapshot, native Mention records, per-record snapshots, mapping coverage, and diagnostics.

The APIs are lazily exported from `interoperability.python_adapter`. The v0.7.0 model is loaded in isolation when needed, so existing v0.4.0/v0.5.0 workflows do not need a new global PYTHONPATH.

## Exact Mention projection

- Opaque Mention `id` and exact `surfaceText`.
- `resolutionStatus` only for the exact v0.7.0 enum values: LINKED, RESOLVED, UNRESOLVED, AMBIGUOUS, UNKNOWN.
- Optional `mentionType` as a string.
- `referentRef` only when it resolves to a declared Referent.
- `antecedentMentionRef` only when it resolves to a declared Mention.
- `antecedentReferentRef` only when it resolves to a declared Referent.
- `sourceSpan` only when its explicit Source exists, offsets are valid Unicode code-point bounds, and the exact source substring equals the Mention surface text.

The three link fields use separate typed reference spaces. No target type is guessed from an ID string.

## Partial mappings and preservation

- Each Mention reports LOSSLESS or PARTIAL status, mapped fields, and exact unmapped fields.
- Dangling references, unknown resolution statuses, invalid/misaligned source spans, and additional properties such as `nativeId` remain in the canonical record and are reported as unmapped.
- A canonical null or omitted optional field is not defaulted. Unchanged fields retain their original representation.
- All Sources, Referents, expressions, assertions, evidence, contexts, definitions, relations, unresolved items, derivations, and document metadata remain canonical-only.
- Equal surface text does not merge occurrences. Multiple Mentions may link to the same Referent. Antecedent Mention and antecedent Referent links remain independent.
- No antecedent, coreference, or Referent assignment is inferred.

## Export and validation

- Export rejects mutation of the retained canonical snapshot.
- Native edits are merged only into the corresponding Mention records; unrelated records and unknown sidecar fields are preserved.
- Changed links require explicit correctly typed references.
- Export validates the complete USG-SEM/1.0 document, including schema constraints, reference integrity, and source-span bounds.
- Source offsets are zero-based, end-exclusive Unicode code-point positions. A span whose source substring does not exactly match the Mention surface text is not projected.

## Conformance

The dedicated tests cover typed links, repeated surface text with distinct occurrence IDs, shared Referents, dangling links, unknown statuses, Unicode code-point alignment, unsupported sidecars, Mention-only edits, stale snapshots, and full-document validation.

Run:

```bash
python -m pip install "jsonschema>=4.18,<5"
PYTHONPATH=implementations/python-kernel/v0.7.0 python -m unittest discover -s implementations/python-kernel/v0.7.0/tests -v
PYTHONPATH=implementations/python-kernel/v0.7.0 python -m unittest discover -s tests -p "test_python_kernel_v07_document_adapter.py" -v
```

## Scope exclusions

No changes to USG-SEM/1.0, the v0.7.0 native model, v0.6.0 identity model or adapter, v0.5.0 kernel/adapter, Workbench v0.5.4, archives, immutable baselines, or existing Node.js action versions. No human-review gate or arbitrary semantic complexity limit is introduced.
