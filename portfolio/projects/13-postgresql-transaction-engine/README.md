# PostgreSQL Transaction Engine

**Portfolio category:** Database Engineering  
**Stack:** Python, SQLite test adapter, PostgreSQL schema  
**Stage:** Tested local engineering reference; cloud deployment not claimed.

## Problem and solution

This standalone implementation addresses key engineering concerns behind postgresql transaction engine: correctness, isolation, observability, fault handling and a maintainable test boundary. It provides runnable code rather than a concept-only notebook.

## Architecture

Accounts -> atomic transfer -> double-entry postings -> idempotency and consistency checks.

See [architecture / design decisions](docs/architecture.md), [security model](docs/security.md), [operational runbook](docs/runbook.md), [testing notes](docs/testing.md), and [provenance](docs/provenance.md).

## Quick start (Python 3.12+)

```bash
cd projects/13-postgresql-transaction-engine
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python src/app.py
```

No environment variables, paid APIs, secrets or cloud accounts are needed for the local tests. The production target would need its own deployment, monitoring, IAM and real integration tests.

## Engineering focus

- Double entry.
- Duplicate-safe request ids.
- Atomic rollback.
- Version guards.


## What this **does not** claim

Runtime is SQLite-compatible adapter; supplied PostgreSQL schema has not been integration-tested.

## Next production milestone

Use PostgreSQL SERIALIZABLE or ordered row locking, migrations, pgbouncer, metrics and stress tests.

## Interview guidance

Discuss *design decisions and their limitations* rather than claiming production-scale numbers or work experience not supported by these files. See docs/provenance.md for the evidence boundary.
