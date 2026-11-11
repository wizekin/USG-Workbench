# Phase 6 Step 6.6 — Benchmark v0.4.1 Genitive Relation Refinement

**Status:** candidate gold corpus; implementation and benchmark acceptance pending.

The v0.4.0 `POSSESSION` labels overclaimed semantics for English *of*-phrases and Arabic iḍāfa: these forms can express possession, association, part-whole, authorship, content, and other relations. The additive v0.4.1 corpus renames this profile `GENITIVE_RELATION`, uses structural roles `GENITIVE_HEAD` and `GENITIVE_DEPENDENT`, and explicitly records `GENITIVE_UNSPECIFIED`. It does not infer ownership or any specific relation from form alone.

The corpus retains 500 fixtures and ten language/construction profiles. All profiles remain disabled. v0.4.0 is preserved unchanged.


## Ambiguity fixture correction

The initial v0.4.1 candidate update reused several positive examples as ambiguous fixtures in the same construction profile. The corrected revision now uses ten construction-specific ambiguity examples per profile and validates that identical source text cannot carry conflicting gold classes within the same language/construction. This is an annotation consistency check, not proof that all ambiguous analyses are linguistically exhaustive.
