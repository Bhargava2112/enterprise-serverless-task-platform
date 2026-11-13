# Enterprise Data Warehouse / Incremental ETL

**Portfolio category:** Database Engineering  
**Stack:** Python, SQLite reference, star schema, SCD2  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind enterprise data warehouse / incremental etl: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Products changes -> type-2 dimensions -> event-time surrogate lookup -> facts -> reconciled aggregates.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/15-incremental-enterprise-warehouse
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Event-time scd2 joins.
- Batch fingerprints.
- Quarantine.
- Referential integrity.


## What this **does not** claim

Local SQL prototype; no live warehouse/cloud resources or production benchmarks.

## Next production milestone

Move to Snowflake, PostgreSQL or Azure Synapse; add Airflow, partition management, SLA monitoring.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
