# Phase 4 — Step 4.9: Semantic Resource and Association Registry

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Registry contract:** `semantic-resource-registry/0.1.0`

The registry tracks immutable versioned descriptors for lexical, grammar, semantic-frame, discourse, model, and other resources. Descriptors include a content digest and provenance. Registry manifests are deterministic and content-addressed.

Associations are stored separately from definitions and identities. They are explicitly provisional and retain source/target refs, relation kind, weight, observation count, and provenance. The API can rank associations by weight and usage count, but cannot promote an association into a definition, equivalence, or identity. Updating the registry creates a new registry version.

Tests cover manifest digests, resource versioning, association ranking, duplicate IDs, and rejection of out-of-range weights or non-provisional statuses.
