# Same-site auth deployment runbook

## Intended production topology

Render now has `https://api.simbawaujamaa.com` attached to the active backend service, `prince-of-pan-africa-backend`, with DNS verified and a certificate issued. Production should use the clean same-site subdomain topology:

- Frontend: `https://simbawaujamaa.com`
- Backend API: `https://api.simbawaujamaa.com`
- Fallback backend only: `https://prince-of-pan-africa-backend.onrender.com`

The fallback Render backend URL should remain documented for emergency operations, but production frontend builds should resolve API traffic through:

```env
VITE_API_BASE_URL=https://api.simbawaujamaa.com
```

Use `api.simbawaujamaa.com` only after Render verifies DNS and certificate for `prince-of-pan-africa-backend`. Now that the domain is verified and the certificate is issued, it is valid for production.

## Backend CORS

Backend CORS must allow credentialed requests from the production browser origins:

```env
ALLOWED_ORIGINS=https://simbawaujamaa.com,https://www.simbawaujamaa.com
```

The backend must keep `allow_credentials=True` so browser requests from the frontend include and receive the `mufasa_session` cookie.

## Session cookie policy

Because the frontend and API are same-site subdomains under `simbawaujamaa.com`, production session cookies should use:

```env
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_DOMAIN=.simbawaujamaa.com
```

Required cookie attributes:

- `HttpOnly=true`
- `Secure=true`
- `Path=/`
- `SameSite=Lax`
- `Domain=.simbawaujamaa.com`

If the backend must temporarily fall back to the browser-facing Render URL, `https://prince-of-pan-africa-backend.onrender.com`, use the fallback-only cookie posture for that emergency window:

```env
VITE_API_BASE_URL=https://prince-of-pan-africa-backend.onrender.com
SESSION_COOKIE_SAMESITE=none
SESSION_COOKIE_DOMAIN=
```

Do not set `SESSION_COOKIE_DOMAIN=.simbawaujamaa.com` while the browser-facing API host is `onrender.com`; an `onrender.com` response cannot set cookies for `simbawaujamaa.com`.

## Health and auth diagnostics

The backend exposes `GET /health`. These endpoints should work through the production API host:

1. `https://api.simbawaujamaa.com/health`
2. `https://api.simbawaujamaa.com/auth/debug/me`

Expected diagnostic behavior:

- Logged out `/auth/debug/me`: `401 Authentication required`
- Logged in through the frontend: `200` with a sanitized auth debug payload

## Owner post-deploy verification

1. Clear site data/cookies for:
   - `simbawaujamaa.com`
   - `www.simbawaujamaa.com`
   - `api.simbawaujamaa.com`
   - `prince-of-pan-africa-backend.onrender.com`
2. Open `https://simbawaujamaa.com`.
3. Sign in as admin.
4. Open `https://simbawaujamaa.com/debug/auth?authDebug=1` and confirm:
   - API base URL is `https://api.simbawaujamaa.com`
   - `frontend user.email` is populated
   - `frontend rbac.roles` is populated
   - `frontend rbac.permissions` is populated
   - backend `/auth/debug/me` status is `200`
   - `isAdminUser=true`
   - `canAccessTextBookOrganizer=true`
5. Open `https://simbawaujamaa.com/dashboard` and confirm the Operations Deck renders.
6. Open `https://simbawaujamaa.com/library/organizer` and confirm the Text Book Organizer renders.

## Quick rollback/fallback checklist

Use this only if `api.simbawaujamaa.com` stops routing to the active backend or its TLS certificate fails:

1. Build the frontend with `VITE_API_BASE_URL=https://prince-of-pan-africa-backend.onrender.com`.
2. Set backend `SESSION_COOKIE_SAMESITE=none`.
3. Clear backend `SESSION_COOKIE_DOMAIN`.
4. Verify `https://prince-of-pan-africa-backend.onrender.com/health`.
5. Return to the intended same-site topology as soon as Render verifies DNS and certificate for `api.simbawaujamaa.com` again.
