-- Second-touch offers and pair stats (system-only, no sender identity exposed).
CREATE TABLE IF NOT EXISTS second_touch_pairs (
  sender_id text NOT NULL,
  recipient_id text NOT NULL,
  positive_count integer NOT NULL DEFAULT 0,
  first_positive_at timestamptz,
  last_positive_at timestamptz,
  last_offer_at timestamptz,
  disabled_until timestamptz,
  disabled_permanent boolean NOT NULL DEFAULT false,
  identity_leak_blocked boolean NOT NULL DEFAULT false,
  PRIMARY KEY (sender_id, recipient_id)
);

CREATE INDEX IF NOT EXISTS second_touch_pairs_recipient_idx
  ON second_touch_pairs (recipient_id);

CREATE TABLE IF NOT EXISTS second_touch_offers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_to_id text NOT NULL,
  counterpart_id text NOT NULL,
  state text NOT NULL DEFAULT 'available',
  created_at timestamptz NOT NULL DEFAULT now(),
  used_at timestamptz
);

CREATE INDEX IF NOT EXISTS second_touch_offers_offer_to_idx
  ON second_touch_offers (offer_to_id, created_at DESC);

ALTER TABLE messages
  ADD COLUMN IF NOT EXISTS identity_leak boolean NOT NULL DEFAULT false;
