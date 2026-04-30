# Final Pilot Readiness Re-Audit (2026-04-30)

## Verdict
**Ready with minor fixes** for an **internal pilot**; **not ready yet for external pilot**.

## Fixed since original audit
- Session cookies are now signed (HMAC SHA-256), timestamped, and validated with max-age enforcement, replacing unsigned cookie trust.
- App startup and health checks now validate `SESSION_SECRET`, preventing silent insecure startup in non-dev environments.
- RBAC is now data-backed with roles, permissions, and role-permission seeding (`member`, `admin`, `superadmin`).
- Admin and system routes are permission-gated using `require_permission(...)` dependencies.
- Member route reads are constrained to the authenticated user (`current_user.id`) for overview/activity data.
- Assessment submit/read/dashboard paths now bind reads/writes to authenticated user identity rather than caller-provided `userId`.
- System readiness endpoints now return structured readiness metadata (database/service/integration checks).

## Remaining blockers
1. **Environment-gated auth/session behavior causes auth test and local confidence drift without explicit pilot env contract.**  
   - Risk: **High** (pilot runtime misconfiguration can cause login/session failures).  
   - Files: `backend/app/session.py`, `backend/app/main.py`, `config/env.example`.  
   - Recommended fix: add explicit pilot env profile and test bootstrap defaults (e.g., documented `SESSION_SECRET` for non-prod CI + startup guard docs), and add a smoke test that verifies cookie creation/parsing under pilot env.

2. **System route contract mismatch between tests and implementation (`/system/verification/full`).**  
   - Risk: **Medium** (automation drift; false negatives in readiness gate).  
   - Files: `backend/tests/test_rbac_phase2_route_protection.py`, `backend/app/routes/system.py`.  
   - Recommended fix: either restore `/system/verification/full` alias or update tests/clients to the canonical route set.

3. **Direct unit tests for assessment handlers bypass FastAPI dependency injection and now fail against secured signatures.**  
   - Risk: **Medium** (test suite no longer reliably protects assessment logic regression).  
   - Files: `backend/tests/test_assessment_dashboard_chain.py`, `backend/app/routes/assessment.py`.  
   - Recommended fix: refactor tests to use `TestClient` authenticated requests or helper wrappers that pass `current_user` and `db` explicitly.

## Non-blocking improvements
- **Admin/member endpoints still return placeholder aggregates (zeros/empty lists).** Priority: P1. Timing: before external pilot metrics commitments.
- **`LoginGate` frontend is currently pass-through; no centralized 401 handling UX.** Priority: P1. Timing: before opening pilot beyond controlled users.
- **Legacy compatibility endpoints are extensive; route deprecation plan missing.** Priority: P2. Timing: during first pilot stabilization sprint.
- **Deprecated FastAPI `on_event` startup warning present.** Priority: P3. Timing: routine tech debt sprint.

## Test summary (this audit run)
- Command baseline required `PYTHONPATH=.` for test discovery.
- Outcome: **31 passed, 6 failed**.
- Failing areas:
  - Assessment dashboard chain tests (dependency-injection mismatch in direct function calls).
  - Auth password migration tests failing because `SESSION_SECRET` not set in test environment.
  - RBAC phase2 route protection expecting `/system/verification/full` (404).
- Coverage gap noted: no dedicated frontend auth flow regression tests validating 401-to-login UX behavior.

## Deployment checklist
### Required env vars
- `SESSION_SECRET` (required outside explicit local/dev fallback)
- `ENVIRONMENT` / `APP_ENV` (to control secure cookie behavior)
- DB config vars used by deployment target
- Integration vars as needed: `OPENAI_API_KEY`, `AIVOICE_BASE_URL`, `AIVOICE_API_KEY`

### Render readiness
- Backend is structurally closer to pilot-ready:
  - startup now fails fast if session secret policy is violated;
  - health endpoint includes session+database status.
- Ensure Render service has `SESSION_SECRET` set and production-like `ENVIRONMENT` value before promote.

### Manual smoke tests required
1. Login + cookie issuance + refresh navigation persistence.
2. Member user cannot read another member’s overview/activity/assessment.
3. Admin can access admin routes; member cannot.
4. `GET /health` returns `status=ok` with `details.session=ok` and `details.database=ok`.
5. `/system/verification` accessible to authorized role and denied for unauthorized role.


### Frontend auth UX decision (internal pilot)
- `LoginGate` is currently a pass-through and is not referenced by any mounted route/page component in the current frontend tree.
- For internal pilot, backend RBAC + signed session enforcement remains the authoritative protection layer.
- Before external pilot, either wire `LoginGate` (or route-level equivalent) into protected views with `/auth/me` checks, or remove it to avoid false security assumptions.

## Final recommendation
- **Internal pilot:** proceed **after** fixing test contract/runtime-env items above (or formally waiving them with compensating manual smoke test evidence).
- **External pilot:** hold until placeholders are replaced for promised admin/member metrics and frontend auth guard UX is tightened.
