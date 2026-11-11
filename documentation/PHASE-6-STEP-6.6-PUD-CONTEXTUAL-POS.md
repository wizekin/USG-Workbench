# Phase 6 Step 6.6 — PUD Contextual POS Baseline v0.3

**Status:** diagnostic experiment only; not a USG runtime feature or semantic acceptance.

The prior cross-validated POS candidate audit found that exact-form lexical
coverage is incomplete and many tokens have multiple candidate tags. This
experiment compares a simple deterministic first-order HMM (Viterbi decoding)
against a most-frequent-tag-per-word baseline using the same ten stable
sentence-ID-hash folds over English and Arabic PUD.

## Method

- Train on nine folds and evaluate on the held-out fold, repeated ten times.
- Use exact surface forms, English case-folding, and add-alpha smoothing.
- Compare unigram lexical majority tagging with bigram POS transition decoding.
- Report overall, seen-word, OOV, content-word, and exact-sentence metrics.
- Download pinned PUD snapshots and verify their Git blob hashes; do not store
  source text or trained models in the repository.

## Interpretation boundary

This is a small POS-tagging diagnostic, not a semantic grammar. It does not
predict dependency attachments, semantic roles, or USG construction IDs.
A better POS score would justify investigating a replaceable lexical/morphology
candidate module, not integrating it automatically into the USG runtime.
Results are corpus-specific and cannot establish broad English/MSA coverage.

All USG constructions remain candidate-only. Step 6.6 remains unaccepted and
Step 6.7 remains blocked.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_external_pud_hmm.py' -v
python -m tools.phase6_external_pud_v0_3.hmm
```

## Observed ten-fold run (2026-11-11)

| Measure | English PUD | Arabic PUD |
|---|---:|---:|
| Unigram baseline token accuracy | 82.04% | 81.96% |
| HMM token accuracy | 82.55% | 79.59% |
| HMM accuracy on seen tokens | 91.74% | 92.88% |
| HMM accuracy on OOV tokens | 38.84% | 38.64% |
| Unigram content-token accuracy | 71.01% | 71.98% |
| HMM content-token accuracy | 70.46% | 68.43% |
| Unigram exact-sentence accuracy | 4.1% | 4.1% |
| HMM exact-sentence accuracy | 6.1% | 4.1% |

The HMM improved English overall token accuracy by only 0.51 percentage
points while slightly reducing English content-token accuracy. It reduced
Arabic overall accuracy by 2.37 points and Arabic content-token accuracy by
3.55 points. OOV accuracy remained below 39% in both languages.

**Decision:** do not integrate this HMM into USG. It does not provide a
consistent improvement over the simple lexical-majority baseline, especially
on content words and Arabic. Keep it as a reproducible negative result.
A future morphology/context candidate would need a different design and
must beat this baseline on held-out data before integration is considered.

Report artifact:
[workflow run 42988494714](https://github.com/wizekin/USG-Workbench/actions/runs/42988494714).
