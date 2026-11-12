# USG cross-implementation tests

This directory contains contract-level fixtures, adapter tests, round-trip conformance tests, and regression cases spanning implementation boundaries.

Each test must identify the contract and implementation versions it covers. Package-local tests remain with their respective implementation baselines.

## Current Phase 1 checks

Predicate/frame registry:

```bash
python -m unittest discover -s tests -p "test_predicate_frame_registry.py" -v
```

Operator/scope registry:

```bash
python -m unittest discover -s tests -p "test_operator_scope_registry.py" -v
```

Document-level Python adapter:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_document_adapter.py" -v
```

The document adapter tests verify the full USG-SEM/1.0 envelope, exact source and assertion projections where supported, shared expression-DAG identity across roots, explicit partial mapping for unsupported kernel records/constructors, Unicode code-point spans, and exact canonical-document export. The adapter does not alter the Python kernel 0.4.0 baseline or write to its SQLite store.

The predicate/frame test checks registry coverage against the Workbench predicate vocabulary and verifies target frame names, versions, inherited roles, role requirements, and class constraints against the archived Python kernel source.

The operator/scope test checks registry dispositions against Workbench operator declarations and verifies the Python kernel operator signatures, quantifier distinctions, conditional/unless scope semantics, and loss-prevention policy against both immutable source baselines.


Python reverse serializer (Phase 1 Step 4B):

```bash
python -m unittest discover -s tests -p "test_python_reverse_serializer.py" -v
```

The reverse serializer tests cover fresh serialization of current Python Source,
SemIR Node and Assertion projections; operand order; modified roots; annotation
source-reference safety; preservation of unsupported original roots; canonical
snapshot integrity; and JSON Schema validation. Canonical-only record classes
remain in the output and are explicitly listed as unmapped to kernel 0.4.0.

Workbench source adapter (Phase 1 Step 4A):

```bash
node --test tests/test_workbench_source_adapter.js
python -m unittest discover -s tests -p "test_workbench_source_adapter.py" -v
```

The source adapter tests exercise Workbench v0.5.4 semantic-model conversion, operator/connective scope, argument-role ordering, unresolved mentions, native snapshot digests, partial mapping, dangling references, and UTF-16 → Unicode code-point offset conversion. The Python test validates the actual generated document against the USG-SEM/1.0 JSON Schema.

The complete four-boundary execution test is implemented in Step 4D. The expected result is document-level PARTIAL wherever Python 0.4.0 lacks an exact native constructor or enum; those records must remain canonical and explicitly reported. This is successful conformance to the loss-preservation contract, not a claim that every Workbench semantic construction is natively executable in Python 0.4.0.


End-to-end semantic invariant conformance (Phase 1 Step 4D):

```bash
python -m unittest discover -s tests -p "test_round_trip_conformance.py" -v
```

This suite executes Workbench v0.5.4 → USG-SEM/1.0 → Python kernel 0.4.0
projection → fresh USG-SEM/1.0 serialization → Workbench reconstruction. It
compares semantic invariants rather than generated IDs or incidental JSON
ordering. It includes nested operator scope, FORALL versus EXISTS scope under
negation, directed IF/UNLESS, WHEN versus CONCESSIVE, role ordering, tense,
aspect, temporal metadata, attribution, unresolved mentions, evidence alignment
after supplementary Unicode, relation metadata, multiple roots, unsupported
canonical constructors, source-builder warnings, stale native snapshots, and a
512-root graph. A PARTIAL result is expected where Python 0.4.0 lacks an exact
constructor; the canonical graph must survive unchanged and be reported rather
than coerced.


Python kernel 0.5.0 USG-SEM graph adapter (Phase 1 Step 5C):

```bash
python -m unittest discover -s tests -p "test_python_kernel_v05_adapter.py" -v
```

This suite exercises native `PREDICATE_APP`, `CONNECTIVE`, and `QUANTIFIER` projections, reverse graph serialization, binder identity, OPAQUE/UNRESOLVED_REF distinctions, unknown and malformed operators, and shared DAG identity. It runs in an isolated Python process with the v0.5.0 package path; the existing v0.4.0 adapter remains unchanged.


Python kernel 0.5.0 document-level adapter (Phase 1 Step 5D):

```bash
python -m unittest discover -s tests -p "test_python_kernel_v05_document_adapter.py" -v
```

This suite verifies the full USG-SEM/1.0 document envelope around native v0.5.0
expression roots, preservation/reporting of canonical-only record families,
fresh serialization of edited native Nodes, immutable snapshot enforcement,
unreachable-expression retention, and invalid-document rejection. It does not
claim native v0.5.0 document records for sources, referents, mentions,
assertions, evidence, contexts, definitions, relations, unresolved items, or
derivations.


Step 5E adds exact native Source record coverage to the Python kernel 0.5.0
document adapter suite. It verifies typed source identity, exact round-trip,
native text edits with SHA-256 recomputation, and canonical-only preservation
for unsupported or absent source enum values. The same suite retains the Step
5D full-document, graph-edit, and stale-snapshot checks.


## Phase 2 Step 2.2 — Semantic reasoning benchmark

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_semantic_reasoning_benchmark.py" -v
```

The versioned corpus is in `benchmarks/semantic-reasoning/v1.0.0/`. It includes fixture and candidate-result JSON Schemas plus frozen pre-inference thresholds. The evaluator is `tools/semantic_reasoning_benchmark_v1_0_0/evaluator.py`; it scores structured candidate results and does not execute inference. Tests validate the 35 fixtures and inject prohibited conclusions, scope/evidence errors, missing provenance, dropped items, resource truncation, nondeterminism, and per-category coverage failures.

See [Phase 2 Step 2.2 documentation](../documentation/PHASE-2-STEP-2.2-BENCHMARK-CORPUS-AND-EVALUATOR.md).


## Phase 2 Step 2.3 — Declarative rule model and registry

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_rule_registry.py" -v
```

The rule-model package is in `rules/semantic-reasoning/v1.0.0/`. The static validator is `tools/semantic_rule_registry_v1_0_0/validator.py`. The registry contains four disabled reference rules and cross-links to positive and negative/boundary/adversarial/unsupported fixtures in the frozen Step 2.2 corpus. No rule is executable in Step 2.3.

See [Phase 2 Step 2.3 documentation](../documentation/PHASE-2-STEP-2.3-RULE-MODEL-AND-REGISTRY.md).


## Phase 2 Step 2.4 — Rule semantics and safety contract

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_rule_semantics.py" -v
```

The formal contract is in `rules/semantic-reasoning/semantics/v1.0.0/`; the static cross-validator is `tools/semantic_rule_semantics_v1_0_0/validator.py`. It defines nine distinct applicability outcomes, all 19 rule constraint kinds, the initial SOURCE_ASSERTED-only premise policy, conflict and open-world behavior, deterministic ordering, and interruption without semantic truncation. No rule is executable in Step 2.4.

See [Phase 2 Step 2.4 documentation](../documentation/PHASE-2-STEP-2.4-RULE-SEMANTICS-AND-SAFETY-CONTRACT.md).


## Phase 2 Step 2.5 — Deterministic grounding services

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase2_grounding.py" -v
```

The grounding service is `tools/semantic_grounding_v1_0_0/grounding.py`. It resolves typed records, exact definition versions/catalogue releases, explicit Mention-to-Referent links, assertion contexts, context parent paths, and exact ordered expression scope paths. It returns distinct resolution states and never resolves identity by label. The compact Step 2.2 fixture preflight preserves payloads and reports missing canonical fields without defaulting assertion status.

See [Phase 2 Step 2.5 documentation](../documentation/PHASE-2-STEP-2.5-DETERMINISTIC-GROUNDING-SERVICES.md).


## Phase 2 Step 2.10 — Final exit acceptance

Run the complete integrated Phase 2 and Phase 1 compatibility gate:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m tools.phase2_exit_acceptance.run --report phase2-exit-acceptance-report.json
```

The runner compiles all Phase 2 packages, validates the declarative rule registry and semantics contract, reruns the frozen Step 2.2 evaluator tests, all Phase 2 step regressions, the Kernel Lab integration tests, and the Phase 1 exit/adapter/interoperability suites. It emits a schema-validated JSON report. The overall status is ACCEPTED only if every required check passes. GitHub Actions uploads the report as an artifact; a failed or missing check blocks Phase 2 completion.

See [Phase 2 Step 2.10 documentation](../documentation/PHASE-2-STEP-2.10-EXIT-ACCEPTANCE.md).


## Phase 3 Step 3.2 — SQLite canonical document store

Run the dedicated store suite:

```bash
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_phase3_graph_store.py" -v
```

The package is tools/semantic_graph_store_v1_0_0. It stores complete canonical USG-SEM/1.0 snapshots as authoritative bytes and maintains rebuildable SQLite indexes for expressions, assertions, evidence, and sources. Tests cover canonical byte round-trip, Unicode preservation, immutable revisions, compare-and-swap updates, idempotency, atomic rollback, hash/integrity checks, index rebuild, and large graph preservation. See [Step 3.2 documentation](../documentation/PHASE-3-STEP-3.2-SQLITE-CANONICAL-STORE.md).


## Phase 6 automatic acceptance factory

The deterministic generator and integrated API evaluator are documented in [the Phase 6 Automatic Acceptance Factory](../documentation/PHASE-6-AUTOMATIC-ACCEPTANCE-FACTORY.md).

```bash
python -m unittest discover -s tests -p 'test_phase6_acceptance_v1_0.py' -v
python -m unittest discover -s tests -p 'test_phase6_auto_reference_v1_0.py' -v
python -m tools.phase6_acceptance_v1_0.generate
python -m tools.phase6_acceptance_v1_0.evaluate
```

The evaluator writes the bilingual corpus and schema-validated report to the documented benchmark/artifact paths. A successful execution means the evaluation completed; the report's per-step status remains authoritative for Phase 6 acceptance.


## Phase 7 knowledge contract

Run `python -m pip install jsonschema==4.23.0` then `python -m unittest discover -s tests -p 'test_phase7_knowledge_contract.py' -v`. Validate the example with `python -m tools.phase7_knowledge_contract.validate`.


## Phase 7 SQLite knowledge repository

Run `python -m unittest discover -s tests -p 'test_phase7_knowledge_repository.py' -v` after installing the pinned `jsonschema==4.23.0` validator.


## Phase 7 rights-aware source adapters

Run `python -m unittest discover -s tests -p 'test_phase7_knowledge_sources.py' -v` after installing `jsonschema==4.23.0`.


## Phase 7 bilingual alignment proposals

Run `python -m unittest discover -s tests -p 'test_phase7_knowledge_alignment.py' -v` after installing `jsonschema==4.23.0`.
