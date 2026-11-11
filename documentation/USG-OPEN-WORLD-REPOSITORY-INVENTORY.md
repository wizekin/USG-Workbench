# OW-0 — USG repository and capability inventory

**Status:** OW-0 inventory completed; reviewable repository evidence recorded.  
**Inventory snapshot:** `7a71afec5cafcda6bd8b88f26e57cfe600de6860` on `main` (2026-11-11).  
**Machine-readable companion:** [USG-OPEN-WORLD-CAPABILITY-INVENTORY.json](USG-OPEN-WORLD-CAPABILITY-INVENTORY.json)

## 1. Executive finding

The repository does **not** contain one unified general-purpose USG chatbot. It contains multiple versioned implementation lines and supporting semantic services. They have different runtimes, contracts, entry points, persistence boundaries, and capability limits. The evaluator must test them separately.

The inventory is pinned to commit `7a71afec5cafcda6bd8b88f26e57cfe600de6860`. That snapshot contains 1,124 tracked tree entries (936 files), 91 workflow YAML files, 89 root-level Python test files, and 7 JavaScript Workbench test files. These counts describe repository structure; they are not counts of passing tests or proof that every workflow ran.

## 2. Implementation and capability map

| Evaluation target | Actual entry point(s) | What is present | Capability boundary |
|---|---|---|---|
| JavaScript Semantic Workbench v0.5.4 | `implementations/semantic-workbench-js/v0.5.4/launch_windows.bat`, `index.html`, `server.js` | Local-first browser workbench, source composer, semantic graph, optional local Ollama generation/review/repair, typed generation-failure audit | Finite English source-composition patterns; optional model path is not proof of general understanding. Its deterministic tests use fixtures/fake endpoints and do not establish live model quality. |
| Python reference kernel v0.4.0 | `implementations/python-kernel/v0.4.0/usg/__main__.py`, `usg/cli.py`, `run-usg.ps1` | Versioned semantic kernel package with its own internal modules, runtime, CLI, and package-local tests | Preserved reference baseline. Keep it independent of the top-level local API and newer model packages. |
| Python kernel snapshot v0.5.0 | `implementations/python-kernel/v0.5.0/usg/__main__.py` | Versioned successor snapshot with additional predicate-application, connective, and quantifier constructors | Separate package/version; do not merge results with v0.4.0. |
| Python native model packages v0.6.0–v1.4.0 | Version-specific package `__init__.py` files under `implementations/python-kernel/` | Referent identity, Mention, Assertion, Evidence, Context, ExpressionRelation, typed UnresolvedItem, Derivation, and Definitions catalogue models | These are native model/record APIs, not complete language parsers. v1.2.1 is the typed UnresolvedItem generation used by the composed adapter; v1.2.0 is historical. |
| Python canonical document adapters | `interoperability/python_adapter/document_v*.py`; composed `document_v15.py` | Loss-preserving USG-SEM/1.0 mapping across versioned native record families, with mapping reports and cross-family checks | Adapters are serialization/projection boundaries, not parsers. PARTIAL mapping is expected where no exact native representation exists; canonical-only records must be preserved. |
| Phase 2 structured reasoning | `tools/semantic_grounding_v1_0_0`, `semantic_rule_registry_v1_0_0`, `semantic_rule_semantics_v1_0_0`, `semantic_inference_v1_0_0`, `semantic_evidence_assessment_v1_0_0`, `semantic_query_interface_v1_0_0` | Deterministic grounding, rule validation, inference execution, evidence/conflict assessment, structured query/explanation, and controlled benchmark | Operates on structured semantic documents/rules/evidence. It is not a free-form language interpreter. |
| Phase 3 canonical store | `tools/semantic_graph_store_v1_0_0/store.py`, `canonical.py`, persistent query service | SQLite canonical persistence, immutable revisions, validation, query, integrity, export, and conflict handling | SQLite is the authoritative store. DuckDB, LanceDB, Qdrant, and RocksDB/Rocksdict code is comparison/evaluation work, not the canonical runtime. |
| Phase 4 interpreter v0.1.0 | `tools/usg_interpretation_v0_1_0/pipeline.py`; Kernel Lab `POST /v1/interpret` | Bounded raw-text-to-USG-SEM/1.0 demonstrator with staged source, lexical, syntax, semantic-composition, mention, discourse, assertion/evidence, and resource processing | Small bounded English/MSA Arabic scope, not a general-purpose English or Arabic parser. |
| Phase 5 interpreter v0.2.0 | `tools/usg_interpretation_v0_2_0/integration.py`; `POST /v2/interpret`; CLI `interpret-v2` | Lexical, segmentation, syntax, operator, semantic composition, discourse artifacts, resource catalogue, immutable runs, and deterministic replay | The pipeline does not emit a USG-SEM/1.0 document. The accepted 100-fixture benchmark measures three simple-transitive English/MSA Arabic target constructions only. |
| Phase 6 expansion | `tools/phase6_predicate_argument_v0_3_0`, `phase6_semantic_frames_v0_3_0`, `phase6_nominal_candidate_v0_4_1`, UD and external parser adapters | Steps 6.1–6.5 accepted for their bounded scope; Step 6.6 nominal/property/modifier candidate work and external structural audits | The current Phase 6 roadmap says Step 6.6 remains blocked on an independent bilingual semantic-gold acceptance set; Step 6.7 remains blocked. Candidate evidence is not accepted capability. |
| Kernel Lab / local API / CLI | `tools/usg-kernel-lab/server.py`, `tools/usg-kernel-lab/index.html`, `tools/usg_local_api_v1_0_0/application.py`, `cli.py` | Loopback browser UI, shared HTTP/CLI dispatcher, canonical document endpoints, Phase 4/5 entry points, SQLite store and replay | Runs locally on loopback; it does not unify every JS/Python implementation or every model version into one service. |
| JavaScript Workbench adapter | `interoperability/workbench_adapter/index.js`, `reconstruct.js` | Conversion between Workbench semantic-core representation and canonical USG-SEM/1.0 with mapping/validation reporting | Contract adapter, not a natural-language understanding entry point. |

## 3. Python model generations are not one runtime

The versioned model line must be recorded separately:

| Version | Model family | Package |
|---|---|---|
| 0.6.0 | Referent identity | `usg_identity_v06` |
| 0.7.0 | Mention occurrence | `usg_discourse_v07` |
| 0.8.0 | Assertion | `usg_assertion_v08` |
| 0.9.0 | Evidence | `usg_evidence_v09` |
| 1.0.0 | Context | `usg_context_v10` |
| 1.1.0 | ExpressionRelation | `usg_expression_relation_v11` |
| 1.2.0 | Initial UnresolvedItem (historical) | `usg_unresolved_v12` |
| 1.2.1 | Typed UnresolvedItem | `usg_unresolved_v121` |
| 1.3.0 | Derivation | `usg_derivation_v13` |
| 1.4.0 | Definitions catalogue | `usg_definitions_v14` |

The composed document adapter is version 1.5.1; it composes the family-specific adapters over an immutable canonical snapshot. It is not a v1.5.1 natural-language parser.

## 4. User-facing execution surfaces

### Python local service and Kernel Lab

The root package declares the console script:

```text
usg-workbench = tools.usg_local_api_v1_0_0.cli:main
```

Local launch commands documented by the repository:

```powershell
py tools/usg-kernel-lab/server.py
```

or, after installing the root package:

```powershell
usg-workbench lab --db .\usg-workbench.sqlite3
```

The local service binds to `127.0.0.1:8765`. The shared API/CLI includes canonical validation, document storage/retrieval/revisions, integrity checking, conditions, contradictions, export, structured query, Phase 4 `/v1/interpret`, and Phase 5 `/v2/interpret`, resource manifest retrieval, immutable interpretation runs, and replay. The documented health endpoint is `GET /health`; `GET /v1/health` is not defined.

### JavaScript workbench

The v0.5.4 Windows launcher starts the local Node bridge when Node.js is present, otherwise it falls back to a static local browser mode. The full optional bridge talks to a local Ollama-compatible service; it must be evaluated separately from the deterministic Phase 4/5 services.

## 5. Contracts, schemas, and resources

The canonical interchange contract is `USG-SEM/1.0`, defined in `specifications/USG-SEM-1.0.md` and `specifications/usg-sem-1.0.schema.json`.

Other versioned contract/registry assets include the Phase 6 interpretation and expression-graph schemas, predicate-frame registry schemas, operator-scope registry schema, Workbench adapter documentation, and Python extension contracts. Resource families include lexical resources v0.1.0–v0.3.0, Phase 6 English/Arabic candidate lexicons, operators v0.1.0, semantic frames v0.3.0, Phase 6 construction rules, and the Phase 2 semantic reasoning rule registries.

The machine-readable inventory lists every current schema, resource family, and ruleset path used in this map. The list is deliberately path-based so CI can flag deleted or moved resources.

## 6. Existing benchmark inventory

The repository already contains controlled diagnostic corpora for:

- Phase 4 interpretation v0.1.0.
- Phase 5 interpretation v0.2.0 and v0.2.1.
- Phase 6 interpretation v0.3.0, v0.3.1, v0.3.2, v0.4.0, v0.4.1, and v0.4.2.
- Phase 2 semantic reasoning v1.0.0, plus separate executor, query, and evidence fixture suites.

These are not three independent open-world populations. In particular, this audit did not identify a repository-owned naturalistic request corpus with verified licenses for the new campaign, nor an unconstrained random population. Existing benchmark results must remain separate from future open-world results.

## 7. Known implementation gaps before OW-1

The following OW program components were absent from the repository snapshot:

1. A seeded/unseeded open-world scenario generator.
2. A unified isolated runner for all selected USG entry points.
3. Shared case/result/report schemas and an append-only report store.
4. A repository-owned naturalistic corpus with verified source/license metadata.
5. A failure-clustering/minimization/adaptive-discovery loop.
6. A continuous open-world schedule and hidden-sample rotation mechanism.

OW-0 therefore does **not** claim that randomized simulations have run. It identifies the exact systems and boundaries that OW-1 through OW-8 must respect.

## 8. Evaluation rules derived from the inventory

- A test case is routed to a named implementation, version, interface, and contract—not simply to “USG”.
- Model-only APIs are evaluated as data-model contracts, not as parsers.
- Adapters are evaluated for mapping fidelity, loss preservation, and round-trip conformance.
- Structured reasoning services are evaluated with structured inputs and independent deterministic oracles.
- Text interpreters are evaluated only within their stated language/construction scopes; outside-scope behavior is reported as unsupported/unknown rather than treated as a false parse.
- SQLite is the canonical persistence target; alternate database prototypes are not interchangeable backends.
- Phase 6 Step 6.6 candidate output is not accepted semantic gold.
- Semantic correctness is scored only where an independent oracle exists. Unsupported, partial, ambiguous, abstained, timeout, crash, and infrastructure-error outcomes stay distinct.

## 9. OW-0 exit determination

**OW-0 inventory deliverable: complete.** The inventory identifies the implementation lines, versioned native models, adapters, actual text-interpreter stages, structured reasoning services, storage/API/CLI/browser interfaces, schemas, resource families, existing controlled benchmarks, and known gaps. The companion JSON is checked by a new repository validation workflow so deleted or moved inventory paths fail CI.

OW-1 can now define the protocol and common report schemas against an explicit, versioned test surface.
