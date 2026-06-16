# Render Postgres persistence verification

Use this checklist after deploying the backend with the Render database service `SemaDB` and the persistent disk mounted at `/var/data`.

## Automated readiness checks

Call the authenticated system verification endpoint and confirm these checks are `ok`:

- `required_environment`: `DATABASE_URL` is present.
- `production_persistence`: `db_type` reports `postgres`, `DATABASE_URL` is present, and no SQLite fallback is active.
- `migration_tables`: the audiobook and book organizer persistence tables are present, including `audiobooks`, `audiobook_chapters`, `audiobook_progress`, `audiobook_chapter_reflections`, `audio_assets`, `book_organizer_documents`, `book_organizer_blocks`, and `book_organization_plans`.
- `render_disk_mount`: `/var/data` exists and is a directory.
- `persistent_media_storage`: `AUDIO_STORAGE_DIR` is `/var/data/static/audio` and `BOOK_COVER_STORAGE_DIR` is `/var/data/static/book-covers`.

A failed check means the named Render environment variable, disk mount, or database migration must be corrected before using the deployment for production persistence.

## Restart survival test

1. Create a small test book through the frontend Library flow or `POST /audiobooks/create` with `generate_audio` set to `false`.
2. Confirm the book appears in `GET /audiobooks` or in the frontend Library.
3. Restart or redeploy the backend Render service.
4. Confirm the same book still appears in `GET /audiobooks` or in the frontend Library.

If the book disappears after restart, the backend is not reading from the managed Postgres database or the request is using a different authenticated user/session than the one that created the book.
