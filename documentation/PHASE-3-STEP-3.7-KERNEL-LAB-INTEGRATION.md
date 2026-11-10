# Phase 3 Step 3.7 — Kernel Lab product integration

**Status:** IMPLEMENTED — awaiting exact-PR-head CI and merge.
**UI:** existing local USG Kernel Lab, extended additively.
**Backend:** the same `USGApplication` dispatcher and SQLite canonical store used by Step 3.6.

## Integration design

The Kernel Lab HTTP server now owns one `USGApplication` instance backed by the selected SQLite database. It serves the existing browser UI and forwards the versioned `/v1/*` routes to that same application dispatcher. The browser therefore does not maintain a second semantic store or duplicate reasoning implementation.

The existing Mention adapter panel and frozen Phase 2 in-memory query benchmark remain available. A new persistent workspace panel adds:
- save complete canonical document with SQLite compare-and-swap revision semantics;
- load and verify the current or selected immutable revision;
- inspect snapshot/index integrity;
- run a structured query against the exact stored revision;
- inspect conditions, exceptions, nested negations, and exact-scope contradictions;
- export the complete canonical USG-SEM/1.0 document.

The server is loopback-only and defaults to `127.0.0.1:8765`. The default database is `usg-workbench.sqlite3` in the repository root; `--db` selects another path.

## Data and safety behavior

- All persistent operations use the Step 3.6 `USGApplication` and Step 3.2 SQLite store.
- Query, condition, contradiction, integrity, and export results are tied to the same immutable revision/digest.
- The browser UI displays diagnostics and machine-readable JSON results; it does not hide unresolved or unsupported outcomes.
- The complete canonical graph remains the preservation envelope. Mention edits are exported as a canonical document and must be saved explicitly to create a new SQLite revision.
- No raw-text parser, cloud dependency, telemetry, automatic truth promotion, implicit closed-world reasoning, or semantic truncation is added.
- The frozen Phase 2 benchmark endpoint remains in-memory and is labelled as a benchmark; the new query action explicitly targets a stored revision.

## Launch

```powershell
py tools/usg-kernel-lab/server.py
```

Open `http://127.0.0.1:8765`. Use `--db PATH` to select a database file.

## Automated integration coverage

The Step 3.7 suite starts the actual loopback HTTP server and exercises the browser asset, health metadata, canonical save/load, integrity check, complete export, revision-pinned query, conditions, contradictions, and non-loopback bind rejection. Existing v0.7.0 Mention adapter and Phase 2 Kernel Lab tests remain in the workflow.
