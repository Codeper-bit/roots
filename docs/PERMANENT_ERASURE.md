# Permanent erasure (design note, NOT implemented)

Day 1 deliberately has **no** way to physically destroy story data. `DELETE /stories/{id}` (Day 2)
will only set `stories.deleted_at`. Every foreign key is `ON DELETE RESTRICT`, so even a raw
`DELETE FROM stories` fails while any audio, content, review, consent, participant, job or question
row exists.

Permanent erasure is a separate, rare, deliberate operation, for example when a family or
storyteller exercises a right to have recordings destroyed. It must be designed before it is built.
This note records the intended shape.

## Principles
1. **Never part of normal deletion.** It is a distinct action with its own endpoint or admin command.
2. **Only for already soft-deleted stories**, and only after a waiting period (length to be decided).
3. **Authorized and auditable.** Requires an explicit confirmation by the story owner (or an
   administrator acting on a verified request). The fact that an erasure happened is recorded.
4. **Consent history.** Consent records are evidence. Whether they are erased or retained in
   minimal form (no personal content) is a legal decision to confirm before implementation.

## Intended order of operations
1. Verify the story is soft-deleted and the waiting period has passed.
2. Collect every `audio_assets.storage_key` for the story.
3. Delete the objects from cloud storage first. This step must be idempotent (deleting an
   already-missing object is not an error), so the whole process can be safely re-run after a failure.
4. In ONE database transaction, delete rows in dependency order:
   `content_reviews` → `content_versions` (newest versions first, because of `based_on_version_id`)
   → `processing_jobs` → `story_questions` → `audio_assets` → `consent_records`
   → `story_participants` → `stories`.
5. Write a minimal tombstone (story id, erasure time, who requested it), with no content.
6. Also address: backups, log files, and copies held by third-party AI providers.

## Database-level protections to add with this feature
- Run erasure under a dedicated database role. The normal application role should have **no**
  `DELETE` privilege on `audio_assets`, `content_versions`, `content_reviews` or `consent_records`.
  (Today the foreign keys protect parents, but a direct `DELETE` on those child tables is not
  blocked by the schema alone.)

## Open questions
- Waiting period length.
- Retention of consent evidence after erasure.
- Handling of backups and provider-held copies.
