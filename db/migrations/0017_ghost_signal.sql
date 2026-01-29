-- Ghost Signal: delayed delivery, silent hours support, and notification intents.

ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS deliver_at timestamptz NULL,
  ADD COLUMN IF NOT EXISTS delivery_status text NOT NULL DEFAULT 'pending'
    CHECK (delivery_status IN ('pending', 'delivered', 'blocked'));

ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS recipient_device_id text NULL;

CREATE INDEX IF NOT EXISTS messages_delivery_pending_idx
  ON messages (delivery_status, deliver_at);

CREATE INDEX IF NOT EXISTS messages_recipient_device_id_idx
  ON messages (recipient_device_id);

ALTER TABLE eligible_principals
  ADD COLUMN IF NOT EXISTS last_known_timezone_offset_minutes integer NULL;

CREATE TABLE IF NOT EXISTS notification_intents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  intent_key text NOT NULL,
  recipient_hash text NOT NULL,
  kind text NOT NULL CHECK (kind IN ('inbox_message')),
  status text NOT NULL CHECK (status IN ('created', 'sent', 'failed')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS notification_intents_intent_key_idx
  ON notification_intents (intent_key);
