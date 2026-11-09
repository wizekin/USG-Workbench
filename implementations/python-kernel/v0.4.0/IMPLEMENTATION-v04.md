# USG 0.4: seven implementation workstreams

This release adds executable work in each of the seven requested areas. Runtime
operation requires neither human review nor a model. It does not establish full
semantic conformance with every requirement of the twelve-part specification.

| Step | Implemented behavior | Executable evidence |
|---|---|---|
| 1. Audit and traceability | Reproducible inventory of 423 normative/rule statements and 562 sections across all twelve parts; exact source locations, source hash, implementation/test references and explicit unproven status. References cannot manufacture conformance. | `usg traceability`; `TraceabilityTests` |
| 2. Semantic foundation | Typed scoped definitions, immutable constraints, append-only versions, compare-and-swap updates, history, completeness metadata, hash audits, essential-condition inheritance and automatic equivalence revocation on definition changes. Identity checks use the current scoped definition. | `DefinitionWorkflowTests` |
| 3. Assurance | Reproducible derivations retain configuration, discourse, lexical resources and dependency analyses; seven explicit L5 contextual outcomes; unavailable checks remain NOT_CHECKED. Exact-context conflict index, authenticated evidence evaluation, signing-key independence checks, transactional promotion checks, persisted independent-origin calibration, ECE, conservative Wilson bounds, drift detection and bounded constant tuning. Essential completed effects are checked against contradictory properties within one context. | `ContextAndCalibrationTests`; `ContextRegressionTests`; existing evaluation/validator tests |
| 4. Interpretation | Installation-owned, versioned lexical resources that preserve ambiguity; offline CoNLL-U input with source offsets, coverage/cycle checks and a closed dependency compiler. Expanded Arabic past/present verbs, vocalization handling, explicit past/future negation and relative dates. Unsupported dependencies, morphology and questions abstain. | `LanguageAdapterTests`; Arabic and question regression tests |
| 5. Learning | Typed anti-unification, co-reference preservation, positive/contrastive testing, bounded shadow hypotheses, counterexample rejection and automatic discovery/testing of vetted aliases. Canary observations are deduplicated and must exercise the rule. Claims record rule dependencies; cascading rollback invalidates affected claims and automatically queues source reprocessing. New pipeline results supersede old interpretations in current views while preserving history. Exact world mentions retain their IDs on replay. | `LearningLifecycleTests`; current-view/replay regression tests |
| 6. Runtime and interchange | Function inheritance without entity-class substitution; scoped domain-model definition entailments; measured RAM/disk/load backpressure, conservative rules-only fallback, queue aging and lease renewal. Exact structural templates, hardened decoding, measured codec fallback, JSON-LD/Turtle/TriG, ontology/relation metadata, SHACL shapes, PROV-O source envelopes and named contexts. JSON-LD source imports re-enter quarantine. | `RuntimeAndEncodingAcceptanceTests`; exchange and inference tests |
| 7. Acceptance and delivery | Packaged offline acceptance, full regression mode, adversarial/restart/corruption checks, schema upgrade checks, an acceptance-gated upgrade command with a pre-migration snapshot and automatic restoration on failure, wheel packaging and runnable examples. | `ReleaseAcceptanceTests`; `usg acceptance --full` |

## Operational use

```powershell
.\run-usg.ps1 run --db output\usg-v04.db --input examples --watch
.\run-usg.ps1 acceptance --full --output acceptance-v04.json
.\run-usg.ps1 traceability --output requirements-traceability.json
.\run-usg.ps1 ingest --db output\usg-v04.db --text "The surgeon examined the patient." --lexicon examples\lexicon.json
.\run-usg.ps1 ingest --db output\usg-v04.db --file examples\dependency-source.txt --conllu examples\dependency-analysis.conllu
.\run-usg.ps1 define --db output\usg-v04.db --file examples\definition.json
.\run-usg.ps1 reason --db output\usg-v04.db --view source --scope example-medicine
.\run-usg.ps1 export --db output\usg-v04.db --output output\knowledge-v04.usbf --codec template
.\run-usg.ps1 export --db output\usg-v04.db --output output\knowledge-v04.jsonld --format jsonld
```

Use new output filenames: artifacts and backups are not silently overwritten.
`define` stipulates meaning within a named domain model; it grants no world-truth
status. Empirical conditions cannot be promoted to defining ESSENTIAL conditions.
`calibration --category NAME` reports calibration from persisted observations;
missing independent observations keep the category uncalibrated.

For an existing database on the compatible foundation release, a deployment job
can execute `upgrade --db DATABASE --backup NEW_BACKUP`. It runs offline acceptance,
checks the existing audit/database/foundation, snapshots it, migrates, reseals the
explicit new release, and audits the result. Failure restores the snapshot. This
command assumes the installation is stopped for the release. The inbox worker
does not reseal enforcement code. Incompatible foundation meanings are refused.

## Evidence and limits

`acceptance-v04.json` records 430 passing regression tests, thirteen passing release
checks, and the 49-case constructed benchmark. No model was used. The benchmark
measures covered constructions and implementation consistency, not unrestricted
natural-language accuracy. Its timing excludes storage, model calls and I/O.

The requirement inventory deliberately leaves semantic requirements unproven
where it has only references. It is not a certification. Remaining limits are
open-domain language understanding, independent natural-language evaluation,
unrestricted novel-concept/fundamental-frame promotion, complete domain theories,
general procedural discovery, authoritative distributed sharding, and unrestricted
external RDF/OWL import/reasoning. Physical domain files remain verified snapshots.
Shadow learning cannot override these boundaries merely by accumulating examples.

Contextual checks are finite checks, not an oracle. A cross-claim conflict requires
matching persistent referents, context and an explicit shared temporal reference;
unknown past occurrence times are not equated. Similar names never establish
individual identity. Signed attestations satisfy an installed policy, not a
universal guarantee that an authority is correct.

The linked-data profile preserves full expression payloads and reified syntax.
USG extensions carry scope, alternatives, holes and epistemic distinctions that
have no direct OWL equivalent. JSON-LD and TriG retain named contexts; Turtle
retains syntax and provenance but loses graph membership. External contexts and
OWL imports are never fetched or executed. Reference standards:
[PROV-O](https://www.w3.org/TR/prov-o/),
[SHACL](https://www.w3.org/TR/shacl/).

## Post-v0.4 semantic-kernel correction (2026-11-07)

The typechecker now validates exact semantic kinds after the existing broad-sort
check. This closes a defect where `EVENT`, `PROCESS`, and `STATE` (all `SIT`), or
`VALUE` and `QUANTITY` (both `VAL`), could be interchanged in a frame role.
Every branch of an `ALT` is checked independently. Regression coverage and the
full acceptance results are recorded in `SEMANTIC-KERNEL-KIND-FIX.md`.
