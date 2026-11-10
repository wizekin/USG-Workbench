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


## Candidate 1 measured result: RocksDB (initial benchmark)

Benchmark artifact from the corrected adapter run: GitHub Actions run 42819794960, artifact `phase3-rocksdb-benchmark`. Three repetitions used the same 1,204-expression USG document and identical operations. These are measurements from the hosted Ubuntu CI runner, not universal performance guarantees.

| Operation | SQLite median | RocksDB median | RocksDB / SQLite |
|---|---:|---:|---:|
| Initial write | 175.0 ms | 168.0 ms | 0.960× |
| Warm read (7-read median) | 160.7 ms | 162.2 ms | 1.009× |
| Idempotent write | 160.5 ms | 157.6 ms | 0.982× |
| Revision update | 166.9 ms | 167.8 ms | 1.005× |
| Revision history | 0.109 ms | 0.062 ms | 0.565× |
| Integrity verification | 160.4 ms | 161.9 ms | 1.010× |
| Index rebuild | 262.7 ms | 164.1 ms | 0.625× |
| On-disk files after close | 962,560 B | 294,585 B | 0.306× |

The first benchmark exposed excess work in the RocksDB idempotent/update path (it performed a full integrity/index read). That path was corrected to match SQLite's behavior: verify the stored snapshot hash and compare the digest, without rescanning derived indexes during the write. The table above is from the corrected implementation.

### Preliminary interpretation

RocksDB is promising for this workload: approximately 69.4% less disk space, comparable warm reads and integrity checks, and faster index rebuild/history operations. Initial write and revision-update latencies are effectively comparable. This is a meaningful storage-footprint improvement, not a dramatic general speedup.

The RocksDB adapter uses one embedded primary process per database directory. A sidecar OS lock serializes writer critical sections but cannot make RocksDB's exclusive database-open lock support multiple independent primary processes. The added concurrency regression checks concurrent readers and serialized writers within one process. If USG requires multiple independent processes to open the same database concurrently, this candidate does not meet that topology without a separate single-owner service.

**Current status:** promising candidate, not yet promoted. Await the latest concurrency regression workflow on commit `db64ae4630572c1812e6494a3259a63c31a9c939`. Even if accepted as a canonical-store candidate, continue the separately requested DuckDB, LanceDB, and Qdrant evaluations. No default backend change is made by this evaluation.

## Candidate 2: DuckDB

DuckDB is evaluated as a true SQL canonical-store candidate, not as a vector database. Its strengths are analytical scans, SQL, and columnar execution. The local adapter preserves full canonical snapshots in BLOB columns and keeps explicit derived indexes in relational tables. It uses ACID transactions for atomic snapshot/revision/index/current-pointer writes.

Important topology constraint: the standard in-process DuckDB read-write database is owned by one process. Multiple writer threads are supported within that process; multiple processes can open read-only. The evaluation therefore tests multiple connections within one process and a read-only reopen. It does not assume a multi-process write topology. This limitation is weighed against SQLite and RocksDB.


### Candidate 2 measured result: DuckDB

Benchmark artifact: GitHub Actions run 42820307739, artifact `phase3-duckdb-benchmark`. Three repetitions used the same 1,204-expression USG document and the same canonical-store operations.

| Operation | SQLite median | DuckDB median | DuckDB / SQLite |
|---|---:|---:|---:|
| Initial write | 202.1 ms | 880.8 ms | 4.36× |
| Warm read (7-read median) | 196.4 ms | 201.4 ms | 1.03× |
| Idempotent write | 194.0 ms | 195.0 ms | 1.01× |
| Revision update | 208.9 ms | 886.4 ms | 4.24× |
| Revision history | 0.135 ms | 1.371 ms | 10.18× |
| Integrity verification | 199.2 ms | 200.0 ms | 1.00× |
| Index rebuild | 205.0 ms | 888.7 ms | 4.34× |
| On-disk files after close | 962,560 B | 4,206,592 B | 4.37× |

The adapter passed exact canonical round-trip, schema/grounding and source-hash validation, idempotent writes, revision history, stale-writer rejection within the connection, index drift/rebuild, snapshot tampering detection, large-graph preservation, multiple in-process connections writing separate documents, and read-only reopen. SQLite baseline and Phase 1/2 regression suites also passed.

**Decision:** DuckDB is not a good replacement for SQLite for the current canonical persistence workload. Reads and integrity checks are similar, but write/revision/index-rebuild paths are about 4.2–4.4 times slower and the database footprint is about 4.4 times larger at this scale. Its analytical SQL and columnar execution remain potentially useful as a separate reporting/analytics layer over exported or replicated USG data, but that complementary use needs its own workload test and must not become the canonical source of truth.

## Candidate 3: LanceDB

LanceDB is evaluated both as a potential canonical snapshot store and as a complementary retrieval system. Its embedded local mode supports versioned Lance tables, vector similarity, and full-text search. The prototype stores one complete canonical USG snapshot per revision in an append-only table and keeps semantic/vector retrieval in a separate rebuildable sidecar.

The key contract question is whether LanceDB's table-level MVCC and append commits can meet USG's per-document compare-and-swap revision guarantees. The adapter deliberately reports duplicate revision rows as integrity failures; the append/read/CAS sequence is not a database-enforced unique conditional transaction. A sidecar retrieval index is rebuildable and must never become authoritative semantic truth.

### Candidate 3 initial measured result: LanceDB

The corrected three-run benchmark on the 1,204-expression USG document showed:
- Initial write: 2.5% faster than SQLite (114.0 ms vs 117.0 ms)
- Warm read: 2.5% slower (112.8 ms vs 110.1 ms)
- Idempotent write: effectively equal (109.4 ms vs 108.9 ms)
- Revision update: 5.9% faster (110.4 ms vs 117.2 ms)
- Revision listing: 2.23 ms vs 0.075 ms (about 29.7× slower, but still a low absolute latency)
- Integrity verification: 7.5% faster (107.1 ms vs 115.8 ms)
- Canonical table disk footprint: 373,007 B vs 958,464 B (61.1% smaller)

This artifact was produced before adding the local cross-instance writer lock, so the final benchmark is rerun after that addition. The retrieval sidecar's vector/FTS index storage is not included in the canonical-table size.

The initial implementation revealed that a table append is atomic, but LanceDB does not expose a per-document unique conditional append. The adapter now adds an OS-level local writer lock around read/check/append and refreshes the table manifest after acquiring the lock. This can serialize compare-and-swap updates made through this adapter by separate local instances. Direct writes that bypass the adapter are outside this guarantee; object-store deployments need a separate conditional coordination design.

The retrieval test confirms exact nearest-neighbor mechanics with synthetic known-answer vectors and full-text search with a Lance FTS index. This validates the retrieval engine mechanics, not semantic quality of real embeddings; no model-generated embedding quality claim is made.

### Candidate 3 final measured result: LanceDB after local CAS locking

Final benchmark artifact: GitHub Actions run 42821729870, artifact `phase3-lancedb-benchmark`. Three runs, each using the same 1,204-expression canonical USG document:

| Operation | SQLite median | LanceDB median | LanceDB / SQLite |
|---|---:|---:|---:|
| Initial write | 250.0 ms | 248.2 ms | 0.993× |
| Warm read (7-read median) | 246.9 ms | 244.3 ms | 0.989× |
| Idempotent write | 243.7 ms | 244.8 ms | 1.005× |
| Revision update | 279.7 ms | 248.1 ms | 0.887× |
| Revision history | 0.116 ms | 5.099 ms | 44.1× |
| Integrity verification | 250.0 ms | 242.6 ms | 0.970× |
| Canonical table disk footprint | 958,464 B | 373,007 B | 0.389× |

The final run includes the local writer lock and table-handle refresh. All LanceDB adapter tests passed, including competing writes through two separate store instances: exactly one writer created revision 2 and the stale competing writer received a revision conflict. Duplicate revision rows are detected, table time-travel works, and vector/FTS retrieval tests pass. The full SQLite, Phase 1, Phase 2, RocksDB, and DuckDB regression gates also passed.

**Decision:** LanceDB is a promising candidate for local canonical storage and a strong complementary retrieval layer. It provides near-SQLite latency for the tested operations and a 61.1% smaller canonical-table footprint, with slower revision-history listing (about 5 ms absolute). The adapter's OS file lock supplies local compare-and-swap serialization for writers that use the adapter; direct table writes bypass that guarantee. The retrieval sidecar remains independently rebuildable. Actual embedding generation and semantic retrieval quality have not yet been tested.

Do not promote it as the default until Qdrant is evaluated and the final cross-candidate decision is made. SQLite remains the active backend for now.
