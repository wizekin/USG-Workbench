# USG Python reference kernel

Versioned source releases are stored in subdirectories. Current archived baseline: v0.4.0/.

Additive semantic record models:
- v0.5.0/: native predicate application, connective, and quantifier constructors.
- v0.6.0/: Referent identity model.
- v0.7.0/: Mention occurrence model.
- v0.8.0/: Assertion model.
- v0.9.0/: Evidence model.
- v1.0.0/: Context model.
- v1.1.0/: ExpressionRelation model.

These versioned extensions are separate packages; they do not mutate the frozen v0.4.0 baseline. See the corresponding Step 5 contracts under interoperability/python-kernel-extension/. Model-only releases do not imply document-adapter integration.

See ARCHIVE_INVENTORY.md at the repository root for checksums, test results, and known discrepancies.
