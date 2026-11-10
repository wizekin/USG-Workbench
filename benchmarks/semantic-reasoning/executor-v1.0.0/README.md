# Semantic Inference Executor Benchmark 1.0.0

This benchmark extension is separate from the frozen compact
`benchmarks/semantic-reasoning/v1.0.0` corpus. Each fixture is a complete
USG-SEM/1.0 document plus an explicit task; compact snapshots are never
coerced into canonical executor inputs.

The executor test suite constructs and validates the canonical documents
against `specifications/usg-sem-1.0.schema.json`, then evaluates positive
Modus Ponens and left-conjunction elimination cases plus converse rejection,
context/attribution mismatch, disputed and unknown premises, ambiguous and
unresolved expressions, disabled rules, and resource interruption.

Expected outputs distinguish candidates from assertions and require
DERIVED_NOT_VERIFIED, complete deterministic provenance, no inferred-premise
chaining, no truth promotion, and preservation of all input records.
