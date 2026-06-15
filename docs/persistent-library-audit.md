# Persistent Book + Audiobook Library PR Review Audit

## 1. Persistence reality

- **Books/audiobooks are database-backed.** Uploaded or pasted books are created through `POST /audiobooks/create` and `POST /audiobooks/upload`, normalized into chapters, and persisted in `audiobooks`, `audiobook_chapters`, `audiobook_progress`, and `audio_assets` records. The library page reads `/audiobooks`; it is not populated from frontend-only state.
- **Runtime generation state is intentionally not durable.** Background-thread tracking only reflects in-flight generation. After restart, the book/chapter/database records remain, but an in-progress job may need to be restarted from the saved status.
- **Production DB must be durable.** `backend/app/database.py` requires `DATABASE_URL` in production-like environments. The Render blueprint now provisions a managed database and injects `DATABASE_URL`; this prevents production from relying on a reset-on-redeploy SQLite file.
- **Generated audio uses durable media configuration.** TTS audio writes to `AUDIO_STORAGE_DIR` when configured, falling back to `backend/app/static/audio` locally. The Render blueprint now mounts `/var/data` as a persistent disk and sets `AUDIO_STORAGE_DIR=/var/data/static/audio`. Audio URLs remain `/static/audio/<file>` and metadata remains in `audio_assets`/chapter records.
- **Known future migration:** S3-compatible storage is still a future storage backend. The current PR keeps local development simple while making deployed Render media durable via persistent disk.

## 2. Cover image behavior

- Every saved book defaults to `/book-covers/library-placeholder.svg`.
- Custom `cover_image_path` values can point to public assets, e.g. `/book-covers/forgotten-black-mega-cities.jpg`, because the frontend uses public-relative paths directly.
- Backend-hosted media paths under `/static/` are converted to the configured API base URL.
- Broken or missing cover images fall back in the browser to the default cover via `onError` handlers on both library cards and the reader detail page.

## 3. Library UI

- Library cards display cover thumbnail, title, author, description, status, access level, voiced chapter count, audiobook badge, and a Read / Listen CTA.
- Clicking the cover or CTA opens `/study?book=<id>`, the existing detail/player route.
- Mobile behavior uses the existing responsive grid plus fixed-ratio cover images, so cards collapse into narrower columns without requiring horizontal scrolling.

## 4. Book detail/player

- The detail/player page displays cover, title, author, access/status metadata, description, generation progress, readable chapter text, chapter list, progress controls, and audiobook controls.
- If chapter audio is missing, the player `src` remains unset and the UI shows a safe status message telling the member to generate audio or continue reading.
- Existing saved-audio lookup, saved-audio reuse, download, regeneration, playback, and progress persistence code paths remain in place.

## 5. Restart survival verification

Manual verification sequence:

1. Start backend and frontend with the Render-style durable configuration (`DATABASE_URL` plus `AUDIO_STORAGE_DIR`) or local `backend/mufasa.db` for development.
2. Create/save a book in `/study` with pasted text or a `.txt`/`.pdf` upload.
3. Use `generate_audio=false` for a fast text-only persistence test or `generate_audio=true` to verify persisted audio references and files.
4. Confirm `/library` shows the saved cover, title, author, description, status, access level, audiobook badge, and CTA.
5. Open the cover/card to `/study?book=<id>` and verify the cover, description, readable text/chapters, chapter list, and player controls render.
6. Stop both backend and frontend.
7. Restart backend and frontend without deleting the database or media directory.
8. Reload `/library`; the same book should still appear.
9. Open the book again; text and cover should still render.
10. If audio was generated, confirm the player can load `/static/audio/<file>`. If audio is absent or failed, confirm the UI shows the safe missing-audio state and allows regeneration.

## 6. Data ownership/access

- The current audiobook list/detail routes filter by `Audiobook.user_id == current_user.id`, so members only see their private saved books.
- Guest/dev mode maps unauthenticated local users to the pilot guest account; production-like environments require authentication unless explicitly configured otherwise.
- A shared/community library is **not implemented in this PR**. The product decision for public/community featured books vs user-private saved books remains a future decision and should use a distinct access model rather than mixing records into private libraries.

## 7. Review outcome

Issues found and fixed in this audit:

- Render deployment did not explicitly provision a durable database in the blueprint. Fixed by adding a managed database and wiring `DATABASE_URL`.
- Generated audio was still tied to the repo static folder by default in deployed configuration. Fixed by adding `AUDIO_STORAGE_DIR`, mounting `/static/audio` from that path, and configuring a Render persistent disk.
- Broken cover paths did not fall back in the browser. Fixed by adding cover `onError` fallbacks on library and reader pages.
- Missing audio copy implied pressing Play would generate audio. Fixed copy to clearly state that members can generate audio or continue reading.
