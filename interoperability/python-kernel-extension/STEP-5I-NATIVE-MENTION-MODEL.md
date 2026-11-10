# Phase 1 Step 5I — Native Mention model v0.7.0

**Canonical contract:** USG-SEM/1.0 (unchanged)  
**Native model:** `usg_discourse_v07` 0.7.0  
**Preceding identity model:** `usg_identity_v06` 0.6.0 (unchanged)

## Purpose

Define an additive, versioned native model for Mention occurrences. A Mention is not a Referent: a Mention ID identifies one textual occurrence, while a Referent ID identifies the discourse entity. Multiple mentions may link to one referent; equal surface strings do not establish shared identity.

## Model

The package is located at `implementations/python-kernel/v0.7.0/usg_discourse_v07/`.

- `NativeMentionV07`: opaque occurrence ID, exact surface text, resolution status, optional mention type, typed optional referent and antecedent links, and optional source grounding.
- `MentionResolutionStatus`: LINKED, RESOLVED, UNRESOLVED, AMBIGUOUS, UNKNOWN.
- `TypedReference`: opaque ID plus explicit MENTION, REFERENT, or SOURCE target space.
- Source spans are zero-based, end-exclusive Unicode code-point pairs and require an explicit SOURCE reference.
- `same_mention()` compares only opaque Mention IDs.

## Non-negotiable safeguards

- Mention identity is independent of surface text, mention type, and Referent identity.
- A referent link, antecedent-mention link, and antecedent-referent link use distinct typed spaces.
- No antecedent, coreference, or referent assignment is inferred.
- Resolution status remains independent from link presence; the model does not invent status/link implications absent from the canonical contract.
- UNRESOLVED, AMBIGUOUS, and UNKNOWN remain distinct.
- Unknown native extension fields and exact document round-trip are outside this model-only step and remain a later adapter responsibility.
- No changes to USG-SEM/1.0, v0.6.0, v0.5.0, Workbench v0.5.4, archives, immutable baselines, or existing Node.js action versions.

## Conformance

The tests cover occurrence identity versus surface equality, multiple mentions sharing a referent, typed antecedent links, unresolved and ambiguous cases, optional links, source spans, and rejection of incorrect reference spaces.

Run:

```bash
PYTHONPATH=implementations/python-kernel/v0.7.0 python -m unittest discover -s implementations/python-kernel/v0.7.0/tests -v
```

## Next integration boundary

A subsequent document-adapter step may project exact Mention fields from USG-SEM/1.0 into this model. It must retain unsupported fields and all canonical records, validate source spans against exact source text, preserve dangling references canonically with explicit partial status, and never infer antecedents or merge Referents.
