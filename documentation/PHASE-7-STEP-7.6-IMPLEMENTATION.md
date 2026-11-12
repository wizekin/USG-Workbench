# Phase 7 Step 7.6 — Typed Semantic Relations and Source Reconciliation

**Status:** implementation submitted for CI; acceptance remains pending until the exact pull-request head passes its required checks.  
**Registry:** `USG-KNOWLEDGE-RELATIONS/0.1.0`  
**Knowledge bundle compatibility:** additive to `USG-KNOWLEDGE/0.1.0`; `USG-SEM/1.0` is unchanged.

## Deliverables

- A versioned predicate registry with explicit domain and range record kinds.
- Deterministic validation of relation predicates, endpoint kinds, direction, and registry version.
- Evidence aggregation for exact directed claims.
- A provider-conflict ledger that preserves supporting, contradicting, and unassessed evidence.
- Distinct-provider counting; repeated observations from one provider are not independent corroboration.
- Explicit non-inference flags: no source voting, inverse closure, transitive closure, causal inference, or automatic promotion.

## Relation profile

The initial candidate registry declares `RELATED_TO`, `HAS_PROPERTY`, `HAS_PART`, `SUBCLASS_OF`, and `HAS_ROLE`. Each relation is directed and non-inferential. Domains and ranges constrain the record kinds that may occupy each endpoint. A predicate absent from the registry is rejected.

## Reconciliation behavior

Reconciliation groups only identical directed triples (subject, predicate, object). It aggregates the referenced evidence statuses and provider identities without choosing a winning provider. A claim is labelled `CONFLICT` when both supporting and contradicting providers exist, `SUPPORT_ONLY`, `CONTRADICTION_ONLY`, or `UNASSESSED` otherwise. These labels summarize evidence states; they are not truth judgments.

The implementation deliberately does not infer an inverse edge, transitive path, causal consequence, or equivalent claim. Provider counts are diagnostic only and do not constitute a majority vote.

## Acceptance tests

`python -m unittest discover -s tests -p 'test_phase7_knowledge_relations.py' -v`

The test suite covers registry invariants, unknown predicates, domain/range mismatches, registry-version mismatch, conflict retention, provider deduplication, deterministic replay, and forbidden closure/voting.

## Limitations

This first registry is a bounded candidate profile, not a universal ontology. Relation labels are not executable inference rules. The reconciliation report does not adjudicate semantic correctness, source independence beyond provider identifiers, legal rights, or truth. All relation state remains supplied by the input bundle; no record is promoted.
