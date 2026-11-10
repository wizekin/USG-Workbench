# USG 0.3 implementation increment

New executable mechanisms:

- Version-pinned compact frame payloads, local dictionaries, signed/unsigned
  canonical integers, typed values and three-bit role states. Repeated event
  descriptions are not identity-merged. JSON containers remain readable.
- Measured codec/block optimizer, available through `export --codec auto`.
- Evidence-policy evaluator with authenticated independent-origin attestations,
  recency and scope gates, automated verifier panel, policy/version audit trails,
  VERIFIED promotion and DISPUTED transitions. Source documents cannot install
  evidence authorities. Worker evaluation is optional installation configuration.
- Completed-view frame final-state and essential-effect inference, respecting
  negation, intention and other opaque contexts; typical effects remain excluded.
- Versioned physical domain snapshots, stable global IDs, content verification,
  atomic catalogue publication, pinned older versions and bounded open-shard cache.
- CLI integration: `evaluate`, `partition`, compact/automatic export selection.

The explicit normative statements are inventoried in `conformance-inventory.json`.
Their status is UNASSESSED until a specific implementation and test are traced to
that statement. This inventory deliberately does not claim full conformance.

This increment does not complete every requirement across all twelve parts.
Remaining work includes broader language analysis and lexical coverage, richer
contextual validation, complete domain definitions, concept/grammar learning
beyond vetted aliases, advanced pattern/generalization tests and constraints,
complete kernel inference/function inheritance, authoritative domain sharding,
template compression, interoperability and broader independent evaluation.
The existing conservative autonomy restrictions continue to apply.
