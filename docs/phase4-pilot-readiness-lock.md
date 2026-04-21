# Phase 4 — Pilot Readiness Lock

Date: 2026-04-21

## Scope Lock Applied
1. No new product features were added.
2. Deferred surfaces were not reopened; they were locked behind pilot deferral messaging.
3. Work focused on end-to-end pilot verification visibility and release safety.
4. Preference was given to route gating and documentation over expanding functionality.

## A) Exact Pilot Journeys (Must Work End-to-End)

### Journey 1 — Core learner path
1. Open `/`.
2. Use top navigation to open `/timeline`.
3. Return and open `/languages`.
4. Open `/decolonize`.
5. Launch `/portal/decolonize` from the library CTA.
6. Open `/leadership`, submit assessment, and land on `/results?userId=...`.

### Journey 2 — Dashboard path
1. Open `/dashboard`.
2. Non-admin users view member metrics.
3. Admin users view Operations Deck.
4. Admin can access `/ops/verification` for release checks.

## B) Page-by-Page / Route-by-Route Trace
- Navigation now exposes only pilot-safe links plus dashboard/admin links.
- Included routes remain active and reachable.
- Deferred routes remain reachable by URL but now render a clear pilot deferral notice instead of incomplete functionality.

## C) Visible Surfaces Audit (Broken/Misleading/Incomplete)
- Prior to lock, several routes were visible despite being incomplete or backend-dependent (`/study`, `/language-practice`, `/pagt`, `/membership`, `/ledger`, `/fitness`, `/calendar`, `/journal`).
- These are now explicitly labeled deferred-for-pilot to prevent misleading UX.

## D) Visibility Control Actions
- Reduced global navigation to pilot routes only.
- Added a shared `PilotDeferredPage` and mapped excluded routes to that page.
- Preserved URLs for controlled messaging rather than hard 404/redirect, so testers receive explicit scope intent.

## E) Final Pilot Readiness Matrix

### 1) Working and in-scope
- `/`
- `/dashboard`
- `/timeline` and `/history`
- `/languages`
- `/decolonize`
- `/portal/decolonize`
- `/leadership`
- `/results`
- `/ops/verification` (admin)

### 2) Visible but intentionally deferred
- None in navigation. Deferred surfaces are URL-accessible only and explicitly labeled.

### 3) Hidden/disabled
- Hidden from nav and disabled for pilot via deferral page:
  - `/fitness`
  - `/language-practice`
  - `/calendar`
  - `/journal`
  - `/study`
  - `/pagt`
  - `/membership`
  - `/ledger`

### 4) Unresolved blockers
- No new code-level blockers introduced by Phase 4 lock.
- Operational risk remains environment-dependent backend health (API/auth/services) and should be validated through `/ops/verification` during go-live checks.

## Required Phase 4 Report

1. **Exact files changed**
   - `src/App.jsx`
   - `src/components/GlobalNav.jsx`
   - `src/pages/PilotDeferredPage.jsx`
   - `src/pilotScope.js`
   - `docs/phase4-pilot-readiness-lock.md`
2. **Pilot journeys traced**
   - Core learner journey and dashboard/admin journey (listed above).
3. **Visible routes/pages included in pilot**
   - `/`, `/dashboard`, `/timeline`, `/history`, `/languages`, `/decolonize`, `/portal/decolonize`, `/leadership`, `/results`, `/ops/verification`.
4. **Routes/pages intentionally excluded from pilot**
   - `/fitness`, `/language-practice`, `/calendar`, `/journal`, `/study`, `/pagt`, `/membership`, `/ledger`.
5. **Remaining blockers, if any**
   - Environment/backend availability checks required at release time; no new frontend lock blockers.
6. **Smoke verification steps**
   - Build the frontend bundle.
   - Validate pilot links render.
   - Validate deferred URLs display explicit lock messaging.
   - Validate admin verification route accessibility when admin identity is present.
7. **Final recommendation**
   - **GO**, contingent on verification endpoint passing in target environment.
8. **PASS / FAIL**
   - **PASS** for Phase 4 Pilot Readiness Lock implementation.
