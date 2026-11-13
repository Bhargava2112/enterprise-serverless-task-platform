#!/usr/bin/env python3
"""Run local unit suites for all independent portfolio projects."""
from pathlib import Path
import os
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
count=0
for project in sorted((root/'projects').iterdir()):
    if not project.is_dir():continue
    env=os.environ.copy();env['PYTHONPATH']=str(project/'src')
    print(f'\n>>> {project.name}',flush=True)
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(project/'tests'),'-v'],env=env,timeout=90)
    if result.returncode:raise SystemExit(result.returncode)
    count+=1
print(f'\nPASS: {count} project test suites',flush=True)
