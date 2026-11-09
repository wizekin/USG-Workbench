# USG implementation: design decisions for an unattended system

This implements the 12-part specification with two hard constraints:

1. **No human review or intervention at runtime.**
2. **Big (remote) models are used only to set general rules or analyse general issues**, under tiny
   free-plan quotas.

## 1. Where the specification used a person, and what replaces it

| Spec element (human role) | Replacement in this implementation |
|---|---|
| Human reviewer for HIGH / VERY_HIGH candidates (Part 6 §6.11) | **Automated Verification Panel (AVP)**: a quorum of *distinct verifier classes* (deterministic replay, independent extraction method, metamorphic variants, counterexample search, regression suite, synthetic held-out gold, optional local-model second opinion, statistical audit). Any hard-failing verifier **vetoes**. Minimum panel size is a pinned constant (>= 3). |
| "VERY_HIGH: never automatic" (Part 6 §6.10.2) | Each such action gets one of: `GATED` (only where deterministic proof exists, e.g. concept equivalence at grade ESTABLISHED, applied at read time so it is exactly reversible), `SHADOW_ONLY` (recorded, analysed, **never activated**: new fundamental frames, concept generalizations) or `FORBIDDEN` (universal claims, physical merges, non-ESTABLISHED equivalences). |
| Out-of-band human release of Level-1 rules, validator, FN primitives (SG-FND-005) | **Code seal**: SHA-256 of sealed modules recorded at install; verified at start-up and periodically. A mismatch means SAFE MODE (no promotions). Changing sealed code is a package release + explicit `reseal`, never a runtime action. |
| Human audit sampling to calibrate risk (Part 6 §6.10.3) | **Audit oracle**: automated re-derivation by an independent method; "error" = disagreement that a deterministic oracle resolves (replay mismatch, unsupported span, metamorphic break). Wilson upper bounds over these proxy errors set risk classes. Until calibrated, constants stay conservative. |
| Human veto of mined patterns (`REJECTED_PATTERN`, Part 6 §6.12.3) | **Automatic veto** from a verified counterexample or an audit-oracle failure; stored with the structural signature so the pattern is not re-proposed without materially stronger evidence. |
| Human decision on provisional concepts | Deterministic resolution only (link / specialise / define when the grade is met); otherwise the provisional concept **expires** (TTL) and is archived. |
| Human gold-set annotation (Part 12 §12.6.3) | **Programmatic gold by construction**: a grammar-driven sentence generator whose expected IR is known because it built the sentence; plus invariants, metamorphic pairs and contrastive pairs. See limits below. |
| Human trust decisions on sources | `QUARANTINE -> STANDARD` by automatic probation (N clean units); `-> TRUSTED` is **forbidden** (the trusted list is install-time configuration); lowering trust is automatic. |
| Calibrating `[Provisional]` constants | `Config.calibrate`: automatic, only inside declared bounds, recorded; safety-relevant constants are **pinned** and never calibrated. |

**Direction of the change:** removing the human makes the system *less* willing to change itself, never more.

## 2. Big-model policy

* **Allowed tasks (exactly two):** `GENERAL_RULE_PROPOSAL`, `GENERAL_ISSUE_ANALYSIS`.
* **Input:** aggregated *issue digests* (counts, rule IDs, error codes, structural signatures, PUBLIC/synthetic
  examples) — never a per-sentence stream and never non-PUBLIC text (SG-SEC-008).
* **Output:** constrained, declarative proposals (a rule DSL with mandatory positive / negative / contrastive tests)
  or `ISSUE_FINDING`s. Model output is **never executed** and never edits a store.
  * A rule proposal becomes a `CANDIDATE` and is activated only if the AVP quorum passes, a canary
    period shows no regression, and it can be rolled back automatically.
  * An issue finding can only **raise** scrutiny (raise a risk floor, prioritise reprocessing, request a rule
    proposal, raise audit rate). Effects that would relax a check are rejected by construction.
* **Budget (persisted in SQLite, enforced before any request is sent):** disabled by default; hard caps on
  calls/hour, calls/day, tokens/day, request size, minimum interval; exponential back-off circuit breaker on
  failures; failed calls still count; the same digest is never sent twice; stale reservations are reaped.
  Caps are *pinned* — the system cannot raise its own quota.
* **Offline behaviour:** with the big model disabled, exhausted or failing, everything still works with the
  deterministic and local-model paths. Issues simply accumulate until a call is allowed.

## 3. Honest limits of a fully unattended system

* Semantic *correctness* on open text cannot be proven without a human reference. The system measures
  consistency, rule compliance, unsupported-content rates and metamorphic stability, and it **abstains**
  (AMBIGUOUS / UNRESOLVED) rather than guess. Benchmarks built by construction measure the covered phenomena,
  not the whole of language.
* Frozen safety code cannot repair itself. A bug in sealed code needs a new package release.
* Conservative autonomy means some knowledge growth is deliberately blocked (SHADOW_ONLY / FORBIDDEN).
  It is recorded and counted so the operator can see what the system declined to do.
* Two models agreeing is not proof; panels therefore require *independence classes*, not just votes.

## 4. Part 1 module map (this delivery)

| Module | Purpose | Spec |
|---|---|---|
| `usg/config.py` | Constants register, pinned vs calibratable, backend configs | Part 12 §12.10 |
| `usg/core/ids.py`, `kinds.py`, `values.py`, `roles.py`, `spans.py`, `records.py` | Typed ids, 15 kinds, five status axes + transition rules, two-tier roles, code-point spans, core records with invariants | Parts 1–2 |
| `usg/storage/schema.py`, `database.py` | STRICT schema, WAL, single writer, **sole-writer table ownership** | Part 11 §11.3, SG-GOV-008 |
| `usg/storage/registry.py` | Sole ID allocator, idempotency, tombstones, never-reused ids | Part 2 §2.4, Part 7 §7.10 |
| `usg/storage/audit.py` | Append-only, hash-chained audit log; models can never be decision actors | SG-FND-004/006, SEC-009 |
| `usg/autonomy/policy.py` | Action classes -> AUTOMATIC / GATED / SHADOW_ONLY / FORBIDDEN; big-model task limits | replaces human review |
| `usg/autonomy/ledger.py` | Big-model quota ledger + circuit breaker | free-plan constraint |
| `usg/autonomy/seal.py` | Sealed-code manifest | SG-FND-005 |
| `usg/cli.py` | `init / status / verify / policy / reseal` | — |

## 5. Delivery plan (12 parts, mirroring the specification)

1. **Foundation** (done) — autonomy, budgets, core types, storage, registry, audit.
2. **Record persistence + Foundation Package** (done) — ontology, relations, FN, 33 frames (24 kernel).
3. **Expression grammar** (done) — sorts, operators, scope, time, typing, canonicalization, serialization.
4. Rulebook, validator (VC checks), certificates and replay.
5. Epistemics, security, **automated verification panel**, risk calibration.
6. Concept identity and resolution.
7. Deterministic interpreter (parser, valence, operators, coreference).
8. Model layer: local gateway, **big-model gateway**, issue digests, rule DSL + automated acceptance gate.
9. Learning and generalization.
10. Cognitive architecture, memory, resource governor.
11. Binary encoding (USBF) and export.
12. Synthetic benchmark, end-to-end runner, packaging.


## 6. Part 2 delivery: data model persistence and the Foundation Package

| Module | Purpose | Spec |
|---|---|---|
| `usg/ontology.py` | Concept seeds, IS_A closure, declared disjointness, **three-valued class compatibility** (COMPATIBLE / INCOMPATIBLE / UNDETERMINED), value domains, structural validation (unsatisfiable concepts, cycles) | Part 3 §3.3.2, Part 7 |
| `usg/model/relations.py` | `RelationDef` (LOGICAL / ASSOCIATIVE / EPISTEMIC), declared properties, edge checks (cycles, asymmetry, weights) | Part 2 §2.8 |
| `usg/model/frames.py` | Frame definitions, append-only role resolution, SPECIALIZES vs STRUCTURAL_INSTANCE_OF, narrowing rules, multi-parent conjunction, parameters/pins, perspectives, `validate_bindings` (VC-S05..S08, VC-T06), projection, version append-only check | Part 4 |
| `usg/foundation/*` | The sealed Foundation Package: 81 concepts, 17 relations, 6 FN primitives + 2 derived + sub-functions, **33 frames (24 kernel)**, each with valid / incomplete / invalid / contrastive tests | Part 4 §4.12 |
| `usg/storage/records_store.py` | Persistence of sources, concepts, relations/edges, frames, referents, frame instances, assertions with invariants enforced at the boundary | Parts 2, 11 |
| `usg/foundation/install.py` | One-transaction install, load-from-database, hash verification | Part 4, SG-FND-005 |

**Decisions and refinements made while implementing**

* **E-117 — ATTITUDE** declares only EXPERIENCER; BELIEVE/KNOW (CONTENT = proposition) and WANT (CONTENT = unasserted situation) each add their own CONTENT. A specialization may not change a role's kind (SG-FRM-003), so the spec's single shared CONTENT was not implementable as written.
* **Kernel set = 24**: the 20 frames of the specification plus OPEN, SEE, ALLERGIC and OWNERSHIP_TRANSFER, which the kernel benchmark and COMMERCIAL_TRANSACTION need.
* **Ontology finding**: "a pump eats" was only UNDETERMINED until animate entities were declared disjoint from artifacts and substances. Disjointness is never inferred (open world); it is declared deliberately in the sealed package.
* **Dictionary tables hold only PROMOTED records.** Candidates and provisional concepts will live in the candidate store (Part 6); the store refuses anything else.
* **Defence in depth**: invariants are enforced in objects, in `RecordStore`, and as SQLite `CHECK`s / triggers (hole states carry no filler, assertions need a source or authorized origin, inferences are never SOURCE_ASSERTED, sources and frame versions are immutable and never deleted).
* **Status changes** (`set_assertion_status`, `set_assertion_stage`) require both the right *writer role* and the right *component*; PROMOTED is reachable only by the promotion controller; no module can reach VERIFIED except the evaluation process.
* **The Foundation Package is sealed twice**: its Python modules are in the code seal, and its database rows are covered by a content hash verified by `python -m usg verify` (exit 4 on tamper).

**Known limits at this stage**: the seed ontology is deliberately small; frame tests are data (strings) that become executable gold in Part 12; class-compatibility checking of fillers belongs to the Part 4 validator (the `Ontology` API it will call is already here); the lexicon and identity resolution arrive in Part 6.


## 7. Part 3 delivery: the expression grammar

| Module | Purpose | Spec |
|---|---|---|
| `usg/grammar/node.py` | Uniform immutable AST (`Node(op, args, params, ann)`), 5 sorts, 36 operators with signatures, authoring builders, readable printer | Part 3 §3.2–3.5 |
| `usg/grammar/typecheck.py` | Static checks: sort discipline, frame application, closed role lists, **three-valued class typing**, figurative (FIG) handling, ALT limits, scope, time, depth; issues vs warnings | SG-CON-002/003/006/007/008, SG-TYP-001/002 |
| `usg/grammar/scope.py` | Free variables, shadowing, alpha-renaming, de Bruijn keys | SG-CON-005 |
| `usg/grammar/timeval.py` | Allen's 13 relations, **exact** consistency solver, anchored resolution of relative time | §3.9 |
| `usg/grammar/canon.py` | Permitted normalizations only, with an audit trace; forbidden simplifications deliberately absent | SG-CAN-001..004 |
| `usg/grammar/serialize.py` | Canonical strings/hashes (structural ignores annotations; full includes them), exact JSON round trip | SG-CAN-004 |
| `usg/grammar/opaque.py` | Referent substitution that respects attitude/attribution contexts | SG-KNW-003 |

**Key properties (all covered by tests)**
* A situation is not a proposition: `NOT(APPLY(...))` is a construction error; builders insert `HOLDS`. A negated giving is therefore never stored as an event that happened (SG-CON-009).
* Annotations (spans, rules, basis) never affect equality or hashing; two expressions differing only in provenance are structurally equal.
* Canonicalization is **idempotent, invariant under reordering/renaming, validity-preserving and JSON-round-trippable** — checked on 300 seeded random expressions each — and never does double-negation elimination, quantifier/negation swaps, duplicate removal, or offer→give normalization.
* The Allen solver agrees with an exhaustive search over interval placements (250 random constraint triples, both outcomes exercised).
* Relative time resolves only against a source anchor; vague or ambiguous expressions stay unresolved; the resolved bounds are stored next to the original expression.

**Defects found by the tests while building (and fixed)**
* **Canonical sort keys used variable names**, so alpha-renaming could reorder `AND` children and break idempotence. Keys are now built from de Bruijn indices (binding distance), independent of names and sibling order.
* **E-118 — CAUSATION relates propositions**, not situations. The specification's own worked example puts a *negated* giving as an effect, which a bare situation cannot represent.
* **Ontology gap**: "a person is not a place" was only UNDETERMINED until animate entities were declared disjoint from locations (a sealed-seed declaration, never inferred).

**Choices to be aware of**: the canonical direction of an inverse relation pair is the alphabetically first name; `INSTANT` date-times have no extent and take no part in interval reasoning; class warnings (`W-TYPE-UNDETERMINED`, `W-FIGURATIVE`) raise review priority later but never invalidate an expression.
