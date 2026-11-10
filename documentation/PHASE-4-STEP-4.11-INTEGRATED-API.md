# Phase 4 — Step 4.11: Integrated Interpretation API and Kernel Lab

**Status:** IMPLEMENTED — pending exact-PR CI and merge acceptance  
**Pipeline:** `USG-INTERPRET/0.1.0`  
**Persistence:** existing Phase 3 canonical SQLite store

## API

`POST /v1/interpret` accepts `{"text":"...","language":"en|ar","persist":true|false}`. It returns the interpretation envelope, ordered stage outcomes, diagnostics, and a USG-SEM/1.0 document. Persistence defaults to true and uses the same immutable, revisioned SQLite store as canonical document submissions. Set `persist:false` for a non-persistent preview.

## Initial demonstrator coverage

The service wires source ingestion, segmentation, lexical analysis, grammar patterns, semantic frames, mention extraction, discourse markers, and conservative assertion/evidence projection. The bundled lexicon is intentionally tiny and demonstrative: English `Ada writes code` and Arabic `كتب الطالب الدرس`. Production-scale lexical and grammar resources must be supplied through versioned resource injection. Unknown words remain unresolved; multi-sentence composition is explicitly unsupported in this first integrated slice.

The API validates and stores every returned canonical document through the existing SQLite document store. It does not create a second database or mutate USG-SEM/1.0. A stored document's schema/reference validation is the persistence gate.

## Kernel Lab integration

The Kernel Lab exposes the same API endpoint through a raw-text input panel, language selector, persistence toggle, and stage-diagnostics view. A persisted result is loaded into the canonical document editor, allowing the user to inspect and continue with the same shared SQLite document and reasoning workflows. No separate front-end parser or alternate storage engine is introduced.

## Limits

This is a bounded end-to-end demonstrator, not a production English/Arabic parser. Model assistance remains optional and unused by default. Assertion commitment stays NONE and evidence support NOT_ESTABLISHED. Exact quotation alignment does not establish truth.
