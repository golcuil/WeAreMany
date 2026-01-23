-- Store normalized primary theme tag for mood events.
ALTER TABLE mood_events
ADD COLUMN theme_tag text NULL;

CREATE INDEX mood_events_theme_tag_idx
  ON mood_events (theme_tag);
