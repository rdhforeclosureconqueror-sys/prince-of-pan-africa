# Same-site auth deployment fix — 2026-05-10

## Current production fallback — active during the outage

As of the production outage triage, `https://api.simbawaujamaa.com` shows a suspended-service page and is **not** a usable backend API host. Production frontend builds must therefore use the active Render backend until the custom API domain is repaired:

```env
VITE_API_BASE_URL=https://prince-of-pan-africa-backend.onrender.com
```

Current fallback topology:

- Frontend: `https://simbawaujamaa.com`
- Backend API: `https://prince-of-pan-africa-backend.onrender.com`

Backend CORS must continue to allow the browser origins that call the API with credentials:

```env
ALLOWED_ORIGINS=https://simbawaujamaa.com,https://www.simbawaujamaa.com
```

For this temporary cross-site fallback, the backend must use a host-only secure cookie that can be set by the Render backend host:

```env
SESSION_COOKIE_SAMESITE=none
SESSION_COOKIE_DOMAIN=
```

Do **not** set `SESSION_COOKIE_DOMAIN=.simbawaujamaa.com` while the browser-facing backend host is `prince-of-pan-africa-backend.onrender.com`; an `onrender.com` response cannot set cookies for `simbawaujamaa.com`.

## Live failure observed before the fallback

The `/debug/auth` page showed the frontend was fully unauthenticated even after login:

- Frontend origin: `https://simbawaujamaa.com`
- API base URL: `https://prince-of-pan-africa-backend.onrender.com`
- Frontend `user.email`: `null`
- Frontend roles/permissions: empty arrays
- Backend `/auth/debug/me`: `401 {"detail":"Authentication required"}`

That means the backend did not receive the `mufasa_session` cookie. This is a session-cookie delivery problem before admin/RBAC checks can run.

## Future same-site target — do not activate until the domain is live

The long-term target is a same-site browser-facing API domain instead of exposing the Render service hostname to browsers:

- Frontend: `https://simbawaujamaa.com`
- Backend API: `https://api.simbawaujamaa.com`

Only switch the frontend to this value after the custom backend domain is proven active:

```env
VITE_API_BASE_URL=https://api.simbawaujamaa.com
```

`https://api.simbawaujamaa.com` must not be used in production until all of these are true:

- DNS points to the active backend.
- Render custom domain is attached to `prince-of-pan-africa-backend`.
- TLS is active for the custom domain.
- `https://api.simbawaujamaa.com/health` returns a backend health response.
- `/auth/debug/me` returns `401` when logged out, not a suspended-service page.

When the custom domain is live, the backend CORS allowlist should still include only the browser origins that should call the API with credentials:

```env
ALLOWED_ORIGINS=https://simbawaujamaa.com,https://www.simbawaujamaa.com
```

## Session cookie policy

Production session cookies are configurable with these environment variables:

```env
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_DOMAIN=.simbawaujamaa.com
```

Recommended production attributes after `api.simbawaujamaa.com` points at the backend are:

- `HttpOnly=true`
- `Secure=true`
- `Path=/`
- `SameSite=Lax`
- `Domain=.simbawaujamaa.com`

`SameSite=Lax` is appropriate once the frontend and API are same-site subdomains under `simbawaujamaa.com`. If the backend must temporarily remain browser-facing at `onrender.com`, use `SESSION_COOKIE_SAMESITE=none` and leave `SESSION_COOKIE_DOMAIN` unset/empty; cookie auth may still fail in Safari/mobile browsers even with `SameSite=None; Secure`, so do not treat that as the long-term architecture.

## Health check recommendation

The backend exposes `GET /health`. Verify both hosts before and after any API-domain change:

1. `https://prince-of-pan-africa-backend.onrender.com/health` must work for the current fallback.
2. `https://api.simbawaujamaa.com/health` must work before switching production frontend builds to `https://api.simbawaujamaa.com`.

## Verification checklist

### Current Render fallback

1. Build frontend with `VITE_API_BASE_URL=https://prince-of-pan-africa-backend.onrender.com`.
2. Set backend `SESSION_COOKIE_SAMESITE=none`.
3. Leave backend `SESSION_COOKIE_DOMAIN` unset/empty.
4. Login on `https://simbawaujamaa.com`.
5. Confirm `POST /auth/login` responds with `Set-Cookie: mufasa_session=...; HttpOnly; Secure; Path=/; SameSite=none` and no `Domain=` attribute.
6. Open `/debug/auth` and confirm the backend request reaches Render rather than a suspended custom-domain page.
7. Confirm `/auth/me` and `/auth/debug/me` behave as expected for the logged-in or logged-out state.

### Future same-site custom API

1. Confirm `https://api.simbawaujamaa.com/health` returns the backend response.
2. Build frontend with `VITE_API_BASE_URL=https://api.simbawaujamaa.com`.
3. Set backend `SESSION_COOKIE_SAMESITE=lax`.
4. Set backend `SESSION_COOKIE_DOMAIN=.simbawaujamaa.com`.
5. Login on `https://simbawaujamaa.com`.
6. Confirm `POST /auth/login` responds with `Set-Cookie: mufasa_session=...; HttpOnly; Secure; Path=/; SameSite=lax; Domain=.simbawaujamaa.com`.
7. Open `/debug/auth` and confirm frontend `user.email` is populated.
8. Confirm `/debug/auth` backend `/auth/debug/me` returns `200` for an authenticated admin.
9. Confirm `/auth/me` returns authenticated user/RBAC data.
10. Confirm admin users show `isAdminUser=true`.
11. Confirm admin users see Operations Deck and Text Book Organizer.
12. Confirm `/dashboard` works.
13. Confirm `/library/organizer` works for admin/subscriber accounts.
