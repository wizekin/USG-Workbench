# OW-7 — Continuous open-world exploration

**Status:** OW-7 implementation  
**Workflow:** `.github/workflows/open-world-continuous.yml`

## Cadences and budgets

| Trigger | UTC schedule / event | Base prompts | Target-matrix cases | Diagnostic cases | Total planned cases |
|---|---|---:|---:|---:|---:|
| Daily smoke | 02:15 UTC daily | 20 | 60 | 106 | 166 |
| Weekly deep | 03:30 UTC every Monday | 100 | 300 | 106 | 406 |
| Release | Published GitHub release | 250 | 750 | 106 | 856 |
| On demand | Manual workflow dispatch | 1–2,000 (default 100) | 3–6,000 | 106 | 109–6,106 |

Each campaign runs the same versioned random generator, controlled diagnostic importer, isolated runner, scorer, and append-only report publisher. The profile resolver enforces campaign limits before generation. One concurrency group prevents scheduled and manually requested runs from overlapping; queued work is not cancelled.

## Published evidence

Every run:
- pins the tested Git commit;
- records the campaign cadence and seed in a generation manifest;
- executes the three currently registered targets, with the browser-only JavaScript interface explicitly marked `not_executed`;
- preserves separate random and controlled diagnostic populations;
- assigns semantic scores only to imported diagnostic fields with an independent oracle declaration;
- produces JSON/Markdown report bundles and a SHA-256 manifest;
- uploads a GitHub Actions artifact and opens a new report PR under a unique campaign directory.

The naturalistic population remains empty until a dataset passes source-license, redistribution, attribution, provenance, and privacy review. Reports therefore remain partial by design.

## Resource and safety policy

- Daily 20, weekly 100, and release 250 prompts are bounded default budgets.
- Manual runs are limited to 2,000 base prompts.
- Each case has its own wall-time and memory limit; the runner also applies the per-job ceiling.
- Test content is passed as JSON data, not shell code.
- The workflow compares target-specific failure signatures with prior campaign reports. Structural/runtime failures can produce up to 150 formatting-only follow-up cases per campaign; unsupported/ambiguous/partial/not-executed outcomes do not automatically trigger mutations. The follow-up cases are executed and rescored before the final report is created.
- The workflow does not tune USG from test failures or alter grammar/resources.
- The adaptive comparison labels a cluster candidate-new only when it is absent from the scanned history directory; this is not proof of global novelty.
- Hidden seed rotation is not yet implemented because public manifests/artifacts cannot safely hold a hidden seed or hidden corpus.
- The workflow cannot prove unrestricted coverage; it keeps an expanding sample and exposes untested areas.

## OW-7 acceptance

OW-7 is accepted when profile selection and limits are unit-tested, daily/weekly/release/manual triggers are configured, all campaigns use the same validated pipeline, report publication is append-only, and the prior Phase 3–6 and OW-0–OW-6 regression workflows remain green.
