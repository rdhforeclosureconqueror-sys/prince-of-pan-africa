# Backend/Auth Alignment

## Active backend identity
- Service: **Prince of Pan-Africa Backend**
- Auth routes: `/auth/register`, `/auth/login`, `/auth/me`
- OAuth/Google routes are not required in current backend.

## Frontend expectations
- Frontend API base should point to backend service URL via `VITE_API_BASE_URL`.
- Frontend should not call `/auth/google`.
- `GET /auth/me` requires `Authorization: Bearer <token>` from `/auth/login`.

## CORS
- Configure `ALLOWED_ORIGINS` env var with frontend origins:
  - `https://simbawaujamaa.com`
  - `https://www.simbawaujamaa.com`
  - `https://prince-of-pan-africa-frontend.onrender.com`
