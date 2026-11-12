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
from tools.semantic_query_interface_v1_0_0.interface import QueryInterface  # noqa: E402
from tools.usg_local_api_v1_0_0 import USGApplication  # noqa: E402

QUERY_BENCHMARK_PATH = ROOT / "benchmarks" / "semantic-reasoning" / "query-v1.0.0" / "fixtures.json"
EXECUTOR_BENCHMARK_PATH = ROOT / "benchmarks" / "semantic-reasoning" / "executor-v1.0.0" / "fixtures.json"
EVIDENCE_BENCHMARK_PATH = ROOT / "benchmarks" / "semantic-reasoning" / "evidence-v1.0.0" / "fixtures.json"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _query_benchmark():
    return _load_json(QUERY_BENCHMARK_PATH)


def _resolve_query_document(document_ref):
    if document_ref.get("benchmark_id") == "USG-INFERENCE-EXECUTOR-BENCHMARK":
        bundle = _load_json(EXECUTOR_BENCHMARK_PATH)
    elif document_ref.get("benchmark_id") == "USG-EVIDENCE-ASSESSMENT-BENCHMARK":
        bundle = _load_json(EVIDENCE_BENCHMARK_PATH)
    else:
        raise ValueError("Unregistered canonical benchmark reference")
    matches = [item for item in bundle["fixtures"] if item["id"] == document_ref.get("fixture_id")]
    if len(matches) != 1:
        raise ValueError("Benchmark fixture reference must resolve exactly once")
    return matches[0]["document"]


def _compare_query_expected(result, expected):
    actual = {
        "completion_status": result["completion_status"],
        "goal_status": result["goal_status"],
        "candidate_count": len(result["inference_candidates"]),
        "derivation_count": len(result["derivations"]),
        "source_assertion_count": len(result["source_assertions"]),
        "conflict_count": len(result["conflicts"]),
    }
    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected.items()
        if key in actual and actual[key] != value
    }
    return {"passed": not mismatches, "actual": actual, "mismatches": mismatches}


def load_query_fixture(fixture_id):
    bundle = _query_benchmark()
    matches = [item for item in bundle["fixtures"] if item["id"] == fixture_id]
    if len(matches) != 1:
        raise ValueError("Query fixture ID must resolve exactly once")
    fixture = matches[0]
    return {
        "fixture_id": fixture["id"], "document": _resolve_query_document(fixture["document_ref"]),
        "query": fixture["query"], "expected": fixture["expected"],
        "benchmark_id": bundle["benchmark_id"], "benchmark_version": bundle["benchmark_version"],
    }


def run_query_payload(document, query, expected=None):
    result = QueryInterface().run(document, query)
    comparison = _compare_query_expected(result, expected) if isinstance(expected, dict) else None
    return {"result": result, "comparison": comparison}


def run_query_benchmark():
    bundle = _query_benchmark()
    interface = QueryInterface()
    rows = []
    for fixture in bundle["fixtures"]:
        document = _resolve_query_document(fixture["document_ref"])
        result = interface.run(document, fixture["query"])
        comparison = _compare_query_expected(result, fixture["expected"])
        rows.append({
            "fixture_id": fixture["id"], "expected": fixture["expected"],
            "comparison": comparison, "result": result,
        })
    passed = sum(1 for row in rows if row["comparison"]["passed"])
    return {
        "benchmark_id": bundle["benchmark_id"], "benchmark_version": bundle["benchmark_version"],
        "total": len(rows), "passed": passed, "failed": len(rows) - passed,
        "accepted": passed == len(rows), "results": rows,
    }

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
        if path.startswith(("/v1/", "/v2/", "/v3/")):
            status, payload = self.server.usg_application.dispatch("GET", self.path)
            self._send(status, payload)
            return
        if path in ("/", "/index.html"):
            self._send(200, (WEB_ROOT / "index.html").read_bytes(),
                       "text/html; charset=utf-8")
        elif path == "/health":
            self._send(200, {
                "ok": True, "app": "USG Kernel Lab", "mentionModel": "0.7.0",
                "adapter": "USG-SEM/1.0", "queryInterface": "USG-QUERY/1.0.0",
                "evidenceAssessment": "USG-EVIDENCE-ASSESSMENT/1.0.0",
                "documentStore": "SQLite",
                "persistentApi": "USG-LOCAL-API/1.0.0",
                "analysisServices": "USG-DOCUMENT-ANALYSIS/1.0.0",
                "phase5Pipeline": "USG-INTERPRET/0.2.0",
                "phase6CandidatePipeline": "USG-INTERPRET/0.3.0",
                "phase6CandidateCapabilities": "CANDIDATE_ONLY",
                "resourceCatalogue": "sqlite-semantic-resource-catalogue/0.1.0",
            })
        elif path == "/api/fixtures":
            bundle = _query_benchmark()
            self._send(200, {
                "ok": True, "benchmarkId": bundle["benchmark_id"],
                "benchmarkVersion": bundle["benchmark_version"],
                "fixtures": [{
                    "id": item["id"], "goal": item["query"]["goal"],
                    "ruleIds": item["query"]["inference_task"]["rule_ids"],
                    "expected": item["expected"],
                } for item in bundle["fixtures"]],
            })
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith(("/v1/", "/v2/", "/v3/")):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0:
                    raise ValueError("Content-Length must be a positive integer")
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                status, payload = self.server.usg_application.dispatch("POST", self.path, request)
                self._send(status, payload)
            except Exception as exc:
                self._send(400, {"error": str(exc), "errorType": type(exc).__name__})
            return
        if path not in ("/api/inspect", "/api/export", "/api/query", "/api/fixture", "/api/benchmark"):
            self._send(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 8_000_000:
                raise ValueError("Request body must be between 1 byte and 8 MB")
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            if path == "/api/fixture":
                fixture = load_query_fixture(request.get("fixture_id"))
                self._send(200, {"ok": True, **fixture})
                return
            if path == "/api/benchmark":
                self._send(200, {"ok": True, **run_query_benchmark()})
                return
            document = request.get("document")
            if not isinstance(document, dict):
                raise ValueError("document must be a JSON object")
            if path == "/api/query":
                query = request.get("query")
                if not isinstance(query, dict):
                    raise ValueError("query must be a JSON object")
                payload = run_query_payload(document, query, request.get("expected"))
                self._send(200, {"ok": True, **payload})
                return

            imported = document_to_kernel_v07(document, validate=True)
            if path == "/api/inspect":
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


class KernelLabHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, database_path):
        self.usg_application = USGApplication(database_path)
        super().__init__(address, Handler)

    def server_close(self):
        try:
            super().server_close()
        finally:
            self.usg_application.close()


def create_lab_server(database_path=None, host=HOST, port=PORT):
    if host != "127.0.0.1":
        raise ValueError("USG Kernel Lab is loopback-only and binds only to 127.0.0.1")
    if database_path is None:
        database_path = ROOT / "usg-workbench.sqlite3"
    return KernelLabHTTPServer((host, port), database_path)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="USG Kernel Lab — local-only interface")
    parser.add_argument("--db", default=str(ROOT / "usg-workbench.sqlite3"), help="SQLite canonical document database path")
    parser.add_argument("--host", choices=["127.0.0.1"], default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args(argv)
    server = create_lab_server(args.db, args.host, args.port)
    print("USG Kernel Lab — local-only interface")
    print(f"Open http://{args.host}:{server.server_address[1]} in your browser")
    print(f"SQLite canonical database: {args.db}")
    print("Persistent API: /v1/ · Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nUSG Kernel Lab stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
