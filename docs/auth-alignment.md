# Auth Alignment (Post-Cleanup)

- This repository no longer contains Google OAuth server routes or handlers.
- The FastAPI backend under `backend/` now provides core AI and system operations only.
- Authentication/session variables in `config/env.example` were simplified to generic session/database settings.

## Current Backend Auth Posture
1. No `/auth/google` routes are registered in FastAPI.
2. No Google OAuth middleware or client configuration is active.
3. Administrative bootstrap account is seeded at startup for development verification.

## Operational Notes
- If a separate identity provider is introduced later, it should be integrated as an independent module and documented in deployment config.
