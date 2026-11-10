# Phase 1 Step 5G — Versioned native Referent identity model

**Model version:** 0.6.0 (standalone identity extension)  
**Previous kernel:** Python kernel v0.5.0 (unchanged)  
**Contract:** USG-SEM/1.0 (unchanged)

## Objective

Introduce an independently versioned native data model for Referent identity semantics identified as missing in Step 5F. This is an additive model extension, not an in-place edit to the frozen v0.5.0 package and not yet a document adapter.

## Delivered model

Package: `implementations/python-kernel/v0.6.0/usg_identity_v06/`

- `IdentityStatus`: PROVISIONAL, RESOLVED, AMBIGUOUS, UNRESOLVED, DISPUTED, UNKNOWN.
- `IdentityScope`: DOCUMENT, WORKSPACE, CORPUS, GLOBAL.
- `ReferentIdentity`: independent optional status and scope, ordered explicit equivalence refs, and basis.
- `TypedReference`: opaque external identifier paired with an explicit target space; identifier text is never parsed for meaning.
- `IntroductionContext`: introduction kind plus a typed INSTANCE or NODE context reference where required.
- `NativeReferentV06`: discourse referent with separate label, aliases, concept refs, identity metadata, introduction context, source reference, and source span.
- `same_referent()`: compares only opaque referent IDs; labels, aliases, concepts, and equivalence links never merge referents.

## Semantic safeguards

1. Resolution status and identity scope are orthogonal and independently optional. An omitted field is not silently changed to UNKNOWN or any scope.
2. Explicit equivalence links remain ordered referent-to-referent links. The model does not infer symmetry, transitivity, or merge records.
3. Concept references and equivalence references have disjoint typed target spaces.
4. Labels and aliases are descriptive data, not identity keys.
5. Introduction context is independent of identity scope. WORLD has no context ref; other supported introduction kinds require an explicitly typed INSTANCE or NODE reference.
6. Source spans use non-negative Unicode code-point offsets. This model validates pair shape/order; the document adapter must additionally validate against the referenced Source text.
7. Unknown or unsupported enum values must remain canonical-only in a future adapter with exact diagnostics; they must not be coerced to a nearest enum.
8. Referent and Mention remain separate record families. No mention or antecedent semantics are inferred here.

## Scope boundary

Step 5G adds the model and unit tests only. It does not:
- change Python kernel v0.5.0 or its adapter;
- modify USG-SEM/1.0 or Workbench v0.5.4;
- claim native document-level Referent mapping or lossless round-trip;
- change archives, immutable baselines, or Node.js workflow/action versions.

## Tests

Run from the package directory:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

The conformance suite covers all status/scope values, same-label distinct referents, alias independence, concept/equivalence target separation, explicit links without merging, introduction-context typing, absent versus UNKNOWN, and source-span ordering.
