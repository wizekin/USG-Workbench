# Phase 3 Step 3.2 — SQLite Canonical Document Store

**Status:** IMPLEMENTED — awaiting exact-PR-head CI and merge.
**Package:** tools/semantic_graph_store_v1_0_0
**Canonical profile:** USG-SEM/1.0
**Canonicalization profile:** USG-CANONICAL-JSON/1.0.0

## Deliverable

The new store persists the complete USG-SEM document as canonical UTF-8 JSON bytes in SQLite. It adds rebuildable indexes for expressions, assertions, evidence, and sources. The canonical snapshot remains authoritative; the indexes are verified projections.

## Implemented behavior

- Recursive object-key sorting and compact UTF-8 serialization, preserving all array order and exact string content.
- SHA-256 content addressing over canonical bytes.
- Full USG-SEM/1.0 JSON Schema validation and Phase 2 typed-reference/grounding validation before writes and after reads.
- SQLite migrations, foreign keys, WAL for file-backed databases, full synchronous writes, busy timeout, and explicit transactions.
- Append-only immutable document revisions with predecessor links.
- Compare-and-swap updates: a changed existing document requires its exact expected current revision. A stale writer cannot replace a newer revision.
- Idempotent retries for an identical current snapshot.
- Atomic snapshot, index, and current-revision updates.
- Rebuildable derived indexes and index-drift detection.
- Snapshot digest, canonicalization profile, schema/profile identity, and JSON integrity verification on reads.
- Machine-readable integrity report.
- No deletion or in-place mutation of canonical revisions.

## Test coverage

The Step 3.2 suite covers deterministic canonicalization, array-order preservation, supplementary Unicode and combining sequences, invalid JSON values, byte-identical save/load, idempotency, immutable revisions, stale-writer rejection, atomic rollback on injected index failure, index drift and rebuild, snapshot tampering, large graph preservation without semantic truncation, invalid-document rejection, and integrity reporting.

Run locally:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase3_graph_store.py" -v
```

The dedicated workflow is .github/workflows/phase3-graph-store.yml. Phase 1 and Phase 2 compatibility workflows continue to run independently on the same pull request.

## Known boundary

This step stores and verifies USG-SEM documents; it does not infer truth, merge cross-document identities, execute new rules, or expose a network API. Query integration is Step 3.3. The store does not normalize source strings or introduce semantic item-count limits.
