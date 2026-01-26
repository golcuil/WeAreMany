-- Matching tuning parameters for health feedback loop.
CREATE TABLE IF NOT EXISTS matching_tuning (
  id integer PRIMARY KEY,
  low_intensity_band integer NOT NULL,
  high_intensity_band integer NOT NULL,
  pool_multiplier_low real NOT NULL,
  pool_multiplier_high real NOT NULL,
  allow_theme_relax_high boolean NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO matching_tuning
  (id, low_intensity_band, high_intensity_band, pool_multiplier_low, pool_multiplier_high, allow_theme_relax_high)
VALUES
  (1, 0, 2, -0.5, 0.5, true)
ON CONFLICT (id) DO NOTHING;
