# Phase 2 Step 2.7 — Evidence Support and Conflict Assessment

**Status:** COMPLETE — merged as PR #46. The integrated implementation and regression scope are recorded in the Phase 2 roadmap.

## Purpose

Step 2.7 adds a deterministic assessment layer without changing USG-SEM/1.0.
It keeps source-span alignment, declared semantic support, relation claims,
exact-scope conflicts, source diversity, source independence, corroboration,
and external verification as independent result axes.

## Implemented behavior

- **Source-span alignment:** verifies exact Unicode-code-point offsets and
  quote equality against the referenced source text. Missing sources remain
  unresolved; mismatched quotes remain mismatches; a mismatched source hash
  prevents an exact-alignment claim.
- **Semantic support:** preserves the canonical Evidence
  `semanticSupportStatus` as a declaration. A `RULE_SUPPORTED` or
  `CORROBORATED` label is not promoted to established support.
- **Relation claims:** preserves SUPPORTS/CONTRADICTS and other relation labels
  as claims. A relation type or declared verification token is not proof.
- **Conflict assessment:** detects only exact direct-NOT complements with
  matching context identity, context kind, commitment, and attributed referent.
  It reports CONFLICTING and never chooses a winner.
- **Source independence:** distinguishes multiple source records from proven
  independence. Distinct IDs or URIs alone do not establish independence;
  matching hashes/URIs are treated as shared or possibly shared lineage.
- **Corroboration:** remains NOT_ESTABLISHED unless independence is established
  by a future separately governed policy.
- **External verification:** task declarations remain DECLARED_UNVERIFIED
  unless a trusted verifier registry and procedure are actually bound and run.

## Explicit non-goals and invariants

This step does not perform natural-language entailment, infer support from
quote overlap, infer contradiction from relation labels, establish source
independence from record count, or execute external fact-checking. It does not
promote truth, select conflict winners, mutate canonical documents, truncate
semantic content, or require a human-review gate.

All outputs are a separate `USG-EVIDENCE-ASSESSMENT/1.0.0` result ledger. The
canonical evidence and relation records are preserved unchanged.

## Benchmark and acceptance

The additive benchmark contains complete canonical USG-SEM/1.0 documents for
exact/mismatched/Unicode/hash-mismatched/unresolved spans, declared support,
unverified contradiction relations, exact-scope conflicts, context and
attribution boundaries, source diversity and shared lineage, and external
verification declarations. Every fixture is schema-validated and regression
tested. Frozen Step 2.2 and Step 2.6 fixtures remain unchanged.
