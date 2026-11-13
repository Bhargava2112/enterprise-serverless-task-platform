# Engineering interview guide

This work demonstrates the types of engineering decisions expected from a mid-level cloud/backend developer. It is independent portfolio code rather than a claim of past employer work.

## Discuss the following tradeoffs

1. **Isolation:** JWT authorizer -> immutable Cognito attributes -> tenant partition keys -> per-owner authorization; potential pitfalls with direct Lambda invocation.
2. **Database access:** Primary tenant key versus OwnerIndex; consistent GetItem versus eventually consistent GSI Query; partition hotspots and changing access patterns.
3. **Correctness:** Conditional expected-version checks for concurrency, atomic DynamoDB task+audit transactions, and what happens when clients retry a successful request after a timeout.
4. **Reliability:** Why an idempotency-key design is a future feature and how to add it safely, including retention and request-body fingerprinting.
5. **Scalability:** Lambda concurrency, DynamoDB adaptive capacity and limits, noisy tenants, and cost of additional transaction write units.
6. **Delivery:** Why IAM credentials are not stored in the repository, why CI tests use an emulator, and what live AWS tests should prove before deployment.

## Resume-style wording (only after verifying completion)

- Designed a multi-tenant AWS serverless task API using API Gateway, Lambda and DynamoDB, with Cognito JWT identity enforcement and per-user authorization.
- Implemented version-conditional DynamoDB transactions to prevent lost updates and ensure task mutations atomically generate audit events.
- Documented database access patterns, GSI consistency tradeoffs, architecture decisions, and security boundaries; created automated tests and CI checks.

Do **not** add latency improvements, throughput, production user counts, cost reductions, or deployment claims without real evidence.
