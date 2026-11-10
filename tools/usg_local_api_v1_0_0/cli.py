"""Command-line interface for the local USG workbench."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .application import USGApplication, create_server


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser():
    parser = argparse.ArgumentParser(prog="usg-workbench", description="Local USG-SEM/1.0 workbench")
    parser.add_argument("--version", action="version", version="usg-workbench 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="start the loopback-only HTTP API")
    serve.add_argument("--db", default="usg-workbench.sqlite3")
    serve.add_argument("--host", choices=["127.0.0.1", "::1"], default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    lab = sub.add_parser("lab", help="launch the integrated browser Kernel Lab and SQLite workspace")
    lab.add_argument("--db", default="usg-workbench.sqlite3")
    lab.add_argument("--host", choices=["127.0.0.1"], default="127.0.0.1")
    lab.add_argument("--port", type=int, default=8765)

    validate = sub.add_parser("validate", help="validate a canonical USG-SEM/1.0 JSON file")
    validate.add_argument("file")

    for name, help_text in [
        ("store", "store a canonical document"),
        ("get", "retrieve a stored document revision"),
        ("check", "verify stored snapshot and derived-index integrity"),
        ("conditions", "extract conditions, exceptions, and negations"),
        ("contradictions", "inspect exact-scope conflicts"),
        ("export", "export a complete canonical document"),
        ("revisions", "list immutable document revisions"),
    ]:
        command = sub.add_parser(name, help=help_text)
        command.add_argument("document_id_or_file")
        command.add_argument("--db", default="usg-workbench.sqlite3")
        if name in {"get", "check", "conditions", "contradictions", "export"}:
            command.add_argument("--revision", type=int)
        if name == "store":
            command.add_argument("--expected-revision", type=int)
        if name == "export":
            command.add_argument("--output")

    query = sub.add_parser("query", help="run a structured query against a stored revision")
    query.add_argument("document_id")
    query.add_argument("query_file")
    query.add_argument("--db", default="usg-workbench.sqlite3")
    query.add_argument("--revision", type=int)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "lab":
        import importlib.util
        root = Path(__file__).resolve().parents[2]
        server_path = root / "tools" / "usg-kernel-lab" / "server.py"
        spec = importlib.util.spec_from_file_location("usg_kernel_lab_packaged_server", server_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("packaged Kernel Lab server asset is missing")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        server = module.create_lab_server(args.db, args.host, args.port)
        print(f"USG Kernel Lab: http://{args.host}:{server.server_address[1]}")
        print(f"SQLite database: {args.db}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0

    if args.command == "serve":
        application = USGApplication(args.db)
        try:
            server = create_server(application, args.host, args.port)
            print(f"USG API listening at http://{args.host}:{server.server_address[1]}")
            print(f"SQLite database: {args.db}")
            print("Press Ctrl+C to stop.")
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if "server" in locals():
                server.server_close()
            application.close()
        return 0

    if args.command == "validate":
        application = USGApplication(":memory:")
        try:
            status, result = application.dispatch("POST", "/v1/validate", _read_json(args.file))
            _emit(result)
            return 0 if status == 200 else 1
        finally:
            application.close()

    application = USGApplication(args.db)
    try:
        if args.command == "store":
            body = {"document": _read_json(args.document_id_or_file)}
            if args.expected_revision is not None:
                body["expected_revision"] = args.expected_revision
            status, result = application.dispatch("POST", "/v1/documents", body)
        elif args.command == "query":
            status, result = application.dispatch("POST", "/v1/query", {
                "document_id": args.document_id,
                "query": _read_json(args.query_file),
                "revision": args.revision,
            })
        else:
            suffix = {
                "get": "",
                "check": "/check",
                "conditions": "/conditions",
                "contradictions": "/contradictions",
                "export": "/export",
                "revisions": "/revisions",
            }[args.command]
            target = f"/v1/documents/{args.document_id_or_file}{suffix}"
            if getattr(args, "revision", None) is not None:
                target += f"?revision={args.revision}"
            status, result = application.dispatch("GET", target)
        if args.command == "export" and status == 200 and args.output:
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Exported canonical document to {args.output}")
        else:
            _emit(result)
        return 0 if status < 400 else 1
    finally:
        application.close()


if __name__ == "__main__":
    raise SystemExit(main())
