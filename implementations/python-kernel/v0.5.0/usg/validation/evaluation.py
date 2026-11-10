"""Policy-driven truth evaluation using independently authenticated attestations.

Keys and policies are installation configuration; extracted documents cannot
add authorities. A signature authenticates an authority, not universal truth.
Policies remain responsible for the chosen domain's evidence standard.
"""
import hashlib
import hmac
import json
import math
from dataclasses import asdict,dataclass

from ..core.ids import Ref
from ..core.values import Component,EpistemicStatus,Lifecycle
from ..errors import PolicyDenied
from ..storage.schema import WriterRole as W
from ..util import canonical_json


@dataclass(frozen=True)
class EvidencePolicy:
    policy_id: str
    version: int=1
    min_origins: int=2
    max_age_seconds: int=86400
    allowed_trust_tiers: tuple[str,...]=('STANDARD','TRUSTED')
    allowed_contexts: tuple[str,...]=('WORLD','DOMAIN_MODEL')

    def __post_init__(self):
        if not self.policy_id or type(self.version) is not int or self.version<1 or type(self.min_origins) is not int or self.min_origins<2 or not 0<self.max_age_seconds<=31536000:
            raise ValueError('invalid evidence policy')


def sign_attestation(secret, *, authority,origin,claim_hash,verdict,issued_at,context='WORLD'):
    body=dict(authority=authority,origin=origin,claim_hash=claim_hash,verdict=verdict,issued_at=issued_at,context=context)
    return {**body,'signature':hmac.new(secret,canonical_json(body).encode('utf8'),hashlib.sha256).hexdigest()}


class EvaluationProcess:
    def __init__(self,service,policy,authorities):
        self.service,self.policy=service,policy
        # authority -> (independence cluster, key bytes). Claimed origins in
        # receipts cannot create independence; the installed cluster is binding.
        self.authorities=dict(authorities)
        if any(not isinstance(v,tuple) or len(v)!=2 or not v[0] or not isinstance(v[1],bytes) or len(v[1])<16 for v in self.authorities.values()):
            raise ValueError('authority keys need independent clusters and >=16 bytes')
        key_clusters={}
        for cluster,key in self.authorities.values():
            if key in key_clusters and key_clusters[key]!=cluster:
                raise ValueError('shared signing key cannot establish independent origins')
            key_clusters[key]=cluster

    def evaluate(self,assertion_id,receipts):
        if type(assertion_id) is not int or assertion_id<=0:raise ValueError('assertion ID')
        s,p=self.service,self.policy
        s.assert_integrity()
        from .contextual import ConflictIndex
        conflicts=ConflictIndex(s)
        conflicts.rebuild()
        with s.db.read() as r:
            row=r.one("SELECT a.*,e.full_hash,s.trust_tier FROM assertion a JOIN expression e ON a.content_space='NODE' AND e.node_id=a.content_id JOIN source s USING(source_id) WHERE assertion_id=?",(assertion_id,))
        if row is None:raise ValueError('unknown assertion')
        from ..storage.views import CURRENT_ASSERTION
        with s.db.read() as r:
            active=r.one('SELECT a.assertion_id FROM assertion a WHERE a.assertion_id=? AND '+CURRENT_ASSERTION,(assertion_id,))
        if active is None:return {'decision':'DEFERRED','reason':'SUPERSEDED_OR_INACTIVE_CLAIM'}
        if row['lifecycle'] in {'DEFERRED','REJECTED','DEPRECATED'}:return {'decision':'DEFERRED','reason':'INACTIVE_CLAIM'}
        if row['commitment']!='AUTHOR' or row['eval_context'] not in p.allowed_contexts or row['trust_tier'] not in p.allowed_trust_tiers:
            return {'decision':'DEFERRED','reason':'POLICY_SCOPE'}
        if not s.audit_store()['ok']:raise PolicyDenied('store audit failed')
        from ..grammar.serialize import node_from_json
        from ..grammar.node import walk
        with s.db.read() as r:
            body=r.scalar('SELECT body FROM expression WHERE node_id=?',(row['content_id'],))
        if any(n.op in {'ALT','ERROR'} for _,n in walk(node_from_json(json.loads(body)))):
            return {'decision':'DEFERRED','reason':'UNRESOLVED_INTERPRETATION'}
        if not isinstance(receipts,list) or len(receipts)>1000:raise ValueError('receipt budget')
        yes,no=set(),set()
        for receipt in receipts:
            if not isinstance(receipt,dict) or set(receipt)!={'authority','origin','claim_hash','verdict','issued_at','context','signature'}:continue
            if not isinstance(receipt['authority'],str):continue
            authority=self.authorities.get(receipt['authority'])
            if authority is None:continue
            origin,key=authority
            if receipt['origin']!=origin or receipt['claim_hash']!=row['full_hash'] or receipt['context']!=row['eval_context']:continue
            at=receipt['issued_at']
            if type(at) not in (float,int) or not math.isfinite(at) or not 0<=s.db.clock.now()-at<=p.max_age_seconds:continue
            body={k:v for k,v in receipt.items() if k!='signature'}
            expected=hmac.new(key,canonical_json(body).encode('utf8'),hashlib.sha256).hexdigest()
            if not isinstance(receipt['signature'],str) or not hmac.compare_digest(expected,receipt['signature']):continue
            if receipt['verdict']=='SUPPORT':yes.add(origin)
            elif receipt['verdict']=='CONTRADICT':no.add(origin)
        status='DISPUTED' if no else 'VERIFIED' if len(yes)>=p.min_origins else None
        if status is None:return {'decision':'DEFERRED','reason':'INSUFFICIENT_AUTHENTICATED_ORIGINS','origins':len(yes)}
        if status=='VERIFIED':
            from ..autonomy.panel import AutomatedPanel,Verdict
            from ..autonomy.policy import ActionClass,VerifierClass as VC
            checks={VC.DETERMINISTIC_REPLAY:s.audit_store()['ok'],
                    VC.INDEPENDENT_METHOD:len(yes)>=p.min_origins, VC.COUNTEREXAMPLE:not no}
            verifiers={cls:(lambda candidate,cls=cls,ok=ok:Verdict(cls,ok,hashlib.sha256(canonical_json([row['full_hash'],cls.value,sorted(yes),sorted(no)]).encode()).hexdigest(),hard_failure=not ok)) for cls,ok in checks.items()}
            panel=AutomatedPanel(verifiers).evaluate(ActionClass.ASSERTION_PROMOTE_TRUSTED,row['full_hash'],origins=len(yes),rollback_plan=True)
            if not panel.approved:return {'decision':'DEFERRED','reason':panel.reason}
        with s.db.write(W.EVALUATION,W.PROMOTION,W.CANDIDATE_STORE) as t:
            current=t.one('SELECT * FROM assertion WHERE assertion_id=?',(assertion_id,))
            current_hash=t.scalar('SELECT full_hash FROM expression WHERE node_id=?',(current['content_id'],))
            if current_hash!=row['full_hash']:raise PolicyDenied('claim changed during evaluation')
            current_tier=t.scalar('SELECT trust_tier FROM source WHERE source_id=?',(current['source_id'],))
            if current_tier not in p.allowed_trust_tiers or current['eval_context'] not in p.allowed_contexts or current['commitment']!='AUTHOR':
                raise PolicyDenied('evaluation scope changed')
            if not t.one('SELECT a.assertion_id FROM assertion a WHERE a.assertion_id=? AND '+CURRENT_ASSERTION,(assertion_id,)):return {'decision':'DEFERRED','reason':'SUPERSEDED_OR_INACTIVE_CLAIM'}
            if current['lifecycle'] in {'DEFERRED','REJECTED','DEPRECATED'}:return {'decision':'DEFERRED','reason':'INACTIVE_CLAIM'}
            if status=='VERIFIED' and conflicts.conflicts(assertion_id,txn=t):
                return {'decision':'DEFERRED','reason':'CONFLICTING_CLAIMS'}
            ref=Ref.parse(f'ASSERTION:{assertion_id}')
            if current['epistemic_status']!=status:
                s.store.set_assertion_status(t,ref,EpistemicStatus(status))
            if status=='VERIFIED' and current['lifecycle']=='VALIDATED_FORMALLY':
                s.store.set_assertion_stage(t,ref,Lifecycle.REVIEWED_SEMANTICALLY,Component.AUTOMATED_PANEL)
                s.store.set_assertion_stage(t,ref,Lifecycle.CORROBORATED,Component.EVALUATION_PROCESS)
                s.store.set_assertion_stage(t,ref,Lifecycle.PROMOTED,Component.PROMOTION_CONTROLLER)
            decision={'policy':asdict(p),'status':status,'claim_hash':row['full_hash'],'support_origins':sorted(yes),'contradicting_origins':sorted(no)}
            t.audit(Component.EVALUATION_PROCESS,'EVIDENCE_POLICY_APPLIED',str(ref),canonical_json(decision))
        return {'decision':status,'policy_id':p.policy_id,'policy_version':p.version,'origins':len(yes)}
