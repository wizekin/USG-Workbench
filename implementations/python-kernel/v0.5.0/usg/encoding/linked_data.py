"""RDF/OWL taxonomy, SHACL frame shapes and PROV-O assertion envelopes.

Expressions remain reified syntax trees. Negation, quantifiers and attitudes
are never flattened into unconditional RDF world statements.
"""
import json
from urllib.parse import quote

from ..grammar.serialize import node_from_json
from ..util import canonical_json

USG='https://usg.example/vocab#'
RDF='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
RDFS='http://www.w3.org/2000/01/rdf-schema#'
OWL='http://www.w3.org/2002/07/owl#'
SH='http://www.w3.org/ns/shacl#'
PROV='http://www.w3.org/ns/prov#'
XSD='http://www.w3.org/2001/XMLSchema#'


def graph(service,mode='semantic'):
    if mode not in {'semantic','reversible'}:raise ValueError('linked data mode')
    service.assert_integrity()
    result=[]
    with service.db.read() as r:installation=r.scalar("SELECT value FROM meta WHERE key='installation_id'")
    onto=service.foundation.ontology
    def iri(kind,name):
        return 'urn:usg:'+installation+':'+kind+':'+quote(str(name),safe='')
    for concept in sorted(onto.concepts()):
        result.append({'@id':iri('concept',concept),'@type':['rdf:Property' if onto.kind_of(concept).value=='PROPERTY' else 'owl:Class','usg:Concept'],
                       'rdfs:label':concept,'usg:semanticKind':onto.kind_of(concept).value,
                       'rdfs:subClassOf':[{'@id':iri('concept',p)} for p in onto.parents_of(concept)],
                       'owl:disjointWith':[{'@id':iri('concept',p)} for p in onto.seed(concept).disjoint_with]})
    for name,relation in sorted(service.foundation.relations.items()):
        types=['owl:ObjectProperty']
        for attr,kind in (('transitive','TransitiveProperty'),('symmetric','SymmetricProperty'),('asymmetric','AsymmetricProperty'),('irreflexive','IrreflexiveProperty')):
            if getattr(relation,attr):types.append('owl:'+kind)
        item={'@id':iri('relation',name),'@type':types,'rdfs:label':name}
        if relation.inverse_of:item['owl:inverseOf']={'@id':iri('relation',relation.inverse_of)}
        result.append(item)
    for name in sorted(service.foundation.frames.names()):
        frame=service.foundation.frames.resolved(name)
        fid=iri('frame',name+'@'+str(frame.frame.version))
        result.append({'@id':fid,'@type':'owl:Class','rdfs:label':name})
        properties=[]
        for role in frame.roles:
            rid=iri('role',name+'@'+str(frame.frame.version)+'.'+role.name)
            result.append({'@id':rid,'@type':'owl:ObjectProperty','rdfs:domain':{'@id':fid},'rdfs:subPropertyOf':{'@id':iri('tier1',role.spec.tier1_parent)}})
            shape={'@type':'sh:PropertyShape','sh:path':{'@id':rid},'sh:minCount':max(role.spec.card_min,1 if role.required else 0),'sh:maxCount':role.spec.card_max}
            if role.cls:shape['sh:class']={'@id':iri('concept',role.cls)}
            properties.append(shape)
        result.append({'@id':fid+':shape','@type':'sh:NodeShape','sh:targetClass':{'@id':fid},'sh:property':properties})
    with service.db.read() as r:
        for source in r.query('SELECT source_id,text_hash,language,sensitivity FROM source ORDER BY source_id'):
            result.append({'@id':iri('source',source['source_id']),'@type':'prov:Entity',
                           'usg:sha256':source['text_hash'],'usg:language':source['language'],'usg:sensitivity':source['sensitivity']})
            if mode=='reversible':
                from ..core.ids import IdSpace,Ref
                stored=service.store.get_source(r,Ref(IdSpace.SOURCE,source['source_id']))
                result[-1]['usg:sourceText']=stored.text
                result[-1]['usg:sourceAnchor']=canonical_json(stored.anchor.to_json() if stored.anchor else None)
        rows=r.query("SELECT a.*,e.body FROM assertion a JOIN expression e ON a.content_space='NODE' AND a.content_id=e.node_id ORDER BY assertion_id")
        for row in rows:
            aid=iri('assertion',row['assertion_id'])
            result.append({'@id':aid,'@type':['prov:Entity','usg:Assertion'],
                           'prov:wasDerivedFrom':{'@id':iri('source',row['source_id'])},
                           'usg:epistemicStatus':row['epistemic_status'],'usg:lifecycle':row['lifecycle'],
                           'usg:commitment':row['commitment'],'usg:context':row['eval_context'],
                           'usg:expression':{'@id':aid+':expression'},'usg:payload':row['body']})
            def tree(node,path):
                nid=aid+':expression'+path
                item={'@id':nid,'@type':'usg:Expression','usg:operator':node.op,
                      'usg:parameters':canonical_json(node.params_dict()),
                      'usg:arguments':{'@list':[{'@id':nid+':'+str(i)} for i in range(len(node.args))]}}
                if node.op=='APPLY':
                    item['usg:frame']={'@id':iri('frame',node.get('frame')+'@'+str(node.get('version')))}
                result.append(item)
                for i,child in enumerate(node.args):
                    tree(child,path+':'+str(i))
            begin=len(result)
            tree(node_from_json(json.loads(row['body'])),'')
            nodes=result[begin:]
            del result[begin:]
            result.append({'@id':aid+':context','@graph':nodes})
    return {'@context':{'usg':USG,'rdf':RDF,'rdfs':RDFS,'owl':OWL,'sh':SH,'prov':PROV,'xsd':XSD},'@graph':result}


def to_turtle(document):
    """Serialize the closed JSON-LD subset above without optional dependencies."""
    context=document['@context'];triples=[];counter=[0]
    def expand(value):
        prefix,sep,local=value.partition(':')
        return context[prefix]+local if sep and prefix in context else value
    def iri(value):
        expanded=expand(value)
        if any(c in expanded for c in '<>"{}|^`\\\n\r\t '):
            raise ValueError('unsafe RDF IRI')
        return '<'+expanded+'>'
    def blank():
        counter[0]+=1
        return '_:b'+str(counter[0])
    def value(x):
        if isinstance(x,dict):
            if set(x)=={'@id'}:
                return iri(x['@id'])
            if set(x)=={'@list'}:
                if not x['@list']:
                    return iri('rdf:nil')
                head=blank();at=head
                for i,item in enumerate(x['@list']):
                    nxt=blank() if i+1<len(x['@list']) else iri('rdf:nil')
                    triples.append((at,iri('rdf:first'),value(item)))
                    triples.append((at,iri('rdf:rest'),nxt));at=nxt
                return head
            subject=iri(x['@id']) if '@id' in x else blank()
            emit(subject,x)
            return subject
        if type(x) is bool:
            return 'true' if x else 'false'
        if type(x) is int:
            return str(x)
        if isinstance(x,str):
            return json.dumps(x,ensure_ascii=False)
        raise ValueError('unsupported RDF object')
    def emit(subject,item):
        for key,objects in item.items():
            if key=='@id':continue
            predicate=iri('rdf:type' if key=='@type' else key)
            for obj in objects if isinstance(objects,list) else [objects]:
                triples.append((subject,predicate,iri(obj) if key=='@type' else value(obj)))
    for item in document['@graph']:
        if '@graph' in item:
            # Turtle carries reified syntax only; TriG retains graph membership.
            for child in item['@graph']:emit(iri(child['@id']),child)
        else:emit(iri(item['@id']),item)
    return '\n'.join(' '.join(t)+' .' for t in triples)+'\n'


def to_trig(document):
    root={'@context':document['@context'],'@graph':[x for x in document['@graph'] if '@graph' not in x]}
    parts=[to_turtle(root)]
    for item in document['@graph']:
        if '@graph' not in item:continue
        if any(c in item['@id'] for c in '<>\\ \n\r\t'):raise ValueError('unsafe graph IRI')
        body=to_turtle({'@context':document['@context'],'@graph':item['@graph']})
        # Blank-node labels are graph-local in our writer. Prefix them uniquely
        # when assembling a dataset, where blank identifiers share one scope.
        prefix='g'+str(len(parts))+'b'
        body=body.replace('_:b','_:'+prefix)
        parts.append('<'+item['@id']+'> {\n'+body+'}\n')
    return ''.join(parts)


def export_linked_data(service,path,*,format='jsonld',mode='semantic'):
    from pathlib import Path
    if format not in {'jsonld','turtle','trig'}:raise ValueError('linked data format')
    document=graph(service,mode)
    data=(canonical_json(document) if format=='jsonld' else to_trig(document) if format=='trig' else to_turtle(document)).encode('utf8')
    if len(data)>64*1024*1024:raise ValueError('linked data size budget')
    with open(path,'xb') as f:f.write(data)
    return {'file':str(Path(path).resolve()),'format':format,'bytes':len(data),'mode':mode,
            'losses':['USG syntax extensions carry negation, modality, quantification, holes and evidence axes.',
                      'Turtle omits named graph membership; use TriG or JSON-LD for contexts.']}


def import_jsonld(service,document):
    # Accept our bounded JSON-LD source envelope only. No remote context fetches,
    # OWL imports, incoming trust statuses or rule declarations are executed.
    context={'usg':USG,'rdf':RDF,'rdfs':RDFS,'owl':OWL,'sh':SH,'prov':PROV,'xsd':XSD}
    if not isinstance(document,dict) or document.get('@context')!=context or not isinstance(document.get('@graph'),list) or len(document['@graph'])>100000:
        raise ValueError('unsupported JSON-LD source envelope')
    from ..core.records import Source,Anchor
    from ..core.values import Sensitivity
    sources=[]
    for item in document['@graph']:
        if not isinstance(item,dict):raise ValueError('invalid linked data node')
        if 'usg:sourceText' in item:
            anchor=json.loads(item.get('usg:sourceAnchor','null'))
            sources.append(Source(item['usg:sourceText'],language=item['usg:language'],text_hash=item['usg:sha256'],
                sensitivity=Sensitivity(item['usg:sensitivity']),anchor=Anchor(**anchor) if anchor else None))
    results=[service.ingest(s.text,language=s.language,sensitivity=s.sensitivity.value,anchor=s.anchor,trust_tier='QUARANTINE') for s in sources]
    return {'reinterpreted_sources':len(results),'results':results,'imported_trusted_claims':0,
            'semantic_only_records_retained_in_file':not sources}
