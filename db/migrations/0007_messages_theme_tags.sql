-- Store normalized theme tags for each message.
ALTER TABLE messages
ADD COLUMN theme_tags text[] NOT NULL DEFAULT '{}';

CREATE INDEX messages_theme_tags_idx
  ON messages USING GIN (theme_tags);
