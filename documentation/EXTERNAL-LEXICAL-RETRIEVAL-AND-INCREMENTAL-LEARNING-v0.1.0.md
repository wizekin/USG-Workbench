# External Lexical Retrieval and Incremental Analysis — v0.1.0

**Status:** Initial implementation; additive subsystem, not connected to the accepted runtime interpreter.

## Objective

Allow USG to consult large public English lexical sources without importing their full inventories into the USG repository. USG requests an individual spelling only when it needs lexical evidence. Retrieved records are normalized, checked, analyzed, and retained in a small local cache so repeated requests do not require repeated network calls.

The subsystem is intentionally separate from the Phase 5 interpretation pipeline and the canonical semantic-document SQLite database.

## Retrieval model

    User / optional future USG lexical request
                      |
                      v
              Local word cache
                 /       \
            cache hit   cache miss
               |            |
               |            v
               |     Provider adapters
               |       /     |      \
               |      /      |       \
               |   Free    Dictionary GitHub
               |   Dictionary API      dictionary
               |   API       dev       entry index
               |      \       |        /
               |       \      |       /
               |        v     v      v
               |     Normalized source records
               |                  |
               |                  v
               |        Structural validation
               |                  |
               |                  v
               |       Lexical observations / graph
               |                  |
               |                  v
               |           Local SQLite cache
               |                  |
               +------------------+
                                  |
                                  v
                    Explicit USG candidate export
                     (no runtime promotion here)

The GitHub provider reads the relevant alphabetical index and one matching page to locate the requested spelling, then fetches the selected entry file. It does not download the complete browse indexes, every entry, a repository archive, or the 1.4-million-headword inventory. Dictionary API providers receive only the requested word.

The local cache is outside the repository by default:

- Windows: %LOCALAPPDATA%\USG\cache\external-lexical.sqlite3
- Other platforms: ~/.cache/usg/external-lexical.sqlite3
- Override: set USG_LEXICAL_CACHE_PATH to another path.

Only words that have actually been requested are cached. The positive-record lifetime is 30 days; a not-found result is cached for one hour. The refresh option bypasses a fresh record and also resolves a new pinned GitHub source commit. The offline option uses cached material only.

## Ten implementation points

| # | Roadmap point | Implementation in v0.1.0 |
|---:|---|---|
| 1 | External vocabulary discovery | On-demand GitHub alphabetical-index navigation. No headword dump or bulk corpus import. |
| 2 | Definition retrieval | Fetch only the selected GitHub entry and/or requested API word record. |
| 3 | Structured lexical normalization | Separate entries, records, parts of speech, forms, pronunciations, senses, examples, tags and provenance. |
| 4 | Lexical relationships | Preserve explicit synonyms and antonyms at their original scope. Sense relations remain sense-scoped; entry relations remain entry-scoped. |
| 5 | Morphological evidence | Retain observed source forms and provider tags. Do not invent unobserved inflection tables. |
| 6 | Definition-pattern discovery | Apply transparent, versioned rules to produce raw-definition-linked pattern observations. |
| 7 | Semantic candidate graph | Build lemma, entry, sense and form nodes with typed, source-scoped edges. |
| 8 | Validation and source comparison | Check structural contracts, missing provenance and relation scope; report cross-provider differences without choosing a winner. |
| 9 | USG integration boundary | Export USG-LEXICAL-CANDIDATES/0.1.0. Export is non-mutating and all candidates remain unpromoted. |
| 10 | Evaluation | Run an offline fixture suite for pattern handling, relation scope, homograph separation and structural validation. This is not a claim of broad linguistic accuracy. |

## Providers and source handling

### FreeDictionaryAPI.com

Endpoint:

    https://freedictionaryapi.com/api/v1/entries/en/{word}

The adapter reads its documented entries structure, including parts of speech, forms, pronunciations, senses, examples, tags, synonyms, antonyms, and source/license information. The provider documents a limit of 1,000 requests per hour per IP. USG enforces a conservative local rolling budget of 900 requests per hour for this provider. That local budget cannot coordinate other devices or applications sharing the same public IP.

The provider states that its dictionary data comes from Wiktionary under CC BY-SA 4.0 and requires attribution to the original Wiktionary page and FreeDictionaryAPI.com. The returned source URL and license notice are retained. Do not redistribute an adapted dataset without checking and satisfying the applicable attribution and ShareAlike conditions.

### dictionaryapi.dev

Endpoint:

    https://api.dictionaryapi.dev/api/v2/entries/en/{word}

The adapter reads the v2 array response and keeps separate meanings and definitions, with examples and any returned synonyms/antonyms. It preserves sourceUrls and any license fields actually supplied. The provider response does not always provide a complete data-license declaration; USG marks missing license information rather than assuming that the data is freely redistributable.

### figueirego/english-dictionary

The provider uses the source's alphabetical browse indexes only to locate an exact or case-folded candidate. It then fetches the corresponding individual Markdown entry at a pinned commit.

The entry parser preserves source entry IDs, source URLs, history URLs, snapshot IDs, record numbers, source sense IDs, part of speech, examples, and the source's review-status metadata. The upstream publication identifies Wiktionary-derived material under CC BY-SA 4.0 but documents supplemental content with separate licences. Rights are therefore retained per source record; the code does not assign one blanket licence to every entry.

The upstream entry format itself warns that some related-word links are attached to a whole headword entry and are not sense-resolved. Those remain entry-level edges in USG and cannot be used as proof that two words are interchangeable in a particular sentence.

## Normalized record boundaries

The normalized bundle uses:

- **Entry:** a provider/source record with one lemma candidate and a part of speech.
- **Sense:** one source-specific meaning with its original definition and source sense identifier.
- **Cumulative graph:** a rebuildable local view assembled from cached entries across prior lookups; it is not a canonical ontology.
- **Form:** a spelling explicitly observed in the source, together with source tags.
- **Relation:** a provider-asserted relation with a relation type, direction, source sense (when present), and an explicit sense or entry scope.
- **Source:** provider identity, record/history URLs, snapshot or revision identifiers, and license/attribution notes.

Records from different providers are not collapsed. Similar wording does not prove that two definitions represent the same sense. Differences are retained in cross_source_disagreements.

## Definition analysis and graph boundaries

The first definition analyzer recognizes a small set of visible surface patterns such as:

- person / one who ...
- act, action, process, state, or quality of ...
- type / kind / sort / form of ...
- a broader initial nominal phrase.

Every result preserves the full original definition and the exact matched prefix. It is labelled unvalidated_observation. These patterns are discovery aids, not a complete definition grammar and not validated ontological classes.

The candidate graph retains source-scoped edges. A source-provided synonym is evidence that the provider lists a relationship; it does not establish universal substitutability, identity, entailment, or truth.

Morphology is similarly evidence-led. Explicit forms and tags are retained, but the subsystem does not generate a complete paradigm from a few observed forms.

## Incremental learning and cache behavior

The system accumulates lexical evidence as users request words:

1. Cache lookup occurs first.
2. A cache miss triggers the configured provider adapters.
3. Each returned record is normalized independently.
4. Structural checks and analysis observations are generated.
5. Retrieved records and analysis observations are saved locally.
6. Every access updates local use counts and recency.
7. Future requests can be served from the local cache.
8. The cumulative candidate graph can be rebuilt from all cached word records, joining repeated lemma candidates and preserving relation scope across lookups.

Inspect the locally accumulated graph with:

    py -m tools.usg_external_lexical_v0_1_0 graph --limit 10000

The graph command performs no network requests. It only reconstructs a rebuildable view from words previously retrieved into the local cache; it reports the words and records that are stale.

The activity ranking measures how often a word has been requested in this local installation. It is not an English-language frequency list, semantic importance score, or probability.

This is incremental knowledge acquisition, not model training. It does not autonomously create new grammar rules, validate facts, or rewrite a USG resource.

## Run

From the repository root on Python 3.10+:

    py -m tools.usg_external_lexical_v0_1_0 lookup photosynthesis
    py -m tools.usg_external_lexical_v0_1_0 analyze photosynthesis
    py -m tools.usg_external_lexical_v0_1_0 export photosynthesis
    py -m tools.usg_external_lexical_v0_1_0 activity --limit 20
    py -m tools.usg_external_lexical_v0_1_0 benchmark

Use one or more providers explicitly:

    py -m tools.usg_external_lexical_v0_1_0 lookup bank --providers freedictionaryapi dictionaryapi_dev

Refresh cached data or work offline:

    py -m tools.usg_external_lexical_v0_1_0 lookup bank --refresh
    py -m tools.usg_external_lexical_v0_1_0 lookup bank --offline

Choose a separate cache path:

    py -m tools.usg_external_lexical_v0_1_0 --cache D:\USGData\external-lexical.sqlite3 lookup bank

No API key, paid service, additional Python package, or full-corpus download is required.

## Versioned candidate adapter contract

The external lexical service exposes candidate packages under `USG-LEXICAL-CANDIDATES/0.1.0`, defined by:

- `specifications/usg-lexical-candidates-0.1.0.schema.json`
- `tools/usg_external_lexical_v0_1_0/adapter.py`

Use `validate_candidate_package(package)` to check contract identity, candidate counts, stable candidate IDs, source provenance, required source identity fields, and the candidate-only boundary. Use `adapt_candidate_package(package)` to obtain a deterministic read-only view under `USG-LEXICAL-ADAPTER/0.1.0`.

The adapter preserves separate senses and source provenance. It does not resolve ambiguity, choose an authoritative provider, infer a unique POS or lemma, write to a runtime `LexicalResource`, or promote candidates. A null native source-sense identifier is permitted when the provider does not supply one, but the field must remain present so absence is explicit.

The adapter digest identifies the normalized read-only view. It is not a semantic-quality score and does not establish correctness. Contract validation is structural only.

## Runtime and persistence boundaries

- Existing Phase 4 and Phase 5 interpreter behavior is unchanged.
- Existing USG-SEM/1.0 and USG-INTERPRET contracts are unchanged.
- The canonical Phase 3 SQLite semantic-document store is unchanged.
- The lexical cache is a separate, rebuildable local store.
- The export adapter produces candidates only. It does not modify resources/lexical, the resource manifest, grammar, predicate frames, or the interpreter.
- Promotion requires a separately designed, versioned mapping, conformance tests, and regression evaluation.

## Evaluation

Run:

    py -m tools.usg_external_lexical_v0_1_0 benchmark
    py -m unittest discover -s tests -p "test_external_lexical_retrieval.py" -v

The benchmark checks subsystem contracts with offline fixtures. It does not measure coverage of the 1.4 million entries, certify source accuracy, or establish broad English understanding. Provider availability and the actual source content are not tested during normal CI to keep builds reproducible and network-independent.

## Source references

- FreeDictionaryAPI: https://freedictionaryapi.com/ and https://freedictionaryapi.com/api/v1
- dictionaryapi.dev API usage and v2 response examples: https://github.com/meetDeveloper/freeDictionaryAPI
- English dictionary source index: https://github.com/figueirego/english-dictionary
- English dictionary source metadata: https://github.com/figueirego/english-dictionary/blob/main/dictionary/SOURCE.md
- English dictionary licensing: https://github.com/figueirego/english-dictionary/blob/main/LICENSE.md
- Wiktionary CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/
