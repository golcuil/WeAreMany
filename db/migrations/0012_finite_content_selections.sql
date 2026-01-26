-- Persist finite content selections per principal + day.
CREATE TABLE IF NOT EXISTS finite_content_selections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  principal_id text NOT NULL,
  day_key date NOT NULL,
  valence_bucket text NOT NULL,
  intensity_bucket text NOT NULL,
  theme_id text NULL,
  content_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (principal_id, day_key, valence_bucket, intensity_bucket, theme_id)
);

CREATE INDEX IF NOT EXISTS finite_content_selections_principal_day_idx
  ON finite_content_selections (principal_id, day_key DESC);
