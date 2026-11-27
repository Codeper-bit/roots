-- Roots migration 003: add English to the languages table.
--
-- The translation endpoint accepts target language 'en' (schemas/translation.py)
-- and the translation prompt knows about it, but 001 only seeded yo/ha/ig. Saving
-- an English translation failed on content_versions_language_fk.
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/003_add_english.sql

INSERT INTO languages (code, name, native_name) VALUES
    ('en', 'English', 'English')
ON CONFLICT (code) DO NOTHING;
