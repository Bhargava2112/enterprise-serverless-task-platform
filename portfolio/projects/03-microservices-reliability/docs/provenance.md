# Portfolio provenance and claims

This project is newly authored portfolio reference code, independent of any employer source or private production service.

**What exists:** Client -> retry policy -> circuit breaker -> bounded bulkhead -> upstream dependency; tests in `tests/test_app.py`.

**What remains:** Deploy on ECS/EKS with OpenTelemetry, Prometheus, fault-injection jobs and burn-rate alerts.

**Limitations:** Library-level resilience primitives only; no running service fleet or real chaos platform.

Do not describe this project as a four- or five-year production deployment or claim measured users, performance, uptime, savings, AI accuracy, or business outcomes without independently collecting data.
