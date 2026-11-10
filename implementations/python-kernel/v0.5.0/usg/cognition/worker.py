"""Autonomous local inbox worker. Jobs survive restarts and failures are bounded."""
from __future__ import annotations

import json
from pathlib import Path

from .. import __version__
from ..autonomy.policy import BigModelTask
from ..core.records import Source
from ..core.spans import Span
from ..core.values import Outcome
from ..errors import USGError
from ..learning.dsl import RuleProposal
from ..learning.engine import LearningEngine
from ..models.gateway import BigGateway
from ..storage.schema import WriterRole
from ..util import sha256_hex
from .controller import TaskQueue, ResourceGovernor
from .resources import decide, snapshot


class Worker:
    def __init__(self, service):
        self.service = service
        self.queue = TaskQueue(service.db)
        self.learning = LearningEngine(service.db, service.config)

    def scan(self, directory, language="en"):
        root = Path(directory).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("input must be a directory")
        count = 0
        from itertools import islice
        for file in sorted(islice(root.rglob("*"),5000)):
            if not file.is_file() or file.suffix.casefold() not in {".txt", ".md"} or file.is_symlink():
                continue
            if not file.resolve().is_relative_to(root) or file.stat().st_size > self.service.config["max_source_chars"]*4:
                continue
            text = file.read_text(encoding="utf-8-sig")
            if not text.strip() or len(text) > self.service.config["max_source_chars"]:
                continue
            key = sha256_hex(self.service.pipeline_identity()+language+str(file)+text)
            self.queue.enqueue(key, "INGEST", {"text": text, "language": language, "uri": file.as_uri()})
            count += 1
        return count

    def drain(self, max_jobs=1000):
        done, failed = 0, 0
        for _ in range(max_jobs):
            measured=snapshot(Path(self.service.db.path).parent if self.service.db.path!=':memory:' else '.')
            mode=decide(measured,ResourceGovernor(self.service.config))
            if mode=='DEFER':break
            task = self.queue.claim(lease_seconds=3600)
            if task is None:
                break
            try:
                if task.kind == "INGEST":
                    payload={**task.payload,'allow_local':mode!='RULES_ONLY'}
                    if isinstance(payload.get('anchor'),dict):
                        from ..core.records import Anchor
                        payload['anchor']=Anchor(**payload['anchor'])
                    result = self.service.ingest(**payload)
                elif task.kind == "LEARN":
                    result = self.learning.discover()
                else:
                    result = self.service.audit_store()
                self.queue.finish(task, {"ok": True, "source": result.get("source"), "counts": result.get("counts")})
                done += 1
            except (USGError, OSError, ValueError) as ex:
                self.queue.finish(task, error=type(ex).__name__ + ": " + str(ex))
                failed += 1
        return {"completed": done, "failed_attempts": failed}

    def maintenance(self):
        self.service.assert_integrity()
        from ..learning.semantic import SemanticLearner
        semantic=SemanticLearner(self.service)
        generated_aliases=semantic.discover_aliases()
        hypotheses=semantic.mine()
        reprocessing=self.reprocess_invalidated()
        patterns = self.learning.discover()
        with self.service.db.read() as r:
            proposals = r.query("SELECT candidate_id FROM learning_candidate WHERE action='INTERP_RULE' AND stage='STRUCTURED' ORDER BY candidate_id LIMIT 5")
        staged = []
        for row in proposals:
            staged.append(self.learning.stage_rule(row[0]))
        from ..services import automatic_evaluation
        evaluations=automatic_evaluation(self.service)
        return {"generated_aliases":generated_aliases,"semantic_learning":hypotheses,"reprocessing_jobs":reprocessing,"evidence_evaluation":evaluations,"patterns": patterns, "staged_rules": staged, "sources_past_probation": self.probation(), "audit": self.service.audit_store()}

    def reprocess_invalidated(self):
        from ..core.ids import IdSpace, Ref
        with self.service.db.read() as r:
            rows=r.query("SELECT DISTINCT a.source_id FROM assertion a JOIN rule_claim_dependency d USING(assertion_id) JOIN promotion_bundle b USING(bundle_id) WHERE b.state='ROLLED_BACK' AND a.lifecycle IN ('DEFERRED','DEPRECATED') LIMIT 100")
            sources=[self.service.store.get_source(r,Ref(IdSpace.SOURCE,x[0])) for x in rows]
        for source in sources:
            key='reprocess:'+self.service.pipeline_identity()+':'+str(source.ref)
            self.queue.enqueue(key,'INGEST',{'text':source.text,'language':source.language,'uri':source.uri,
                'sensitivity':source.sensitivity.value,'anchor':source.anchor.to_json() if source.anchor else None,'trust_tier':source.trust_tier.value if source.trust_tier.value!='TRUSTED' else 'STANDARD'})
        return len(sources)

    def probation(self):
        from ..core.ids import IdSpace, Ref
        from ..core.values import TrustTier
        promoted = 0
        with self.service.db.write(WriterRole.PROVENANCE) as t:
            rows = t.query("SELECT source_id FROM source WHERE trust_tier='QUARANTINE' ORDER BY source_id LIMIT 100")
            for row in rows:
                failed = t.scalar("SELECT COUNT(*) FROM candidate WHERE source_id=? AND lifecycle<>'VALIDATED_FORMALLY'", (row[0],))
                clean = t.scalar("SELECT COUNT(*) FROM (SELECT DISTINCT unit_start,unit_end FROM candidate WHERE source_id=? AND lifecycle='VALIDATED_FORMALLY')", (row[0],))
                if not failed and clean >= self.service.config['probation_clean_units']:
                    self.service.store.set_trust_tier(t, Ref(IdSpace.SOURCE,row[0]),TrustTier.STANDARD,probation_passed=True)
                    promoted += 1
        return promoted

    def analyze_general_issues(self):
        from ..util import canonical_json
        with self.service.db.read() as r:
            pending = r.one("SELECT * FROM general_rule_request WHERE state='PENDING' ORDER BY created_at LIMIT 1")
            counts = {x[0]: x[1] for x in r.query("SELECT code,count FROM issue ORDER BY count DESC LIMIT 40")}
        gateway = BigGateway(self.service.db)
        if pending:
            result = gateway.analyze(BigModelTask.GENERAL_RULE_PROPOSAL, json.loads(pending['digest']))
            if result.ok:
                cid = self.learning.propose(result.value)
                with self.service.db.write(WriterRole.HISTORY) as t:
                    t.execute("UPDATE general_rule_request SET state='DONE',candidate_id=? WHERE digest_hash=?", (cid,pending['digest_hash']))
            return {"ok": result.ok, "reason": result.reason, "task": "GENERAL_RULE_PROPOSAL"}
        result = gateway.analyze(BigModelTask.GENERAL_ISSUE_ANALYSIS, counts)
        if result.ok:
            with self.service.db.write(WriterRole.HISTORY) as t:
                for finding in result.value["findings"]:
                    t.execute("UPDATE issue SET risk_floor=MAX(risk_floor,3) WHERE code=?", (finding["code"],))
                    if finding['effect'] == 'REQUEST_RULE_PROPOSAL':
                        digest = canonical_json(counts)
                        t.execute("INSERT OR IGNORE INTO general_rule_request VALUES(?,?,'PENDING',?,NULL)",
                                  (sha256_hex(digest),digest,self.service.db.clock.now()))
        return {"ok": result.ok, "reason": result.reason, "result": result.value}
