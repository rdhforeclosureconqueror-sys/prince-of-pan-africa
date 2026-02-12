# Auth and API Alignment

## Current architecture
- Frontend uses `VITE_API_BASE_URL` for primary auth/session endpoints (`/auth/google`, `/auth/me`, `/auth/google/callback`).
- Mufasa Knowledge Bank backend under `backend/` is a secondary AI service and does not implement Google OAuth.

## Alignment checks
1. Google OAuth callback route must be served by primary API (`api.simbawaujamaa.com`), not Mufasa Knowledge Bank.
2. Frontend admin recognition remains:
   - backend role: `user.role === "admin"` or `user.is_admin`
   - allowlist fallback: `VITE_ADMIN_EMAILS` (case-insensitive)
3. CORS for Mufasa service controlled by `ALLOWED_ORIGINS`.

## Required environment variables
- Auth service: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SESSION_SECRET`, `DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`, `BACKEND_URL`.
- Mufasa service: `OPENAI_API_KEY`, `AIVOICE_BASE_URL`, `AIVOICE_API_KEY`, `OPENVOICE_URL`, `ALLOWED_ORIGINS`.
