"""Command line entry point for demand-driven lexical retrieval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

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
    sub.add_parser("benchmark", help="Run offline structural checks; no network calls.")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "benchmark":
        _print(run_structural_benchmark())
        return 0
    cache = LexicalCache(args.cache)
    service = ExternalLexicalService(cache=cache)
    try:
        if args.command == "activity":
            _print({
                "cache_path": str(cache.path),
                "activity": service.activity(args.limit),
                "note": "Activity counts represent lookup use, not semantic importance or word frequency in English.",
            })
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
