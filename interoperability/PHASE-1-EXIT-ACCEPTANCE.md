# USG Phase 1 — Exit acceptance and completion record

**Phase:** 1 — Normative semantic contract `USG-SEM/1.0`  
**Status:** COMPLETE when this acceptance suite and all required CI checks pass on the merged main branch.  
**Canonical contract and schema:** unchanged.

## Exit criteria

| Requirement | Acceptance evidence |
|---|---|
| One versioned canonical contract | `specifications/USG-SEM-1.0.md` and `specifications/usg-sem-1.0.schema.json` remain normative and unchanged |
| Predicate/frame mapping is explicit | Predicate-to-frame registry v1.0.0 and conformance tests |
| Operator/scope mapping is explicit | Operator/scope registry v1.0.0 and conformance tests |
| Workbench boundary is reversible | Steps 4A–4D, four-boundary semantic invariant suite, and reconstruction tests |
| Python native families have explicit models | Versioned native Source, Referent, Mention, Assertion, Evidence, Context, ExpressionRelation, UnresolvedItem, Derivation, and Definitions models |
| Every supported record family has a document adapter | Python adapter generations v0.5.0–v1.4.0 |
| One document can compose all family adapters | Composed adapter v1.5.0; only each adapter's owned collections are merged |
| Canonical-only content is preserved | Unknown, unsupported, dangling, and unmapped fields remain in the canonical envelope with diagnostics |
| Cross-family source evidence remains coherent | Final composed source-span and exact-quote checks use zero-based, end-exclusive Unicode code-point offsets |
| Baselines and compatibility remain intact | Registry workflow's immutable baseline verification; no mutation of USG-SEM/1.0, Workbench v0.5.4, Python v0.4.0, archives, or historical baselines |
| Reproducible CI and documentation | Dedicated per-step workflows, aggregate adapter regression, implementation indexes, and this exit record |

## Family coverage

The composed adapter reports independent coverage for Sources, Expressions, Referents, Mentions, Assertions, Evidence, Contexts, ExpressionRelations, UnresolvedItems, Derivations, and each Definitions subgroup (Concepts, Frames, Roles, Relations). Validation metadata, mapping metadata, and extensions remain canonical sidecars.

A `PARTIAL` family report is an explicit and valid outcome when a record cannot be represented exactly. It does not permit silent loss or coercion. Phase 1 establishes the contract and tested interchange boundaries; it does not claim that every natural-language construction is interpreted correctly or that all record families are fully supported by every native runtime.

## Explicit non-goals retained

Phase 1 does not establish open-domain semantic accuracy, truth evaluation, entailment, a generalized reasoner, autonomous ontology learning, distributed execution, multilingual coverage, or production readiness. Those require later phases and independent evaluation.

## Final verification procedure

1. Run the Phase 1 exit acceptance tests.
2. Run the complete composed document adapter and every versioned adapter regression.
3. Run predicate/frame and operator/scope registry conformance.
4. Run Workbench source/reconstruction and end-to-end semantic invariant tests.
5. Verify immutable implementation baselines.
6. Confirm every required check is successful on the exact PR head before merge.

Completion means all these checks pass on the merged commit; a numbered-step count alone is insufficient.
