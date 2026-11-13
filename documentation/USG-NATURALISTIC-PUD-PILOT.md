# Bilingual Naturalistic PUD Evaluation Pilot

**Contract:** `USG-NATURALISTIC-CORPUS-MANIFEST/0.1.0`  
**Population:** `naturalistic` (kept separate from randomized and controlled-diagnostic populations)  
**Use:** unlabeled evaluation input only; not training data and not semantic gold.

## Sources and licensing

This pilot samples the English and Arabic Parallel Universal Dependencies (PUD) treebanks:

- [UD_English-PUD](https://github.com/UniversalDependencies/UD_English-PUD) — pinned commit `a697bab43d4111073356de0df5802488bca3de7e`.
- [UD_Arabic-PUD](https://github.com/UniversalDependencies/UD_Arabic-PUD) — pinned commit `c606299bc9eb8baa6c61c8dd3efc9a0fbf73aa87`.

Both repositories declare **CC BY-SA 3.0** and describe the source genre as news and Wikipedia. The workflow downloads the exact CoNLL-U files from those immutable commits, hashes them, retains source sentence IDs, and includes the upstream license text and attribution notice in every campaign bundle. Redistribution of the extracted sentence text and derived scenario artifacts is under CC BY-SA 3.0 with attribution and share-alike terms.

The PUD treebanks contain 1,000 sentences per language. The English set contains 750 originally English sentences and 250 translations from other European languages. The Arabic set is translated: 750 sentences originate in English and 250 originate in German, French, Italian, or Spanish and are translated via English. Therefore this is a useful bilingual news/Wikipedia stress population, but it is **not** a representative native-Arabic MSA corpus or a conversational user-request corpus.

## Sampling and privacy checks

The default pilot selects 50 sentences per language by deterministic SHA-256 ranking from the pinned source file. It:

1. extracts the CoNLL-U `# text` field verbatim;
2. deduplicates within each language using Unicode NFKC plus whitespace normalization;
3. rejects sentences matching email-address or URL patterns;
4. retains public proper names as part of the public news/Wikipedia text;
5. records retrieval date, pinned repository commit, file hash, source sentence ID, license, attribution, transformations, and rejection counts.

The privacy review is scoped to this bounded internal evaluation: no user-submitted or private chat material is used; public proper names remain; the direct-contact pattern screen is not a comprehensive personal-data detector; no sensitive-attribute inference or user profiling is performed. The source and privacy assessment are recorded in `source-manifest.json`.

## Evaluation boundary

- Every case has `population: naturalistic`.
- The oracle is explicitly `none`; no semantic correctness score is inferred.
- UD POS and dependency annotations are not used as USG semantic-role or semantic-frame gold.
- The PUD test set is used only as evaluation input, not as training material.
- The JS Workbench is English-only; Arabic cases are expected to be marked unsupported by that target, not translated.
- Results are reported separately from randomized and controlled-diagnostic cases.

## Structural-frequency diagnostics (SYS-08)

The pilot generator now emits `structural-frequency.json` from the **full pinned PUD treebanks**, separately from the sampled scenario population and campaign outcome counts. It reuses the existing Phase 6 external-PUD structural extractor rather than creating a second construction parser. The report is content-hashed from `generation-manifest.json` and copied into the campaign bundle.

The latest independently recorded PUD structural audit (workflow run [42987777649](https://github.com/wizekin/USG-Workbench/actions/runs/42987777649)) extracted 393 eligible contiguous structural cases: 254 English and 139 Arabic. Its construction counts were:

| Structural family | English | Arabic |
|---|---:|---:|
| Nominal adjective modifier | 72 | 42 |
| Genitive surface pattern | 77 | 46 |
| Prepositional nominal modifier | 56 | 45 |
| Temporal adverbial modifier | 5 | 6 |

**Selected candidate for SYS-09 annotation:** nominal adjective modification (`en.nominal.adjective_modifier` / `ar.nominal.adjective_modifier`), with 72 English and 42 Arabic eligible cases. This is a bounded, already represented candidate family with a shared UD `amod` structural proxy and language-specific ordering to evaluate. Genitive and prepositional families have greater unresolved relation/attachment ambiguity. The selection is an annotation priority only.

These counts are **eligible structural proxies**, not total raw occurrences and not semantic gold. The previous audit had zero exact candidate matches and abstained on all 114 adjective-modifier cases; that is a coverage diagnostic, not proof that the construction or its semantics are incorrect. The new report explicitly records that UD annotations are not USG semantic gold and that runtime promotion is prohibited.

The PUD source population remains news/Wikipedia text, not conversational requests. Arabic PUD is translated and is not a native-MSA distribution. Structural-frequency counts must not be merged with randomized, controlled-diagnostic, or naturalistic campaign outcome denominators.

## Run locally

    python -m tools.open_world_evaluation.pud_naturalistic_pilot \
      --sample-per-language 50 \
      --target js-semantic-workbench-v054 \
      --target phase4-bounded-interpreter \
      --target phase5-bounded-interpreter \
      --output-dir ./pud-naturalistic-pilot

The scheduled workflow executes the generated cases, scores outcomes, builds the campaign bundle, and opens an append-only report PR. A completed pilot measures coverage, abstention, and stage blockers; it does not establish broad semantic accuracy.
