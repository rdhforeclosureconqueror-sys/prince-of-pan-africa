# Internal Pilot Deployment Smoke Test — 2026-04-30

## Scope
Attempted to validate deployed Render environment for internal pilot on 2026-04-30.

## Runtime constraint encountered
All outbound HTTPS requests to Render-hosted domains from this execution environment were blocked at the network boundary with:

- `curl: (56) CONNECT tunnel failed, response 403`
- proxy response headers included `HTTP/1.1 403 Forbidden` and `server: envoy`

This prevented direct verification of live deployment behavior.

## Commands executed
- `curl -sS https://mufasa-knowledge-bank.onrender.com/health`
- `curl -sS https://mufasa-knowledge-bank.onrender.com/`
- `curl -I -sS https://prince-of-pan-africa.onrender.com`
- `curl -I -sS https://prince-of-pan-africa-frontend.onrender.com`
- `curl -I -sS https://api.simbawaujamaa.com`

## Checklist status
1. Render env vars present (`SESSION_SECRET`, `DATABASE_URL`, API keys): **UNVERIFIED (network-blocked)**
2. App startup successful on Render: **UNVERIFIED (network-blocked)**
3. `/health` safe `ok`/`degraded`: **UNVERIFIED (network-blocked)**
4. Login sets signed session cookie: **UNVERIFIED (network-blocked)**
5. Protected admin route statuses (401/403/200): **UNVERIFIED (network-blocked)**
6. Member overview/activity user isolation: **UNVERIFIED (network-blocked)**
7. Assessment submit/read for authenticated member: **UNVERIFIED (network-blocked)**
8. `/system/verification` permission-gated: **UNVERIFIED (network-blocked)**
9. No secrets exposed in public responses: **UNVERIFIED live; code/tests indicate intended behavior**

## Code-level expectations (non-live)
Based on backend route and dependency code, the expected authorization model for the requested checks is implemented:

- `/health` returns only status/service/details and does not include secret values.
- Auth routes set HTTP-only session cookie via signed token.
- Admin/member/system/assessment routes enforce permission checks through `require_permission(...)`.

These indicate readiness of implementation, but **do not replace live deployment verification**.
