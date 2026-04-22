# Runtime Verification Report — PDF Ingestion

**Date:** 2026-04-22 (UTC)

## Environment verified
- Runnable backend environment from this repository using FastAPI `TestClient` and isolated SQLite DB.
- `pypdf` import verified at runtime: **5.4.0**.
- TTS network dependency was stubbed (`app.routes.chat.request_aivoice_tts`) so audiobook generation flow could be verified end-to-end without external provider/network variance.

## Exact runtime flows tested

1. **Upload text-based PDF successfully**
   - Endpoint: `POST /audiobooks/upload`
   - Input: synthetic text PDF payload (`sample.pdf`)
   - Parameters: `generate_audio=false`

2. **Save PDF as draft without audio generation**
   - Verified from upload response and `GET /audiobooks/{id}`

3. **Generate audiobook from uploaded PDF**
   - Endpoint: `POST /audiobooks/{id}/generate-audio`
   - Then polled `GET /audiobooks/{id}` until terminal state

4. **Confirm segmentation/chapter creation**
   - Verified chapter metadata in upload response and detail endpoint

5. **Confirm uploaded PDF-derived book appears in library**
   - Endpoint: `GET /audiobooks`

6. **Confirm image-only/scanned PDF fails with clear error**
   - Endpoint: `POST /audiobooks/upload`
   - Input: blank-page PDF (`scanned.pdf`)

7. **Confirm malformed/unreadable PDF fails gracefully**
   - Endpoint: `POST /audiobooks/upload`
   - Input: invalid PDF bytes (`bad.pdf`)

8. **Confirm existing `.txt` flow still works (regression check)**
   - Endpoint: `POST /audiobooks/upload`
   - Input: UTF-8 `sample.txt`

## Expected vs Actual

| Check | Expected | Actual | Result |
|---|---|---|---|
| 1. text PDF upload | HTTP 200 + audiobook created | HTTP 200, audiobook created | PASS |
| 2. draft save (no audio) | `status=draft`, no chapter audio | `status=draft`, `audio_chapter_count=0` | PASS |
| 3. generate audio | generation completes | transitioned to `complete`, `audio_chapter_count=1` | PASS |
| 4. chapter segmentation | chapter(s) created from PDF text | chapter created; strategy `segmented:upload:auto_partitioned` | PASS (with caveat) |
| 5. appears in library | listed in `/audiobooks` | book present in library list | PASS |
| 6. image-only PDF error | clear validation error | HTTP 422: `This PDF appears to be image-based or unsupported.` | PASS |
| 7. malformed PDF error | graceful parse failure | HTTP 422: `This PDF could not be parsed as text.` | PASS |
| 8. `.txt` upload regression | still ingests | HTTP 200, created as `draft` | PASS |

## Extraction quality notes

- On the tested text PDF sample, extraction quality was acceptable for ingestion and generation.
- **Caveat observed:** chapter heading detection did not split into multiple chapters for this sample and resolved to `auto_partitioned` with one chapter. This is likely due normalized text flattening line structure before heading detection, depending on how source PDFs encode line breaks.
- Malformed PDFs produced parser warnings (from `pypdf`) and then the expected graceful 422 response path.

## Is PDF support fully live?

- **In the runnable backend environment tested here:** Yes, core PDF support is live for upload, draft-save, generation trigger, library listing, and failure handling.
- **Deployment confirmation caveat:** this run validates the runnable backend in this environment; if you require verification against a specific remote deployed instance, run the same flow against that deployment URL.

## PASS / FAIL

**Overall verdict: PASS** (with extraction/chapter-detection caveat for some PDF formatting patterns).
