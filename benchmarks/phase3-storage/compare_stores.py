"""Fair, reproducible SQLite-vs-LMDB benchmark for the Phase 3 canonical store.

This measures identical semantic operations on identical USG-SEM documents. Results
are observations, not a pass/fail speed claim; correctness is gated separately.
"""
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
from tools.semantic_graph_store_lmdb_v1_0_0 import CanonicalDocumentStore as LMDBStore

FIXTURES = json.loads(
    (ROOT / "benchmarks/semantic-reasoning/executor-v1.0.0/fixtures.json").read_text(encoding="utf-8")
)
BASE = next(item["document"] for item in FIXTURES["fixtures"] if item["id"] == "EXEC-MP-POSITIVE-001")


def timed(fn):
    start = time.perf_counter()
    value = fn()
    return time.perf_counter() - start, value


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def run_once(backend: str, document: dict, root: Path) -> dict:
    path = root / backend
    store_type = SQLiteStore if backend == "sqlite" else LMDBStore
    store = store_type(path)
    try:
        write_s, stored = timed(lambda: store.put_document(document))
        read_samples = []
        for _ in range(7):
            elapsed, loaded = timed(lambda: store.get_document(document["documentId"]))
            read_samples.append(elapsed)
            if loaded.digest != stored.digest:
                raise RuntimeError(f"{backend}: digest mismatch after read")
        idempotent_s, repeated = timed(lambda: store.put_document(document))
        if repeated.revision != stored.revision:
            raise RuntimeError(f"{backend}: idempotent write created an unexpected revision")
        changed = deepcopy(document)
        changed["extensions"]["benchmarkRevision"] = "revision-2"
        update_s, updated = timed(lambda: store.put_document(changed, expected_revision=1))
        history_s, history = timed(lambda: store.list_revisions(document["documentId"]))
        integrity_s, integrity = timed(lambda: store.verify_integrity(document["documentId"]))
        rebuild_s, rebuilt = timed(lambda: store.rebuild_indexes(document["documentId"]))
        final = store.get_document(document["documentId"])
        if final.revision != 2 or final.digest != updated.digest:
            raise RuntimeError(f"{backend}: final revision mismatch")
        if integrity["status"] != "PASS":
            raise RuntimeError(f"{backend}: integrity check failed: {integrity}")
        if len(history) != 2 or [item["revision"] for item in history] != [1, 2]:
            raise RuntimeError(f"{backend}: revision history mismatch")
        if not rebuilt or any(count < 0 for count in rebuilt.values()):
            raise RuntimeError(f"{backend}: index rebuild returned invalid counts")
        return {
            "write_seconds": write_s,
            "read_seconds_median_7": statistics.median(read_samples),
            "read_seconds_all_7": read_samples,
            "idempotent_write_seconds": idempotent_s,
            "revision_update_seconds": update_s,
            "list_revisions_seconds": history_s,
            "integrity_seconds": integrity_s,
            "index_rebuild_seconds": rebuild_s,
            "final_revision": final.revision,
            "final_sha256": final.digest,
            "index_counts": rebuilt,
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
        {
            "id": f"benchmark-expression-{i}", "op": "PREDICATE_APP", "sort": "PROP",
            "operandRefs": [], "params": {"predicate": f"BENCHMARK_{i}"},
            "interpretationStatus": "RESOLVED",
        }
        for i in range(args.extra_expressions)
    ])
    results = {"benchmark": "USG Phase 3 canonical graph storage", "repeats": args.repeats,
               "extra_expressions": args.extra_expressions, "backends": {}}
    for backend in ("sqlite", "lmdb"):
        samples = []
        for repeat in range(args.repeats):
            run_document = deepcopy(document)
            run_document["documentId"] = f"{document['documentId']}-bench-{backend}-{repeat}"
            with tempfile.TemporaryDirectory() as tmp:
                sample = run_once(backend, run_document, Path(tmp))
                samples.append(sample)
        metric_names = [
            "write_seconds", "read_seconds_median_7", "idempotent_write_seconds",
            "revision_update_seconds", "list_revisions_seconds", "integrity_seconds",
            "index_rebuild_seconds",
        ]
        results["backends"][backend] = {
            "samples": samples,
            "median_seconds": {
                name: statistics.median(item[name] for item in samples)
                for name in metric_names
            },
        }

    sqlite = results["backends"]["sqlite"]["median_seconds"]
    lmdb = results["backends"]["lmdb"]["median_seconds"]
    results["lmdb_over_sqlite_ratio"] = {
        name: (lmdb[name] / sqlite[name] if sqlite[name] else None)
        for name in sqlite
    }
    output = ROOT / "phase3-storage-benchmark.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Benchmark report: {output}")


if __name__ == "__main__":
    main()
