

### Step 5H — USG-SEM/1.0 ↔ Python identity model v0.6.0 document adapter

- **Implementation:** [document_v06.py](python_adapter/document_v06.py); contract: [Step 5H Referent document adapter](python-kernel-extension/STEP-5H-REFERENT-DOCUMENT-ADAPTER.md).
- Public APIs: `document_to_kernel_v06()` and `kernel_v06_document_to_contract()`; exported from `interoperability.python_adapter`.
- Projects exact Referent identity fields into the separate v0.6.0 model, including independent status/scope, explicit typed equivalence links, concept references, supported introduction context, source grounding, and Unicode code-point spans.
- Reports per-record and per-field mapping coverage. Unsupported fields, unknown values, unresolved typed references, and additional contract properties remain canonical-only; no coercion or guessed reference-space assignment.
- Native edits are merged only into Referent records. Unchanged canonical fields, omitted fields, unknown sidecars, Mentions, and all other record families are retained.
- Export rejects stale canonical snapshots and validates the complete document, including source-span bounds.
- The v0.5.0 adapter, USG-SEM/1.0, Workbench v0.5.4, archives, immutable baselines, and existing Node.js action versions remain unchanged.
