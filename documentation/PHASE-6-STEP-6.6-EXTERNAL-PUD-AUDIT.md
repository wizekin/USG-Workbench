# Phase 6 Step 6.6 — Independent PUD Structural Audit v0.1

**Status:** external structural audit; candidate-only; not Step 6.6 acceptance.

## Sources and reproducibility

This audit reads the English and Arabic Parallel Universal Dependencies (PUD)
treebanks. Each source contains 1,000 sentences and text with syntactic
annotations. Both are licensed CC BY-SA 3.0. The exact repository commits and
Git blob SHA-1 values are pinned in `tools/phase6_external_pud_v0_1/run.py`.
The downloader verifies Git's blob hash before parsing, so a changed upstream
file fails closed. Source text is downloaded at test time and is not copied
into this repository.

- English: `UniversalDependencies/UD_English-PUD`, `en_pud-ud-test.conllu`.
- Arabic: `UniversalDependencies/UD_Arabic-PUD`, `ar_pud-ud-test.conllu`.
- Attribution: Universal Dependencies PUD contributors; see each source
  repository's README and LICENSE.txt. License: CC BY-SA 3.0.

## Evaluation design

Gold candidates are selected exclusively from the treebanks' CoNLL-U POS tags,
dependency relations, and token order. The USG analyzer is called only after
gold extraction; its output never creates, filters, or rewrites expected labels.
This removes the circular positive-case generation in the earlier v0.4.3
combination test.

The adapter currently measures exact candidate recall for a conservative
subset of structural proxies:
- English adjective modifiers, `of` genitives, noun compounds,
  prepositional nominal modifiers, and subject–verb–adverb sequences.
- Arabic adjective modifiers, adjacent `nmod` nominal pairs, prepositional
  nominal modifiers, and verb–subject–adverb sequences.

The Arabic lexicalized-compound subtype is intentionally not scored: UD
dependency syntax alone cannot establish that semantic subtype. Profiles with
no eligible cases are omitted from the per-profile report.

## Important interpretation limits

This is **not** a human-adjudicated USG semantic-role gold corpus. UD dependency
labels are syntactic evidence and only approximate some USG construction
boundaries. Arabic PUD UPOS and dependency relations were converted to UD from
prior annotation. The candidate lexicon remains closed and was derived from USG
development fixtures. Consequently, this audit does not test unseen vocabulary.

The report measures recall on extracted eligible structures only. It does not
measure precision, full-sentence coverage, calibrated confidence, or broad
semantic correctness. It cannot enable any construction or satisfy the full
independent semantic benchmark acceptance gate. All constructions remain
candidate-only. Step 6.7 remains blocked.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud.py' -v
python -m tools.phase6_external_pud_v0_1.run
```

The generated report is written to
`artifacts/phase6-step-6.6-pud-report.json`.
