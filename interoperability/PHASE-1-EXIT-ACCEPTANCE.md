# USG Phase 1 — Exit acceptance and completion record

**Phase:** 1 — Normative semantic contract `USG-SEM/1.0`  
**Status:** COMPLETE. Step 5Z was merged as PR #38 (merge commit `482e183e941f018f858c9c4701e7948229d00d2d`) after the full exit CI gate passed on both the PR head and merged main commit.  
**Canonical contract and schema:** unchanged.

## Exit criteria

| Requirement | Acceptance evidence |
|---|---|
| One versioned canonical contract | `specifications/USG-SEM-1.0.md` and `specifications/usg-sem-1.0.schema.json` remain normative and unchanged |
| Predicate/frame mapping is explicit | Predicate-to-frame registry v1.0.0 and conformance tests |
| Operator/scope mapping is explicit | Operator/scope registry v1.0.0 and conformance tests |
| Workbench boundary is reversible | Steps 4A–4D, four-boundary semantic invariant suite, and reconstruction tests |
| Python native families have explicit models | Versioned native Source, Referent, Mention, Assertion, Evidence, Context, ExpressionRelation, UnresolvedItem v1.2.1, Derivation, and Definitions models |
| Every supported record family has a document adapter | Python adapter generations v0.5.0–v1.4.0, including typed UnresolvedItem v1.2.1 |
| One document can compose all family adapters | Composed adapter v1.5.1; each adapter merges only its owned collections |
| Canonical-only content is preserved | Unknown, unsupported, dangling, and unmapped fields remain in the canonical envelope with diagnostics |
| Cross-family source evidence remains coherent | Composed source-span and exact-quote checks use zero-based, end-exclusive Unicode code-point offsets |
| Baselines and compatibility remain intact | Immutable baseline verification; no mutation of USG-SEM/1.0, Workbench v0.5.4, Python v0.4.0, or frozen archives |
| Reproducible CI and documentation | Dedicated per-step workflows, versioned adapter regressions, registry tests, Workbench boundary tests, and this exit record |

## Family coverage

The composed adapter reports independent coverage for Sources, Expressions, Referents, Mentions, Assertions, Evidence, Contexts, ExpressionRelations, UnresolvedItems, Derivations, and each Definitions subgroup (Concepts, Frames, Roles, Relations). Validation metadata, mapping metadata, and extensions remain canonical sidecars.

A `PARTIAL` family report is an explicit and valid outcome when a record cannot be represented exactly. It does not permit silent loss or coercion. Phase 1 establishes the contract and tested interchange boundaries; it does not claim that every natural-language construction is interpreted correctly or that all record families are fully supported by every native runtime.

## Explicit non-goals retained

Phase 1 does not establish open-domain semantic accuracy, truth evaluation, entailment, a generalized reasoner, autonomous ontology learning, distributed execution, multilingual coverage, or production readiness. Those require later phases and independent evaluation.

## Final verification procedure

1. Run the Phase 1 exit acceptance tests against the composed adapter v1.5.1.
2. Run every versioned Python document-adapter regression, including the corrected UnresolvedItem v1.2.1 adapter.
3. Run predicate/frame and operator/scope registry conformance.
4. Run canonical adapter, Workbench source/reconstruction, and end-to-end semantic invariant tests.
5. Verify immutable implementation baselines.
6. Confirm every required check is successful on the exact PR head before merge. This was satisfied for PR #38; the post-merge Phase 1 Exit Acceptance workflow also completed successfully.

Completion means all these checks pass on the merged commit; a numbered-step count alone is insufficient.
