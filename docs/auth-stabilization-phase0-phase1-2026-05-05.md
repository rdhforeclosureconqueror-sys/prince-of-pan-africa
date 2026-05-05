# Auth Stabilization — Phase 0 Trace + Phase 1 SSoT Decision (2026-05-05)

## Scope executed
- Executed **Phase 0** (no-code trace using source + auth tests).
- Executed **Phase 1** (single-source-of-truth decision and variable classification).
- **Stopped before Phase 2** (no bridge behavior changes made).

## Phase 0 — Full login lifecycle trace

### 1) Backend URL login uses
- Frontend auth form posts to `api(endpoint)` where `endpoint` is `/auth/login` (or `/auth/join`).
- `api()` resolves full URL as `${API_BASE_URL}${path}`.
- `API_BASE_URL` resolves to:
  - `VITE_API_BASE_URL` if set, else
  - `http://localhost:3000` on localhost, else
  - `https://prince-of-pan-africa-backend.onrender.com` in non-local runtime.

### 2) Whether `POST /auth/login` returns `Set-Cookie`
- Yes. Backend `auth_login` calls `_set_session_cookie(response, user.id)`.
- Phase 7 auth wiring test confirms login succeeds and returns cookie (`login.cookies.get('mufasa_session')`).

### 3) Cookie shape: Name, Domain, Path, SameSite, Secure, HttpOnly
- Name: `mufasa_session`.
- Domain: **not explicitly set** by backend (browser defaults host-only domain).
- Path: **not explicitly set** by backend (framework default path behavior).
- SameSite: `none` when secure cookie mode is enabled (prod-like env), otherwise `lax`.
- Secure: `true` in prod-like env; `false` in local/dev/test.
- HttpOnly: `true`.

### 4) Whether `GET /auth/me` returns 200 immediately after login
- Yes in current backend test flow: login -> `/auth/me` succeeds with 200 and `authenticated=true`.

### 5) Whether `/auth/me` still returns 200 after refresh
- In backend/test-client lifecycle this is true while cookie is retained.
- `App.jsx` also re-runs `refreshAuth()` on mount, so browser refresh is designed to rehydrate from `/auth/me`.

### 6) Whether React `App.jsx` user state updates
- Yes by design: `refreshAuth()` sets `setUser(data?.user || null)` after `/auth/me`.
- `Home.submitAuth()` calls `onAuthChange()` immediately after login, which triggers `refreshAuth()`.

### 7) Whether `GlobalNav` receives the user
- Yes by prop chain: `App -> AppRoutes -> GlobalNav` with `user={user}`.

### 8) Whether `window.APP_AUTH` updates
- No reference in current tracked React runtime files; no update path found in `src/`.

### 9) Whether `window.__AUTH_READY` updates
- No reference in current tracked React runtime files; no update path found in `src/`.

### 10) Whether `maatAuthToken` is written/removed/ignored
- No reference found in current tracked React/backend files; appears not used by current shared API auth path.

### 11) Whether `auth:changed` / `auth:ready` fire
- No reference/emitter found in current tracked React/backend files.

### 12) Which code renders “Logged out · Sign in.”
- Rendered in `src/components/GlobalNav.jsx` when `user?.email` is falsy.

### 13) Whether giant inline script overwrites/clears auth after login
- Could not directly verify in this repo snapshot: no obvious inline auth-runtime script containing `APP_AUTH`, `__AUTH_READY`, `maatAuthToken`, `auth:changed`, or `auth:ready` was found under `src/`, `public/`, or `backend/` via static search.
- This likely indicates either:
  - the load-bearing script exists only in deployed HTML/runtime outside this repository snapshot, or
  - naming drift between expected and actual legacy globals/events.

## Phase 0 outputs

### Current source(s) of auth truth (observed)
1. **Backend signed HttpOnly session cookie (`mufasa_session`)**.
2. **`GET /auth/me` response** as frontend hydration source.
3. React local state (`App.jsx user`) mirrors `/auth/me`.

### Exact failure point (current evidence)
- No backend authentication break reproduced in tests (`/auth/login` and `/auth/me` path is healthy).
- Most likely failure area is **frontend runtime cohesion/hydration boundary**: a legacy runtime surface (not visible in this repo snapshot) likely diverges from React auth state.

### Most likely issue class
- **Primary hypothesis:** legacy inline overwrite / dual-auth-state drift.
- **Secondary risk:** API host mismatch if production page runtime resolves different host/origin than expected cookie scope.
- Cookie persistence in backend implementation appears correct.

### Files involved (confirmed)
- `src/config.js`
- `src/api/api.js`
- `src/App.jsx`
- `src/components/GlobalNav.jsx`
- `src/pages/Home.jsx`
- `backend/app/routes/auth.py`
- `backend/app/session.py`
- `backend/tests/test_auth_credential_wiring_phase7.py`
- `backend/tests/test_session_cookie_security_phase5.py`

### Recommended Phase 1 fix (no behavior change)
- Adopt and document **single source of truth** as:
  - signed HttpOnly cookie (`mufasa_session`) + `/auth/me`.
- Classify legacy variables/events as **bridge-only** until proven required by load-bearing script:
  - `window.APP_AUTH` -> bridge-only
  - `window.__AUTH_READY` -> bridge-only
  - `auth:changed` -> bridge-only
  - `auth:ready` -> bridge-only
- Classify `maatAuthToken` as **deprecated** unless hard runtime dependency is found in deployed inline script.

## Phase 1 — Single Source of Truth decision

### Decision
- **Canonical auth truth:** Backend HttpOnly signed session cookie + `GET /auth/me`.

### Constraints locked
- No sensitive tokens in localStorage.
- No loosening backend auth checks.
- No guest-auth broadening.

### Legacy auth surface classification
- **Still required:**
  - None confirmed yet from repository-visible code.
- **Bridge-only (provisionally):**
  - `window.APP_AUTH`
  - `window.__AUTH_READY`
  - `auth:changed`
  - `auth:ready`
- **Deprecated (provisionally):**
  - `maatAuthToken`

### Next action gate (for Phase 2, not executed)
- Before implementing bridge code, capture runtime evidence from deployed page/devtools to confirm the exact legacy inline script hooks and overwrite timing.

---

## Runtime verification addendum (requested after initial review)

Date: 2026-05-05

### What was attempted
1. Attempted live remote runtime auth verification against `https://prince-of-pan-africa-backend.onrender.com` using real HTTP session flow with cookie jar (join/login -> `/auth/me` -> repeat `/auth/me` as refresh simulation).
2. Command failed at network boundary with `curl: (56) CONNECT tunnel failed, response 403`, so remote runtime/browser verification could not complete in this execution environment.

### Exact observed failure (runtime verification phase)
- Failure point is **environmental access block**, not app auth logic:
  - outbound tunnel/proxy denied remote request before app request/response exchange.
- Because of that block, this run could **not** capture browser-devtools-level proof for:
  - frontend POST URL as observed in browser network tab,
  - browser cookie storage view,
  - live GlobalNav post-login visual state,
  - organizer ingest via authenticated browser session.

### What remains required to fully close Phase 0
To satisfy the live-session criteria exactly, run the same checks in an environment with:
- browser automation availability (Playwright/Cypress/Selenium or manual browser), and
- outbound access to deployed frontend/backend targets.

Then collect:
- Network record for POST `/auth/login` URL + response headers (`Set-Cookie`).
- Browser cookie storage evidence (`mufasa_session`).
- `/auth/me` immediate + after hard refresh.
- UI evidence that GlobalNav received `user.email`.
- `/library/organizer` ingest 200 while authenticated.
- If mismatch occurs, classify into: not set cookie / not sent cookie / `/auth/me` false / React stale state / stale GlobalNav props.

### Interim conclusion
- This repository run cannot yet claim a complete **browser-verified Phase 0** due to tooling/network constraints encountered at runtime.
- No code changes were made; Phase 2 remains unstarted.
