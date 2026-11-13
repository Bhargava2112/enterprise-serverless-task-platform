"""Offline policy-aware code review; optional LLM augmentation is advisory only."""
from dataclasses import dataclass,asdict
import ast
import json
import re

@dataclass(frozen=True)
class Finding:
    path:str
    line:int
    severity:str
    rule:str
    explanation:str

SECRET_PATTERNS=[('private-key',re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')),
                 ('aws-access-key',re.compile(r'AKIA[0-9A-Z]{16}')),
                 ('generic-secret',re.compile(r'(?i)(?:secret|api_key|token)\s*=\s*[\x27\x22][^\x27\x22\s]{12,}[\x27\x22]'))]

class PolicyReviewer:
    def review_file(self,path,source):
        if not isinstance(source,str):raise TypeError('source must be text')
        out=[]
        for n,line in enumerate(source.splitlines(),1):
            for rule,regex in SECRET_PATTERNS:
                if regex.search(line):out.append(Finding(path,n,'critical',rule,'Potential credential in source'))
            if re.search(r'\b(?:eval|exec)\s*\(',line):
                out.append(Finding(path,n,'high','dynamic-execution','Dynamic execution requires security review'))
            if re.search(r'\b(?:subprocess\.|os\.system)\b',line) and ('shell=True' in line or 'os.system' in line):
                out.append(Finding(path,n,'high','shell-execution','Shell command invocation requires user-input audit'))
        if path.endswith('.py'):
            try:
                tree=ast.parse(source)
            except SyntaxError as e:
                out.append(Finding(path,e.lineno or 1,'high','syntax','Python parse failure'))
            else:
                for node in ast.walk(tree):
                    if isinstance(node,ast.ExceptHandler) and node.type is None:
                        out.append(Finding(path,node.lineno,'medium','bare-except','Bare except may hide defects'))
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and len(node.body)>60:
                        out.append(Finding(path,node.lineno,'low','large-function','Review decomposition and testability'))
        return out
    def review_diff(self,unified):
        path=None;new_line=0;findings=[]
        for raw in unified.splitlines():
            if raw.startswith('+++ b/'):
                path=raw[6:];continue
            if raw.startswith('@@'):
                match=re.search(r'\+(\d+)',raw)
                if match:new_line=int(match.group(1))
                continue
            if not path or raw.startswith(('--- ','+++ ')):continue
            if raw.startswith('+'):
                line=raw[1:]
                for rule,pattern in SECRET_PATTERNS:
                    if pattern.search(line):findings.append(Finding(path,new_line,'critical',rule,'Potential credential added'))
                if re.search(r'\b(?:eval|exec)\s*\(',line):
                    findings.append(Finding(path,new_line,'high','dynamic-execution','Potentially unsafe dynamic execution added'))
                new_line+=1
            elif raw.startswith(' '):new_line+=1
        return findings

def gate(findings,block={'critical','high'}):
    return not any(f.severity in block for f in findings)

def summarize(findings,extra=None):
    return {'pass':gate(findings),'findings':[asdict(f) for f in findings],
            'advisory':extra or 'No LLM analysis configured. Deterministic checks only.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('file');args=p.parse_args()
    with open(args.file,encoding='utf-8') as f:report=summarize(PolicyReviewer().review_file(args.file,f.read()))
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['pass'] else 1)
