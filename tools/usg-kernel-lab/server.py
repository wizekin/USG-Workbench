from __future__ import annotations

import json
import sys
import traceback
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "implementations" / "python-kernel" / "v0.7.0"))

from interoperability.python_adapter.document_v07 import (  # noqa: E402
    document_to_kernel_v07,
    kernel_v07_document_to_contract,
)
from usg_discourse_v07 import (  # noqa: E402
    MentionResolutionStatus,
    NativeMentionV07,
    ReferenceSpace,
    TypedReference,
)

WEB_ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765


def _native_json(mention: NativeMentionV07) -> dict:
    return {
        "id": mention.external_id,
        "surfaceText": mention.surface_text,
        "resolutionStatus": mention.resolution_status.value,
        "mentionType": mention.mention_type,
        "referentRef": mention.referent_ref.external_id if mention.referent_ref else None,
        "antecedentMentionRef": (
            mention.antecedent_mention_ref.external_id
            if mention.antecedent_mention_ref else None
        ),
        "antecedentReferentRef": (
            mention.antecedent_referent_ref.external_id
            if mention.antecedent_referent_ref else None
        ),
        "sourceRef": mention.source_ref.external_id if mention.source_ref else None,
        "sourceSpan": list(mention.source_span) if mention.source_span is not None else None,
    }


def _typed(value, space):
    if value is None or value == "":
        return None
    return TypedReference(space, value)


def _apply_native_edits(imported, rows):
    if not isinstance(rows, list):
        raise ValueError("nativeMentions must be a JSON array")
    supplied = {row.get("id"): row for row in rows if isinstance(row, dict)}
    if len(supplied) != len(rows):
        raise ValueError("Every native Mention edit must be an object with an id")
    if set(supplied) != set(imported.mentions):
        raise ValueError("The native Mention list must contain exactly the imported Mention IDs")

    for mention_id, row in supplied.items():
        source_span = row.get("sourceSpan")
        if source_span is not None:
            if (not isinstance(source_span, list) or len(source_span) != 2
                    or any(not isinstance(x, int) or isinstance(x, bool) for x in source_span)):
                raise ValueError(f"{mention_id}: sourceSpan must be null or [start, end]")
            source_span = tuple(source_span)

        status = MentionResolutionStatus(row["resolutionStatus"])
        imported.mentions[mention_id] = NativeMentionV07(
            external_id=mention_id,
            surface_text=row["surfaceText"],
            resolution_status=status,
            mention_type=row.get("mentionType"),
            referent_ref=_typed(row.get("referentRef"), ReferenceSpace.REFERENT),
            antecedent_mention_ref=_typed(
                row.get("antecedentMentionRef"), ReferenceSpace.MENTION
            ),
            antecedent_referent_ref=_typed(
                row.get("antecedentReferentRef"), ReferenceSpace.REFERENT
            ),
            source_ref=_typed(row.get("sourceRef"), ReferenceSpace.SOURCE),
            source_span=source_span,
        )


class Handler(BaseHTTPRequestHandler):
    server_version = "USGKernelLab/0.1"

    def _send(self, status, payload, content_type="application/json; charset=utf-8"):
        data = payload if isinstance(payload, bytes) else json.dumps(
            payload, ensure_ascii=False, indent=2
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, (WEB_ROOT / "index.html").read_bytes(),
                       "text/html; charset=utf-8")
        elif path == "/health":
            self._send(200, {
                "ok": True, "app": "USG Kernel Lab", "mentionModel": "0.7.0",
                "adapter": "USG-SEM/1.0",
            })
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if urlparse(self.path).path not in ("/api/inspect", "/api/export"):
            self._send(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 8_000_000:
                raise ValueError("Request body must be between 1 byte and 8 MB")
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            document = request.get("document")
            if not isinstance(document, dict):
                raise ValueError("document must be a JSON object")

            imported = document_to_kernel_v07(document, validate=True)
            if self.path == "/api/inspect":
                self._send(200, {
                    "ok": True,
                    "modelVersion": "0.7.0",
                    "mappingReport": imported.mapping_report,
                    "diagnostics": imported.diagnostics,
                    "nativeMentions": [
                        _native_json(item) for item in imported.mentions.values()
                    ],
                    "canonicalRecordCounts": {
                        key: len(document.get(key, []))
                        for key in (
                            "sources", "referents", "mentions", "expressions",
                            "assertions", "evidence", "contexts",
                        )
                    },
                })
                return

            _apply_native_edits(imported, request.get("nativeMentions", []))
            exported = kernel_v07_document_to_contract(imported, validate=True)
            self._send(200, {
                "ok": True,
                "exportedDocument": exported,
                "message": "Native Mention edits exported; full USG-SEM/1.0 validation passed.",
            })
        except Exception as exc:
            self._send(400, {
                "ok": False,
                "error": str(exc),
                "errorType": type(exc).__name__,
            })

    def log_message(self, fmt, *args):
        print("[USG Kernel Lab] " + fmt % args)


if __name__ == "__main__":
    print("USG Kernel Lab — local-only interface")
    print(f"Open http://{HOST}:{PORT} in your browser")
    print("Press Ctrl+C to stop. The server binds to loopback only.")
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nUSG Kernel Lab stopped.")
