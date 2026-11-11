# External English Lexical Corpus — Initial Import

## Objective

Add a large, provenance-aware English vocabulary inventory to USG without changing
the existing Phase 5 lexical analyzer. The first stage collects headword candidates
and pointers to source entries. Definition enrichment is a later, demand-driven stage.

## Verified source snapshot

The linked repository,
https://github.com/figueirego/english-dictionary, currently publishes 1,396,111
exact headwords, 1,499,161 English lexical records, and 1,795,048 source sense
positions. Its Markdown export is about 5.4 GB and is divided into alphabetical
browse pages and individual entry files. The browse pages contain roughly 1,000
candidate labels each, plus a relative path to the full source entry.

The importer fetches the small root and source indexes, alphabetical letter indexes,
and browse pages only. It does not fetch all individual entry files. This avoids
cloning the full multi-gigabyte data export.

## Run

From the USG repository root, first run a small pilot:

    python -m tools.usg_lexical_corpus_v0_1_0.import_headwords --max-pages 2

Then import the complete headword inventory:

    python -m tools.usg_lexical_corpus_v0_1_0.import_headwords

Optional settings include --workers 2 or --workers 4, --ref main, and --output
PATH. The importer resolves the requested Git ref to one commit SHA before reading
any content, so all pages in a run come from the same immutable source revision.

By default, it writes:

- data/lexical-corpus/english-headwords.jsonl.gz
- data/lexical-corpus/english-headwords.jsonl.gz.manifest.json

The compressed corpus is intentionally kept outside Git. The manifest records the
source repository, commit, Wiktionary snapshot, expected and imported counts,
output checksum, and rights/usage boundaries. A complete import is rejected if
its final unique count differs from the source index's declared headword count.
Using --max-pages produces a clearly marked incomplete pilot inventory.

## What a record means

Each JSONL row contains a stable USG-side candidate ID, the displayed headword
candidate, a case-folded lookup key, the relative source entry path, a commit-pinned
GitHub URL, the dictionary snapshot ID, and a note that rights must be checked
per entry.

A browse label is not always guaranteed to be the exact underlying headword.
For example, the source renders some unusual symbols with explanatory labels.
Therefore the importer preserves the browse label as a candidate and does not
claim that it has verified every headword against the entry front matter.

## Important boundary: inventory is not a lexical sense

The current USG LexicalResource requires explicit form, lemma, part of speech,
sense ID, and features. A large list of headword candidates cannot safely satisfy
that contract. The importer therefore does not alter or extend the runtime lexical
resource. Unknown words can later be matched against this inventory as
"known source candidate, not yet sense-resolved" without pretending that a sense
has been understood.

The next stage should retrieve selected entry files on demand, parse each separate
record and sense, retain the source's exact IDs and page/history links, and map
only verified fields into an external lexical knowledge store. Synonyms should
remain sense- and source-scoped; a shared headword or a thesaurus link alone does
not establish that two words are interchangeable in every context.

## Licensing and attribution

The source repository's base English Wiktionary-derived content is CC BY-SA 4.0,
but its licensing document explicitly identifies supplements with different
licences. The importer therefore records rights as per-entry rather than assigning
one licence to every word. Later definition imports must preserve each entry's
source page, contributor/history link, applicable licence, and notice of changes.
Redistribution of adapted CC BY-SA material must comply with its attribution and
share-alike requirements. See:

- https://github.com/figueirego/english-dictionary/blob/main/LICENSE.md
- https://github.com/figueirego/english-dictionary/blob/main/dictionary/SOURCE.md

## Planned enrichment order

1. Bulk headword inventory from the GitHub browse indexes.
2. On-demand retrieval of source entry files and extraction of separate records,
   forms, parts of speech, senses, examples, synonyms, antonyms, and topic labels.
3. Secondary API lookups through DictionaryAPI.dev and FreeDictionaryAPI.com,
   cached locally and stored with independent provider/version/licence metadata.
4. USG analysis of reusable definition patterns, semantic roles, genus/differentia
   structures, relation types, and ambiguity—without collapsing source senses.
5. Evaluation against held-out words and sentences before any extracted knowledge
   is allowed to influence lexical selection.

The two API sources are enrichment providers, not a reason to issue one request for
every word immediately. FreeDictionaryAPI documents a limit of 1,000 requests per
hour per IP and identifies Wiktionary CC BY-SA 4.0 as its data source. API results
should be cached and fetched only when a word is needed.
