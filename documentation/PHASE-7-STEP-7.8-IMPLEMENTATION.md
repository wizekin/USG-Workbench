# Phase 7 Step 7.8 — Read-Only Integration with Reasoning and Interpretation

**Status:** implementation submitted for exact-head CI; acceptance is pending.  
**Adapter:** `usg-knowledge-read-adapter/0.1.0`

## Deliverables

- A read-only adapter over the existing Phase 7 SQLite knowledge repository.
- Explicit consumer profiles for Phase 2, Phase 4, Phase 5, and Phase 6.
- Phase 2/4/5 default visibility restricted to `ACCEPTED` and `VALIDATED_FOR_PROFILE` records.
- An explicit opt-in to include candidate/unresolved evidence for Phase 2/4/5 diagnostics without promoting it.
- A Phase 6 adapter that exposes only `CANDIDATE` and `UNRESOLVED` records and always labels the result candidate-only.
- Snapshot/version metadata and explicit no-mutation/no-promotion flags.

## Safety boundary

The adapter reads immutable repository snapshots and delegates candidate ranking to the Step 7.7 retrieval policy. It does not modify the repository, lexical resources, Phase 2 rule registry, Phase 4/5 interpreter stages, Phase 6 output, or canonical USG-SEM documents. It does not inject knowledge into a running interpretation pipeline or change existing inference behavior. Existing services can call the adapter as an optional read-only evidence provider; consuming services remain responsible for their own rule/evidence gates.

Phase 2/4/5 cannot see candidate or unresolved records by default. A caller must explicitly request candidate evidence, and the adapter still marks promotion as forbidden. Phase 6 results are candidate-only by construction.

## Acceptance tests

`python -m unittest discover -s tests -p 'test_phase7_knowledge_integration.py' -v`

Tests cover consumer state boundaries, explicit candidate opt-in, Phase 6 candidate-only visibility, repository immutability, and rejection of unknown consumers.

## Limitations

This is a stable read-only adapter contract, not a completed wiring of every existing Phase 2/4/5 runtime route or Kernel Lab panel. No runtime automatically consumes or acts on retrieved knowledge yet. Automatic rule changes, lexical resource updates, semantic promotion, and canonical assertion projection remain out of scope.
