# USG Kernel Lab

A local-only browser workbench combining:
- the Python v0.7.0 Mention model and USG-SEM/1.0 adapter;
- the Phase 2 structured query/reasoning pipeline;
- the Phase 3 SQLite canonical document store and immutable revisions;
- persistent query, conditions/exception maps, and exact-scope contradiction inspection.

## What it can test

- Import and schema-validate a complete USG-SEM/1.0 document.
- Inspect native v0.7.0 Mention projections and mapping coverage.
- Edit native Mention text, resolution status, Mention type, and typed links.
- Export edits while preserving canonical-only records and source spans.
- Save complete canonical documents into the SQLite store.
- Load current or historical immutable revisions.
- Verify snapshot hashes, schema, typed references, and derived indexes.
- Run structured queries against a selected stored revision.
- Inspect IF/UNLESS conditions, exceptions, and nested NOT scopes.
- Inspect exact-scope contradictions without selecting a winner.
- Export the complete canonical document as JSON.

## What it does not do

The Mention adapter remains an adapter/model test bench, not a natural-language semantic parser. The reasoning interface accepts explicit canonical semantic structures and exact typed references. It does not generate semantic structures from raw sentences, perform free-text inference, infer a UNLESS consequent from an absent exception, or claim objective truth. Raw-text interpretation is explicitly unsupported.

## Requirements

- Python 3.10 or newer
- `jsonschema>=4.18,<5`

Install from the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
```

## Run on Windows

From the repository root:

```powershell
py tools/usg-kernel-lab/server.py
```

After installing the package, the same integrated browser lab can be launched with one command:

```powershell
usg-workbench lab --db .\\usg-workbench.sqlite3
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

The server binds only to `127.0.0.1`. The default canonical database is `usg-workbench.sqlite3` in the repository root. Choose a different file with:

```powershell
py tools/usg-kernel-lab/server.py --db D:\USGData\usg-workbench.sqlite3
```

Press Ctrl+C to stop. No telemetry, cloud calls, or paid APIs are used.

## Quick start

1. Choose **Load sample document** and **Import & inspect**.
2. Use the Mention panel to inspect or edit native Mention records.
3. Choose **Save current document** in the persistent workspace to create SQLite revision 1.
4. Use **Verify integrity** to check the stored snapshot and rebuildable indexes.
5. Use **Load stored document** to reload a verified revision.
6. Select a query fixture, then save the loaded document and choose **Run query on stored revision**.
7. Inspect **Conditions** and **Contradictions** and export the complete canonical JSON.

The existing **Run all query fixtures** control remains a frozen in-memory benchmark; the new stored-revision query control exercises the SQLite-backed API.

## Local API

The Kernel Lab server exposes the same versioned application dispatcher as the standalone local API. In addition to the browser/adapter endpoints below, it exposes:
- `GET /v1/health` is not defined; use `GET /health` for combined Kernel Lab health.
- `POST /v1/validate`
- `POST /v1/documents`
- `GET /v1/documents/{document_id}?revision=N`
- `GET /v1/documents/{document_id}/check?revision=N`
- `GET /v1/documents/{document_id}/revisions`
- `GET /v1/documents/{document_id}/conditions?revision=N`
- `GET /v1/documents/{document_id}/contradictions?revision=N`
- `GET /v1/documents/{document_id}/export?revision=N`
- `POST /v1/query`
- `POST /v1/interpret` returns 501 UNSUPPORTED; raw-text parsing is not implemented.

The legacy UI endpoints remain available:
- `GET /`, `GET /health`, `GET /api/fixtures`
- `POST /api/fixture`, `POST /api/query`, `POST /api/benchmark`
- `POST /api/inspect`, `POST /api/export`

The canonical SQLite store is the sole persistence authority. The browser does not create a second data store.
