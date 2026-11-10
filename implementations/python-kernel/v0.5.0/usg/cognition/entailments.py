"""Completed-view frame entailments, including inherited essential effects.

Returns proof-carrying n-ary facts, never silently converts typical outcomes
or intentions into achieved effects.
"""
from ..grammar.node import role_entries


def completed_frames(node,complete=False):
    if node.op in {'ASSERT','AND'}:
        for a in node.args:yield from completed_frames(a,complete)
    elif node.op=='TENSE' and node.get('tense')!='FUTURE':
        yield from completed_frames(node.args[1],complete)
    elif node.op=='HOLDS':
        sit=node.args[0]
        if sit.op=='ASPECT' and sit.get('aspect') in {'PERFECT','PERFECTIVE'}:
            sit=sit.args[0];complete=True
        if sit.op=='APPLY' and complete:yield sit


def frame_entailments(expression,library,premise,support_cap='SOURCE_ASSERTED',limit=1000):
    out=[]
    if limit<=0:return out
    for instance in completed_frames(expression):
        name=instance.get('frame');rf=library.resolved(name)
        # Attitude CONTENT and component descriptions are never traversed.
        bindings={}
        for role,_,filler in role_entries(instance):bindings.setdefault(role,[]).append(filler)
        def resolve(arg):
            if arg.startswith('param:'):return rf.pins.get(arg[6:])
            if arg.startswith('value:'):return arg[6:]
            values=bindings.get(arg,())
            if len(values)!=1 or values[0].op not in {'REF','KIND','VALUE'}:return None
            return str(values[0].get('ref',values[0].get('concept')))
        todo,seen=[name],set()
        while todo:
            at=todo.pop()
            if at in seen:continue
            seen.add(at);f=library.get(at)
            todo.extend(library.resolved(at).specializes)
            patterns=list(f.final)
            patterns.extend(c.pattern for c in f.consequences if c.strength.value=='ESSENTIAL' and c.kind.value=='EFFECT')
            for pattern in patterns:
                args=tuple(resolve(a) for a in pattern.args)
                if not args or any(a is None for a in args):continue
                result={'relation':pattern.predicate,'arguments':list(args),'rule':'SG-KNW-004',
                        'premises':[premise,f'FRAME:{at}@{f.version}'],'epistemic_status':'INFERRED','support_cap':support_cap}
                if result not in out:out.append(result)
                if len(out)>=limit:return out
    return out
