CREATE TABLE IF NOT EXISTS second_touch_events (
  event_day_utc date NOT NULL,
  event_type text NOT NULL,
  reason text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS second_touch_events_day_idx
  ON second_touch_events (event_day_utc);
