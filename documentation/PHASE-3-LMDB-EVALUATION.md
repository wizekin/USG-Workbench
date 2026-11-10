# Phase 3 — LMDB Evaluation and Migration Gate

**Status:** EVALUATION IN PROGRESS. SQLite remains the active canonical backend until the LMDB gate passes.

## Why LMDB is being evaluated

LMDB is an embedded, memory-mapped ordered key/value store. The Python binding documents concurrent readers that do not block writers, one concurrent write transaction per environment, multi-process access on one host, named databases covered by a single transaction, and no need for a background maintenance process. These characteristics are promising for USG's immutable canonical snapshots and read-heavy document lookups.

LMDB is not a relational database. It has no SQL, joins, or automatic secondary indexes. This implementation therefore uses named databases and explicit rebuildable index records. Canonical USG-SEM snapshots remain the only semantic authority.

## Physical layout

The LMDB implementation is additive and isolated in `tools/semantic_graph_store_lmdb_v1_0_0/`. It does not alter or remove the SQLite implementation.

| Named database | Contents |
|---|---|
| documents | Current revision pointer and document profile metadata |
| revisions | Immutable revision metadata, predecessor, canonicalization profile, digest |
| snapshots | Exact authoritative canonical UTF-8 JSON bytes |
| expression_index | Derived expression lookup rows |
| assertion_index | Derived assertion lookup rows |
| evidence_index | Derived evidence lookup rows |
| source_index | Derived source lookup rows |
| migrations | Versioned storage migration marker |

All named databases participate in the same LMDB write transaction. Thus a snapshot, revision metadata, derived indexes, and current pointer are committed or aborted together. Index keys are SHA-256 hashes of canonical composite keys so long document and record identifiers do not encounter LMDB's fixed key-length ceiling; full identifiers remain in index values and are verified.

## Important LMDB operating constraints

- Multiple read transactions are supported; a single write transaction is active at a time. LMDB serializes writers rather than allowing parallel write transactions.
- Write transactions and cursors must remain within their documented thread/lifetime constraints. The implementation uses context-managed transactions.
- LMDB environments are local to one host and must be opened according to py-lmdb's process/fork rules. An inherited environment must not be reused after fork.
- The map size is a virtual-address reservation on 64-bit systems, not an immediate disk allocation. It is configurable; a map-full condition must fail visibly rather than truncate a document.
- Long-lived read transactions can prevent page reuse and cause file growth. Callers must keep read transactions short.
- This is a local embedded store, not a distributed database or network service.

## Free software and licensing

LMDB and py-lmdb are available without purchase and can be self-hosted locally. The upstream py-lmdb distribution identifies the OpenLDAP Public License (OLDAP-2.8), not MIT or Apache-2.0. This is a permissive free-software license with notice and redistribution conditions; preserve its license notices when distributing the dependency. No hosted service or paid plan is required.

## Evaluation plan and acceptance gate

The SQLite implementation is retained as the baseline. The same USG fixture and generated large graph are run against both backends.

Required correctness gates:

1. Exact canonical UTF-8 byte round-trip, including supplementary Unicode, combining sequences, whitespace, CRLF, opaque extensions, and array order.
2. Schema, grounding/reference, source-hash, snapshot-hash, and profile verification.
3. Idempotent writes, immutable history, predecessor links, compare-and-swap stale-writer rejection.
4. Atomicity across snapshot, metadata, indexes, and current pointer after injected failure.
5. Detection and deterministic rebuild of missing, altered, or extra index rows.
6. Reopen/recovery after an aborted transaction and concurrent reader/writer behavior.
7. Large graph preservation without semantic truncation or identifier-size restrictions.
8. Full Phase 1, Phase 2, SQLite Phase 3, and LMDB-specific regression suites.

Performance observations include write latency, warm read latency, idempotent write, revision update, history listing, integrity verification, index rebuild, and database file size. Benchmark output is an artifact; it is not reduced to one aggregate score. A speed advantage cannot compensate for a failed correctness gate.

**Decision rule:** If any critical correctness/recovery/concurrency gate fails, stop the LMDB migration and evaluate the remaining free alternatives. If all gates pass and the benchmark shows acceptable behavior for the target USG workload, then promote LMDB as the default backend in a separate migration PR, complete the remaining Phase 3 steps, and auto-merge each PR only after its exact-head required checks pass. SQLite code and migration/export compatibility remain available until a separately tested deprecation decision.
