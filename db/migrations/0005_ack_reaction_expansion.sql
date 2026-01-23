-- Expand allowed acknowledgement reactions to match UI options.
ALTER TABLE acknowledgements
DROP CONSTRAINT IF EXISTS acknowledgements_reaction_check;

ALTER TABLE acknowledgements
ADD CONSTRAINT acknowledgements_reaction_check
CHECK (reaction IN ('helpful', 'thanks', 'relate', 'seen', 'not_helpful'));
