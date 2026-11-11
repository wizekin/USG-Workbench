# USG Open-World Campaign OWC-OW6-43025776433-1

**Status:** PARTIAL
**Tested commit:** `f2b633987bdc6613b523129ecd54461982c570d0`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `39a381307b48d5dead899fdaa9298aa0007423a82fbfbd423cbaeec7f8b79924`
**Created:** 2026-11-11T13:17:02Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 44 |
| unsupported | 945 |
| ambiguous | 94 |
| abstained | 0 |
| partial | 8023 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 2000 |

**Total attempts:** 11106  
**Completed:** 44  
**Unexecuted scenarios:** 0

## Population coverage

| Population | Cases | Attempts | Completed |
|---|---:|---:|---:|
| unconstrained_random | 11000 | 11000 | 0 |
| naturalistic | 0 | 0 | 0 |
| controlled_diagnostic | 106 | 106 | 44 |

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
| OWCL-34BCFFA8B7AB875C | 5 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED |
| OWCL-4B9E5AF44E57E495 | 39 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 43 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 1 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9939FA433BF31E62 | 6 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-834B8148F4FDD43F | 1000 | interpretation_partial|kernel-lab-local-api-cli|no_diagnostic |
| OWCL-1932CBE4B08C96AF | 1000 | interpretation_partial|phase2-structured-semantic-reasoning|no_diagnostic |
| OWCL-8705084148225656 | 1000 | interpretation_partial|phase3-canonical-sqlite-store|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 68 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 125 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 61 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 6 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 349 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 413 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-7CDBB670CED83866 | 1 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-5835C2BB0F0A9CAB | 1000 | interpretation_partial|phase6-candidate-expansion|no_diagnostic |
| OWCL-0904218A1C47FFA3 | 1000 | interpretation_partial|python-native-semantic-models-v06-v14|no_diagnostic |
| OWCL-F4770FF2C9D67F1B | 1000 | interpretation_partial|python-reference-kernel-v04-v05|no_diagnostic |
| OWCL-65100D84201A8A89 | 1000 | interpretation_partial|python-usg-sem-document-adapters-v15|no_diagnostic |
| OWCL-C47AEE338D923D3F | 935 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |
| OWCL-4BDA983C69906A3A | 1 | interpretation_unsupported|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-F9D62B064666630E | 2 | interpretation_unsupported|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-8DFD80FFF5EB7AB1 | 5 | interpretation_unsupported|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-82D0A7844BC9FB0B | 2 | interpretation_unsupported|phase5-bounded-interpreter|syntax:UNSUPPORTED_INTERROGATIVE_FORCE |

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

- `scenario-cases.jsonl` — SHA-256 `fc3d9044e19715fb053a812d949612940ca75e781d761b6f75b6f60c479ff6ad`
- `execution-results.jsonl` — SHA-256 `bc6c9d20fd93520196429de03c7d65f867f6984488b5c09645e6d2ed500b9d2c`
- `score-results.jsonl` — SHA-256 `51bee546bb2a702330a4a9adc991aef5363a67a73e6bdf3f4b565bde66fc29db`
- `generation-manifest.json` — SHA-256 `a4c3ef0a025abdaf0ddbaff355a5928d6704e46856e3400f3f7ff2d5847344e6`
- `coverage-ledger.json` — SHA-256 `990020c3ebcb6e62b51bc0d900c978eedbd3e88fa17cd3bc80259f0d0971e6c7`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
