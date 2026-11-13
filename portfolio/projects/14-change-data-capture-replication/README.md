# Change Data Capture / Replication System

**Portfolio category:** Database Engineering  
**Stack:** Python, SQLite WAL-like outbox, checkpoints  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind change data capture / replication system: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Transactional source changelog -> ordered polling -> atomic sink apply + offset commit.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/14-change-data-capture-replication
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Gap detection.
- Sink deduplication.
- Atomic checkpoints.
- Schema-flexible json payloads.


## What this **does not** claim

Reference changelog is application-managed SQLite, not real PostgreSQL WAL/ Debezium.

## Next production milestone

Connect Debezium PostgreSQL logical decoding to Kafka, schema registry and partitioned target sink.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
