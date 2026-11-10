# Phase 4 — Step 4.10: Optional Model-Assisted Candidate Generation

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Adapter:** `model-candidate-adapter/0.1.0`

The optional `CandidateGenerator` protocol accepts local or external model implementations without making any model a required dependency. Proposal batches carry source digest, language, model ID/version, configuration digest, prompt digest, and ordered candidate records.

The deterministic validator rejects a batch if the source digest or language differs, if candidate IDs repeat, or if a candidate span is outside the source or does not exactly reproduce its surface text. Accepted proposals are explicitly labelled as model candidates with provenance; they are not automatically added to the authoritative lexicon, grammar, semantic frame registry, or canonical graph.

No model is called by the baseline pipeline. This step adds only the adapter contract and validator; it does not download, configure, or require an inference server.
