from __future__ import annotations

import json
import math
import platform
import statistics
import sys
import time
import tracemalloc
import uuid
from collections import Counter

from ..core.records import Source
from ..core.spans import Span
from ..encoding.usbf import decode, encode
from ..grammar.serialize import node_to_json
from ..grammar.typecheck import Typechecker
from ..interpretation.parser import DeterministicInterpreter
from ..validation.validator import ValidationContext, Validator
from ..storage.schema import WriterRole
from ..util import canonical_json
from .corpus import CONTRASTIVE, cases, semantic_fingerprint


def interval(correct, n):
    if not n:
        return [0.0, 1.0]
    z, p = 1.96, correct/n
    center = (p+z*z/(2*n))/(1+z*z/n)
    margin = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [max(0,center-margin), min(1,center+margin)]


def run(*, split="test", db=None):
    parser = DeterministicInterpreter()
    samples, durations, failures, json_records = list(cases(split=split)), [], [], []
    outcome_hits = frame_hits = exact_hits = false_resolved = supported = unsupported = roundtrips = 0
    tp = fp = fn = 0
    tracemalloc.start()
    start = time.perf_counter()
    for c in samples:
        begin = time.perf_counter()
        x = parser.interpret(Source(c.text, language=c.language), Span(0,len(c.text)))
        durations.append((time.perf_counter()-begin)*1000)
        got = semantic_fingerprint(x)
        outcome = x.candidate.certificate.outcome.value
        outcome_hits += outcome == c.outcome
        if outcome == "RESOLVED" and c.outcome != "RESOLVED":
            false_resolved += 1
        if c.expected is not None:
            supported += 1
            exact_hits += got == c.expected
            frame_hits += got is not None and got["frames"] == c.expected["frames"]
            actual_roles = Counter(tuple(t) for t in (got["roles"] if got else []))
            gold_roles = Counter(tuple(t) for t in c.expected["roles"])
            tp += sum((actual_roles & gold_roles).values())
            fp += sum((actual_roles-gold_roles).values())
            fn += sum((gold_roles-actual_roles).values())
            mentions = {m.handle:m for m in x.mentions}
            v = Validator(ValidationContext(Typechecker(parser.foundation.frames,classes_of=lambda r:[mentions[r].concept] if r in mentions else ()),
                                           resolves_ref=lambda r:r in mentions,surface_of=lambda r:[mentions[r].label] if r in mentions else []))
            report = v.validate(x.candidate)
            if report.failed():
                unsupported += 1
                failures.append({"id": c.id, "text": c.text, "validation": report.codes()})
            if got != c.expected:
                failures.append({"id": c.id, "text": c.text, "expected": c.expected, "actual": got})
        elif outcome != c.outcome:
            failures.append({"id": c.id, "text": c.text, "expected_outcome": c.outcome, "actual": outcome})
        record = node_to_json(x.candidate.expression)
        json_records.append(record)
        roundtrips += decode(encode([record])) == [record]
    contrastive_failures = []
    for a, b in CONTRASTIVE:
        def fingerprint(text):
            return semantic_fingerprint(parser.interpret(Source(text),Span(0,len(text))))
        if fingerprint(a) == fingerprint(b):
            contrastive_failures.append([a,b])
    elapsed = time.perf_counter()-start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    plain = canonical_json(json_records).encode("utf-8")
    import zlib
    container = encode(json_records)
    report = {"run_id": uuid.uuid4().hex, "split": split, "scope": "constructed subset; consistency proxies, not open-domain correctness",
              "checked_invariants": ["covered_outputs_validate", "no_false_confident_resolution_in_corpus", "contrastive_preservation", "exact_binary_roundtrip"],
              "latency_scope": "parser and canonicalization; excludes database, models and I/O",
              "samples": len(samples), "supported_samples": supported, "outcome_accuracy": outcome_hits/max(1,len(samples)),
              "exact_semantic_accuracy": exact_hits/max(1,supported), "exact_semantic_95_ci": interval(exact_hits,supported),
              "frame_accuracy": frame_hits/max(1,supported), "role_f1": 2*tp/max(1,2*tp+fp+fn),
              "false_confident_resolutions": false_resolved, "validation_failures": unsupported,
              "contrastive_collapses": contrastive_failures, "roundtrip_passes": roundtrips,
              "hard_invariants_pass": not unsupported and not false_resolved and not contrastive_failures and roundtrips==len(samples),
              "latency_ms_p50": statistics.median(durations), "latency_ms_p95": sorted(durations)[max(0,math.ceil(len(durations)*.95)-1)],
              "elapsed_s": elapsed, "peak_traced_python_bytes": peak, "compression": {"canonical_json_bytes": len(plain),
              "zlib_json_bytes": len(zlib.compress(plain,9)), "usbf_bytes": len(container), "selection": "measure; no compression superiority assumed"},
              "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "sqlite": __import__('sqlite3').sqlite_version,
                              "models": "none", "dependencies": "standard library"}, "failures": failures}
    if db:
        with db.write(WriterRole.HISTORY) as t:
            t.execute("INSERT INTO benchmark_run VALUES(?,?,?)", (report["run_id"],db.clock.now(),canonical_json(report)))
    return report
