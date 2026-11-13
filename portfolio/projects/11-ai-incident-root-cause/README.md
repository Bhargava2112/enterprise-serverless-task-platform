# AI-Powered Incident Root Cause Analysis

**Portfolio category:** AI-Integrated Engineering  
**Stack:** Python, topology, SLI anomalies, timelines  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind ai-powered incident root cause analysis: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Telemetry signals + service dependency DAG -> temporal correlation -> ranked hypotheses with evidence.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/11-ai-incident-root-cause
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Dependency impact distance.
- Anomaly z-scores.
- Confidence reduction on ties.
- Abstain on missing evidence.


## What this **does not** claim

Hypothesis engine, not demonstrated causal inference or an ML/LLM production incident system.

## Next production milestone

Integrate OpenTelemetry/Prometheus, deploy change events, robust baselines and human incident workflows.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
