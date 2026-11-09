# USG interoperability

This directory contains explicit, versioned adapters and conformance work between the distinct USG implementation lines and the canonical semantic contract.

Mappings must be exact and documented. Unsupported or lossy mappings must be reported as partial or unsupported; do not silently coerce, flatten, or discard semantic content. No full interoperability is claimed merely because the implementations are stored in this repository.

## Current Phase 1 work

- [Predicate-to-frame registry 1.0.0](predicate-frame-registry/README.md)
- Registry data: [v1.0.0.json](predicate-frame-registry/v1.0.0.json)
- Baseline pair: Workbench v0.5.4 → Python reference kernel v0.4.0
- Initial result: one conditional exact mapping (`CLOSES/CLOSED` → `CLOSE@1`); other reviewed predicates are explicitly non-mapped.

This registry covers predicate/frame identity and role correspondence only. Operators, scopes, nested propositions, document metadata, and round-trip adapters remain separate Phase 1 tasks.
