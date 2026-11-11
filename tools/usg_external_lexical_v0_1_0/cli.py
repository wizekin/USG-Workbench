"""Command line entry point for demand-driven lexical retrieval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .audit import audit_crawl_state
from .remote_audit import audit_github_branch
from .cache import LexicalCache, default_cache_path
from .evaluation import run_structural_benchmark
from .service import DEFAULT_PROVIDER_ORDER, ExternalLexicalService


def _print(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usg-lexical",
        description="Retrieve and analyze individual English lexical entries on demand.",
    )
    parser.add_argument("--cache", type=Path, default=default_cache_path(), help="Local cache path (outside the repository by default).")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("lookup", "analyze", "export"):
        command = sub.add_parser(name)
        command.add_argument("word")
        command.add_argument("--refresh", action="store_true", help="Ignore a fresh cache record and retrieve current data.")
        command.add_argument("--offline", action="store_true", help="Use only previously cached records.")
        command.add_argument("--providers", nargs="+", choices=DEFAULT_PROVIDER_ORDER, default=None)
    activity = sub.add_parser("activity", help="Show which words have been requested most often.")
    activity.add_argument("--limit", type=int, default=20)
    graph = sub.add_parser("graph", help="Assemble the cumulative graph from previously cached words.")
    graph.add_argument("--limit", type=int, default=10000)
    sub.add_parser("benchmark", help="Run offline structural checks; no network calls.")
    audit = sub.add_parser("audit", help="Reconcile crawl checkpoint, manifest and shard inventory.")
    audit.add_argument("--checkpoint", type=Path, required=True)
    audit.add_argument("--manifest", type=Path, required=True)
    audit.add_argument("--shard-inventory", type=Path, required=True,
                       help="JSON array of GitHub shard inventory objects (path, size, sha).")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "benchmark":
        _print(run_structural_benchmark())
        return 0
    if args.command == "audit-remote":\n        try:\n            report = audit_github_branch(args.repository, args.branch, token=__import__("os").environ.get("GITHUB_TOKEN"))\n            _print(report)\n            return 0 if report["status"] != "failed" else 1\n        except (OSError, ValueError, RuntimeError) as exc:\n            print(f"USG remote lexical audit failed: {exc}", file=sys.stderr)\n            return 2\n    if args.command == "audit":
        try:
            checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            inventory = json.loads(args.shard_inventory.read_text(encoding="utf-8"))
            if not isinstance(inventory, list):
                raise ValueError("--shard-inventory must contain a JSON array")
            report = audit_crawl_state(checkpoint, manifest, inventory)
            _print(report)
            return 0 if report["status"] != "failed" else 1
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"USG lexical audit failed: {exc}", file=sys.stderr)
            return 2

    cache = LexicalCache(args.cache)
    service = ExternalLexicalService(cache=cache)
    try:
        if args.command == "activity":
            _print({
                "cache_path": str(cache.path),
                "activity": service.activity(args.limit),
                "note": "Activity counts represent lookup use, not semantic importance or word frequency in English.",
            })
        elif args.command == "graph":
            graph = service.knowledge_graph(limit=args.limit)
            graph["cache_path"] = str(cache.path)
            _print(graph)
        elif args.command == "lookup":
            _print(service.lookup(
                args.word, refresh=args.refresh, offline=args.offline, providers=args.providers
            ))
        elif args.command == "analyze":
            _print(service.analyze(
                args.word, refresh=args.refresh, offline=args.offline, providers=args.providers
            ))
        elif args.command == "export":
            _print(service.export_usg_candidates(
                args.word, refresh=args.refresh, offline=args.offline, providers=args.providers
            ))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"USG lexical operation failed: {exc}", file=sys.stderr)
        return 2
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
