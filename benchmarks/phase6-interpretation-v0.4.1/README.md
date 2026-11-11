# USG Interpretation Gold Benchmark v0.4.1 — Genitive Relation Refinement

Additive refinement of the v0.4.0 candidate corpus. It retains 500 fixtures across ten English/MSA Arabic profiles (20 positive, 20 negative, 10 ambiguous each), but corrects the semantic overclaim in the former POSSESSION profile. English *of*-phrases and Arabic iḍāfa encode a genitive relation; they do not by themselves prove ownership, control, authorship, kinship, or another specific relation. The gold roles are therefore `GENITIVE_HEAD` and `GENITIVE_DEPENDENT`, and positive examples carry `GENITIVE_UNSPECIFIED` relation semantics.

All constructions remain disabled pending implementation and independent acceptance. v0.4.0 remains unchanged as a historical candidate snapshot.

The validator also rejects contradictory positive/negative/ambiguous labels for identical source text within the same language and construction profile. Ambiguous examples are construction-specific; they are not reused across all profiles.
