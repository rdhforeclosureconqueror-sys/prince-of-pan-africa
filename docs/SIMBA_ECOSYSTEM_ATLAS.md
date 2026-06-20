# Simba Ecosystem Atlas

_Date: 2026-06-20_

## Purpose

This atlas is the master repository baseline for the Simba ecosystem before the first public pilot. It summarizes institutions, capabilities, implementation status, member experience, developer philosophy, system boundaries, and future expansion support. It is documentation-only and introduces no runtime changes.

## One-Sentence Definition

Simba is a Community Operating System that connects learning, assessment, development, service, trust, publishing, operations, commerce, investment, leadership, and legacy into one lifelong member journey.

## Core Philosophy

The repository consistently frames Simba as more than a website. The governing idea is that technology should strengthen people, families, communities, and institutions without reducing members to scores, labels, payments, or engagement metrics. The key principles are dignity, agency, continuous growth, truthfulness, stewardship, cooperation, privacy, consent, service before status, ownership through contribution, and legacy.

## Primary Institutional Split

```text
Garvey = Observation Engine
  - assessments
  - scoring
  - evidence
  - assessment archetypes
  - results and callbacks

Simba = Development Engine
  - characteristics
  - community archetypes
  - development pathways
  - recommendations
  - community opportunities
  - member journey
```

This separation is the most important architectural boundary. Garvey must not become the owner of community identity, and Simba must not mutate assessment scores.

## Institutions That Exist

1. Constitution
2. Architecture Decision Framework
3. Member Lifecycle
4. Knowledge Commons
5. Garvey
6. Simba
7. Member Home
8. Assessment Center
9. Characteristics
10. Archetypes
11. Development Pathways
12. Community Circles
13. Community Operations
14. Preparedness
15. Publishing
16. Marketplace
17. PocketPT
18. Investment Platform
19. STAR
20. Business Systems
21. Admin / Analytics
22. Discord / Notifications
23. Legacy

Some are fully implemented, some are partial, and some are architecture-only. The repository's maturity is strongest when treated as an internal pilot platform, not a complete public operating system.

## How Institutions Interact

```text
Member identity and membership
  → Auth / RBAC / Billing
  → Member Home
  → Knowledge Commons learning
  → Assessment Center
  → Garvey evidence
  → Simba interpretation
  → Characteristics / Archetypes / Pathways
  → Circles / Operations / Preparedness
  → Participation / STAR / Trust
  → Publishing / Marketplace / Business / Investment
  → Leadership / Institution Building / Legacy
```

Member Home is the aggregator. It should not own all data; it should display data with institutional source context.

## What Is Currently Implemented

- React app shell, route map, global navigation, pilot scope controls.
- Public and authenticated pages: home, dashboard, applications, timeline/history, languages, study, brain training, membership, onboarding, community directory, preparedness, assessments, library, portal, verification, auth debug.
- Auth, sessions, RBAC, member overview/activity, billing/Stripe foundation.
- Garvey assessment integration endpoints: catalog, archetypes, transfer token, results, result detail, sync diagnostics, growth profile, callbacks.
- Local leadership assessment submit/results/dashboard/analytics.
- Audiobook creation/upload/generation/progress/reflection/share APIs.
- Text Book Organizer ingestion, planning, review, preview, exports, immutable block model.
- Participation engine with activities, points, STAR transactions, verification, reputation, rewards, leaderboards, and feeds.
- Preparedness household profile, inventory, volunteer, and summary APIs.
- Admin operations, analytics, shares, reviews, activity stream, holistic overview.
- Discord bridge health, diagnostics, test messages, regional posts, daily Black economics facts.
- Voice/TTS/STT/chat endpoints and Skill World audio endpoint.
- Deployment/config docs, smoke scripts, and many backend tests.

## What Is Architectural Only or Future

- Characteristics as a member-facing profile.
- Simba community archetypes as distinct from Garvey assessment archetypes.
- Development Pathways as active opt-in workflows.
- Community Circles as functioning groups.
- Marketplace as commerce/exchange institution.
- PocketPT as a complete health institution.
- Investment Platform as compliant capital system.
- Legacy institution workflows.
- Unified notification preferences and member settings.

## Current Member Experience

The strongest current journey is:

```text
Visitor → Sign in/join → Dashboard → Timeline/History → Languages → Library/Study → Assessments → Preparedness → Admin-supported feedback loop
```

A broader conceptual journey already exists in architecture:

```text
Visitor → Member → Knowledge Commons → Assessments → Garvey → Characteristics → Archetypes → Pathways → Circles → Operations → Preparedness → Marketplace → Publishing → Investment → Leadership → Institution Building → Legacy
```

The product should not pretend all stages are live. The pilot should use the first journey while explaining the second as roadmap/vision.

## Developer Philosophy

A developer joining years from now should understand these rules:

1. Start with the Constitution and Operating Philosophy.
2. Use the Architecture Decision Framework before adding features.
3. Identify the owning institution before coding.
4. Preserve Garvey/Simba boundaries.
5. Prefer member agency, consent, and transparent explanations.
6. Do not duplicate systems when an existing institution can own the feature.
7. Treat STAR as recognition, not worth.
8. Hide or label future systems until they are ready.
9. Document integrations and environment dependencies.
10. Keep pilot scope smaller than ecosystem vision.

## Systems That Communicate

- Frontend calls backend APIs through the shared API client.
- Auth feeds dashboard, RBAC, organizer gates, admin gates, billing, member APIs.
- Billing/Stripe feeds subscription status and membership access.
- Assessment Center consumes Garvey assessment APIs.
- Member Dashboard consumes member overview/activity and assessment-related data.
- Audiobook and organizer APIs feed publishing/library workflows.
- Participation/STAR can receive activities from modules and feed summaries/reputation.
- Preparedness writes operational readiness data and can become a participation source.
- Discord bridge can send safe operational/content messages to external channels.
- Admin dashboard consumes overview, members, profiles, shares, reviews, activity, and verification data.

## Where Each Feature Belongs

- **Assessments/scoring/results evidence:** Garvey.
- **Growth interpretation/pathways/recommendations:** Simba.
- **Learning content/books/languages/history:** Knowledge Commons.
- **Book creation/audiobooks/organizer:** Publishing.
- **Membership/subscriptions/checkout/applications:** Business Systems.
- **Projects/volunteers/preparedness:** Community Operations.
- **Points/STAR/reputation/verification:** STAR.
- **Commerce/exchange:** Marketplace.
- **Health/fitness:** PocketPT.
- **Capital/ledger/investments:** Investment Platform.
- **Aggregated daily member view:** Member Home.
- **Internal support/release checks:** Admin / Analytics / Reliability.

## Future Expansions Already Supported by Architecture

- Community Circles and facilitators.
- Volunteer coordination and mutual aid modules.
- STAR verification and reputation-based trust.
- Publishing pipeline from manuscript to audiobook to curriculum.
- Cooperative marketplace and business directory.
- Community investment and ledger system.
- PocketPT wellness integration.
- Discord-based community engagement.
- Legacy/mentorship/institution memory.
- Unified development pathways.

## Duplications and Inconsistencies Found

1. **Legacy/local Leadership Assessment vs Garvey Assessment Center:** Both exist; canonical ownership should be clarified.
2. **Multiple TTS/voice routes:** `/tts`, `/chat/tts`, `/api/voice/tts`, audiobook generation, and Skill World audio should share a documented boundary.
3. **Admin route families:** `/admin/ai/*` and compatibility `/admin/*` overlap.
4. **Pilot docs vs current route map:** Some previously deferred routes are active now, especially study/membership, requiring an explicit pilot decision.
5. **Prototype directories:** v2-ledger, v2-admin, root-level app files, Express admin routes, and fitness components may be useful but are not all connected to the main app.
6. **Navigation vs direct URL access:** Hidden features may still be URL-accessible, so pilot messaging must be deliberate.

## Recommended Pilot Experience

Pilot should showcase:

- Mission-focused home page.
- Account/auth flow.
- Member dashboard.
- Timeline/history.
- Swahili and Yoruba static learning.
- Library and selected study content if verified.
- Assessment Center/Garvey results.
- Preparedness as first Community Operations proof.
- Admin verification center and operations dashboard for staff.

Pilot should hide or clearly mark as roadmap:

- Marketplace.
- Investment/Ledger.
- PocketPT/Fitness.
- Community Circles.
- Full Publishing/Organizer unless guided Builder test.
- STAR rewards marketplace.
- Chat/AI coach.
- Talent/PAGT.

## Recommended Roadmaps

### Phase 2

- Reconcile pilot navigation and route decisions.
- Consolidate assessment ownership around Garvey.
- Add member orientation and privacy/settings foundation.
- Create first Simba Pathway MVP as read-only recommendations.
- Polish preparedness and participation UX.
- Define STAR earning/verification policy.
- Add unified Knowledge Commons taxonomy.
- Create operator runbooks for Stripe, Discord, Garvey, deployment.

### Phase 3

- Launch Community Circles MVP.
- Launch Publishing workflow for guided creators.
- Add community operations modules beyond preparedness.
- Introduce limited marketplace with trusted cohort.
- Build PocketPT as separate privacy-protected institution.
- Begin investment education before any investment transactions.
- Create legacy/mentorship workflows.

## Long-Term Architectural Observations

Simba has the architecture of a serious community institution, not a simple SaaS product. Its strength is a coherent philosophy tying learning, evidence, contribution, trust, economics, health, and legacy together. Its risk is overbreadth: many future institutions are present as prototypes or documents, and without strict scope control the pilot can feel unfinished. The platform should mature by making a small number of journeys excellent while preserving the larger atlas as the long-term map.

## Overall Assessment

Simba is a promising Community Operating System with unusually strong institutional architecture and a meaningful implemented pilot spine. It is not yet ready to expose every concept publicly. It is ready for a controlled pilot if the team freezes scope, validates environment dependencies, clarifies assessment ownership, and communicates honestly about what is live versus planned.
