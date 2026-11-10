# Phase 4 — Step 4.6: Mention and Reference Interpretation

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Analyzer:** `mention-reference/0.1.0`

The analyzer extracts source-grounded nominal, proper-name, and pronoun mentions from resolved lexical candidates. Every mention retains token ID, exact surface, source span, and lexical sense IDs.

Exact repeated surface forms may produce a `CANDIDATE` antecedent relation. This is a retrieval cue only; it does not establish that two mentions denote the same entity. All mentions remain unresolved in this initial implementation. No alias expansion, entity database lookup, pronoun resolution, or identity promotion is performed.

Tests cover English proper/nominal/pronoun mentions, exact span alignment, repeated-name candidate links, and unresolved/unknown material.
