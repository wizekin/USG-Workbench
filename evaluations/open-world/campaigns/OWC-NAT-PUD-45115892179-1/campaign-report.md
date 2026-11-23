# USG Open-World Campaign OWC-NAT-PUD-45115892179-1

**Status:** PARTIAL
**Tested commit:** `8c5f0a733c516a80d1b33c73d589984b8c7d571c`
**Protocol / generator / evaluator:** 1.0.0 / 0.1.0 / 1.0.0
**Master seed:** `3c0ff9b37877675321787efb205b3a08e5dabeaa548cef1afa8cbba9a548fe35`
**Created:** 2026-11-23T05:10:52Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 4 |
| unsupported | 51 |
| ambiguous | 0 |
| abstained | 0 |
| partial | 245 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 0 |

**Legacy result records (v1.0 attempted field):** 300  
**Actual execution attempts:** 300  
**Not-executed target records:** 0  
**Scenarios with no result record:** 0  
**Scenarios with only not-executed records:** 0  
**Completed outcomes:** 4  
**Scenarios with no result record (legacy field):** 0

## Population coverage

| Population | Cases | Result records | Actual attempts | Not executed | Completed |
|---|---:|---:|---:|---:|---:|
| unconstrained_random | 0 | 0 | 0 | 0 | 0 |
| naturalistic | 300 | 300 | 300 | 0 | 4 |
| controlled_diagnostic | 0 | 0 | 0 | 0 | 0 |

## Target coverage

| Target | Cases |
|---|---:|
| js-semantic-workbench-v054 | 100 |
| phase4-bounded-interpreter | 100 |
| phase5-bounded-interpreter | 100 |

## Inventory-backed scope coverage

- Inventory components: 11
- Components with an exercised entry point: 3
- Components not registered as open-world targets: 0
- Components with only not-executed attempts: 0
- Unclassified cases retained: 300

An exercised entry point does not mean every capability or interface in that component was tested.

## Failure and diagnostic clusters

| Cluster | Cases | Proposed signature |
|---|---:|---|
| OWCL-5076B13CCA1B3CA4 | 46 | interpretation_partial|js-semantic-workbench-v054|no_diagnostic |
| OWCL-3C5D8709F73A92B7 | 99 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 4 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 16 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-5650588D074E1112 | 10 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 70 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9ED248EE0107E15D | 50 | interpretation_unsupported|js-semantic-workbench-v054|no_diagnostic |
| OWCL-C47AEE338D923D3F | 1 | interpretation_unsupported|phase4-bounded-interpreter|no_diagnostic |

## First blocking stage and downstream diagnostic impact

A first blocker is an observed diagnostic with no other blocked declared ancestor. Parallel first blockers are retained. Dependency-related later blockers are co-occurrences, not proof that an upstream failure caused them.

- Actual attempts analyzed: 300
- Attempts without target-result payload: 50
- Attempts without observed blocking diagnostics: 101

| First blocker (dependency DAG) | Cases | Dependency-related later blockers |
|---|---:|---:|
| discourse | 0 | 20 |
| lexical | 100 | 0 |
| operators | 0 | 14 |
| semantic_composition | 0 | 199 |
| syntax | 99 | 100 |

### First-blocking diagnostic codes

| Stage | Diagnostic code | Cases |
|---|---|---:|
| lexical | LEXICAL_UNRESOLVED_TOKEN | 100 |
| lexical | STAGE_STATUS_PARTIAL | 100 |
| syntax | INCOMPLETE | 99 |
| syntax | STAGE_STATUS_INCOMPLETE | 99 |

### Resource fingerprint groups

- phase4-bounded-interpreter / naturalistic / ar / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase4-bounded-interpreter / naturalistic / en / usg-interpretation/0.1.0: stage-refs:c0dc48196f0e57ba3d4ef0d150250db96bf4815102d039dfbdd6bf93d9c52a2a
- phase5-bounded-interpreter / naturalistic / ar / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f
- phase5-bounded-interpreter / naturalistic / en / phase5-interpretation-integration/0.3.0: manifest:76e83880e7932135390553a1becd26b532fc569893882dda068e6f09076aaf3f

### Examples

- **lexical:** `OW-NAT-PUD-EN-36E190990EDA`, `OW-NAT-PUD-EN-36261ADF8775`, `OW-NAT-PUD-EN-4E18A1351ECC`, `OW-NAT-PUD-EN-737B2EF35BCB`, `OW-NAT-PUD-EN-B8421ACCCA4D`, `OW-NAT-PUD-EN-DAA8F9887823`, `OW-NAT-PUD-EN-721DFAE8593C`, `OW-NAT-PUD-EN-8E291108E994`
- **syntax:** `OW-NAT-PUD-EN-C6392CCFE970`, `OW-NAT-PUD-EN-5B4927D02ADE`, `OW-NAT-PUD-EN-052C65529111`, `OW-NAT-PUD-EN-9123779F81EF`, `OW-NAT-PUD-EN-E7BBE13ECB82`, `OW-NAT-PUD-EN-3516123D7E17`, `OW-NAT-PUD-EN-9236EF8EC641`, `OW-NAT-PUD-EN-1F5385604F61`

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
- The JavaScript Workbench target is English-only and uses a deterministic local rule fallback. When the Playwright adapter runs, its evidence establishes UI execution and structured output only, not semantic correctness.
- Process isolation is best-effort containment, not a hardened sandbox for hostile native code.

## Artifacts

- `scenario-cases.jsonl` — SHA-256 `1cd3c5d34dba63201d92fe5670440c7e265840be56d0ae1acd118529210f15ef`
- `execution-results.jsonl` — SHA-256 `4422bc365de29243199bf4f3cd9d32392bfa3a875fc17e92186edbb2c2f52e6e`
- `score-results.jsonl` — SHA-256 `77ba58e438e999dd4b0b8f098b1c47592167c5d479482aba1195b6d62deadaca`
- `generation-manifest.json` — SHA-256 `98b1f4fd21eff05d27d78881e874ee195100cb389b3e2e84c5cf68d9ee5aa078`
- `coverage-ledger.json` — SHA-256 `a587e698f1fc6b995abd669c620f7a77c412c30bb888f976570f9992c25f0d0f`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
