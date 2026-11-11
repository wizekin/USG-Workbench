"""Cross-reference validation for the candidate Phase 6 frame registry."""
from pathlib import Path
import json
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[2]
SCHEMA=ROOT/"specifications/usg-frame-registry-0.3.0.schema.json"
REGISTRY=ROOT/"resources/semantic-frames/v0.3.0/registry.json"
BENCHMARK=ROOT/"benchmarks/phase6-interpretation-v0.3.0/corpus.json"

def validate_registry():
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    errors=list(Draft202012Validator(schema).iter_errors(data))
    if errors:
        raise ValueError("; ".join(f"{list(e.path)}: {e.message}" for e in errors))
    roles={r["roleId"]:r for r in data["roleDefinitions"]}
    if len(roles)!=len(data["roleDefinitions"]):
        raise ValueError("duplicate roleId")
    frames={f["frameId"]:f for f in data["frames"]}
    if len(frames)!=len(data["frames"]):
        raise ValueError("duplicate frameId")
    benchmark=json.loads(BENCHMARK.read_text(encoding="utf-8"))
    expected={(lang,c["construction_id"]) for lang,items in benchmark["construction_inventory"].items() for c in items}
    seen=set()
    for frame in data["frames"]:
        slot_ids=set()
        for slot in frame["slots"]:
            if slot["slotId"] in slot_ids:
                raise ValueError(f"duplicate slotId in {frame['frameId']}")
            slot_ids.add(slot["slotId"])
            role=roles.get(slot["roleRef"])
            if role is None:
                raise ValueError(f"unknown role reference: {slot['roleRef']}")
            if not set(slot["allowedFillerSorts"]).issubset(set(role["compatibleFillerSorts"])):
                raise ValueError(f"slot filler sorts conflict with role {role['roleId']}")
            if slot["maxFillers"] is not None and slot["minFillers"]>slot["maxFillers"]:
                raise ValueError(f"invalid slot cardinality: {frame['frameId']}/{slot['slotId']}")
        for binding in frame["constructionBindings"]:
            key=(binding["language"],binding["constructionId"])
            if key not in expected:
                raise ValueError(f"construction binding absent from Step 6.2 corpus: {key}")
            if key in seen:
                raise ValueError(f"construction binding appears more than once: {key}")
            seen.add(key)
        langs={(x["language"],x["languageProfile"]) for x in frame["lexicalRealizations"]}
        if ("en","en/standard-written-1.0") not in langs or ("ar","ar/modern-standard-1.0") not in langs:
            raise ValueError(f"missing language realization: {frame['frameId']}")
        if frame["status"]!="CANDIDATE":
            raise ValueError("Step 6.3 must not enable or approve a frame")
    if seen!=expected:
        raise ValueError(f"unbound benchmark constructions: {sorted(expected-seen)}")
    if data["status"]!="CANDIDATE":
        raise ValueError("registry must remain candidate-only")
    return data

if __name__=="__main__":
    registry=validate_registry()
    print(f"validated {len(registry['roleDefinitions'])} roles and {len(registry['frames'])} candidate frames")
