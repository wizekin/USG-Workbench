# Phase 7 Step 7.9 — Knowledge Inspection API, CLI, and Kernel Lab

**Status:** implementation submitted for exact-head CI; acceptance is pending.  
**Service:** `usg-knowledge-inspection/0.1.0`

## Deliverables

- A shared read-only inspection service over the existing Phase 3 SQLite authority and Phase 7 repository.
- Bundle snapshot listing with immutable version and digest metadata.
- Exact record inspection showing source records, evidence, contexts, mappings, and typed relations.
- A conflict ledger that surfaces support/contradiction disagreement without selecting a winner.
- Consumer-aware knowledge query using the Step 7.8 adapter and Step 7.7 retrieval policy.
- A CLI with `bundles`, `query`, `inspect`, and `conflicts` commands.
- Kernel Lab API endpoints and a browser panel for search, bundle listing, provenance inspection, and provider conflicts.

## Kernel Lab API

- `GET /api/knowledge/bundles`
- `GET /api/knowledge/record?record_id=...`
- `GET /api/knowledge/conflicts`
- `POST /api/knowledge/query`

All endpoints are read-only. They reuse the application-owned SQLite connection; they do not create a second database or mutate canonical semantic documents, runtime resources, lifecycle states, or interpretation output.

## CLI

Example commands:

```bash
python -m tools.phase7_knowledge_inspection.cli --db usg-workbench.sqlite3 bundles
python -m tools.phase7_knowledge_inspection.cli --db usg-workbench.sqlite3 query bank --consumer PHASE2 --language en
python -m tools.phase7_knowledge_inspection.cli --db usg-workbench.sqlite3 inspect sense:example
python -m tools.phase7_knowledge_inspection.cli --db usg-workbench.sqlite3 conflicts
```

## Acceptance tests

`python -m unittest discover -s tests -p 'test_phase7_knowledge_inspection.py' -v`

Tests cover bundle listing, provenance inspection, unknown records, conflict output, shared retrieval adapter, CLI command parsing, and live Kernel Lab HTTP endpoints.

## Limitations

This is a local read-only inspection interface. It does not automatically ingest external data, resolve provider conflicts, promote candidates, or modify interpretation behavior. The API and CLI expose the same inspection service; Kernel Lab uses the same application-owned repository. No claim is made that the browser UI is a universal ontology editor or semantic truth adjudicator.
