-- Production target schema for PostgreSQL 16+. Validate under a real PostgreSQL instance before launch.
CREATE TABLE IF NOT EXISTS accounts(
 id UUID PRIMARY KEY, balance_cents BIGINT NOT NULL CHECK(balance_cents >= 0), version BIGINT NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS transfers(
 id UUID PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE,
 from_id UUID NOT NULL REFERENCES accounts(id), to_id UUID NOT NULL REFERENCES accounts(id),
 cents BIGINT NOT NULL CHECK(cents > 0), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT different_accounts CHECK(from_id <> to_id));
CREATE TABLE IF NOT EXISTS ledger_entries(
 transfer_id UUID NOT NULL REFERENCES transfers(id), account_id UUID NOT NULL REFERENCES accounts(id),
 delta_cents BIGINT NOT NULL, PRIMARY KEY(transfer_id, account_id));
CREATE INDEX IF NOT EXISTS transfer_from_lookup ON transfers(from_id, created_at DESC);
CREATE INDEX IF NOT EXISTS transfer_to_lookup ON transfers(to_id, created_at DESC);
-- Application transaction: SELECT both accounts FOR UPDATE in sorted UUID order; validate
-- nonnegative balances, insert transfer and two ledger entries, UPDATE both account versions,
-- and COMMIT. Use SERIALIZABLE or targeted locks with retry for serialization failures.
