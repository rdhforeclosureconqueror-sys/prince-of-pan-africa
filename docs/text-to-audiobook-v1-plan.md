# Text-to-Audiobook (V1) — Feature Design & Implementation Readiness Plan

## 1) Audit of existing voice pipeline (reuse opportunities)

### Reusable backend pieces
- `POST /chat/tts` already supports text-to-speech generation with `voice_model`, local file caching by deterministic hash (`voice|text`), and static URL return (`audio_url`). This is the best current fit for chapter-by-chapter generation jobs.  
- `chat.py` already persists generated audio into backend static storage at `backend/app/static/audio` and exposes those files via FastAPI static routing (`/static`).  
- Existing provider integration (`request_aivoice_tts`) already handles provider URL config, API key header injection, timeout, and error diagnostics (network / auth / payload issues).

### Reusable frontend pieces
- `VoiceControls.jsx` already has stable playback controls, progress time tracking, and state handling (`idle`, `generating`, `ready`, `error`) that can be reused as audiobook player interaction patterns.
- `aiVoiceService.js` already wraps the `/chat/tts` endpoint and normalizes returned URL handling.
- `useLocalMemory` provides immediate local persistence pattern for pilot-side progress fallback if backend progress save is temporarily unavailable.

### Gaps in current pipeline for audiobooks
- Current TTS routes are single-text-request endpoints; there is no orchestration route for multi-chapter, asynchronous generation.
- No audiobook domain data model exists in SQLAlchemy models.
- No persistent user progress model for chapter + position + completion state.
- No frontend screens dedicated to upload/paste, processing queue, library, or a chapter-aware player.

## 2) Backend data model recommendation

Add SQLAlchemy entities:

### `audiobooks`
- `id` (PK)
- `user_id` (FK -> `users.id`, indexed)
- `title` (string, required)
- `author_source` (string, nullable)
- `voice` (string, required; e.g., `alloy`)
- `source_type` (enum/string: `paste`, `txt_upload`)
- `full_text` (long text; optional for storage policy)
- `status` (enum/string: `draft`, `processing`, `ready`, `failed`)
- `total_chapters` (int)
- `total_duration_seconds` (int nullable)
- `created_at`, `updated_at`

### `audiobook_chapters`
- `id` (PK)
- `audiobook_id` (FK -> `audiobooks.id`, indexed)
- `chapter_index` (int, indexed)
- `title` (string; generated like “Chapter 1” when absent)
- `text` (long text, required)
- `char_count` / `token_estimate` (int)
- `status` (`pending`, `processing`, `ready`, `failed`)
- `duration_seconds` (int nullable)
- `created_at`, `updated_at`

### `audio_assets`
- `id` (PK)
- `chapter_id` (FK -> `audiobook_chapters.id`, indexed)
- `provider` (string: `aivoice`)
- `voice` (string)
- `format` (string, `mp3`)
- `storage_path` (string, local static path)
- `public_url` (string)
- `checksum` (string for dedupe/integrity)
- `generation_latency_ms` (float)
- `created_at`

### `audiobook_progress`
- `id` (PK)
- `user_id` (FK -> `users.id`, indexed)
- `audiobook_id` (FK -> `audiobooks.id`, indexed)
- `last_chapter_index` (int)
- `last_position_seconds` (int)
- `playback_rate` (float default 1.0)
- `is_completed` (bool)
- `updated_at`
- Unique constraint: (`user_id`, `audiobook_id`)

## 3) Backend API pieces needed (new)

### Create/generate flow
1. `POST /audiobooks`  
   Create audiobook record from title, author/source, voice, and input text payload.
2. `POST /audiobooks/{id}/ingest`  
   Accepts paste text or `.txt` file content, performs chunking into chapters, creates chapter records.
3. `POST /audiobooks/{id}/generate`  
   Triggers chapter audio generation job (sequential in V1, optionally async worker later).

### Read/list flow
4. `GET /audiobooks`  
   Library list for current user with status and progress.
5. `GET /audiobooks/{id}`  
   Metadata + chapter list + chapter audio URLs + progress snapshot.

### Progress flow
6. `PUT /audiobooks/{id}/progress`  
   Upsert last chapter, position seconds, playback rate, completion.

### Implementation notes
- Reuse `request_aivoice_tts` and chapter-level deterministic caching to avoid regenerating identical chapter+voice outputs.
- Use existing cookie session pattern (`auth.py`) to resolve current user; avoid anonymous write paths.
- Keep `.txt` upload parser strict to UTF-8 text in V1; reject unsupported file types.

## 4) Frontend UX proposal

### A) Upload/Paste page (`/audiobooks/new`)
- Fields: title (required), author/source (optional), voice selector, text area OR `.txt` upload.
- Validation: min text length + max text length warning.
- CTA: “Generate Audiobook”.

### B) Processing state (`/audiobooks/:id/processing`)
- Show chapter split summary (N chapters).
- Per-chapter status list: pending / generating / ready / failed.
- Retry failed chapter button (V1 optional if low effort).

### C) Player view (`/audiobooks/:id`)
- Core controls (V1): play/pause, previous/next chapter, playback speed (0.75x/1x/1.25x/1.5x/2x).
- Chapter list with active highlight.
- Position tracker + auto-save progress (e.g., every 10 sec and on pause/chapter change).

### D) Library view (`/audiobooks`)
- Saved audiobook cards with title, author/source, voice, chapter count, status, and resume button.
- “Continue listening” section sorted by `updated_at` progress.

## 5) Chunking/chapter strategy recommendation

### V1 deterministic strategy (recommended)
1. Normalize input (`\r\n` -> `\n`, trim excessive whitespace).
2. Split by strong boundaries first:
   - explicit headings like `Chapter`, `Lesson`, `Section`
   - double-newline paragraph groups
3. Merge/split into target size windows:
   - target: 1,500–3,500 characters per chapter
   - hard cap: 4,500 chars (provider safety)
   - hard floor: 600 chars (merge tiny fragments)
4. Generate synthetic titles where none exist: `Chapter 1`, `Chapter 2`, etc.

### Why this is best for pilot
- Predictable output size for latency/cost control.
- No dependency on LLM summarization/chaptering for first release.
- Easier retries at chapter granularity.

## 6) Limits, risks, and copyright cautions

### Technical risks
- Long-generation latency for many chapters; synchronous request timeouts likely if whole book is attempted in one call.
- Storage growth from many MP3 files in local static disk.
- Provider throttling/rate limits if many chapters generated rapidly.
- Failure recovery complexity without chapter-level status.

### Product/copyright cautions
- Scope V1 to user-authored or clearly rights-safe text.
- Add explicit user attestation checkbox: user confirms rights/permission to synthesize uploaded text.
- Do not market as arbitrary commercial book ingestion.
- Add moderation guardrails for disallowed content categories if required by platform policy.

## 7) Pilot vs later-version recommendations

### Pilot (ship now)
- Paste text + `.txt` upload
- Deterministic chunking
- Single selected voice for all chapters
- Chapter-by-chapter generation with status
- Player controls: play/pause, prev/next, speed
- Progress save/resume
- Library list

### Later versions
- Multi-voice narration / character voices
- Background job queue + webhooks for large imports
- EPUB/PDF ingestion with parsing
- Smarter semantic chaptering using LLM
- Offline download / streaming optimization
- Team/shared libraries and permissions

## 8) Phased implementation plan

### Phase 0 — Design lock (0.5–1 day)
- Finalize data schema + API contract + chunking constants.
- Add policy copy (rights attestation).

### Phase 1 — Backend foundation (1–2 days)
- Add models + migrations for audiobook/chapter/audio/progress.
- Add CRUD/list endpoints + progress endpoint.
- Add `.txt` ingestion + deterministic chunking service.

### Phase 2 — Generation pipeline (1–2 days)
- Add chapter generation orchestration route.
- Reuse `request_aivoice_tts` for chapter-level synthesis.
- Persist audio asset rows + URLs.

### Phase 3 — Frontend core UX (2–3 days)
- New pages: New Audiobook, Processing, Player, Library.
- Integrate API client calls and optimistic progress updates.
- Implement chapter navigation + playback speed controls.

### Phase 4 — Hardening (1–2 days)
- Retry strategy, timeout handling, and partial-failure UX.
- Limits/validation (input size, chapter caps).
- QA pass with short/medium/long text scenarios.

## 9) Readiness verdict

**PASS (Implementation-ready for a controlled V1 pilot)** with the following conditions:
1. Ship with strict text-size caps and chapter count caps.
2. Keep ingestion to paste + `.txt` only.
3. Use chapter-level generation and persistence (not monolithic single-call generation).
4. Require rights attestation for uploaded content.
