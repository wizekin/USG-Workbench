# Phase 3 Step 3.1 — Canonical Graph-Store Contract

**Status:** CONTRACT DEFINED — implementation is Step 3.2.
**Profile:** USG-SEM/1.0 remains the canonical semantic document contract.
**Storage package:** to be introduced additively in Step 3.2; no legacy baseline is modified.

## 1. Purpose

Define how complete USG-SEM/1.0 semantic documents are persisted, versioned, retrieved, verified, and indexed. This contract prevents the storage layer from turning the graph into flattened claims or creating a second, conflicting semantic authority.

## 2. Authority and data model

### 2.1 Canonical snapshot is authoritative

The complete, schema-valid USG-SEM document is stored as one canonical JSON snapshot. The snapshot includes every required collection and field: sources, definitions, referents, mentions, expressions, ordered roots, assertions, evidence, contexts, expression relations, unresolved items, derivations, validation, mapping, and namespaced extensions.

Relational tables may index the canonical document for efficient retrieval, but they are derived projections. They must be rebuildable from the snapshot and must never be used to silently reconstruct missing semantic content.

### 2.2 Document-local identity

All IDs retain their USG-SEM document-local meaning. A record ID from one document is not globally unique and must not be treated as such. Store keys use the document identity plus the record ID and record family. No cross-document entity merge, referent equivalence, or alias-based identity resolution is introduced by storage.

### 2.3 Immutable revisions

A stored revision is immutable. A changed document is stored as a new revision linked to its predecessor. The store maintains a current-revision pointer, updated atomically with the new revision. Historical snapshots remain retrievable and verifiable. Deletion and destructive in-place editing are outside this contract.

### 2.4 Canonical serialization

Canonical bytes are UTF-8 JSON with:

- object keys sorted recursively and deterministically;
- compact separators with no insignificant whitespace;
- ensure_ascii=false so Unicode is represented without unnecessary escaping;
- array order preserved exactly;
- string values preserved exactly, with no Unicode normalization, trimming, punctuation rewriting, or whitespace normalization;
- numeric and boolean types preserved;
- no field omission or default insertion unless a future, separately versioned canonicalization profile explicitly defines it.

The canonicalization profile itself is versioned and recorded. The initial profile identifier is USG-CANONICAL-JSON/1.0.0.

The SHA-256 digest is calculated over the exact canonical UTF-8 bytes. The source text hashes already present in USG-SEM remain independently validated against the exact source UTF-8 text; a document hash is not a replacement for source hashes.

### 2.5 Schema validation

Before persistence, the full document must validate against the pinned USG-SEM/1.0 JSON Schema and the Phase 2 grounding/reference checks. Validation must not mutate the document. A structurally invalid document is rejected with stable diagnostics.

On read, the store verifies the snapshot digest and schema/profile identity before returning it. Hash mismatch, unsupported canonicalization version, unavailable schema version, and malformed JSON are distinct failures.

## 3. Logical storage layout

The implementation may refine physical table names, but must preserve these logical records:

| Record | Required data |
|---|---|
| documents | Stable document key, profile ID, current revision number, creation metadata |
| document_revisions | Document key, revision number, canonicalization profile, canonical JSON bytes, SHA-256, predecessor revision, created timestamp |
| expression_index | Document/revision key, expression ID, sort, semantic kind, operator/constructor, canonical path metadata |
| assertion_index | Document/revision key, assertion ID, expression reference, context, commitment, epistemic status |
| evidence_index | Document/revision key, evidence ID, source reference, span, alignment/support declarations |
| source_index | Document/revision key, source ID, exact source hash, language, source type |
| schema_migrations | Ordered migration version, stable migration name, application timestamp |

The canonical snapshot is the source of truth. Index tables can be deleted and rebuilt without changing the snapshot hash or semantic meaning.

The physical implementation must use parameterized SQL, foreign keys where appropriate, explicit transaction boundaries, and registered migration versions. It must not accept model-provided SQL or dynamically execute document content.

## 4. Write semantics

1. Validate the complete input document and all document-local references before opening the write transaction.
2. Canonicalize without mutating the caller's object.
3. Compute the canonical snapshot digest.
4. If the document key and revision already exist with the same digest, return an idempotent-existing result.
5. If the same document key is submitted with changed content, create the next immutable revision; do not overwrite the previous revision.
6. Insert the revision and all derived index rows in one atomic transaction.
7. Update the current-revision pointer only after all inserts succeed, in the same transaction.
8. On any error, roll back the entire transaction. No partial snapshot or partial index state may be visible.
9. Concurrent writers must use compare-and-swap against the expected current revision. A stale writer receives a conflict result and must not overwrite a newer revision.
10. Return the exact document key, revision, digest, and storage status.

The store does not infer that a newer revision is more truthful or semantically better.

## 5. Read and integrity semantics

- Read by document key and optionally exact revision.
- Return the canonical snapshot and metadata; do not reconstruct it from indexes.
- Verify the stored digest before parsing the snapshot.
- Validate against the pinned schema/profile before returning a usable document.
- Verify that derived indexes correspond to the snapshot; report index drift separately and allow deterministic index rebuild.
- A failed integrity check returns no successful document result.
- Historical revisions remain readable even when a newer revision exists, provided their schema and canonicalization versions remain supported.

## 6. Failure and resource behavior

- Database busy/locked, stale revision, schema-invalid input, missing document, digest mismatch, unsupported profile, index drift, and interrupted transaction must be distinguishable.
- A failed or interrupted write is atomic.
- Resource budgets may stop expensive validation or index construction, but the result must be explicitly INCOMPLETE and no partial revision may be committed.
- No semantic record-count, expression-count, operand-count, or evidence-count cap may be added to USG-SEM or the store contract.
- The implementation may impose configurable operational budgets only if it preserves all data and reports a resource interruption without representing the operation as complete.

## 7. Security and privacy boundary

The initial store is local SQLite. It does not expose a network listener, remote database, telemetry, or cloud synchronization. The API layer introduced later binds to loopback by default.

All queries use parameterized statements. SQL permissions and storage APIs are enforced by code-level boundaries, not claimed as an OS-level security sandbox. Database files, backups, and exported documents are treated as potentially sensitive user data.

## 8. Required Step 3.2 tests

- canonicalization is deterministic across insertion/key order differences while preserving all array order and exact string content;
- source strings with supplementary Unicode, combining characters, line endings, and whitespace round-trip exactly;
- every USG-SEM record family and namespaced extension survives save/load byte-identically;
- shared expression DAG references and multiple roots survive unchanged;
- identical document/revision/digest writes are idempotent;
- changed content creates a new revision and preserves the prior snapshot;
- stale concurrent writes fail without overwriting current state;
- injected failure between snapshot and index writes rolls back all writes;
- digest tampering, JSON corruption, schema mismatch, and index drift are detected distinctly;
- index rebuild reproduces the same index contents without changing canonical bytes;
- unsupported or invalid records are rejected or preserved exactly according to the canonical schema; they are never coerced;
- a practical large-graph test proves no arbitrary semantic truncation is present;
- all Phase 1 and Phase 2 acceptance suites continue to pass.

## 9. Explicit non-goals

This contract does not define cross-document identity resolution, semantic truth, rule activation, autonomous learning, distributed storage, a general graph database, or human approval queues. Those concerns cannot be inferred from successful persistence.
