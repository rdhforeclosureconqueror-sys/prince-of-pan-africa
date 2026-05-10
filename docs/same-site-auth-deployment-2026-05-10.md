# Same-site auth deployment fix — 2026-05-10

## Live failure observed

The `/debug/auth` page showed the frontend was fully unauthenticated even after login:

- Frontend origin: `https://simbawaujamaa.com`
- API base URL: `https://prince-of-pan-africa-backend.onrender.com`
- Frontend `user.email`: `null`
- Frontend roles/permissions: empty arrays
- Backend `/auth/debug/me`: `401 {"detail":"Authentication required"}`

That means the backend did not receive the `mufasa_session` cookie. This is a session-cookie delivery problem before admin/RBAC checks can run.

## Required production topology

Use a same-site browser-facing API domain instead of exposing the Render service hostname to browsers:

- Frontend: `https://simbawaujamaa.com`
- Backend API: `https://api.simbawaujamaa.com`

The frontend must be built with:

```env
VITE_API_BASE_URL=https://api.simbawaujamaa.com
```

The backend CORS allowlist must include only the browser origins that should call the API with credentials:

```env
ALLOWED_ORIGINS=https://simbawaujamaa.com,https://www.simbawaujamaa.com
```

## Session cookie policy

Production session cookies are now configurable with these environment variables:

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

`SameSite=Lax` is appropriate once the frontend and API are same-site subdomains under `simbawaujamaa.com`. If the backend must temporarily remain browser-facing at `onrender.com`, cookie auth may still fail in Safari/mobile browsers even with `SameSite=None; Secure`; do not treat that as the long-term architecture.

## Verification checklist

1. Login on `https://simbawaujamaa.com`.
2. Confirm `POST /auth/login` responds with `Set-Cookie: mufasa_session=...; HttpOnly; Secure; Path=/; SameSite=lax; Domain=.simbawaujamaa.com`.
3. Open `/debug/auth` and confirm frontend `user.email` is populated.
4. Confirm `/debug/auth` backend `/auth/debug/me` returns `200`.
5. Confirm `/auth/me` returns authenticated user/RBAC data.
6. Confirm admin users show `isAdminUser=true`.
7. Confirm admin users see Operations Deck and Text Book Organizer.
8. Confirm `/dashboard` works.
9. Confirm `/library/organizer` works for admin/subscriber accounts.
