"""Run the bounded Step 6.5 interpreter against the corrected frozen corpus."""
import json
from pathlib import Path
from tools.phase6_predicate_argument_v0_3_0.analyzer import predict_corpus
from tools.phase6_interpretation_benchmark_v0_3_1.run import load_corpus,evaluate,quality_gate
ROOT=Path(__file__).resolve().parents[2]
corpus=load_corpus()
predictions=predict_corpus(corpus)
report=evaluate(corpus,predictions)
gate=quality_gate(report)
output={"benchmark":report,"quality_gate":gate}
path=ROOT/"artifacts/phase6-step-6.5-benchmark-report.json"
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(output,ensure_ascii=False,indent=2))
if not gate["passed"]: raise SystemExit("Step 6.5 quality gates failed; no construction is enabled.")
