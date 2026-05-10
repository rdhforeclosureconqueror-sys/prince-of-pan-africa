# Production Auth / Route / RBAC Flow Audit — 2026-05-10

## Deployment status

- Local branch contains `3a6b7b0 Fix member dashboard auth hydration` in history.
- The named commits `6be0433`, `2d04287`, and `092a817` are not present by SHA in this local history; their functional changes appear to have landed under later merge/squash commits (`30d876d`, `4c6784e`, `13496ad`, `169c10c`, `db6365e`).
- Live verification from this environment was blocked by the outbound proxy (`CONNECT tunnel failed, response 403`) for `https://simbawaujamaa.com` and the Render backend. Verify deployed SHA via `GET /system/runtime` after deploy; the backend exposes `build_commit` for this purpose.

## Frontend route map

| Route | Rendered element | Protected behavior |
| --- | --- | --- |
| `/` | `Home` | Public. Receives hydrated `user`, `isAdmin`, and organizer access props. |
| `/dashboard` | `DashboardRoute` | Waits for `authChecked`; logged-out users redirect to `/?auth=login`; admin/superadmin render `AdminOperationsDashboard`; non-admin authenticated users render `MemberDashboard`. |
| `/admin` | `Navigate` to `/dashboard` | Safe redirect to the canonical dashboard decision path. |
| `/admin-legacy` | `Navigate` to `/dashboard` | Safe redirect to the canonical dashboard decision path. |
| `/library` | `LibraryDecolonize` | Public page; organizer CTA is shown only after auth hydration and centralized organizer access. |
| `/library/organizer` | `OrganizerRoute` | Waits for auth hydration; logged-out redirects to login; subscriber/admin/superadmin render `LibraryOrganizer`; member gets access notice; feature-off gets feature notice. |
| `/audiobooks` | No React route | Backend API namespace only in current app. |
| fallback `*` | `Navigate` to `/` | Unknown frontend routes return home after React loads. Production hosting must rewrite direct deep links to `index.html`. |

## Auth flow trace

1. `App` initializes `user=null`, empty RBAC, and `authChecked=false`.
2. `App.refreshAuth()` calls `api('/auth/me')` on first mount.
3. The shared `api()` helper always sends `credentials: 'include'`, preserving the HTTP-only session cookie.
4. `/auth/me` data sets `auth.user` and `auth.rbac` together; failures reset both to anonymous.
5. `authChecked` is set in `finally`, so protected route decisions happen only after hydration completes.
6. `/dashboard` explicitly shows a loading state until `authChecked=true`, then chooses Operations Deck vs Member Dashboard from the centralized admin helper.
7. `/library/organizer` follows the same auth-hydrated pattern and central organizer helper.

## Canonical `/auth/me` payload

Expected authenticated admin shape:

```json
{
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "role": "admin",
    "is_admin": true
  },
  "rbac": {
    "roles": ["admin"],
    "permissions": [
      "admin:read_dashboard",
      "book_organizer:create_self"
    ]
  }
}
```

The implementation includes `company` and `member_profile_role` as additive compatibility fields.

## Admin RBAC trace

For a canonical admin user:

- `users.id`: current signed session user id from `mufasa_session`.
- `users.email`: returned in `/auth/me` and `/auth/debug/me`.
- `users.role`: included through `get_user_role_names()` even when `user_roles` rows exist.
- `member_profiles.role`: returned in `/auth/me` as `member_profile_role` and in `/auth/debug/me`.
- Resolved roles: union of `user_roles` plus normalized `users.role`.
- Resolved permissions: all permissions attached to resolved roles.
- Admin permissions include member dashboard, organizer create/read/update/export, and `admin:read_dashboard`.
- Superadmin receives every default permission.

## Route permission table

| Backend route | Required auth/permission | Expected missing session | Expected valid session missing permission |
| --- | --- | --- | --- |
| `GET /auth/me` | Signed session optional for hydration | `200` with anonymous payload | N/A |
| `GET /auth/debug/me` | Signed session; production non-admin blocked | `401` | `403` for non-admin production users |
| `GET /member/overview` | `member:read_overview_self` | `401` | `403` |
| `GET /member/activity` | `member:read_activity_self` | `401` | `403` |
| `GET /admin/ai/overview` | `admin:read_dashboard` | `401` | `403` |
| `GET /admin/overview` | `admin:read_dashboard` | `401` | `403` |
| `GET /admin/activity-stream` | `admin:read_activity` | `401` | `403` |
| `POST /audiobooks/organizer/ingest-text` | `book_organizer:create_self` | `401` | `403` |
| `POST /audiobooks/organizer/propose-plan` | `book_organizer:update_self` | `401` | `403` |
| `POST /audiobooks/organizer/review-structure` | `book_organizer:update_self` | `401` | `403` |
| `POST /audiobooks/organizer/preview` | `book_organizer:read_self` | `401` | `403` |
| `POST /audiobooks/organizer/export-txt` | `book_organizer:export_self` | `401` | `403` |

## Root cause fixed

The cohesive route/auth path was present, but `POST /auth/login` and `POST /auth/join` returned a serialized user without resolved RBAC, which made their immediate response say `is_admin=false` for an admin because `_serialize_user()` had no role/permission inputs. The frontend normally refreshes `/auth/me`, but a live cookie, CORS, or deployment lag problem could leave the browser with a misleading post-login payload while route hydration remained hard to diagnose. This change makes login/join return the same canonical user/RBAC payload shape as `/auth/me` and adds production-safe debug logging behind `VITE_AUTH_DEBUG`/`authDebug=1`.

## Production verification checklist

1. Deploy this commit.
2. Verify `GET /system/runtime` reports the new `build_commit`.
3. In a clean browser session, sign in as admin.
4. Confirm Network:
   - `POST /auth/login` is `200` and response has `Set-Cookie: mufasa_session=...; HttpOnly; Secure; SameSite=None` in production.
   - `GET /auth/me` is `200` and request includes cookies.
   - `GET /auth/debug/me` is `200` for admin and contains no secrets.
   - `GET /admin/ai/overview`, `GET /admin/overview`, and `GET /admin/activity-stream` are `200` for admin.
   - `GET /member/overview` and `GET /member/activity` are `200` for admin/subscriber/member accounts.
5. Manually navigate directly to `/dashboard`; verify React app is served and Operations Deck renders for admin.
6. Manually navigate to `/library/organizer`; verify organizer renders for admin and subscriber, but not member.
7. Enable temporary frontend debug with `?authDebug=1` or `VITE_AUTH_DEBUG=true` only during investigation; confirm logs show route, authChecked, email, role, roles, permission count, admin state, and organizer access only.
