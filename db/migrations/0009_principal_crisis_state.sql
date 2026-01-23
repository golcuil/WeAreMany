-- Track last crisis action per principal to enforce delivery gates.
CREATE TABLE IF NOT EXISTS principal_crisis_state (
  device_id text PRIMARY KEY,
  last_action text NULL,
  last_action_at timestamptz NULL
);

CREATE INDEX principal_crisis_state_last_action_at_idx
  ON principal_crisis_state (last_action_at);
