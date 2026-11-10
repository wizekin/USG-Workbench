# Phase 2 Step 2.2 — Benchmark corpus and evaluator

**Status:** IMPLEMENTED AS A VERSIONED BENCHMARK CONTRACT AND EVALUATOR  
**Inference implementation:** Not started; this step does not add a rule model or inference engine.  
**Parent roadmap:** [Phase 2 roadmap](PHASE-2-ROADMAP.md)  
**Definitions:** [Step 2.1 semantic reasoning definitions](PHASE-2-STEP-2.1-SEMANTIC-REASONING-DEFINITIONS.md)  
**Benchmark package:** [Semantic Reasoning Benchmark v1.0.0](../benchmarks/semantic-reasoning/v1.0.0/README.md)

## 1. Purpose and boundary

This step turns the Step 2.1 evaluation strategy into an executable benchmark contract before any production rule model or inference executor is designed.

It provides:
- a versioned fixture corpus with stable IDs and explicit positive and negative expectations;
- schemas for fixture definitions and candidate result bundles;
- a pre-inference threshold policy;
- a deterministic evaluator that scores structured candidate outputs;
- focused tests that validate the fixture contract and deliberately inject failure cases;
- a dedicated GitHub Actions workflow.

The evaluator does not perform natural-language interpretation, apply rules, infer facts, or produce candidate conclusions. Test-only reference policies included inside fixtures are not a production rule registry.

## 2. Corpus inventory

The v1.0.0 corpus contains **35 fixtures across 18 categories**:

| Category | What is tested |
|---|---|
| Identity | Explicit shared referents; equal labels and lexical similarity without identity proof |
| Typed references | Wrong reference target types |
| Operator scope | Negation, existential quantification, and scope distinctions |
| Conditionals/connectives | Directed implication, modus ponens, conjunction elimination, and invalid converse |
| Roles/semantic kinds | Ordered AGENT/PATIENT bindings and PROCESS/STATE mismatch |
| Modality/attribution/temporal | Possibility vs actuality, attributed belief, BEFORE direction, and past vs present |
| Contexts | Fictional content does not transfer to WORLD |
| Evidence | Exact alignment vs semantic support, Unicode code-point offsets, irrelevant quotes, and conflicting assessments |
| Inference | Licensed rule examples, missing premises, and unlicensed transitivity |
| World assumptions | Open-world absence, complete closed-domain negation, and incomplete-domain safeguards |
| Corroboration | Repeated evidence from the same source is not independent |
| Ambiguity | Multiple definitions with a shared label |
| Unresolved | Missing antecedents and distinct UNKNOWN/UNRESOLVED/AMBIGUOUS states |
| Conflict | Conflicting assertions without arbitrary winner selection |
| Unsupported | OPAQUE premises and model proposals without registered rules |
| Provenance | Exact rule identity/version and ordered premise/output references |
| Determinism | Stable repeated structured output and meaningful list order |
| Resource interruption | Explicit INCOMPLETE status, interruption diagnostics, and preservation without truncation |

Every fixture declares its stable ID, category and test classes, relevant profile/implementation versions, exact input snapshot, task/query, assumptions and test-only reference policy, expected completion state, expected conclusions, prohibited conclusions, diagnostics, scope bindings, evidence assessments, required provenance, preserved item IDs, and a case-specific rationale. Resource fixtures additionally specify interruption and preservation requirements.

## 3. Candidate output and evaluator

The evaluator consumes a JSON bundle with one structured result per fixture. The result schema requires completion status, conclusion keys, diagnostics, scope bindings, evidence assessments, derivations, preservation IDs, and at least two repeat-run snapshots. Resource cases also require interruption, truncation, input-count, and preserved-count fields.

The evaluator reports each measure separately:

| Metric | Formula / comparison | Frozen gate |
|---|---|---:|
| Precision | True-positive emitted conclusions / all emitted conclusions | **100%** |
| Supported-case recall | Correct expected conclusions / all expected conclusions | **95% minimum** |
| False-inference rate | Unexpected, prohibited, or duplicate emissions / all emitted conclusions | **0%** |
| Scope/binding accuracy | Exact expected scope and binding checks / required checks | **100%** |
| Evidence-assessment accuracy | Exact expected evidence assessments / required checks | **100%** |
| Provenance completeness | Required derivations with all fields and exact required values / required derivations | **100%** |
| Preservation accuracy | Required preserved item IDs present / all required preserved IDs | **100%** |
| Completion-status accuracy | Exact status matches / fixtures | **100%** |
| Diagnostic accuracy | Exact diagnostic-code sets / fixtures | **100%** |
| Determinism accuracy | Fixtures whose reported snapshot and repeated snapshots agree / deterministic fixtures | **100%** |
| Resource behavior accuracy | Resource cases with correct interruption, no truncation, and sufficient preservation / resource cases | **100%** |
| Per-category supported-case recall | Minimum recall among categories with expected positive conclusions | **90% minimum** |

An undefined metric (zero applicable denominator) is reported as `null` and fails its gate. A candidate cannot pass by emitting no conclusions: precision is undefined and recall is zero. The separate false-inference gate remains zero-tolerance.

### Why these thresholds

False inferences are the central semantic safety failure, so the allowed rate is zero. Precision is also fixed at 100%. The 95% aggregate recall and 90% per-category recall permit a small initial coverage gap in a scoped benchmark, while preventing a strong overall score from concealing a neglected supported category. Structural scope, evidence distinctions, provenance, preservation, status, diagnostics, determinism, and resource behavior are exact-contract checks, so their gates are 100%.

These thresholds are frozen before the inference implementation. They may be raised based on new evidence, but not reduced merely because an implementation fails. Any future change requires a new threshold-policy version and a documented rationale.

## 4. Metric semantics and failure handling

- Duplicate conclusion emissions count as false inferences.
- Any emitted conclusion not declared expected is a false inference; prohibited conclusions are also counted separately for visibility.
- Evidence alignment never substitutes for semantic support or corroboration.
- Scope and evidence checks compare stable check IDs and exact structured values.
- Required derivations must include every required field and match expected rule IDs, versions, ordered input references, output references, and status.
- Preservation checks require all declared IDs to remain present. Extra preserved records do not compensate for missing required records.
- Determinism compares the first repeat snapshot with the reported result and compares all repeat snapshots against one another. Only explicitly named runtime metadata fields are ignored; semantic list order is not sorted away.
- A resource interruption must report the declared input count, an interrupted state, no semantic truncation, the required preserved item count, and the expected incomplete completion status.
- Missing, duplicate, or unknown fixture results are structural errors and prevent acceptance.

## 5. Files and execution

- `benchmarks/semantic-reasoning/v1.0.0/fixtures.json`
- `benchmarks/semantic-reasoning/v1.0.0/fixtures.schema.json`
- `benchmarks/semantic-reasoning/v1.0.0/results.schema.json`
- `benchmarks/semantic-reasoning/v1.0.0/thresholds.json`
- `tools/semantic_reasoning_benchmark_v1_0_0/evaluator.py`
- `tests/test_semantic_reasoning_benchmark.py`
- `.github/workflows/phase2-semantic-reasoning-benchmark.yml`

Run the suite from the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
py -m unittest discover -s tests -p "test_semantic_reasoning_benchmark.py" -v
```

Score a future candidate result bundle:

```powershell
py -m tools.semantic_reasoning_benchmark_v1_0_0.evaluator --results path/to/candidate-results.json
```

The dedicated workflow runs Python 3.11, validates schemas, compiles the evaluator, and executes the focused unit tests. It does not upgrade or otherwise change the repository's existing Node.js action runtime.

## 6. Compatibility and current limitations

- USG-SEM/1.0, its JSON Schema, Phase 1 registries/adapters, historical packages, source archives, and implementation baselines remain unchanged.
- No production Rule record, rule registry, inference executor, truth evaluator, entailment engine, ontology learner, or runtime integration is introduced.
- Test-only policy examples are intentionally local to benchmark fixtures. They do not change the meaning of opaque rule references in USG-SEM/1.0.
- Resource budgets are execution constraints only. They do not cap semantic arrays, operand counts, or meaning complexity.
- No human-review gate, automatic truth promotion, confidence collapse, silent coercion, or semantic truncation is introduced.

**Step 2.2 completion condition:** The schemas and evaluator tests pass in CI, the frozen thresholds and corpus are merged, and Phase 1 compatibility checks remain green. The first inference engine remains blocked until this benchmark is available and its thresholds are accepted.
