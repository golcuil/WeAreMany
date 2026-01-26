-- Daily privacy-safe aggregates for deliveries and acknowledgements.
CREATE TABLE IF NOT EXISTS daily_ack_aggregates (
  utc_day date NOT NULL,
  theme_id text NOT NULL DEFAULT 'unknown',
  delivered_count integer NOT NULL DEFAULT 0,
  positive_ack_count integer NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (utc_day, theme_id)
);

CREATE INDEX IF NOT EXISTS daily_ack_aggregates_day_idx
  ON daily_ack_aggregates (utc_day DESC);
