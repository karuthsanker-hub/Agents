ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS evidence_excerpt TEXT;

ALTER TABLE articles
    ADD COLUMN IF NOT EXISTS evidence_context TEXT;

