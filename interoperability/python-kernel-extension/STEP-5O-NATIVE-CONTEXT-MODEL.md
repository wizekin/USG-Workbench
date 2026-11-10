# Phase 1 Step 5O — Native Context model v1.0.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_context_v10` 1.0.0  
**Scope:** Native Context record model and conformance tests only. The document adapter is a separate subsequent step.

## Why Context is a distinct record family

A Context scopes semantic content to a declared interpretive setting. It may describe the actual world, fiction, a hypothetical situation, a historical belief, a domain model, an attitude, a conditional setting, or a negated setting. A context is not an assertion, a truth value, or proof that its contents hold in the actual world.

## Native fields

- Opaque Context ID.
- Required explicit Context kind, preserving all nine USG-SEM/1.0 values: `WORLD`, `FICTION`, `HYPOTHETICAL`, `HISTORICAL_BELIEF`, `DOMAIN_MODEL`, `ATTITUDE`, `CONDITIONAL`, `NEGATED`, and `UNKNOWN`.
- Optional typed parent Context reference.
- Optional typed Source reference.
- Optional typed agent Referent reference.
- Optional exact name string.
- Optional metadata object, retained as descriptive opaque JSON data.

Reference spaces are explicit: parent links target CONTEXT, source links target SOURCE, and agent links target REFERENT. IDs are opaque and are never interpreted by their spelling.

## Governing invariants

1. Context identity is its opaque Context ID, never its name, kind, parent, or metadata.
2. All standardized Context kinds remain distinct; UNKNOWN is not replaced by WORLD or another convenient default.
3. Parent, Source, and agent links retain separate typed reference spaces.
4. Missing optional links remain absent. No parent, agent, or Source is inferred.
5. Context nesting is represented only by an explicit parent reference; no transitive closure or scope propagation is performed.
6. A context label or kind does not establish that an embedded proposition is true.
7. Context metadata is descriptive data and does not override standardized fields.
8. The model does not resolve references against a document; that is the responsibility of the document adapter.
9. The model performs no truth evaluation, attitude interpretation, context inheritance, entailment, or automatic status transition.
10. No arbitrary context-count or nesting-depth semantic limits are introduced.

## Compatibility boundary

- Python v0.4.0–v0.9.0 packages remain unchanged.
- USG-SEM/1.0 and its JSON Schema remain unchanged.
- Workbench v0.5.4, archives, historical baselines, and existing Node.js workflow/action versions remain unchanged.
- This is a model-only step; it does not claim Context document projection or full document interoperability.
- No human-review gate, silent coercion, or semantic-complexity cap is introduced.

## Tests

Run from repository root:

```bash
PYTHONPATH=implementations/python-kernel/v1.0.0 python -m unittest discover -s implementations/python-kernel/v1.0.0/tests -v
```
