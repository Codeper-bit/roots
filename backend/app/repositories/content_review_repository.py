
import asyncpg
from uuid import UUID


async def create_content_review(
    conn: asyncpg.Connection,
    content_version_id: UUID,
    reviewer_id: UUID,
    decision: str,
    comment: str | None = None,
) -> asyncpg.Record | None:
    async with conn.transaction():
        # Lock the version so concurrent reviews for it
        # are processed in a consistent order.
        version = await conn.fetchrow(
            """
            SELECT id
            FROM content_versions
            WHERE id = $1
            FOR UPDATE;
            """,
            content_version_id,
        )

        if version is None:
            return None

        review = await conn.fetchrow(
            """
            INSERT INTO content_reviews (
                content_version_id,
                reviewer_id,
                decision,
                comment
            )
            VALUES ($1, $2, $3, $4)
            RETURNING *;
            """,
            content_version_id,
            reviewer_id,
            decision,
            comment,
        )

        await conn.execute(
            """
            UPDATE content_versions
            SET review_status = $1
            WHERE id = $2;
            """,
            decision,
            content_version_id,
        )

        return review


async def get_content_reviews_by_version_id(
    conn: asyncpg.Connection,
    content_version_id: UUID,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT *
        FROM content_reviews
        WHERE content_version_id = $1
        ORDER BY created_at DESC;
        """,
        content_version_id,
    )


async def get_content_reviews_by_reviewer_id(
    conn: asyncpg.Connection,
    reviewer_id: UUID,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT *
        FROM content_reviews
        WHERE reviewer_id = $1
        ORDER BY created_at DESC;
        """,
        reviewer_id,
    )
