# USG Phase 3 — Persistent Semantic Graph and Bounded Product Core

**Status:** IN PROGRESS — Steps 3.1–3.8 are merged; Step 3.9 runs the integrated automated exit acceptance gate.
**Prerequisite:** Phase 2 exit acceptance passed on merged main commit da0760ac13029892f40a08a412e139c34a8e48d3.
**Normative semantic contract:** USG-SEM/1.0.
**Implementation boundary:** additive tools and packages; do not mutate archived releases or the completed Phase 1/2 contracts.

## 1. Goal

Turn the accepted Phase 2 reasoning pipeline into a persistent, locally usable semantic system. The next increment is not a broader claim of universal language understanding. It is a reliable system that can persist complete USG-SEM documents, reason over a deliberately expanded but formally bounded operator subset, and expose useful document-analysis operations through a local API, CLI, and Kernel Lab.

The first product slice is a **conditions, exceptions, and contradiction inspector** over validated USG-SEM documents. It must show the represented structure, exact source evidence, separate epistemic/evidence statuses, derivations, unresolved portions, and reasons for abstention.

## 2. Non-negotiable invariants

1. **USG-SEM/1.0 remains authoritative.** Do not add fields or statuses to its schema implicitly. Any required contract change needs a separately versioned profile and migration.
2. **Canonical graph first.** The complete compositional expression graph is authoritative. Flat claim rows, SQL indexes, UI summaries, and generated prose are derived projections only.
3. **Lossless persistence.** Store and reload must preserve every record family, every ordered array, shared expression references, opaque extensions, source text, and unresolved content. No unsupported record is silently dropped or rewritten.
4. **Exact source preservation.** Do not normalize source Unicode, whitespace, punctuation, or text before hashing or calculating spans. USG-SEM source offsets remain zero-based, end-exclusive Unicode code-point offsets.
5. **No truth promotion.** Persistence, structural validation, inference, source alignment, and successful API responses do not establish objective truth. Evidence dimensions remain independent.
6. **Scope-safe reasoning.** Negation, conditionals, exceptions, attribution, modality, and quantifier scope must remain structural and ordered. A rule must declare exactly what it licenses.
7. **Open-world behavior.** Missing facts never satisfy an exception or antecedent. UNLESS does not become an assertion of its consequent merely because the exception is absent.
8. **No arbitrary semantic-complexity caps.** Resource budgets may stop work, but the result must be explicitly INCOMPLETE with diagnostics. Never truncate semantic arrays, graph nodes, operands, candidates, or conclusions silently.
9. **Deterministic and reproducible.** Identical canonical documents, rule versions, and execution configuration produce equivalent structured results and provenance.
10. **No human-review dependency.** Acceptance is through automated tests, frozen fixtures, schema validation, mutation/adversarial cases, and machine-readable reports. Human review queues and correction flywheels are excluded from this phase.
11. **Preserve baselines.** Phase 1/2, USG-SEM/1.0, and archived Python/JavaScript releases remain immutable. New behavior is additive and separately versioned.

## 3. Phase 3 architecture

- **Canonical document store:** authoritative immutable USG-SEM snapshots with canonical bytes, content hashes, schema/profile pins, and append-only revisions.
- **Derived indexes:** rebuildable SQLite indexes for document, expression, assertion, evidence, context, and source lookups. Index rows never replace or override the canonical snapshot.
- **Scope-aware inference:** additive, versioned rule handlers for a narrow set of operator-aware reasoning tasks. Each rule has positive, boundary, and forbidden-inference fixtures.
- **Document analysis services:** deterministic operations over persisted documents, including query, conditions/exception extraction, and same-scope contradiction inspection.
- **Local API and CLI:** a local-only service and command-line interface with explicit status, evidence references, derivation traces, unresolved portions, and abstention diagnostics.
- **Kernel Lab:** a local browser UI to load/persist documents, run analysis, inspect conditions and conflicts, and export complete machine-readable results.
- **Release and acceptance:** reproducible installation/demo, version manifest, and an integrated Phase 3 gate.

The older Python kernel storage/reasoning implementation and the new Phase 2 USG-SEM reasoning tools are distinct implementation lines. Phase 3 must inspect and reuse proven algorithms where appropriate, but must not assume their data models are interchangeable or write canonical documents through an unverified legacy adapter.

## 4. Ordered implementation sequence

| Step | Name | Main deliverable | Exit condition |
|---|---|---|---|
| **3.1** | Canonical graph-store contract | Versioned storage design, document lifecycle, canonicalization/hash rules, transaction/revision semantics, and test contract | Store invariants are precise and compatible with USG-SEM/1.0; no schema mutation or semantic loss is required. |
| **3.2** | SQLite canonical document store | New versioned store package, migrations, atomic writes, immutable snapshots/revisions, integrity verification, and rebuildable indexes | Every accepted document round-trips byte-identically; hash/schema/reference checks detect tampering and corruption; retries are idempotent. |
| **3.3** | Persistent query integration | Query and evidence assessment read from stored canonical snapshots and return revision-pinned results | A query result is reproducible from its exact document revision, rule versions, and configuration; storage failure cannot produce a partial success. |
| **3.4** | Scope-aware rule expansion | Additive rule package for explicitly specified NOT/IF/UNLESS/attribution behaviors | Each enabled rule passes positive, negative, scope, attribution, conflict, open-world, and forbidden-inference fixtures; unsupported patterns abstain. |
| **3.5** | Conditions and contradiction services | Deterministic document-level conditions/exception map and exact-scope conflict report | Conditions retain polarity, scope, exception linkage, and source spans; contradictions are never inferred across incompatible contexts or attribution boundaries. |
| **3.6** | Local API and CLI | Versioned local HTTP endpoints and CLI for validate/store/get/query/check/conditions/contradictions/export | Responses are schema-valid, deterministic, explicit about incomplete/unsupported outcomes, and loopback-only by default. Raw-text interpretation is exposed only where an implemented parser can support it; otherwise it is explicitly unsupported. |
| **3.7** | Kernel Lab product integration | UI for stored documents, conditions, exceptions, conflicts, evidence axes, derivation traces, and JSON export | The UI operates on the same API and canonical store; it does not create a second source of truth or conceal diagnostics. |
| **3.8** | Packaging and one-command demo | Installable local package, pinned dependencies, sample canonical documents, launch command, and reproducible release manifest | A clean environment can install and run the bounded product without cloud services, paid APIs, or human approval. |
| **3.9** | Phase 3 exit acceptance | Integrated store, inference, API, UI, regression, and release gate | All frozen acceptance checks pass on the exact PR head and merged main commit; limitations remain explicit. |

Steps are sequential unless the roadmap explicitly marks a task independent. A later step cannot bypass a failed earlier gate. Every implementation step uses a dedicated PR; merge only after all required checks on that exact PR head succeed.

## 5. Step 3.4 reasoning boundary

The first expansion is intentionally narrow:

- **NOT:** preserve and inspect negation at its exact structural scope. A negated expression is not treated as an affirmative assertion, and nested operator scope is not flattened.
- **IF:** Modus Ponens may fire only when the exact antecedent is an eligible assertion in the same applicable context/commitment/attribution binding and the rule's other premises are satisfied.
- **UNLESS:** represent the consequent as conditional on the exception. The absence of the exception is not evidence that the consequent holds. No closed-world assumption is introduced.
- **Attribution:** an attributed proposition remains attributed. No inference may cross from ATTRIBUTED to AUTHOR/ASSERTED without an explicit, separately specified rule that is not part of this initial expansion.
- **Conflict:** compare only under the explicit context, commitment, attribution, polarity, and scope policy. Do not select a winner or collapse conflict into a confidence score.

The rules will be additive and versioned. Existing Phase 2 v1.0.0 rules, activation manifests, and result contracts remain unchanged.

## 6. Exclusions

The following are not Phase 3 deliverables:

- human-review queues, manual adjudication, or correction flywheels;
- autonomous invention or promotion of ontologies, frames, or rules;
- unrestricted natural-language understanding or a general theorem prover;
- world-truth determination from text;
- distributed/multi-controller deployment;
- multilingual expansion;
- public multi-user hosting or production/security certification;
- claims of operational readiness before the Phase 3 gate passes.

Independent model-based semantic verification, broader parser coverage, external ontology mappings, and additional domains may be proposed in later phases only with separate evaluation contracts and evidence.

## 7. Phase 3 acceptance principles

The integrated gate must report independent results for:

- byte-identical canonical document round-trip and content-hash integrity;
- schema, typed-reference, graph, and source-span integrity;
- persistence atomicity, idempotency, revision immutability, and recovery;
- inference precision and false-inference rate for every enabled rule;
- operator-scope, attribution, context, and exception correctness;
- evidence alignment, semantic support, contradiction, source independence, corroboration, and external verification as separate axes;
- derivation completeness and revision/rule-version reproducibility;
- explicit abstention and INCOMPLETE behavior under unsupported input or resource interruption;
- Phase 1 and Phase 2 regression compatibility;
- local-only API/UI behavior and clean-install reproducibility.

No aggregate score may conceal a failure in a critical invariant. A failed critical gate blocks acceptance.

## 8. Current status

Phase 1 is complete. Phase 2 Steps 2.1–2.10 are complete for their documented scope. The final Phase 2 merged-main acceptance run [42811673922](https://github.com/wizekin/USG-Workbench/actions/runs/42811673922) passed. The completion record was merged in [PR #53](https://github.com/wizekin/USG-Workbench/pull/53).

Steps 3.1–3.8 are complete and merged. Step 3.2 provides the authoritative SQLite store; Step 3.3 provides revision-pinned persistent queries; Step 3.4 adds versioned scope-aware operator inspection; Step 3.5 provides conditions/exception maps and exact-scope contradiction reports; Step 3.6 provides the loopback-only API and CLI; Step 3.7 integrates the browser Kernel Lab with that same API and SQLite database; Step 3.8 packages the local workbench, pinned dependencies, sample canonical documents, one-command demo, and reproducible SHA-256 release manifest. SQLite remains the only canonical backend after evaluation of LMDB, RocksDB, DuckDB, LanceDB, and Qdrant. Step 3.9 is the remaining integrated acceptance gate.
