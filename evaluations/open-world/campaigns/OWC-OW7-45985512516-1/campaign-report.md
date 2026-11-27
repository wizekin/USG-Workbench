# USG Open-World Campaign OWC-OW7-45985512516-1

**Status:** PARTIAL
**Tested commit:** `af9cf4c804317b57f4463f15b463f62b0c6b5423`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `5df1bf2f477b4adbf359039292498337c8fa6fd8124b827f704fcb49d7282980`
**Created:** 2026-11-27T10:52:20Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 49 |
| unsupported | 42 |
| ambiguous | 9 |
| abstained | 0 |
| partial | 206 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 20 |

**Legacy result records (v1.0 attempted field):** 326  
**Actual execution attempts:** 306  
**Not-executed target records:** 20  
**Scenarios with no result record:** 0  
**Scenarios with only not-executed records:** 20  
**Completed outcomes:** 49  
**Scenarios with no result record (legacy field):** 0

## Population coverage

| Population | Cases | Result records | Actual attempts | Not executed | Completed |
|---|---:|---:|---:|---:|---:|
| unconstrained_random | 220 | 220 | 200 | 20 | 1 |
| naturalistic | 0 | 0 | 0 | 0 | 0 |
| controlled_diagnostic | 106 | 106 | 106 | 0 | 48 |

## Target coverage

| Target | Cases |
|---|---:|
| js-semantic-workbench-v054 | 20 |
| kernel-lab-local-api-cli | 20 |
| phase2-structured-semantic-reasoning | 20 |
| phase3-canonical-sqlite-store | 20 |
| phase4-bounded-interpreter | 26 |
| phase5-bounded-interpreter | 120 |
| phase6-candidate-expansion | 20 |
| python-native-semantic-models-v06-v14 | 20 |
| python-reference-kernel-v04-v05 | 20 |
| python-usg-sem-document-adapters-v15 | 20 |
| workbench-to-canonical-adapter | 20 |

## Inventory-backed scope coverage

- Inventory components: 11
- Components with an exercised entry point: 10
- Components not registered as open-world targets: 0
- Components with only not-executed attempts: 1
- Unclassified cases retained: 74

An exercised entry point does not mean every capability or interface in that component was tested.

## Failure and diagnostic clusters

| Cluster | Cases | Proposed signature |
|---|---:|---|
| OWCL-8B877600EA88B01E | 2 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 3 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 2 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9939FA433BF31E62 | 2 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-5076B13CCA1B3CA4 | 12 | interpretation_partial|js-semantic-workbench-v054|no_diagnostic |
| OWCL-834B8148F4FDD43F | 20 | interpretation_partial|kernel-lab-local-api-cli|no_diagnostic |
| OWCL-1932CBE4B08C96AF | 20 | interpretation_partial|phase2-structured-semantic-reasoning|no_diagnostic |
| OWCL-8705084148225656 | 20 | interpretation_partial|phase3-canonical-sqlite-store|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 2 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 3 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 7 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 37 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-44865010FE50BEE5 | 1 | interpretation_partial|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-5835C2BB0F0A9CAB | 20 | interpretation_partial|phase6-candidate-expansion|no_diagnostic |
| OWCL-0904218A1C47FFA3 | 20 | interpretation_partial|python-native-semantic-models-v06-v14|no_diagnostic |
| OWCL-F4770FF2C9D67F1B | 20 | interpretation_partial|python-reference-kernel-v04-v05|no_diagnostic |
| OWCL-65100D84201A8A89 | 20 | interpretation_partial|python-usg-sem-document-adapters-v15|no_diagnostic |
| OWCL-9ED248EE0107E15D | 7 | interpretation_unsupported|js-semantic-workbench-v054|no_diagnostic |
| OWCL-C47AEE338D923D3F | 21 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |
| OWCL-4BDA983C69906A3A | 1 | interpretation_unsupported|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DDC797F15B3CDCE5 | 1 | interpretation_unsupported|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-F9D62B064666630E | 1 | interpretation_unsupported|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-8DFD80FFF5EB7AB1 | 9 | interpretation_unsupported|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-82D0A7844BC9FB0B | 2 | interpretation_unsupported|phase5-bounded-interpreter|syntax:UNSUPPORTED_INTERROGATIVE_FORCE |

## First blocking stage and downstream diagnostic impact

A first blocker is an observed diagnostic with no other blocked declared ancestor. Parallel first blockers are retained. Dependency-related later blockers are co-occurrences, not proof that an upstream failure caused them.

- Actual attempts analyzed: 306
- Attempts without target-result payload: 7
- Attempts without observed blocking diagnostics: 229

| First blocker (dependency DAG) | Cases | Dependency-related later blockers |
|---|---:|---:|
| discourse | 1 | 18 |
| lexical | 61 | 0 |
| operators | 0 | 7 |
| semantic_composition | 0 | 73 |
| syntax | 16 | 59 |

### First-blocking diagnostic codes

| Stage | Diagnostic code | Cases |
|---|---|---:|
| discourse | DISCOURSE_ANTECEDENT_UNRESOLVED | 1 |
| discourse | STAGE_STATUS_PARTIAL | 1 |
| lexical | LEXICAL_AMBIGUOUS_TOKEN | 5 |
| lexical | LEXICAL_UNRESOLVED_TOKEN | 61 |
| lexical | STAGE_STATUS_AMBIGUOUS | 5 |
| lexical | STAGE_STATUS_PARTIAL | 56 |
| syntax | INCOMPLETE | 2 |
| syntax | STAGE_STATUS_INCOMPLETE | 2 |
| syntax | STAGE_STATUS_PARTIAL | 1 |
| syntax | STAGE_STATUS_UNSUPPORTED | 11 |
| syntax | SYNTAX_UNSUPPORTED | 11 |
| syntax | UNSUPPORTED | 1 |
| syntax | UNSUPPORTED_INTERROGATIVE_FORCE | 3 |

### Resource fingerprint groups

- phase4-bounded-interpreter / controlled_diagnostic / en / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase4-bounded-interpreter / unconstrained_random / en-ar / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase5-bounded-interpreter / controlled_diagnostic / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / controlled_diagnostic / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / en-ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f

### Examples

- **discourse:** `OW-DIAG-P5-000058`
- **lexical:** `OW-RAND-00000002-21D20D76C5`, `OW-RAND-00000013-66688A08CF`, `OW-RAND-00000024-09BA670802`, `OW-RAND-00000035-81811A4597`, `OW-RAND-00000046-E52FBEE810`, `OW-RAND-00000057-2DEB00E5C2`, `OW-RAND-00000068-01FDE2E1CA`, `OW-RAND-00000079-58C1C9FE09`
- **syntax:** `OW-RAND-00000045-5585289FB1`, `OW-DIAG-P4-000003`, `OW-DIAG-P4-000005`, `OW-DIAG-P5-000040`, `OW-DIAG-P5-000041`, `OW-DIAG-P5-000042`, `OW-DIAG-P5-000044`, `OW-DIAG-P5-000045`

## Adaptive discovery

- Follow-up cases generated: 0
- Failure clusters compared: 0
- Candidate-new clusters: 0
- Prior reports scanned: 3

Candidate-new means not found in the scanned history, not globally novel. Human review remains required.

## Limitations

- A finite campaign samples a bounded set of cases and cannot prove unrestricted real-world coverage.
- Novel clusters are within-campaign groupings and require historical comparison and human review before being called newly discovered failure families.
- Structural validation does not establish semantic correctness or factual truth.
- Semantic metrics are reported only when independent case-specific oracle adapters are available.
- Naturalistic and controlled-diagnostic populations may be empty; missing populations are reported explicitly and keep campaign status partial.
- The JavaScript Workbench target is English-only and uses a deterministic local rule fallback. When the Playwright adapter runs, its evidence establishes UI execution and structured output only, not semantic correctness.
- Process isolation is best-effort containment, not a hardened sandbox for hostile native code.

## Artifacts

- `scenario-cases.jsonl` — SHA-256 `1f2e60df5df5f1262c20377d4d89d54f8656399baf728e9470674bb02ff64b60`
- `execution-results.jsonl` — SHA-256 `9898504864479b21eab3d3bb74faaaf93bf45a634121e6cce3b9132e91ebf8ea`
- `score-results.jsonl` — SHA-256 `d2a6cbe73c53506aa9a15e6b8d888878aca2264839fdc690a2d36d1054736acf`
- `generation-manifest.json` — SHA-256 `2efa4b472304179a7d6a78166a93f7acd8d5fb6ddcfb417df58fbee8dfe804a2`
- `adaptive-followup-cases.jsonl` — SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `adaptive-discovery.json` — SHA-256 `f922ddb7e642a8e55dd19f8f23fe9f4ce73dc0d0a0645a891ee1e3e6d30f0961`
- `coverage-ledger.json` — SHA-256 `a6b1b824461a1d4d95beda04405557cc4bdbd8c5ef398bd5b7d0cc91d57b5b1f`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
