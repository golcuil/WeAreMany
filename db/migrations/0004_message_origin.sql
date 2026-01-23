-- Add origin principal reference for internal-only impact aggregation.
ALTER TABLE messages
ADD COLUMN origin_device_id text NULL;

CREATE INDEX messages_origin_device_id_idx
  ON messages (origin_device_id);
