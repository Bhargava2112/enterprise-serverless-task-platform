# Intelligent Enterprise Data Lakehouse

**Portfolio category:** Azure / Data Engineering  
**Stack:** Python, SQLite, bronze/silver/gold, SCD2, lineage  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind intelligent enterprise data lakehouse: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Input records -> immutable bronze -> validated silver/quarantine -> gold aggregations + dimension history.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/05-enterprise-lakehouse
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Hash-linked ingestion provenance.
- Replay-safe run ids.
- Row-level quarantine.
- Scd2 history.


## What this **does not** claim

Local transactional approximation rather than Delta Lake, Spark or Fabric deployment.

## Next production milestone

Move storage to ADLS Gen2/Delta tables, orchestrate with ADF/Fabric, use Synapse analytics.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
