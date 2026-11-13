# Portfolio provenance and claims

This project is newly authored portfolio reference code, independent of any employer source or private production service.

**What exists:** Input records -> immutable bronze -> validated silver/quarantine -> gold aggregations + dimension history; tests in `tests/test_app.py`.

**What remains:** Move storage to ADLS Gen2/Delta tables, orchestrate with ADF/Fabric, use Synapse analytics.

**Limitations:** Local transactional approximation rather than Delta Lake, Spark or Fabric deployment.

Do not describe this project as a four- or five-year production deployment or claim measured users, performance, uptime, savings, AI accuracy, or business outcomes without independently collecting data.
