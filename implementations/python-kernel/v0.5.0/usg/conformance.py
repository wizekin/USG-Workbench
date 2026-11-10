"""Reproducible requirement inventory with explicit, conservative evidence status.

Text references are discovery aids, not proof. Passing a part's tests does not
silently mark every sentence in that part as conformant.
"""
from __future__ import annotations

import re
from pathlib import Path

from .util import sha256_hex

PARTS={
 1:('Foundations',['core/values.py','autonomy/policy.py','autonomy/seal.py'],['tests.test_core','tests.test_autonomy']),
 2:('Data model',['core/records.py','storage/records_store.py','concepts/definitions.py'],['tests.test_store','tests.test_completion.DefinitionWorkflowTests']),
 3:('Grammar',['grammar/node.py','grammar/typecheck.py','grammar/canon.py'],['tests.test_grammar','tests.test_typecheck','tests.test_canon','tests.test_time']),
 4:('Frames and functions',['model/frames.py','foundation/functions.py'],['tests.test_frames','tests.test_foundation']),
 5:('Validation',['validation/validator.py','validation/contextual.py'],['tests.test_validator','tests.test_completion.ContextAndCalibrationTests']),
 6:('Assurance',['validation/evaluation.py','validation/calibration.py'],['tests.test_extended_services.EvaluationTests','tests.test_completion.ContextAndCalibrationTests']),
 7:('Identity',['concepts/identity.py','concepts/definitions.py'],['tests.test_runtime_guards','tests.test_completion.DefinitionWorkflowTests']),
 8:('Interpretation',['interpretation/parser.py','interpretation/dependencies.py','interpretation/resources.py'],['tests.test_pipeline','tests.test_completion.LanguageAdapterTests']),
 9:('Learning',['learning/engine.py','learning/semantic.py'],['tests.test_runtime_guards','tests.test_completion.LearningLifecycleTests']),
 10:('Cognition',['cognition/controller.py','cognition/worker.py','cognition/reasoner.py','cognition/resources.py'],['tests.test_runtime_guards','tests.test_completion.RuntimeAndEncodingAcceptanceTests']),
 11:('Storage and interchange',['encoding/compact.py','encoding/templates.py','encoding/linked_data.py','storage/partitions.py'],['tests.test_compact','tests.test_extended_services.PhysicalAndReasoningTests','tests.test_completion.RuntimeAndEncodingAcceptanceTests']),
 12:('Evaluation and delivery',['benchmark/runner.py','acceptance.py','conformance.py'],['tests.test_cli','tests.test_cli_workflow','tests.test_completion'])}

STEPS=[
 {'step':1,'mechanism':'Requirement inventory and executable evidence trace','modules':['conformance.py'],'tests':['tests.test_delivery.TraceabilityTests']},
 {'step':2,'mechanism':'Scoped immutable definition versions and inherited essential conditions','modules':['concepts/definitions.py','concepts/identity.py'],'tests':['tests.test_completion.DefinitionWorkflowTests']},
 {'step':3,'mechanism':'Contextual reports, conflicts, authenticated evaluation and persisted calibration','modules':['validation/contextual.py','validation/calibration.py','validation/evaluation.py'],'tests':['tests.test_completion.ContextAndCalibrationTests']},
 {'step':4,'mechanism':'Local lexical resources and exact-offset dependency compiler','modules':['interpretation/resources.py','interpretation/dependencies.py'],'tests':['tests.test_completion.LanguageAdapterTests']},
 {'step':5,'mechanism':'Typed generalization, counterexamples, automatic aliases, canaries and rollback reprocessing','modules':['learning/semantic.py','learning/engine.py','cognition/worker.py'],'tests':['tests.test_completion.LearningLifecycleTests']},
 {'step':6,'mechanism':'Function/definition inference, measured scheduling, template codecs and linked data','modules':['cognition/reasoner.py','cognition/resources.py','encoding/templates.py','encoding/linked_data.py'],'tests':['tests.test_completion.RuntimeAndEncodingAcceptanceTests']},
 {'step':7,'mechanism':'Offline acceptance, regression, adversarial, crash and upgrade checks','modules':['acceptance.py'],'tests':['tests.test_delivery','tests.test_completion','tests.test_runtime_guards']},
]

OPEN_CAPABILITIES=[
 'Open-domain English and Arabic semantics, including idioms and arbitrary scope/attachment ambiguity.',
 'Independent natural-language accuracy evidence; constructed gold tests establish bounded consistency only.',
 'Autonomous promotion of novel concepts and fundamental frames without adequate independent semantic proof.',
 'Complete domain theories and general procedural discovery or arbitrary theorem proving.',
 'Authoritative distributed domain sharding; current domain files are verified immutable snapshots.',
 'Full external RDF/OWL reasoning and unrestricted RDF import; the exchange profile preserves unsupported semantics as USG syntax.',
]


def build(specification,root=None):
    path=Path(specification);root=Path(root) if root is not None else path.parent
    with open(path,'rb') as source:raw=source.read(2_000_001)
    text=raw.decode('utf8')
    if len(raw)>2_000_000:raise ValueError('specification size limit')
    sections=[];requirements=[];section=None;fenced=False
    for line_no,line in enumerate(text.splitlines(),1):
        if line.lstrip().startswith('```'):
            fenced=not fenced;continue
        if fenced:continue
        heading=re.match(r'^#{2,6}\s+(\d{1,2}\.\d+(?:\.\d+)*)\s+(.*)',line)
        if heading:
            number,title=heading.groups()
            part=int(number.split('.')[0])
            if part in PARTS:
                section=number
                sections.append({'id':number,'part':part,'title':title,'source_line':line_no,'status':'AUTOMATED_COVERAGE_NOT_ESTABLISHED'})
        rule_ids=sorted(set(re.findall(r'\b(?:SG-[A-Z]+-\d{3}|VC-[STGVC]\d{2}|I-\d{2})\b',line)))
        normative=bool(re.search(r'\bMUST(?: NOT)?\b|\bSHOULD(?: NOT)?\b|\bNormative\b',line))
        if section and line.strip() and (normative or rule_ids and line.strip().startswith('|')):
            req_id='REQ-'+sha256_hex(section+'\n'+line.strip())[:16]
            if any(r['id']==req_id for r in requirements):continue
            requirements.append({'id':req_id,'section':section,'source_line':line_no,'statement':line.strip(),
                                 'rule_ids':rule_ids,'status':'UNPROVEN','evidence':[]})
    code_files=sorted((root/'usg').rglob('*.py'));test_files=sorted((root/'tests').glob('test_*.py'))
    code_text={str(p.relative_to(root)):p.read_text(encoding='utf8') for p in code_files}
    test_text={str(p.relative_to(root)):p.read_text(encoding='utf8') for p in test_files}
    for req in requirements:
        for rid in req['rule_ids']:
            req['evidence'].append({'rule':rid,'implementation_mentions':[p for p,s in code_text.items() if rid in s],
                                    'test_mentions':[p for p,s in test_text.items() if rid in s],
                                    'evidence_kind':'TEXT_REFERENCE_ONLY'})
        if req['evidence']:
            req['status']='REFERENCED_UNPROVEN'
    parts=[{'part':p,'name':name,'modules':['usg/'+m for m in modules],'test_targets':tests,
            'status':'BOUNDED_IMPLEMENTATION','full_conformance_proven':False,
            'requirements':sum(r['section'].startswith(str(p)+'.') for r in requirements)} for p,(name,modules,tests) in PARTS.items()]
    return {'specification':str(path.resolve()),'specification_sha256':sha256_hex(text),
            'coverage_rule':'References and passing bounded tests are not full semantic conformance.',
            'user_constraints':{'human_review':False,'large_models':'disabled by default; aggregate general issues/rules only'},
            'full_conformance':False,'parts':parts,'steps':STEPS,'sections':sections,'requirements':requirements,
            'open_capabilities':OPEN_CAPABILITIES}
