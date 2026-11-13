# Cloud-Native Microservices Reliability Platform

**Portfolio category:** AWS / Distributed Systems  
**Stack:** Python, concurrency, circuit breaker, SLI/SLO  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind cloud-native microservices reliability platform: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Client -> retry policy -> circuit breaker -> bounded bulkhead -> upstream dependency.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/03-microservices-reliability
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Half-open recovery.
- Fail-fast capacity controls.
- No silent retries on non-idempotent writes.
- Latency and error-budget metrics.


## What this **does not** claim

Library-level resilience primitives only; no running service fleet or real chaos platform.

## Next production milestone

Deploy on ECS/EKS with OpenTelemetry, Prometheus, fault-injection jobs and burn-rate alerts.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
