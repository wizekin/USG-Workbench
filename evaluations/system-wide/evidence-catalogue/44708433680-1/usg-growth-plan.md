# USG Evidence-Driven Growth Plan

Generated: 2026-11-20T09:11:34Z
Campaigns analyzed: 3

## Baseline warnings

- Naturalistic cases in the assessment baseline: 0
- External lexical exact-surface coverage in the assessment baseline: 0.0244
- External lexical OOV rate in the assessment baseline: 0.9756
- Phase 6 Step 6.6: blocked_pending_independent_bilingual_semantic_gold

## Ranked evidence-backed investigations

### 1. lexical — score 135

- First-blocker records: 122
- Campaign recurrence: 2
- Diagnostic codes: {"LEXICAL_AMBIGUOUS_TOKEN": 13, "LEXICAL_UNRESOLVED_TOKEN": 122, "STAGE_STATUS_AMBIGUOUS": 13, "STAGE_STATUS_PARTIAL": 109}
- Languages: ar, en, en-ar
- Targets: phase5-bounded-interpreter
- Populations: controlled_diagnostic, unconstrained_random
- Example cases: OW-RAND-00000002-289A10A032, OW-RAND-00000013-8AB585B8EE, OW-RAND-00000024-37F71C9282, OW-RAND-00000035-5C1DBBA4E6, OW-RAND-00000046-4F552472F0, OW-RAND-00000057-EF1621B3E8, OW-RAND-00000068-0770BC2702, OW-RAND-00000079-F2B5D93B19, OW-RAND-00000002-2D0539593F, OW-RAND-00000013-DF749FB9D5, OW-RAND-00000024-68CF59469F, OW-RAND-00000035-2E13F6D620, OW-RAND-00000046-6EB1855132, OW-RAND-00000057-495AF348DB, OW-RAND-00000068-E17FA02904, OW-RAND-00000079-6353B040A3
- Proposed next action: Investigate unresolved and ambiguous lexical evidence; add candidate-only source coverage and morphology regressions.
- Acceptance gate: independent_lexical_evaluation
- Runtime change allowed by this plan: no

### 2. syntax — score 119

- First-blocker records: 102
- Campaign recurrence: 3
- Diagnostic codes: {"INCOMPLETE": 73, "STAGE_STATUS_INCOMPLETE": 73, "STAGE_STATUS_PARTIAL": 2, "STAGE_STATUS_UNSUPPORTED": 23, "SYNTAX_UNSUPPORTED": 22, "UNSUPPORTED": 3, "UNSUPPORTED_INTERROGATIVE_FORCE": 6}
- Languages: ar, en, en-ar
- Targets: phase4-bounded-interpreter, phase5-bounded-interpreter
- Populations: controlled_diagnostic, unconstrained_random
- Example cases: OW-RAND-00000045-6053E606C7, OW-RAND-00000067-D228BFE3A2, OW-RAND-00000100-D6DB9FD3E4, OW-DIAG-P4-000003, OW-DIAG-P4-000005, OW-DIAG-P5-000040, OW-DIAG-P5-000041, OW-DIAG-P5-000042, OW-RAND-00000111-35ECB8B1D6, OW-DIAG-P5-000044, OW-DIAG-P5-000045, OW-RAND-00000070-FB82024D12, OW-RAND-00000088-BC746DB0F5, OW-RAND-00000139-9B55C64A2B, OW-RAND-00000235-F9083DE696, OW-RAND-00000265-D842DEBDE6, OW-RAND-00000355-2F19EA9F25, OW-RAND-00000532-36253757AE, OW-RAND-00000577-3BD8D298FE
- Proposed next action: Cluster recurring construction failures and add minimal positive, negative, ambiguous, and boundary fixtures before proposing a rule.
- Acceptance gate: independent_construction_gold
- Runtime change allowed by this plan: no

### 3. discourse — score 11

- First-blocker records: 2
- Campaign recurrence: 2
- Diagnostic codes: {"DISCOURSE_ANTECEDENT_UNRESOLVED": 2, "STAGE_STATUS_PARTIAL": 2}
- Languages: en
- Targets: phase5-bounded-interpreter
- Populations: controlled_diagnostic
- Example cases: OW-DIAG-P5-000058
- Proposed next action: Build reference-resolution cases with competing antecedents, explicit ambiguity, and discourse-boundary negatives.
- Acceptance gate: independent_discourse_gold
- Runtime change allowed by this plan: no

## Safety

- This planner ranks investigations; it does not edit runtime code or resources.
- Lexical resources remain candidate-only until independently evaluated and separately accepted.
- Semantic rule and contract changes require independent gold and explicit acceptance.
- Agreement between implementations is not treated as semantic correctness.
