# USG Rule Execution Activation 1.0.0

This is a separately versioned execution overlay. It does **not** modify the
declarative rule registry or semantics contract. Those source documents remain
unchanged, with registry-level execution disabled and each rule marked
`SPECIFIED_NOT_EXECUTABLE`.

The overlay activates exactly two deterministic handlers:
- `benchmark-rule:modus-ponens@1.0.0`
- `benchmark-rule:and-elimination-left@1.0.0`

The executor accepts complete, schema-valid USG-SEM/1.0 documents and an
explicit task. It does not parse raw prose. The supported patterns require
resolved PROP-sorted expression nodes, exact ordered operands, exact context
identity, and exact attribution/commitment bindings.

Only original `SOURCE_ASSERTED` assertions can be premises. Inferred outputs
are held in a separate candidate ledger and are never added to the canonical
assertion collection or reused as premises. DISPUTED, UNKNOWN, ambiguous,
unresolved, unsupported, and invalid inputs are not silently coerced.

Every candidate has a deterministic derivation ID and records the input
snapshot hash, exact input references, rule/version, registry, semantics,
activation, and grounding versions. Candidate status is
`DERIVED_NOT_VERIFIED`; truth promotion is always false.

A task may specify `max_rule_applications` as an execution budget. If the
budget is exhausted, the result is `INCOMPLETE`, unprocessed work is listed,
and every input record remains represented. There is no semantic truncation
or arbitrary cap on expression size, operands, or meaning complexity.

This package does not assess evidence, verify claims, select conflict winners,
assume a closed world, perform converse inference, or infer rule closure.
No human-review gate is part of the execution contract.
