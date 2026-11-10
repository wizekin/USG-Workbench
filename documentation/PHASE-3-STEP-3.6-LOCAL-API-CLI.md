# Phase 3 Step 3.6 — Local API and CLI

**Status:** IMPLEMENTED — awaiting exact-PR-head CI and merge.
**API profile:** `USG-LOCAL-API/1.0.0`.
**Storage:** SQLite canonical store; one application process owns the connection and serves concurrent local requests through its thread-safe store.

## Start

```bash
python -m tools.usg_local_api_v1_0_0.cli serve --db ./usg-workbench.sqlite3
```

Default listener: `http://127.0.0.1:8765`. Binding is restricted to `127.0.0.1` or `::1`; wildcard and non-loopback addresses are rejected. No cloud service or paid API is used.

## HTTP endpoints

- `GET /health`
- `POST /v1/validate` — body is one complete USG-SEM/1.0 document
- `POST /v1/documents` — body contains `document` and optional `expected_revision`
- `GET /v1/documents/{document_id}?revision=N`
- `GET /v1/documents/{document_id}/check?revision=N`
- `GET /v1/documents/{document_id}/revisions`
- `GET /v1/documents/{document_id}/conditions?revision=N`
- `GET /v1/documents/{document_id}/contradictions?revision=N`
- `GET /v1/documents/{document_id}/export?revision=N` — returns the complete canonical document, without a summary projection
- `POST /v1/query` — body contains `document_id`, `query`, and optional `revision`
- `POST /v1/interpret` — explicit 501 UNSUPPORTED response; raw-text parsing is not implemented

HTTP responses are JSON. Invalid input returns 400/422, missing documents 404, revision compare-and-swap conflicts 409, and unsupported raw-text interpretation 501. Query results remain revision-pinned. No successful response implies objective truth.

## CLI

```bash
python -m tools.usg_local_api_v1_0_0.cli validate document.json
python -m tools.usg_local_api_v1_0_0.cli store document.json --db ./usg.sqlite3
python -m tools.usg_local_api_v1_0_0.cli get DOC-ID --db ./usg.sqlite3
python -m tools.usg_local_api_v1_0_0.cli check DOC-ID --db ./usg.sqlite3
python -m tools.usg_local_api_v1_0_0.cli conditions DOC-ID --db ./usg.sqlite3
python -m tools.usg_local_api_v1_0_0.cli contradictions DOC-ID --db ./usg.sqlite3
python -m tools.usg_local_api_v1_0_0.cli query DOC-ID query.json --db ./usg.sqlite3
python -m tools.usg_local_api_v1_0_0.cli export DOC-ID --db ./usg.sqlite3 --output export.json
python -m tools.usg_local_api_v1_0_0.cli revisions DOC-ID --db ./usg.sqlite3
```

## Scope and safety

The API accepts canonical USG-SEM/1.0 structures. It does not parse raw text or claim unrestricted natural-language understanding. SQLite remains authoritative. Canonical snapshots remain immutable and revisioned; all analysis outputs are derived. Unsupported/incomplete outcomes and diagnostics are explicit. No semantic truncation or automatic truth promotion is introduced.

## Tests

Automated tests cover validation, lossless store/get/export, idempotency, CAS conflicts, integrity checks, revision history, query, conditions, contradiction inspection, loopback-only binding, unsupported raw-text behavior, route errors, and CLI argument parsing.
