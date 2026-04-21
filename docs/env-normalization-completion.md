# Env normalization completion report

Date: 2026-04-21

## Exact files changed
- `src/components/VoiceControls.jsx`
- `src/pages/Home.jsx`
- `src/services/aiVoiceService.js`
- `src/api/mufasaClient.js`
- `backend/app/main.py`
- `config/render.yaml`

## Legacy URLs removed
Removed active frontend voice/chat hardcoded URL:
- `https://mufasa-knowledge-bank.onrender.com`

Removed active voice/chat env dependency:
- `VITE_MUFASA_API`

## Env vars no longer needed
Frontend:
- `VITE_MUFASA_API`

## Final frontend env list
Keep:
- `VITE_API_BASE_URL` (required for voice/chat)

Optional (non-core to voice/chat):
- `VITE_ADMIN_EMAILS`
- `VITE_WS_URL` / `VITE_WS_BASE_URL`
- `VITE_APP_BASE_URL`
- `VITE_OPENVOICE_API`
- `VITE_AI_MODEL_API`

## Final backend env list
Keep:
- `ALLOWED_ORIGINS` (or `CORS_ALLOWED_ORIGINS` alias)
- `AIVOICE_BASE_URL`
- `AIVOICE_API_KEY` (if provider requires key)
- `OPENAI_API_KEY` (needed for non-`/chat/tts` flows)
- `DATABASE_URL`

Optional:
- `ENVIRONMENT`
- `BASE_URL`

Legacy alias still supported (optional migration window):
- `OPENVOICE_URL`

## Why `OPTIONS /chat/tts` returned 400
Starlette/FastAPI `CORSMiddleware` returns `400 Disallowed CORS origin` for preflight when request `Origin` is not in configured `allow_origins`.

In this codebase, prior defaults did not include Vite dev origins (`http://localhost:5173`, `http://127.0.0.1:5173`) and parsed only `ALLOWED_ORIGINS` (ignoring `CORS_ALLOWED_ORIGINS` used elsewhere).

## Smallest safe fix
Implemented minimal CORS normalization:
1. Include `localhost:5173` and `127.0.0.1:5173` in backend default origins.
2. Accept either `ALLOWED_ORIGINS` or `CORS_ALLOWED_ORIGINS`.
3. Normalize trailing slashes in parsed origins.

## PASS / FAIL
PASS

- Active Prince of Pan Africa voice/chat flows now resolve through `VITE_API_BASE_URL`.
- Legacy hardcoded `mufasa-knowledge-bank` URL removed from active voice/chat files.
- `VITE_MUFASA_API` removed from active voice/chat code and frontend Render env.
