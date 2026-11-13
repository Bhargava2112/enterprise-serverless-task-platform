# Architecture: Real-Time Retail Data Processing Platform

## Context and requirements

Goal: Retail ingest -> atomic outbox -> ordered projector -> stock and revenue projections.

**Functional goals:** idempotent event processing, rollback on insufficient stock, strict per-order ordering, durable outbox replay.

**Quality attributes:** integrity, repeatable execution, clear failure handling, auditability, observability, documented extension points and readable interfaces.

## System boundary

This repository runs without cloud dependencies using a local reference adapter. It isolates core state transformations, contracts and validation from provider-specific integration. For distributed/cloud systems, this is the domain-level design; adapters and runtime infrastructure must be added and validated in a real environment.

## Data flow

```mermaid
flowchart LR
  Input[Validated Input] --> Core[Domain / Policy Engine]
  Core --> State[(Durable State or Model)]
  Core --> Output[Auditable Result]
  Output --> Ops[Diagnostics and SLO Review]
```

## Important tradeoffs

- **Correctness before throughput:** atomic operations, schema guards and deterministic replay are prioritized over speculative speed claims.
- **Operational realism:** source and sink failures must be observable; a live deployment requires tracing, alerting, secrets and infrastructure ownership.
- **Security boundary:** local reference behavior does not replace proper authentication, RBAC, encryption, IAM or network isolation.
- **Cost:** no cloud resource was provisioned. Establish budgets, retention limits and measured usage before rolling out.

## Production target

Publish to Kinesis or MSK, project into DynamoDB/S3, configure DLQs and lag alerts.

## Declared limitation

No Kafka, Kinesis, or cloud resources provisioned; consumer reference is synchronous SQLite.
