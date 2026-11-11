# Phase 6 Step 6.6 — Benchmark v0.4.2 Token-Boundary Correction

The v0.4.1 corpus contained one false grammatical-marker span: the `of` marker for *the office of the manager* pointed to the substring inside *office*. The additive v0.4.2 corpus corrects the marker to the standalone preposition and adds token-boundary validation for all grammatical-marker and predicate spans. The 500 fixtures and semantic role annotations are otherwise preserved. All constructions remain disabled.
