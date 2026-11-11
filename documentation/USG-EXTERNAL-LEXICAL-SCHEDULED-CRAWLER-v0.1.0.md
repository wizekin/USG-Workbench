# USG External Lexical Scheduled Crawler — v0.1.0

## Purpose

Run the external English lexical analysis incrementally on GitHub Actions. Each scheduled run processes a bounded slice of the public English Dictionary source, publishes one compressed analysis shard, saves a checkpoint, and exits. The next scheduled run resumes from the exact next headword.

This worker is separate from the interactive on-demand lookup command. It gradually processes the source snapshot; it does not download the full multi-gigabyte source archive or import a 1.4-million-word inventory in one operation.

## Schedule and runtime

- Workflow: .github/workflows/usg-external-lexical-crawl.yml
- Schedule: 23 */6 * * * (00:23, 06:23, 12:23, 18:23 UTC).
- Job timeout: 350 minutes (5 hours 50 minutes).
- Crawler soft runtime: 320 minutes (5 hours 20 minutes).
- Scheduled headword budget: 30,000 per run.
- A 40-minute buffer remains before the six-hour runner ceiling; the job timeout itself leaves 10 minutes for job cleanup.
- The concurrency group prevents overlapping crawls.
- Each run exits early when it reaches its headword limit, time budget, upstream rate limit, or persistent-storage guard.

GitHub's standard hosted runner job limit is six hours. The repository is public, so standard GitHub-hosted Ubuntu runner usage is free under GitHub's current Actions rules. The workflow uses ubuntu-latest, not a billed larger runner.

## Durable storage

Results are published to the separate usg-external-lexical-data branch, not main.

- README.md: explains the data-branch contents and rights policy.
- state/checkpoint.json: immutable source snapshot, page/entry cursor, cumulative counters, pending failed-headword retry queue, and next resume position.
- state/manifest.json: cumulative counts, compressed bytes, batch count, and last batch metadata.
- shards/<snapshot-id>/batch-*.jsonl.gz: append-only per-run lexical analysis results.

The workflow publishes each batch through GitHub's Git Data API. It does not check out or download the growing data branch on every run. It retrieves only the small checkpoint through the GitHub Contents API (not the CDN-cached raw branch URL), then uploads the new shard and updated state. This avoids replaying a previously published batch when the raw-file CDN briefly serves a stale checkpoint.

The initial storage budget is 700 MiB of compressed shards. This is a safety limit, not a prediction of the final corpus size. If the budget is reached, the worker writes a storage_limit_reached status and stops; it does not silently delete old results or reset the cursor. Continuing beyond that point requires a separately chosen storage destination or storage-budget revision.

## What is stored

The crawler retrieves individual Markdown entry files at one pinned source commit and runs the USG lexical normalizer and analysis rules.

Stored fields include:
- Original headword candidate and source entry path.
- Source entry and history URLs, snapshot, declared licence, attribution and editorial-review notes.
- Entry and sense identifiers, parts of speech, observed forms and tags.
- Source-asserted relations with their original entry-level or sense-level scope.
- SHA-256 hashes of definitions, compact definition-pattern classifications, and a source-linked candidate graph.
- Per-entry and cumulative counts, validation status, and failure events.

Raw definition text and example sentences are not copied into the public data branch. The source retains the original wording; USG keeps hashes and source links so it can retrieve a definition on demand when needed. This reduces storage and avoids republishing source passages whose rights may differ by sense.

The source repository documents per-entry and per-sense rights distinctions. Every record retains the declared source licence and provenance. Any future export that includes raw definitions or examples must separately preserve the relevant attribution and licensing terms.

## Resume behavior

The crawler pins one Git commit and its snapshot ID for the duration of a full crawl. If a run ends after page 17, entry 412, the next scheduled run resumes at that cursor and fetches the same source revision. It does not switch to a newer upstream revision halfway through a snapshot.

When the pinned snapshot is complete, subsequent runs compare the upstream source snapshot. If the source publishes a new snapshot, the crawler starts a new cycle while preserving prior shards and cumulative storage accounting.

The worker records failed entry fetches and parser failures as compact failure events and continues where it can. A transient source rate limit stops the run without advancing past the current headword. A browse-page fetch or parse error is recorded separately and stops the batch without advancing the page/entry cursor; the next scheduled run retries that exact page so a temporary index failure cannot silently skip hundreds of headwords.

Older crawler versions recorded per-headword failures but did not retry them. On upgrade, the crawler scans the existing snapshot shards once, reconstructs a deduplicated retry queue from those failure events, and persists it in the checkpoint. Pending failures are retried before new headwords; recovered entries are published with an explicit `retrieval_event` marker. A failed retry is deferred to a later run and is moved to a dead-letter count after three attempts. Retry attempts, recoveries, failures, and pending queue size are reported separately from the original source-cursor counters.

## Run manually

Open the repository's Actions tab, select **USG External Lexical Incremental Crawl**, and choose **Run workflow**.

The manual default is a 200-headword / 15-minute pilot. To run a larger manual batch, supply:
- max_headwords: up to 30,000.
- max_runtime_minutes: up to 320.
- validation_only: true to run the offline validation suite without starting a crawl.

The scheduled cadence always uses 30,000 headwords / 320 minutes.

## Pause and resume

- To pause: disable the workflow from the GitHub Actions workflow page.
- To resume: re-enable the workflow. The next scheduled or manual run reads state/checkpoint.json and continues from the saved cursor.
- Do not delete or reset the usg-external-lexical-data branch unless you intend to discard the crawl state and all published shards.

## Important capability boundary

The crawler is a gradual lexical-evidence acquisition process. It is not an LLM training job, it does not create or approve new USG grammar rules, and it does not automatically modify the runtime LexicalResource or Phase 5 interpreter. Promotion remains a separate, test-gated operation.

## Local test commands

    py -m compileall -q tools/usg_external_lexical_v0_1_0
    py -m unittest discover -s tests -p "test_external_lexical_crawl.py" -v
    py -m unittest discover -s tests -p "test_external_lexical_retrieval.py" -v

## References

- GitHub Actions job and schedule limits: https://docs.github.com/en/actions/reference/limits
- GitHub Actions workflow schedule syntax: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- GitHub Actions billing for public repositories: https://docs.github.com/en/actions/concepts/billing-and-usage
- GitHub repository size recommendations: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- English Dictionary source and rights: https://github.com/figueirego/english-dictionary


## Recovery verification — 2026-11-11

After the checkpoint freshness and failed-headword retry repair was merged, production recovery run [43102113033](https://github.com/wizekin/USG-Workbench/actions/runs/43102113033) completed successfully.

Observed post-run checkpoint values on `usg-external-lexical-data`:

- `processed_headwords`: 402 (the source cursor advanced from 400 to 402; this is distinct from retry recoveries).
- `retried_headwords`: 198.
- `recovered_headwords`: 198.
- `retry_failed_headwords`: 0.
- `retry_dead_letter_headwords`: 0.
- `retry_queue`: empty.
- `processed_entries`: 469.
- `processed_senses`: 602.
- `stored_bytes`: 185,234.
- `batch_number`: 3.

This is a successful recovery pilot, not proof that the entire 1.4-million-headword crawl is complete or that every future scheduled run is replay-safe. The next acceptance gate is a clean offline validation run, followed by at least one subsequent scheduled/manual resume run that demonstrates a strictly advancing cursor, a new batch identifier, and consistent checkpoint/manifest/shard accounting.

## Operational acceptance gates

A crawl batch is accepted only when all of the following are true:

1. The workflow exits successfully and the crawler reports a published batch.
2. The source cursor advances monotonically, unless the run explicitly records a retry-only batch.
3. The batch identifier is new; no previously published batch is replayed.
4. Retry queue counters reconcile: recovered + still pending + dead-lettered outcomes account for attempted historical failures.
5. Manifest batch count, headword/entry/sense totals, and stored-byte total reconcile with the published shards.
6. Storage remains below the configured budget, and the pinned source snapshot remains unchanged within a cycle.
7. Offline crawler contract tests, lexical retrieval tests, compilation, and structural benchmark pass before code changes are merged.

External lexical records remain candidate evidence only. Successful crawling does not authorize automatic promotion into USG's active lexical resource or grammar.


## Offline state reconciliation audit

The crawler package includes a read-only metadata audit for comparing the data
branch's checkpoint, manifest, and physical shard inventory. Prepare three
UTF-8 JSON files: the decoded `state/checkpoint.json`, decoded
`state/manifest.json`, and a JSON array of shard inventory objects containing
`path`, `size`, and Git blob `sha` fields. Then run:

```bash
python -m tools.usg_external_lexical_v0_1_0 audit \
  --checkpoint checkpoint.json \
  --manifest manifest.json \
  --shard-inventory shard-inventory.json
```

Exit code 0 means metadata reconciles (possibly with warnings); exit code 1
means a consistency error was found; exit code 2 means the audit inputs could
not be read or parsed. Identical duplicate shard blobs are warnings, not
silently discarded: their physical bytes remain included in storage totals.
The audit is read-only and does not modify checkpoints, manifests, or shards.


## Automatic post-crawl reconciliation

After each successful crawl batch, the workflow runs a final read-only audit
step in the same job. It fetches the current checkpoint and manifest from the data branch and
uses the Git tree inventory to reconcile every compressed shard for the pinned
snapshot. A truncated Git tree response fails closed. Counter mismatches,
missing last-batch shards, byte-accounting errors, or conflicting duplicate
batch IDs fail the audit. Identical historical duplicate copies are reported
as warnings and remain included in physical storage accounting.

The same operation can be run manually from a checkout with a GitHub token:

```bash
GITHUB_TOKEN=... python -m tools.usg_external_lexical_v0_1_0 audit-remote \\
  --repository wizekin/USG-Workbench \\
  --branch usg-external-lexical-data
```
