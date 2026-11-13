# Portfolio provenance and claims

This project is newly authored portfolio reference code, independent of any employer source or private production service.

**What exists:** Transactional source changelog -> ordered polling -> atomic sink apply + offset commit; tests in `tests/test_app.py`.

**What remains:** Connect Debezium PostgreSQL logical decoding to Kafka, schema registry and partitioned target sink.

**Limitations:** Reference changelog is application-managed SQLite, not real PostgreSQL WAL/ Debezium.

Do not describe this project as a four- or five-year production deployment or claim measured users, performance, uptime, savings, AI accuracy, or business outcomes without independently collecting data.
