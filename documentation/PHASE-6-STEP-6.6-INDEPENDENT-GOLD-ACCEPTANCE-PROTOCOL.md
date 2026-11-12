# Historical record — Independent human semantic-gold protocol superseded

**Status:** Retained for historical context; not an active Step 6.6 prerequisite.

On 2026-11-12, the project replaced the human-annotation and qualifying external bilingual dataset dependency with the graph-first automatic synthetic reference benchmark documented in [PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md](PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md).

No human annotations are required or used by the new benchmark. No human-labeled dataset has been fabricated or relabeled as gold. The former protocol below is preserved in Git history; this file now serves only as a migration pointer so repository readers do not mistake it for the current acceptance contract.

**Current acceptance scope:** 500 generated cases across ten English/MSA construction profiles; 20 positive, 20 negative, and 10 ambiguous/boundary cases per profile. The candidate recognizer must pass per-profile detection, exact role/span/relation, negative abstention, and ambiguity gates. This establishes controlled synthetic conformance only; it does not establish naturalistic language accuracy or promote runtime constructions.

See the [current Step 6.6 protocol](PHASE-6-STEP-6.6-AUTOMATIC-SYNTHETIC-REFERENCE-PROTOCOL.md) for the exact generation method, evidence boundaries, commands, and limitations.
