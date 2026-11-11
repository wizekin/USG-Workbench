# Phase 6 Step 6.4 — CAMeL Tools MSA Morphology Evaluation v0.5

**Status:** optional external-tool experiment; not integrated into USG runtime.

## Why this experiment exists

The preceding ten-fold PUD experiment found that generic prefix/suffix
paradigm rules improved English lemma/POS candidate recall by 2.03 percentage
points, but Arabic by only 0.014 points. Arabic requires richer treatment of
clitics and non-concatenative morphology. This experiment evaluates a
purpose-built MSA morphological analyzer against the same pinned Arabic PUD
treebank.

## External dependency and licensing boundary

- Toolkit: CAMeL Tools 1.6.0; project code is MIT-licensed.
- Database: CALIMA MSA r13, distributed as the CAMeL Tools
  morphology-db-msa-r13 package under GPL-2.0.
- The toolkit and database are installed only in an ephemeral GitHub Actions
  runner. Neither is copied into this repository, added to the USG package, or
  made a required runtime dependency.
- Analyzer backoff is disabled (NONE) so the evaluation does not count
  generated unknown-word backoff guesses as lexicon analyses.
- The separate calima-msa-s31 database is not used because its post-install
  instructions require a separately licensed SAMA 3.1 copy.

References:
- https://github.com/CAMeL-Lab/camel_tools
- https://camel-tools.readthedocs.io/en/latest/api/morphology/analyzer.html
- https://camel-tools.readthedocs.io/en/latest/api/morphology/database.html
- https://camel-tools.readthedocs.io/en/latest/reference/packages.html
- https://camel-tools.readthedocs.io/en/latest/reference/db_install.html

## Evaluation

The adapter compares each CAMeL analysis' lemma (lex) and Universal
Dependencies POS (ud) candidates against the gold lemma and UPOS in Arabic PUD.
It reports all-token and Arabic-script-only coverage, lemma recall, UPOS recall,
lemma/POS candidate recall, ambiguity, and mean candidate count.

PUD is an external treebank, but this experiment does not claim that the
analyzer's training data is guaranteed disjoint from PUD. Candidate inclusion
is not disambiguation accuracy. The evaluation does not establish semantic
roles, word-sense selection, or USG construction support.

## Runtime and release guardrails

This experiment is deliberately isolated. It must not add CAMeL Tools to
runtime dependencies, bundle its GPL morphology database, or alter the
existing SQLite store. Any future adapter proposal must preserve this boundary
and explicitly document the effect of the database license on distributions.

No semantic acceptance credit or construction promotion is permitted.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_camel_msa.py' -v
python -m tools.phase6_external_pud_v0_5.camel_msa
```
