# Simba Institution Dependency Map

_Date: 2026-06-20_

## Purpose

This map documents institutional ownership, boundaries, dependencies, and information flow across the Simba ecosystem. It is planning-only and changes no runtime behavior.

## Boundary Principles

1. **Garvey observes; Simba develops.** Garvey owns assessment evidence. Simba may interpret evidence into growth opportunities but must not alter Garvey scoring.
2. **STAR recognizes participation; it does not define human worth.** Rewards are operational signals, not identity.
3. **Member agency and consent govern sensitive data flow.** Assessment, health, preparedness, financial, and community reputation data need explicit boundaries.
4. **Institutions consume outputs without stealing ownership.** A dashboard may display data from multiple institutions without becoming the owner.

## Institution Map

| Institution | Purpose | Responsibilities | Inputs | Outputs | Ownership | Dependencies | Data ownership / boundaries |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Constitution | Durable covenant for mission, dignity, agency, privacy, stewardship. | Define non-negotiable principles. | Community mission, philosophy. | Governing constraints. | Ecosystem governance. | None; highest reference. | Does not own runtime data. |
| Architecture Decision Framework | Prevent feature sprawl and place work correctly. | Review features, assign institution, check ethics/fit. | Proposals, lifecycle stage, risks. | Placement decisions, review checklist. | Architecture governance. | Constitution, Operating Philosophy. | Owns design rationale, not member data. |
| Member Lifecycle | Explain lifelong journey from visitor to legacy. | Journey stages, non-linear progression, agency. | Member goals, stages, ecosystem capabilities. | Journey blueprint and placement. | Member Experience / Simba. | Constitution, Knowledge Commons, Garvey, STAR, Operations. | Should not expose sensitive stage in ways that shame/rank members. |
| Knowledge Commons | Shared learning, cultural memory, library, languages, history. | Curate educational content, reading/listening/study pathways. | Books, lessons, history data, publishing outputs. | Learning resources and progress signals. | Knowledge Commons. | Publishing, Library, Languages, Timeline. | Owns content metadata and learning events; not assessment identity. |
| Garvey | Observation and assessment engine. | Assessments, scoring, archetypes in assessment context, results, callbacks, evidence. | Responses, external assessment callbacks, user identity linkage. | Scores, assessment results, evidence summaries, growth profile. | Garvey. | Auth, Assessment Center, secure callback config. | Owns assessment evidence; Simba must not mutate scores. |
| Simba | Interpretation and development engine. | Characteristics, community archetypes, pathways, recommendations, member growth. | Garvey evidence, learning, participation, member goals, reflections. | Development suggestions, pathways, opportunities. | Simba. | Garvey, Knowledge Commons, STAR, Operations. | Owns interpretations; must explain uncertainty and preserve agency. |
| Member Home | Unified member-facing surface. | Display next steps, metrics, learning, assessment state, operations invitations. | Auth user, dashboard data, assessments, participation, preparedness. | Member experience and calls to action. | Member Experience / Simba. | Auth, Garvey, STAR, Knowledge Commons, Operations. | Displays data; source institutions retain ownership. |
| Characteristics | Developable qualities that support community. | Interpret evidence into growth-oriented characteristics. | Garvey evidence, STAR, learning, reflections. | Characteristic profile and practices. | Simba. | Garvey, Development Pathways. | No fixed labels; must be private by default. |
| Archetypes | Contribution-role alignment. | Map evidence/characteristics to possible community functions. | Garvey assessment archetypes, characteristics, goals. | Suggested roles and contribution options. | Garvey owns assessment archetypes; Simba owns community archetypes. | Garvey, Characteristics, Circles. | Must distinguish assessment output from community role recommendation. |
| Development Pathways | Turn evidence into learning/practice/contribution cycles. | Recommend resources, practices, milestones, reflections. | Characteristics, archetypes, learning history, goals. | Active pathway states and recommendations. | Simba. | Knowledge Commons, Operations, STAR, Member Home. | Member opt-in; no forced advancement. |
| Community Circles | Small group structure for practice and trust. | Group formation, roles, facilitation, peer support. | Member goals, location/interests, archetypes, consent. | Circle membership, activity, support requests. | Community Circles. | Member Systems, Operations, STAR. | Circle participation data should be visible only by consent/role. |
| Community Operations | Coordinate real-world/community work. | Projects, roles, tasks, verification, preparedness modules. | Member participation, Circle needs, community needs. | Activity records, operations status, volunteer requests. | Community Operations. | STAR, Preparedness, Admin, Discord. | Owns operational records; sensitive details minimized. |
| Preparedness | Household and community resilience. | Household profile, inventory, volunteers, readiness summaries. | Household data, inventory items, volunteer skills. | Readiness summaries and volunteer availability. | Preparedness / Community Operations. | Auth, Operations, STAR. | Highly sensitive; private by default and aggregated carefully. |
| Marketplace | Cooperative exchange and local commerce. | Listings, services, mutual aid, commerce flows. | Member/business profiles, trust signals, payments. | Transactions, opportunities, marketplace reputation. | Marketplace / Business Systems. | Billing, STAR, Business Systems, Compliance. | Commerce data separated from assessment data unless consented. |
| Publishing | Preserve and distribute knowledge. | Books, audiobooks, organizer, exports, creator workflow. | Manuscripts, audio, metadata, reflections. | Published resources, audiobooks, share links. | Publishing. | Knowledge Commons, Voice, Billing (future), Marketplace (future). | Creator rights and content ownership require policy. |
| PocketPT | Health and fitness institution. | Fitness, nutrition, recovery, wellness education. | Health goals, sessions, wellness data. | Plans, progress, coaching. | PocketPT / Health. | Member Home, privacy controls, voice/AI optionally. | Health data must remain isolated and consent-protected. |
| Investment Platform | Community capital and investment opportunities. | Ledger, cooperative investment, capital education, governance. | Financial education, eligibility, trust/compliance data. | Investment opportunities, ledger records, reports. | Investment Platform. | Business Systems, Marketplace, Legal/Compliance, STAR. | Financial data has strict compliance and privacy boundaries. |
| STAR | Participation recognition. | Activities, points, STAR transactions, rewards, reputation, verification. | Activity events, verification, guest/member identity. | STAR balance/events, reputation summaries, rewards. | STAR / Participation. | Operations, Member Home, Discord, Admin. | Must not become social-credit identity; explain earning rules. |
| Business Systems | Membership, billing, subscriptions, applications, business workflows. | Stripe checkout/portal/webhooks, tiers, applications, entitlements. | User, subscriptions, payments, applications. | Access status, membership tier, business opportunities. | Business Systems. | Auth, Stripe, RBAC, Marketplace. | Payment data separated from assessment and health data. |
| Assessment Center | Member-facing access to assessment experiences. | Catalog display, launch, results UI, result detail. | Garvey catalog/results, auth user. | Assessment UX and navigation. | Assessment Center UI; Garvey data. | Garvey, Member Home. | Does not own scores; displays Garvey outputs. |
| Admin / Analytics | Internal operational visibility. | Overview, members, profiles, shares, reviews, activity, verification. | Aggregated system data. | Admin dashboards, support insight, readiness checks. | Admin Operations. | Auth/RBAC, all modules. | Must apply least privilege and privacy minimization. |
| Discord / Notifications | Extend operations/community updates outside app. | Health checks, daily facts, regional prompts, test messages, alerts. | Discord config, content facts, operation events. | Channel messages and diagnostics. | Community Operations / Notifications. | Discord, STAR, Admin. | Avoid sending sensitive member data to third-party channels. |
| Legacy | Preserve knowledge, mentorship, institutional memory. | Elders, mentorship lineage, published lessons, continuity. | Member contributions, publications, leadership history. | Legacy records, teachings, institutional handoff. | Legacy Institution. | Publishing, Leadership, Circles, Knowledge Commons. | Consent and dignity around life stories and lineage. |

## Information Flow

```text
Visitor / Member
  → Auth / Membership
  → Member Home
  → Knowledge Commons learning events
  → Assessment Center
  → Garvey evidence/results
  → Simba interpretations
  → Characteristics / Archetypes / Pathways
  → Community Circles and Operations
  → Preparedness / Projects / Participation
  → STAR recognition and reputation summaries
  → Marketplace / Publishing / Business / Investment when mature
  → Leadership / Institution Building / Legacy
```

## Ownership-Preserving Integration Rules

- Member Home may aggregate data but must show source context.
- Simba may consume Garvey results but must not recalculate or overwrite Garvey scores.
- STAR may accept activity events from Operations, Knowledge Commons, or Preparedness but should not expose sensitive details unnecessarily.
- Discord should receive only safe, intentional, non-sensitive notifications.
- Investment and health data must remain institutionally isolated until compliance/privacy designs are complete.

## Immediate Dependency Risks

1. Assessment Center depends on clarity between legacy Leadership Assessment and Garvey.
2. Preparedness depends on privacy policy and clear member expectations.
3. Billing depends on live Stripe configuration and entitlement synchronization.
4. Discord depends on external token/channel configuration.
5. Voice/audiobook systems depend on external providers and quota controls.
