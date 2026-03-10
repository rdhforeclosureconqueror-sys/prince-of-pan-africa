# System Executive Report

## 1) Repository Architecture Overview
This repository is a split frontend/backend application:
- **Frontend (React + Vite):** user interface and experience.
- **Backend (FastAPI under `backend/`):** AI chat, portal learning, voice proxying, admin seeding, and system verification.
- **Operational docs/config:** deployment and audit support in `docs/`, `config/`, and `scripts/`.

## 2) Directory Structure Explanation
- `backend/app/main.py`: FastAPI app bootstrap, CORS, router registration, startup hooks.
- `backend/app/routes/`: domain routers (`chat`, `portal`, `voice`, `system`).
- `backend/app/services/`: service layer logic (admin seeding).
- `backend/app/database.py` and `backend/app/models.py`: SQLite connection/bootstrap and user model definitions.
- `backend/verification/verification_engine.py`: system-wide health verification engine.
- `docs/`: architecture, scan, and governance documentation.

## 3) API Module Inventory
- `chat` module: conversational response, TTS, voice input pipeline.
- `portal` module: portal listing, start/continue flow, image generation.
- `voice` module: proxy endpoints to aiVoice STT/TTS services.
- `system` module: verification and testing endpoints.

## 4) Service Layer Description
- `admin_seed.seed_admin`: ensures baseline administrative identity is present.
- `verification_engine.build_system_verification`: aggregates route/model/env/service checks.

## 5) Database Models
- `User`
  - `id` (PK)
  - `email` (unique)
  - `password_hash`
  - `role` (`admin|operator|viewer`)
  - `created_at`

## 6) External Integrations
- OpenAI API (`OPENAI_API_KEY`) for text/image/voice transcription support.
- aiVoice API (`AIVOICE_BASE_URL`, optional `AIVOICE_API_KEY`) for TTS/STT.

## 7) AI Modules
- `backend/app/routes/chat.py`
- `backend/app/utils/openai_client.py`
- `backend/app/routes/voice.py`

## 8) Security Architecture
- CORS allowlist policy (`ALLOWED_ORIGINS`).
- Password hashing via SHA-256 utility prior to persistence.
- Role-based user model with constrained role set (`admin`, `operator`, `viewer`).

## 9) Missing or Broken Components
- No dedicated async task workers currently registered.
- Environment-dependent integrations will show degraded status if API keys are not set.
- No Google OAuth server module detected in backend; no backend fitness modules detected.

## 10) Deployment Structure
- Backend deploy target: Render (`backend/Procfile`, `config/render.yaml`).
- FastAPI serves OpenAPI at `/docs` and static assets under `/static`.

---

## Capability Map (Endpoint Inventory)

### Core
- `GET /` — service liveness banner.
- `GET /health` — basic health/environment signal.
- `GET /info` — app metadata and route list.
- `GET /auth/me` — no-auth compatibility identity payload for frontend bootstrap.

### Chat
- `GET /chat/ping` — chat subsystem ping.
- `POST /chat/message` — text conversation (optional TTS output).
- `POST /chat/tts` — direct TTS generation.
- `POST /chat/voice` — speech input -> transcription -> response + TTS.

### Portals
- `GET /portal/list` — list available portal IDs.
- `POST /portal/start` — begin a portal run.
- `POST /portal/continue` — continue with resume code and question.
- `POST /portal/create_image` — generate portal image artifacts.

### Voice Proxy
- `POST /api/voice/tts` — proxy TTS to aiVoice.
- `POST /api/voice/stt` — proxy STT to aiVoice.
- `GET /api/voice/health` — aiVoice health probe.

### System Verification + Tests
- `GET /system/verification` — aggregate status report for routes, DB, models, services, env, AI modules, and workers.
- `GET /system/tests/routes` — validates critical route registration.
- `GET /system/tests/database` — executes connectivity query.
- `GET /system/tests/services` — validates service readiness map.
- `GET /system/tests/integrations` — validates integration configuration availability.
