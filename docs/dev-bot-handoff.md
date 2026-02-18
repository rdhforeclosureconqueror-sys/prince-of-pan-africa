# Dev Bot Handoff — Prince of Pan-Africa Unified Repo

## What this repo contains
- Frontend (Vite/React) at root (`src/`, `public/`, `package.json`)
- Backend (FastAPI) at `backend/`
- Deploy/env templates at `config/`

## Current backend contract
### Branding
- FastAPI title/health/root/info now identify as **Prince of Pan-Africa Backend**.

### Routes
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /chat/ping`
- `POST /chat/message`
- `POST /chat/tts`
- `POST /chat/voice`
- `GET /portal/list`
- `POST /portal/start`
- `POST /portal/continue`
- `POST /portal/create_image`
- `POST /api/voice/tts`
- `POST /api/voice/stt`
- `GET /api/voice/health`
- `GET /health`
- `GET /`
- `GET /info`

### Auth notes
- Auth is basic token auth using JWT-like HS256 token format in `backend/app/routes/auth.py`.
- `/auth/login` returns `token`; `/auth/me` expects `Authorization: Bearer <token>`.
- In-memory user store is used for prototype operation.

## Frontend API behavior
- Central API helper in `src/api/api.js` supports mocked responses for prototype dashboards/ledger/member APIs.
- Frontend references `/auth/me` (not `/auth/google`, not `/prototype/me`).

## Environment variables
### Required backend vars
- `OPENAI_API_KEY`
- `AIVOICE_BASE_URL`
- `AIVOICE_API_KEY`
- `OPENVOICE_URL`
- `ALLOWED_ORIGINS`
- `JWT_SECRET`

### Required frontend var
- `VITE_API_BASE_URL=https://prince-of-pan-africa-backend.onrender.com`

## Render
- `config/render.yaml` defines two services:
  - `prince-of-pan-africa-backend` (Python, rootDir `backend/`)
  - `prince-of-pan-africa-frontend` (Static, rootDir `.`)

## Guardrails for future bots
1. Do not reintroduce `/auth/google` unless product explicitly requires OAuth.
2. Keep backend route names stable; frontend depends on these exact paths.
3. If removing API mocks from `src/api/api.js`, ensure backend parity for every mocked route first.
4. Keep static mount in backend (`/static`) for generated assets/uploads.
