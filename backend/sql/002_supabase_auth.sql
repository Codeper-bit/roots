-- Roots migration 002: delegate password management to Supabase Auth.
-- Review and back up the database before applying this migration.

ALTER TABLE users
    ADD COLUMN supabase_auth_id UUID;

ALTER TABLE users
    ALTER COLUMN password_hash DROP NOT NULL;

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS users_password_hash_not_empty;

ALTER TABLE users
    ADD CONSTRAINT users_supabase_auth_id_unique UNIQUE (supabase_auth_id);

ALTER TABLE users
    ADD CONSTRAINT users_auth_credential_present CHECK (
        password_hash IS NOT NULL OR supabase_auth_id IS NOT NULL
    );

COMMENT ON COLUMN users.supabase_auth_id IS
    'UUID of the corresponding user in Supabase Auth. Passwords are managed only by Supabase.';
