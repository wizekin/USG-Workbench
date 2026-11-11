# USG Open-World Campaign OWC-OW6-43117034352-1

**Status:** PARTIAL
**Tested commit:** `ebfcd46f85f7795f4d736178aab72270e044782c`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `c23a9db3d928d5deff913e4956656f8d147aa467b5e998865c6d052014ab8487`
**Created:** 2026-11-11T23:21:17Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 48 |
| unsupported | 957 |
| ambiguous | 387 |
| abstained | 0 |
| partial | 7714 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 2000 |

**Legacy result records (v1.0 attempted field):** 11106  
**Actual execution attempts:** 9106  
**Not-executed target records:** 2000  
**Scenarios with no result record:** 0  
**Scenarios with only not-executed records:** 2000  
**Completed outcomes:** 48  
**Scenarios with no result record (legacy field):** 0

## Population coverage

| Population | Cases | Result records | Actual attempts | Not executed | Completed |
|---|---:|---:|---:|---:|---:|
| unconstrained_random | 11000 | 11000 | 9000 | 2000 | 0 |
| naturalistic | 0 | 0 | 0 | 0 | 0 |
| controlled_diagnostic | 106 | 106 | 106 | 0 | 48 |

## Target coverage

| Target | Cases |
|---|---:|
| js-semantic-workbench-v054 | 1000 |
| kernel-lab-local-api-cli | 1000 |
| phase2-structured-semantic-reasoning | 1000 |
| phase3-canonical-sqlite-store | 1000 |
| phase4-bounded-interpreter | 1006 |
| phase5-bounded-interpreter | 1100 |
| phase6-candidate-expansion | 1000 |
| python-native-semantic-models-v06-v14 | 1000 |
| python-reference-kernel-v04-v05 | 1000 |
| python-usg-sem-document-adapters-v15 | 1000 |
| workbench-to-canonical-adapter | 1000 |

## Inventory-backed scope coverage

- Inventory components: 11
- Components with an exercised entry point: 9
- Components not registered as open-world targets: 0
- Components with only not-executed attempts: 2
- Unclassified cases retained: 3667

An exercised entry point does not mean every capability or interface in that component was tested.

## Failure and diagnostic clusters

| Cluster | Cases | Proposed signature |
|---|---:|---|
| OWCL-34BCFFA8B7AB875C | 13 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED |
| OWCL-8B877600EA88B01E | 76 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-4B9E5AF44E57E495 | 37 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 118 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 77 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9939FA433BF31E62 | 66 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-834B8148F4FDD43F | 1000 | interpretation_partial|kernel-lab-local-api-cli|no_diagnostic |
| OWCL-1932CBE4B08C96AF | 1000 | interpretation_partial|phase2-structured-semantic-reasoning|no_diagnostic |
| OWCL-8705084148225656 | 1000 | interpretation_partial|phase3-canonical-sqlite-store|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 60 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 125 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 131 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 202 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 193 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-44865010FE50BEE5 | 1 | interpretation_partial|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-5835C2BB0F0A9CAB | 1000 | interpretation_partial|phase6-candidate-expansion|no_diagnostic |
| OWCL-0904218A1C47FFA3 | 1000 | interpretation_partial|python-native-semantic-models-v06-v14|no_diagnostic |
| OWCL-F4770FF2C9D67F1B | 1000 | interpretation_partial|python-reference-kernel-v04-v05|no_diagnostic |
| OWCL-65100D84201A8A89 | 1000 | interpretation_partial|python-usg-sem-document-adapters-v15|no_diagnostic |
| OWCL-C47AEE338D923D3F | 943 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |
| OWCL-4BDA983C69906A3A | 1 | interpretation_unsupported|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DDC797F15B3CDCE5 | 1 | interpretation_unsupported|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-F9D62B064666630E | 1 | interpretation_unsupported|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-8DFD80FFF5EB7AB1 | 9 | interpretation_unsupported|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-82D0A7844BC9FB0B | 2 | interpretation_unsupported|phase5-bounded-interpreter|syntax:UNSUPPORTED_INTERROGATIVE_FORCE |

## First blocking stage and downstream diagnostic impact

First blocking stage is an observed diagnostic heuristic, not proven root cause. Later blockers are downstream co-occurrences and may be independent.

- Actual attempts analyzed: 9106
- Attempts without target-result payload: 0
- Attempts without observed blocking diagnostics: 8052

| First blocking stage | Cases | Later-stage blocker co-occurrences |
|---|---:|---:|
| discourse | 0 | 567 |
| lexical | 1041 | 0 |
| operators | 0 | 454 |
| semantic_composition | 0 | 1050 |
| syntax | 13 | 1039 |

### Examples

- **lexical:** `OW-RAND-00000002-B50A79F6BF`, `OW-RAND-00000013-3E8AACFA3D`, `OW-RAND-00000024-E4EC9FE818`, `OW-RAND-00000035-3813C004E1`, `OW-RAND-00000046-A0629445E2`, `OW-RAND-00000057-DBDB30D35E`, `OW-RAND-00000068-45EDC9B6C3`, `OW-RAND-00000079-39E7DEAC19`
- **syntax:** `OW-DIAG-P5-000040`, `OW-DIAG-P5-000041`, `OW-DIAG-P5-000042`, `OW-DIAG-P5-000044`, `OW-DIAG-P5-000045`, `OW-DIAG-P5-000046`, `OW-DIAG-P5-000054`, `OW-DIAG-P5-000058`

## Adaptive discovery

- Follow-up cases generated: 0
- Failure clusters compared: 0
- Candidate-new clusters: 0
- Prior reports scanned: 0

Candidate-new means not found in the scanned history, not globally novel. Human review remains required.

## Limitations

- A finite campaign samples a bounded set of cases and cannot prove unrestricted real-world coverage.
- Novel clusters are within-campaign groupings and require historical comparison and human review before being called newly discovered failure families.
- Structural validation does not establish semantic correctness or factual truth.
- Semantic metrics are reported only when independent case-specific oracle adapters are available.
- Naturalistic and controlled-diagnostic populations may be empty; missing populations are reported explicitly and keep campaign status partial.
- The registered browser-only JavaScript target is not executed until a real browser automation adapter is available.
- Process isolation is best-effort containment, not a hardened sandbox for hostile native code.

## Artifacts

- `scenario-cases.jsonl` — SHA-256 `eb2a40b38a496d854154fa0d863c99bf4d34ae06caae96a250409fadd1710fcd`
- `execution-results.jsonl` — SHA-256 `c68bdb9ecf7b026ef50f04cd1b9ded6c7ce93525ce02e100053b1d37b94f8d6b`
- `score-results.jsonl` — SHA-256 `7deaa887c9d0612e6c4b89f5b51c629b159519330569a5aa3f8cfc8709693872`
- `generation-manifest.json` — SHA-256 `ab6b2c045bf45d7558656d6262344ce44bde6193c52366f7981f91024f6c8aa2`
- `coverage-ledger.json` — SHA-256 `99696c6ff26a24a7cda3ac446d1943cb726f5622fbee33959beeee97e9864683`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
