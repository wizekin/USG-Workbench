"""Portable exports; imports always re-enter the untrusted source pipeline."""
import json
from pathlib import Path

from ..core.ids import IdSpace, Ref
from ..core.records import Anchor
from ..grammar.serialize import node_from_json, node_to_json
from ..util import canonical_json
from .usbf import MAX_FILE, Reader, encode


def export_file(service, path, *, mode="reversible", format="usbf", codec="compact"):
    service.assert_integrity()
    if mode not in {"reversible", "semantic"} or format not in {"usbf", "json"}:
        raise ValueError("invalid export mode/format")
    records = []
    with service.db.read() as r:
        sources = r.query("SELECT source_id FROM source ORDER BY source_id")
        for row in sources:
            source = service.store.get_source(r, Ref(IdSpace.SOURCE, row[0]))
            records.append({"type": "source", "source_id": row[0], "language": source.language,
                            "source_hash": source.text_hash, "uri": source.uri, "sensitivity": source.sensitivity.value,
                            "anchor": source.anchor.to_json() if source.anchor else None,
                            **({"text": source.text} if mode == "reversible" else {})})
        for row in r.query("SELECT a.*,e.body FROM assertion a JOIN expression e ON e.node_id=a.content_id WHERE a.content_space='NODE' ORDER BY a.assertion_id"):
            expr = node_from_json(json.loads(row["body"]))
            evidence = r.one("SELECT body FROM evidence WHERE evidence_id=?", (row["evidence_id"],))
            records.append({"type": "assertion", "source_id": row["source_id"], "assertion_id": row["assertion_id"],
                            "epistemic_status": row["epistemic_status"], "expression": node_to_json(expr, include_ann=mode=="reversible"),
                            "evidence": json.loads(evidence[0]) if evidence else None})
        if mode == "reversible":
            for row in r.query("SELECT candidate_id,source_id,payload,report FROM candidate ORDER BY candidate_id"):
                records.append({"type": "derivation", "candidate_id": row["candidate_id"], "source_id": row["source_id"],
                                "payload": json.loads(row["payload"]), "report": json.loads(row["report"])})
    definitions = {"frames": [service.foundation.frames.get(n).to_json() for n in service.foundation.frames.names()],
                   "concepts": [service.foundation.ontology.seed(n).to_json() for n in service.foundation.ontology.concepts()]}
    if format == "usbf":
        from .compact import schemas_from_library
        schemas=schemas_from_library(service.foundation.frames)
        block_size=65536
        if codec=='auto':
            from .optimizer import choose_plan
            plan=choose_plan(records,schemas,codecs=('json','compact','template'))['selected']
            codec,block_size=plan['codec'],plan['block_size']
        data = encode(records, mode=mode, definitions=definitions, codec=codec, schemas=schemas,block_size=block_size)
    else:
        data = canonical_json({"profile": "USG-JSON-0.2", "mode": mode, "records": records, "definitions": definitions}).encode("utf-8")
    if len(data) > MAX_FILE:
        raise ValueError("export exceeds size budget")
    # Do not silently replace an existing artifact or live database.
    with open(path, "xb") as f:
        f.write(data)
    return {"file": str(Path(path).resolve()), "bytes": len(data), "records": len(records), "mode": mode}


def import_file(service, path):
    with open(path, "rb") as f:
        data = f.read(MAX_FILE+1)
    if len(data) > MAX_FILE:
        raise ValueError("import exceeds size budget")
    if data.startswith(b"USBF"):
        records = list(Reader(data).records())
    else:
        from .usbf import _json
        bundle = _json(data)
        if '@context' in bundle:
            from .linked_data import import_jsonld
            return import_jsonld(service,bundle)
        if bundle.get("profile") != "USG-JSON-0.2":
            raise ValueError("unsupported JSON profile")
        records = bundle["records"]
    # Validate all source records before writing any of them. Assertion statuses,
    # mappings, rules, definitions and derivations in the archive have no authority.
    from ..core.records import Source
    from ..core.values import Sensitivity
    sources = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid export record")
        if record.get("type") == "source" and "text" in record:
            source = Source(record["text"], language=record["language"], text_hash=record["source_hash"],
                            sensitivity=Sensitivity(record.get("sensitivity", "INTERNAL")),
                            anchor=Anchor(**record["anchor"]) if record.get("anchor") else None, uri=record.get("uri"))
            sources.append(source)
    results = [service.ingest(s.text, language=s.language, uri=s.uri, sensitivity=s.sensitivity.value,
                              anchor=s.anchor, trust_tier="QUARANTINE") for s in sources]
    return {"reinterpreted_sources": len(results), "results": results,
            "semantic_only_records_retained_in_file": not sources, "imported_trusted_claims": 0}
