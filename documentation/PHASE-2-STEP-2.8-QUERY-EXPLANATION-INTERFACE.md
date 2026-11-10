# Phase 2 Step 2.8 — Query and Explanation Interface

**Status:** COMPLETE — merged as PR #48. The integrated implementation and regression scope are recorded in the Phase 2 roadmap.

## Contract

The query interface accepts explicit typed references only: a PROP expression,
context identity and kind, commitment, optional attributed referent, and an
explicit inference task with a rule allowlist. It does not accept free text,
search labels, or infer a goal from natural language.

## Processing order

1. Validate the complete USG-SEM/1.0 document and query contract.
2. Ground the exact expression, context, and attribution references.
3. Find exact source assertions in the requested scope.
4. Run the Step 2.6 executor using only the task's explicitly listed rules.
5. Match derived candidates only when every assertion premise has the exact
   requested context, commitment, and attribution binding.
6. Run Step 2.7 evidence and conflict assessment on the relevant scope.
7. Withhold any derived candidate whose source assertion premises participate
   in an exact-scope conflict; report the blocked derivation and conflict.
8. Return a deterministic structured explanation and all relevant diagnostics.

## Result semantics

The interface distinguishes SOURCE_ASSERTED_NOT_VERIFIED,
DERIVED_NOT_VERIFIED, DISPUTED, UNKNOWN, CONFLICTING, NOT_ESTABLISHED,
AMBIGUOUS, UNRESOLVED, UNSUPPORTED, and INCOMPLETE. An absent match is
NOT_ESTABLISHED under the open-world policy, never false by default.

Results include explicit assumptions, exact source assertions, scope
assertions, inference candidates, derivation paths, evidence assessments,
relation claims, conflicts, unresolved questions, unsupported portions, and a
deterministic explanation trace. Natural-language explanations are not
generated and are not authoritative.

The canonical document is never mutated. The interface cannot promote truth,
chain inferred premises, select conflict winners, or truncate semantic content.

## CLI

`python -m tools.semantic_query_interface_v1_0_0.cli --document document.json --query query.json --output result.json`

The query JSON must validate against
`rules/semantic-reasoning/query/v1.0.0/query.schema.json`.
