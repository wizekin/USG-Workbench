# Phase 3 Step 3.5 — Conditions and contradiction services

**Status:** IMPLEMENTED — awaiting exact-PR-head CI and merge.
**Profile:** `USG-DOCUMENT-ANALYSIS/1.0.0`.
**Storage:** consumes complete USG-SEM/1.0 snapshots; SQLite remains the authoritative persistence layer.

## Conditions and exceptions

The service composes the Step 3.4 scope-aware analyzer and creates a document-level map of:
- IF antecedent/consequent links;
- explicitly represented UNLESS consequent/exception links;
- NOT scopes, including nested negation;
- exact assertion bindings for context, commitment, attribution, and epistemic status;
- available source spans and assertion links.

A condition is reported as represented structure, not as a fact. An absent exception never asserts the UNLESS consequent. Unsupported conditional encodings remain explicit diagnostics.

## Contradiction inspection

The service reuses the frozen Phase 2 evidence assessor's exact direct-NOT complement policy. It reports conflicts only when expression complement, context reference and kind, commitment, and attributed referent match exactly. Context/attribution mismatches are not conflicts. It never chooses a winner or uses recency, frequency, or confidence tie-breaks.

Evidence alignment, declared semantic support, relation claims, source diversity/independence, and external verification are returned as separate axes; they are not collapsed into contradiction status.

## Tests

Tests cover IF and UNLESS linkage, nested NOT, same-scope direct NOT conflict, context and attribution boundaries, ineligible epistemic statuses, snapshot consistency, immutability, and evidence-axis separation.

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase3_conditions_contradictions.py" -v
```
