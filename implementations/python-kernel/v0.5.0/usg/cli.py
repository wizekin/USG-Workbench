"""Command line entry point:  python -m usg <command>

  init    create/migrate the database and install the code seal
  status  schema version, seal state, audit-chain state, budgets, constants
  verify  exit 0 only if seal, audit chain and Foundation Package are intact (2 / 3 / 4)
  policy  print the autonomy table (what may happen with no human in the loop)
  reseal  release-time action: re-record the sealed manifest after an upgrade
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import GRAMMAR_VERSION, ONTOLOGY_RELEASE, RULESET_RELEASE, __version__
from .autonomy import seal
from .autonomy.policy import AutonomyPolicy
from .config import BigModelConfig, Config, LocalModelConfig
from .storage.audit import verify_chain
from .foundation.install import install_foundation, verify_foundation
from .storage.database import Database
from .errors import USGError


def _open(path: str) -> Database:
    db = Database(path)
    db.migrate()
    return db


def cmd_init(a) -> int:
    db = _open(a.db)
    rep = install_foundation(db)
    manifest = seal.install_seal(db)
    print(json.dumps({"db": a.db, "schema_version": db.schema_version(), "sealed_modules": len(manifest),
                      "foundation_already_installed": rep.already_installed, "foundation_hash": rep.content_hash[:16]}))
    return 0


def _audit_ok(db: Database) -> tuple[bool, int | None]:
    with db.read() as r:
        return verify_chain(r.query("SELECT * FROM audit_log ORDER BY seq"))


def cmd_status(a) -> int:
    db = _open(a.db)
    cfg = Config()
    rep = seal.verify_seal(db)
    ok, bad = _audit_ok(db)
    big, local = BigModelConfig.from_env(), LocalModelConfig.from_env()
    with db.read() as r:
        entries = int(r.scalar("SELECT COUNT(*) FROM registry_entry", default=0))
        n_concepts = int(r.scalar("SELECT COUNT(*) FROM concept", default=0))
        n_frames = int(r.scalar("SELECT COUNT(*) FROM frame_def", default=0))
        n_kernel = int(r.scalar("SELECT COUNT(*) FROM frame_def WHERE kernel=1", default=0))
        audit_rows = int(r.scalar("SELECT COUNT(*) FROM audit_log", default=0))
        runtime_counts = {table:int(r.scalar('SELECT COUNT(*) FROM '+table,default=0))
                          for table in ('source','candidate','assertion','provisional','learning_candidate')}
        queue_counts = {row[0]:row[1] for row in r.query('SELECT state,COUNT(*) FROM task_queue GROUP BY state')}
    print(json.dumps({
        "version": __version__, "grammar": GRAMMAR_VERSION, "ontology": ONTOLOGY_RELEASE, "ruleset": RULESET_RELEASE,
        "runtime_counts": runtime_counts, "queue_counts": queue_counts,
        "schema_version": db.schema_version(), "seal_ok": rep.ok, "seal_mismatches": list(rep.mismatches),
        "seal_missing": list(rep.missing), "audit_chain_ok": ok, "audit_rows": audit_rows,
        "registry_entries": entries, "foundation_ok": verify_foundation(db), "concepts": n_concepts,
        "frames": n_frames, "kernel_frames": n_kernel, "local_model": local.backend, "big_model_configured": big.enabled,
        "uncalibrated_constants": len(cfg.uncalibrated()),
    }, indent=2))
    return 0


def cmd_verify(a) -> int:
    db = _open(a.db)
    rep = seal.verify_seal(db)
    if not rep.ok:
        print(f"SEAL FAILED mismatches={list(rep.mismatches)} missing={list(rep.missing)}", file=sys.stderr)
        return 2
    ok, bad = _audit_ok(db)
    if not ok:
        print(f"AUDIT CHAIN BROKEN at seq {bad}", file=sys.stderr)
        return 3
    if not verify_foundation(db):
        print("FOUNDATION PACKAGE FAILED VERIFICATION", file=sys.stderr)
        return 4
    from .runtime import USG
    result = USG(db, initialize=False).audit_store()
    if not result["ok"]:
        print(json.dumps(result), file=sys.stderr)
        return 5
    print("OK")
    return 0


def cmd_policy(a) -> int:
    pol = AutonomyPolicy()
    for r in (pol.requirement(x.action) for x in pol.table()):
        print(f"{r.action.value:34s} {r.mode.value:12s} risk={r.risk.name:9s} "
              f"verifiers>={r.min_verifier_classes} canary={'Y' if r.needs_canary else '-'} "
              f"rollback={'Y' if r.needs_rollback_plan else '-'}")
    return 0


def cmd_reseal(a) -> int:
    db = _open(a.db)
    manifest = seal.install_seal(db, reseal=True)
    print(json.dumps({"resealed_modules": len(manifest)}))
    return 0


def _print(value):
    print(json.dumps(value, indent=2, ensure_ascii=False))


def cmd_ingest(a):
    from .runtime import USG
    from .core.records import Anchor
    if a.file and Path(a.file).stat().st_size > Config()["max_source_chars"]*4:
        raise ValueError("source file exceeds the byte budget")
    text = Path(a.file).read_text(encoding="utf-8-sig") if a.file else a.text
    anchor = Anchor(document_date=a.anchor_date) if a.anchor_date else None
    resource=analysis=None
    if a.lexicon:
        from .interpretation.resources import LexicalResource
        from .foundation.builder import build_foundation
        resource=LexicalResource.load(a.lexicon,build_foundation().ontology)
    if a.conllu:
        from .interpretation.dependencies import ConlluAnalysis
        if Path(a.conllu).stat().st_size>8_000_000:raise ValueError('dependency analysis byte budget')
        analysis=ConlluAnalysis(Path(a.conllu).read_text(encoding='utf8'),text)
    with USG(a.db,resource=resource,analysis=analysis) as service:
        result = service.ingest(text, language=a.language, sensitivity=a.sensitivity, anchor=anchor,
                                uri=a.source_uri or (Path(a.file).resolve().as_uri() if a.file else None))
        if a.compact:
            result["units"] = [{k:x[k] for k in ("id", "outcome", "decision", "span")} for x in result["units"]]
        _print(result)
    return 0


def cmd_query(a):
    from .runtime import USG
    with USG(a.db) as s:
        _print(s.query(frame=a.frame, role=a.role, label=a.label, concept=a.concept, view=a.view, limit=a.limit))
    return 0


def cmd_reason(a):
    from .runtime import USG
    from .cognition.reasoner import KernelReasoner
    with USG(a.db) as s:
        _print(KernelReasoner(s).run(view=a.view,scope=a.scope))
    return 0


def cmd_inspect(a):
    from .runtime import USG
    with USG(a.db) as s:
        _print(s.candidate(a.candidate))
    return 0


def cmd_export(a):
    from .runtime import USG
    from .encoding.exchange import export_file
    with USG(a.db) as s:
        if a.format in {'jsonld','turtle','trig'}:
            from .encoding.linked_data import export_linked_data
            _print(export_linked_data(s,a.output,format=a.format,mode=a.mode))
        else:
            _print(export_file(s, a.output, mode=a.mode, format=a.format, codec=a.codec))
    return 0


def cmd_import(a):
    from .runtime import USG
    from .encoding.exchange import import_file
    with USG(a.db) as s:
        _print(import_file(s, a.file))
    return 0


def cmd_benchmark(a):
    from .benchmark.runner import run
    result = run(split=a.split)
    if a.output:
        Path(a.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    _print(result)
    return 0 if result["hard_invariants_pass"] and not result["failures"] else 1


def cmd_learn(a):
    from .runtime import USG
    from .learning.engine import LearningEngine
    from .cognition.worker import Worker
    with USG(a.db) as s:
        s.assert_integrity()
        if a.proposal:
            p = json.loads(Path(a.proposal).read_text(encoding="utf-8"))
            cid = LearningEngine(s.db).propose(p)
        _print(Worker(s).maintenance())
    return 0


def cmd_run(a):
    import time
    from .runtime import USG
    from .cognition.worker import Worker
    if not 1 <= a.interval <= 3600:
        raise ValueError("interval must be 1..3600 seconds")
    resource=None
    if a.lexicon:
        from .interpretation.resources import LexicalResource
        from .foundation.builder import build_foundation
        resource=LexicalResource.load(a.lexicon,build_foundation().ontology)
    with USG(a.db,resource=resource) as s:
        worker = Worker(s)
        while True:
            scanned = worker.scan(a.input, language=a.language)
            result = {"scanned_files": scanned, "jobs": worker.drain(), "maintenance": worker.maintenance()}
            if BigModelConfig.from_env().enabled:
                result["general_issue_analysis"] = worker.analyze_general_issues()
            _print(result)
            if not a.watch:
                break
            time.sleep(a.interval)
    return 0


def cmd_issues(a):
    from .runtime import USG
    from .cognition.worker import Worker
    with USG(a.db) as s:
        if a.analyze:
            _print(Worker(s).analyze_general_issues())
        else:
            with s.db.read() as r:
                _print([dict(x) for x in r.query("SELECT * FROM issue ORDER BY count DESC")])
    return 0


def cmd_backup(a):
    from .runtime import USG
    with USG(a.db) as s:
        _print(s.backup(a.output))
    return 0


def cmd_evaluate(a):
    from .runtime import USG
    from .services import evaluate_files
    with USG(a.db) as service:_print(evaluate_files(service,a.config,a.receipts))
    return 0


def cmd_partition(a):
    from .runtime import USG
    from .services import partition_claims
    with USG(a.db) as service:_print(partition_claims(service,a.directory,a.domain,a.version))
    return 0


def cmd_traceability(a):
    from .conformance import build
    report=build(a.specification)
    if a.output:Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    _print({'parts':len(report['parts']),'sections':len(report['sections']),'requirements':len(report['requirements']),
            'full_conformance':report['full_conformance'],'open_capabilities':report['open_capabilities'],'output':a.output})
    return 0


def cmd_acceptance(a):
    from .acceptance import run
    report=run(full=a.full)
    if a.output:Path(a.output).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    _print(report)
    return 0 if report['passed'] else 1


def cmd_define(a):
    from .runtime import USG
    from .concepts.definitions import Constraint,DefinitionStore
    from .grammar.serialize import node_from_json
    from .encoding.usbf import _json
    raw=Path(a.file).read_bytes()
    if len(raw)>1000000:raise ValueError('definition batch size')
    data=_json(raw)
    allowed={'concept','scope','constraints','expected_version','complete'}
    if not isinstance(data,dict) or set(data)-allowed:raise ValueError('definition batch schema')
    if not isinstance(data.get('constraints'),list) or not 1<=len(data['constraints'])<=100:raise ValueError('constraint list budget')
    constraints=[]
    for item in data['constraints']:
        if not isinstance(item,dict):raise ValueError('constraint schema')
        if set(item)-{'expression','strength','provenance','evidence_id'}:raise ValueError('constraint fields')
        constraints.append(Constraint(node_from_json(item['expression']),item.get('strength','ESSENTIAL'),item.get('provenance','DEFINITIONAL'),item.get('evidence_id')))
    with USG(a.db) as s:
        did=DefinitionStore(s).publish(data['concept'],data['scope'],constraints,
                expected_version=data.get('expected_version',0),complete=data.get('complete',False))
        _print({'definition_id':did,'scope':data['scope'],'world_truth_granted':False})
    return 0


def cmd_upgrade(a):
    from .release import upgrade
    _print(upgrade(a.db,a.backup))
    return 0


def cmd_calibration(a):
    from .runtime import USG
    from .validation.calibration import Calibrator
    with USG(a.db) as s:_print(Calibrator(s.db,s.config).report(a.category))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="usg", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("init", cmd_init), ("status", cmd_status), ("verify", cmd_verify), ("reseal", cmd_reseal)):
        sp = sub.add_parser(name)
        sp.add_argument("--db", default="usg.db")
        sp.set_defaults(fn=fn)
    sp = sub.add_parser("policy")
    sp.set_defaults(fn=cmd_policy)
    def command(name, fn):
        sp = sub.add_parser(name)
        sp.add_argument("--db", default="usg.db")
        sp.set_defaults(fn=fn)
        return sp
    sp = command("ingest", cmd_ingest)
    inputs = sp.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--text")
    inputs.add_argument("--file")
    sp.add_argument("--language", default="en")
    sp.add_argument("--lexicon", help="installed lexical resource JSON")
    sp.add_argument("--conllu", help="offline dependency analysis of this exact source")
    sp.add_argument("--sensitivity", choices=("PUBLIC", "INTERNAL", "SENSITIVE"), default="INTERNAL")
    sp.add_argument("--source-uri")
    sp.add_argument("--anchor-date")
    sp.add_argument("--compact", action="store_true")
    sp = command("query", cmd_query)
    for opt in ("frame", "role", "label", "concept"):
        sp.add_argument("--"+opt)
    sp.add_argument("--view", choices=("source", "trusted", "all"), default="source")
    sp.add_argument("--limit", type=int, default=50)
    sp = command("reason", cmd_reason)
    sp.add_argument("--view", choices=("trusted", "source"), default="trusted")
    sp.add_argument("--scope", help="optional scoped DOMAIN_MODEL definition inference")
    sp = command("inspect", cmd_inspect)
    sp.add_argument("--candidate", type=int, required=True)
    sp = command("export", cmd_export)
    sp.add_argument("--output", required=True)
    sp.add_argument("--mode", choices=("semantic", "reversible"), default="reversible")
    sp.add_argument('--codec', choices=('json','compact','template','auto'), default='compact')
    sp.add_argument("--format", choices=("usbf", "json", "jsonld", "turtle", "trig"), default="usbf")
    sp = command("import", cmd_import)
    sp.add_argument("--file", required=True)
    sp = sub.add_parser("benchmark")
    sp.set_defaults(fn=cmd_benchmark)
    sp.add_argument("--split", choices=("dev", "test"), default="test")
    sp.add_argument("--output")
    sp = command("learn", cmd_learn)
    sp.add_argument("--proposal")
    sp = command("run", cmd_run)
    sp.add_argument("--input", required=True, help="UTF-8 .txt/.md inbox directory")
    sp.add_argument("--language", default="en")
    sp.add_argument("--watch", action="store_true")
    sp.add_argument("--lexicon", help="installed lexical resource JSON for all inbox files")
    sp.add_argument("--interval", type=int, default=30)
    sp = command("issues", cmd_issues)
    sp.add_argument("--analyze", action="store_true", help="optional general analysis; requires opt-in environment")
    sp = command("backup", cmd_backup)
    sp.add_argument("--output", required=True)
    sp=command('evaluate',cmd_evaluate)
    sp.add_argument('--config',required=True)
    sp.add_argument('--receipts',required=True)
    sp=command('partition',cmd_partition)
    sp.add_argument('--directory',required=True)
    sp.add_argument('--domain',default='UNIVERSAL_CORE')
    sp.add_argument('--version',type=int,required=True)
    sp=sub.add_parser('traceability');sp.set_defaults(fn=cmd_traceability)
    sp.add_argument('--specification',default='SPECIFICATION.md');sp.add_argument('--output')
    sp=sub.add_parser('acceptance');sp.set_defaults(fn=cmd_acceptance)
    sp.add_argument('--full',action='store_true');sp.add_argument('--output')
    sp=command('define',cmd_define);sp.add_argument('--file',required=True)
    sp=command('calibration',cmd_calibration);sp.add_argument('--category',required=True)
    sp=command('upgrade',cmd_upgrade);sp.add_argument('--backup',required=True)
    a = p.parse_args(argv)
    try:
        return int(a.fn(a))
    except (USGError, OSError, ValueError, KeyError, TypeError) as ex:
        print(json.dumps({"error": type(ex).__name__, "code": getattr(ex, "code", "USG-INPUT"), "detail": str(ex)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
