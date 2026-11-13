"""Explainable incident correlation with topology, baseline anomalies, evidence IDs."""
from dataclasses import dataclass
from datetime import datetime,timezone
from statistics import mean,pstdev
from collections import defaultdict
import json

@dataclass(frozen=True)
class Signal:
    id:str
    service:str
    time:int
    kind:str
    value:float
    description:str

class DependencyGraph:
    def __init__(self,edges):
        self.downstream=defaultdict(list)
        for upstream,dependent in edges:self.downstream[upstream].append(dependent)
    def impact_distance(self,origin,target):
        frontier=[(origin,0)];seen=set()
        while frontier:
            node,dist=frontier.pop(0)
            if node==target:return dist
            if node in seen:continue
            seen.add(node);frontier.extend((x,dist+1) for x in self.downstream[node])
        return None

def anomaly_score(baseline,observed):
    if len(baseline)<3:raise ValueError('need at least three baseline points')
    if not all(isinstance(x,(float,int)) for x in baseline):raise TypeError('numeric metric required')
    deviation=pstdev(baseline)
    return (observed-mean(baseline))/max(deviation,0.01)

class IncidentAnalyzer:
    def __init__(self,graph,window_seconds=900):
        if window_seconds<1:raise ValueError('invalid time window')
        self.graph=graph;self.window=window_seconds
    def analyze(self,impacted_service,incident_time,signals,baselines=None):
        baselines=baselines or {};candidates=[]
        for s in signals:
            dt=incident_time-s.time
            if not 0<=dt<=self.window:continue
            dist=self.graph.impact_distance(s.service,impacted_service)
            if dist is None:continue
            score=2.5/(1+dist)+1-dt/self.window
            reasons=['upstream impact distance '+str(dist)]
            if s.kind=='deployment':score+=1.0;reasons.append('change event')
            if s.kind=='error':score+=.5;reasons.append('error observed')
            if s.kind=='metric' and s.service in baselines:
                z=anomaly_score(baselines[s.service],s.value)
                score+=min(max(z,0),5)/2;reasons.append('z-score='+str(round(z,2)))
            candidates.append({'signal_id':s.id,'service':s.service,'score':round(score,4),
                               'reasons':reasons,'time':s.time,'description':s.description})
        candidates.sort(key=lambda x:(-x['score'],x['time'],x['signal_id']))
        if not candidates:return {'status':'insufficient-evidence','candidates':[],'timeline':[]}
        ambiguous=len(candidates)>1 and candidates[0]['score']-candidates[1]['score']<.4
        return {'status':'needs-review' if ambiguous else 'hypothesis','candidates':candidates[:5],
                'timeline':sorted([{'time':x['time'],'signal_id':x['signal_id']} for x in candidates],key=lambda x:x['time']),
                'confidence':'low' if ambiguous or candidates[0]['score']<3 else 'moderate',
                'note':'Correlation is not proof of causality. Human incident review required.'}

if __name__=='__main__':
    g=DependencyGraph([('db','api'),('api','web')]);a=IncidentAnalyzer(g)
    print(json.dumps(a.analyze('web',100,[Signal('deploy1','db',80,'deployment',0,'schema migration')]),indent=2))
