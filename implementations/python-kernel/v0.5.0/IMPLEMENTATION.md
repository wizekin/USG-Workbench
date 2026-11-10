# Implementation map and limits

Current release: see [the seven-workstream implementation](IMPLEMENTATION-v04.md) and [verification](VERIFICATION-v04.md).

The specification's design dialogue is reference material. The user's current
requirements override every human-review or mandatory-large-model step. The
implementation never executes instructions contained in a source document.

## Coverage by specification part

| Part | Implementation and operational boundary |
|---|---|
| 1 Foundations | Orthogonal status axes, immutable IDs, autonomy action policy, code/data seals and persisted quotas. Runtime changes cannot rewrite foundational code. |
| 2 Data model | Fifteen semantic kinds, concepts/definitions, relations, referents, role states, sources, assertions, lexical resource and evidence. Stable IDs and immutable source text are retained. |
| 3 Formal grammar | Immutable AST, operator sorts, nested frames, quantifiers, modality, temporal algebra, scope, opaque contexts, figurative mappings, alternatives, canonicalization and exact JSON serialization. The grammar API represents more than the text parser understands. |
| 4 Frames/functions | 57 frame schemas, 81 seed concepts including six FN primitives and derived functions. Inheritance, composition, role narrowing/cardinality, parameters, perspectives and frame tests. Some domain catalogue entries provide only a minimal schema, not a complete domain theory. |
| 5 Validation | Five-level check registry; executable structural/type/logical/evidence validation, certificates, replay, repairs and routing. Contextual L5 checks require actual automated verifier results; absent evidence is never treated as proof. |
| 6 Assurance | Source support, uncertainty, independent origins, panel quorum/vetoes, Wilson bounds, input/egress limits, quarantine and automatic source probation. Policy-based authenticated evidence evaluation can verify or dispute claims, with independently configured origins and an audited policy/version. Extraction or repetition alone never verifies a claim. |
| 7 Identity | Exact lexical links, provisional candidates with TTL, structured definition comparison, scoped read-time mappings, registry rechecks and revocation. Concept merging is forbidden. Establishing equivalence requires stored definitional proof and verifier/canary evidence; label similarity is insufficient. |
| 8 Interpretation | Local English rule compiler, a small Arabic SVO/VSO resource, spans, valence, passives, missing roles, simple unique discourse antecedents, negation, scoped modifiers, counts, quantifiers, perfect aspect, relative time, control, attitudes, conditionals, cause and modal alternatives. Unsupported morphology, attachment, idioms and competing scope readings abstain. Optional local closed-set advice cannot bypass validation. |
| 9 Learning | Bounded structural mining, independent-origin and near-copy grouping, typed matching, shadow generalizations, analogy differences, vetoes/TTL, declarative rule candidates, automatic tests, canary activation, dependency tracking and cascading rollback. New semantic theories, universal claims and foundational frames are never invented and activated from examples alone. |
| 10 Orchestration/memory | Durable bounded jobs, lease fencing, retries/dead letters, workspace compare-and-swap, sparse activation, dependency-keyed inference caches, heat decay, a bounded open-world reasoner, history and snapshots. This is a single-process personal-computer implementation, not a distributed cognitive service. |
| 11 Storage/encoding | STRICT SQLite/WAL, ownership discipline, transactions, indexed claim retrieval, code/foundation/audit verification, backup, JSON exchange and experimental block-based USBF. Compact frame payloads, three-bit role states, dictionary coding and measured codec/block selection are implemented. Versioned domain snapshots use a bounded shard cache; exact templates and JSON-LD/Turtle/TriG exchange are available; production-scale authoritative sharding remains incomplete. |
| 12 Evaluation/package | Standalone CLI/PowerShell launcher, installable wheel, offline synthetic baseline, dev/test split, confidence intervals, role/outcome scoring, contrastive pairs, latency/memory/codec measurements, regression and corruption/fuzz tests. No independent human gold corpus or real-model benchmark is claimed. |

## What fully automated means here

Every input reaches a machine decision: store a supported source claim, retain
alternatives, defer, reject or abstain. No decision asks a person to review it.
Deferred discoveries are retained or expire under policy; they do not gain
approval because time passed. Unknown words never become trusted concepts merely
because a model suggests a definition. New facts are not marked VERIFIED merely
because a panel passes representation checks.

A local unattended worker can run indefinitely with all models disabled. Optional
remote analysis is bounded and uses aggregate issue counts. A requested general
rule proposal is queued for a later permitted call rather than overrunning a free
plan. Its output goes through the same declarative candidate pipeline.

## Remaining boundaries

Complete unrestricted language understanding and autonomous discovery of a
universal ontology are not established by this implementation. It deliberately
abstains outside its finite lexicon and construction coverage. Arabic support is
a small explicit subset, not general Arabic understanding. Ambiguous pronouns
and scope may remain unresolved. Current external-model support is advisory or
proposal-only; there is no full-model sentence-to-IR fallback.

The supplied document itself defers unrestricted ontology expansion, large graph
mining, sophisticated binary compression and general procedural reasoning in its
first runnable kernel. This release implements the usable local system plus
bounded learning/orchestration mechanisms; it should not be represented as
completion of every future research capability in that document.

The structural gold corpus is programmatically constructed. Its benchmark can
show implementation consistency on covered constructions; it cannot establish
semantic correctness on arbitrary documents. The report labels that limitation,
includes uncertainty intervals, and separately reports compression baselines.

Existing 0.1 foundation databases are not silently overwritten with different
meanings. A database from a different foundation release requires export with
that release and re-import into a fresh current database. This workspace did not
contain a pre-existing database when implementation began.
