# Phase 6 Bounded Automatic Acceptance Record

**Decision:** ACCEPTED for the registered bounded synthetic profile set.  
**Date:** 12 November 2026  
**Interpretation contract:** `USG-INTERPRET/0.3.0`  
**Canonical interchange:** `USG-SEM/1.0`, unchanged  
**Acceptance implementation:** [PR #204 — Phase 6 automatic bilingual acceptance factory](https://github.com/wizekin/USG-Workbench/pull/204)

## Accepted scope

The automatic factory accepted Steps 6.7–6.14 for the explicitly registered English and Modern Standard Arabic profiles:

| Step | Accepted bounded scope |
|---|---|
| 6.7 | Intra-clause coordinated agents sharing one predicate and patient |
| 6.8 | Registered causal attachment and ambiguous causal/temporal attachment alternatives |
| 6.9 | Registered passive-question profile |
| 6.10 | Modality plus negation, including unresolved nested-scope alternatives |
| 6.11 | Preservation of single- and multiple-antecedent candidates without identity merging |
| 6.12 | Lossless `OPAQUE_PRESERVATION_ONLY` into the unchanged canonical schema |
| 6.13 | Integrated bilingual API and CLI, SQLite persistence, deterministic replay, editable package installation, and Kernel Lab regression |
| 6.14 | Integrated acceptance report and protected regression suite; accepted because all prior bounded gates passed |

Step 6.6's separate 500-case / 10-profile graph-first nominal benchmark also passed its previously defined bounded synthetic gate. Its results are not pooled with this acceptance benchmark.

## Reproducible benchmark evidence

- Benchmark: `usg-phase6-automatic-acceptance/1.0.0`
- Generated cases: **500**
- Bilingual profiles: **10** (five construction families × English and MSA Arabic)
- Per profile: **20 positive, 20 negative, and 10 ambiguous cases**
- Corpus SHA-256: `bb58f7857ab3f9bc5475ed91ce437d96cb0adc9d2eda3ac9a8db2a84416d5fcf`
- License: `CC0-1.0`
- End-to-end evaluator: the actual `POST /v3/phase6/interpret` operation
- Recorded factory execution: 44,399.505 ms on the GitHub-hosted runner; this is a CI observation, not a production latency guarantee.

All ten profiles passed every required factory gate:

| Metric | Result in each of the 10 profiles |
|---|---:|
| Construction precision | 100% |
| Construction recall | 100% |
| Exact role-span accuracy | 100% |
| Negative abstention | 100% |
| Ambiguity preservation | 100% |
| False unique or invalid outcomes | 0 |

The report also verified the exact source snapshot and digest, emitted span alignment, and the versioned report schema. The final status was `ACCEPTED`.

Validation workflow on the final PR head: [GitHub Actions run 43200506859](https://github.com/wizekin/USG-Workbench/actions/runs/43200506859), which tested implementation head `0d2cc5676445cf294aa4f52c1145d4a27938ba01`. All 26 repository PR checks passed on this exact head. The report and generated corpus are attached as the `phase6-automatic-acceptance-v1.0` workflow artifact.

## Step 6.12 projection boundary

The accepted Step 6.12 scope is strictly **OPAQUE preservation**. The report checked all 500 generated candidate results:

- schema-valid OPAQUE document;
- full candidate graph payload preserved;
- exact source text and SHA-256 digest preserved;
- zero canonical assertions emitted.

The measured preservation rate was **500/500 (100%)**.

`semantic_assertion_projection_accepted` remains **false**. This record does not accept mapping candidate graphs into canonical semantic assertions.

## Step 6.13 integration evidence

The report marked all eight bilingual checks successful:

- English and Arabic integrated API calls;
- English and Arabic executable `phase6-interpret` CLI calls;
- English and Arabic SQLite persistence;
- English and Arabic deterministic replay.

The same workflow passed the editable package install and CLI help checks, the Kernel Lab tests, the integrated interpreter regressions, the Phase 6 provider regressions, and protected Phase 1–5 paths.

## Capability and evidence limits

This is a controlled, graph-first synthetic conformance acceptance. The reference graph is composed before realization of the new text; the generator does not use human annotations, model-generated labels, Phase 6 runtime predictions, Phase 6 development fixtures, the active candidate lexicon, or external corpora to assign the new references. The frozen Phase 5 corpus supplies the seed lexical/role inventory. The result is therefore reproducible synthetic evidence, not an independently adjudicated naturalistic gold corpus.

All Phase 6 interpretation outputs remain **candidate-only**. No candidate is promoted into canonical knowledge by this acceptance process.

The following remain outside the accepted bounded profile set and require separate work/evidence:

- other productive coordination patterns and general shared-argument propagation;
- broad complement, relative-clause, conditional, temporal, and argument-gap attachment;
- general active/passive, imperative, command, and request interpretation;
- wider quantifier and cross-construction scope families;
- unique discourse identity resolution;
- semantic assertion projection into canonical `USG-SEM/1.0`;
- naturalistic semantic accuracy across unconstrained English and Arabic.

Accordingly, the bounded automatic Phase 6 exit is accepted; unrestricted language understanding, naturalistic semantic accuracy, and the broader research objective are not claimed.
