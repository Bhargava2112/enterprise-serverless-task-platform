"""Bounded multi-agent planning/review workflow, human-gated changes and audit."""
from dataclasses import dataclass,field
from datetime import datetime,timezone
from pathlib import PurePosixPath
import hashlib
import json

class WorkflowError(RuntimeError):pass

def safe_path(filename):
    p=PurePosixPath(filename)
    if p.is_absolute() or '..' in p.parts or not p.parts or '\\' in filename or p.parts[0].startswith('.'):
        raise WorkflowError('unsafe or hidden path')
    return str(p)

@dataclass
class Task:
    id:str
    requirement:str
    dependencies:list=field(default_factory=list)
    status:str='queued'
    proposal:dict|None=None
    review:str=''

class AuditLog:
    def __init__(self):self.events=[]
    def append(self,task,action,details):
        prior=self.events[-1]['hash'] if self.events else 'genesis'
        payload={'task':task,'action':action,'details':details,'prior':prior}
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        self.events.append({**payload,'hash':digest})
    def verify(self):
        previous='genesis'
        for event in self.events:
            payload={k:event[k] for k in ('task','action','details','prior')}
            if event['prior']!=previous or hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()!=event['hash']:
                return False
            previous=event['hash']
        return True

class EngineeringWorkflow:
    def __init__(self,worker,reviewer,max_steps=10,max_bytes=16000):
        if max_steps<1 or max_bytes<1:raise ValueError('invalid limits')
        self.tasks={};self.worker=worker;self.reviewer=reviewer
        self.max_steps=max_steps;self.max_bytes=max_bytes;self.audit=AuditLog();self.steps=0
    def schedule(self,task_id,requirement,deps=()):
        if task_id in self.tasks or task_id in deps:raise WorkflowError('duplicate or circular task')
        if any(dep not in self.tasks for dep in deps):raise WorkflowError('dependency not found')
        self.tasks[task_id]=Task(task_id,requirement,list(deps));self.audit.append(task_id,'queued',{'dependencies':list(deps)})
    def advance(self,task_id):
        task=self.tasks[task_id]
        if self.steps>=self.max_steps:raise WorkflowError('step budget exceeded')
        if task.status!='queued':raise WorkflowError('invalid transition')
        if any(self.tasks[d].status!='approved' for d in task.dependencies):raise WorkflowError('dependency not approved')
        self.steps+=1
        proposal=self.worker(task.requirement)
        if not isinstance(proposal,dict) or not isinstance(proposal.get('path'),str) or not isinstance(proposal.get('content'),str):
            raise WorkflowError('invalid patch proposal')
        filename=safe_path(proposal['path'])
        if len(proposal['content'].encode())>self.max_bytes:raise WorkflowError('patch too large')
        if any(p in proposal['content'].lower() for p in ['-----begin private key-----','aws_secret_access_key=']):
            raise WorkflowError('secret-like content rejected')
        task.proposal={'path':filename,'content':proposal['content']};task.status='review'
        self.audit.append(task_id,'proposed',{'path':filename,'sha256':hashlib.sha256(proposal['content'].encode()).hexdigest()})
        verdict=self.reviewer(task.requirement,task.proposal)
        if verdict not in ('accept','reject'):raise WorkflowError('reviewer must accept/reject')
        task.review=verdict;task.status='awaiting-human' if verdict=='accept' else 'rejected'
        self.audit.append(task_id,'reviewed',{'verdict':verdict})
        return task.status
    def human_approve(self,task_id,approved):
        task=self.tasks[task_id]
        if task.status!='awaiting-human':raise WorkflowError('review required before approval')
        task.status='approved' if approved else 'rejected'
        self.audit.append(task_id,'human-decision',{'approved':bool(approved)})
        # Does not execute arbitrary model-generated code or merge to a repo.
        return task.proposal if approved else None
    def report(self):return {'steps':self.steps,'states':{i:t.status for i,t in self.tasks.items()},'audit_verified':self.audit.verify()}

if __name__=='__main__':
    f=EngineeringWorkflow(lambda req:{'path':'src/demo.py','content':'print("hello")\n'},lambda req,patch:'accept')
    f.schedule('t1','create a demo');f.advance('t1');print(json.dumps(f.report()))
