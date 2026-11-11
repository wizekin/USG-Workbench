# Phase 6 Step 6.6 — UD Dependency-Driven Nominal Candidate Adapter v0.1

**Status:** candidate-only structural adapter; not Step 6.6 acceptance.

## Why this exists

The previous external PUD audit found 393 eligible nominal/modifier structures,
but the closed USG candidate lexicon matched none. The root problem is that
the current interpreter requires exact lexical entries before it can recognize
a construction. This adapter tests a different boundary: use an already
available dependency graph to identify syntactic relations, then translate
only the explicitly supported relations into USG candidate structures.

## Supported mappings

- UD amod → attribute modifier (head noun + adjective attribute).
- UD compound → noun compound (head + compound modifier).
- UD nmod:poss → possession (possessed + possessor).
- UD nmod with case=of → genitive relation with semantics explicitly
  unspecified.
- UD nmod with another case marker → prepositional nominal modifier.
- Unmarked UD nmod → ambiguous alternatives; it is never forced to possession.
- UD advmod with a whitelisted temporal adverb → temporal modifier.

Every output is CANDIDATE or AMBIGUOUS. The adapter does not assert a specific
real-world relation where UD syntax alone cannot establish it.

## Source fidelity

The adapter aligns token forms back to the original PUD sentence text using
language-specific normalization only for matching. Output spans are code-point
offsets into the untouched original sentence. If a required token cannot be
aligned, the candidate is not emitted and the failure is counted.

## Evaluation boundary

The experiment consumes gold UD dependency trees from the pinned English and
Arabic PUD snapshots. It measures graph-to-USG transformation and span
alignment, not end-to-end parsing. UD dependency labels are independent
syntactic annotations, but they are not human-adjudicated USG semantic-role
labels. The result therefore does not satisfy the independent semantic
acceptance gate.

The new adapter does not replace the closed lexical interpreter. It is a
separate candidate provider whose output can later be combined with parser
predictions after each language's parser has passed its own held-out tests.

## Run

```bash
python -m unittest discover -s tests -p 'test_phase6_ud_nominal_adapter.py' -v
python -m tools.phase6_ud_nominal_candidate_v0_1.adapter
```

## Observed gold-UD extraction results (2026-11-11)

The adapter processed 1,000 English PUD sentences (21,180 tokens) and 1,000
Arabic PUD sentences (20,747 tokens), using the pinned treebank snapshots.

| Measure | English PUD | Arabic PUD |
|---|---:|---:|
| Candidate outputs | 3,295 | 4,714 |
| Sentences with at least one clear candidate | 903 | 155 |
| Sentences containing an ambiguous relation | 8 | 807 |
| Sentences with no supported candidate | 89 | 38 |
| Token span alignment success | 100.00% | 99.92% |

Construction outputs (ambiguous alternatives are counted separately):

| Construction | English | Arabic |
|---|---:|---:|
| Attribute modifier | 1,240 | 1,610 |
| Genitive relation candidate | 487 | 1,971 |
| Compound modifier | 701 | 6 |
| Prepositional nominal modifier | 467 | 1,124 |
| Possession | 361 | 0 |
| Temporal adverbial | 39 | 3 |
| Unspecified nominal-modifier alternative | 8 | 1,971 |

The Arabic treebank uses many unmarked `nmod` relations instead of the more
specific `nmod:poss` label. The adapter therefore preserves two alternatives
(genitive relation vs. unspecified nominal modifier) rather than declaring
ownership. The 1,971 entries in each of those two rows are alternatives for
the same ambiguous relations, not 3,942 distinct source relations.

**Decision:** the dependency-driven adapter successfully creates source-
grounded candidate structures without requiring the old closed lexical
inventory. It is a useful front-end boundary for USG, but this run uses gold
UD syntax and does not measure a parser's errors or semantic correctness.
The Arabic ambiguity is intentionally retained. The 16 unaligned Arabic
tokens are counted and no candidate requiring those spans is emitted.

This is not Step 6.6 acceptance: the benchmark supplies syntactic relations,
not independently annotated USG semantic-role decisions. All outputs remain
candidate-only.

Report artifact:
[workflow run 42994916166](https://github.com/wizekin/USG-Workbench/actions/runs/42994916166).
