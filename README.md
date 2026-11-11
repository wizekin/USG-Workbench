# USG External Lexical Analysis Data

This branch is the append-only storage target for the scheduled external lexical crawler.

It is intentionally separate from `main`. The scheduled workflow writes compressed, per-batch JSONL shards under `shards/<snapshot-id>/` and updates only the small progress files under `state/`.

## Data policy

- No full source dictionary, source Markdown files, raw definitions, or example sentences are copied here.
- Shards contain source-linked lexical identifiers, parts of speech, observed forms/tags, sense-scoped and entry-scoped relation metadata, definition hashes, and compact analysis classifications.
- Every source record retains its source entry URL, history URL, snapshot, declared licence, and attribution metadata.
- Source claims remain candidate evidence. No data in this branch is automatically promoted into the runtime USG LexicalResource or grammar.
- The underlying source may contain per-entry and per-sense rights differences. This branch therefore preserves rights metadata and avoids redistributing definition/example passages.

## Resume and progress

- `state/checkpoint.json`: current source snapshot and cursor. The crawler resumes from this exact point after the next six-hour schedule.
- `state/manifest.json`: cumulative counts, output bytes and last successful batch.
- `shards/<snapshot-id>/batch-*.jsonl.gz`: immutable batch outputs.

The crawler pauses itself before the GitHub Actions job timeout, publishes the batch and checkpoint, then exits. It is scheduled every six hours by the workflow in the main branch.

## Storage guard

The initial implementation stops at a 700 MiB cumulative shard-storage budget to keep the repository comfortably below GitHub's recommended repository size. A storage-limit stop is recorded in the manifest and does not silently discard prior batches.

## Licence and source references

- English Dictionary source: https://github.com/figueirego/english-dictionary
- Source snapshot metadata: https://github.com/figueirego/english-dictionary/blob/main/dictionary/SOURCE.md
- Per-entry rights and attribution: https://github.com/figueirego/english-dictionary/blob/main/LICENSE.md
- CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/

The user must review the exact source licence and applicable attribution for any further export or redistribution.
