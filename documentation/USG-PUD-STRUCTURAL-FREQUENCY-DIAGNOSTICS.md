# PUD Structural-Frequency Diagnostics

**Contract:** USG-PUD-STRUCTURAL-FREQUENCY/0.1.0  
**Workstream:** SYS-08  
**Evidence boundary:** descriptive Universal Dependencies syntactic proxies, not USG semantic gold.

## Purpose

The bilingual naturalistic pilot previously extracted text and created target cases but did not calculate construction-frequency diagnostics. This analyzer measures selected syntactic patterns over the complete pinned English and Arabic PUD files. It supports bounded construction selection; it does not score USG semantic correctness.

Run it with:

~~~bash
python -m tools.open_world_evaluation.pud_structural_frequency \
  --source-manifest /path/to/pud-naturalistic/source-manifest.json \
  --output /path/to/pud-structural-frequency-report.json
~~~

The analyzer downloads only the two pinned CoNLL-U files, verifies their Git blob SHA-1 and content SHA-256 against the source manifest, applies the pilot's existing email/URL screen and within-language deduplication, and writes aggregate counts only. No sentence text, token examples, or annotations are persisted.

## Construction definitions

All sentence rates use the count of privacy-screened, deduplicated sentences with exactly one UD root as the denominator. Counts are sentence-presence counts, not token counts.

| Metric | Operational definition |
|---|---|
| Relative clause | At least one token has DEPREL=acl:relcl anywhere in the sentence |
| Active transitive root | Root has UPOS=VERB, a direct nsubj or nsubj:outer, and a direct obj |
| Copular predicate root | Root has a direct cop child |
| Clause complement root | Root has a direct ccomp or xcomp child |
| Clause complement anywhere | At least one ccomp or xcomp token occurs anywhere |
| Passive verb root | Root has UPOS=VERB and a direct nsubj:pass, csubj:pass, or aux:pass child |
| Adverbial clause root | Root has a direct advcl child |
| Adverbial clause anywhere | At least one advcl token occurs anywhere |
| Coordination root | Root has a direct conj child |
| Coordination anywhere | At least one conj token occurs anywhere |

For active transitive roots, the first direct subject and object are ordered relative to the root and classified as SVO, VSO, VOS, or OTHER. This is a surface-order proxy, not a semantic-role judgment.

## Source and licensing

- English: UniversalDependencies/UD_English-PUD, commit a697bab43d4111073356de0df5802488bca3de7e, file en_pud-ud-test.conllu.
- Arabic: UniversalDependencies/UD_Arabic-PUD, commit c606299bc9eb8baa6c61c8dd3efc9a0fbf73aa87, file ar_pud-ud-test.conllu.
- Both source treebanks declare CC BY-SA 3.0. Campaigns must continue to include the source LICENSE.txt and ATTRIBUTION.md.
- PUD is news/Wikipedia text, not conversational user requests. All Arabic PUD sentences are translated and do not represent a native-MSA distribution.
- The privacy screen rejects email and URL patterns but is not a comprehensive personal-data detector; public proper names remain.

## Interpretation limits

UD POS and dependency labels are syntactic annotations. They are not independently adjudicated USG semantic frames, roles, relations, or construction-level semantic gold. A high frequency is a reason to consider a bounded candidate, not evidence that USG supports it. Any runtime expansion still requires SYS-09 independent construction-level gold, positive/negative/ambiguous/boundary cases, held-out evaluation, abstention checks, and explicit acceptance.

The analyzer reports the full pinned source population separately from the pilot's sampled campaign cases. Do not combine these frequency counts with randomized or controlled-diagnostic campaign outcome rates.

## Rollback

This branch adds a diagnostic module, its tests, documentation, and a workflow artifact step only. It does not change runtime semantics, lexical resources, gold labels, thresholds, or canonical contracts. Revert the branch commits or discard the branch to remove the proposal.
