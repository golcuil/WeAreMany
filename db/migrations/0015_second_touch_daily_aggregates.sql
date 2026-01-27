CREATE TABLE IF NOT EXISTS second_touch_daily_aggregates (
  utc_day date NOT NULL,
  counter_key text NOT NULL,
  count integer NOT NULL DEFAULT 0,
  PRIMARY KEY (utc_day, counter_key)
);
