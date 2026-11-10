"""Bounded dictionary encoding with versioned frame schemas and 3-bit role states.

No event instances are interned: two occurrences remain two encoded trees.
Unknown frame shapes fall back to typed value encoding without discarding data.
"""
import math
import struct
from .usbf import DecodeError, MAX_BLOCK, read_varint, varint, zigzag, unzigzag

HOLES = ('UNSPECIFIED', 'UNKNOWN', 'NOT_APPLICABLE', 'WITHHELD')


def schemas_from_library(library):
    return {(name, library.get(name).version): library.resolved(name).role_names() for name in library.names()}


def dumps(value, schemas=None):
    schemas = schemas or {}
    strings = set()
    def collect(x, depth=0):
        if depth > 96:
            raise ValueError('compact nesting limit')
        if isinstance(x, str):
            strings.add(x)
        elif isinstance(x, dict):
            for k,v in x.items():
                if not isinstance(k,str): raise ValueError('string keys required')
                strings.add(k); collect(v,depth+1)
        elif isinstance(x,list):
            for v in x: collect(v,depth+1)
        elif x is not None and type(x) not in (bool,int,float):
            raise ValueError('unsupported compact value')
    collect(value)
    for (name,version), roles in schemas.items():
        strings.add(name); strings.update(roles)
    strings = sorted(strings)
    if len(strings)>100000: raise ValueError('dictionary limit')
    ids = {s:i for i,s in enumerate(strings)}
    frames = sorted(schemas)
    frame_ids = {key:i for i,key in enumerate(frames)}
    out = bytearray(b'CIR1'+varint(len(strings)))
    for s in strings:
        raw=s.encode('utf-8'); out.extend(varint(len(raw))); out.extend(raw)
    out.extend(varint(len(frames)))
    for name,version in frames:
        roles=schemas[(name,version)]
        if len(roles)>256 or len(set(roles))!=len(roles):raise ValueError('frame role limit/duplicates')
        out.extend(varint(ids[name])+varint(version)+varint(len(roles)))
        for role in roles:out.extend(varint(ids[role]))

    def frame(x):
        if set(x)-{'op','params','args','ann'} or x.get('op')!='APPLY':return None
        p=x.get('params',{})
        if set(p)!={'frame','version','roles'}:return None
        key=(p['frame'],p['version'])
        if key not in frame_ids or len(p['roles'])!=len(x.get('args',())):return None
        groups={r:[] for r in schemas[key]}
        for entry,arg in zip(p['roles'],x['args']):
            name,sep,ordinal=entry.rpartition('#')
            if not sep or name not in groups or ordinal!=str(len(groups[name])):return None
            groups[name].append(arg)
        if p['roles']!=sorted(p['roles'],key=lambda s:(s.rsplit('#',1)[0],int(s.rsplit('#',1)[1]))):return None
        states=[]
        for args in groups.values():
            if not args:states.append(0)
            elif len(args)==1 and args[0].get('op')=='HOLE' and set(args[0])=={'op','args','params'} and args[0]['params'].get('state') in HOLES:
                states.append(2+HOLES.index(args[0]['params']['state']))
            else:states.append(1)
        return key,groups,states

    def emit(x,depth=0):
        if depth>96:raise ValueError('compact nesting limit')
        if x is None:out.append(0)
        elif x is False:out.append(1)
        elif x is True:out.append(2)
        elif type(x) is int:out.append(3);out.extend(varint(zigzag(x)))
        elif type(x) is float:
            if not math.isfinite(x):raise ValueError('nonfinite number')
            out.append(4);out.extend(struct.pack('<d',x))
        elif isinstance(x,str):out.append(5);out.extend(varint(ids[x]))
        elif isinstance(x,list):
            out.append(6);out.extend(varint(len(x)))
            for v in x:emit(v,depth+1)
        elif isinstance(x,dict):
            packed=frame(x)
            if packed:
                key,groups,states=packed
                out.append(8);out.extend(varint(frame_ids[key]))
                bits=sum(state<<(3*i) for i,state in enumerate(states))
                out.extend(bits.to_bytes((3*len(states)+7)//8,'little'))
                for role,state in zip(schemas[key],states):
                    if state==1:
                        out.extend(varint(len(groups[role])))
                        for arg in groups[role]:emit(arg,depth+1)
                out.append(int('ann' in x))
                if 'ann' in x:emit(x['ann'],depth+1)
            else:
                out.append(7);out.extend(varint(len(x)))
                for k in sorted(x):out.extend(varint(ids[k]));emit(x[k],depth+1)
        else:raise ValueError('unsupported value')
        if len(out)>MAX_BLOCK:raise ValueError('compact block budget')
    emit(value)
    return bytes(out)


def loads(data):
    if len(data)>MAX_BLOCK or not data.startswith(b'CIR1'):raise DecodeError('compact header/length')
    at=4
    def take(n):
        nonlocal at
        if n<0 or at+n>len(data):raise DecodeError('truncated compact field')
        result=data[at:at+n];at+=n;return result
    def integer(limit=2**64-1):
        nonlocal at
        n,at=read_varint(data,at)
        if n>limit:raise DecodeError('compact count limit')
        return n
    strings=[]
    try:
        for _ in range(integer(min(100000,len(data)))):
            s=take(integer(len(data))).decode('utf-8')
            if strings and s<=strings[-1]:raise DecodeError('noncanonical dictionary')
            strings.append(s)
        def string():
            i=integer()
            if i>=len(strings):raise DecodeError('dictionary index out of range')
            return strings[i]
        frames=[]
        for _ in range(integer(min(10000,len(data)))):
            name=string();version=integer();roles=[string() for _ in range(integer(256))]
            if not version or len(roles)!=len(set(roles)) or frames and (name,version)<=frames[-1][:2]:raise DecodeError('invalid frame schema')
            frames.append((name,version,roles))
        nodes=0
        def read(depth=0):
            nonlocal nodes
            nodes+=1
            if depth>96 or nodes>200000:raise DecodeError('compact node/depth budget')
            tag=take(1)[0]
            if tag==0:return None
            if tag==1:return False
            if tag==2:return True
            if tag==3:return unzigzag(integer())
            if tag==4:
                x=struct.unpack('<d',take(8))[0]
                if not math.isfinite(x):raise DecodeError('nonfinite compact float')
                return x
            if tag==5:return string()
            if tag==6:return [read(depth+1) for _ in range(integer(len(data)-at))]
            if tag==7:
                result={};previous=None
                for _ in range(integer(len(data)-at)):
                    key=string()
                    if previous is not None and key<=previous:raise DecodeError('noncanonical object keys')
                    previous=key;result[key]=read(depth+1)
                return result
            if tag==8:
                index=integer()
                if index>=len(frames):raise DecodeError('unknown frame schema')
                name,version,roles=frames[index]
                bits=int.from_bytes(take((3*len(roles)+7)//8),'little')
                if bits>>(3*len(roles)):raise DecodeError('nonzero role-state padding')
                entries=[]
                for i,role in enumerate(roles):
                    state=(bits>>(3*i))&7
                    if state>5:raise DecodeError('unknown role state')
                    if state==1:
                        count=integer(min(10000,len(data)-at))
                        if not count:raise DecodeError('empty specified role')
                        entries.extend((role,o,read(depth+1)) for o in range(count))
                    elif state>=2:
                        entries.append((role,0,{'op':'HOLE','args':[],'params':{'state':HOLES[state-2]}}))
                entries.sort(key=lambda x:(x[0],x[1]))
                result={'op':'APPLY','args':[x[2] for x in entries],'params':{'frame':name,'version':version,'roles':[f'{r}#{o}' for r,o,_ in entries]}}
                ann=take(1)[0]
                if ann not in (0,1):raise DecodeError('annotation presence flag')
                if ann:result['ann']=read(depth+1)
                return result
            raise DecodeError('unknown critical compact tag')
        result=read()
        if at!=len(data):raise DecodeError('trailing compact bytes')
        return result
    except (UnicodeError,ValueError,TypeError,IndexError,struct.error,RecursionError) as ex:
        raise DecodeError('malformed compact payload') from ex
