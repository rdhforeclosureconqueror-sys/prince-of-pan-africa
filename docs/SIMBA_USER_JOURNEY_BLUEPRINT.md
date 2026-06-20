# Simba User Journey Blueprint

_Date: 2026-06-20_

## Purpose

This document describes the complete Simba member experience as a lifelong journey. It is planning-only and does not implement routes, scoring, APIs, permissions, database changes, Garvey changes, Simba changes, STAR changes, or runtime behavior.

## Core Journey

```text
Visitor
  ↓
Member
  ↓
Knowledge Commons
  ↓
Assessments
  ↓
Garvey
  ↓
Characteristics
  ↓
Archetypes
  ↓
Development Pathways
  ↓
Community Circles
  ↓
Community Operations
  ↓
Preparedness
  ↓
Marketplace
  ↓
Publishing
  ↓
Investment
  ↓
Leadership
  ↓
Institution Building
  ↓
Legacy
```

This is not a forced funnel. Members may enter through learning, language, library, preparedness, publishing, health, business, or service. The journey should be understood as an invitation map: each stage creates context for deeper responsibility, but members retain agency.

## Stage Blueprint

### 1. Visitor

- **Current implementation:** Public home route, global navigation, library/language/timeline entry points, sign-in/join flow.
- **Planned future implementation:** Public orientation explaining Simba as a Community Operating System, not just an app.
- **Recommended experience:** Visitor sees mission, sample learning resources, membership invitation, and clear pilot expectations.
- **Decision points:** Join now, explore public learning, read mission/constitution, return later.
- **Optional paths:** Public language lessons, history timeline, library browsing.

### 2. Member

- **Current implementation:** Authenticated user account, dashboard routing, membership/community/builder pages, onboarding endpoints.
- **Planned future implementation:** Guided onboarding that captures goals, consent, privacy preferences, and areas of interest.
- **Recommended experience:** Member understands dignity, agency, privacy, and responsibility before taking assessments or joining operations.
- **Decision points:** Select community membership, builder path, learning focus, operations interest.
- **Optional paths:** Join without assessment, learn first, explore preparedness, apply for builder tools.

### 3. Knowledge Commons

- **Current implementation:** Library, study page, timeline/history, Swahili/Yoruba lessons, daily historical data, brain training.
- **Planned future implementation:** Unified commons with search, collections, learning tracks, progress, citations, audio, and community reading plans.
- **Recommended experience:** Member begins with culturally grounded learning and chooses one or more learning paths.
- **Decision points:** Read, listen, study language, explore history, practice brain training.
- **Optional paths:** Skip to assessment; use language lessons publicly; use library without publishing tools.

### 4. Assessments

- **Current implementation:** Assessment Center routes, local leadership assessment, Garvey assessment catalog/results/archetypes/callbacks.
- **Planned future implementation:** One coherent assessment center powered by Garvey as observation engine.
- **Recommended experience:** Member is told assessments are evidence, not destiny. Results explain strengths, growth edges, and next steps.
- **Decision points:** Take an assessment, review prior results, retake later, decline.
- **Optional paths:** Begin with learning or service before assessment.

### 5. Garvey

- **Current implementation:** Garvey backend integration for catalog, archetypes, transfer tokens, results, callbacks, sync diagnostics, growth profile.
- **Planned future implementation:** Hardened external Garvey contract and read-only evidence stream into Simba.
- **Recommended experience:** Garvey observes and records evidence; it does not assign permanent community identity.
- **Decision points:** Consent to assessment transfer/callback, review results, share with Simba for recommendations.
- **Optional paths:** Member can keep some assessment insights private if future privacy controls allow.

### 6. Characteristics

- **Current implementation:** Architecture framework only; no production characteristic scoring UI.
- **Planned future implementation:** Simba interprets Garvey, learning, participation, and reflection evidence into developable characteristics.
- **Recommended experience:** Member sees growth-oriented language such as “you are currently demonstrating reliability,” never fixed labels.
- **Decision points:** Choose characteristic to strengthen, ask for learning/practice recommendations, hide/share profile.
- **Optional paths:** Characteristics can be bypassed in favor of direct learning or operations.

### 7. Archetypes

- **Current implementation:** Garvey assessment archetypes exist; community archetype specification is architectural.
- **Planned future implementation:** Simba community archetypes represent contribution roles such as organizer, steward, builder, mentor, cultural guardian.
- **Recommended experience:** Member receives possible contribution alignments, with clear wording that roles are flexible and plural.
- **Decision points:** Explore an archetype, reject it, combine roles, revisit later.
- **Optional paths:** Member contributes without adopting an archetype label.

### 8. Development Pathways

- **Current implementation:** Planning document only.
- **Planned future implementation:** Opt-in pathways with learning, practice, contribution, reflection, milestones, and mentor support.
- **Recommended experience:** Member chooses a pathway such as “become a stronger organizer,” then receives books, lessons, service opportunities, and reflection prompts.
- **Decision points:** Select, pause, switch, combine, complete, mentor another member.
- **Optional paths:** Non-linear; a member may lead in one area while learning basics in another.

### 9. Community Circles

- **Current implementation:** Architecture document; community directory prototype exists.
- **Planned future implementation:** Small groups organized around learning, service, locality, mentorship, business, or preparedness.
- **Recommended experience:** Member joins a Circle when ready for cooperative practice, not as a forced progression.
- **Decision points:** Join existing Circle, request facilitator, form a Circle, remain independent.
- **Optional paths:** Time-limited circles, family circles, youth circles, business circles, emergency circles.

### 10. Community Operations

- **Current implementation:** Operations framework and registry; preparedness module; admin operations dashboard; participation APIs.
- **Planned future implementation:** Reusable operations modules for mutual aid, events, projects, volunteer coordination, resource stewardship.
- **Recommended experience:** Member moves from learning to coordinated action through clear roles and humane expectations.
- **Decision points:** Volunteer, verify contribution, join project, decline, request help.
- **Optional paths:** Operations participation can happen before assessments.

### 11. Preparedness

- **Current implementation:** Household profile, inventory, volunteer endpoints and page.
- **Planned future implementation:** Neighborhood readiness, mutual aid, resource maps, emergency roles, training plans.
- **Recommended experience:** Member builds household and community resilience without exposing sensitive details unnecessarily.
- **Decision points:** Complete household profile, add inventory, volunteer, join local preparedness group.
- **Optional paths:** Anonymous learning materials; private household planning only.

### 12. Marketplace

- **Current implementation:** Planned future capability; no primary production marketplace.
- **Planned future implementation:** Cooperative marketplace for local goods, services, mutual aid, publishing, and business collaboration.
- **Recommended experience:** Marketplace should emerge after trust, contribution, and stewardship foundations exist.
- **Decision points:** Offer service, purchase, barter, support mutual aid, form cooperative.
- **Optional paths:** Members can use Simba without commerce.

### 13. Publishing

- **Current implementation:** Library, audiobooks, organizer, exports, share tracking.
- **Planned future implementation:** Full publishing pipeline from manuscript to book, audiobook, study guide, community curriculum.
- **Recommended experience:** Knowledge creators preserve and distribute culturally grounded work with editorial support.
- **Decision points:** Organize manuscript, create audiobook, share privately, publish to commons, monetize later.
- **Optional paths:** Reader-only, narrator, editor, teacher, author.

### 14. Investment

- **Current implementation:** Ledger/v2-ledger prototype and investment architecture concepts; no production investment workflow.
- **Planned future implementation:** Community capital, cooperative investment, real estate platform, transparent governance.
- **Recommended experience:** Investment is introduced only after trust, literacy, compliance, and governance are mature.
- **Decision points:** Learn, qualify, participate, abstain, mentor, steward capital.
- **Optional paths:** Members can build leadership and legacy without investing money.

### 15. Leadership

- **Current implementation:** Leadership assessments, role meters, results dashboard, admin analytics.
- **Planned future implementation:** Leadership as service: mentorship, facilitation, project accountability, institution stewardship.
- **Recommended experience:** Leadership is a responsibility earned through trust and service, not status gamification.
- **Decision points:** Mentor, facilitate Circle, lead operation, steward resource, continue as contributor.
- **Optional paths:** Quiet service without formal leadership title.

### 16. Institution Building

- **Current implementation:** Architecture and operating philosophy; no full institution-builder workflow.
- **Planned future implementation:** Tooling for cooperatives, cultural institutions, schools, mutual aid groups, businesses, publishing houses, preparedness networks.
- **Recommended experience:** Mature members help build durable structures that outlast individual participation.
- **Decision points:** Found, join, govern, document, transition leadership.
- **Optional paths:** Advisory, funding, teaching, operations, technical support.

### 17. Legacy

- **Current implementation:** Constitutional/architecture documents and publishing primitives support the idea.
- **Planned future implementation:** Legacy profiles, knowledge preservation, mentorship lineage, institutional memory, elder roles.
- **Recommended experience:** Member’s learning and service becomes guidance for future generations.
- **Decision points:** Record lessons, mentor successors, publish knowledge, preserve institution history.
- **Optional paths:** Family legacy, Circle legacy, institutional legacy, cultural legacy.

## Non-Linear Progression Rules

1. A member may begin anywhere.
2. Assessment should inform, not gate, contribution.
3. STAR should recognize contribution, not define worth.
4. Marketplace/investment should require extra trust, compliance, and consent.
5. Leadership should remain service-based.
6. Every stage should permit pause, exit, return, and privacy.

## Recommended Pilot Journey

For the first public pilot, use a simplified path:

```text
Visitor → Member → Dashboard → Timeline/Library/Languages → Assessment Center → Preparedness → Reflection/Admin-supported follow-up
```

Keep Community Circles, Marketplace, full Publishing, Investment, PocketPT, and advanced STAR visible only as roadmap concepts unless intentionally included in a guided test.
