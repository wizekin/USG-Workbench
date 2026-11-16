# USG Open-World Campaign OWC-OW7-43807165809-1

**Status:** PARTIAL
**Tested commit:** `8e3f1308882b2e8ce581350746d9ee76fca31216`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `c5f9be52212c561bcf2882302f5fc35c42af73957756c2c15d27e58c634a28b3`
**Created:** 2026-11-16T05:01:14Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 50 |
| unsupported | 140 |
| ambiguous | 56 |
| abstained | 0 |
| partial | 860 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 100 |

**Legacy result records (v1.0 attempted field):** 1206  
**Actual execution attempts:** 1106  
**Not-executed target records:** 100  
**Scenarios with no result record:** 0  
**Scenarios with only not-executed records:** 100  
**Completed outcomes:** 50  
**Scenarios with no result record (legacy field):** 0

## Population coverage

| Population | Cases | Result records | Actual attempts | Not executed | Completed |
|---|---:|---:|---:|---:|---:|
| unconstrained_random | 1100 | 1100 | 1000 | 100 | 2 |
| naturalistic | 0 | 0 | 0 | 0 | 0 |
| controlled_diagnostic | 106 | 106 | 106 | 0 | 48 |

## Target coverage

| Target | Cases |
|---|---:|
| js-semantic-workbench-v054 | 100 |
| kernel-lab-local-api-cli | 100 |
| phase2-structured-semantic-reasoning | 100 |
| phase3-canonical-sqlite-store | 100 |
| phase4-bounded-interpreter | 106 |
| phase5-bounded-interpreter | 200 |
| phase6-candidate-expansion | 100 |
| python-native-semantic-models-v06-v14 | 100 |
| python-reference-kernel-v04-v05 | 100 |
| python-usg-sem-document-adapters-v15 | 100 |
| workbench-to-canonical-adapter | 100 |

## Inventory-backed scope coverage

- Inventory components: 11
- Components with an exercised entry point: 10
- Components not registered as open-world targets: 0
- Components with only not-executed attempts: 1
- Unclassified cases retained: 367

An exercised entry point does not mean every capability or interface in that component was tested.

## Failure and diagnostic clusters

| Cluster | Cases | Proposed signature |
|---|---:|---|
| OWCL-34BCFFA8B7AB875C | 5 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED |
| OWCL-8B877600EA88B01E | 9 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-4B9E5AF44E57E495 | 7 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 13 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 12 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9939FA433BF31E62 | 10 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-5076B13CCA1B3CA4 | 66 | interpretation_partial|js-semantic-workbench-v054|no_diagnostic |
| OWCL-834B8148F4FDD43F | 100 | interpretation_partial|kernel-lab-local-api-cli|no_diagnostic |
| OWCL-1932CBE4B08C96AF | 100 | interpretation_partial|phase2-structured-semantic-reasoning|no_diagnostic |
| OWCL-8705084148225656 | 100 | interpretation_partial|phase3-canonical-sqlite-store|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 9 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 6 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 14 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 16 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 46 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-44865010FE50BEE5 | 1 | interpretation_partial|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-5835C2BB0F0A9CAB | 100 | interpretation_partial|phase6-candidate-expansion|no_diagnostic |
| OWCL-0904218A1C47FFA3 | 100 | interpretation_partial|python-native-semantic-models-v06-v14|no_diagnostic |
| OWCL-F4770FF2C9D67F1B | 100 | interpretation_partial|python-reference-kernel-v04-v05|no_diagnostic |
| OWCL-65100D84201A8A89 | 100 | interpretation_partial|python-usg-sem-document-adapters-v15|no_diagnostic |
| OWCL-9ED248EE0107E15D | 32 | interpretation_unsupported|js-semantic-workbench-v054|no_diagnostic |
| OWCL-C47AEE338D923D3F | 94 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |
| OWCL-4BDA983C69906A3A | 1 | interpretation_unsupported|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DDC797F15B3CDCE5 | 1 | interpretation_unsupported|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-F9D62B064666630E | 1 | interpretation_unsupported|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-8DFD80FFF5EB7AB1 | 9 | interpretation_unsupported|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-82D0A7844BC9FB0B | 2 | interpretation_unsupported|phase5-bounded-interpreter|syntax:UNSUPPORTED_INTERROGATIVE_FORCE |

## First blocking stage and downstream diagnostic impact

A first blocker is an observed diagnostic with no other blocked declared ancestor. Parallel first blockers are retained. Dependency-related later blockers are co-occurrences, not proof that an upstream failure caused them.

- Actual attempts analyzed: 1106
- Attempts without target-result payload: 32
- Attempts without observed blocking diagnostics: 942

| First blocker (dependency DAG) | Cases | Dependency-related later blockers |
|---|---:|---:|
| discourse | 1 | 64 |
| lexical | 141 | 0 |
| operators | 0 | 46 |
| semantic_composition | 0 | 160 |
| syntax | 23 | 139 |

### First-blocking diagnostic codes

| Stage | Diagnostic code | Cases |
|---|---|---:|
| discourse | DISCOURSE_ANTECEDENT_UNRESOLVED | 1 |
| discourse | STAGE_STATUS_PARTIAL | 1 |
| lexical | LEXICAL_AMBIGUOUS_TOKEN | 34 |
| lexical | LEXICAL_UNRESOLVED_TOKEN | 141 |
| lexical | STAGE_STATUS_AMBIGUOUS | 34 |
| lexical | STAGE_STATUS_PARTIAL | 107 |
| syntax | INCOMPLETE | 9 |
| syntax | STAGE_STATUS_INCOMPLETE | 9 |
| syntax | STAGE_STATUS_PARTIAL | 1 |
| syntax | STAGE_STATUS_UNSUPPORTED | 11 |
| syntax | SYNTAX_UNSUPPORTED | 11 |
| syntax | UNSUPPORTED | 1 |
| syntax | UNSUPPORTED_INTERROGATIVE_FORCE | 3 |

### Resource fingerprint groups

- phase4-bounded-interpreter / controlled_diagnostic / en / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase4-bounded-interpreter / unconstrained_random / ar / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase4-bounded-interpreter / unconstrained_random / en / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase4-bounded-interpreter / unconstrained_random / en-ar / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase5-bounded-interpreter / controlled_diagnostic / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / controlled_diagnostic / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / unconstrained_random / en-ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f

### Examples

- **discourse:** `OW-DIAG-P5-000058`
- **lexical:** `OW-RAND-00000002-5E0AD17478`, `OW-RAND-00000013-403145A603`, `OW-RAND-00000024-F12A4EA9B8`, `OW-RAND-00000035-C2DEE032F6`, `OW-RAND-00000046-8F886C6511`, `OW-RAND-00000057-F41C5B223D`, `OW-RAND-00000068-1FF268FF9C`, `OW-RAND-00000079-72468847A6`
- **syntax:** `OW-RAND-00000034-8D04A42295`, `OW-RAND-00000375-25272CC2EF`, `OW-RAND-00000496-683A07C9B9`, `OW-RAND-00000595-6554B230A9`, `OW-RAND-00000837-F742876B25`, `OW-RAND-00000859-1DBA336288`, `OW-RAND-00000914-F540BBA99A`, `OW-RAND-00001024-9F9761192C`

## Adaptive discovery

- Follow-up cases generated: 0
- Failure clusters compared: 0
- Candidate-new clusters: 0
- Prior reports scanned: 1

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

- `scenario-cases.jsonl` — SHA-256 `e5cfc562e1425a02b4168cc2a18c872274c62dfd90de80dc4e20130cbb596b37`
- `execution-results.jsonl` — SHA-256 `8d1d4e65e166649e55fc581a85232811c070801a67b2cfa4bb1acf98d3632164`
- `score-results.jsonl` — SHA-256 `dff7a25b8d19e953508ebc90cefa403e341d80d9cf4c1d3699c660bd305063ab`
- `generation-manifest.json` — SHA-256 `77b1e330d3fe9a02e714d6c0e69e4eef1a69a6cd1057621e942b2a91f2daf7d5`
- `adaptive-followup-cases.jsonl` — SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `adaptive-discovery.json` — SHA-256 `9430a01230c5f0b52beeee9f3fe1b5212196f1759e10277a95c0bb74663c3896`
- `coverage-ledger.json` — SHA-256 `6b6daa4fe51589ad7f3fa7d82bdc01659cec42f6e72bb4919894449f20e6c029`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
