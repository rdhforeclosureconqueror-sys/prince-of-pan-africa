# Frontend Workspace

Current frontend source remains at repository root (`src/`, `public/`, and Vite config files)
to preserve existing deployment behavior.

This folder is reserved for frontend-specific docs/scripts during the monorepo transition.

## Feature Flag Alignment (Text Book Organizer)
- Frontend must set `VITE_ENABLE_TEXT_BOOK_ORGANIZER=true` to show the organizer link and allow `/library/organizer` route access.
- Backend must also set `ENABLE_TEXT_BOOK_ORGANIZER=true` or organizer API calls will return `404`.
