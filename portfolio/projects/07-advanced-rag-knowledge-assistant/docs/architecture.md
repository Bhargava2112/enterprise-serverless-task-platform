# Architecture: Advanced RAG Enterprise Knowledge Assistant

## Context and requirements

Goal: Document -> overlapping chunk -> tenant-scoped BM25 -> retrieved excerpts -> optional generator -> source checks.

**Functional goals:** tenant-scoped ranking, source ACL, reference ids, retrieval recall evaluation.

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

Add hybrid vectors, durable vector index, authz gateway, LLM adapter, safety evaluations and prompt-injection testing.

## Declared limitation

Offline lexical search and optional generation interface; no remote LLM or embedding provider configured.
