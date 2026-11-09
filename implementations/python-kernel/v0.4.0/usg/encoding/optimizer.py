"""Measured physical-plan selection; never changes authoritative semantics."""
import time
from .usbf import encode,decode


def choose_plan(records,schemas=None,block_sizes=(16384,65536,262144),tolerance=.05,codecs=('json','compact')):
    if not 0<=tolerance<=.25 or not 1<=len(block_sizes)<=8:raise ValueError('optimizer budget')
    records=list(records)
    trials=[]
    failures=[]
    if not codecs or len(codecs)>3 or any(c not in {'json','compact','template'} for c in codecs):raise ValueError('optimizer codecs')
    for size in block_sizes:
        for codec in codecs:
            begin=time.perf_counter()
            try:
                data=encode(records,codec=codec,schemas=schemas,block_size=size)
            except ValueError as ex:
                failures.append({'codec':codec,'block_size':size,'reason':str(ex)[:200]})
                continue
            encoding_ms=(time.perf_counter()-begin)*1000
            begin=time.perf_counter()
            restored=decode(data)
            decoding_ms=(time.perf_counter()-begin)*1000
            if restored!=records:raise ValueError('plan violates exact round trip')
            trials.append({'codec':codec,'block_size':size,'bytes':len(data),'encoding_ms':encoding_ms,'decoding_ms':decoding_ms})
    if not trials:raise ValueError('no representable encoding plan')
    best=min(t['bytes'] for t in trials)
    eligible=[t for t in trials if t['bytes']<=best*(1+tolerance)]
    selected=min(eligible,key=lambda t:(t['block_size'],t['bytes'],t['decoding_ms']))
    return {'selected':selected,'trials':trials,'unavailable':failures,'semantic_changes':0,'tolerance':tolerance}
