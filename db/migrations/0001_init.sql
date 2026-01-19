-- MVP schema for mood + one-shot messaging.
-- No sender identity fields stored.
-- No social graph links.
-- If risk_level==2: no free text persisted.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE mood_submissions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id text NOT NULL,
  valence text NOT NULL CHECK (valence IN ('positive', 'neutral', 'negative')),
  intensity text NOT NULL CHECK (intensity IN ('low', 'medium', 'high')),
  emotion text NULL CHECK (emotion IN (
    'calm', 'content', 'hopeful', 'happy', 'anxious', 'sad',
    'disappointed', 'angry', 'overwhelmed', 'numb'
  )),
  risk_level smallint NOT NULL CHECK (risk_level IN (0, 1, 2)),
  sanitized_text text NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT mood_level2_no_text
    CHECK (NOT (risk_level = 2 AND sanitized_text IS NOT NULL))
);

CREATE INDEX mood_submissions_device_id_created_at_idx
  ON mood_submissions (device_id, created_at DESC);

CREATE TABLE messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  valence text NOT NULL CHECK (valence IN ('positive', 'neutral', 'negative')),
  intensity text NOT NULL CHECK (intensity IN ('low', 'medium', 'high')),
  emotion text NULL CHECK (emotion IN (
    'calm', 'content', 'hopeful', 'happy', 'anxious', 'sad',
    'disappointed', 'angry', 'overwhelmed', 'numb'
  )),
  risk_level smallint NOT NULL CHECK (risk_level IN (0, 1, 2)),
  sanitized_text text NULL,
  reid_risk numeric(3,2) NULL CHECK (reid_risk >= 0 AND reid_risk <= 1),
  status text NOT NULL CHECK (status IN ('queued', 'blocked')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT message_level2_block
    CHECK (
      (risk_level = 2 AND status = 'blocked' AND sanitized_text IS NULL)
      OR (risk_level IN (0, 1) AND status = 'queued')
    )
);

CREATE TABLE inbox_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  recipient_device_id text NOT NULL,
  state text NOT NULL CHECK (state IN ('unread', 'responded', 'locked')),
  received_at timestamptz NOT NULL DEFAULT now(),
  locked_at timestamptz NULL,
  UNIQUE (message_id, recipient_device_id)
);

CREATE INDEX inbox_items_recipient_state_idx
  ON inbox_items (recipient_device_id, state);

CREATE TABLE acknowledgements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  recipient_device_id text NOT NULL,
  reaction text NOT NULL CHECK (reaction IN ('helpful', 'seen', 'not_helpful')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (message_id, recipient_device_id)
);

CREATE INDEX acknowledgements_recipient_created_at_idx
  ON acknowledgements (recipient_device_id, created_at DESC);

CREATE TABLE safety_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'risk_scored', 'identity_leak_detected', 'rewrite_blocked', 'crisis_shown'
  )),
  risk_level smallint NULL CHECK (risk_level IN (0, 1, 2)),
  identity_leak boolean NOT NULL DEFAULT false,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX safety_events_device_id_created_at_idx
  ON safety_events (device_id, created_at DESC);

CREATE TABLE event_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  device_id text NOT NULL,
  event_type text NOT NULL CHECK (event_type IN (
    'mood_submitted', 'message_created', 'message_delivered', 'acknowledgement_created'
  )),
  risk_level smallint NULL CHECK (risk_level IN (0, 1, 2)),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX event_log_device_id_created_at_idx
  ON event_log (device_id, created_at DESC);
