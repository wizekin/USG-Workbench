# USG Open-World Campaign OWC-OW7-44858520501-1

**Status:** PARTIAL
**Tested commit:** `8c5f0a733c516a80d1b33c73d589984b8c7d571c`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `2fcf4d718310e228531b30e2876c6dd5d35d50db79b64e5a9887dc4308e33928`
**Created:** 2026-11-21T02:57:54Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 50 |
| unsupported | 43 |
| ambiguous | 8 |
| abstained | 0 |
| partial | 205 |
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
**Completed outcomes:** 50  
**Scenarios with no result record (legacy field):** 0

## Population coverage

| Population | Cases | Result records | Actual attempts | Not executed | Completed |
|---|---:|---:|---:|---:|---:|
| unconstrained_random | 220 | 220 | 200 | 20 | 2 |
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
| OWCL-8B877600EA88B01E | 1 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-4B9E5AF44E57E495 | 3 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 2 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 2 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-5076B13CCA1B3CA4 | 10 | interpretation_partial|js-semantic-workbench-v054|no_diagnostic |
| OWCL-834B8148F4FDD43F | 20 | interpretation_partial|kernel-lab-local-api-cli|no_diagnostic |
| OWCL-1932CBE4B08C96AF | 20 | interpretation_partial|phase2-structured-semantic-reasoning|no_diagnostic |
| OWCL-8705084148225656 | 20 | interpretation_partial|phase3-canonical-sqlite-store|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 2 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 3 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 7 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 38 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-44865010FE50BEE5 | 1 | interpretation_partial|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-5835C2BB0F0A9CAB | 20 | interpretation_partial|phase6-candidate-expansion|no_diagnostic |
| OWCL-0904218A1C47FFA3 | 20 | interpretation_partial|python-native-semantic-models-v06-v14|no_diagnostic |
| OWCL-F4770FF2C9D67F1B | 20 | interpretation_partial|python-reference-kernel-v04-v05|no_diagnostic |
| OWCL-65100D84201A8A89 | 20 | interpretation_partial|python-usg-sem-document-adapters-v15|no_diagnostic |
| OWCL-9ED248EE0107E15D | 8 | interpretation_unsupported|js-semantic-workbench-v054|no_diagnostic |
| OWCL-C47AEE338D923D3F | 21 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |
| OWCL-4BDA983C69906A3A | 1 | interpretation_unsupported|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DDC797F15B3CDCE5 | 1 | interpretation_unsupported|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-F9D62B064666630E | 1 | interpretation_unsupported|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-8DFD80FFF5EB7AB1 | 9 | interpretation_unsupported|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-82D0A7844BC9FB0B | 2 | interpretation_unsupported|phase5-bounded-interpreter|syntax:UNSUPPORTED_INTERROGATIVE_FORCE |

## First blocking stage and downstream diagnostic impact

A first blocker is an observed diagnostic with no other blocked declared ancestor. Parallel first blockers are retained. Dependency-related later blockers are co-occurrences, not proof that an upstream failure caused them.

- Actual attempts analyzed: 306
- Attempts without target-result payload: 8
- Attempts without observed blocking diagnostics: 229

| First blocker (dependency DAG) | Cases | Dependency-related later blockers |
|---|---:|---:|
| discourse | 1 | 14 |
| lexical | 61 | 0 |
| operators | 0 | 10 |
| semantic_composition | 0 | 73 |
| syntax | 16 | 59 |

### First-blocking diagnostic codes

| Stage | Diagnostic code | Cases |
|---|---|---:|
| discourse | DISCOURSE_ANTECEDENT_UNRESOLVED | 1 |
| discourse | STAGE_STATUS_PARTIAL | 1 |
| lexical | LEXICAL_AMBIGUOUS_TOKEN | 6 |
| lexical | LEXICAL_UNRESOLVED_TOKEN | 61 |
| lexical | STAGE_STATUS_AMBIGUOUS | 6 |
| lexical | STAGE_STATUS_PARTIAL | 55 |
| syntax | INCOMPLETE | 2 |
| syntax | STAGE_STATUS_INCOMPLETE | 2 |
| syntax | STAGE_STATUS_PARTIAL | 1 |
| syntax | STAGE_STATUS_UNSUPPORTED | 11 |
| syntax | SYNTAX_UNSUPPORTED | 11 |
| syntax | UNSUPPORTED | 1 |
| syntax | UNSUPPORTED_INTERROGATIVE_FORCE | 3 |

### Resource fingerprint groups

- phase4-bounded-interpreter / controlled_diagnostic / en / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase4-bounded-interpreter / unconstrained_random / en / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase5-bounded-interpreter / controlled_diagnostic / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / controlled_diagnostic / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / en-ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f

### Examples

- **discourse:** `OW-DIAG-P5-000058`
- **lexical:** `OW-RAND-00000002-D1565037FC`, `OW-RAND-00000013-09AD6A93B9`, `OW-RAND-00000024-C4CAAEA968`, `OW-RAND-00000035-BB8548480F`, `OW-RAND-00000046-DD37603A5E`, `OW-RAND-00000057-F33BD99842`, `OW-RAND-00000068-304EA5EEDF`, `OW-RAND-00000079-4CBCAE5918`
- **syntax:** `OW-RAND-00000078-2DBFACD0B9`, `OW-DIAG-P4-000003`, `OW-DIAG-P4-000005`, `OW-DIAG-P5-000040`, `OW-DIAG-P5-000041`, `OW-DIAG-P5-000042`, `OW-DIAG-P5-000044`, `OW-DIAG-P5-000045`

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

- `scenario-cases.jsonl` — SHA-256 `f49f52c02e6e56e948a0a76fdb56ca7599d0913de6cd0f3fd21fd8eeb60d896f`
- `execution-results.jsonl` — SHA-256 `a578f357ba9173860c2223b3c47e2c170c28c5e5f504555fb440c06d5d26be54`
- `score-results.jsonl` — SHA-256 `9d7ae912d95041d8fa120759456529ae4a757c99bf9ef5cc74cc24b50e13916d`
- `generation-manifest.json` — SHA-256 `3e52cf73e9b7624cde3136aa1da08ad2e585bf560146c72ea94e5ddca701bdff`
- `adaptive-followup-cases.jsonl` — SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `adaptive-discovery.json` — SHA-256 `68fbff9d5679295e2079f63f8314277c0153e3f2b0ce3b54d1116afc74d9e5c5`
- `coverage-ledger.json` — SHA-256 `7931011d74ddb11a4458fe857bbe9ccdfde466e296f40a7e67f77a34e4e6667f`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
