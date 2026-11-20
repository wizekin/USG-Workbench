# USG External Lexical Completion Launcher — v0.1.0

## Purpose

Provide one manual initiation that continues the existing external English lexical crawl until its cumulative headword target is reached or a safety boundary prevents further processing.

This is a controller/adapter over the existing implementation in
\`tools/usg_external_lexical_v0_1_0/crawl.py\`. It does not replace the lexical
crawler, source parser, checkpoint schema, shard format, manifest, or publisher.
Each batch is executed by the repository's \`LexicalCrawler.run_batch()\`.

## Default behavior

- Cumulative target: 1,396,111 processed headwords (or the source checkpoint's
  declared headword count when the CLI target is set to zero).
- Internal batch ceiling: 30,000 headwords.
- One Actions session: up to 18,000 seconds (5 hours).
- Workflow job timeout: 350 minutes.
- Continuation: when a session approaches its execution budget, the launcher
  dispatches one further run of this workflow. The next run reloads the
  authoritative checkpoint before doing any work.
- Durable state: the existing \`usg-external-lexical-data\` branch.
- Compressed shard storage ceiling: exactly 700 MiB (734,003,200 bytes).

The 700 MiB ceiling is fixed in the launcher. It is not an overrideable
workflow input. The existing crawler is constructed with the same byte limit
and continues to enforce the storage guard when publishing checkpoint,
manifest, and shard updates.

## One-launch continuation model

A manual launch starts one Actions run. The controller repeatedly invokes
\`LexicalCrawler.run_batch()\` while it has session time and headwords remaining.
Before each batch it reads the durable checkpoint and computes the next batch
size from the target. After each batch it reads the checkpoint again and
verifies durable progress.

When the runner's reserved time is reached, it calls GitHub's
\`workflow_dispatch\` endpoint to queue the next run, preserving the target
and batch size. The next run resumes from the data-branch checkpoint; it does
not restart the source snapshot or reprocess already committed batches.

The workflow has \`contents: write\` for the existing data-branch publisher and
\`actions: write\` for the continuation dispatch. No personal access token or
additional secret is required when the repository's \`GITHUB_TOKEN\` settings
allow these permissions.

## Replacing the legacy crawl

The legacy six-hour scheduled workflow has been paused:
- its schedule trigger was removed;
- its manual crawl job was disabled;
- its pull-request validation job remains available.

The new workflow deliberately uses the same Actions concurrency group as the
legacy crawler. Its first manual launch has \`continuation=false\` and
\`cancel-in-progress=true\`, so GitHub cancels a still-running legacy crawl
before starting the completion launcher. Continuation runs carry
\`continuation=true\` and do not cancel their preceding launcher while it
finishes the end-of-session reconciliation step.

If the legacy run is still running before the first new manual launch, it may
continue until that launch obtains the shared concurrency group. The repository
connection used to create this change does not provide a direct Actions run
cancellation operation.

## Safety and stop conditions

The launcher stops without queuing a continuation when any of these applies:

1. The cumulative checkpoint count reaches the target.
2. The stored compressed-shard byte count reaches the 700 MiB ceiling.
3. The crawler reports that the source snapshot is already complete but the
   target is still unmet.
4. The source is rate-limited or a browse page fails. The durable cursor is
   preserved for a later manual resume; the launcher does not spin in a
   self-dispatch loop against a persistent upstream error.
5. The crawler produces no durable cursor, retry-counter, or storage progress.
6. The GitHub continuation dispatch fails. The published checkpoint remains
   resumable and the workflow reports the dispatch error.

The existing crawler also retains its pinned-source snapshot behavior,
failed-headword retry queue, append-only gzip JSONL shards, rights metadata,
and read-only candidate-evidence boundary. No external lexical candidate is
promoted into an active runtime lexical resource.

## Run manually

After this workflow is merged into \`main\`:

1. Open the repository's Actions tab.
2. Select **USG External Lexical Completion Launcher**.
3. Choose **Run workflow**.
4. Keep the default target (1,396,111), batch size (30,000), and
   **continue until target** enabled.

The first manual launch replaces any still-running legacy crawl through the
shared concurrency group. Subsequent continuation runs are dispatched
automatically. A new manual launch can also resume a checkpoint after a
storage, source, or runner interruption once the cause has been addressed.

To run only one bounded Actions session, disable **continue until target**.
The checkpoint remains available for a later manual launch.

## Local offline tests

From the repository root:

\`\`\`bash
python -m compileall -q tools/usg_external_lexical_v0_1_0
python -m unittest discover -s tests -p "test_external_lexical_manual_crawl.py" -v
python -m unittest discover -s tests -p "test_external_lexical_crawl.py" -v
\`\`\`

The manual launcher tests use a fake crawler and do not make network requests,
change the real data branch, or initiate a crawl. The integration workflow also
runs the existing lexical retrieval, state reconciliation, remote audit, and
offline structural benchmark suites.

## Acceptance criteria

- The launcher calls the existing \`LexicalCrawler.run_batch()\`; no separate
  parser or source-cursor implementation is introduced.
- Every new batch starts from the latest durable checkpoint.
- Batch sizes never exceed 30,000 headwords.
- The configured cumulative target is never exceeded by the batch size
  requested from the crawler.
- Compressed storage never exceeds 734,003,200 bytes.
- A healthy session that exhausts its runner budget dispatches one continuation.
- A target-complete session dispatches no continuation.
- Source errors, no-progress states, and storage limits stop the chain safely.
- The existing crawler's checkpoint, manifest, shard and candidate-only
  semantics remain unchanged.
