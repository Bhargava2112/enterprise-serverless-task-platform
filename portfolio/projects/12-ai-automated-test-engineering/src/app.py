"""AST-guided test-plan synthesizer, Python contract test runner and audit artifacts."""
import ast
from dataclasses import dataclass,asdict
import json
import subprocess
import sys
from pathlib import Path

class AnalysisError(ValueError):pass

@dataclass(frozen=True)
class TestIdea:
    function:str
    kind:str
    description:str
    line:int

class TestPlanner:
    def analyze(self,source):
        try:tree=ast.parse(source)
        except SyntaxError as e:raise AnalysisError(str(e)) from e
        ideas=[]
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
            ideas.append(TestIdea(node.name,'happy-path','Verify documented nominal inputs and output contract',node.lineno))
            for child in ast.walk(node):
                if isinstance(child,ast.If):
                    ideas.append(TestIdea(node.name,'branch','Exercise both outcomes of conditional at line '+str(child.lineno),child.lineno))
                elif isinstance(child,ast.Raise):
                    ideas.append(TestIdea(node.name,'error-path','Assert raised exception type and message',child.lineno))
                elif isinstance(child,(ast.For,ast.While)):
                    ideas.append(TestIdea(node.name,'boundary','Cover empty, one-item and many-item iteration',child.lineno))
            if len(node.args.args)>0:
                ideas.append(TestIdea(node.name,'invalid-input','Try None, empty input, wrong types and boundary values',node.lineno))
        return list(dict.fromkeys(ideas))
    def to_json(self,source):return json.dumps([asdict(x) for x in self.analyze(source)],indent=2)

class ContractRunner:
    """Only execute tests from trusted local checkout; not a security sandbox."""
    def __init__(self,timeout=15):
        if not 1<=timeout<=300:raise ValueError('invalid timeout')
        self.timeout=timeout
    def run(self,test_directory):
        folder=Path(test_directory).resolve()
        if not folder.is_dir():raise FileNotFoundError(folder)
        try:
            result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(folder),'-v'],
                                  capture_output=True,text=True,timeout=self.timeout,cwd=folder.parent)
            return {'status':'passed' if result.returncode==0 else 'failed','exit_code':result.returncode,
                    'stdout':result.stdout[-12000:],'stderr':result.stderr[-12000:]}
        except subprocess.TimeoutExpired:
            return {'status':'timeout','exit_code':124,'stdout':'','stderr':'Test runtime exceeded limit'}

def summarize_coverage(ideas,verified_kinds):
    groups={x.kind for x in ideas}
    matched=groups.intersection(verified_kinds)
    return {'categories':len(groups),'validated':len(matched),
            'uncovered':sorted(groups-matched),'coverage_ratio':len(matched)/len(groups) if groups else 1.0}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('python_file');args=p.parse_args()
    print(TestPlanner().to_json(Path(args.python_file).read_text()))
