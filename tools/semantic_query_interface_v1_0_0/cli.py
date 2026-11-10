"""Command-line interface for structured USG queries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .interface import QueryInterface, QueryInterfaceError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run an explicit typed-reference USG query; this CLI does not parse free text.")
    parser.add_argument("--document", required=True, help="Canonical USG-SEM/1.0 JSON document.")
    parser.add_argument("--query", required=True, help="USG structured query JSON.")
    parser.add_argument("--output", help="Optional output JSON path; stdout is used when omitted.")
    args = parser.parse_args(argv)
    try:
        document = json.loads(Path(args.document).read_text(encoding="utf-8"))
        query = json.loads(Path(args.query).read_text(encoding="utf-8"))
        result = QueryInterface().run(document, query)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0 if result["completion_status"] in {"COMPLETE", "INCOMPLETE"} else 2
    except (OSError, json.JSONDecodeError, QueryInterfaceError, ValueError) as exc:
        print(json.dumps({"error":str(exc),"completion_status":"INVALID_INPUT"},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
