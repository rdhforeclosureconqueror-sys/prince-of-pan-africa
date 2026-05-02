# Repo-Wide Route/Data Wiring Trace Report (2026-05-02)

## Executive summary
- Primary frontend runtime API origin is centralized at `API_BASE_URL` and defaults to `https://api.simbawaujamaa.com` in non-local hosts; many calls use shared `api()` client with cookies forced on (`credentials: include`).
- Operations Deck endpoints are real and mounted (`/admin/ai/overview`, `/admin/overview`, `/admin/activity-stream`) and require RBAC permissions. Browser 401s are most likely session cookie transport/parsing issues, not missing route mounts.
- There is a critical auth mismatch in audiobook routes: they parse the session cookie as `int`, but auth now writes signed cookie payloads. This can silently downgrade signed-in users to guest-mode data paths.
- Assessment frontend calls do not include credentials, while backend requires auth permissions, creating likely 401 behavior for submit/results/dashboard.
- Verification frontend call omits credentials while backend requires `system:read_verification`, so this path can 401 even when logged in.
- Swahili and Brain Games are mostly frontend/local assets with no dedicated backend routes in this repo.

## Route trace table
(See report body for full mapping details.)

## Operation Deck deep trace
- Frontend component: `src/pages/AdminOperationsDashboard.jsx`.
- Calls via shared API client: `api('/admin/ai/overview')` fallback `api('/admin/overview')`, and `api('/admin/activity-stream')`.
- Credentials: Included by `api()` wrapper unconditionally.
- Backend routes exist:
  - `/admin/ai/overview` (`admin_ai_overview`) permission `admin:read_dashboard`.
  - `/admin/overview` (`admin_overview_compat`) permission `admin:read_dashboard`.
  - `/admin/activity-stream` (`admin_activity_stream_compat`) permission `admin:read_activity`.
- Response mapping:
  - Frontend expects overview at `payload.data.metrics` and activity at `items[]`.
  - Backend returns exactly those keys.
- DB-backed cards:
  - Real counts: users, member profiles, activity logs, leadership assessments, audiobooks, audiobook progress, reflections, users_by_role, new users (7d), active users (7d).
- Likely 401 origin:
  - Missing/invalid session cookie at backend dependency layer (`require_auth`/`require_permission`).

## API base URL inventory
- `src/config.js`
  - `API_BASE_URL`: env `VITE_API_BASE_URL` or localhost fallback, else `https://api.simbawaujamaa.com`.
  - `WS_BASE_URL`: env or `wss://api.simbawaujamaa.com`.
  - Other external services: `MUFASA_API_URL`, `OPENVOICE_API_URL` (Render domains).
- Hardcoded backend/service origins found:
  - `https://api.simbawaujamaa.com` (primary API default).
  - `https://mufasa-knowledge-bank.onrender.com` (knowledge bank service).
  - `https://aivoice-wmrv.onrender.com` (voice service).
- Mixed-origin risk:
  - Most modules use `API_BASE_URL`; however auth/session-sensitive calls in some files bypass shared `api()` and use raw `fetch`, sometimes without credentials.

## Auth/session trace
- Login/join:
  - Frontend: `Home.submitAuth()` posts `/auth/join` or `/auth/login` with `credentials: include`.
  - Backend sets session cookie using signed value via `build_session_cookie_value()` and `response.set_cookie()`.
- Logout:
  - Frontend posts `/auth/logout` with credentials.
  - Backend deletes cookie with matching SameSite/Secure policy.
- `/auth/me`:
  - Frontend called from app bootstrap and other surfaces with credentials.
  - Backend returns `{ok, auth, authenticated, user, company, member_profile_role, rbac{roles,permissions}}` when authenticated.
- 401 sources:
  - Any `require_permission(...)` route when `get_current_user()` cannot parse/validate cookie.
  - CORS/cookie policy mismatches (cross-site secure cookie expectations).
  - Frontend calls that omit credentials (assessment and verification paths).

## Response shape mismatches
- Assessment service frontend expects auth-free behavior but backend enforces permission checks.
- Assessment frontend `submitLeadershipAssessment`, `fetchLeadershipResultByUserId`, `fetchLeadershipDashboard` use raw `fetch` without credentials -> likely 401 despite otherwise matching JSON shapes.
- System Verification frontend `fetch('/system/verification/full')` without credentials, backend requires permission.
- Audiobook auth mismatch (cookie format) may return guest dataset while frontend assumes current user records.

## Stub/missing endpoint inventory
- Admin stubs:
  - `/admin/ai/members`, `/admin/ai/profiles`, `/admin/members`, `/admin/profiles`, `/admin/holistic/overview` currently return empty arrays.
- Swahili:
  - Frontend routes/assets in `public/languages/*` and links from nav/pages.
  - No backend Swahili API routes found.
- Brain Games:
  - Frontend local game modules (`rhythmGame`, `sightGame`, `puzzleGame`) mounted in `BrainTraining` page.
  - No backend brain-game routes found.

## Highest-risk broken links
1. Assessment endpoints called without credentials while backend requires auth permissions.
2. Verification endpoint called without credentials while backend route is permission-guarded.
3. Audiobook route auth parser expects integer cookie; signed session cookie format likely breaks user resolution.
4. Any cross-origin deployment where cookie SameSite/Secure settings and allowed origins are misaligned.

## Recommended fix order
1. Standardize frontend assessment + verification to shared `api()` client (cookie-including).
2. Fix audiobook user resolution to use shared session parser (`parse_session_cookie_value`) instead of `int(cookie)`.
3. Verify deployed `ALLOWED_ORIGINS`/`CORS_ALLOWED_ORIGINS` includes exact frontend origin(s).
4. Add explicit frontend handling for 401/403 in leadership and verification surfaces.
5. Decide whether admin member/profile/holistic routes should remain stubbed or be DB-backed.

## Files inspected
- Frontend:
  - `src/config.js`
  - `src/api/api.js`
  - `src/App.jsx`
  - `src/pages/Home.jsx`
  - `src/pages/AdminOperationsDashboard.jsx`
  - `src/pages/MemberDashboard.jsx`
  - `src/services/leadershipService.js`
  - `src/pages/StudyPage.jsx`
  - `src/pages/SystemVerificationPage.jsx`
  - `src/pages/BrainTraining.jsx`
  - `src/pages/LanguagesHub.jsx`
  - `src/components/GlobalNav.jsx`
- Backend:
  - `backend/app/main.py`
  - `backend/app/routes/auth.py`
  - `backend/app/dependencies/auth.py`
  - `backend/app/routes/admin.py`
  - `backend/app/routes/member.py`
  - `backend/app/routes/assessment.py`
  - `backend/app/routes/audiobook.py`
  - `backend/app/routes/system.py`
  - `backend/app/models.py`

## Tests/build commands recommended
- Frontend static:
  - `npm run build`
- Backend tests focused on auth + routing:
  - `pytest backend/tests/test_session_cookie_security_phase5.py`
  - `pytest backend/tests/test_rbac_phase2_route_protection.py`
  - `pytest backend/tests/test_assessment_dashboard_chain.py`
- Targeted API smoke (with authenticated cookie jar):
  - `/auth/login` -> `/auth/me` -> `/admin/ai/overview` -> `/admin/activity-stream`
  - `/assessment/submit` -> `/assessment/dashboard/{id}`
  - `/audiobooks` list after login
