# Phase 5 — Step 5.9: Persistent Semantic Resource Catalogue and Association Retrieval

**Status:** IMPLEMENTED CANDIDATE — acceptance pending exact-head CI  
**Catalogue contract:** `USG-RESOURCE-CATALOGUE/0.1.0`  
**Package:** `tools/usg_resource_catalogue_v0_1_0`  
**Persistence:** the same SQLite database file used by `CanonicalDocumentStore`

## 1. Deliverable

Step 5.9 adds an independently versioned SQLite resource catalogue for:

- lexical realizations;
- grammar patterns;
- semantic frames;
- discourse resources; and
- provisional associations.

The catalogue is an additive subsystem. It does not change `USG-SEM/1.0`, canonical document tables, the Phase 4 interpreter, or the Phase 5 interpretation artifacts.

## 2. Storage boundary

The caller supplies the existing canonical SQLite database path to `SQLiteResourceCatalogue`. The catalogue opens its own SQLite connection to that same file and creates only namespaced tables:

- `resource_catalogue_migrations`;
- `semantic_resource_snapshots`;
- `semantic_resource_heads`; and
- `semantic_resource_usage_events`.

It does not create a second database file or a second canonical semantic-document store. Resource snapshots are not USG-SEM documents and are never inserted into `documents` or `document_revisions`. The Phase 5.10 application integration will pass the same database path to both services.

SQLite transactions, foreign keys, WAL for file-backed databases, busy timeout, and full synchronous writes are used. The catalogue owns and closes only its own connection.

## 3. Resource identity, versioning, and provenance

Every resource snapshot has:

- a stable `resource_id`;
- a stable semantic `MAJOR.MINOR.PATCH` version;
- one declared resource class;
- non-empty provenance metadata;
- a JSON-object content payload;
- canonical UTF-8 JSON bytes; and
- a SHA-256 digest over the complete versioned envelope.

The envelope pins the catalogue contract version. Canonicalization sorts object keys and preserves array order and exact string content. NaN and non-JSON values are rejected.

A resource ID/version pair is immutable. Re-registering identical content is idempotent; attempting to write different content under an existing ID/version fails. A changed resource requires a new version. Database triggers also reject direct updates/deletes of snapshots and usage events.

Provenance is inspectable metadata, not an assertion that a resource is linguistically complete or externally authoritative. The catalogue does not download, execute, or trust resource content as code.

## 4. Active and secondary resources

A resource snapshot is secondary when first registered unless the caller explicitly activates it. Activation changes only the mutable head pointer; it never edits a snapshot.

- Each resource ID has at most one active version.
- Historical and secondary versions remain queryable.
- Activation uses compare-and-swap through `expected_active_version`.
- A stale activation request fails rather than silently replacing a newer head.
- The resource class cannot change across versions of one resource ID.

Retrieval can include or exclude secondary versions. Active versions sort first by default; remaining ties use deterministic resource ID and semantic-version ordering.

## 5. Usage and activation metadata

Usage is recorded as append-only events. Counts and last-use timestamps are derived by querying those events; no usage score is written into a resource snapshot.

For a retrieval time (t), last-use time (t_0), event count (n), and configured half-life (h), the catalogue computes:

[
A(t) = n \, e^{-\ln(2)\max(0,t-t_0)/h}
]

The default half-life is 30 days. Tests can supply a fixed time and half-life for reproducible results. The score is retrieval metadata only; it is not a calibrated probability, truth value, semantic confidence, identity score, entailment, or evidence of causal relation. It cannot promote an association or canonical definition.

## 6. Provisional association retrieval

Association resources use an explicit `associations` array. Each item requires a unique association ID and exact `source_ref`, `relation`, and `target_ref` strings. Optional fields are retained as attributes.

Retrieval filters only by exact supplied reference/relation fields and returns candidates marked:

- `status = PROVISIONAL`;
- `identity_resolution = false`.

No association automatically creates a concept, changes a canonical definition, merges mentions, resolves coreference, establishes entailment, or changes semantic history. Similarity search and learned promotion are not introduced by this step.

## 7. Integrity and deterministic behavior

The catalogue provides:

- canonical envelope and SHA-256 verification on reads;
- resource-row/envelope identity consistency checks;
- active-head foreign-key and resource-class checks;
- whole-catalogue integrity reporting;
- append-only snapshot and usage-event constraints;
- deterministic active/secondary ordering; and
- deterministic usage ranking when the retrieval time is fixed.

Usage history is derived operational metadata. It may be rebuilt from usage events and never overrides resource content.

## 8. Acceptance tests

The dedicated Step 5.9 suite covers:

- immutable versions and idempotent retries;
- explicit activation and stale compare-and-swap rejection;
- active/secondary retrieval ordering;
- all five resource classes;
- required provenance, stable versions, and JSON payload validation;
- provisional association shape, exact filtering, and non-resolution guarantees;
- fixed-time decay calculations and snapshot digest stability;
- append-only usage and snapshot tamper detection;
- persistence across close/reopen; and
- coexistence with the existing canonical SQLite document-store tables in the same database file.

The Step 5.9 workflow also runs the Phase 5.2–5.8 regressions and frozen Phase 4 suite. The existing Phase 3 integrated exit workflow is triggered by Phase 5 test changes and verifies the shared SQLite/API/Kernel Lab baseline.

## 9. Explicit limits and deferred integration

This step does not yet import all bundled lexical/operator assets automatically, provide a general-purpose grammar/frame authoring interface, expose catalogue operations through the local API/CLI, or add Kernel Lab screens. Those are integration concerns for Step 5.10.

It also does not provide embeddings, approximate-nearest-neighbor search, automatic ontology induction, canonical-definition promotion, identity resolution, or unrestricted resource learning. Candidate ranking remains derived retrieval metadata.

## 10. Next step

After Step 5.9 passes its exact-head workflow and merges, begin **Step 5.10 — Integrated API, CLI, and Kernel Lab Expansion**. It will connect this catalogue to the existing local application using the same SQLite database path and expose only the already accepted artifacts and diagnostics.
