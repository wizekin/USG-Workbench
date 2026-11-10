Current release additions and operational boundaries: [IMPLEMENTATION-v04.md](IMPLEMENTATION-v04.md).

# Unattended implementation design

The current executable entry point is `usg.runtime.USG`, exposed by `python -m
usg` and `run-usg.ps1`. `IMPLEMENTATION.md` maps all twelve specification parts to
code and states the coverage boundaries. The initial partial project's design
notes are preserved in `docs/INITIAL-DESIGN.md` for history.

## Commit path

1. Enforce source limits, keep exact Unicode and immutable code-point offsets,
   register the source, segment units and pin the active rules snapshot.
2. Compile each unit using explicit lexical and construction rules. Unsupported
   text produces an ERROR candidate with UNRESOLVED outcome, not a partial fact.
3. Validate independently against the frame library, ontology, evidence spans,
   registered rules, operator cues, scope, types and derivation certificate.
4. In one transaction, retain the candidate/report/evidence, allocate persistent
   referents, map workspace handles, store the expression and source assertion,
   build retrieval indexes, and append the audit/history/ingest checkpoint.
5. Ambiguous or uncertain representations retain that status. Nothing in this
   path marks a claim VERIFIED. Retrieval returns the full expression, including
   negation, attitudes and other scopes, rather than presenting nested events as
   unqualified facts.

Retries use source, pipeline/rule snapshot and unit offsets as idempotency keys.
New active rules change that key, enabling reprocessing without rewriting prior
records. Universal variables are not persisted as particular individuals.
Non-world introductions carry their own context. Discourse anaphora is accepted
only when a unique compatible prior referent exists; ambiguous matches abstain.

## Governance without people

The action policy separates automatic, gated, shadow-only and forbidden actions.
The automated panel counts distinct verifier classes and applies hard vetoes.
Learned proposals cannot approve themselves. New fundamental frames, concept
restructuring and unsupported semantic guesses remain inactive. Runtime learning
cannot edit Python, foundational rules, the validator or the seed ontology.

The rule DSL currently supports literal verb aliases. A proposal must exercise
its own trigger in positive tests and include negatives/contrasts. Model-written
examples alone do not establish semantic equivalence: the alignment must also
exist in the package's vetted lexical resource. Validation replay, a regression
corpus, constructed test gold, metamorphic substitution and contrasts must pass
before a CANARY bundle exists. Actual ingestion provides canary observations.
A minimum sample count and Wilson bound gate activation; any subsequent detected
regression rolls back the rule and dependent bundles automatically. Vetoed
candidates stay rejected. Candidate TTLs and queue capacities bound accumulation.

Representation assurance and world-truth evaluation are separate. Independent
origins are grouped conservatively by origin and near-copy checks. Source
probation may raise QUARANTINE to STANDARD after enough clean distinct units;
it cannot grant TRUSTED. A quorum of representation checks is never a substitute
for an external evidence policy.

## Resources and recovery

SQLite uses STRICT tables, foreign keys, WAL, immediate writer transactions and
FULL synchronization for registry/promotion commits. Table ownership is checked
at the write boundary. Evidence, expressions, source text and audit history are
immutable or append-only. A code seal protects all enforcement modules; a
separate content hash protects foundation rows. `verify` checks both and the
hash-chained audit history, then rechecks stored types, evidence and spans.
These are tamper-evidence and discipline guards, not an OS-level security
boundary against arbitrary privileged local code.

Jobs are durable, bounded, idempotent and leased with unique fencing tokens.
Expired leases can be reclaimed; a stale worker cannot acknowledge a newer
worker's job. Repeated failures go to a dead-letter state automatically. Shared
workspaces use optimistic version checks and bounded persistent references.
Graph matching, activation, queries, model output and binary decoding have
explicit caps. Optional components can be disabled independently.

Models are shared HTTP services. The local gateway only accepts loopback hosts,
closed choices and bounded output; it cannot write a store. The remote gateway
has no document-text parameter. It accepts only issue-code counts and exactly
two general task types, with HTTPS, no redirects/proxies, pre-reserved persistent
quotas, digest deduplication and a circuit breaker. Failed calls consume quota.
API keys are never persisted. No request is needed for the default workflow.

## Storage, inference and exchange

The query interface distinguishes source and trusted views. The reasoner stops
at negation, alternatives, future tense, quantifiers, modalities, hypotheticals
and attitude content. It performs bounded subclass, declared inverse/symmetric
and logical transitive derivations, returning premise IDs, INFERRED status and a
support cap. It never infers truth from missing data or activation scores.
Caches carry dependency keys and remain derived.

USBF profile `USBF-JSON-0.1` uses canonical JSON records inside independent zlib
blocks, with version pins, checksums, a footer directory and bounded decoding.
Varints are canonical and reject overflow/overlong forms. Length/count/depth
limits precede decompression/allocation. Reversible exports retain exact source
text and derivations; semantic exports may omit them. Imported archives cannot
supply authoritative status, rules or mappings: reversible source records are
re-interpreted in quarantine, while semantic-only files remain exchange
artifacts without invented source support. The benchmark compares bytes against
plain and compressed JSON without claiming a compression advantage.
