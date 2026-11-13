# ADR-0001: Tenant-scoped DynamoDB single-table design

**Status:** Accepted for this reference project.

**Decision:** Store tasks and audit events under a shared tenant partition, separate entity types with sort-key prefixes, and add a sparse GSI for per-owner task listings.

**Why:** Tenant partition boundaries make cross-tenant access restrictions explicit, the GSI avoids inefficient filtered scans for ordinary users, and DynamoDB transactions guarantee all-or-nothing task changes and audit insertion.

**Tradeoffs:** A GSI is eventually consistent, transactions incur more write capacity, a large tenant can create hot partitions, and archival policies will need an event lifecycle strategy.

**Alternatives:** Separate task/audit tables, PostgreSQL with RLS and transactional audit, tenant-per-table or event-sourced aggregate persistence. Select based on workload, cost, consistency and retention requirements.
