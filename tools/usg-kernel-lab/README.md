# USG Kernel Lab

A small, local-only browser interface for exercising the current Python Mention model (v0.7.0) and the USG-SEM/1.0 ↔ v0.7.0 document adapter (Step 5J).

## What it can test

- Import and schema-validate a complete USG-SEM/1.0 document.
- Inspect native v0.7.0 Mention projections and per-record/per-field mapping coverage.
- Edit native Mention text, resolution status, Mention type, and explicitly typed Referent/antecedent/Source links.
- Edit Unicode code-point source spans.
- Export edits into the canonical document and run full document validation plus exact source-span alignment checks.
- Preserve canonical-only records and unsupported fields through the adapter's canonical envelope.

## What it does not do

This is an adapter/model test bench, not a natural-language semantic parser or an integrated runtime for all USG modules. It does not generate Mentions from raw sentences, infer coreference, infer Referents, or test all v0.5/v0.6/v0.7 components in one pipeline. The existing JavaScript Semantic Workbench v0.5.4 remains a separate application for model-assisted sentence interpretation.

## Requirements

- Python 3.10 or newer
- `jsonschema>=4.18,<5`

Install the validator from the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
```

## Run on Windows

From the repository root, double-click `tools/usg-kernel-lab/launch_windows.bat`, or run:

```powershell
py tools/usg-kernel-lab/server.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765).

The server binds only to `127.0.0.1`; it is not exposed to the network. Press Ctrl+C in the terminal to stop it.

## Quick test

1. Choose **Load sample document**.
2. Choose **Import & inspect**.
3. Inspect the mapping report and three sample Mention records. The two occurrences of “Alex” intentionally share a Referent but have different Mention IDs.
4. Change a Mention's surface text or resolution status.
5. Choose **Export native edits**. The export is accepted only if the complete canonical document remains valid.
6. Choose **Download exported JSON** to save the result.

Try changing the first Mention's surface text without updating its source span: export should be rejected because the span no longer aligns with the source. This is an intentional integrity check, not an arbitrary text-length cap.

## API

- `GET /` — browser interface
- `GET /health` — local server health and model/contract versions
- `POST /api/inspect` — `{"document": <USG-SEM/1.0 document>}`
- `POST /api/export` — `{"document": <document>, "nativeMentions": [<edited native Mention records>]}`

No telemetry or cloud calls are implemented.
