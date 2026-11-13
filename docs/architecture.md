# Architecture and operational tradeoffs

**Entry point:** API Gateway HTTP API validates a Cognito-signed JWT against the configured issuer and client audience. The Lambda reads its API Gateway JWT claim context rather than unverified headers. The public route is only `GET /health`.

**Storage:** A tenant-scoped partition key `TENANT#id` holds task (`TASK#uuid`) and audit (`EVENT#iso-time#uuid`) records; a GSI `OwnerIndex` keyed `TENANT#id#USER#sub` supports member listings without scans.

**Consistency:** Tasks are written with `TransactWriteItems` together with their immutable audit entry. Updates/deletes use conditional version checks to prevent lost updates. `GetItem` uses strong consistency. The GSI offers eventual consistency on listings.

**Scaling:** Lambda and on-demand DynamoDB remove server fleet management, but extremely large tenants can generate hot partitions. Transactions consume more write capacity; log/audit retention requires an explicit lifecycle design. Benchmark p50/p95/p99 latency, AWS billing and error rates before offering performance claims.

**Constraints:** A front end, event-driven notifications, production alarms, disaster-recovery testing and real-provider integration tests remain planned work.
