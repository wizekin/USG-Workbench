"""End-to-end unattended USG service. All authoritative writes are transactional."""
from __future__ import annotations

import dataclasses
import json
import re
import urllib.parse
from collections import Counter

from . import GRAMMAR_VERSION, ONTOLOGY_RELEASE, __version__
from .autonomy import seal
from .config import Config, LocalModelConfig
from .core.ids import IdSpace, Ref
from .core.kinds import SemKind
from .core.records import Assertion, ContentType, Referent, Source
from .core.spans import Span
from .core.values import (Component, EvalContextKind, IntroducedInKind, Lifecycle, Number, Outcome,
                          Sensitivity, SourceType, TrustTier)
from .errors import InvariantViolation, PolicyDenied, SealViolation, StorageError
from .foundation.builder import build_foundation
from .foundation.install import install_foundation, verify_foundation
from .grammar.node import Node, role_entries, walk
from .grammar.serialize import full_hash, node_from_json, node_to_json, structural_hash
from .grammar.typecheck import Typechecker
from .interpretation.parser import DeterministicInterpreter, Mention
from .models.gateway import LocalGateway
from .security.text import normalize, segment
from .storage.audit import verify_chain
from .storage.database import Database
from .storage.records_store import RecordStore
from .storage.registry import IdRegistry
from .storage.schema import WriterRole as W
from .storage.views import CURRENT_ASSERTION
from .util import canonical_json, sha256_hex
from .validation.certificate import Candidate
from .validation.evidence import EvidenceVector
from .validation.validator import ValidationContext, Validator, route

PIPELINE_VERSION = __version__ + ":rules-1"


class USG:
    def __init__(self, db=":memory:", *, config=None, local=None, initialize=True, resource=None, analysis=None):
        self.db = db if isinstance(db, Database) else Database(str(db))
        self.config = config or Config()
        self.store, self.registry = RecordStore(), IdRegistry()
        self.foundation = build_foundation()
        self.local = local or LocalGateway(LocalModelConfig.from_env())
        self.db.migrate()
        from .validation.calibration import Calibrator
        Calibrator(self.db,self.config).restore()
        if initialize:
            install_foundation(self.db)
            # Do not bless changed code on an existing installation.
            with self.db.read() as r:
                exists = r.scalar("SELECT COUNT(*) FROM sealed_manifest")
            if not exists:
                seal.install_seal(self.db)
        if analysis is None:
            self.parser = DeterministicInterpreter(self.foundation, self.config)
        else:
            from .interpretation.dependencies import DependencyInterpreter
            self.parser = DependencyInterpreter(analysis,self.foundation,self.config)
        self.resource=resource
        self.analysis=analysis
        if resource is not None:self.parser.resolve=resource.resolve
        from .learning.engine import LearningEngine
        self.parser.aliases = LearningEngine(self.db, self.config).active_aliases()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def assert_integrity(self):
        seal.assert_sealed(self.db)
        if not verify_foundation(self.db):
            raise SealViolation("foundation definitions changed")
        with self.db.read() as r:
            ok, bad = verify_chain(r.query("SELECT * FROM audit_log ORDER BY seq"))
        if not ok:
            raise SealViolation(f"audit chain broken at {bad}")

    def pipeline_identity(self):
        from .learning.engine import LearningEngine
        aliases = LearningEngine(self.db, self.config).active_aliases()
        return PIPELINE_VERSION + ":" + sha256_hex(canonical_json([aliases,self.config.snapshot(),self.resource.digest if self.resource else None,self.analysis.digest if self.analysis else None]))[:16]

    def ingest(self, text, *, language="en", uri=None, sensitivity="INTERNAL", anchor=None, trust_tier="STANDARD", allow_local=True):
        self.assert_integrity()
        from .learning.engine import LearningEngine
        self.parser.aliases = LearningEngine(self.db, self.config).active_aliases()
        pipeline_version = self.pipeline_identity()
        if TrustTier(trust_tier) is TrustTier.TRUSTED:
            raise PolicyDenied('ingestion cannot grant installation-only source trust', 'SG-SEC-003')
        source = Source(text, language, SourceType.DOCUMENT, TrustTier(trust_tier), Sensitivity(sensitivity), anchor=anchor, uri=uri)
        # Materialize a bounded list before opening a transaction; fail atomically
        # on oversize input. Original Unicode text remains the source of spans.
        from itertools import islice
        units = list(islice(segment(text, self.config), self.config['max_units_per_source']+1))
        if len(units) > self.config['max_units_per_source']:
            raise InvariantViolation('source exceeds semantic-unit budget', 'SG-SEC-006')
        if not units:
            raise InvariantViolation("source contains no semantic units", "SG-SEC-006")
        normalize(text)  # exercise/retain the offset-preserving normalization contract
        with self.db.write(W.REGISTRY, W.PROVENANCE) as t:
            source = self.store.add_source(t, source)
            # Identical bytes supplied under a different sensitivity may never
            # silently lower the stored classification or raise stored trust.
            source = self.store.get_source(t, source.ref)
        output = []
        for unit in units:
            self.parser.aliases = LearningEngine(self.db, self.config).active_aliases()
            pipeline_version = self.pipeline_identity()
            with self.db.read() as r:
                previous = r.scalar("SELECT candidate_id FROM ingest_ledger WHERE source_id=? AND pipeline_version=? AND unit_start=? AND unit_end=?",
                                    (source.ref.n, pipeline_version, unit.start, unit.end))
            if previous:
                output.append(self.candidate(previous))
                continue
            discourse = self._discourse(source, unit.start)
            interpreted = self.parser.interpret(source, unit, discourse=discourse)
            candidate, mentions = interpreted.candidate, interpreted.mentions
            mention_map = {m.handle: m for m in (*discourse, *mentions)}
            checker = Typechecker(self.foundation.frames, config=self.config,
                                  classes_of=lambda r: [mention_map[r].concept] if r in mention_map else ())
            from .validation.contextual import ContextualValidator
            contextual = ContextualValidator(tuple(mention_map.values()), self.parser.resolve)
            validator = Validator(ValidationContext(checker, contextual=contextual, resolves_ref=lambda r: r in mention_map,
                                                   surface_of=lambda r: [mention_map[r].label] if r in mention_map else []))
            report = validator.validate(candidate)
            # Optional local analysis is advisory. It cannot turn an unsupported
            # parse into a committed claim or bypass the independent validator.
            local_advice = None
            if candidate.certificate.outcome is Outcome.UNRESOLVED and allow_local and self.local.config.backend != "none":
                result = self.local.choose("FRAME_SELECTION", source.span_text(unit), self.foundation.frames.kernel_frames())
                local_advice = {"ok": result.ok, "choice": result.value, "reason": result.reason}
            admitted = candidate.certificate.outcome is not Outcome.UNRESOLVED and not report.failed()
            reason = route(report).route.value if admitted else "ABSTAIN" if candidate.certificate.outcome is Outcome.UNRESOLVED else "REJECT"
            # Each unit is atomic: candidate, evidence, mapped IDs, expression,
            # assertion, index, history and ingest checkpoint commit together.
            with self.db.write(W.REGISTRY, W.CANDIDATE_STORE, W.PROVENANCE, W.HISTORY, W.EVALUATION) as t:
                key = f"{source.ref}:{pipeline_version}:{unit.start}:{unit.end}"
                # Recheck under the write lock for concurrent/retried controllers.
                existing = t.scalar("SELECT candidate_id FROM candidate WHERE dedup_key=?", (key,))
                if existing:
                    cid = existing
                else:
                    cref = self.registry.allocate(t, IdSpace.CANDIDATE, record_kind="Interpretation")
                    cid = cref.n
                    payload = {**candidate.to_json(), "mentions": [dataclasses.asdict(m) for m in mentions], "local_advice": local_advice,
                               "pipeline_version": pipeline_version, "runtime_aliases": dict(self.parser.aliases), "lexical_resource": self.resource.body if self.resource else None, "dependency_analysis_hash": self.analysis.digest if self.analysis else None,
                               "dependency_analysis": self.analysis.body if self.analysis else None,
                               "replay_profile":"RULES-0.4", "runtime_config":self.config.snapshot(),
                               "discourse":[dataclasses.asdict(m) for m in discourse]}
                    t.execute("INSERT INTO candidate VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                              (cid, source.ref.n, unit.start, unit.end, key, canonical_json(payload), canonical_json(report.to_json()),
                               candidate.certificate.outcome.value, "VALIDATED_FORMALLY" if admitted else "DEFERRED", reason, self.db.clock.now()))
                    origin = self._origin(source)
                    evidence = EvidenceVector(source.text_hash, (unit.start, unit.end), "DETERMINISTIC_RULES", report.aggregate.value,
                                              (origin,), tuple(interpreted.issues) + tuple(x.detail for x in report.results if x.result.value == "UNCERTAIN"))
                    eref = self.registry.allocate(t, IdSpace.EVIDENCE, record_kind="EvidenceVector")
                    evidence_body = canonical_json(evidence.to_json())
                    t.execute("INSERT INTO evidence VALUES(?,?,?,?)", (eref.n, cid, evidence_body, sha256_hex(evidence_body)))
                    if admitted:
                        self._store_claim(t, source, candidate, mentions, eref, discourse=discourse)
                    for word in interpreted.unknown_words:
                        self._provisional(t, source, word)
                    for code in set(interpreted.issues) | set(report.codes()):
                        t.execute("INSERT INTO issue(code,count,last_seen) VALUES(?,1,?) ON CONFLICT(code) DO UPDATE SET count=count+1,last_seen=excluded.last_seen",
                                  (code, self.db.clock.now()))
                    t.execute("INSERT INTO ingest_ledger VALUES(?,?,?,?,?)", (source.ref.n, pipeline_version, unit.start, unit.end, cid))
                    t.audit(Component.CONTROLLER, "INGEST_UNIT", str(cref), canonical_json({"outcome": candidate.certificate.outcome.value, "decision": reason}))
                    t.execute("INSERT INTO process_history(at,task_key,event,body) VALUES(?,?,?,?)",
                              (self.db.clock.now(), key, "INGEST", canonical_json({"candidate_id": cid, "decision": reason})))
            output.append(self.candidate(cid))
            self._observe_canaries(source, unit)
        return {"source": str(source.ref), "units": output, "counts": dict(Counter(x["outcome"] for x in output)), "model_required": False}

    def _observe_canaries(self, source, unit):
        from .learning.engine import LearningEngine
        from .learning.dsl import RuleProposal
        from .benchmark.corpus import semantic_fingerprint
        with self.db.read() as r:
            rows = r.query("SELECT b.bundle_id,c.payload FROM promotion_bundle b JOIN learning_candidate c USING(candidate_id) WHERE b.state IN ('CANARY','ACTIVE') AND c.veto IS NULL ORDER BY CASE b.state WHEN 'CANARY' THEN 0 ELSE 1 END,b.bundle_id LIMIT 100")
        learning = LearningEngine(self.db, self.config)
        for row in rows:
            p = RuleProposal.from_json(json.loads(row["payload"]))
            if not re.search(r'\b'+re.escape(p.trigger)+r'\b',source.span_text(unit),re.I):continue
            trial = DeterministicInterpreter(self.foundation, self.config, {**self.parser.aliases, p.trigger:p.equivalent_verb})
            baseline_aliases = {k:v for k,v in self.parser.aliases.items() if k != p.trigger}
            baseline = DeterministicInterpreter(self.foundation, self.config, baseline_aliases)
            discourse = self._discourse(source, unit.start)
            original = baseline.interpret(source, unit, discourse=discourse)
            shadow = trial.interpret(source, unit, discourse=discourse)
            # Existing resolved/ambiguous readings must never change. On new
            # forms, conservatively count only successfully validated trials.
            regression = original.candidate.certificate.outcome is not Outcome.UNRESOLVED and semantic_fingerprint(original) != semantic_fingerprint(shadow)
            if original.candidate.certificate.outcome is Outcome.UNRESOLVED:
                if shadow.candidate.certificate.outcome is Outcome.UNRESOLVED:
                    continue
                m = {x.handle:x for x in (*discourse, *shadow.mentions)}
                valid = Validator(ValidationContext(Typechecker(self.foundation.frames, classes_of=lambda r:[m[r].concept] if r in m else ()),
                                 resolves_ref=lambda r:r in m, surface_of=lambda r:[m[r].label] if r in m else [])).validate(shadow.candidate)
                regression = bool(valid.failed())
            learning.observe_canary(row["bundle_id"], error=regression, observation_key=sha256_hex(source.text_hash+str(unit.start)+str(unit.end)))

    def _discourse(self, source, before):
        with self.db.read() as r:
            rows = r.query("SELECT rf.*,c.canonical_label FROM referent rf JOIN referent_class rc USING(referent_id) JOIN concept c ON c.concept_id=rc.concept_id WHERE rf.source_id=? AND rf.span_end<=? AND EXISTS (SELECT 1 FROM assertion_ref usage JOIN assertion a USING(assertion_id) WHERE usage.referent_id=rf.referent_id AND "+CURRENT_ASSERTION+") ORDER BY rf.referent_id DESC LIMIT ?",
                           (source.ref.n, before, self.config["workspace_capacity"]))
        return tuple(Mention(f"REFERENT:{x['referent_id']}", source.text[x["span_start"]:x["span_end"]], x["canonical_label"],
                             (x["span_start"],x["span_end"]),x["number"],json.loads(x["cardinality"]) if x["cardinality"] else None,
                             x["introduced_kind"]) for x in rows)

    def _store_claim(self, t, source, candidate, mentions, evidence, *, discourse=()):
        mapping = {}
        # Quantifier-bound variables are not particular discourse individuals.
        used_handles = {n.get("ref") for _, n in walk(candidate.expression) if n.op == "REF"}
        mentions = tuple(m for m in mentions if m.handle in used_handles)
        for m in mentions:
            concept = t.scalar("SELECT concept_id FROM concept WHERE canonical_label=?", (m.concept,))
            if concept is None:
                raise InvariantViolation("unknown class", "SG-INT-001")
            # Non-world introduction is recorded on the expression context as
            # well as on each referent; it never entails real-world existence.
            from .core.records import IntroducedIn
            context_ref = None
            intro = IntroducedIn()
            if m.introduced_in != "WORLD":
                context_ref = self.registry.allocate(t, IdSpace.NODE, record_kind="IntroductionContext")
                context = {"op": "INTRODUCTION_CONTEXT", "candidate_hash": candidate.content_hash(), "kind": m.introduced_in}
                b = canonical_json(context)
                t.execute("INSERT INTO expression VALUES(?,?,?,?,?,?)", (context_ref.n, b, sha256_hex(b), sha256_hex(b), GRAMMAR_VERSION, ONTOLOGY_RELEASE))
                intro = IntroducedIn(IntroducedInKind(m.introduced_in), context_ref)
            reusable=[]
            if m.introduced_in=='WORLD':
                reusable=t.query("SELECT DISTINCT rf.referent_id FROM referent rf JOIN referent_class rc USING(referent_id) WHERE rf.source_id=? AND rf.span_start=? AND rf.span_end=? AND rf.introduced_kind='WORLD' AND rf.number=? AND rc.concept_id=? AND rf.cardinality IS ?",(source.ref.n,m.span[0],m.span[1],m.number,concept,canonical_json(m.cardinality) if m.cardinality is not None else None))
            if len(reusable)==1:
                mapping[m.handle]=str(Ref(IdSpace.REFERENT,reusable[0][0]))
                continue
            mapped = self.store.add_referent(t, Referent(SemKind.ENTITY, (Ref(IdSpace.CONCEPT, concept),), Number(m.number),
                                                         cardinality=m.cardinality, source=source.ref, span=Span(*m.span), introduced_in=intro))
            mapping[m.handle] = str(mapped)
        def map_node(n):
            params = n.params_dict()
            if n.op == "REF":
                params["ref"] = mapping.get(params["ref"], params["ref"])
                if not params["ref"].startswith("REFERENT:"):
                    raise InvariantViolation("unresolved workspace handle", "SG-FND-001")
            return Node(n.op, tuple(map_node(a) for a in n.args), params, n.ann)
        expression = map_node(candidate.expression)
        nref = self.registry.allocate(t, IdSpace.NODE, record_kind="Expression")
        t.execute("INSERT INTO expression VALUES(?,?,?,?,?,?)", (nref.n, canonical_json(node_to_json(expression)), structural_hash(expression), full_hash(expression), GRAMMAR_VERSION, ONTOLOGY_RELEASE))
        assertion = Assertion.new(ContentType.NODE, nref, candidate.declared_origin, source=source.ref, evidence=evidence,
                                  lifecycle=Lifecycle.STRUCTURED, eval_context=EvalContextKind.FICTION if source.genre == "fiction" else EvalContextKind.WORLD)
        aref = self.store.add_assertion(t, assertion)
        self.store.set_assertion_stage(t, aref, Lifecycle.VALIDATED_FORMALLY, Component.VALIDATOR)
        for rid in sorted({n.get('ref') for _,n in walk(expression) if n.op=='REF'}):
            t.execute('INSERT OR IGNORE INTO assertion_ref VALUES(?,?)',(aref.n,Ref.parse(rid).n))
        from .validation.contextual import index_claim
        index_claim(t, aref.n, expression, assertion.eval_context.value, None, None)
        for bundle in t.query("SELECT b.bundle_id,c.payload FROM promotion_bundle b JOIN learning_candidate c USING(candidate_id) WHERE b.state='ACTIVE' AND c.action='INTERP_RULE'"):
            trigger=json.loads(bundle['payload'])['trigger']
            if re.search(r'\b'+re.escape(trigger)+r'\b',source.span_text(candidate.unit_span),re.I):
                t.execute('INSERT OR IGNORE INTO rule_claim_dependency VALUES(?,?)',(aref.n,bundle['bundle_id']))
        by_ref = {mapping[m.handle]: m for m in mentions}
        by_ref.update({m.handle:m for m in discourse})
        for _, n in walk(expression):
            if n.op != "APPLY":
                continue
            for role, _, filler in role_entries(n):
                if filler.op == "REF" and filler.get("ref") in by_ref:
                    m = by_ref[filler.get("ref")]
                    t.execute("INSERT OR IGNORE INTO claim_index VALUES(?,?,?,?,?,?)", (aref.n, n.get("frame"), role, Ref.parse(filler.get("ref")).n, m.label.casefold(), m.concept))

    def _provisional(self, t, source, word):
        if t.scalar("SELECT COUNT(*) FROM provisional WHERE status='ACTIVE'") >= self.config["gen_max_candidates"]:
            return
        context = source.text_hash
        if t.one("SELECT 1 FROM provisional WHERE language=? AND form=? AND context=?", (source.language, word, context)):
            return
        p = self.registry.allocate(t, IdSpace.PROVISIONAL, record_kind="ProvisionalConcept")
        t.execute("INSERT INTO provisional VALUES(?,?,?,?,?,'ACTIVE')", (p.n, source.language, word, context,
                  self.db.clock.now() + 86400*self.config["provisional_concept_ttl_days"]))

    @staticmethod
    def _origin(source):
        host = urllib.parse.urlsplit(source.uri or "").hostname
        return "host:" + host.casefold() if host else "content:" + sha256_hex(" ".join(re.findall(r"\w+", source.text.casefold())))

    def candidate(self, candidate_id):
        with self.db.read() as r:
            row = r.one("SELECT * FROM candidate WHERE candidate_id=?", (candidate_id,))
            if row is None:
                raise StorageError("unknown candidate")
        return {"id": row["candidate_id"], "source": f"SOURCE:{row['source_id']}", "span": [row["unit_start"], row["unit_end"]],
                "outcome": row["outcome"], "lifecycle": row["lifecycle"], "decision": row["reason"],
                "validation": json.loads(row["report"]), **json.loads(row["payload"])}

    def query(self, *, frame=None, role=None, label=None, concept=None, view="source", limit=50):
        if view not in {"source", "trusted", "all"} or not 1 <= limit <= 1000:
            raise ValueError("invalid query view/limit")
        clauses, params = ["a.content_space='NODE'"], []
        if view != "all":clauses.append(CURRENT_ASSERTION)
        if view == "trusted":
            clauses.extend(["a.epistemic_status='VERIFIED'", "a.commitment='AUTHOR'", "a.eval_context IN ('WORLD','DOMAIN_MODEL')", "a.lifecycle='PROMOTED'"])
        elif view == "source":
            clauses.append("a.lifecycle NOT IN ('DEFERRED','REJECTED','DEPRECATED')")
            clauses.append("a.origin IN ('SOURCE_TEXT','GRAMMATICAL')")
        if any(x is not None for x in (frame, role, label, concept)):
            filters = ["c.assertion_id=a.assertion_id"]
            for col, val in (("frame", frame), ("role", role), ("label", label.casefold() if label else label), ("concept", concept)):
                if val is not None:
                    filters.append(f"c.{col}=?")
                    params.append(val)
            clauses.append("EXISTS(SELECT 1 FROM claim_index c WHERE " + " AND ".join(filters) + ")")
        with self.db.read() as r:
            rows = r.query("SELECT a.*,e.body,s.language FROM assertion a JOIN expression e ON e.node_id=a.content_id JOIN source s USING(source_id) WHERE " +
                           " AND ".join(clauses) + " ORDER BY a.assertion_id LIMIT ?", (*params, limit))
        return [{"assertion": f"ASSERTION:{x['assertion_id']}", "source": f"SOURCE:{x['source_id']}", "epistemic_status": x["epistemic_status"],
                 "lifecycle": x["lifecycle"], "expression": json.loads(x["body"]), "language": x["language"]} for x in rows]

    def audit_store(self):
        self.assert_integrity()
        errors, checked = [], 0
        with self.db.read() as r:
            rows = r.query("SELECT a.*,e.body,e.full_hash AS expression_hash FROM assertion a JOIN expression e ON e.node_id=a.content_id WHERE a.content_space='NODE'")
            for row in rows:
                checked += 1
                e = node_from_json(json.loads(row["body"]))
                def classes(rid):
                    return [x[0] for x in r.query("SELECT c.canonical_label FROM referent_class rc JOIN concept c ON c.concept_id=rc.concept_id WHERE rc.referent_id=?", (Ref.parse(rid).n,))]
                tr = Typechecker(self.foundation.frames, config=self.config, classes_of=classes).check(e)
                if tr.issues or full_hash(e) != row["expression_hash"] or row["evidence_id"] is None:
                    errors.append(row["assertion_id"])
                if any(n.op == "REF" and str(n.get("ref")).startswith("W:") for _, n in walk(e)):
                    errors.append(row["assertion_id"])
            for row in r.query("SELECT body,content_hash FROM evidence"):
                if sha256_hex(row["body"]) != row["content_hash"]:
                    errors.append("evidence_hash")
            for row in r.query("SELECT rf.referent_id,rf.span_start,rf.span_end,s.text_len FROM referent rf JOIN source s USING(source_id)"):
                if row["span_start"] is not None and not 0 <= row["span_start"] < row["span_end"] <= row["text_len"]:
                    errors.append(f"referent_span:{row['referent_id']}")
            for row in r.query("SELECT c.candidate_id,c.payload,c.unit_start,c.unit_end,s.text_len FROM candidate c JOIN source s USING(source_id)"):
                if not 0 <= row["unit_start"] < row["unit_end"] <= row["text_len"]:
                    errors.append(f"unit_span:{row['candidate_id']}")
                payload = json.loads(row["payload"])
                full_row = r.one("SELECT source_id,lifecycle FROM candidate WHERE candidate_id=?", (row['candidate_id'],))
                source = self.store.get_source(r, Ref(IdSpace.SOURCE, full_row['source_id']))
                if full_row['lifecycle'] == 'VALIDATED_FORMALLY':
                    candidate = Candidate.from_json(source, payload)
                    known = {m['handle']:m for m in payload.get('mentions',())}
                    def audit_resolves(handle):
                        if handle in known:
                            return True
                        try:
                            return self.registry.get(r, Ref.parse(handle)) is not None
                        except InvariantViolation:
                            return False
                    def audit_classes(handle):
                        if handle in known:
                            return [known[handle]['concept']]
                        if not handle.startswith('REFERENT:'):
                            return []
                        return [x[0] for x in r.query("SELECT c.canonical_label FROM referent_class rc JOIN concept c ON c.concept_id=rc.concept_id WHERE rc.referent_id=?", (Ref.parse(handle).n,))]
                    validation = Validator(ValidationContext(Typechecker(self.foundation.frames, config=self.config, classes_of=audit_classes),
                                          resolves_ref=audit_resolves, surface_of=lambda handle:[known[handle]['label']] if handle in known else [])).validate(candidate)
                    if validation.failed():
                        errors.append({'candidate':row['candidate_id'],'checks':validation.codes()})
                    if payload.get('replay_profile')=='RULES-0.4':
                        try:
                            replay_config=Config(payload['runtime_config'])
                            if payload.get('dependency_analysis') is not None:
                                from .interpretation.dependencies import ConlluAnalysis,DependencyInterpreter
                                analysis=ConlluAnalysis(payload['dependency_analysis'],source.text)
                                if analysis.digest!=payload['dependency_analysis_hash']:raise ValueError('analysis digest')
                                replay_parser=DependencyInterpreter(analysis,self.foundation,replay_config,payload['runtime_aliases'])
                            else:
                                replay_parser=DeterministicInterpreter(self.foundation,replay_config,payload['runtime_aliases'])
                            if payload.get('lexical_resource') is not None:
                                from .interpretation.resources import LexicalResource
                                replay_parser.resolve=LexicalResource(payload['lexical_resource'],self.foundation.ontology).resolve
                            replay_discourse=tuple(Mention(**m) for m in payload.get('discourse',()))
                            replayed=replay_parser.interpret(source,candidate.unit_span,discourse=replay_discourse)
                            if full_hash(replayed.candidate.expression)!=full_hash(candidate.expression) or replayed.candidate.certificate.content_hash()!=candidate.certificate.content_hash():
                                errors.append({'candidate':row['candidate_id'],'checks':['DETERMINISTIC_REPLAY']})
                        except (ValueError,KeyError,TypeError,InvariantViolation):
                            errors.append({'candidate':row['candidate_id'],'checks':['REPLAY_INPUT_INVALID']})
                for step in payload["certificate"]["steps"]:
                    for a, b in step["spans"]:
                        if not row["unit_start"] <= a < b <= row["unit_end"]:
                            errors.append(f"certificate_span:{row['candidate_id']}")
        from .concepts.definitions import DefinitionStore
        definitions=DefinitionStore(self).audit()
        if not definitions['ok']:errors.append({'definitions':definitions['errors']})
        return {"ok": not errors and self.db.integrity_check(), "checked_assertions": checked, 'checked_definitions':definitions['checked_definitions'], "errors": errors}

    def backup(self, path):
        import sqlite3
        from pathlib import Path
        if str(Path(path).resolve()) == str(Path(self.db.path).resolve()):
            raise ValueError("backup must use a different file")
        self.assert_integrity()
        if Path(path).exists():
            raise FileExistsError(path)
        with self.db._lock, sqlite3.connect(str(path)) as destination:
            self.db.raw_unsafe_connection().backup(destination)
        return {"backup": str(Path(path).resolve()), "integrity_checked": True}
