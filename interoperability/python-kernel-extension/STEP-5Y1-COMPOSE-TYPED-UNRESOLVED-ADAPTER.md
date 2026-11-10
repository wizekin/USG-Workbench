# Phase 1 Step 5Y1 — Compose typed UnresolvedItem adapter v1.2.1

**Patch to:** Composed document adapter v1.5.0  
**Composed adapter version:** v1.5.1  
**Canonical contract:** USG-SEM/1.0 (unchanged)

The canonical contract validator establishes that UnresolvedItem `scopeRef` resolves to an Expression. Step 5T1 introduced a corrected v1.2.1 model/adapter with typed EXPRESSION scope references and typed EVIDENCE references.

This patch updates the composed v1.5.x adapter to delegate UnresolvedItems to `document_to_kernel_v121()` rather than the historical v1.2.0 adapter. The aggregate adapter's public function names remain stable; its patch version is advanced to v1.5.1.

The composed integration fixture now uses an actual Expression ID for `scopeRef`. The complete-document acceptance path therefore exercises the canonical reference constraint rather than bypassing it.

No other family adapter, model version, canonical schema, Workbench baseline, archive, or Node.js action version is changed.
