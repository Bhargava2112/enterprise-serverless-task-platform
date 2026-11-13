# Real-Time Retail Data Processing Platform

**Portfolio category:** AWS / Data Engineering  
**Stack:** Python, SQLite reference, event-stream/outbox patterns  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind real-time retail data processing platform: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Retail ingest -> atomic outbox -> ordered projector -> stock and revenue projections.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/02-real-time-retail-pipeline
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Idempotent event processing.
- Rollback on insufficient stock.
- Strict per-order ordering.
- Durable outbox replay.


## What this **does not** claim

No Kafka, Kinesis, or cloud resources provisioned; consumer reference is synchronous SQLite.

## Next production milestone

Publish to Kinesis or MSK, project into DynamoDB/S3, configure DLQs and lag alerts.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
