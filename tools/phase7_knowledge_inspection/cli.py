"""Command-line inspection of the Phase 7 knowledge repository."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from tools.usg_local_api_v1_0_0 import USGApplication
from tools.semantic_graph_store_v1_0_0.store import RESOURCE_CATALOGUE_ROLE
from tools.phase7_knowledge_repository import SQLiteKnowledgeRepository
from .service import KnowledgeInspectionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True, help="Existing USG SQLite database")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("bundles", help="List immutable knowledge bundle snapshots")
    query = sub.add_parser("query", help="Run a read-only contextual knowledge query")
    query.add_argument("text")
    query.add_argument("--consumer", choices=["PHASE2", "PHASE4", "PHASE5", "PHASE6"], default="PHASE2")
    query.add_argument("--language")
    query.add_argument("--candidate-evidence", action="store_true")
    inspect = sub.add_parser("inspect", help="Inspect a record and its provenance")
    inspect.add_argument("record_id")
    sub.add_parser("conflicts", help="List provider conflicts without selecting a winner")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    app = USGApplication(args.db)
    try:
        with app.store.resource_catalogue_session(role=RESOURCE_CATALOGUE_ROLE, write=True) as connection:
            repository = SQLiteKnowledgeRepository(connection)
        service = KnowledgeInspectionService(repository)
        if args.command == "bundles":
            result = service.list_bundles()
        elif args.command == "query":
            result = service.query(args.text, consumer=args.consumer, language=args.language,
                                   include_candidate_evidence=args.candidate_evidence)
        elif args.command == "inspect":
            result = service.inspect_record(args.record_id)
            if result is None:
                print(json.dumps({"error": "KNOWLEDGE_RECORD_NOT_FOUND"}, indent=2))
                return 1
        else:
            result = service.list_conflicts()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
