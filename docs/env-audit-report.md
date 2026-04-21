# Environment Variable Audit — Prince of Pan Africa

Date: 2026-04-21 (UTC)

## Scope and architecture target
Target architecture audited:

Frontend -> `VITE_API_BASE_URL` -> backend `/chat/tts` -> AI Voice provider

## Exact files checked

Frontend:
- `src/config.js`
- `src/api/api.js`
- `src/api/mufasaClient.js`
- `src/services/aiVoiceService.js`
- `src/services/leadershipService.js`
- `src/App.jsx`
- `src/pages/SystemVerificationPage.jsx`
- `src/utils/sessionLogger.js`
- `src/v2-ledger/components/SimbaBotWidget.jsx`
- `src/components/VoiceControls.jsx`
- `src/pages/Home.jsx`
- `src/pages/PortalDecolonize.jsx`

Backend:
- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/routes/chat.py`
- `backend/app/routes/tts.py`
- `backend/app/routes/voice.py`
- `backend/app/routes/portal.py`
- `backend/app/routes/system.py`
- `backend/app/utils/openai_client.py`
- `backend/app/utils/voice_client.py`
- `config/env.example`
- `config/render.yaml`

---

## Frontend env vars referenced in code

Actively referenced via `import.meta.env`:
- `VITE_API_BASE_URL`
- `VITE_MUFASA_API`
- `VITE_APP_BASE_URL`
- `VITE_WS_BASE_URL`
- `VITE_OPENVOICE_API`
- `VITE_AI_MODEL_API`
- `VITE_ADMIN_EMAILS`
- `VITE_WS_URL`

### Classification (frontend)

**Required frontend**
- `VITE_API_BASE_URL` (primary backend API root used by most active routes, including `/chat/tts` path callers)

**Optional frontend**
- `VITE_ADMIN_EMAILS` (admin role override list)
- `VITE_WS_URL` or `VITE_WS_BASE_URL` (only needed for websocket notification widget)

**Legacy/removable frontend env vars**
- `VITE_MUFASA_API` (legacy split-service base; no longer needed for target unified architecture)
- `VITE_OPENVOICE_API` (not required by current frontend TTS path)
- `VITE_AI_MODEL_API` (currently only computed in config; no active usage)
- `VITE_APP_BASE_URL` (not required for API/TTS flow)

**Suspicious/unsafe in frontend**
- No secret keys are referenced from frontend env usage in current code.
- Any `OPENAI_API_KEY` in frontend build/runtime env would be unsafe and should not exist.

---

## Backend env vars referenced in code

Referenced in backend Python code/config:
- `OPENAI_API_KEY`
- `AIVOICE_BASE_URL`
- `AIVOICE_API_KEY`
- `OPENVOICE_URL` (legacy alias/fallback)
- `ALLOWED_ORIGINS`
- `DATABASE_URL`
- `BASE_URL`
- `ENVIRONMENT`

### Classification (backend)

**Required backend (for current `/chat/tts` voice flow)**
- `AIVOICE_BASE_URL` (or legacy `OPENVOICE_URL` fallback) — provider endpoint used by `/chat/tts` in `chat.py`

**Backend optional for `/chat/tts` only**
- `AIVOICE_API_KEY` (only if provider requires keyed access)
- `OPENAI_API_KEY` (not needed for `/chat/tts`; needed for `/chat/message`, `/chat/voice`, `/tts`, portal generation)
- `ALLOWED_ORIGINS` (deployment/cors correctness, not intrinsic to TTS generation logic)

**Backend platform/core (outside direct tts path)**
- `DATABASE_URL`
- `ENVIRONMENT`
- `BASE_URL`

**Legacy/removable backend env vars**
- `OPENVOICE_URL` should be treated as legacy alias after migration to `AIVOICE_BASE_URL`

---

## Required confirmations

### 1) Is `VITE_MUFASA_API` still required anywhere active?
- **No** for target architecture. It is still referenced in legacy frontend code (`src/api/mufasaClient.js` and config alias), but the intended architecture should route frontend calls through `VITE_API_BASE_URL` only.

### 2) Is `OPENAI_API_KEY` improperly present in frontend and should be removed?
- **Yes if present in frontend env/deployment settings**. Frontend code does not need it and does not reference it; it must remain backend-only.

### 3) Exact backend env vars required for `/chat/tts`
- Required:
  - `AIVOICE_BASE_URL` (preferred)
- Legacy fallback accepted by code:
  - `OPENVOICE_URL`
- Optional:
  - `AIVOICE_API_KEY` (provider-auth dependent)

---

## Final clean env matrix

### Frontend keep
- `VITE_API_BASE_URL`
- `VITE_ADMIN_EMAILS` (optional by feature)
- `VITE_WS_URL` (optional websocket widget)

### Frontend remove
- `VITE_MUFASA_API`
- `VITE_OPENVOICE_API`
- `VITE_AI_MODEL_API`
- `VITE_APP_BASE_URL` (unless needed for external links)
- Any accidental secret keys (`OPENAI_API_KEY`, provider API keys, JWT secrets)

### Backend keep
- `AIVOICE_BASE_URL`
- `ALLOWED_ORIGINS`
- `DATABASE_URL`
- `OPENAI_API_KEY` (needed for non-`/chat/tts` AI paths)

### Backend optional
- `AIVOICE_API_KEY`
- `ENVIRONMENT`
- `BASE_URL`

### Backend remove/deprecate
- `OPENVOICE_URL` (keep temporary fallback only during migration)

---

## Pages/components still hardcoded to legacy service URLs

Hardcoded `https://mufasa-knowledge-bank.onrender.com` detected in active frontend pages/components:
- `src/components/VoiceControls.jsx`
- `src/pages/Home.jsx`

Also present as fallback defaults in:
- `src/services/aiVoiceService.js`
- `src/api/mufasaClient.js`

These should be normalized to `VITE_API_BASE_URL` (or centralized config import) to fully align with the target architecture.

---

## PASS / FAIL

**FAIL** (normalization incomplete in current codebase)

Reason:
- Active frontend still includes legacy split-base env (`VITE_MUFASA_API`) and hardcoded legacy backend URLs in voice/chat paths.
- Backend still supports legacy alias `OPENVOICE_URL`, indicating migration not yet fully normalized.
