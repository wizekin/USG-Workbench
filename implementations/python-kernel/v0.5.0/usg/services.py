"""Bounded unattended service adapters; configuration is separate from source data."""
import json
import os
from pathlib import Path
from .validation.evaluation import EvidencePolicy,EvaluationProcess


def evaluate_files(service,config_path,receipts_path):
    def read(path,limit):
        with open(path,'rb') as f:raw=f.read(limit+1)
        if len(raw)>limit:raise ValueError('evidence configuration/input byte budget')
        return json.loads(raw)
    config=read(config_path,65536)
    authorities={name:(entry['origin'],os.environ[entry['key_env']].encode('utf8')) for name,entry in config['authorities'].items()}
    policy=dict(config['policy'])
    for name in ('allowed_trust_tiers','allowed_contexts'):
        if name in policy:policy[name]=tuple(policy[name])
    evaluator=EvaluationProcess(service,EvidencePolicy(**policy),authorities)
    requests=read(receipts_path,1024*1024)
    if not isinstance(requests,list) or len(requests)>1000:raise ValueError('evaluation batch limit')
    return [evaluator.evaluate(x['assertion_id'],x['receipts']) for x in requests]


def automatic_evaluation(service):
    config=os.environ.get('USG_EVIDENCE_CONFIG')
    receipts=os.environ.get('USG_EVIDENCE_RECEIPTS')
    if not config or not receipts:return {'enabled':False,'evaluations':[]}
    return {'enabled':True,'evaluations':evaluate_files(service,config,receipts)}


def partition_claims(service,directory,domain,version):
    from .storage.partitions import DomainPartitions
    service.assert_integrity()
    with service.db.read() as r:
        if domain=='UNIVERSAL_CORE':
            ids=r.query('SELECT assertion_id FROM assertion ORDER BY assertion_id LIMIT 100000')
        else:
            ids=r.query('''SELECT DISTINCT i.assertion_id FROM claim_index i JOIN concept c ON c.canonical_label=i.concept
                JOIN concept_domain cd ON cd.concept_id=c.concept_id JOIN domain d ON d.domain_id=cd.domain_id WHERE d.name=? LIMIT 100000''',(domain,))
        records=[]
        for row in ids:
            data=r.one("SELECT a.*,e.body FROM assertion a JOIN expression e ON e.node_id=a.content_id WHERE a.assertion_id=? AND a.content_space='NODE'",(row[0],))
            if data:
                body=dict(data);body['body']=json.loads(body['body'])
                records.append({'space':'ASSERTION','id':row[0],'body':body})
    with DomainPartitions(directory) as partitions:digest=partitions.publish(domain,version,records)
    return {'domain':domain,'version':version,'records':len(records),'sha256':digest,'authoritative':False}
