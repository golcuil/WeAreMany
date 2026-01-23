-- Add per-sender affinity scores by theme for matching bias.
CREATE TABLE IF NOT EXISTS affinity_scores (
  sender_device_id text NOT NULL,
  theme_id text NOT NULL,
  score real NOT NULL DEFAULT 0,
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  PRIMARY KEY (sender_device_id, theme_id)
);
