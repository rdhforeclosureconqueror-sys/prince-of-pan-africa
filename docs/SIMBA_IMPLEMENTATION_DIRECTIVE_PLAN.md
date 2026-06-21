# Simba Implementation Directive Plan

_Date: 2026-06-21_

## Status

This plan completes the pre-implementation review required by the Simba Implementation Directive. It is documentation-only and does not modify production code, runtime behavior, APIs, database schemas, permissions, authentication, Garvey behavior, Simba runtime behavior, STAR behavior, Marketplace behavior, Publishing behavior, PocketPT behavior, Investment behavior, or member-facing workflows.

No production implementation should begin from this directive until a specific feature scope is selected from the roadmap and reviewed against the repository observations below.

## Institution Owner

**Primary owner:** Simba / Member Experience for implementation planning and routing discipline.

**Contributing institutions:**

- Knowledge Commons, when a selected feature affects learning, library, history, languages, study, publishing, or teach-back surfaces.
- Garvey, when a selected feature affects assessments, evidence, result display, callbacks, or growth-profile inputs.
- Community Operations and Preparedness, when a selected feature affects projects, volunteer coordination, readiness, mutual aid, operations dashboards, or operational activity.
- Marketplace, only for commerce and listings work.
- Investment Platform, only for ownership, capital, ledger, or investment education work.

## Roadmap Phase

**Phase 1 — Pilot Stabilization** is the active phase for this directive. The repository already contains architecture and prototype breadth; the next implementation should stabilize the pilot spine before introducing new institutions or broad feature families.

## Mission

The next implementation should make members stronger by reducing confusion, clarifying what is currently available, and creating a trustworthy path from arrival to member home, learning, assessments, preparedness, and support.

It should make the community stronger by improving pilot reliability, operator visibility, and institutional boundaries so future work can grow through reusable systems rather than duplicate dashboards, duplicate APIs, or conflicting ownership models.

## Architecture References Reviewed

The following Version 1.0 references are relevant to this directive:

- `docs/SIMBA_ARCHITECTURE_v1.0.md` — establishes Architecture Version 1.0, the institutional baseline, and the reuse-before-rebuilding rule.
- `docs/SIMBA_IMPLEMENTATION_MASTER_ROADMAP.md` — identifies Phase 1 pilot stabilization as the current implementation priority and sequences later phases.
- `docs/SIMBA_ARCHITECTURE_DECISION_FRAMEWORK.md` — defines the feature review questions that must be answered before a concrete build begins.
- `docs/SIMBA_ECOSYSTEM_ARCHITECTURE.md` — defines the main engines and reminds implementers that technology serves the mission.
- `docs/MEMBER_LIFECYCLE_ARCHITECTURE.md` — places features in the visitor-to-legacy journey and protects member agency.
- `docs/SIMBA_KNOWLEDGE_COMMONS_ARCHITECTURE.md` — governs learning, reflection, study, mentorship, teach-back, and preservation work.
- `docs/COMMUNITY_OPERATIONS_FRAMEWORK.md` — governs operations modules and establishes Preparedness as the first live operations module.
- `docs/SIMBA_INSTITUTION_DEPENDENCY_MAP.md` — defines ownership, data boundaries, dependencies, and sensitive-data constraints.
- `docs/SIMBA_PILOT_READINESS_REPORT.md` — identifies current readiness, pilot-safe areas, prototypes, and critical launch gaps.
- `docs/SIMBA_PROJECT_CONTROL_CENTER.md` — records the current phase, sprint, pilot score, blockers, and operating rule.

## Repository Observations

### What already exists

- A Vite/React frontend with member, admin, learning, assessment, preparedness, membership, and prototype routes.
- A formal Architecture Version 1.0 baseline and roadmap that emphasize Phase 1 pilot stabilization.
- Member-facing pilot surfaces: home, dashboard, onboarding, membership, assessment center, library, languages, timeline/history, preparedness, and community directory.
- Reusable Community Operations concepts in `src/operations/communityOperationsRegistry.js` and `src/components/operations/OperationComponents.jsx`.
- Preparedness as the first live operations proof-of-concept through `src/pages/CommunityPreparednessPage.jsx`, `src/api/preparedness.js`, and shared operations components.
- Garvey-aligned assessment routes and Assessment Center pages, with legacy leadership assessment compatibility still present.
- Admin/operator surfaces, including admin dashboards, admin operations dashboard, system verification, and route-level admin navigation.
- Backend tests covering RBAC, auth cohesion, member dashboard auth, admin analytics, billing, Discord, community labor exchange, and assessment-related routes.

### What can be reused

- The existing pilot route map and `src/pilotScope.js` should be reused for navigation discipline rather than creating a second feature-flag system.
- Existing API clients in `src/api/` should be extended only when a selected feature needs a real endpoint; duplicate clients should not be introduced.
- Shared operations components and the operations registry should be used for any Phase 2 operations module instead of creating another dashboard pattern.
- Assessment Center routes should be the canonical member-facing entry for Garvey-related work; legacy assessment routes should remain compatibility paths until consolidation.
- Existing admin dashboards should be refined or consolidated instead of creating a new steward dashboard.
- Existing documentation assets should be linked and tightened rather than replaced by another architecture layer.

### Duplicates and overlap

- Assessment Center and legacy Leadership Assessment routes overlap and can confuse members unless copy and redirects stay clear.
- Admin dashboard surfaces are broad and partially overlapping; future steward work should consolidate information architecture before adding another dashboard.
- Voice and AI service utilities appear in multiple places and should be consolidated before any assistant-like feature is promoted.
- Knowledge Commons exists as several slices rather than one unified commons experience; Phase 1 should present the slices honestly as the current MVP.
- Future-facing systems such as Marketplace, Investment/Ledger, PocketPT/Fitness, Pagt, and some community directory concepts exist as prototypes or planned surfaces and should not be promoted as pilot-core.

### Technical debt

- Pilot route visibility, documentation status, and member-facing navigation need continued reconciliation.
- Privacy and consent language is incomplete for preparedness, directory/profile sharing, STAR, analytics, and assessment interpretation.
- STAR has data/API foundations but needs clearer member-facing policy before heavy exposure.
- Some implementation references in Architecture Version 1.0 point to documents that must remain synchronized with actual repository filenames and current scope.
- Production readiness depends on deployment-specific auth, cookie, Garvey callback, Stripe, Discord, and provider configuration checks.

### Refactor instead of rebuild

- Refactor current dashboards, route guards, and navigation copy before adding new dashboards.
- Extend Community Operations registry patterns before adding separate operations module systems.
- Consolidate assessment UX around Assessment Center before adding new assessment entry points.
- Present Knowledge Commons slices through existing pages before building a separate learning platform shell.
- Add compatibility adapters for operations or preparedness data before migrating schemas or renaming records.

## Files Affected by a Likely Phase 1 Implementation

A concrete Phase 1 stabilization task will likely touch some subset of:

- `src/App.jsx`
- `src/pilotScope.js`
- `src/components/GlobalNav.jsx`
- `src/components/NavBar.jsx`
- `src/pages/Home.jsx`
- `src/pages/MemberDashboard.jsx`
- `src/pages/AssessmentCenter.jsx`
- `src/pages/CommunityPreparednessPage.jsx`
- `src/operations/communityOperationsRegistry.js`
- `src/components/operations/OperationComponents.jsx`
- `docs/SIMBA_PROJECT_CONTROL_CENTER.md`
- `docs/manual-internal-pilot-checklist.md`
- `docs/internal-pilot-deployment-smoke-test-2026-04-30.md`

This planning pass changes only this document.

## Dependencies

- Stable auth/session behavior in the target deployment environment.
- Confirmed Garvey assessment catalog/results/callback contract and environment variables.
- Known Stripe membership and entitlement state for pilot users.
- Admin/RBAC access for operator checks.
- Discord and external provider credentials only if the selected implementation touches those integrations.
- Agreement on which routes are pilot-ready, hidden, prototype-only, or future.

## Risks

- Scope drift from implementing a broad new feature instead of stabilizing Phase 1.
- Duplicate dashboards or APIs if new surfaces are created without reusing existing registries, components, and clients.
- Privacy leakage if preparedness, directory, assessment, STAR, or analytics data is exposed without visibility rules.
- Garvey/Simba boundary drift if implementation treats assessment output as fixed identity or recalculates Garvey evidence in Simba-owned UI.
- Marketplace or Investment boundary drift if commerce or ownership concepts are introduced before their architecture and compliance gates are ready.
- Pilot trust risk if the UI promises future systems that are not operationally supported.

## Recommended Implementation Order

1. Select one specific Phase 1 stabilization gap from the roadmap or pilot readiness report.
2. Run the Architecture Decision Framework questions for that scoped feature.
3. Confirm institution owner, lifecycle stage, pilot status, privacy posture, and data source ownership.
4. Audit existing routes, components, API clients, tests, and docs for reuse.
5. Update copy/navigation/route visibility first when the problem is scope clarity.
6. Refactor existing shared components or registries before adding new ones.
7. Add or update tests for the selected behavior.
8. Update the Project Control Center and pilot checklist with any changed status, risks, or operator steps.

## Testing Strategy

For a future concrete implementation, run the narrowest reliable checks first and then expand:

1. `npm run build` for frontend production compilation.
2. Relevant static or unit checks for changed data/docs scripts, such as `npm run validate:daily-spotlights` when historical spotlight data changes.
3. Targeted backend tests for changed backend behavior, such as `python -m pytest backend/tests/test_member_dashboard_auth.py` for dashboard/auth work.
4. `npm run verify-system` or the smoke script before pilot release when environment dependencies are available.
5. Manual route checks for changed pilot navigation, especially `/`, `/dashboard`, `/assessments`, and `/community/preparedness`.

## Follow-Up Work Before Production Code Changes

- Choose the exact Phase 1 feature or bug to implement.
- Fill the Architecture Decision Framework answers for that feature.
- Decide whether the work is copy/navigation stabilization, route gating, assessment consolidation, preparedness polish, admin support, or documentation/runbook cleanup.
- Confirm whether screenshots are required because of visible UI changes.
