import asyncpg
import pytest

from app.core.config import Settings, get_settings
from app.core.database import acquire, close_pool, create_pool, transaction
from app.main import app
from tests import factories as f

EXPECTED_TABLES = {
    "users", "stories", "story_participants", "consent_records", "audio_assets",
    "content_versions", "content_reviews", "processing_jobs", "story_questions", "languages",
}
SHA256 = "a" * 64


# --------------------------------------------------------------------------- connection & setup


async def test_pool_connects_and_runs_query(database_url: str) -> None:
    pool = await create_pool(Settings(database_url=database_url))
    try:
        assert await pool.fetchval("SELECT 1") == 1
    finally:
        await close_pool(pool)
    assert pool.is_closing()


async def test_acquire_and_transaction_helpers(database_url: str) -> None:
    pool = await create_pool(Settings(database_url=database_url))
    try:
        async with acquire(pool) as connection:
            assert await connection.fetchval("SELECT 1") == 1

        email = "rollback-check@example.com"
        with pytest.raises(RuntimeError):
            async with transaction(pool) as connection:
                await f.insert_user(connection, email=email)
                raise RuntimeError("force a rollback")
        async with acquire(pool) as connection:
            assert await connection.fetchval("SELECT count(*) FROM users WHERE email = $1", email) == 0
    finally:
        await close_pool(pool)


async def test_app_lifespan_opens_and_closes_pool(database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    try:
        async with app.router.lifespan_context(app):
            pool = app.state.db_pool
            assert await pool.fetchval("SELECT 1") == 1
        assert pool.is_closing()
    finally:
        get_settings.cache_clear()


async def test_required_tables_exist(conn: asyncpg.Connection) -> None:
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    assert EXPECTED_TABLES <= {row["table_name"] for row in rows}


async def test_initial_languages_are_seeded(conn: asyncpg.Connection) -> None:
    rows = await conn.fetch("SELECT code FROM languages")
    assert {"yo", "ha", "ig"} <= {row["code"] for row in rows}


async def test_database_generates_uuids(conn: asyncpg.Connection) -> None:
    first = await f.insert_user(conn)
    second = await f.insert_user(conn)
    assert first != second
    assert first.version == 4


# --------------------------------------------------------------------------- users


async def test_duplicate_email_is_rejected(conn: asyncpg.Connection) -> None:
    await f.insert_user(conn, email="amaka@example.com")
    with pytest.raises(asyncpg.UniqueViolationError):
        async with conn.transaction():
            await f.insert_user(conn, email="amaka@example.com")


async def test_uppercase_email_is_rejected(conn: asyncpg.Connection) -> None:
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await f.insert_user(conn, email="Amaka@Example.com")


# --------------------------------------------------------------------------- foreign keys


async def test_story_requires_existing_owner(conn: asyncpg.Connection) -> None:
    from uuid import uuid4

    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with conn.transaction():
            await f.insert_story(conn, uuid4())


async def test_story_requires_known_language(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with conn.transaction():
            await f.insert_story(conn, owner, source_language="xx")


async def test_audio_requires_existing_story(conn: asyncpg.Connection) -> None:
    from uuid import uuid4

    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with conn.transaction():
            await f.insert_audio(conn, uuid4())


async def test_job_cannot_reference_audio_from_another_story(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_a = await f.insert_story(conn, owner)
    story_b = await f.insert_story(conn, owner)
    audio_a = await f.insert_audio(conn, story_a)
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with conn.transaction():
            await f.insert_job(conn, story_b, audio_asset_id=audio_a)


async def test_version_cannot_be_based_on_another_storys_version(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story_a = await f.insert_story(conn, owner)
    story_b = await f.insert_story(conn, owner)
    version_a = await f.insert_version(conn, story_a)
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        async with conn.transaction():
            await f.insert_version(
                conn, story_b, origin="human_edited", created_by=owner, based_on_version_id=version_a
            )


# --------------------------------------------------------------------------- CHECK constraints


@pytest.mark.parametrize("field,value", [("status", "bogus"), ("visibility", "public")])
async def test_invalid_story_values_are_rejected(conn: asyncpg.Connection, field: str, value: str) -> None:
    owner = await f.insert_user(conn)
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await f.insert_story(conn, owner, **{field: value})


async def test_invalid_job_type_and_status_are_rejected(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await f.insert_job(conn, story, job_type="bogus")
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await f.insert_job(conn, story, status="bogus")


async def test_job_completion_time_must_match_status(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            # finished but no completed_at
            await f.insert_job(conn, story, status="succeeded")


async def test_invalid_question_status_is_rejected(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await f.insert_question(conn, story, status="bogus")


async def test_uploaded_audio_requires_size_and_checksum(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await f.insert_audio(conn, story, upload_status="uploaded")


# --------------------------------------------------------------------------- consent


async def test_granted_consent_requires_a_grant_time(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    participant = await f.insert_participant(conn, story)
    with pytest.raises(asyncpg.CheckViolationError):
        async with conn.transaction():
            await conn.execute(
                "INSERT INTO consent_records (participant_id, purpose, status) VALUES ($1, 'transcription', 'granted')",
                participant,
            )


async def test_only_one_active_consent_per_purpose_but_history_is_kept(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    participant = await f.insert_participant(conn, story)
    first = await f.insert_consent(conn, participant, purpose="transcription")

    with pytest.raises(asyncpg.UniqueViolationError):
        async with conn.transaction():
            await f.insert_consent(conn, participant, purpose="transcription")

    # Withdraw, then grant again: allowed, and both rows remain.
    await conn.execute("UPDATE consent_records SET status = 'withdrawn', withdrawn_at = clock_timestamp() WHERE id = $1", first)
    await f.insert_consent(conn, participant, purpose="transcription")
    assert await conn.fetchval("SELECT count(*) FROM consent_records WHERE participant_id = $1", participant) == 2


# --------------------------------------------------------------------------- content versions


async def test_duplicate_content_version_number_is_rejected(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    await f.insert_version(conn, story, version_number=1)
    with pytest.raises(asyncpg.UniqueViolationError):
        async with conn.transaction():
            await f.insert_version(conn, story, version_number=1)


async def test_same_version_number_allowed_for_other_type_or_language(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    await f.insert_version(conn, story, content_type="transcript", language_code="yo", version_number=1)
    await f.insert_version(conn, story, content_type="translation", language_code="yo", version_number=1)
    await f.insert_version(conn, story, content_type="transcript", language_code="ha", version_number=1)


async def test_human_edit_requires_author_and_base(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    draft = await f.insert_version(conn, story)
    with pytest.raises(asyncpg.CheckViolationError):  # no author
        async with conn.transaction():
            await f.insert_version(conn, story, version_number=2, origin="human_edited", based_on_version_id=draft)
    with pytest.raises(asyncpg.CheckViolationError):  # no base version
        async with conn.transaction():
            await f.insert_version(conn, story, version_number=2, origin="human_edited", created_by=owner)
    # Valid correction
    await f.insert_version(
        conn, story, version_number=2, origin="human_edited", created_by=owner, based_on_version_id=draft
    )


async def test_content_of_a_version_cannot_be_changed(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    version = await f.insert_version(conn, story, content="Original draft")
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("UPDATE content_versions SET content = 'Silently rewritten' WHERE id = $1", version)
    assert await conn.fetchval("SELECT content FROM content_versions WHERE id = $1", version) == "Original draft"


async def test_ai_content_cannot_be_inserted_as_approved(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await f.insert_version(conn, story, review_status="approved")


async def test_approval_requires_an_approving_review(conn: asyncpg.Connection) -> None:
    reviewer = await f.insert_user(conn)
    story = await f.insert_story(conn, reviewer)
    version = await f.insert_version(conn, story, content_type="interpretation")

    with pytest.raises(asyncpg.IntegrityConstraintViolationError):  # no review at all
        async with conn.transaction():
            await conn.execute("UPDATE content_versions SET review_status = 'approved' WHERE id = $1", version)

    await f.insert_review(conn, version, reviewer, decision="rejected")
    # latest review is a rejection
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("UPDATE content_versions SET review_status = 'approved' WHERE id = $1", version)

    await f.insert_review(conn, version, reviewer, decision="approved")
    await conn.execute("UPDATE content_versions SET review_status = 'approved' WHERE id = $1", version)
    assert await conn.fetchval("SELECT review_status FROM content_versions WHERE id = $1", version) == "approved"


async def test_reviews_are_append_only(conn: asyncpg.Connection) -> None:
    reviewer = await f.insert_user(conn)
    story = await f.insert_story(conn, reviewer)
    version = await f.insert_version(conn, story)
    review = await f.insert_review(conn, version, reviewer, decision="changes_requested")
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("UPDATE content_reviews SET decision = 'approved' WHERE id = $1", review)


# --------------------------------------------------------------------------- audio immutability


async def test_audio_location_never_changes(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    audio = await f.insert_audio(conn, story)
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("UPDATE audio_assets SET storage_key = 'somewhere/else.webm' WHERE id = $1", audio)


async def test_uploaded_audio_is_frozen(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    audio = await f.insert_audio(conn, story, upload_status="uploaded", size_bytes=1234, checksum=SHA256)
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("UPDATE audio_assets SET checksum = $2 WHERE id = $1", audio, "b" * 64)


async def test_pending_audio_can_complete_upload(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    audio = await f.insert_audio(conn, story)
    await conn.execute(
        "UPDATE audio_assets SET upload_status = 'uploaded', size_bytes = 99, checksum = $2 WHERE id = $1",
        audio, SHA256,
    )
    assert await conn.fetchval("SELECT upload_status FROM audio_assets WHERE id = $1", audio) == "uploaded"


# --------------------------------------------------------------------------- deletion policy


async def test_soft_delete_keeps_the_story_and_its_history(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    participant = await f.insert_participant(conn, story)
    await f.insert_consent(conn, participant)
    await f.insert_audio(conn, story)
    await f.insert_version(conn, story)

    await conn.execute("UPDATE stories SET deleted_at = now() WHERE id = $1", story)

    assert await conn.fetchval("SELECT deleted_at IS NOT NULL FROM stories WHERE id = $1", story) is True
    for table in ("story_participants", "audio_assets", "content_versions"):
        assert await conn.fetchval(f"SELECT count(*) FROM {table} WHERE story_id = $1", story) == 1  # noqa: S608
    assert await conn.fetchval("SELECT count(*) FROM consent_records WHERE participant_id = $1", participant) == 1


@pytest.mark.parametrize(
    "child", ["audio", "version", "participant", "job", "question"],
)
async def test_story_with_history_cannot_be_hard_deleted(conn: asyncpg.Connection, child: str) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    if child == "audio":
        await f.insert_audio(conn, story)
    elif child == "version":
        await f.insert_version(conn, story)
    elif child == "participant":
        await f.insert_participant(conn, story)
    elif child == "job":
        await f.insert_job(conn, story)
    else:
        await f.insert_question(conn, story)

    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("DELETE FROM stories WHERE id = $1", story)
    assert await conn.fetchval("SELECT count(*) FROM stories WHERE id = $1", story) == 1


async def test_participant_with_consent_history_cannot_be_deleted(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    story = await f.insert_story(conn, owner)
    participant = await f.insert_participant(conn, story)
    await f.insert_consent(conn, participant)
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("DELETE FROM story_participants WHERE id = $1", participant)


async def test_user_who_owns_a_story_cannot_be_deleted(conn: asyncpg.Connection) -> None:
    owner = await f.insert_user(conn)
    await f.insert_story(conn, owner)
    with pytest.raises(asyncpg.IntegrityConstraintViolationError):
        async with conn.transaction():
            await conn.execute("DELETE FROM users WHERE id = $1", owner)
