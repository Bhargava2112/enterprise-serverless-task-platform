"""Reproducible binary ML pipeline, signed input schema, model registry, drift."""
import csv
import hashlib
import json
import math
import os
import random
from datetime import datetime,timezone
from pathlib import Path

class SchemaError(ValueError):pass
FEATURES=('throughput','error_rate','queue_depth')

def validate(row,labeled=False):
    try:
        values=[float(row[f]) for f in FEATURES]
        if any(not math.isfinite(v) for v in values):raise ValueError()
        if labeled and int(row['label']) not in (0,1):raise ValueError()
        return values
    except (KeyError,ValueError,TypeError,OverflowError) as e:raise SchemaError('invalid feature schema') from e

def sigmoid(z):
    return 1/(1+math.exp(-max(-60,min(60,z))))

class LogisticModel:
    def __init__(self,weights=None,mean=None,scale=None):
        self.weights=list(weights or [0.0]*4);self.mean=list(mean or [0.0]*3);self.scale=list(scale or [1.0]*3)
    def predict_proba(self,row):
        x=validate(row);v=[(a-m)/s for a,m,s in zip(x,self.mean,self.scale)]
        return sigmoid(self.weights[0]+sum(w*f for w,f in zip(self.weights[1:],v)))
    @classmethod
    def train(cls,rows,epochs=600,lr=.1,seed=41):
        rows=list(rows)
        if len(rows)<8:raise ValueError('need at least 8 samples')
        features=[validate(r,labeled=True) for r in rows]
        labels=[int(r['label']) for r in rows]
        if len(set(labels))!=2:raise ValueError('two classes required')
        means=[sum(v[i] for v in features)/len(features) for i in range(3)]
        scales=[max((sum((v[i]-means[i])**2 for v in features)/len(features))**.5,1e-9) for i in range(3)]
        x=[[1.0]+[(v[i]-means[i])/scales[i] for i in range(3)] for v in features]
        weights=[0.0]*4
        for _ in range(epochs):
            gradient=[0.0]*4
            for v,y in zip(x,labels):
                error=sigmoid(sum(w*t for w,t in zip(weights,v)))-y
                for j in range(4):gradient[j]+=error*v[j]
            for j in range(4):weights[j]-=lr*(gradient[j]/len(x)+(.001*weights[j] if j else 0))
        return cls(weights,means,scales)
    def serialize(self):return {'weights':self.weights,'mean':self.mean,'scale':self.scale,'features':FEATURES}
    @classmethod
    def deserialize(cls,obj):
        if tuple(obj['features'])!=FEATURES or any(len(obj[k])!=n for k,n in [('weights',4),('mean',3),('scale',3)]):
            raise SchemaError('model signature mismatch')
        return cls(obj['weights'],obj['mean'],obj['scale'])

def stratified_split(rows,test_fraction=.25,seed=7):
    buckets={0:[],1:[]};rng=random.Random(seed)
    for r in rows:
        validate(r,True);buckets[int(r['label'])].append(r)
    if min(map(len,buckets.values()))<2:raise ValueError('insufficient class samples')
    train=[];test=[]
    for group in buckets.values():
        group=group.copy();rng.shuffle(group)
        n=min(len(group)-1,max(1,round(len(group)*test_fraction)))
        test.extend(group[:n]);train.extend(group[n:])
    return train,test

def evaluate(model,rows,threshold=.5):
    tp=tn=fp=fn=0
    for row in rows:
        actual=int(row['label']);pred=int(model.predict_proba(row)>=threshold)
        if actual and pred:tp+=1
        elif not actual and not pred:tn+=1
        elif pred:fp+=1
        else:fn+=1
    return {'precision':tp/(tp+fp) if tp+fp else 0,'recall':tp/(tp+fn) if tp+fn else 0,
            'accuracy':(tp+tn)/(tp+tn+fp+fn) if rows else 0,'confusion':{'tp':tp,'tn':tn,'fp':fp,'fn':fn}}

class Registry:
    def __init__(self,folder):self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
    def register(self,model,metrics,data_hash):
        payload={'model':model.serialize(),'metrics':metrics,'training_sha256':data_hash,
                 'registered_utc':datetime.now(timezone.utc).isoformat(),'status':'staging'}
        canonical=json.dumps(payload,sort_keys=True).encode()
        key=hashlib.sha256(canonical).hexdigest()[:16]
        dest=self.folder/f'{key}.json';temp=self.folder/f'{key}.tmp'
        temp.write_bytes(canonical);os.replace(temp,dest)
        return key
    def promote(self,key,min_accuracy=.75):
        record=self.load(key)
        if record['metrics']['accuracy']<min_accuracy:raise ValueError('quality gate failed')
        manifest=self.folder/'production.json';temp=self.folder/'production.tmp'
        temp.write_text(json.dumps({'model_version':key}));os.replace(temp,manifest)
    def load(self,key):
        if not key or any(c not in '0123456789abcdef' for c in key):raise ValueError('bad version')
        return json.loads((self.folder/f'{key}.json').read_text())
    def production(self):
        key=json.loads((self.folder/'production.json').read_text())['model_version']
        return LogisticModel.deserialize(self.load(key)['model'])

def population_stability_index(reference,current,bins=(0,.1,.25,.5,1,2,5,10,float('inf'))):
    if not reference or not current:raise ValueError('empty distribution')
    def proportions(values):
        counts=[0]*len(bins)
        for v in values:
            if not math.isfinite(v):raise ValueError('nonfinite value')
            counts[next((i for i,top in enumerate(bins) if v<top),len(bins)-1)]+=1
        return [max(c/len(values),1e-4) for c in counts]
    old,new=proportions(reference),proportions(current)
    return sum((a-b)*math.log(a/b) for a,b in zip(old,new))

if __name__=='__main__':
    sample=[{'throughput':i,'error_rate':i/100,'queue_depth':i//2,'label':int(i>=15)} for i in range(30)]
    train,test=stratified_split(sample);model=LogisticModel.train(train)
    print(json.dumps(evaluate(model,test)))
