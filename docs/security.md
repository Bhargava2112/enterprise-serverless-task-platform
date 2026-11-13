# Security boundary

- API Gateway is the JWT trust boundary. Direct Lambda invoke permissions must remain restricted.
- Cognito user `custom:tenant_id` and `custom:role` are immutable and **not** writable by the user-pool client. Provision trusted users administratively; there is no self-service tenant registration.
- The sample client sends a Cognito **ID token** carrying the custom claims. Verify this flow on a live deployment before production use.
- Member permissions are enforced by owner checks and a tenant-user GSI. Tenant admins can access only records for their authenticated tenant.
- Audit records are atomically written with task mutations. They're not a complete compliance system and need retention controls.
- Never log access tokens, user PII or secret configuration. A production deployment needs IAM review, WAF/rate limiting where appropriate, CloudWatch alarms, CloudTrail, key rotation and an incident response plan.
- Cursors are opaque and bound to scope for accidental reuse prevention, but are not signed tokens; query identity and partition conditions independently protect data access.
