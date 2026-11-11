# OW-8 — Adaptive discovery and historical failure comparison

**Status:** OW-8 implementation  
**Adaptive discovery:** 1.0.0

## Historical comparison

OW-8 compares target-specific failure signatures in a new campaign against every readable previous `campaign-report.json` under the history directory. A signature already present in a prior report is marked `previously_observed`; otherwise it is marked `not_found_in_scanned_history`.

The latter is a *candidate-new* classification, not proof of global novelty. History may be incomplete, reports may be missing, and cluster definitions may evolve. Every new cluster remains unreviewed until human triage.

## Bounded adaptive follow-ups

The first adaptive generator creates follow-up cases only for:
- structurally invalid execution results;
- timeouts;
- worker crashes;
- invalid output.

It does not automatically expand ordinary `unsupported`, `ambiguous`, `partial`, or `not_executed` outcomes. Those may be correct for bounded components or unimplemented interfaces and require review first.

For random-population failures, it generates whitespace/format-only variations: repeated spaces, non-breaking spaces, tabs, line breaks, or leading/trailing whitespace. Non-whitespace characters are not removed or reordered. Every follow-up gets a new case ID, source digest, derived seed, trace to its originating case/cluster, and no semantic oracle. Controlled diagnostic fixtures are never changed.

The default budget is 150 follow-ups per campaign, with at most three variants per failing source case. The CLI hard cap is 500 follow-up cases and six variants per source.

## Usage

    python -m tools.open_world_evaluation.adaptive_discovery \
      --campaign-id OWC-EXAMPLE-CAMPAIGN-001 \
      --cases campaign-cases.jsonl \
      --results campaign-results.jsonl \
      --scores campaign-scores.jsonl \
      --history-root evaluations/open-world/campaigns \
      --output-cases adaptive-followup-cases.jsonl \
      --output-report adaptive-discovery.json \
      --max-cases 150 --variants-per-case 3

The report records scanned campaign IDs, prior cluster matches, candidate-new clusters, example cases, targets, and the number of follow-up cases generated. Both output files are write-once.

## Hidden sample rotation: explicit gap

A hidden-sample vault is not implemented. Public reports and manifests must never contain hidden seeds or supposedly secret cases. A future implementation needs a genuinely private repository/secret-backed seed source and private case storage before claiming a hidden holdout.

## Safety boundaries

Adaptive cases are robustness probes, not semantically equivalent paraphrases or gold-labeled answers. They receive no semantic accuracy score. They do not change USG source, grammar, resources, model packages, thresholds, or previous reports.
