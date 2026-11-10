# Phase 3 quick demo

This folder contains a complete canonical USG-SEM/1.0 document and a structured query that derives a non-truth-promoting candidate through the explicitly enabled Modus Ponens rule.

Run the integrated browser workbench:

```bash
usg-workbench lab --db ./usg-workbench.sqlite3
```

Open `http://127.0.0.1:8765`, load `sample-usg-sem-1.0.json` into the document editor, save it to SQLite, load `sample-query.json` in the query controls, and run the query against the stored revision.

The example demonstrates structured reasoning only; it does not establish objective truth or parse raw text.
