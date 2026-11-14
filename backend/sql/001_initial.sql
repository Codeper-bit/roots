-- =============================================================================
-- Roots: initial schema (001)
-- Requires PostgreSQL 13+ (gen_random_uuid() is built in; no extension needed).
--
-- Apply once to an empty database:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/001_initial.sql
--
-- Deletion policy
--   * Stories are soft-deleted (stories.deleted_at). Normal deletes never remove rows.
--   * EVERY foreign key is ON DELETE RESTRICT. Nothing cascades, so a stray
--     DELETE can never silently destroy original audio, content history,
--     reviews, consent history or job history.
--   * Permanent erasure is a separate, deliberate process. See docs/PERMANENT_ERASURE.md.
--     It is NOT implemented here.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Shared trigger functions
-- -----------------------------------------------------------------------------

-- Keeps updated_at honest even if application code forgets to set it.
CREATE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- Used on append-only tables: rows may be inserted but never modified.
CREATE FUNCTION reject_update() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '% is append-only: rows cannot be updated', TG_TABLE_NAME
        USING ERRCODE = 'integrity_constraint_violation';
END;
$$;

-- -----------------------------------------------------------------------------
-- languages (lookup table)
-- Uses the ISO 639 code as the primary key instead of a UUID: the code is
-- already a stable, human-readable identifier, and rows reference it directly.
-- Adding a language later is an INSERT, not a schema change.
-- -----------------------------------------------------------------------------
CREATE TABLE languages (
    code        TEXT        PRIMARY KEY,
    name        TEXT        NOT NULL,
    native_name TEXT        NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT languages_code_format CHECK (code ~ '^[a-z]{2,3}$')
);

INSERT INTO languages (code, name, native_name) VALUES
    ('yo', 'Yoruba', 'Yorùbá'),
    ('ha', 'Hausa',  'Hausa'),
    ('ig', 'Igbo',   'Igbo')
ON CONFLICT (code) DO NOTHING;

-- -----------------------------------------------------------------------------
-- users
-- Email must already be lower-case (enforced by CHECK) so the plain UNIQUE
-- constraint is effectively case-insensitive without needing the citext extension.
-- The application normalizes email before inserting.
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT        NOT NULL,
    password_hash TEXT        NOT NULL,
    display_name  TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_email_format CHECK (
        email = lower(email)
        AND char_length(email) <= 254
        AND email ~ '^[^@[:space:]]+@[^@[:space:]]+$'
    ),
    CONSTRAINT users_password_hash_not_empty CHECK (char_length(password_hash) > 0),
    CONSTRAINT users_display_name_length CHECK (char_length(btrim(display_name)) BETWEEN 1 AND 100)
);

CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- stories
-- deleted_at IS NOT NULL means "soft deleted". The row, and everything that
-- references it, stays in place.
-- No 'public' visibility on purpose: the PRD excludes public story feeds.
-- -----------------------------------------------------------------------------
CREATE TABLE stories (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID        NOT NULL,
    title           TEXT        NOT NULL,
    description     TEXT,
    source_language TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'draft',
    visibility      TEXT        NOT NULL DEFAULT 'private',
    deleted_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT stories_owner_fk FOREIGN KEY (owner_id)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT stories_source_language_fk FOREIGN KEY (source_language)
        REFERENCES languages (code) ON DELETE RESTRICT,
    CONSTRAINT stories_title_length CHECK (char_length(btrim(title)) BETWEEN 1 AND 200),
    CONSTRAINT stories_description_length CHECK (description IS NULL OR char_length(description) <= 5000),
    CONSTRAINT stories_status_valid CHECK (status IN ('draft', 'processing', 'in_review', 'completed')),
    CONSTRAINT stories_visibility_valid CHECK (visibility IN ('private', 'family'))
);

-- Listing "my stories": only live rows, newest first.
CREATE INDEX stories_owner_live_idx
    ON stories (owner_id, created_at DESC) WHERE deleted_at IS NULL;

CREATE TRIGGER stories_set_updated_at
    BEFORE UPDATE ON stories
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- story_participants
-- user_id is optional: many storytellers will not have accounts.
-- -----------------------------------------------------------------------------
CREATE TABLE story_participants (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id     UUID        NOT NULL,
    user_id      UUID,
    display_name TEXT        NOT NULL,
    role         TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT story_participants_story_fk FOREIGN KEY (story_id)
        REFERENCES stories (id) ON DELETE RESTRICT,
    CONSTRAINT story_participants_user_fk FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT story_participants_display_name_length CHECK (char_length(btrim(display_name)) BETWEEN 1 AND 100),
    CONSTRAINT story_participants_role_valid CHECK (
        role IN ('storyteller', 'interviewer', 'family_member', 'translator', 'reviewer', 'other')
    )
);

CREATE INDEX story_participants_story_idx ON story_participants (story_id);
CREATE INDEX story_participants_user_idx ON story_participants (user_id) WHERE user_id IS NOT NULL;
-- The same registered user cannot be added to a story twice in the same role.
CREATE UNIQUE INDEX story_participants_story_user_role_uniq
    ON story_participants (story_id, user_id, role) WHERE user_id IS NOT NULL;

CREATE TRIGGER story_participants_set_updated_at
    BEFORE UPDATE ON story_participants
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- consent_records
-- History is kept: withdrawing consent sets status/withdrawn_at on the existing
-- row; granting again later creates a NEW row.
-- -----------------------------------------------------------------------------
CREATE TABLE consent_records (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    participant_id UUID        NOT NULL,
    purpose        TEXT        NOT NULL,
    status         TEXT        NOT NULL,
    granted_at     TIMESTAMPTZ,
    withdrawn_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT consent_records_participant_fk FOREIGN KEY (participant_id)
        REFERENCES story_participants (id) ON DELETE RESTRICT,
    CONSTRAINT consent_records_purpose_valid CHECK (
        purpose IN ('audio_storage', 'transcription', 'translation', 'cultural_interpretation', 'family_sharing')
    ),
    CONSTRAINT consent_records_status_valid CHECK (status IN ('granted', 'declined', 'withdrawn')),
    CONSTRAINT consent_records_timestamps_match_status CHECK (
        (status = 'granted'   AND granted_at IS NOT NULL AND withdrawn_at IS NULL)
        OR (status = 'declined'  AND granted_at IS NULL AND withdrawn_at IS NULL)
        OR (status = 'withdrawn' AND granted_at IS NOT NULL AND withdrawn_at IS NOT NULL
                                 AND withdrawn_at >= granted_at)
    )
);

CREATE INDEX consent_records_participant_idx ON consent_records (participant_id);
-- At most one ACTIVE grant per participant and purpose.
CREATE UNIQUE INDEX consent_records_one_active_grant
    ON consent_records (participant_id, purpose) WHERE status = 'granted';

CREATE TRIGGER consent_records_set_updated_at
    BEFORE UPDATE ON consent_records
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- audio_assets
-- Metadata only. The audio bytes live in object storage (storage_key).
-- mime_type holds the bare media type (e.g. audio/webm), without ";codecs=..." parameters.
-- size_bytes and checksum (SHA-256, lower-case hex) may be unknown while an upload is
-- 'pending', but are mandatory once it is 'uploaded'.
-- UNIQUE (id, story_id) exists so other tables can reference "this audio AND this story"
-- together (see processing_jobs).
-- -----------------------------------------------------------------------------
CREATE TABLE audio_assets (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id      UUID        NOT NULL,
    storage_key   TEXT        NOT NULL,
    mime_type     TEXT        NOT NULL,
    size_bytes    BIGINT,
    duration_ms   INTEGER,
    checksum      TEXT,
    upload_status TEXT        NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT audio_assets_story_fk FOREIGN KEY (story_id)
        REFERENCES stories (id) ON DELETE RESTRICT,
    CONSTRAINT audio_assets_storage_key_unique UNIQUE (storage_key),
    CONSTRAINT audio_assets_id_story_unique UNIQUE (id, story_id),
    CONSTRAINT audio_assets_storage_key_length CHECK (char_length(storage_key) BETWEEN 1 AND 1024),
    CONSTRAINT audio_assets_mime_type_valid CHECK (mime_type ~ '^audio/[A-Za-z0-9.+-]+$'),
    CONSTRAINT audio_assets_size_positive CHECK (size_bytes IS NULL OR size_bytes > 0),
    CONSTRAINT audio_assets_duration_non_negative CHECK (duration_ms IS NULL OR duration_ms >= 0),
    CONSTRAINT audio_assets_checksum_format CHECK (checksum IS NULL OR checksum ~ '^[0-9a-f]{64}$'),
    CONSTRAINT audio_assets_upload_status_valid CHECK (upload_status IN ('pending', 'uploaded', 'failed')),
    CONSTRAINT audio_assets_uploaded_has_integrity_data CHECK (
        upload_status <> 'uploaded' OR (size_bytes IS NOT NULL AND checksum IS NOT NULL)
    )
);

CREATE INDEX audio_assets_story_idx ON audio_assets (story_id);

-- Original recordings are never overwritten: the location is fixed forever, and once
-- an upload is complete its status and integrity data are frozen too.
CREATE FUNCTION protect_audio_assets() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.story_id IS DISTINCT FROM OLD.story_id
       OR NEW.storage_key IS DISTINCT FROM OLD.storage_key THEN
        RAISE EXCEPTION 'audio_assets.story_id and storage_key cannot be changed'
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF OLD.upload_status = 'uploaded'
       AND (NEW.upload_status IS DISTINCT FROM OLD.upload_status
            OR NEW.mime_type IS DISTINCT FROM OLD.mime_type
            OR NEW.size_bytes IS DISTINCT FROM OLD.size_bytes
            OR NEW.duration_ms IS DISTINCT FROM OLD.duration_ms
            OR NEW.checksum IS DISTINCT FROM OLD.checksum) THEN
        RAISE EXCEPTION 'an uploaded audio asset is immutable'
            USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER audio_assets_protect
    BEFORE UPDATE ON audio_assets
    FOR EACH ROW EXECUTE FUNCTION protect_audio_assets();

CREATE TRIGGER audio_assets_set_updated_at
    BEFORE UPDATE ON audio_assets
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- content_versions
-- Append-only history of transcripts, translations and interpretations.
-- A correction is a NEW row (origin = 'human_edited') pointing at the version it
-- corrects via based_on_version_id. Only review_status may change on an existing row.
-- The composite foreign key (based_on_version_id, story_id) guarantees a version
-- can only be based on a version of the SAME story. It is skipped when
-- based_on_version_id is NULL.
-- -----------------------------------------------------------------------------
CREATE TABLE content_versions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id            UUID        NOT NULL,
    content_type        TEXT        NOT NULL,
    language_code       TEXT        NOT NULL,
    version_number      INTEGER     NOT NULL,
    content             TEXT        NOT NULL,
    origin              TEXT        NOT NULL,
    based_on_version_id UUID,
    created_by          UUID,
    review_status       TEXT        NOT NULL DEFAULT 'unreviewed',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT content_versions_story_fk FOREIGN KEY (story_id)
        REFERENCES stories (id) ON DELETE RESTRICT,
    CONSTRAINT content_versions_language_fk FOREIGN KEY (language_code)
        REFERENCES languages (code) ON DELETE RESTRICT,
    CONSTRAINT content_versions_created_by_fk FOREIGN KEY (created_by)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT content_versions_id_story_unique UNIQUE (id, story_id),
    CONSTRAINT content_versions_based_on_same_story_fk FOREIGN KEY (based_on_version_id, story_id)
        REFERENCES content_versions (id, story_id) ON DELETE RESTRICT,
    CONSTRAINT content_versions_number_unique
        UNIQUE (story_id, content_type, language_code, version_number),
    CONSTRAINT content_versions_version_number_positive CHECK (version_number >= 1),
    CONSTRAINT content_versions_content_not_blank CHECK (btrim(content) <> ''),
    CONSTRAINT content_versions_type_valid CHECK (content_type IN ('transcript', 'translation', 'interpretation')),
    CONSTRAINT content_versions_origin_valid CHECK (origin IN ('ai_generated', 'human_created', 'human_edited')),
    CONSTRAINT content_versions_review_status_valid CHECK (
        review_status IN ('unreviewed', 'approved', 'rejected', 'changes_requested')
    ),
    -- Human-made content must say which human made it.
    CONSTRAINT content_versions_human_origin_has_author CHECK (origin = 'ai_generated' OR created_by IS NOT NULL),
    -- A correction must say what it corrects.
    CONSTRAINT content_versions_edit_has_base CHECK (origin <> 'human_edited' OR based_on_version_id IS NOT NULL),
    CONSTRAINT content_versions_not_based_on_self CHECK (based_on_version_id IS DISTINCT FROM id)
);

-- (story_id, content_type, language_code, version_number) is already indexed by the UNIQUE constraint.
CREATE INDEX content_versions_based_on_idx ON content_versions (based_on_version_id) WHERE based_on_version_id IS NOT NULL;
CREATE INDEX content_versions_created_by_idx ON content_versions (created_by) WHERE created_by IS NOT NULL;
CREATE INDEX content_versions_review_queue_idx ON content_versions (story_id, created_at) WHERE review_status = 'unreviewed';

CREATE TRIGGER content_versions_set_updated_at
    BEFORE UPDATE ON content_versions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- content_reviews (append-only)
-- created_at uses clock_timestamp() (real time) rather than now() (transaction start)
-- so that two reviews written in one transaction still sort correctly.
-- -----------------------------------------------------------------------------
CREATE TABLE content_reviews (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    content_version_id UUID        NOT NULL,
    reviewer_id        UUID        NOT NULL,
    decision           TEXT        NOT NULL,
    comment            TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    CONSTRAINT content_reviews_version_fk FOREIGN KEY (content_version_id)
        REFERENCES content_versions (id) ON DELETE RESTRICT,
    CONSTRAINT content_reviews_reviewer_fk FOREIGN KEY (reviewer_id)
        REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT content_reviews_decision_valid CHECK (decision IN ('approved', 'rejected', 'changes_requested')),
    CONSTRAINT content_reviews_comment_length CHECK (comment IS NULL OR char_length(comment) <= 5000)
);

CREATE INDEX content_reviews_version_idx ON content_reviews (content_version_id, created_at DESC);
CREATE INDEX content_reviews_reviewer_idx ON content_reviews (reviewer_id);

CREATE TRIGGER content_reviews_append_only
    BEFORE UPDATE ON content_reviews
    FOR EACH ROW EXECUTE FUNCTION reject_update();

-- -----------------------------------------------------------------------------
-- Human-in-the-loop guard for content_versions
--   1. The text and lineage of a version can never change after insert.
--   2. A version can only have review_status = 'approved' if its most recent
--      review is an 'approved' decision. So AI output cannot become approved
--      by a bug, a typo or a forgotten check in application code.
-- Created after content_reviews because it reads that table.
-- NOTE: this proves *a* review exists, not that the reviewer is *authorized*.
-- Authorization is an application-level rule (added with authentication).
-- -----------------------------------------------------------------------------
CREATE FUNCTION guard_content_versions() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF ROW(NEW.id, NEW.story_id, NEW.content_type, NEW.language_code, NEW.version_number,
               NEW.content, NEW.origin, NEW.based_on_version_id, NEW.created_by)
           IS DISTINCT FROM
           ROW(OLD.id, OLD.story_id, OLD.content_type, OLD.language_code, OLD.version_number,
               OLD.content, OLD.origin, OLD.based_on_version_id, OLD.created_by) THEN
            RAISE EXCEPTION 'content_versions are immutable; only review_status can change. Create a new version instead.'
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    END IF;

    IF NEW.review_status = 'approved' THEN
        IF (SELECT cr.decision
              FROM content_reviews cr
             WHERE cr.content_version_id = NEW.id
             ORDER BY cr.created_at DESC
             LIMIT 1) IS DISTINCT FROM 'approved' THEN
            RAISE EXCEPTION 'content version % cannot be approved without an approving review', NEW.id
                USING ERRCODE = 'integrity_constraint_violation';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER content_versions_guard
    BEFORE INSERT OR UPDATE ON content_versions
    FOR EACH ROW EXECUTE FUNCTION guard_content_versions();

-- -----------------------------------------------------------------------------
-- processing_jobs
-- The composite foreign key (audio_asset_id, story_id) guarantees a job can only
-- point at audio that belongs to the job's own story. Skipped when audio_asset_id is NULL.
-- -----------------------------------------------------------------------------
CREATE TABLE processing_jobs (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id       UUID        NOT NULL,
    audio_asset_id UUID,
    job_type       TEXT        NOT NULL,
    status         TEXT        NOT NULL DEFAULT 'queued',
    attempts       INTEGER     NOT NULL DEFAULT 0,
    error_message  TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at   TIMESTAMPTZ,
    CONSTRAINT processing_jobs_story_fk FOREIGN KEY (story_id)
        REFERENCES stories (id) ON DELETE RESTRICT,
    CONSTRAINT processing_jobs_audio_same_story_fk FOREIGN KEY (audio_asset_id, story_id)
        REFERENCES audio_assets (id, story_id) ON DELETE RESTRICT,
    CONSTRAINT processing_jobs_type_valid CHECK (
        job_type IN ('transcription', 'translation', 'interpretation', 'question_generation')
    ),
    CONSTRAINT processing_jobs_status_valid CHECK (
        status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')
    ),
    CONSTRAINT processing_jobs_attempts_non_negative CHECK (attempts >= 0),
    -- completed_at is set exactly when the job has reached a final status.
    CONSTRAINT processing_jobs_completed_matches_status CHECK (
        (status IN ('succeeded', 'failed', 'cancelled')) = (completed_at IS NOT NULL)
    ),
    CONSTRAINT processing_jobs_transcription_needs_audio CHECK (
        job_type <> 'transcription' OR audio_asset_id IS NOT NULL
    )
);

CREATE INDEX processing_jobs_story_idx ON processing_jobs (story_id);
CREATE INDEX processing_jobs_audio_idx ON processing_jobs (audio_asset_id) WHERE audio_asset_id IS NOT NULL;
-- A future worker polls for the oldest queued job.
CREATE INDEX processing_jobs_queue_idx ON processing_jobs (created_at) WHERE status = 'queued';

CREATE TRIGGER processing_jobs_set_updated_at
    BEFORE UPDATE ON processing_jobs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- -----------------------------------------------------------------------------
-- story_questions
-- -----------------------------------------------------------------------------
CREATE TABLE story_questions (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id   UUID        NOT NULL,
    question   TEXT        NOT NULL,
    status     TEXT        NOT NULL DEFAULT 'suggested',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT story_questions_story_fk FOREIGN KEY (story_id)
        REFERENCES stories (id) ON DELETE RESTRICT,
    CONSTRAINT story_questions_question_length CHECK (char_length(btrim(question)) BETWEEN 1 AND 1000),
    CONSTRAINT story_questions_status_valid CHECK (status IN ('suggested', 'asked', 'dismissed'))
);

CREATE INDEX story_questions_story_idx ON story_questions (story_id);

CREATE TRIGGER story_questions_set_updated_at
    BEFORE UPDATE ON story_questions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
