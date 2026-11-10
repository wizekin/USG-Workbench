# USG Deterministic Grounding Services v1.0.0

**Package:** `USG-GROUNDING/1.0.0`  
**Input profile:** `USG-SEM/1.0`  
**Rule execution:** Not included or enabled.

This package resolves explicit typed references, definition identity/version, mention-to-referent links, assertion contexts, and expression scope paths. It does not infer identity from labels, select among ambiguous definitions, transfer contexts, flatten operator scope, or execute rules.

## API

- `GroundingIndex(document)` validates the canonical document against the USG-SEM/1.0 schema and builds deterministic collection indexes.
- `resolve_reference(expected_type, reference_id)` resolves only within the declared record family.
- `resolve_definition(type, id, version=...)` requires exact record versions for concepts/frames. Roles/relations have no per-record version in USG-SEM/1.0 and therefore require an exact catalogue release/scope when versioned grounding is requested.
- `find_definition_candidates_by_label(type, label)` is a discovery-only operation. Even one matching label does not resolve identity.
- `resolve_mention_referent(mention_id)` follows only explicit Mention.referentRef and preserves UNKNOWN/UNRESOLVED/AMBIGUOUS/CONFLICTING states.
- `resolve_assertion_context(assertion_id)` requires an exact contextRef; it never assumes WORLD from a missing reference.
- `resolve_context_path(context_id)` follows explicit parentRef links and detects cycles.
- `resolve_scope(root_expression_id, target_expression_id)` returns the exact ordered operand path; multiple paths remain ambiguous, opaque paths unsupported, and cycles invalid.
- `inspect_compact_benchmark_snapshot(fixture)` preserves Step 2.2 compact snapshots and reports missing canonical fields. It never manufactures assertion status or a canonical document.

Every result includes status, target type/ID, candidate references, diagnostics, and document-snapshot provenance.

## Status meanings

`RESOLVED`, `UNRESOLVED`, `AMBIGUOUS`, `CONFLICTING`, `UNKNOWN`, `UNSUPPORTED`, and `INVALID_INPUT` remain distinct. A failed lookup never falls back to a label or another record type.

## Tests

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_grounding.py" -v
```
