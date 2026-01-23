-- Store latest crisis action per principal for delivery gating.
CREATE TABLE IF NOT EXISTS principal_crisis_state (
  principal_id text PRIMARY KEY,
  last_action text NULL,
  last_action_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS principal_crisis_state_last_action_at_idx
  ON principal_crisis_state (last_action_at);
