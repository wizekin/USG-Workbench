# Lexical Foundation Baseline — Pre-v0.4.0 Wikipedia Runs

This is a historical, manually transcribed baseline from the two saved Phase 5 Kernel Lab experiments. It records the state before the v0.4.0 composite lexical resource was introduced.

The original JSON outputs are retained in the user's Library as:
- `wikipedia chemistry.txt` — full article input.
- `wikipedia chemistry 2.txt` — reduced article input intended to contain prose only.

The article text and full stage artifacts are not copied into this repository. Therefore this document is a comparison reference, not a fully reproducible benchmark fixture. A future baseline importer should preserve exact source hashes and pipeline/resource versions from the original saved envelopes before claiming byte-for-byte reproducibility.

## Historical results

| Metric | Full article | Reduced article |
|---|---:|---:|
| Characters | 66,654 | 49,229 |
| Total tokens | 13,085 | 9,020 |
| Word tokens | 9,484 | 7,435 |
| Resolved word tokens | 89 | 82 |
| Unresolved word tokens | 9,395 | 7,353 |
| Lexical coverage | 0.94% | 1.10% |
| Sentences | 770 | 255 |
| Clauses | 840 | 277 |

Coverage is resolved word tokens divided by word tokens. It is rounded to two decimal places.

## Interpretation

- Removing headings, captions, references, and other non-prose material reduced the input size, but did not materially repair lexical coverage.
- Both runs recognized approximately the same very small set of lemmas.
- The reduced input still contained some heading, caption, and list remnants when inspected.
- Segmentation remained operational, while syntax and semantic composition produced no successful clause compositions.
- The historical SHA-256 discrepancy between the raw manifest file and the stage's canonical resource digest was later understood as a difference in digest domains, not by itself proof of file corruption.

## Comparison policy

Future re-runs should compare:
1. exact source text SHA-256;
2. exact pipeline and resource manifest versions;
3. raw resource-file SHA-256 values;
4. canonical composite-resource digest and its declared digest kind;
5. word-token coverage, lemma/POS accuracy, morphology accuracy, ambiguity, and unknown-word abstention;
6. downstream syntax and semantic composition separately.

Do not compare only the total number of resolved words. A smaller input can have fewer resolved tokens while showing a slightly higher coverage percentage, and a high lexical coverage score can still hide incorrect analyses.
