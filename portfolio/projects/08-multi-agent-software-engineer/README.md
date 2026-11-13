# Multi-Agent Software Engineering Assistant

**Portfolio category:** Generative AI / Agents  
**Stack:** Python, orchestrator, state machine, approval gate, audit chain  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind multi-agent software engineering assistant: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Task DAG -> worker proposal -> reviewer verdict -> human approval -> auditable patch proposal.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/08-multi-agent-software-engineer
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Bounded steps and patches.
- Dependency gating.
- Path/secret checks.
- Tamper-evident event log.


## What this **does not** claim

Agents are injectable deterministic functions; no autonomous commits, deployment or external LLM calls.

## Next production milestone

Integrate vetted LLM role adapters, isolated filesystem, code sandbox, policy enforcement and PR workflow.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
