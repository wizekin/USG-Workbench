"""Offline CoNLL-U adapter and closed dependency-to-semantics compiler.

Accepts output from locally installed parsers without depending on their SDK or
downloading a model. Analyses are untrusted proposals, checked against all source
tokens. Unsupported dependencies defer the entire unit.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from ..grammar.annot import grammatical
from ..grammar.node import apply, aspect, holds, hole, not_, speech_time, tense
from ..util import sha256_hex
from .parser import DeterministicInterpreter, Token, Unsupported, VERBS, _ParseState


@dataclass(frozen=True)
class Dependency:
    id: int
    form: str
    lemma: str
    upos: str
    features: tuple
    head: int
    relation: str
    start: int
    end: int

    def feature(self,name):
        return dict(self.features).get(name)


class ConlluAnalysis:
    def __init__(self,text,source_text):
        if len(text)>8_000_000 or len(source_text)>200000:
            raise ValueError('analysis size limit')
        sentences=[];sentence=[];cursor=0
        def finish():
            nonlocal sentence
            if sentence:
                if [t.id for t in sentence]!=list(range(1,len(sentence)+1)):
                    raise ValueError('dependency ids must be contiguous')
                roots=[t for t in sentence if t.head==0]
                if len(roots)!=1 or roots[0].relation!='root':
                    raise ValueError('one dependency root required')
                for token in sentence:
                    seen=set();at=token
                    while at.head:
                        if at.id in seen or not 1<=at.head<=len(sentence):
                            raise ValueError('cyclic or dangling dependency')
                        seen.add(at.id);at=sentence[at.head-1]
                sentences.append(tuple(sentence));sentence=[]
        for line in text.splitlines()+['']:
            if line.startswith('#'):
                continue
            if not line.strip():
                finish();continue
            fields=line.split('\t')
            if len(fields)!=10 or not fields[0].isdigit() or not fields[6].isdigit():
                raise ValueError('CoNLL-U rows require ten fields; split/empty tokens need an explicit offset adapter')
            _,form,lemma,upos,_,features,head,relation,_,_=fields
            start=source_text.find(form,cursor)
            if start<0 or source_text[cursor:start].strip():
                raise ValueError('dependency tokens do not cover the exact source')
            pairs=[]
            if features!='_':
                for f in features.split('|'):
                    pair=f.split('=')
                    if len(pair)!=2 or pair[0] in dict(pairs):
                        raise ValueError('malformed dependency features')
                    pairs.append(tuple(pair))
            sentence.append(Dependency(int(fields[0]),form,lemma,upos,tuple(pairs),int(head),relation,start,start+len(form)))
            cursor=start+len(form)
        if source_text[cursor:].strip():
            raise ValueError('unanalysed source suffix')
        self.body=text
        self.sentences=tuple(sentences)
        self.digest=sha256_hex(text+source_text)

    def unit(self,start,end):
        matches=[s for s in self.sentences if s[0].start>=start and s[-1].end<=end]
        if len(matches)!=1:
            raise Unsupported('DEPENDENCY_UNIT_GAP')
        return matches[0]


class DependencyInterpreter(DeterministicInterpreter):
    def __init__(self,analysis,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.analysis=analysis

    def interpret(self,source,unit,discourse=()):
        return _DependencyState(self,source,unit,tuple(discourse)).run()


class _DependencyState(_ParseState):
    def arabic(self,ts):
        return self.clause(ts)

    def clause(self,ts,context='WORLD'):
        tokens=self.parser.analysis.unit(self.unit.start,self.unit.end)
        root=next(t for t in tokens if t.head==0)
        metadata=VERBS.get(root.form.casefold()) or VERBS.get(root.lemma.casefold())
        if metadata is None:
            arabic={'أكل':('EAT','EATER','FOOD','PAST',True),'اكل':('EAT','EATER','FOOD','PAST',True),
                    'فتح':('OPEN','AGENT','UNDERGOER','PAST',True),'عالج':('TREAT','PRACTITIONER','TREATED_ENTITY','PAST',True),
                    'فحص':('EXAMINATION','EXAMINER','EXAMINED_ENTITY','PAST',True)}
            metadata=arabic.get(root.lemma)
        if metadata is None:
            raise Unsupported('DEPENDENCY_FRAME_GAP')
        frame,sr,ore,default_tense,_=metadata
        if root.feature('Mood') not in {None,'Ind'} or root.feature('Polarity') not in {None,'Pos'}:
            raise Unsupported('DEPENDENCY_MORPHOLOGY_SCOPE_GAP')
        if root.feature('Aspect') not in {None,'Perf','Prog','Imp'} or root.feature('Tense') not in {None,'Past','Pres','Fut'}:
            raise Unsupported('DEPENDENCY_MORPHOLOGY_SCOPE_GAP')
        if frame in {'BELIEVE','KNOW','WANT','ATTEMPT','OFFER','COMMUNICATE','CAUSATION'}:
            raise Unsupported('DEPENDENCY_OPAQUE_SCOPE_GAP')
        children=[t for t in tokens if t.head==root.id]
        passive=any(t.relation=='nsubj:pass' for t in children)
        if any(t.relation in {'neg','advmod'} and t.form.casefold() in {'not','never','لم','لا','ليس'} for t in children):context='NEGATED'
        if root.feature('Tense')=='Fut' or any(t.form.casefold()=='will' for t in children):context='HYPOTHETICAL'
        bindings={};consumed={root.id}
        def noun(t,role):
            descendants=[x for x in tokens if x.head==t.id]
            if any(x.relation not in {'det','amod','case'} for x in descendants):
                raise Unsupported('DEPENDENCY_NOUN_MODIFIER_GAP')
            cases=[x.form.casefold() for x in descendants if x.relation=='case']
            allowed={'by'} if passive and role==sr else {'to'} if role=='RECIPIENT' else set()
            if any(x not in allowed for x in cases):raise Unsupported('DEPENDENCY_PREPOSITION_GAP')
            parts=[t]+[x for x in descendants if x.relation!='case']
            consumed.update(x.id for x in [t]+descendants)
            return self.np([Token(x.form,x.start,x.end) for x in sorted(parts,key=lambda x:x.id)],context)
        for token in children:
            rel=token.relation
            role=None
            if rel=='nsubj':role=sr
            elif rel=='nsubj:pass':role=ore
            elif rel=='obj' and not passive:role=ore
            elif rel=='iobj' and frame in {'GIVE','RETURN','LEND'}:role='RECIPIENT'
            elif rel=='obl:agent' and passive:role=sr
            elif rel=='punct':
                if token.form not in {'.','!','?','؟','。',','}:
                    raise Unsupported('DEPENDENCY_PUNCTUATION_GAP')
                consumed.add(token.id);continue
            elif rel in {'aux','aux:pass'}:
                if token.form.casefold() not in {'is','are','was','were','has','have','had','did','does','do','been','be','will'}:
                    raise Unsupported('DEPENDENCY_AUXILIARY_SCOPE_GAP')
                consumed.add(token.id);continue
            elif rel in {'neg','advmod'} and token.form.casefold() in {'not','never','لم','لا','ليس'}:
                consumed.add(token.id);continue
            else:
                raise Unsupported('DEPENDENCY_RELATION_GAP',rel)
            if role is None or role in bindings:
                raise Unsupported('DEPENDENCY_ROLE_CONFLICT')
            bindings[role]=noun(token,role)
        if consumed!={t.id for t in tokens} or sr not in bindings and not passive:
            raise Unsupported('DEPENDENCY_UNCONSUMED_TOKEN')
        for role in self.parser.foundation.frames.resolved(frame).roles:
            if role.required and role.name not in bindings:
                bindings[role.name]=hole()
        sit=grammatical(apply(frame,1,bindings),'SG-INT-040',(root.start,root.end))
        aspect_name={'Perf':'PERFECTIVE','Prog':'PROGRESSIVE','Imp':'IMPERFECTIVE'}.get(root.feature('Aspect'))
        if any(t.form.casefold() in {'has','have','had'} for t in children if t.relation=='aux'):aspect_name='PERFECT'
        if aspect_name:
            sit=grammatical(aspect(aspect_name,sit),'SG-INT-051',(root.start,root.end))
        p=holds(sit)
        negative=[t for t in children if t.relation in {'neg','advmod'} and t.form.casefold() in {'not','never','لم','لا','ليس'}]
        if negative:
            p=grammatical(not_(p),'SG-INT-020',(negative[0].start,negative[0].end))
        t={'Past':'PAST','Pres':'PRESENT','Fut':'FUTURE'}.get(root.feature('Tense'),default_tense)
        if any(x.form.casefold()=='will' for x in children):
            t='FUTURE'
        return grammatical(tense(t,speech_time(),p),'SG-INT-051',(root.start,root.end))
