# Portfolio provenance and claims

This project is newly authored portfolio reference code, independent of any employer source or private production service.

**What exists:** Retail ingest -> atomic outbox -> ordered projector -> stock and revenue projections; tests in `tests/test_app.py`.

**What remains:** Publish to Kinesis or MSK, project into DynamoDB/S3, configure DLQs and lag alerts.

**Limitations:** No Kafka, Kinesis, or cloud resources provisioned; consumer reference is synchronous SQLite.

Do not describe this project as a four- or five-year production deployment or claim measured users, performance, uptime, savings, AI accuracy, or business outcomes without independently collecting data.
