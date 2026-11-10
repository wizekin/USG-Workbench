# USG interoperability

This directory contains explicit, versioned adapters and conformance work between the distinct USG implementation lines and the canonical semantic contract.

Mappings must be exact and documented. Unsupported or lossy mappings must be reported as partial or unsupported; do not silently coerce, flatten, or discard semantic content. No full interoperability is claimed merely because the implementations are stored in this repository.

## Current Phase 1 work

### Step 1 — predicate-to-frame registry

- [Predicate-to-frame registry 1.0.0](predicate-frame-registry/README.md)
- Registry data: [v1.0.0.json](predicate-frame-registry/v1.0.0.json)
- Initial result: one conditional exact mapping (`CLOSES/CLOSED` → `CLOSE@1`); other reviewed predicates are explicitly non-mapped.

### Step 2 — operator and scope registry

- [Operator and scope registry 1.0.0](operator-scope-registry/README.md)
- Registry data: [v1.0.0.json](operator-scope-registry/v1.0.0.json)
- Covers negation, modal force/flavor, quantifier structure, logical connectives, and explicit graph-scope conversion requirements.
- Exact/conditional mappings are separated from ambiguous, partial, and unsupported readings.

### Step 3 — document-level Python adapter (completed)

- [Python adapter package](python_adapter/README.md)
- Canonical contract: [USG-SEM/1.0](../specifications/USG-SEM-1.0.md)
- JSON Schema: [usg-sem-1.0.schema.json](../specifications/usg-sem-1.0.schema.json)
- Preserves the entire canonical document for exact export while projecting only source records, supported SemIR roots and assertions that have exact Python kernel 0.4.0 equivalents.
- Referents, mentions, evidence assessments, contexts, definitions, expression relations, unresolved items, derivations, validation metadata and extensions remain canonical-only and are explicitly reported as partial/unmapped where no exact native model exists.
- No SQLite migration, Workbench runtime integration, or changes to either immutable implementation baseline are included.

### Step 4 — round-trip conformance (active)

- [Round-trip conformance design and verified gap inventory](round-trip-conformance/README.md)
- Establishes the required four-boundary conversion cycle and semantic invariants.
- Initial audit confirms that a Workbench-to-contract adapter and a Python-projection-to-contract serializer are still missing. Step 3's unchanged-snapshot export is not treated as a reverse serializer.
- The Workbench baseline uses UTF-16 string offsets; USG-SEM requires Unicode code-point offsets. This conversion must be explicit and tested.

The registries and adapter target the immutable baseline pair: Workbench v0.5.4 and Python reference kernel 0.4.0. They do not yet establish complete runtime interoperability.
