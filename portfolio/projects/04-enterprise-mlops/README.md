# Enterprise MLOps Platform

**Portfolio category:** Azure / Machine Learning  
**Stack:** Python, reproducible logistic ML, registry, drift PSI  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind enterprise mlops platform: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Validated features -> deterministic train/split -> evaluation quality gate -> immutable registry -> inference.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/04-enterprise-mlops
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Schema and model signature.
- Stratified reproducible split.
- Promotion threshold.
- Drift signal.


## What this **does not** claim

Reference baseline uses standard-library logistic regression; no Azure ML job or online model deployed.

## Next production milestone

Connect to Azure ML pipelines, managed online endpoints, Key Vault, feature store and monitoring.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
