"""Persisted independent-origin calibration, stratification and drift monitoring."""
import math
from collections import defaultdict

from ..autonomy.panel import wilson_upper
from ..config import Calibration
from ..core.values import Component
from ..storage.schema import WriterRole as W
from ..util import canonical_json, sha256_hex


class Calibrator:
    def __init__(self,db,config):
        self.db,self.config=db,config

    def observe(self,key,category,confidence,correct,origin):
        if not all(isinstance(x,str) and 0<len(x)<=200 for x in (key,category,origin)):
            raise ValueError('bounded calibration identities required')
        if type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0<=confidence<=1 or type(correct) is not bool:
            raise ValueError('calibration sample')
        with self.db.write(W.CALIBRATOR) as t:
            old=t.one('SELECT category,confidence,correct,origin FROM calibration_observation WHERE observation_key=?',(key,))
            expected=(category,confidence,int(correct),origin)
            if old and tuple(old)!=expected:
                raise ValueError('observation identities are immutable')
            t.execute('INSERT OR IGNORE INTO calibration_observation VALUES(?,?,?,?,?,?)',(key,*expected,self.db.clock.now()))

    def report(self,category,window=2000):
        if type(window) is not int or not 20<=window<=10000:
            raise ValueError('calibration window')
        with self.db.read() as r:
            rows=r.query('SELECT * FROM calibration_observation WHERE category=? ORDER BY at DESC,observation_key DESC LIMIT ?',(category,window))
        # Count each origin once, using its newest sample; repetitions cannot
        # manufacture precision or satisfy the minimum calibration sample gate.
        seen=set(); samples=[]
        for row in rows:
            if row['origin'] not in seen:
                seen.add(row['origin']);samples.append(row)
        bins=defaultdict(list)
        for row in samples:
            bins[min(9,int(row['confidence']*10))].append(row)
        minimum=self.config['ece_min_samples_per_bin']
        enough=bool(bins) and all(len(xs)>=minimum for xs in bins.values())
        ece=sum(abs(sum(x['confidence'] for x in xs)/len(xs)-sum(x['correct'] for x in xs)/len(xs))*len(xs) for xs in bins.values())/max(1,len(samples))
        errors=sum(1-x['correct'] for x in samples)
        half=len(samples)//2
        recent=sum(1-x['correct'] for x in samples[:half])/max(1,half)
        prior=sum(1-x['correct'] for x in samples[half:])/max(1,len(samples)-half)
        drift=len(samples)>=2*minimum and recent-prior>self.config['ece_threshold']
        return {'category':category,'independent_samples':len(samples),'bins':{str(k):len(v) for k,v in bins.items()},
                'ece':ece,'error_upper_bound':wilson_upper(errors,len(samples)),
                'calibrated':enough and ece<=self.config['ece_threshold'] and not drift,'drift':drift,
                'action':'DEFER_HIGH_RISK' if not enough or drift or ece>self.config['ece_threshold'] else 'CALIBRATED'}

    def tune(self,name,value,run_id,evidence):
        """Only measured, calibrated categories can alter non-pinned constants."""
        report=self.report(evidence)
        if not report['calibrated']:
            raise ValueError('insufficient calibrated evidence')
        # Validate on a copy before persisting. Publication precedes in-memory
        # activation so failed writes cannot leave an unaudited active value.
        from ..config import Config
        probe=Config(self.config.snapshot())
        probe.calibrate(name,value,run_id,evidence)
        with self.db.write(W.CALIBRATOR) as t:
            t.execute('INSERT INTO constant_calibration(at,name,old_value,new_value,run_id,evidence) VALUES(?,?,?,?,?,?)',
                      (self.db.clock.now(),name,canonical_json(self.config[name]),canonical_json(value),run_id,canonical_json(report)))
            t.audit(Component.VALIDATOR,'CONSTANT_CALIBRATED',name,sha256_hex(canonical_json(report)))
        return self.config.calibrate(name,value,run_id,evidence)

    def restore(self):
        import json
        with self.db.read() as r:
            rows=r.query('SELECT * FROM constant_calibration ORDER BY id')
        for row in rows:
            self.config.calibrate(row['name'],json.loads(row['new_value']),row['run_id'],row['evidence'])
        return len(rows)
