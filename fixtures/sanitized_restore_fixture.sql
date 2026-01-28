-- Sanitized restore fixture (schema-only ledger, no app tables, no data).
-- Used only for CI restore dry-run validation.

CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  checksum TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
