# Phase 6 — Step 6.5 Acceptance Record

**Status:** ACCEPTED — bounded benchmark scope only  
**Accepted main commit:** `78d5ea95065f94833b3026e9d22719af11c5e042`  
**Implementation PR:** [#110](https://github.com/wizekin/USG-Workbench/pull/110)  
**Gold profile:** `USG-INTERPRET-GOLD/0.3.2`  
**Construction rules:** `phase6.predicate-argument-rules.candidate/0.3.0`

## Measured result

All eight language/construction profiles passed independently. Each profile contains 50 fixtures: 20 positive, 20 negative, and 10 ambiguous.

| Profile | Precision | Recall | Participant-role accuracy | Participant-span accuracy | Predicate-span accuracy | Marker accuracy | Negative abstention | Ambiguous abstention | False unique |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| English intransitive | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| English ditransitive | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| English copular | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| English prepositional/location | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| MSA Arabic intransitive | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| MSA Arabic ditransitive | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| MSA Arabic copular | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |
| MSA Arabic prepositional/location | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 0 |

The result is from the deterministic Step 6.5 analyzer executed against all 400 fixtures using the corrected v0.3.2 gold profile. The exact-span tokenizer preserves Arabic combining marks. The v0.3.2 correction separately resolves repeated identical participant names to distinct source mentions.

## CI evidence

All 16 GitHub checks passed on the accepted PR head, including:
- Step 6.5 construction-rule validation and all 400 benchmark fixtures;
- corrected Phase 6 benchmark and evaluator;
- Phase 1–5 regression, compatibility, packaging, SQLite, and Kernel Lab checks.

## Accepted capability boundary

The eight listed construction templates are benchmark-enabled for their measured English/MSA Arabic forms. This does **not** mean unrestricted parsing or general language coverage. The implementation remains a bounded deterministic recognizer. Unseen vocabulary, arbitrary auxiliaries, passive voice, coordination, embedded clauses, general Arabic morphology, and discourse composition remain outside this step. The candidate frame and construction resources remain explicitly candidate-only; the runtime interpreter's measured capability state is recorded separately from resource approval.

The analyzer is not yet wired into the unified Phase 6 service, CLI, API, or Kernel Lab. That integration is reserved for Step 6.13.
