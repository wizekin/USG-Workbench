# Phase 3 Step 3.3 — Persistent Query Integration

**Status:** COMPLETE — merged in [PR #62](https://github.com/wizekin/USG-Workbench/pull/62).
**Storage backend:** SQLite canonical document store from Step 3.2.
**Query contract:** USG-QUERY/1.0.0; existing Phase 2 query behavior is unchanged.

## Deliverable

A revision-pinned service runs the existing deterministic query interface against a verified canonical snapshot loaded from SQLite. It does not introduce a second query engine, mutate the stored document, or persist query conclusions as semantic facts.

## Behavior

- Loads the current document revision or an explicitly requested immutable historical revision through `CanonicalDocumentStore.get_document`.
- The store verifies snapshot digest, canonicalization profile, USG-SEM schema, typed references, and derived-index consistency before returning the document.
- Runs the existing Phase 2 `QueryInterface` unchanged.
- Checks that the query result's document identity and digest match the exact stored snapshot.
- Returns a `USG-PERSISTENT-QUERY/1.0.0` envelope containing document ID, revision, digest, canonicalization profile, storage status, and the complete existing query result.
- Storage, validation, query, and integrity errors propagate. No partial-success response is returned.
- Historical queries remain pinned to the selected immutable revision even after a newer revision becomes current.

## Safety boundaries

- SQLite remains the only canonical persistence backend.
- Query outputs are derived analysis, not new assertions or objective truth.
- Evidence alignment, semantic support, conflict, corroboration, and external verification remain separate dimensions.
- Open-world behavior, explicit rule allowlists, attribution boundaries, and no-truth-promotion behavior remain inherited from the Phase 2 query pipeline.
- No semantic arrays or graph content are truncated.

## Tests

The Step 3.3 suite covers verified persisted execution, exact revision/digest pinning, historical revision selection, caller/store immutability, and missing-document failure. The dedicated workflow also runs the complete SQLite Step 3.2 suite and Phase 1/2 regression suites.

Run locally:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase3_persistent_query.py" -v
```

