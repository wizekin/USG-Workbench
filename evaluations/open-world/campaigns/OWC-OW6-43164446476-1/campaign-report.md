# USG Open-World Campaign OWC-OW6-43164446476-1

**Status:** PARTIAL
**Tested commit:** `790da191588608dbe144114af07432b4bab0b9ac`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `c1a42aecc03631adb1ec68024620bba848c8aa4c4ca6b59af157aba2ff4164da`
**Created:** 2026-11-12T06:26:02Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 111 |
| unsupported | 1281 |
| ambiguous | 387 |
| abstained | 0 |
| partial | 8327 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 1000 |

**Legacy result records (v1.0 attempted field):** 11106  
**Actual execution attempts:** 10106  
**Not-executed target records:** 1000  
**Scenarios with no result record:** 0  
**Scenarios with only not-executed records:** 1000  
**Completed outcomes:** 111  
**Scenarios with no result record (legacy field):** 0

## Population coverage

| Population | Cases | Result records | Actual attempts | Not executed | Completed |
|---|---:|---:|---:|---:|---:|
| unconstrained_random | 11000 | 11000 | 10000 | 1000 | 63 |
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
- Components with an exercised entry point: 10
- Components not registered as open-world targets: 0
- Components with only not-executed attempts: 1
- Unclassified cases retained: 3667

An exercised entry point does not mean every capability or interface in that component was tested.

## Failure and diagnostic clusters

| Cluster | Cases | Proposed signature |
|---|---:|---|
| OWCL-34BCFFA8B7AB875C | 19 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED |
| OWCL-8B877600EA88B01E | 58 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-4B9E5AF44E57E495 | 49 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 111 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 87 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9939FA433BF31E62 | 63 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-5076B13CCA1B3CA4 | 612 | interpretation_partial|js-semantic-workbench-v054|no_diagnostic |
| OWCL-834B8148F4FDD43F | 1000 | interpretation_partial|kernel-lab-local-api-cli|no_diagnostic |
| OWCL-1932CBE4B08C96AF | 1000 | interpretation_partial|phase2-structured-semantic-reasoning|no_diagnostic |
| OWCL-8705084148225656 | 1000 | interpretation_partial|phase3-canonical-sqlite-store|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 61 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 124 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 129 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 2 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 182 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 216 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-44865010FE50BEE5 | 1 | interpretation_partial|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-5835C2BB0F0A9CAB | 1000 | interpretation_partial|phase6-candidate-expansion|no_diagnostic |
| OWCL-0904218A1C47FFA3 | 1000 | interpretation_partial|python-native-semantic-models-v06-v14|no_diagnostic |
| OWCL-F4770FF2C9D67F1B | 1000 | interpretation_partial|python-reference-kernel-v04-v05|no_diagnostic |
| OWCL-65100D84201A8A89 | 1000 | interpretation_partial|python-usg-sem-document-adapters-v15|no_diagnostic |
| OWCL-9ED248EE0107E15D | 325 | interpretation_unsupported|js-semantic-workbench-v054|no_diagnostic |
| OWCL-C47AEE338D923D3F | 942 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |
| OWCL-4BDA983C69906A3A | 1 | interpretation_unsupported|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DDC797F15B3CDCE5 | 1 | interpretation_unsupported|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-F9D62B064666630E | 1 | interpretation_unsupported|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE,syntax:UNSUPPORTED_INTERROGATIVE_FORCE |
| OWCL-8DFD80FFF5EB7AB1 | 9 | interpretation_unsupported|phase5-bounded-interpreter|semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
| OWCL-82D0A7844BC9FB0B | 2 | interpretation_unsupported|phase5-bounded-interpreter|syntax:UNSUPPORTED_INTERROGATIVE_FORCE |

## First blocking stage and downstream diagnostic impact

A first blocker is an observed diagnostic with no other blocked declared ancestor. Parallel first blockers are retained. Dependency-related later blockers are co-occurrences, not proof that an upstream failure caused them.

- Actual attempts analyzed: 10106
- Attempts without target-result payload: 325
- Attempts without observed blocking diagnostics: 8990

| First blocker (dependency DAG) | Cases | Dependency-related later blockers |
|---|---:|---:|
| discourse | 1 | 557 |
| lexical | 1041 | 0 |
| operators | 0 | 461 |
| semantic_composition | 0 | 1112 |
| syntax | 75 | 1039 |

### First-blocking diagnostic codes

| Stage | Diagnostic code | Cases |
|---|---|---:|
| discourse | DISCOURSE_ANTECEDENT_UNRESOLVED | 1 |
| discourse | STAGE_STATUS_PARTIAL | 1 |
| lexical | LEXICAL_AMBIGUOUS_TOKEN | 237 |
| lexical | LEXICAL_UNRESOLVED_TOKEN | 1041 |
| lexical | STAGE_STATUS_AMBIGUOUS | 237 |
| lexical | STAGE_STATUS_PARTIAL | 804 |
| syntax | INCOMPLETE | 61 |
| syntax | STAGE_STATUS_INCOMPLETE | 61 |
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
- **lexical:** `OW-RAND-00000002-4A081351BE`, `OW-RAND-00000013-DD00FEEB62`, `OW-RAND-00000024-F99C554961`, `OW-RAND-00000035-B5F4487B93`, `OW-RAND-00000046-1949E473A3`, `OW-RAND-00000057-003170640F`, `OW-RAND-00000068-003B1E9E1F`, `OW-RAND-00000079-46D88783E3`
- **syntax:** `OW-RAND-00000012-BC6F682635`, `OW-RAND-00000353-9A0DBC4961`, `OW-RAND-00000375-006CB916B1`, `OW-RAND-00000485-1796F4E6E8`, `OW-RAND-00000760-E1E8D471EE`, `OW-RAND-00001068-71E202141D`, `OW-RAND-00001134-624E2A1AEC`, `OW-RAND-00001288-FAECC77E3C`

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

- `scenario-cases.jsonl` — SHA-256 `b6b392092f501c55dcae7a3761563b129f3612643fcb8f40fdd064b7bba0722c`
- `execution-results.jsonl` — SHA-256 `f166d955e5999d3a4518fa3b52631143a12531ab4f78f45d72be253f001dd689`
- `score-results.jsonl` — SHA-256 `f67f76d46c7adb83d2e53f6f6896a7ddc12d4905d1f5564e148732c82e56b586`
- `generation-manifest.json` — SHA-256 `dd94b2805c68ebd25403ce725475f84f63b14043890c1f67d564336096a834b9`
- `coverage-ledger.json` — SHA-256 `8f6b77a7b3bc279d984249a034fc64e3e2a3da3a8e3d39829c009f7b3ece6c3a`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
