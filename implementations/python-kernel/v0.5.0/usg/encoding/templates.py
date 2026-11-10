"""Exact structural templates, independent of semantic event identity.

Every occurrence has its own slot vector. No shared event object or RDF identity
is invented by factoring equal physical layouts. Templates cannot reference one
another, so cycles and recursive expansion are impossible.
"""
from collections import Counter

from ..util import canonical_json
from .compact import dumps as compact_dumps, loads as compact_loads
from .usbf import DecodeError


def _shape(value,slots,depth=0):
    if depth>90:
        raise ValueError('template depth')
    if isinstance(value,dict):
        keys=sorted(value)
        return ['D',keys,[_shape(value[k],slots,depth+1) for k in keys]]
    if isinstance(value,list):
        return ['L',[_shape(x,slots,depth+1) for x in value]]
    slots.append(value)
    return ['S']


def dumps(records,schemas=None):
    if not isinstance(records,list) or len(records)>100000:
        raise ValueError('template record budget')
    shapes=[];counts=Counter()
    for record in records:
        slots=[];shape=_shape(record,slots)
        key=canonical_json(shape)
        shapes.append((key,shape,slots))
        counts[key]+=1
    selected=sorted(key for key,count in counts.items() if count>=3 and len(key)>24)[:1000]
    ids={key:i for i,key in enumerate(selected)}
    dictionary={key:shape for key,shape,_ in shapes if key in ids}
    packed={'profile':'USG-TEMPLATES-1','templates':[dictionary[k] for k in selected],
            'records':[[ids[key],slots] if key in ids else [-1,record] for record,(key,_,slots) in zip(records,shapes)]}
    encoded=compact_dumps(packed,schemas)
    plain=compact_dumps({'profile':'USG-TEMPLATES-1','templates':[],'records':[[-1,r] for r in records]},schemas)
    return encoded if len(encoded)<len(plain) else plain


def loads(data):
    packed=compact_loads(data)
    if not isinstance(packed,dict) or set(packed)!={'profile','templates','records'} or packed['profile']!='USG-TEMPLATES-1':
        raise DecodeError('template payload schema')
    templates,records=packed['templates'],packed['records']
    if not isinstance(templates,list) or len(templates)>1000 or not isinstance(records,list) or len(records)>100000:
        raise DecodeError('template count budget')
    budget=[0]
    def expand(shape,slots,cursor,depth=0):
        budget[0]+=1
        if depth>90 or budget[0]>1000000 or not isinstance(shape,list) or not shape:
            raise DecodeError('template expansion budget/schema')
        if shape==['S']:
            if cursor[0]>=len(slots):
                raise DecodeError('missing template slot')
            value=slots[cursor[0]];cursor[0]+=1
            # Slot data is scalar; an attacker cannot smuggle nested expansion.
            if isinstance(value,(dict,list)):
                raise DecodeError('non-scalar template slot')
            return value
        if shape[0]=='L' and len(shape)==2 and isinstance(shape[1],list):
            return [expand(x,slots,cursor,depth+1) for x in shape[1]]
        if shape[0]=='D' and len(shape)==3:
            keys,children=shape[1:]
            if not isinstance(keys,list) or not isinstance(children,list) or len(keys)!=len(children) or any(not isinstance(k,str) for k in keys) or keys!=sorted(set(keys)):
                raise DecodeError('template dictionary schema')
            return {key:expand(child,slots,cursor,depth+1) for key,child in zip(keys,children)}
        raise DecodeError('unknown template tag')
    result=[]
    for record in records:
        if not isinstance(record,list) or len(record)!=2 or type(record[0]) is not int:
            raise DecodeError('template record schema')
        index,slots=record
        if index==-1:
            result.append(slots);continue
        if not 0<=index<len(templates) or not isinstance(slots,list):
            raise DecodeError('unknown template or invalid slots')
        cursor=[0]
        value=expand(templates[index],slots,cursor)
        if cursor[0]!=len(slots):
            raise DecodeError('unused template slots')
        result.append(value)
    return result
