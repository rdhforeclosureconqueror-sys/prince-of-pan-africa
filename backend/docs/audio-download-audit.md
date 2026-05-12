# Audio/Audiobook Download Audit

## Route/API map

| Area | Method | Path | Auth/permission | Params/body | Response type | Expected storage source |
|---|---:|---|---|---|---|---|
| List audiobooks | GET | `/audiobooks` | Session user via audiobook resolver; guest only if `ALLOW_GUEST_AUDIOBOOKS=true` | none | JSON `{items, auth_mode}` | DB rows in `audiobooks` owned by current user |
| Get audiobook/chapter list | GET | `/audiobooks/{audiobook_id}` | Session user via audiobook resolver; owner-only query | path `audiobook_id` | JSON audiobook with chapter metadata/progress | DB rows in `audiobooks`, `audiobook_chapters`, `audiobook_progress` |
| Create audiobook | POST | `/audiobooks/create` | Session user via audiobook resolver; guest only if enabled | JSON title/author/text/voice/generate_audio/access_level | JSON audiobook | DB; optional generated files under backend static audio cache |
| Upload audiobook | POST | `/audiobooks/upload` | Session user via audiobook resolver; guest only if enabled | multipart title/author/voice/access_level/generate_audio/file | JSON audiobook | DB; optional generated files under backend static audio cache |
| Generate all missing audio | POST | `/audiobooks/{audiobook_id}/generate-audio` | Session user via audiobook resolver; owner-only query | path `audiobook_id` | JSON status/audiobook | TTS provider writes MP3 cache files to `app/static/audio` |
| Generation status | GET | `/audiobooks/{audiobook_id}/generation-status` | Session user via audiobook resolver; owner-only query | path `audiobook_id` | JSON generation progress | DB chapter statuses plus in-process job state |
| Generate chapter audio | POST | `/audiobooks/{audiobook_id}/chapters/{chapter_index}/generate?regenerate=bool` | Session user via audiobook resolver; owner-only query | path IDs, optional query `regenerate` | JSON chapter/audio metadata | TTS provider writes MP3 cache files to `app/static/audio`; DB `audio_assets` stores URL/key |
| Save chapter audio metadata | POST | `/api/audio/save` | Canonical session/RBAC `audiobook:update_self`; owner-only book/chapter query | JSON bookId/chapterId/title/voice/model/audioUrl/duration/format | JSON saved audio metadata | Existing local static audio file referenced by URL/key |
| Get saved chapter audio metadata | GET | `/api/audio/book/{book_id}/chapter/{chapter_id}` | Canonical session/RBAC `audiobook:read_self`; owner-only book/chapter query | path book/chapter DB IDs | JSON saved audio metadata | DB `audio_assets`; reconciles chapter audio pointer |
| Download chapter audio | GET | `/api/audio/download/{audio_id}` | Canonical session/RBAC `audiobook:read_self`; owner-only asset/book/chapter query | path `audio_id` | File attachment, e.g. `audio/mpeg` | Local file under `app/static/audio` resolved from `audio_assets.storage_key` or `audio_url` |
| Regenerate saved audio | POST | `/api/audio/regenerate` | Canonical session/RBAC `audiobook:generate_audio_self`; owner-only book/chapter query | JSON bookId/chapterId/confirm | JSON saved audio metadata | TTS provider writes replacement MP3 to `app/static/audio` |
| Raw TTS | POST | `/tts` | No session/RBAC currently | JSON text/voice/style/format | Audio bytes | OpenAI TTS response only, not audiobook storage |
| Static audio streaming | GET | `/static/audio/{filename}` | No session/RBAC; Starlette static file mount | path filename | Static file response, browser may use Range support | Local `backend/app/static/audio` |

No full-audiobook M4B/ZIP download route was found. The supported download path is per saved chapter audio asset.

## Frontend flow

- Main page/component: `src/pages/StudyPage.jsx`.
- Library load: `api('/audiobooks', { credentials: 'include' })`.
- Book load: `api('/audiobooks/{id}', { credentials: 'include' })` and reflections.
- Polling: `api('/audiobooks/{id}/generation-status', { credentials: 'include' })` while book status is active.
- Chapter generation button: calls `api('/audiobooks/{id}/chapters/{chapter_index}/generate', { method: 'POST', credentials: 'include' })`.
- Saved audio lookup/use: calls `/api/audio/book/{book_id}/chapter/{chapter_id}` with credentials.
- Save audio button: calls `/api/audio/save` with credentials.
- Download audio button now fetches `/api/audio/download/{audio_id}` with `credentials: 'include'`, verifies `response.ok`, verifies `Content-Type` starts with `audio/`, reads a blob, derives the filename from `Content-Disposition`, and surfaces JSON/text errors instead of navigating away.

## Storage/persistence findings

Generated audio is cached on local disk in `backend/app/static/audio` and referenced in the database by `audio_assets.audio_url` plus `audio_assets.storage_key`. This is persistent only if the deployment platform keeps that directory across restarts/redeploys. On ephemeral hosts, a service restart or redeploy can leave DB records pointing at missing MP3 files. The download endpoint now returns a clear 404 for that mismatch and logs the resolved storage key plus file-exists result.

## Likely root cause

Most likely: storage/file persistence mismatch after service restarts or redeploys, compounded by frontend download navigation that could not inspect backend JSON errors. Secondary risk: cross-domain session/cookie mismatch if the frontend calls a Render backend URL while login and `/auth/me` use `api.simbawaujamaa.com`.

## Minimal safe fix applied

- Kept the Text Book Organizer routes separate from audio generation/export.
- Hardened `/api/audio/*` authorization to canonical session/RBAC dependencies.
- Hardened local audio path resolution against traversal and stale DB keys.
- Added safe audio download logging without cookies/tokens/signed URLs.
- Changed the frontend download button to use credentialed blob fetch and surface errors.

## Production verification checklist

1. Confirm `VITE_API_BASE_URL` resolves to the same production API origin used by `/auth/me` (prefer `https://api.simbawaujamaa.com` once DNS/TLS are valid).
2. Confirm backend `ALLOWED_ORIGINS`/`CORS_ALLOWED_ORIGINS` include the frontend origin and `allow_credentials=True` remains enabled.
3. Confirm session cookie settings match the chosen API domain (`Secure` in production; `SameSite=Lax` for same-site `api.simbawaujamaa.com`, or `None` only for temporary cross-site API use).
4. Log in and verify `/auth/me` returns 200.
5. Open the audio study page and verify the library loads.
6. Open a completed chapter and verify Download Audio is enabled.
7. Click Download Audio and verify the response is an MP3 attachment that opens and plays.
8. Restart the service and verify previously generated audio still downloads if persistent storage is expected; otherwise expect a clear missing-file error and plan object storage/persistent disk.
9. Temporarily remove/rename an MP3 and verify the frontend shows a clear user-facing error instead of downloading JSON as MP3.
10. Verify audio requests go to the same API base as `/auth/me`, not a mixed Render/custom-domain combination.
