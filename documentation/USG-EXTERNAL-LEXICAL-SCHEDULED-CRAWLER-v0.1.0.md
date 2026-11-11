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
- state/checkpoint.json: immutable source snapshot, page/entry cursor, cumulative counters, and next resume position.
- state/manifest.json: cumulative counts, compressed bytes, batch count, and last batch metadata.
- shards/<snapshot-id>/batch-*.jsonl.gz: append-only per-run lexical analysis results.

The workflow publishes each batch through GitHub's Git Data API. It does not check out or download the growing data branch on every run. It retrieves only the small checkpoint from the branch, then uploads the new shard and updated state.

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

The worker records failed entry fetches and parser failures as compact failure events and continues where it can. A transient source rate limit stops the run without advancing past the current headword.

## Run manually

Open the repository's Actions tab, select **USG External Lexical Incremental Crawl**, and choose **Run workflow**.

The manual default is a 200-headword / 15-minute pilot. To run a larger manual batch, supply:
- max_headwords: up to 30,000.
- max_runtime_minutes: up to 320.

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
