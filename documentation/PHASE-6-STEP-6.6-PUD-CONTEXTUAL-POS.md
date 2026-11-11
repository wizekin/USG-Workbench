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
