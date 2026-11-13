#!/usr/bin/env python3
"""Execute every project's documented CLI smoke example."""
from pathlib import Path
import os
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
for project in sorted((root/'projects').iterdir()):
    if not project.is_dir():continue
    env=os.environ.copy();env['PYTHONPATH']=str(project/'src')
    args=[sys.executable,str(project/'src'/'app.py')]
    if project.name.startswith('10-'):args.append(str(root/'projects'/'03-microservices-reliability'/'src'/'app.py'))
    if project.name.startswith('12-'):args.append(str(project/'src'/'app.py'))
    result=subprocess.run(args,env=env,cwd=project,capture_output=True,text=True,timeout=20)
    print(project.name, 'PASS' if result.returncode==0 else 'FAIL',result.stdout[-200:])
    if result.returncode:print(result.stderr);raise SystemExit(1)
