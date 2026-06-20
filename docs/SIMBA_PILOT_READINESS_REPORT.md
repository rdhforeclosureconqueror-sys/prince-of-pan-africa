# Simba Pilot Readiness Report

_Date: 2026-06-20_

## Purpose

This report evaluates repository readiness for a controlled Simba pilot. It is documentation-only and does not modify runtime systems.

## Readiness Classifications

- 🟢 **Production Ready**: Stable implementation with clear route/API, tests, and low pilot risk.
- 🟡 **Functional but Needs Polish**: Works for a pilot but needs UX, docs, operational hardening, or environment validation.
- 🟠 **Prototype**: Exists but is incomplete, disconnected, or not safe as a primary pilot promise.
- 🔴 **Architecture Only**: Documented blueprint without production implementation.
- ⚪ **Planned Future Capability**: Future roadmap with little/no current implementation.

## Executive Readiness Snapshot

- **Current repository maturity:** Late prototype / early internal pilot platform.
- **Recommended pilot readiness score:** **72 / 100** for a controlled, guided pilot; **55 / 100** for a broad public self-serve launch.
- **Best pilot shape:** Curated cohort with clear navigation, manual support, environment checks, and admin monitoring.

## Capability Ratings

| Capability | Rating | Why | Before-pilot recommendation |
| --- | --- | --- | --- |
| Constitution / Operating Philosophy | 🟢 | Clear documents define mission, dignity, agency, stewardship, and governance. | Make these the first onboarding docs for contributors. |
| Architecture Decision Framework | 🟢 | Strong planning guardrails exist. | Require use before Phase 2 work. |
| Landing page / visitor path | 🟡 | Existing public entry works but messaging can be clearer. | Tighten CTA sequence and pilot expectation language. |
| Authentication | 🟡 | Implemented and tested, but live cookies/session behavior remains deployment-sensitive. | Run smoke tests in target environment; document recovery steps. |
| RBAC | 🟡 | Roles/permissions implemented and tested. | Add admin-visible role audit before wider launch. |
| Member Dashboard | 🟡 | Provides authenticated landing and member metrics. | Align content with exact pilot journey and hide unsupported promises. |
| Admin Operations | 🟡 | Useful internal dashboard and routes exist. | Create operator runbook and canonical endpoint list. |
| System Verification | 🟢 | Dedicated route/API supports release checks. | Make it required go/no-go step. |
| Knowledge Commons | 🟠 | Strong vision and several implemented content slices, but no unified commons UX. | Present Library/Timeline/Languages as current Commons MVP. |
| Library | 🟡 | Functional surface and book assets exist. | Clarify persistence/progress limitations. |
| Study Page | 🟠 | Route exists but earlier pilot docs deferred study; status needs decision. | Either pilot-polish or hide before launch. |
| Audiobooks | 🟠 | Robust backend, but frontend/user workflow and quotas require polish. | Keep creator workflow limited to guided/builder testers. |
| Text Book Organizer | 🟠 | Feature-flagged, permission-gated, and well tested in backend. | Keep hidden unless Builder cohort is specifically testing it. |
| Publishing | 🟠 | Pieces exist via library/audiobook/organizer; no complete publishing institution UX. | Position as future creator pipeline. |
| Swahili | 🟡 | Static lesson and nav link exist. | Add progress caveat and test static asset delivery. |
| Yoruba | 🟡 | Static lesson and nav link exist. | Add progress caveat and test static asset delivery. |
| Languages Hub | 🟡 | Usable hub for language entry. | Keep small and reliable; avoid promising full curriculum. |
| Brain Training | 🟠 | Games exist, but persistence and pilot value proposition unclear. | Keep optional/secondary or hide from primary pilot. |
| Timeline / History | 🟡 | Pilot-safe learning surface with static data. | Validate content and source quality. |
| Daily Historical Spotlights | 🟡 | Data and validation tooling exist. | Decide whether it appears in pilot UI/Discord. |
| Assessment Center | 🟡 | Integrated frontend and Garvey-style routes exist. | Ensure result UX and empty states are clear. |
| Leadership Assessment legacy path | 🟠 | Functional but overlaps with Garvey. | Treat as compatibility until consolidated. |
| Garvey integrations | 🟡 | Catalog/results/archetypes/callbacks/growth profile implemented. | Document external contract and environment requirements. |
| Characteristics | 🔴 | Framework exists but no user-facing implementation. | Do not promise live characteristic scoring in pilot. |
| Archetypes | 🟠 | Assessment archetypes exist; community archetype framework is planning-only. | Clarify distinction in docs and UI copy. |
| Development Pathways | 🔴 | Excellent architecture, no production workflow. | Pilot as manual recommendation language only. |
| Community Circles | 🔴 | Documented, not implemented as working group product. | Keep hidden; use manual cohort structure. |
| Community Directory | 🟠 | Page exists, likely incomplete privacy/data model. | Hide or label as limited until privacy design is complete. |
| Community Operations | 🟡 | Framework exists and preparedness module is active. | Use preparedness as operations proof-of-concept. |
| Preparedness | 🟡 | API/models/page exist. | Pilot with small group; add clear empty states and privacy guidance. |
| Participation Engine | 🟠 | Backend foundation exists; member-facing UX limited. | Use behind the scenes; do not over-emphasize STAR/leaderboards yet. |
| STAR | 🟠 | Data/API foundation exists but reward policy and UX are incomplete. | Keep STAR low-key or internal until rules are explained. |
| Marketplace | ⚪ | Future architecture only. | Keep hidden. |
| Business Systems | 🟠 | Billing/membership/apps exist; broader business workflows planned. | Pilot only membership/billing essentials. |
| Applications | 🟠 | Static/application page exists. | Use only for informational intake if reviewed. |
| PocketPT / Fitness | 🟠 | Components exist but route is deferred. | Keep hidden until privacy/safety/product scope is defined. |
| Investment Platform / Ledger | 🟠 | v2-ledger prototype exists; investment workflow not ready. | Keep hidden from pilot. |
| Pagt / talent | 🟠 | Deferred prototype. | Keep hidden. |
| Voice / AI Voice | 🟠 | Multiple endpoints and utilities exist; provider-dependent and duplicated. | Use only where stable; consolidate service boundary. |
| Chat | 🟠 | Backend endpoints exist; no polished member assistant product. | Keep experimental. |
| Skill World | 🟠 | Audio/API slice exists. | Future learning engine; not pilot core. |
| Discord Bridge | 🟡 | Implemented admin/test/daily-fact bridge but config-dependent. | Validate bot/token/channel config and restrict admin actions. |
| Notifications | 🟠 | Toasts/components/Discord messages exist, no unified system. | Avoid notification promises beyond Discord/admin tests. |
| Analytics | 🟡 | Admin overview and assessment analytics exist. | Create privacy-aware metric definitions. |
| Content share tracking | 🟡 | Implemented; privacy messaging needed. | Add disclosure before broader use. |
| Settings | 🟠 | Debug/config exists but no member settings center. | Add settings to Phase 2; do not promise self-serve preferences. |
| Navigation | 🟡 | Pilot nav is constrained, but current route map has mixed deferred/active decisions. | Reconcile pilotScope, route map, and pilot docs. |
| Deployment/env tooling | 🟡 | Render config, env examples, audits, smoke scripts exist. | Run full smoke in target environment before inviting cohort. |

## Critical Gaps

1. **Pilot scope drift:** Current routes expose some areas earlier marked deferred. This must be resolved in docs and route visibility before public testing.
2. **Garvey/legacy assessment overlap:** Two assessment paths can confuse both developers and members.
3. **STAR policy gap:** Data structures exist, but member-facing rules, fraud/verification process, and reward meaning need explanation.
4. **Settings/privacy gap:** There is no full member settings center for notification preferences, data visibility, or privacy choices.
5. **Unified Knowledge Commons gap:** Library, timeline, languages, audiobooks, and study are not yet presented as one coherent commons.
6. **Voice service duplication:** Multiple endpoints increase maintenance and quota risk.
7. **Future-feature visibility risk:** Ledger, fitness, marketplace, publishing, circles, and investment can overpromise if shown too early.

## Missing UX

- First-run member orientation.
- Empty states for assessments, preparedness, library progress, STAR, and dashboard metrics.
- Clear explanation of what Garvey results mean and do not mean.
- Privacy disclosures for assessments, share tracking, Discord, and participation.
- Admin operator workflow for go-live verification.
- Member settings/preferences.

## Missing Documentation

- Canonical API ownership map.
- Garvey callback and environment contract.
- Stripe live operations runbook.
- Discord operations runbook.
- STAR earning/verification policy.
- Pilot support escalation guide.

## Technical Debt and Simplification Opportunities

- Consolidate voice/TTS APIs behind a shared service layer.
- Declare canonical assessment route family and deprecate ambiguous legacy paths gradually.
- Remove or document root-level legacy files and disconnected prototypes.
- Align frontend route availability with pilot navigation decisions.
- Unify admin API naming and compatibility-route policy.

## High-Priority Pilot Work

1. Freeze visible pilot navigation and direct URLs.
2. Run backend pytest suite and frontend build in target environment.
3. Validate auth, billing status, dashboard, assessments, library/languages/timeline, preparedness, and admin verification.
4. Add human-readable pilot limitations to member-facing pages.
5. Prepare admin support runbook.

## Low-Risk Improvements

- Add docs index linking the new atlas documents.
- Add empty-state copy without changing data behavior.
- Add operator checklists for Stripe/Discord/env verification.
- Add a one-page member pilot guide.

## Final Recommendation

Proceed with a **controlled pilot** centered on learning, assessment, member dashboard, preparedness, and admin verification. Keep marketplace, investment, PocketPT, community circles, full publishing, STAR rewards marketplace, and advanced voice/chat hidden or explicitly experimental until Phase 2/3.
