# USG Evidence-Driven Growth Plan

Generated: 2026-11-12T13:47:35Z
Campaigns analyzed: 1

## Baseline warnings

- Naturalistic cases in the assessment baseline: 0
- External lexical exact-surface coverage in the assessment baseline: 0.0244
- External lexical OOV rate in the assessment baseline: 0.9756
- Phase 6 Step 6.6: blocked_pending_independent_bilingual_semantic_gold

## Ranked evidence-backed investigations

### 1. syntax — score 78

- First-blocker records: 68
- Campaign recurrence: 1
- Diagnostic codes: {"INCOMPLETE": 67, "STAGE_STATUS_INCOMPLETE": 67, "STAGE_STATUS_UNSUPPORTED": 1, "UNSUPPORTED": 1}
- Languages: ar, en, en-ar
- Targets: phase4-bounded-interpreter
- Populations: controlled_diagnostic, unconstrained_random
- Example cases: OW-RAND-00000070-FB82024D12, OW-RAND-00000088-BC746DB0F5, OW-RAND-00000139-9B55C64A2B, OW-RAND-00000235-F9083DE696, OW-RAND-00000265-D842DEBDE6, OW-RAND-00000355-2F19EA9F25, OW-RAND-00000532-36253757AE, OW-RAND-00000577-3BD8D298FE
- Proposed next action: Cluster recurring construction failures and add minimal positive, negative, ambiguous, and boundary fixtures before proposing a rule.
- Acceptance gate: independent_construction_gold
- Runtime change allowed by this plan: no

## Safety

- This planner ranks investigations; it does not edit runtime code or resources.
- Lexical resources remain candidate-only until independently evaluated and separately accepted.
- Semantic rule and contract changes require independent gold and explicit acceptance.
- Agreement between implementations is not treated as semantic correctness.
