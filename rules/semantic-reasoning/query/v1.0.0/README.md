# USG Structured Query and Explanation 1.0.0

Queries are explicit typed-reference requests, not natural-language prompts.
A query identifies one exact PROP expression, context identity and kind,
commitment, optional attributed referent, and an explicit allowlist of
inference rule IDs.

The interface:
1. validates the canonical USG-SEM/1.0 document and query;
2. grounds the exact goal expression, context, and attribution;
3. locates exact source assertions in that scope;
4. executes only the task's explicit rule allowlist through the Step 2.6
   deterministic executor;
5. matches derived candidates only when every source assertion premise has
   the exact requested scope/attribution binding;
6. assesses evidence and conflicts through the separate Step 2.7 assessor;
7. returns a deterministic structured explanation trace.

No natural-language generation or free-text inference is performed. An
unmatched goal is NOT_ESTABLISHED, never false by absence. Source assertions
remain SOURCE_ASSERTED_NOT_VERIFIED; derived candidates remain
DERIVED_NOT_VERIFIED. Disputed, unknown, ambiguous, unresolved, unsupported,
and incomplete outcomes remain distinct. Evidence, conflict, and relation
details are projections from the separate evidence-assessment ledger.

CLI:
`python -m tools.semantic_query_interface_v1_0_0.cli --document document.json --query query.json --output result.json`
