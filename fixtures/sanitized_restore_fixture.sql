-- Sanitized restore fixture (no identifiers, no message text).
-- This file is used only for CI restore dry-run validation.

CREATE TABLE IF NOT EXISTS restore_fixture_check (
  id text PRIMARY KEY,
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO restore_fixture_check (id)
VALUES ('fixture_ok')
ON CONFLICT DO NOTHING;
