# Phase 6 Step 6.4 — External PUD Morphology Generalization v0.4

**Status:** candidate research track; not a production lexical resource or runtime integration.

## Purpose

The existing Phase 5/6 lexical resources are versioned and provenance-bearing,
but their surface forms are mostly fixture-derived. The external PUD audits
showed that exact-form coverage does not transfer well. This experiment tests
whether bounded prefix/suffix paradigms can generate lemma candidates for
held-out forms without copying the held-out annotations into the rules.

## Method

- Use pinned English and Arabic PUD snapshots (CC BY-SA 3.0); verify the
  upstream Git blob hashes through the existing downloader.
- Split each language into ten stable sentence-ID-hash folds.
- For each fold, induce rules only from the other nine folds' FORM, LEMMA,
  UPOS, and FEATS annotations.
- Support prefix attachment, suffix attachment/replacement, and a constrained
  consonant-doubling pattern. Require at least two distinct observed
  lemma/form pairs for each complete rule.
- Require each generated lemma/POS candidate to exist in the training-fold
  lemma inventory; the analyzer does not invent unregistered lexical stems.
- Apply rules to held-out surface forms and report exact-form coverage, OOV,
  lemma/POS candidate recall, feature-bundle candidate recall, morphology
  rescue, and ambiguity.
- Do not persist PUD text, fold-derived lexicons, or rules as production data.

## Scope and limitations

This is a lexical morphology candidate generator, not a contextual POS tagger,
dependency parser, or semantic interpreter. Rule candidates are not truth.
Internal stem changes and non-concatenative Arabic morphology are not guessed.
UD UPOS/FEATS are external syntactic/morphological labels, not USG semantic
sense annotations.

The output receives no semantic acceptance credit and cannot enable a
construction. It is intended to identify which productive forms can be
handled safely and where additional morphology models/resources are needed.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_morphology.py' -v
python -m tools.phase6_external_pud_v0_4.morphology
```

## Observed ten-fold results (2026-11-11)

| Measure | English PUD | Arabic PUD |
|---|---:|---:|
| Annotated tokens evaluated | 21,179 | 20,747 |
| Exact-form coverage | 82.63% | 75.50% |
| OOV rate | 17.37% | 24.50% |
| Exact-form lemma/POS candidate recall | 80.86% | 73.63% |
| Combined exact + morphology lemma/POS recall | 82.89% | 73.65% |
| Gain over exact-form baseline | +2.03 percentage points | +0.014 percentage points |
| OOV forms rescued by morphology | 399 (10.85% of OOV) | 2 (0.04% of OOV) |
| Ambiguous lemma/POS candidate rate | 29.68% | 26.20% |

The prefix/suffix paradigm experiment gives a modest benefit for English but
essentially no benefit for Arabic. It does not solve the overall OOV problem.
It is not suitable as a general lexical analyzer, and it must not be promoted
to the runtime. The remaining English ambiguity also requires contextual
selection rather than accepting every generated candidate.

## Next dependency: evaluate a dedicated Arabic morphology engine

The next Arabic experiment should compare the rule candidate generator against
an established Arabic morphological analyzer rather than expanding ad hoc
prefix/suffix rules. CAMeL Tools is a candidate to evaluate: its toolkit code
is MIT-licensed, while the documented calima-msa-r13 and calima-egy-r13
morphology databases are GPL v2. The calima-msa-s31 database requires a
separately licensed SAMA 3.1 copy. These database terms are material: do not
vendor or bundle the databases, and keep any adapter optional until the
distribution and license boundary is explicitly established.

References:
- CAMeL Tools project and code license: https://github.com/CAMeL-Lab/camel_tools
- CAMeL Tools database names and database licenses:
  https://camel-tools.readthedocs.io/en/latest/api/morphology/database.html
- CAMeL Tools installable data packages and licenses:
  https://camel-tools.readthedocs.io/en/latest/reference/packages.html

A follow-up experiment should run the analyzer over the same pinned Arabic PUD
folds, compare lemma/POS candidate recall, feature coverage, OOV rescue, and
ambiguity, and record exact package/database versions. No runtime integration
or construction promotion follows automatically from that comparison.

The current PR's CI report is available from
[workflow run 42990029883](https://github.com/wizekin/USG-Workbench/actions/runs/42990029883).
