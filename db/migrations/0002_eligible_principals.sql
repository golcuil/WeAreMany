-- Eligible principals pool for matching (no sender/recipient edges).
CREATE TABLE IF NOT EXISTS eligible_principals (
  principal_id text PRIMARY KEY,
  intensity_bucket text NOT NULL CHECK (intensity_bucket IN ('low', 'medium', 'high')),
  theme_tags text[] NOT NULL DEFAULT '{}',
  last_active_bucket timestamptz NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS eligible_principals_intensity_last_active_idx
  ON eligible_principals (intensity_bucket, last_active_bucket DESC);

CREATE INDEX IF NOT EXISTS eligible_principals_last_active_idx
  ON eligible_principals (last_active_bucket DESC);

CREATE INDEX IF NOT EXISTS eligible_principals_theme_tags_gin
  ON eligible_principals USING GIN (theme_tags);
