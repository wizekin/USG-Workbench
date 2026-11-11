# OW-4 — Oracle and validator portfolio

**Status:** OW-4 implementation  
**Scorer:** USG Open-World Structural Evaluator 1.0.0  
**Protocol:** OW-1 execution/scenario contracts 1.0.0

## Separation of claims

OW-4 separates three things that must not be confused:

1. **Execution outcome** — whether an adapter completed, reported unsupported/ambiguous/partial, timed out, crashed, or was not executed.
2. **Structural validation** — whether the emitted record is internally valid, preserves its source, has a correct digest, respects schema/span/reference invariants, and uses the declared implementation contract.
3. **Semantic correctness** — whether an interpretation is right according to an independent case-specific oracle.

Only the first two are automatically scored by the OW-4 general-purpose evaluator. It never converts a structurally valid response into a semantic-accuracy claim.

## Deterministic structural validators

### Common checks

- OW-1 scenario and execution-result schema validity.
- Case/attempt identity and target implementation/version/entry-point match.
- Output payload digest verification when inline output is retained.
- Consistency between result outcome and the worker payload's outcome.
- Explicit retention of unsupported, ambiguous, partial, timeout, crash, infrastructure-error, and not-executed cases.

### Phase 4 v0.1.0

- Verify the declared `USG-INTERPRET/0.1.0` pipeline contract.
- Validate the emitted canonical document against the repository's USG-SEM/1.0 JSON Schema.
- Check exact source preservation and SHA-256.
- Check source-span boundaries, quoted/surface text alignment, and source references.
- Check expression root and operand references against the document's expression IDs.

### Phase 5 v0.2.0

- Verify the `USG-INTERPRET/0.2.0` contract and known completion statuses.
- Check exact source preservation and source SHA-256.
- Check the resource-manifest digest and all required stage artifacts.
- Validate token offsets against exact Unicode-code-point source slices.
- Validate syntax candidate role-token references against lexical token IDs.
- Confirm that the Phase 5 result does not promote truth.

Phase 5 remains a separate result contract. The evaluator does not fabricate a USG-SEM/1.0 document for it.

## Independent-oracle portfolio

The scorer records oracle provenance and status, but it does not invent an expected answer:
- No oracle / non-independent oracle → `not_scored_no_independent_oracle`.
- Independent human rubric → `requires_independent_human_rubric_review`; an actual reviewed rubric record must be supplied before metrics can be produced.
- Declared exact/structural/metamorphic/external oracle without a registered case-specific adapter → `oracle_declared_but_no_case_specific_adapter`.
- Semantic metrics are empty unless a separately versioned independent oracle adapter computes them.

The repository's existing Phase 4 and Phase 5 controlled diagnostic benchmarks remain authoritative for their narrow annotated scopes. Their scores must be reported as separate benchmark results, never mixed into random-population semantic accuracy. Phase 5's independent corpus covers three simple-transitive English/MSA Arabic patterns and is not a gold standard for broad natural-language requests.

Metamorphic, external-reference, and rubric-based oracles are extension points, not claims that such independent datasets or reviewers have already been connected.

## Usage

Generate cases and execute them first. Then score the result file:

    python -m tools.open_world_evaluation.score_cases \
      --cases evaluations/campaign-cases.jsonl \
      --results evaluations/campaign-results.jsonl \
      --scores evaluations/campaign-scores.jsonl \
      --summary evaluations/campaign-score-summary.json

The scorer refuses to overwrite earlier output files. It preserves per-case scores and per-population/per-target outcome counts. A case with no result remains counted in `unexecuted_scenario_count`.

## OW-4 exit boundary

OW-4 supplies deterministic, interface-specific structural checks and an oracle-aware score contract. It does not claim that arbitrary generated prompts have semantic gold. The next stage, OW-5, will add append-only campaign reports, manifests, failure-family summaries, and durable storage; OW-6 will run the first wider pilot and publish the actual observed coverage and limitations.
