# USG specifications

This directory contains normative, versioned USG contracts, schemas, and semantic invariants. Specifications should be implementation-neutral where possible. Implementation-specific behavior belongs with the corresponding implementation or in an explicitly scoped compatibility document.

## Current specifications

- [Predicate-to-frame registry schema 1.0](predicate-frame-registry-1.0.schema.json) validates the versioned cross-implementation predicate/frame registry.
- [Phase 6 interpretation envelope schema 0.3.0](usg-interpret-0.3.0.schema.json) defines the versioned processing result envelope.
- [Phase 6 interpretation graph schema 0.3.0](usg-interpret-expression-graph-0.3.0.schema.json) defines source-grounded graph nodes, edges, and span records.
- [Phase 6 predicate-frame and semantic-role registry schema 0.3.0](usg-frame-registry-0.3.0.schema.json) defines versioned role definitions, frame slots, valency, and language-specific realization links.
- [Phase 6 candidate bilingual lexical and morphology resource schema 0.3.0](phase6-lexical-resource-0.3.0.schema.json) validates provenance-bearing English/MSA Arabic forms, exact fixture evidence, and bounded morphology patterns.

- [Phase 6 candidate predicate/argument construction rules schema 0.3.0](phase6-predicate-argument-rules-0.3.0.schema.json) validates versioned language-specific patterns and frame references.

The canonical semantic interchange contract and schema are maintained separately. Do not infer that an absent specification has already been implemented by either runtime.
