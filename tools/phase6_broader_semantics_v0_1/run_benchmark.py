"""Execute and persist the generated Phase 6 composition contract benchmark."""
from __future__ import annotations
import json
from pathlib import Path
from .benchmark import run_benchmark
ROOT=Path(__file__).resolve().parents[2]
def main():
    report=run_benchmark()
    path=ROOT/"artifacts/phase6-broader-composition-contract-report.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["failed"]: raise SystemExit("Phase 6 composition contract benchmark failed")
if __name__=="__main__": main()
