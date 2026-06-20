# Simba Project Control Center

_Date created: 2026-06-20_

## Planning-Only Notice

This document is the operational planning and tracking dashboard for the Simba repository. It does **not** implement production behavior, routes, APIs, database changes, migrations, permissions, Garvey logic, Simba runtime logic, STAR behavior, Marketplace behavior, Investment behavior, or any member-facing feature.

Future contributors should update this file whenever roadmap scope, implementation status, pilot readiness, pull requests, risks, or architectural decisions change.

---

## 1. Executive Overview

| Field | Current state |
| --- | --- |
| Overall completion percentage | **35%** ecosystem-wide implementation completion; architecture is substantially complete, but several institutions remain prototype or architecture-only. |
| Pilot readiness | **72 / 100** for a controlled guided pilot; not ready for broad public self-serve launch. |
| Current implementation phase | **Phase 1 — Pilot Stabilization**. |
| Current sprint | **Sprint 0 — Control Center, scope freeze, and launch hygiene**. |
| Current milestone | Establish a repository-level project dashboard and align current work with the Simba Implementation Master Roadmap. |
| Next milestone | Freeze pilot navigation, validate environment/auth/Garvey readiness, and prepare the operator runbook for a guided cohort. |
| Biggest blockers | Pilot scope drift, Garvey/legacy assessment overlap, STAR policy gap, settings/privacy gap, Knowledge Commons cohesion, voice service duplication, and future-feature visibility risk. |

### 1.1 Current operating summary

Simba has a strong institutional architecture and a broad implementation foundation. The immediate work is not to add new institutions, but to consolidate the pilot spine:

```text
Visitor clarity
  → Authentication / membership state
  → Member Home
  → Learning surfaces
  → Assessment Center / Garvey integration
  → Preparedness pilot
  → Admin verification and support
```

### 1.2 Current operating rule

If a proposed change does not support the current phase or unblock a later phase, it should be deferred, hidden, or run through the Architecture Decision Framework before implementation.

---

## 2. Status Keys

### 2.1 Roadmap status key

| Status | Meaning |
| --- | --- |
| Not Started | No active implementation work should be assumed. |
| Planning | Architecture or planning exists, but build work is not underway. |
| In Progress | Runtime, UX, docs, or operational work is actively being built or consolidated. |
| Testing | Build exists and is being validated for reliability, privacy, support, and integration. |
| Pilot Ready | Safe for a controlled cohort with support and known limitations. |
| Completed | Scope is implemented, tested, documented, and operationally maintainable. |

### 2.2 Institution readiness key

| Field | Meaning |
| --- | --- |
| Architecture Complete | Institutional purpose, boundaries, and core design are documented. |
| Implementation Complete | Runtime/UI/API/data workflows are fully implemented for the intended release scope. |
| Pilot Ready | Safe for controlled pilot use with support and limitations documented. |
| Production Ready | Safe for broad public/self-serve use. |
| Future Expansion | Known longer-term direction after current release scope. |

---

## 3. Institution Status

| Institution | Architecture Complete | Implementation Complete | Pilot Ready | Production Ready | Current state | Future Expansion |
| --- | --- | --- | --- | --- | --- | --- |
| Knowledge Commons | Yes | Partial | Partial | No | Architecture exists with implemented slices: Library, Timeline/History, Languages, Study, and audiobook foundations. | Unified commons taxonomy, search, progress, recommendations, annotations, group study. |
| Garvey | Yes | Partial | Partial | No | Assessment catalog/results/callback boundary exists; legacy assessment overlap remains. | External contract hardening, clearer result explanations, consolidated route ownership. |
| Member Home | Yes | Partial | Yes with polish | No | Functional authenticated landing surface with metrics and next steps. | Lifecycle-aware cards, pathway recommendations, privacy-aware personalization. |
| Community Operations | Yes | Partial | Partial | No | Framework exists; preparedness is first operational proof-of-concept. | Project records, volunteer coordination, steward dashboard, operational runbooks. |
| Community Circles | Yes | No | No | No | Architecture only; not a working group product yet. | Circle creation, facilitator tools, study/service modes, health indicators. |
| Preparedness | Yes | Partial | Partial | No | API/models/page exist and are a good controlled-pilot candidate. | Household/community summaries, mutual-aid workflows, readiness drills. |
| Marketplace | Yes | No | No | No | Planned institution; no primary runtime product. | Vendor profiles, cooperative listings, local commerce, mutual-aid exchange. |
| Publishing | Yes | Partial | Limited/creator-guided only | No | Library, audiobooks, organizer, and content-share primitives exist; no full publishing house UX. | Editorial workflow, creator pipeline, metadata, royalties, preserved knowledge collections. |
| PocketPT | Partial | Prototype | No | No | Fitness/health components exist but are deferred from pilot. | Separate health institution with strong privacy, safety, and consent boundary. |
| Investment | Yes | Prototype | No | No | Ledger-style prototypes exist; no production investment workflow. | Community capital, cooperative ownership, compliance-aware education and governance. |
| Leadership | Yes | Partial | No | No | Leadership assessment and architecture concepts exist; pipeline is not mature. | Leadership development from participation, mentorship, stewardship, and service evidence. |
| Legacy | Yes | No | No | No | Long-term lifecycle and preservation concepts are documented. | Intergenerational records, knowledge preservation, mentor legacy, institutional memory. |
| STAR | Yes | Partial | Internal/limited only | No | Participation/reward data/API foundation exists; member-facing policy and UX incomplete. | Recognition rules, verification, anti-gaming review, redemption/governance policy. |
| Assessment Center | Yes | Partial | Partial | No | Frontend is integrated with Garvey-style catalog/results; UX polish and empty states remain. | Retake flows, clearer explanations, pathway connections, assessment consolidation. |

---

## 4. Roadmap Tracker

| Phase | Status | Responsible institution(s) | Dependencies | Pull requests | Completion status | Remaining work |
| --- | --- | --- | --- | --- | --- | --- |
| Phase 0 — Architecture Completion | Completed | Architecture Governance | Constitution, Operating Philosophy, Ecosystem Architecture | TBD | Architecture planning set is complete enough to guide implementation. | Keep docs synchronized as decisions change. |
| Phase 1 — Pilot Stabilization | In Progress | Member Home, Garvey, Knowledge Commons, Preparedness, Admin/Reliability | Stable auth, session behavior, Garvey contract, pilot navigation, admin checks | TBD | Pilot spine exists but needs consolidation, polish, support docs, and environment validation. | Freeze navigation, smoke-test auth/Garvey/dashboard/learning/preparedness/admin, document runbooks. |
| Phase 2 — Community Operations | Planning | Community Operations, Preparedness, STAR | Phase 1 stability, consent/privacy rules, project model, volunteer data policy | TBD | Preparedness foundation exists; full operations platform is not complete. | Project records, volunteer coordination, steward workflows, operations dashboard. |
| Phase 3 — Community Circles | Planning | Community Circles, Knowledge Commons, Community Operations | Stable member identity, privacy rules, facilitator process, study resources | TBD | Architecture complete; implementation not started. | Circle creation, invitations, facilitator tools, notes/commitments, service/project links. |
| Phase 4 — Knowledge Commons Expansion | Planning | Knowledge Commons, Publishing, Learning Systems | Pilot learning surfaces, content taxonomy, progress model, source review | TBD | Several learning slices exist; unified commons UX incomplete. | Unified taxonomy/search, reading journeys, learning paths, annotations, group study. |
| Phase 5 — Marketplace Integration | Not Started | Marketplace, Business Systems, Publishing | Trust, identity, billing, vendor rules, business profiles, payments | TBD | Architecture only/planned. | Vendor profiles, cooperative listings, commerce rules, marketplace privacy and support. |
| Phase 6 — Investment Platform | Not Started | Investment, Business Systems, Marketplace | Mature commerce, compliance review, education, ownership policy | TBD | Prototype/ledger concepts only. | Compliance-aware design, ownership education, capital workflows, governance model. |
| Phase 7 — Leadership and Legacy | Not Started | Leadership, Legacy, STAR, Knowledge Commons | Proven participation, mentorship, stewardship patterns, records policy | TBD | Architecture concepts exist; no mature pipeline. | Leadership pathways, mentor tools, legacy preservation, institutional memory workflows. |

---

## 5. Feature Tracker

| Feature / system | Roadmap phase | Responsible institution | Dependencies | Pull requests | Completion status | Remaining work |
| --- | --- | --- | --- | --- | --- | --- |
| Assessment Sync | Phase 1 | Garvey, Assessment Center | Garvey catalog/results/callback contract, auth, member identity | TBD | Partial | Confirm canonical route family, reduce legacy overlap, document external environment contract. |
| Voice System | Phase 4 | Learning Systems, Knowledge Commons, Publishing | Provider configuration, quota policy, service boundary | TBD | Prototype/fragmented | Consolidate TTS/STT endpoints and define module-specific adapters. |
| Dashboard | Phase 1 | Member Home | Auth/session, member overview data, pilot navigation | TBD | Functional pilot surface | Align cards with current pilot promises and add clear empty states. |
| Preparedness | Phase 1 / Phase 2 | Community Operations | Auth, privacy guidance, preparedness models, steward support | TBD | Partial; pilot candidate | Add guided copy, aggregation rules, operator workflows, and project integration. |
| Marketplace | Phase 5 | Marketplace | Business profiles, payments, trust, moderation, support | TBD | Not started/runtime hidden | Keep hidden; define vendor and cooperative exchange model. |
| Business Hub | Phase 5 | Business Systems | Membership, billing, applications, business assessment concepts | TBD | Mixed/prototype | Clarify canonical business flows and relationship to Marketplace/Investment. |
| Learning Paths | Phase 4 | Knowledge Commons, Simba | Characteristics, archetypes, learning history, progress model | TBD | Architecture only | Define MVP pathway cards and opt-in goals after assessment consolidation. |
| Reading Journeys | Phase 4 | Knowledge Commons, Publishing | Library data, study page, progress persistence, annotations | TBD | Partial | Create coherent journey model and progress storage policy. |
| Community Projects | Phase 2 | Community Operations | Member identity, steward roles, privacy/consent rules, STAR vocabulary | TBD | Planning | Implement project records, tasks, owners, statuses, outcomes, and verification path. |
| Investment | Phase 6 | Investment | Marketplace maturity, compliance review, education, governance | TBD | Prototype only | Keep deferred until ownership policy and compliance posture are defined. |
| Legacy | Phase 7 | Legacy, Knowledge Commons | Member lifecycle, publishing, leadership, preservation rules | TBD | Architecture only | Define records, mentorship, legacy artifacts, and long-term stewardship model. |
| Community Circles | Phase 3 | Community Circles | Member identity, privacy, facilitator training, operations support | TBD | Architecture only | Build creation/invitation/facilitation workflows. |
| STAR Recognition | Phase 2 / Phase 7 | STAR | Participation events, verification, fraud policy, reward rules | TBD | Backend foundation | Define member-facing rules, internal verification, and pilot-safe display. |
| Admin Verification | Phase 1 | Admin/Reliability | System verification center, environment checks, operator access | TBD | Functional surface | Make go/no-go checks mandatory and document support escalation. |

---

## 6. Pull Request Log

Use this log to associate future PRs with roadmap phases and project outcomes.

| PR | Date | Phase | Institution(s) | Summary | Status | Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | Phase 1 | Project Management | Create Simba Project Control Center. | Planned | Update this row with PR number after merge. |

### 6.1 PR update rule

Every significant PR should update at least one of these sections:

- Roadmap Tracker
- Feature Tracker
- Pull Request Log
- Risks
- Decision Log, if the PR changes institutional boundaries or operating policy

---

## 7. Documentation Index

| Document | Purpose | Consult when |
| --- | --- | --- |
| `docs/SIMBA_COMMUNITY_CONSTITUTION.md` | Defines the highest-level ethical covenant, dignity, agency, and community purpose. | Any feature affects member identity, consent, agency, power, or institutional purpose. |
| `docs/SIMBA_OPERATING_PHILOSOPHY.md` | Explains how Simba develops members and how Garvey/Simba boundaries should behave. | Deciding what Simba should recommend, interpret, or avoid. |
| `docs/SIMBA_ECOSYSTEM_ARCHITECTURE.md` | Master map of institutions and system boundaries. | Placing a new feature into the correct institution. |
| `docs/SIMBA_ARCHITECTURE_DECISION_FRAMEWORK.md` | Review process for new architecture or implementation proposals. | A feature crosses institutions, introduces risk, or is not clearly in the roadmap. |
| `docs/SIMBA_IMPLEMENTATION_MASTER_ROADMAP.md` | Sequenced implementation plan from pilot stabilization through legacy. | Planning work, sprint scope, or phase transitions. |
| `docs/SIMBA_PILOT_READINESS_REPORT.md` | Evaluates current readiness and launch blockers for a controlled pilot. | Deciding whether a capability can be shown to pilot members. |
| `docs/SIMBA_ECOSYSTEM_CAPABILITY_INVENTORY.md` | Repository-wide capability status inventory. | Checking what exists, what is prototype-only, and which institution owns it. |
| `docs/SIMBA_CAPABILITY_MATRIX.md` | Comparative matrix of capability maturity, ownership, and dependencies. | Prioritizing capabilities or evaluating implementation maturity. |
| `docs/SIMBA_INSTITUTION_DEPENDENCY_MAP.md` | Build-order and dependency map between institutions. | Sequencing work or identifying upstream/downstream risk. |
| `docs/SIMBA_INSTITUTION_STEWARDSHIP_ARCHITECTURE.md` | Stewardship, maintenance, and sustainability model for institutions. | Assigning maintenance responsibility or governance ownership. |
| `docs/SIMBA_ECOSYSTEM_ATLAS.md` | Broad atlas of ecosystem surfaces and future institutional map. | Orienting contributors to how systems relate across the ecosystem. |
| `docs/SIMBA_DIGITAL_CIVILIZATION_REFERENCE_MODEL.md` | Frames Simba as cooperating institutions rather than feature accumulation. | Evaluating long-term coherence and civilization-scale direction. |
| `docs/SIMBA_USER_JOURNEY_BLUEPRINT.md` | End-to-end member journey from visitor to legacy. | Designing UX sequences or onboarding/member lifecycle touchpoints. |
| `docs/MEMBER_LIFECYCLE_ARCHITECTURE.md` | Defines lifelong member progression and development states. | Mapping features to member growth stages. |
| `docs/SIMBA_KNOWLEDGE_COMMONS_ARCHITECTURE.md` | Defines learning, reflection, study, teach-back, mentorship, and preservation. | Building learning, library, reading, publishing, or mentorship features. |
| `docs/COMMUNITY_CIRCLE_ENGINE.md` | Defines circle formation, facilitation, roles, trust-building, and support. | Building group, facilitator, or circle workflows. |
| `docs/COMMUNITY_OPERATIONS_FRAMEWORK.md` | Defines projects, operations, preparedness, volunteer coordination, and community work. | Building preparedness, mutual aid, project, steward, or operations features. |
| `docs/community-archetype-specification.md` | Defines community archetype interpretation and boundaries. | Connecting assessments to roles, pathways, or community contribution. |
| `docs/manual-internal-pilot-checklist.md` | Manual checklist for internal pilot validation. | Preparing or running a guided pilot. |
| `docs/internal-pilot-owner-run-smoke-test.md` | Owner-run smoke-test guidance. | Validating critical pilot behavior before cohort use. |
| `docs/env-audit-report.md` | Environment audit findings. | Debugging environment readiness or deployment configuration. |
| `docs/auth-stabilization-phase0-phase1-2026-05-05.md` | Auth stabilization planning. | Working on authentication/session reliability. |
| `docs/production-auth-flow-audit-2026-05-10.md` | Production auth flow audit. | Reviewing auth behavior for launch readiness. |
| `docs/stripe-implementation-plan.md` | Stripe implementation plan. | Working on billing, checkout, portal, or subscription lifecycle. |
| `docs/discord-integration-plan.md` | Discord integration plan. | Working on Discord notifications or bot/admin workflows. |

---

## 8. Decision Log

| Date | Decision | Rationale | Status | Review trigger |
| --- | --- | --- | --- | --- |
| 2026-06-20 | Garvey observes. | Garvey should collect and return assessment evidence without becoming the whole member development system. | Active | Revisit if assessment, archetype, or growth-profile ownership changes. |
| 2026-06-20 | Simba develops. | Simba turns evidence into opt-in learning, reflection, practice, contribution, and institutional development. | Active | Revisit when Development Pathways move from architecture to runtime. |
| 2026-06-20 | Marketplace owns commerce. | Commerce should not be hidden inside learning, STAR, publishing, or investment flows. | Active | Revisit before Phase 5 implementation. |
| 2026-06-20 | Investment owns ownership. | Capital, ownership, governance, and compliance risks require a separate institution. | Active | Revisit before Phase 6 implementation. |
| 2026-06-20 | Publishing preserves knowledge. | Publishing should protect and circulate authored/community knowledge instead of being reduced to generic content upload. | Active | Revisit when creator workflows or royalties are implemented. |
| 2026-06-20 | Preparedness belongs to Community Operations. | Preparedness is operational community care, not a dashboard widget or STAR reward mechanic. | Active | Revisit when projects, volunteer coordination, and readiness maps are implemented. |
| 2026-06-20 | STAR recognizes participation; it does not define member worth. | Recognition must not become ranking, surveillance, or coercive gamification. | Active | Revisit before exposing STAR rewards or leaderboards. |
| 2026-06-20 | Pilot coherence is more important than feature breadth. | A small reliable pilot is safer than exposing unfinished future institutions. | Active | Revisit after Phase 1 pilot completion. |

---

## 9. Risks

| Risk category | Current risk | Severity | Owner institution | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| Technical debt | Voice/TTS endpoints and utilities are fragmented across modules. | Medium | Learning Systems / Publishing | Define a shared voice boundary and module-specific adapters. | Open |
| Technical debt | Legacy and current assessment paths overlap. | High | Garvey / Assessment Center | Declare canonical route family and migrate/deprecate deliberately. | Open |
| Architecture debt | Some prototype islands exist outside the main pilot journey. | Medium | Architecture Governance | Document, hide, or delete after review; avoid member-facing promises. | Open |
| Integration debt | Garvey, Stripe, Discord, voice, and environment behavior depend on external configuration. | High | Reliability / Admin | Run target-environment smoke tests and document contracts. | Open |
| Documentation debt | Missing canonical API ownership map, STAR policy, Garvey contract, and operator runbooks. | High | Architecture Governance / Admin | Add docs before wider pilot. | Open |
| Pilot blocker | Pilot navigation and route availability may expose deferred areas. | High | Member Experience | Freeze visible navigation and reconcile route map with pilot scope. | Open |
| Pilot blocker | Settings/privacy controls are incomplete. | High | Member Systems / Security | Add privacy disclosures and settings roadmap before broad launch. | Open |
| Pilot blocker | STAR recognition lacks clear member-facing rules. | Medium | STAR | Keep internal/limited until earning, verification, anti-gaming, and redemption policy exists. | Open |
| Pilot blocker | Knowledge Commons is not yet one coherent member experience. | Medium | Knowledge Commons | Present current MVP honestly and define taxonomy/search/progress roadmap. | Open |

---

## 10. Success Metrics

### 10.1 Pilot success

- A guided cohort can understand Simba's purpose, join/sign in, reach Member Home, access learning surfaces, launch or review assessments, and use preparedness without confusion.
- Operators can run pre-launch checks and respond to issues using documented runbooks.
- Deferred institutions are hidden or clearly labeled as future/experimental.
- No member is misled about assessment meaning, STAR status, marketplace availability, investment capability, or privacy boundaries.

### 10.2 Version 1 success

- Pilot spine is reliable and supportable.
- Authentication, dashboard, learning surfaces, assessment center, preparedness, and admin verification have clear ownership and smoke checks.
- Knowledge Commons MVP has a coherent member-facing structure.
- Garvey integration has a documented production contract and canonical assessment path.

### 10.3 Version 2 success

- Community Operations supports real project records, volunteer coordination, preparedness summaries, and steward workflows.
- STAR can safely recognize verified participation with clear rules and privacy protections.
- Community Circles can be piloted with facilitator tools and consent-aware group workflows.

### 10.4 Version 3 success

- Knowledge Commons expands into learning paths, reading journeys, group study, progress, annotations, and publishing workflows.
- Marketplace and Business Systems can support trusted commerce and cooperative exchange without collapsing into STAR or Investment.
- Leadership pathways emerge from verified contribution, mentorship, and stewardship rather than self-declared status.

### 10.5 Long-term vision success

- Simba functions as a digital community operating system made of cooperating institutions.
- Members can move from learning to service, service to leadership, leadership to ownership, and ownership to legacy without losing agency or dignity.
- Knowledge, preparedness, commerce, investment, leadership, and legacy reinforce one another while preserving institutional boundaries.

---

## 11. Implementation Recommendations

1. Treat this document as the repository dashboard and update it in every major planning or implementation PR.
2. Keep Phase 1 focused on pilot stabilization until the pilot spine is supportable.
3. Do not expose Marketplace, Investment, PocketPT, Community Circles, advanced Publishing, or STAR reward flows as pilot promises until their sections move beyond planning/prototype status.
4. Resolve assessment ownership by making Garvey the source of truth for assessment evidence while documenting any legacy compatibility paths.
5. Create missing runbooks before broad pilot expansion: Garvey contract, Stripe operations, Discord operations, STAR policy, privacy/settings, and pilot escalation.
6. Use institution ownership as the primary anti-sprawl mechanism: if a feature has no owner institution, it is not ready to build.

---

## 12. Change Confirmation

This update is documentation only. It creates a project management control center and does not change production behavior, runtime code, APIs, database schemas, permissions, Garvey logic, Simba runtime behavior, or STAR behavior.
