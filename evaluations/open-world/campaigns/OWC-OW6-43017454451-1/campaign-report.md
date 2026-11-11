# USG Open-World Campaign OWC-OW6-43017454451-1

**Status:** PARTIAL
**Tested commit:** `254fecb325c66f617c99c60fb10c599a99c79f3e`
**Protocol / generator / evaluator:** 1.0.0 / 1.0.1 / 1.0.0
**Master seed:** `5497342fea84125d8b2ea1372d5654b32115c870d7bba4c4f350ec7ad87b8ba9`
**Created:** 2026-11-11T12:10:47Z

## Execution outcomes

| Outcome | Attempts |
|---|---:|
| completed | 44 |
| unsupported | 945 |
| ambiguous | 91 |
| abstained | 0 |
| partial | 1026 |
| invalid_output | 0 |
| timeout | 0 |
| crashed | 0 |
| infrastructure_error | 0 |
| not_executed | 1000 |

**Total attempts:** 3106  
**Completed:** 44  
**Unexecuted scenarios:** 0

## Population coverage

| Population | Cases | Attempts | Completed |
|---|---:|---:|---:|
| unconstrained_random | 3000 | 3000 | 0 |
| naturalistic | 0 | 0 | 0 |
| controlled_diagnostic | 106 | 106 | 44 |

## Target coverage

| Target | Cases |
|---|---:|
| js-semantic-workbench-v054 | 1000 |
| phase4-bounded-interpreter | 1006 |
| phase5-bounded-interpreter | 1100 |

## Inventory-backed scope coverage

- Inventory components: 11
- Components with an exercised entry point: 2
- Components not registered as open-world targets: 8
- Components with only not-executed attempts: 1
- Unclassified cases retained: 1000

An exercised entry point does not mean every capability or interface in that component was tested.

## Failure and diagnostic clusters

| Cluster | Cases | Proposed signature |
|---|---:|---|
| OWCL-34BCFFA8B7AB875C | 7 | interpretation_ambiguous|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED |
| OWCL-4B9E5AF44E57E495 | 33 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-A6DF9D60DB38D1AD | 45 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_AMBIGUOUS_TOKEN,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-2FC95A52DEE8B9F5 | 1 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-9939FA433BF31E62 | 5 | interpretation_ambiguous|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-3C5D8709F73A92B7 | 68 | interpretation_partial|phase4-bounded-interpreter|semantic_composition:unspecified,syntax:unspecified |
| OWCL-DE429831B6628DF7 | 117 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-72084C09038185A2 | 69 | interpretation_partial|phase5-bounded-interpreter|discourse:DISCOURSE_ANTECEDENT_UNRESOLVED,lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-DDB43976CF66466F | 6 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN |
| OWCL-5650588D074E1112 | 379 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,operators:OPERATOR_INCOMPLETE,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-80FCACA741E4537B | 386 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_INCOMPLETE |
| OWCL-7CDBB670CED83866 | 1 | interpretation_partial|phase5-bounded-interpreter|lexical:LEXICAL_UNRESOLVED_TOKEN,semantic_composition:SEMANTIC_CLAUSE_UNRESOLVED,syntax:SYNTAX_UNSUPPORTED |
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

- `scenario-cases.jsonl` — SHA-256 `186dda832b4a540bf65db44f71acb18f277c42f42f5cfafcc50d0918b50cbadb`
- `execution-results.jsonl` — SHA-256 `2b9f93029c9d35197871a3fc9cc70101e26926b9055cd43e71c82c12299cfb6d`
- `score-results.jsonl` — SHA-256 `160f0f37f62254796405b0d814cb7b808debe8667f33a13d49ef47b9e7633e3c`
- `generation-manifest.json` — SHA-256 `182e7f032a30390c1f59a79f10fe81de785b4702bf7b37500e34b7cdf3f37ceb`
- `coverage-ledger.json` — SHA-256 `9b526f9f35552c4c50811474cece458c61417a0f1cac8ec49899ee790d96567f`

This report describes observed behavior on this finite sample only. It is not a certification of general intelligence or unrestricted semantic understanding.
