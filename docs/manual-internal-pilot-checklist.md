# Internal Pilot Browser Checklist

Use this checklist to validate the live deployment through the browser only (no local terminal tests required).

## Test data needed before starting
- A **normal member** account (non-admin role).
- An **admin or superadmin** account.
- Live frontend URL (example: `https://prince-of-pan-africa.onrender.com`).
- Live backend URL (example: `https://prince-of-pan-africa-backend.onrender.com`).

## Required Render environment variables (must be set)
- `SESSION_SECRET` (required for signed session cookies and login sessions)
- `OPENAI_API_KEY`
- `AIVOICE_BASE_URL`
- `ALLOWED_ORIGINS` (must include the live frontend origin)

## Browser verification steps

| # | What page to open | What to click / do | Expected result | Pass/Fail |
|---|---|---|---|---|
| 1 | Render Dashboard → Backend service (`mufasa-knowledge-bank`) → **Environment** | Verify `SESSION_SECRET` exists and is non-empty. | `SESSION_SECRET` is present and saved in Render. | ☐ Pass ☐ Fail |
| 2 | Render Dashboard → Backend service (`mufasa-knowledge-bank`) → **Logs / Events** | Trigger or view latest deploy. | Deploy finishes successfully and service shows **Live** / healthy start (no crash loop). | ☐ Pass ☐ Fail |
| 3 | Live frontend home page (`/`) | Load page and refresh once. | Public homepage renders without 5xx errors or blank screen. | ☐ Pass ☐ Fail |
| 4 | Login / signup page | Create test member account (if needed), then log in; log out; log in again. | Signup/login/logout flows work end-to-end and return to expected pages. | ☐ Pass ☐ Fail |
| 5 | Browser DevTools → Application/Storage → Cookies (frontend or API domain) | Log in and inspect cookies. | Signed session cookie `mufasa_session` appears after login (and is removed/invalidated after logout). | ☐ Pass ☐ Fail |
| 6 | Member dashboard route (member user) | Login as normal member and open dashboard routes. | Member dashboard loads; member-only features render without authorization errors. | ☐ Pass ☐ Fail |
| 7 | Admin dashboard route (member user then admin user) | Try admin dashboard as member first, then as admin/superadmin. | Member is denied (403/redirect). Admin/superadmin can access admin dashboard successfully. | ☐ Pass ☐ Fail |
| 8 | Protected backend route in browser (example: `/api/member/me` or another auth-required endpoint) while logged out | Open route directly in browser (or fetch via app) without being authenticated. | Unauthenticated requests are blocked (401/403) and do not return protected data. | ☐ Pass ☐ Fail |

## Notes / issue log
- Record any failing step, exact URL, timestamp, user role, and screenshot.
- If step 1 or step 2 fails, stop and fix deployment config before continuing functional checks.

## Exit criteria for internal pilot testing
- All rows above marked **Pass**.
- No unauthorized access to protected routes.
- Owner confirms flows are usable for internal pilot.
