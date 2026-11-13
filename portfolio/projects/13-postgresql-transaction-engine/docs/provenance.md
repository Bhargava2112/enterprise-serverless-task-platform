# Portfolio provenance and claims

This project is newly authored portfolio reference code, independent of any employer source or private production service.

**What exists:** Accounts -> atomic transfer -> double-entry postings -> idempotency and consistency checks; tests in `tests/test_app.py`.

**What remains:** Use PostgreSQL SERIALIZABLE or ordered row locking, migrations, pgbouncer, metrics and stress tests.

**Limitations:** Runtime is SQLite-compatible adapter; supplied PostgreSQL schema has not been integration-tested.

Do not describe this project as a four- or five-year production deployment or claim measured users, performance, uptime, savings, AI accuracy, or business outcomes without independently collecting data.
