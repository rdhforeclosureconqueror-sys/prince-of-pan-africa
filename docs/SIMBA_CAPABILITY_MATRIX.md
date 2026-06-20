# Simba Capability Matrix

_Date: 2026-06-20_

| Capability | Institution | Current Status | Pilot Status | Dependencies | User Facing | Admin Facing | Production Ready | Future Expansion | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Constitution | Constitution | Documented | Reference | None | No | No | Yes as docs | Governance workflow | High |
| Architecture Decision Framework | Architecture Governance | Documented | Reference | Constitution | No | No | Yes as docs | Proposal templates | High |
| Member Lifecycle | Member Lifecycle | Documented | Reference | Constitution, Simba | No | No | Yes as docs | Lifecycle-aware UX | High |
| Landing/Home | Member Experience | Implemented | Include | React app, nav | Yes | No | Partial | Orientation | High |
| Authentication | Security | Implemented/tested | Include | Users, sessions, cookies | Yes | Yes | Partial | MFA/support tools | Critical |
| RBAC | Security | Implemented/tested | Include | Roles, permissions | Indirect | Yes | Partial | Role admin UI | Critical |
| Membership pages | Business Systems | Implemented/prototype | Include cautiously | Auth, billing | Yes | No | Partial | Tier lifecycle | High |
| Billing | Business Systems | Implemented foundation | Include if env validated | Stripe, subscriptions | Yes | Yes | Partial | Live portal automation | Critical |
| Stripe | Business Systems | Integrated | Validate before pilot | Stripe env/webhook | Indirect | Yes | Partial | Full entitlement sync | Critical |
| Member Dashboard | Member Home | Implemented | Include | Auth, member APIs | Yes | No | Partial | Pathway dashboard | Critical |
| Admin Operations | Admin | Implemented | Include for operators | RBAC, admin APIs | No | Yes | Partial | Runbooks, audit logs | High |
| System Verification | Reliability | Implemented | Include | System APIs | No | Yes | Yes/Partial | Historical checks | Critical |
| Knowledge Commons | Knowledge Commons | Partial | Present as learning hub | Library, timeline, languages | Yes | No | No | Unified search/taxonomy | High |
| Library | Knowledge Commons | Implemented | Include | Static assets, app routes | Yes | Indirect | Partial | Persistent collections | High |
| Study Page | Knowledge Commons | Implemented | Decide/include cautiously | Library data | Yes | No | No | Progress/notes | Medium |
| Audiobooks | Publishing | Backend implemented | Guided test only | Auth, TTS, DB, storage | Partial | Yes | No | Creator workflow | Medium |
| Text Book Organizer | Publishing | Feature-flagged/gated | Hide unless Builder test | RBAC, organizer APIs | Yes gated | Yes | No | Editorial pipeline | Medium |
| Publishing | Publishing | Prototype | Roadmap only | Library, audiobooks | Partial | Partial | No | Publishing house | Medium |
| Swahili | Language Learning | Static implemented | Include | Public files | Yes | No | Partial | Progress/speech | High |
| Yoruba | Language Learning | Static implemented | Include | Public files | Yes | No | Partial | Progress/speech | High |
| Language Hub | Knowledge Commons | Implemented | Include | Static lessons | Yes | No | Partial | Lesson engine | High |
| Brain Training | Learning Systems | Implemented/prototype | Optional/secondary | Frontend games | Yes | No | No | Adaptive engine | Low |
| Timeline/History | Knowledge Commons | Implemented | Include | Static data | Yes | No | Partial | Curated tracks | High |
| Daily Historical Spotlights | Knowledge Commons | Data/tooling | Optional | Data validation | Potential | Potential | Partial | Daily notifications | Medium |
| Assessment Center | Assessment Center | Implemented | Include | Auth, Garvey | Yes | No | Partial | UX/result polish | Critical |
| Leadership Assessment | Garvey/Legacy | Implemented | Compatibility only | Scoring service | Yes | Yes analytics | No | Consolidate | Medium |
| Garvey Integration | Garvey | Implemented | Include/validate | Auth, callbacks | Yes via UI | Yes diagnostics | Partial | Contract docs | Critical |
| Characteristics | Simba | Architecture only | Roadmap only | Garvey evidence | Future | Future | No | Profile cards | Medium |
| Archetypes | Garvey/Simba | Mixed | Use cautiously | Assessments, framework | Yes partial | No | No | Community roles | Medium |
| Development Pathways | Simba | Architecture only | Roadmap only | Characteristics, learning | Future | Future | No | Opt-in pathways | High Phase 2 |
| Community Circles | Community Circles | Architecture/prototype directory | Roadmap only | Member data, consent | Future/partial | Future | No | Circle engine | Medium |
| Community Directory | Community Circles | Prototype | Hide/limited | Auth/data | Yes | No | No | Privacy-aware search | Low |
| Community Operations | Operations | Framework + modules | Include via preparedness | Participation, admin | Yes partial | Yes | Partial | Project modules | High |
| Preparedness | Preparedness | Implemented | Include guided | Auth, models | Yes | Potential | Partial | Neighborhood readiness | High |
| Participation Engine | STAR/Operations | Backend implemented | Internal/limited | Activity models | Partial | Yes | No | Contribution feed | Medium |
| STAR | STAR | Data/API foundation | Internal/limited | Participation | Partial | Yes | No | Reward marketplace | Medium |
| Marketplace | Marketplace | Planned | Hide | Business, payments | No | No | No | Cooperative commerce | Later |
| Business Systems | Business Systems | Partial | Include essentials | Billing, apps | Yes partial | Yes | No | Business directory | Medium |
| Applications | Business Systems | Prototype | Optional/limited | Static data | Yes | Potential | No | Review workflow | Low |
| PocketPT/Fitness | PocketPT | Prototype/deferred | Hide | Health privacy | Yes route deferred | No | No | Health institution | Later |
| Investment/Ledger | Investment Platform | Prototype/deferred | Hide | STAR/business/compliance | Yes route deferred | Potential | No | Community capital | Later |
| Pagt/Talent | Cultural Marketplace | Prototype/deferred | Hide | Frontend page | Yes route deferred | No | No | Creator showcase | Later |
| Voice/AI Voice | Learning/Voice | Implemented endpoints | Limited | External providers | Partial | Diagnostics/tests | No | Unified voice layer | Medium |
| Chat | Assistant/Learning | Backend implemented | Hide/experimental | Voice/OpenAI | Partial | No | No | Guided coach | Later |
| Skill World | Learning Systems | API slice | Hide/experimental | Voice | Partial | No | No | Adaptive learning | Later |
| Discord Bridge | Notifications/Ops | Implemented | Admin-only validate | Discord env | Indirect | Yes | Partial | Circle/event alerts | Medium |
| Notifications | Notifications | Fragmented | Minimal | Toasts, Discord | Partial | Partial | No | Preferences | Medium |
| Analytics | Admin/Analytics | Implemented fragments | Include admin | Data modules | No | Yes | Partial | Privacy-aware metrics | High |
| Content Sharing | Publishing/Analytics | Implemented | Include cautiously | ContentShare, click tracker | Yes | Yes | Partial | Funnel analytics | Medium |
| Settings | Member Systems | Partial/debug | Not pilot core | Auth/config | Partial | Debug | No | Preferences/privacy | High Phase 2 |
| Navigation | Member Experience | Implemented | Include/freeze | Routes, pilotScope | Yes | Indirect | Partial | Role-based IA | Critical |
| Deployment/Env | Reliability | Documented/tooling | Include | Render/env/test scripts | No | Yes | Partial | Release automation | Critical |
