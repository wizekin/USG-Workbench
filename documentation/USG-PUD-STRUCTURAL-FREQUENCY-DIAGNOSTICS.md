# SYS-08: PUD Structural-Frequency Diagnostics

**Status:** implementation branch; full-campaign evidence pending  
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

Both sources are CC BY-SA 3.0. Campaign publication must retain `LICENSE.txt`, `ATTRIBUTION.md`, and `source-manifest.json`. The existing privacy screen rejects email and URL patterns, but is not a comprehensive personal-data detector and retains public proper names.

PUD is news/Wikipedia text, not conversational user requests. Arabic PUD is translated and is not a representative native-MSA distribution. English PUD also contains translated sentences.

## Construction selection policy

The report deliberately does not automatically select or promote a construction. After the full bilingual campaign is available:
1. compare per-language sentence frequencies and instance counts;
2. identify one bounded construction whose evidence is meaningful in both populations or explicitly record the language imbalance;
3. inspect the existing USG syntax, composition, operator, and discourse interfaces before proposing work;
4. freeze positive, negative, ambiguous, and attachment-boundary fixtures;
5. define independent construction-level semantic gold and adjudication under SYS-09 before any semantic rule promotion.

A high UD frequency alone is not a reason to expand runtime behavior.

## Verification status

The new unit fixtures cover parser behavior, multiword/empty-node exclusion, separate sentence and instance denominators, active/passive distinction, malformed input, empty-population handling, source-hash reconciliation, and the explicit no-semantic-gold boundary.

Passing these unit tests is component-level diagnostic verification only. The first full naturalistic PUD campaign and its generated structural-frequency artifact are still required before SYS-08 can be considered evidence-complete.
