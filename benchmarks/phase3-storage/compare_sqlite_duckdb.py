"""Identical SQLite/DuckDB workload benchmark for the USG canonical store."""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.semantic_graph_store_v1_0_0 import CanonicalDocumentStore as SQLiteStore
from tools.semantic_graph_store_duckdb_v1_0_0 import CanonicalDocumentStore as DuckDBStore

FIXTURES = json.loads((ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8"))
BASE = next(x["document"] for x in FIXTURES["fixtures"] if x["id"] == "EXEC-MP-POSITIVE-001")


def timed(fn):
    start = time.perf_counter()
    value = fn()
    return time.perf_counter() - start, value


def storage_size(path: Path) -> int:
    files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    return sum(p.stat().st_size for p in files)


def run_once(backend, document, root):
    path = root / backend
    store = SQLiteStore(path) if backend == "sqlite" else DuckDBStore(path)
    try:
        write_s, first = timed(lambda: store.put_document(document))
        reads = []
        for _ in range(7):
            elapsed, loaded = timed(lambda: store.get_document(document["documentId"]))
            reads.append(elapsed)
            if loaded.digest != first.digest:
                raise RuntimeError(f"{backend}: read digest mismatch")
        idem_s, idem = timed(lambda: store.put_document(document))
        if idem.revision != 1:
            raise RuntimeError(f"{backend}: idempotent retry changed revision")
        changed = deepcopy(document)
        changed["extensions"]["benchmarkRevision"] = "second"
        update_s, updated = timed(lambda: store.put_document(changed, expected_revision=1))
        history_s, history = timed(lambda: store.list_revisions(document["documentId"]))
        integrity_s, report = timed(lambda: store.verify_integrity(document["documentId"]))
        rebuild_s, counts = timed(lambda: store.rebuild_indexes(document["documentId"]))
        final = store.get_document(document["documentId"])
        if final.revision != 2 or final.digest != updated.digest:
            raise RuntimeError(f"{backend}: final revision mismatch")
        if report["status"] != "PASS" or [x["revision"] for x in history] != [1, 2]:
            raise RuntimeError(f"{backend}: history/integrity mismatch")
        store.close()
        return {
            "write_seconds": write_s,
            "warm_read_median_7_seconds": statistics.median(reads),
            "idempotent_write_seconds": idem_s,
            "revision_update_seconds": update_s,
            "history_seconds": history_s,
            "integrity_seconds": integrity_s,
            "index_rebuild_seconds": rebuild_s,
            "storage_bytes": storage_size(path),
            "index_counts": counts,
            "final_sha256": final.digest,
        }
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--extra-expressions", type=int, default=1200)
    args = parser.parse_args()
    if args.repeats < 1 or args.extra_expressions < 0:
        parser.error("repeats must be positive and extra-expressions non-negative")
    document = deepcopy(BASE)
    document["expressions"].extend([
        {"id": f"bench-expression-{i}", "op": "PREDICATE_APP", "sort": "PROP",
         "operandRefs": [], "params": {"predicate": f"BENCH_{i}"},
         "interpretationStatus": "RESOLVED"}
        for i in range(args.extra_expressions)
    ])
    result = {"benchmark": "USG Phase 3 SQLite vs DuckDB", "repeats": args.repeats,
              "extra_expressions": args.extra_expressions, "backends": {}}
    for backend in ("sqlite", "duckdb"):
        samples = []
        for index in range(args.repeats):
            item = deepcopy(document)
            item["documentId"] = f"{document['documentId']}-{backend}-{index}"
            with tempfile.TemporaryDirectory() as tmp:
                samples.append(run_once(backend, item, Path(tmp)))
        metrics = [
            "write_seconds", "warm_read_median_7_seconds", "idempotent_write_seconds",
            "revision_update_seconds", "history_seconds", "integrity_seconds",
            "index_rebuild_seconds", "storage_bytes",
        ]
        result["backends"][backend] = {
            "samples": samples,
            "median": {name: statistics.median(x[name] for x in samples) for name in metrics},
        }
    a, b = result["backends"]["sqlite"]["median"], result["backends"]["duckdb"]["median"]
    result["duckdb_over_sqlite_ratio"] = {
        name: (b[name] / a[name] if a[name] else None) for name in a
    }
    output = ROOT / "phase3-duckdb-benchmark.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Benchmark report: {output}")


if __name__ == "__main__":
    main()
