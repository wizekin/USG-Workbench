# OW-2 — Seed-reproducible randomized scenario generator

**Status:** OW-2 implementation  
**Generator:** usg-open-world-compositional-generator 1.0.0  
**Protocol:** OW-1 scenario schema 1.0.0

## What it generates

The first generator produces synthetic cases in the unconstrained-random population. It combines request styles, topic seeds, context, constraints, and controlled perturbations. Initial scenario families include single requests, multi-step instructions, ambiguous references, contradictory assertions, English/Arabic code-switching, malformed text, context changes, quoted instruction-like content, code-and-explanation requests, format constraints, and unfamiliar-topic questions.

A deterministic portion of the cases remains unclassified before execution. This is intentional: the capability inventory must not become a closed label set that determines what the generator is allowed to ask.

## Actual targets

The target registry is tools/open_world_evaluation/target_profiles.json. It routes cases to three distinct real entry points:
- Phase 4 bounded interpreter v0.1.0.
- Phase 5 bounded interpreter v0.2.0.
- JavaScript Semantic Workbench v0.5.4 browser interface.

The targets have different contracts and runtime modes. The target field is part of every generated case. Use target-matrix mode to emit the same prompt for every selected target; otherwise the generator balances case assignment across selected targets.

## Reproducibility

A caller-supplied seed is normalized to a 256-bit SHA-256 master seed. If no seed is supplied, the generator draws fresh entropy and records it. A per-prompt seed and per-case seed are derived deterministically. The generator records the prompt family, topic, generation trace, mutation operations, target, exact UTF-8 input hash, and resource limits.

For byte-stable scenario records across reruns, supply both a fixed seed and a fixed timestamp. Example:

    python -m tools.open_world_evaluation.generate_scenarios --count 1000 --seed "campaign-seed-2026" --created-at "2026-11-11T11:00:00Z" --output evaluations/ow2-random.jsonl

To compare identical inputs across the three initial targets:

    python -m tools.open_world_evaluation.generate_scenarios --count 100 --seed "campaign-seed-2026" --target-matrix --output evaluations/ow2-matrix.jsonl

Select an individual target with one or more repeated --target options. The registry rejects unknown target IDs and missing entry-point files.

## Outputs and safeguards

The generator writes JSON Lines, one OW-1 scenario per record, and a neighboring manifest containing the seed, target IDs, case IDs, case seeds, input digests, and JSONL SHA-256. It validates every generated case before writing and refuses to overwrite an existing JSONL file or manifest. It does not fetch network sources, import user conversations, execute prompts, start USG, or score responses.

## Known limits

This is an initial compositional generator, not an infinite or unrestricted source of all real-world requests. Its starting meta-grammar and seed topics are finite and intentionally reviewable. Randomized combinations and perturbations increase variety, while unclassified cases expose requests that do not fit the current labels. Later adaptive-discovery stages must add new prompt families and minimized failure-derived cases based on observed results.

OW-2 adds the generation mechanism only. OW-3 must supply isolated execution, and OW-4/OW-5 must validate, score, report, and retain results before a pilot can be claimed.
