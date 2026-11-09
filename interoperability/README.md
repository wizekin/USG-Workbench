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

Both registries target the immutable baseline pair: Workbench v0.5.4 and Python reference kernel v0.4.0. They do not yet implement the complete document adapter or establish round-trip interoperability. Relation mappings, nested proposition arguments, document metadata, and end-to-end conversion remain separate Phase 1 tasks.
