# Frontend Workspace

Current frontend source remains at repository root (`src/`, `public/`, and Vite config files)
to preserve existing deployment behavior.

This folder is reserved for frontend-specific docs/scripts during the monorepo transition.

## Text Book Organizer release-readiness (Phase 7)

### Feature flags (required alignment)
- `VITE_ENABLE_TEXT_BOOK_ORGANIZER`: frontend gate for organizer visibility and route access.
- `ENABLE_TEXT_BOOK_ORGANIZER`: backend gate for organizer API availability.

| Frontend `VITE_ENABLE_TEXT_BOOK_ORGANIZER` | Backend `ENABLE_TEXT_BOOK_ORGANIZER` | Result |
|---|---|---|
| `true` | `true` | Organizer entry is visible and organizer flow works end-to-end. |
| `true` | `false` | Organizer entry is visible, but organizer API calls return `404`. |
| `false` | `true` | Organizer entry is hidden; `/library/organizer` redirects to `/library`. |
| `false` | `false` | Organizer remains hidden and backend endpoints are disabled. |

### Full organizer flow (manual path)
1. Sign in as a member user.
2. Open **Library** (`/library`).
3. Confirm **Organize Text** entry appears only when `VITE_ENABLE_TEXT_BOOK_ORGANIZER=true`.
4. Open `/library/organizer`.
5. Paste raw source text and submit ingestion.
6. Generate a proposed structure plan.
7. Review/adjust structure in review mode.
8. Generate preview and validate chapter ordering/content boundaries.
9. Export `.txt` output from organizer export endpoint.

### Manual QA checklist
- [ ] With both flags `true`, organizer entry is visible from `/library`.
- [ ] With frontend flag `false`, organizer entry is hidden from `/library`.
- [ ] With frontend flag `false`, direct `/library/organizer` navigation redirects to `/library`.
- [ ] Organizer ingest (`/audiobooks/organizer/ingest-text`) succeeds when backend flag is `true`.
- [ ] Organizer plan proposal (`/audiobooks/organizer/propose-plan`) succeeds.
- [ ] Organizer review (`/audiobooks/organizer/review-structure`) persists edits and keeps immutable block ids.
- [ ] Organizer preview (`/audiobooks/organizer/preview`) reflects reviewed structure.
- [ ] Organizer export (`/audiobooks/organizer/export-txt`) produces expected text output.
- [ ] Existing `/study` audiobook create/list/play/progress/reflection flows remain unchanged.
- [ ] No DOCX/PDF organizer ingestion, upload pipeline, AI transformation, or audiobook handoff behavior was added by organizer scope.

### Final regression test command list
Run from repository root unless noted:

1. Frontend production build:
   - `npm run build`
2. Organizer backend test suite:
   - `cd backend && pytest -q tests/test_book_organizer_text_ingestion_phase1.py tests/test_book_organizer_plan_phase2.py tests/test_book_organizer_block_immutability.py tests/test_book_organizer_review_phase5.py`
3. Audiobook regression suite:
   - `cd backend && pytest -q tests/test_audiobook_auth_persistence_guardrails.py tests/test_audiobook_pdf_ingestion.py tests/test_auth_credential_wiring_phase7.py`
