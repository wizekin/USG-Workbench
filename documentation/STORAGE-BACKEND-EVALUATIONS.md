# Storage backend evaluation sequence

This evaluation sequence is deliberately one candidate at a time. SQLite remains the production/default Phase 3 backend unless a candidate independently passes the complete canonical-store contract and demonstrates a material benefit on representative USG workloads.

## Candidates and order

1. RocksDB via rocksdict — embedded ordered key/value store.
2. DuckDB — embedded analytical SQL database.
3. LanceDB — embedded versioned columnar/vector retrieval database.
4. Qdrant — vector search engine; evaluate as a complementary semantic-retrieval layer and separately determine whether it can meet canonical persistence requirements.

Each candidate receives a separate implementation/evaluation branch, CI run, benchmark artifact, and decision record. Do not combine candidates in one benchmark PR. Do not change the canonical USG-SEM/1.0 contract during these evaluations.

## Common acceptance dimensions

- Byte-exact canonical snapshot round-trip (Unicode, combining sequences, CRLF, whitespace, opaque extensions, array order).
- Complete graph preservation with no arbitrary semantic truncation.
- Schema, grounding/reference, source-hash, and snapshot-hash verification.
- Immutable revisions, predecessor links, idempotent retry, compare-and-swap stale-writer rejection.
- Atomic snapshot + revision + index + current-pointer writes.
- Reopen/recovery, crash/rollback behavior, concurrent readers and multi-process writers.
- Detection and deterministic rebuild of derived-index drift.
- Query/lookup performance, write/read latency, revision operations, integrity scans, index rebuild, RAM and disk size.
- Free local/self-hosted operation, licensing, Windows and Linux/Python compatibility.

A candidate may be useful as a secondary retrieval layer even if it fails canonical persistence. Vector similarity results must never be treated as authoritative semantic facts or truth judgments.

## Candidate 1: RocksDB

Initial implementation uses rocksdict in raw byte mode, synchronous WAL writes, atomic WriteBatch, consistent read snapshots, and a process-shared OS file lock around compare-and-swap writer critical sections. The lock is necessary because ordinary WriteBatch is atomic but does not itself provide conditional compare-and-swap transactions.

This adapter is an evaluation prototype, not the active backend. The test suite and benchmark decide whether to proceed.
