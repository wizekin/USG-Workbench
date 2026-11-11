# Phase 6 Benchmark Annotation Correction — v0.3.2

**Status:** Additive corrected gold profile; v0.3.0 and v0.3.1 remain immutable.

This revision preserves the 400 texts, target labels, participant-role values, predicate spans, and grammatical-marker spans from v0.3.1. It corrects 5 repeated-mention fixtures (10 role-span annotations) where identical participant surface forms caused both role bindings to point to the first occurrence.

Participant spans are now assigned in the construction's left-to-right argument order. Repeated values remain distinct source mentions; identical names do not imply the same mention or entity. The evaluator continues to score participant roles, participant spans, predicate spans, grammatical markers, construction detection, and abstention independently.

Use v0.3.2 for Step 6.5 benchmark acceptance and Step 6.14. The earlier gold profiles remain available for historical reproducibility.
