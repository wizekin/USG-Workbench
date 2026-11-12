"""Command-line interface for the local USG workbench."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.parse import quote

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

    interpret_v2 = sub.add_parser("interpret-v2", help="run the integrated Phase 5 v0.2 interpretation pipeline")
    interpret_v2.add_argument("file", help="UTF-8 source text file")
    interpret_v2.add_argument("--language", choices=["en", "ar"], required=True)
    interpret_v2.add_argument("--db", default="usg-workbench.sqlite3")
    interpret_v2.add_argument("--no-persist", action="store_true")
    interpret_v2.add_argument("--output")

    resources = sub.add_parser("resources", help="show the persistent semantic resource catalogue")
    resources.add_argument("--db", default="usg-workbench.sqlite3")

    associations = sub.add_parser("associations", help="retrieve provisional associations by exact source reference")
    associations.add_argument("source_ref")
    associations.add_argument("--db", default="usg-workbench.sqlite3")
    associations.add_argument("--active-limit", type=int, default=10)
    associations.add_argument("--secondary-limit", type=int, default=20)

    replay = sub.add_parser("replay", help="replay a stored Phase 5 interpretation run")
    replay.add_argument("run_id")
    replay.add_argument("--db", default="usg-workbench.sqlite3")

    phase6_interpret = sub.add_parser("phase6-interpret", help="run the integrated bilingual Phase 6 candidate interpreter")
    phase6_interpret.add_argument("file", help="UTF-8 source text file")
    phase6_interpret.add_argument("--language", choices=["en", "ar"], required=True)
    phase6_interpret.add_argument("--db", default="usg-workbench.sqlite3")
    phase6_interpret.add_argument("--no-persist", action="store_true")
    phase6_interpret.add_argument("--output")

    phase6_compose = sub.add_parser("phase6-compose", help="compose and validate a Phase 6 candidate semantic graph")
    phase6_compose.add_argument("file", help="JSON request with source, language, and graph")
    phase6_compose.add_argument("--db", default="usg-workbench.sqlite3")
    phase6_compose.add_argument("--no-persist", action="store_true")
    phase6_compose.add_argument("--output")

    phase6_extract = sub.add_parser("phase6-extract", help="extract a strict-template Phase 6 candidate graph from raw text")
    phase6_extract.add_argument("file", help="UTF-8 source text file")
    phase6_extract.add_argument("--language", choices=["en", "ar"], required=True)
    phase6_extract.add_argument("--db", default="usg-workbench.sqlite3")
    phase6_extract.add_argument("--no-persist", action="store_true")
    phase6_extract.add_argument("--output")

    phase6_replay = sub.add_parser("phase6-replay", help="replay a stored Phase 6 candidate composition run")
    phase6_replay.add_argument("run_id")
    phase6_replay.add_argument("--db", default="usg-workbench.sqlite3")

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
        if args.command == "phase6-interpret":
            source_text = Path(args.file).read_text(encoding="utf-8")
            status, result = application.dispatch("POST", "/v3/phase6/interpret", {
                "source": source_text, "language": args.language,
                "persist": not args.no_persist,
            })
        elif args.command == "phase6-extract":
            source_text = Path(args.file).read_text(encoding="utf-8")
            status, result = application.dispatch("POST", "/v3/phase6/extract", {
                "source": source_text, "language": args.language,
                "persist": not args.no_persist,
            })
        elif args.command == "phase6-compose":
            request = _read_json(args.file)
            if not isinstance(request, dict):
                raise ValueError("Phase 6 request file must contain a JSON object")
            request["persist"] = not args.no_persist
            status, result = application.dispatch("POST", "/v3/phase6/compose", request)
        elif args.command == "phase6-replay":
            status, result = application.dispatch(
                "POST", "/v3/phase6/runs/" + quote(args.run_id, safe="") + "/replay", {}
            )
        elif args.command == "interpret-v2":
            source_text = Path(args.file).read_text(encoding="utf-8")
            status, result = application.dispatch("POST", "/v2/interpret", {
                "text": source_text, "language": args.language,
                "persist": not args.no_persist,
            })
        elif args.command == "resources":
            status, result = application.dispatch("GET", "/v2/resources")
        elif args.command == "associations":
            target = "/v2/associations?source_ref=" + quote(args.source_ref, safe="")
            target += f"&active_limit={args.active_limit}&secondary_limit={args.secondary_limit}"
            status, result = application.dispatch("GET", target)
        elif args.command == "replay":
            status, result = application.dispatch(
                "POST", "/v2/interpretations/" + quote(args.run_id, safe="") + "/replay", {}
            )
        elif args.command == "store":
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
        if args.command in {"export", "interpret-v2", "phase6-compose", "phase6-extract", "phase6-interpret"} and status == 200 and getattr(args, "output", None):
            Path(args.output).write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Exported JSON result to {args.output}")
        else:
            _emit(result)
        return 0 if status < 400 else 1
    finally:
        application.close()


if __name__ == "__main__":
    raise SystemExit(main())
