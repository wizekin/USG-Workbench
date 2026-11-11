# USG Interpretation Gold Benchmark v0.4.2 — Token-Boundary Span Correction

Additive 500-fixture correction of v0.4.1. It preserves all construction labels and role graphs but corrects a grammatical-marker span that previously matched the substring `of` inside `office` rather than the standalone preposition. The validator now requires grammatical markers and predicate spans to align to complete Unicode word tokens and rejects conflicting labels for identical text.

All profiles remain candidate-only. v0.4.1 and earlier snapshots remain unchanged.
