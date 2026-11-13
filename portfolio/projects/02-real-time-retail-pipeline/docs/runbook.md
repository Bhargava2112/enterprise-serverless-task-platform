# Operational runbook: Real-Time Retail Data Processing Platform

## Development verification

Run `PYTHONPATH=src python -m unittest discover -s tests -v` and inspect failures before merging. The default implementation uses no external services.

## Failure response

1. Identify which input or state transition failed; reproduce from synthetic fixtures.
2. Verify validation, idempotency, and atomic rollback behavior in the affected code path.
3. Record a failing regression test before changing business logic.
4. Re-run all local tests, then any connected provider integration tests.
5. For cloud deploys, use a staged rollout, feature flags, metrics, budgets and rollback playbook.

## Metrics to add in deployed environments

- Success/error rate and p95/p99 latency under realistic load.
- Dependency health, retry amplification and task/consumer backlog where relevant.
- Data accuracy, freshness, audit failures and alert triage time.
- Security violations, cost per request and recovery time.

No production metrics have been collected for this reference code.
