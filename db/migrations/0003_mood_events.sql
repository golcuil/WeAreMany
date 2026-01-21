-- Mood event log for Reflection summary.
-- No sender identity fields.
-- No social graph links.
-- No free text stored.

CREATE TABLE IF NOT EXISTS mood_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id text NOT NULL,
  valence text NOT NULL CHECK (valence IN ('positive', 'neutral', 'negative')),
  intensity text NOT NULL CHECK (intensity IN ('low', 'medium', 'high')),
  expressed_emotion text NULL CHECK (expressed_emotion IN (
    'calm', 'content', 'hopeful', 'happy', 'anxious', 'sad',
    'disappointed', 'angry', 'overwhelmed', 'numb'
  )),
  risk_level smallint NOT NULL CHECK (risk_level IN (0, 1, 2)),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS mood_events_device_id_created_at_idx
  ON mood_events (device_id, created_at DESC);
