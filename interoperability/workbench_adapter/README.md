# Workbench v0.5.4 source adapter

**Adapter:** `USG-WB-SEM/1.0` (package version 1.0.0)  
**Input profile:** Workbench semantic core `USG-SR/0.5.1` (included in Workbench v0.5.4)  
**Output contract:** USG-SEM/1.0  
**Implementation:** `index.js`

## API

Browser global:

```js
const { model, validation } = USGSemanticCore.buildSemanticModel(sourceRecord);
if (!validation.valid) throw new Error('Workbench semantic model is structurally invalid');
const { document, report } =
  await USGWorkbenchSemAdapter.workbenchToContract(model);
```

CommonJS:

```js
const adapter = require('./interoperability/workbench_adapter');
const { model, validation } = semanticCore.buildSemanticModel(sourceRecord);
if (!validation.valid) throw new Error('Workbench semantic model is structurally invalid');
const result = await adapter.workbenchToContract(model);
```

The adapter is asynchronous because it computes SHA-256 hashes using Web Crypto. It accepts the semantic model produced by Workbench's semantic core; it does not parse or reinterpret source text.

## Conversion behavior

- Workbench entities become document-local USG-SEM referents. Entity IDs are encoded as opaque UTF-8-hex IDs; labels are never used as identity keys.
- Workbench mentions remain distinct from referents. Resolved/linked/unresolved state and antecedent referent links are retained.
- Workbench PREDICATION nodes become `PREDICATE_APP`. Argument order and role order are retained. Each argument is represented by a `REF` or `UNRESOLVED_REF` expression; unresolved pronouns do not create referents.
- NEGATION maps to `NOT`; MODAL maps to `MODAL`; QUANTIFIER maps to `QUANTIFIER`. Their exact Workbench operator label, force, scope kind, variable and restrictor metadata are retained in parameters.
- POLARITY/unknown-scope operators become explicit `OPAQUE` nodes and force a PARTIAL mapping result. They are not relabelled as negation.
- Directed connectives retain ordered antecedent/consequent references and their marker, logical status, exception interpretation, condition metadata and attribution. Multi-operand connectives retain operand order and explicit operand roles.
- Evidence references, quote text, source offsets, relations, roots, unresolved items, temporal data, completeness and provenance are carried into the canonical document.
- The original Workbench model is retained under `extensions.org.usg.workbench.v0.5.4.nativeModel`, with a SHA-256 digest. A second digest covers the canonical projection. `verifyNativeSnapshot(document)` verifies both; a canonical edit invalidates the projection digest and blocks any claim that the stored native snapshot is still synchronized.
- The adapter does not create assertions or contexts that Workbench did not supply. It does not convert the legacy `acceptanceBoundary.requiresHumanReview` field into canonical semantics; the field remains only in the archival native payload.

## Offset conversion

Workbench offsets are JavaScript UTF-16 code-unit offsets. USG-SEM offsets are Unicode code-point offsets.

Every mapped mention/evidence span is converted against the exact source string. A boundary that splits a UTF-16 surrogate pair is rejected. A mention span whose source substring does not equal its surface text is omitted from the canonical span and listed as partial; the native model still retains the original offsets. Evidence marked as an exact source match must match its source substring; explicitly mismatched/unverified evidence retains its declared status.

## Mapping status

The adapter returns `LOSSLESS`, `PARTIAL`, or an error for malformed/dangling input. PARTIAL is reported for opaque operator meanings, unaligned mention spans, non-exact relation-verification states, and Workbench builder warnings that indicate upstream discarded or source-unaligned information. The report includes the canonical/native references associated with partial mappings.

An unresolved referent or unresolved item is not by itself a mapping failure when it is faithfully represented as unresolved content.

## Boundaries

- This adapter does not claim that Workbench's original interpretation is semantically correct.
- The native snapshot preserves the supplied semantic model, not any information discarded before that model was produced. Builder warnings therefore prevent a LOSSLESS claim.
- It does not implement Python kernel projection, canonical-to-Workbench reconstruction, or a complete four-boundary round trip. Those are later Step 4 tasks.
- It does not change the immutable Workbench v0.5.4 source or archive.

## Tests

```bash
node --test tests/test_workbench_source_adapter.js
python -m pip install "jsonschema>=4.18,<5"
python -m unittest discover -s tests -p "test_workbench_source_adapter.py" -v
```

The Node tests cover predicate/argument structure, nested negation and modality, directed UNLESS/EXCEPTION, unresolved mentions, supplementary Unicode offsets, surrogate-pair rejection, partial mappings, stale-snapshot detection and dangling references. The Python test validates actual adapter output against the normative USG-SEM/1.0 JSON Schema.
