# SYS-08: PUD Structural-Frequency Diagnostics

**Status:** implementation branch; first naturalistic campaign executed without this diagnostic; structural-frequency campaign evidence pending  
**Contract:** `USG-PUD-STRUCTURAL-FREQUENCY/0.1.0`  
**Population:** pinned English and Arabic PUD, kept separate

## Purpose

The naturalistic PUD pilot extracts source text for evaluation. This diagnostic adds reproducible counts of selected syntactic constructions from the same pinned CoNLL-U source files. It is intended to inform which bounded construction should be investigated next; it does not evaluate USG semantic correctness.

The diagnostic runs after the PUD generator creates `source-manifest.json`. It downloads the same pinned source files, verifies each Git blob SHA-1 and content SHA-256 against the generator's manifest, and writes `structural-frequency.json`. The source manifest is updated with the report's SHA-256 and per-language sentence denominators. Raw CoNLL-U source text is not copied into the campaign artifact.

## Fixed UD proxy definitions

Each language is reported independently. For each construction, the report includes:
- sentence count containing at least one match;
- dependency/root instance count;
- sentence-presence rate;
- sentence-presence count per 1,000 sentences;
- instance count per 1,000 sentences.

| Diagnostic | UD proxy rule |
|---|---|
| Relative-clause attachment | One or more `acl:relcl` arcs |
| Active transitive root | A root `VERB` with a direct `obj` dependent and no passive marker |
| Copular predicate | A predicate head with a dependent `cop` |
| Clause complement | One or more `ccomp` or `xcomp` arcs |
| Passive root | A root `VERB` with `Voice=Pass`, `aux:pass`, `nsubj:pass`, or `csubj:pass` |
| Adverbial clause | One or more `advcl` arcs |
| Coordination | One or more `conj` arcs |

Multiword-token and empty-node rows are excluded from syntactic word-token counts. Malformed rows fail closed rather than being silently ignored.

## Evidence boundary

These are Universal Dependencies syntactic proxies. In particular, UD `nsubj` and `obj` are not treated as USG semantic Agent and Patient roles. The diagnostic does not label semantic frames, argument roles, discourse relations, or truth conditions. It does not turn PUD annotations into semantic gold.

The source manifest records the pinned commits:
- English: `UD_English-PUD@a697bab43d4111073356de0df5802488bca3de7e`
- Arabic: `UD_Arabic-PUD@c606299bc9eb8baa6c61c8dd3efc9a0fbf73aa87`

Both sources are CC BY-SA 3.0. Campaign publication must retain `LICENSE.txt`, `ATTRIBUTION.md`, and `source-manifest.json`. The current attribution file names Universal Dependencies contributors and points to the pinned upstream READMEs; the named contributor lists are not embedded in the campaign bundle. Before external redistribution, verify whether the pinned README files or their complete contributor/acknowledgement content should also be included to make attribution self-contained.

The existing privacy screen rejects email and URL patterns, but is not a comprehensive personal-data detector and retains public proper names.

PUD is news/Wikipedia text, not conversational user requests. Arabic PUD is translated and is not a representative native-MSA distribution. English PUD also contains translated sentences.

## First naturalistic campaign — 2026-11-16

The first full 50-per-language campaign ran on main commit `8e3f1308882b2e8ce581350746d9ee76fca31216` before this branch's workflow integration was available:

- Run: [43810018720](https://github.com/wizekin/USG-Workbench/actions/runs/43810018720)
- Campaign: `OWC-NAT-PUD-43810018720-1`
- Population: 300 naturalistic cases; 150 English and 150 Arabic
- Target matrix: 100 records each for JS Workbench, Phase 4, and Phase 5
- Actual attempts: 300; completed 4, partial 245, unsupported 51
- First blockers: lexical 100, syntax 99; no semantic-scored attempts
- No independent USG semantic gold was available
- The JS Workbench executed 50 English cases (4 completed, 46 partial) and returned unsupported for all 50 Arabic cases; this confirms the current English-only boundary, not semantic correctness

The campaign artifact was uploaded and its report branch was pushed as `reports/naturalistic-pud-43810018720-1` at commit `e6841e98d5512c19b98b58e15da0ec956d3d60af`. Pull-request creation failed because GitHub Actions is not permitted to create or approve pull requests. Therefore the report is not committed to main, auto-merge was not attempted, and the naturalistic population is executed artifact evidence rather than accepted committed campaign history.

The first campaign has no `structural-frequency.json`: it ran before the branch workflow change. This branch's updated workflow adds the diagnostic and publication-failure reporting, but that workflow has not yet completed a full campaign. Do not reuse the first campaign's execution results as proof that the new diagnostic ran.

## Measured full-treebank frequencies — 2026-11-16

A manual reproduction was completed against the exact pinned CoNLL-U blobs. Both Git blob SHA-1 and content SHA-256 matched the campaign source manifest. The full machine-readable report is [pud-structural-frequency-manual-2026-11-16.json](../evaluations/system-wide/pud-structural-frequency-manual-2026-11-16.json).

| UD proxy | English sentences / instances per 1,000 | Arabic sentences / instances per 1,000 |
|---|---:|---:|
| Relative-clause attachment | 193 / 211 | 265 / 319 |
| Active transitive root | 295 / 295 | 241 / 241 |
| Copular predicate | 286 / 319 | 93 / 95 |
| Clause complement (`ccomp` or `xcomp`) | 348 / 453 | 349 / 437 |
| Passive root | 141 / 141 | 85 / 85 |
| Adverbial clause | 241 / 294 | 274 / 315 |
| Coordination (`conj`) | 428 / 634 | 440 / 661 |

Denominators are 1,000 sentences per language (21,180 English syntactic word tokens; 20,747 Arabic). These are descriptive counts from the pinned PUD test treebanks, not population estimates.

The actual naturalistic campaign used 50 unique sentences per language, repeated across three targets (300 target records total). On those same source sentences, the combined clause-complement proxy appeared in 18/50 English sentences (23 instances) and 16/50 Arabic sentences (18 instances). The `ccomp` and `xcomp` subtypes both occurred in both languages, but their balance differs; preserve the subtype as a separate stratum.

## Candidate construction selection

**Selected for independent annotation/evaluation design only:** `clause_complement.ccomp_xcomp`.

Reasons:
1. Full-treebank sentence presence is closely balanced (34.8% English; 34.9% Arabic).
2. The actual 50-sentence-per-language naturalistic sample is also reasonably balanced (36% English; 32% Arabic).
3. Both `ccomp` and `xcomp` occur in both languages, so a bounded evaluation can explicitly test the distinction rather than treating the labels as interchangeable.
4. The current accepted Phase 4 interpreter has only tiny SVO/VSO patterns, while the Phase 5 roadmap documents no nested or multi-clause syntax.
5. The existing Phase 6 continuation item P6-CONT-02 already covers broader embedded/subordinate/relative/argument-gap attachment; SYS-09 should supply its independent evidence path rather than duplicate runtime functionality.

The broader `conj` frequency is higher, but it mixes phrase-level and clause-level coordination and is not a sufficiently specific proxy for one clause-level semantic construction. Clause complement is therefore the more bounded initial candidate.

This selection is **CANDIDATE_ONLY**. Frequency does not establish semantic correctness, and no runtime rule or semantic relation is enabled.

The first naturalistic campaign (run [43810018720](https://github.com/wizekin/USG-Workbench/actions/runs/43810018720)) still has 300 actual attempts (4 completed, 245 partial, 51 unsupported), 100 lexical and 99 syntax first blockers, and zero semantic-scored attempts. Its campaign artifact did not contain `structural-frequency.json`; the manual full-treebank report is separate from that campaign artifact.

## Verification status

- Both pinned source Git blob SHA-1 values and content SHA-256 values were verified against the PUD campaign source manifest.
- The seven documented UD proxy rules were manually reproduced over the full pinned English and Arabic CoNLL-U sources; the report contains exact denominators and source hashes.
- The report is a manual analysis artifact, **not** a GitHub Actions run and not execution evidence for the branch's Python module.
- The branch contains eight unit tests, but no GitHub Actions run has tested this branch's workflow or test suite. Their presence is not a CI pass.
- The first full naturalistic campaign ran on main before the SYS-08 workflow integration and has no structural-frequency artifact.
- SYS-08 has completed the full-treebank frequency measurement and candidate selection. It remains incomplete until the branch tests/workflow are executed, a full campaign emits the structural-frequency artifact, and positive/negative/ambiguous/boundary fixtures are frozen.
- No independent semantic gold exists for this construction. No semantic runtime, lexical resource, or canonical contract was changed.
