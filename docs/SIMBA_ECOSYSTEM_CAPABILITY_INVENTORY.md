# Simba Ecosystem Capability Inventory

_Date: 2026-06-20_

## Purpose

This repository-wide inventory documents what currently exists in the Simba ecosystem before additional pilot work. It is documentation-only and does not change production code, runtime behavior, APIs, database tables, authentication, Garvey logic, Simba logic, STAR behavior, or permissions.

## Inventory Method

Sources reviewed include the React route map, global navigation, backend FastAPI routers, SQLAlchemy models, service modules, tests, public assets, and existing architecture/planning documents. Status language reflects repository evidence, not live-production verification.

## Status Key

- **Implemented**: Has active route/API/model/service and tests or visible UI.
- **Functional pilot surface**: Usable enough for controlled pilot, often with polish gaps.
- **Prototype**: Exists as UI, API, data, or plan but is not fully integrated.
- **Architecture only**: Documented institution or blueprint with little/no runtime implementation.
- **Deferred/hidden**: Route or capability exists but is intentionally not in pilot navigation.

## Capability Inventory

| Capability | Purpose | Current status | Owner institution | Dependencies | Related systems | Future expansion opportunities |
| --- | --- | --- | --- | --- | --- | --- |
| Community Constitution | Highest-level ethical and design covenant for the ecosystem. | Architecture only; comprehensive governing document exists. | Constitution | Operating Philosophy, Architecture Decision Framework | All institutions | Formal design review checklist; release governance. |
| Architecture Decision Framework | Places new work in the right institution and prevents feature sprawl. | Architecture only; documented. | Architecture Governance | Constitution, Ecosystem Architecture | Product planning, engineering review | Required proposal template before implementation. |
| Member Lifecycle | Defines lifelong progression from visitor to legacy builder. | Architecture only; documented. | Member Lifecycle | Constitution, Simba Architecture | Member Home, assessments, STAR, circles | Lifecycle-aware recommendations and consent controls. |
| Landing pages / Visitor experience | Introduce public mission and routes visitors toward membership and learning. | Functional pilot surface via home page and app shell. | Member Experience | React app, global nav, auth modal flow | Membership, Library, Timeline | Public orientation, clearer pilot CTA, content hierarchy. |
| Authentication | Account creation, login, logout, current-user session, debug route. | Implemented and tested; environment-sensitive. | Member Systems / Security | Users, sessions, RBAC, cookies | Dashboard, organizer, billing, admin | Hardening docs, admin support tooling, session observability. |
| RBAC / permissions | Gate admin/member/organizer capabilities. | Implemented in backend and frontend helpers with tests. | Security / Business Systems | Roles, permissions, user_roles | Dashboard, organizer, admin | Role management UI; least-privilege audit. |
| Membership tiers | Community and Builder membership pages and onboarding. | Functional/prototype; routes exist, billing dependency remains. | Member Systems / Business Systems | Auth, billing, Stripe, onboarding APIs | Dashboard, organizer access | Membership copy refinement; automated entitlement reconciliation. |
| Billing | Checkout, portal, status, webhook, config endpoints. | Implemented foundation; live readiness depends on Stripe config. | Business Systems | Stripe env vars, subscriptions, webhook signing | Membership, access control | Live checkout launch, customer portal polish, entitlement audit. |
| Stripe integration | Paid subscription lifecycle and webhook event capture. | Functional but needs live-production validation. | Business Systems | Stripe API, webhook events, subscriptions | Billing, RBAC | Phase 3 live checkout plan completion. |
| Member Home / Dashboard | Unified member landing after login with metrics and next steps. | Functional pilot surface. | Member Home / Simba | Auth, member overview, participation, assessments | Admin dashboard, Garvey, STAR | Personal pathway dashboard, lifecycle cards, recommendations. |
| Admin Operations Dashboard | Admin view of overview, profiles, members, activity stream, shares, reviews. | Functional internal/admin surface. | Community Operations / Admin | Admin APIs, authz, activity data | Analytics, verification, content shares | Operational runbooks; clearer production support workflows. |
| System Verification Center | Release and environment checks. | Implemented admin-facing route/API. | Admin / Reliability | Backend system routes, verification engine | Pilot smoke tests | Go/no-go dashboard, historical check storage. |
| Knowledge Commons | Mission-level learning commons and architecture for content. | Architecture + implemented slices through library/timeline/languages. | Knowledge Commons | Library, public data, publishing | Member journey, Development Pathways | Unified commons taxonomy and search. |
| Library | Book catalog, public reading entry points, decolonize redirect. | Functional pilot surface. | Knowledge Commons / Publishing | Static book covers/data, study page, audiobooks | Portal, organizer, shares | Persistent library model, collections, recommendations. |
| Study Page | Reading/study interface for selected books. | Implemented route; not listed in older pilot lock but currently active. | Knowledge Commons | Library data, frontend state | Audiobooks, reflections | Study progress persistence, annotations. |
| Audiobooks | Create/upload/list audiobooks, chapters, generation, progress, reflections, shares. | Implemented backend; frontend integration partial. | Publishing / Knowledge Commons | Auth, audio assets, TTS/voice, storage, DB | Library, organizer, share tracking | Creator workflow, moderation, quota UX, public listening pages. |
| Text Book Organizer | Ingest text, immutable blocks, propose/review/export plans. | Implemented but feature-flagged and permission-gated. | Publishing | Builder membership, organizer APIs, immutable blocks | Library, audiobooks | Editorial workflow and publishing pipeline. |
| Publishing | Author/book/audiobook infrastructure and organizer exports. | Prototype/architecture; pieces exist. | Publishing | Library, audiobooks, organizer | Knowledge Commons, marketplace | Publishing house workflow, ISBN/metadata, contributor royalties. |
| Swahili | Public static lesson and language hub link. | Functional static learning surface. | Knowledge Commons / Language Learning | Public lesson files, TTS lesson script | Languages hub, global nav | Progress tracking, speech practice, more modules. |
| Yoruba | Public static lesson and language hub link. | Functional static learning surface. | Knowledge Commons / Language Learning | Public lesson files, TTS lesson script | Languages hub, global nav | Progress tracking, speech practice, more modules. |
| Language hub | React page aggregating language resources. | Functional pilot surface. | Knowledge Commons | Static lesson files | Swahili, Yoruba | Unified lesson engine, audio, quizzes. |
| Brain Training | Games and UI for cognitive practice. | Implemented route and game modules; pilot polish unknown. | Learning Systems | Frontend games/styles | Member Home, STAR | Persistence, adaptive difficulty, accessibility. |
| Timeline / History | Historical learning route using timeline data. | Functional pilot surface. | Knowledge Commons | Static timeline data, historical spotlights | Library, daily facts | Curated pathways, source citations, quizzes. |
| Daily Historical Spotlights | Historical fact data and validation script. | Implemented data/tooling. | Knowledge Commons | Data file, validation script | Timeline, Discord facts | Daily content engine and notifications. |
| Assessments Center | Assessment landing, center, and result routes. | Implemented frontend integrated with Garvey catalog/results. | Assessment Center / Garvey | Auth, Garvey endpoints, frontend pages | Member Home, Characteristics | UX polish, result explanations, retake flows. |
| Leadership Assessment | Local submit/results/dashboard/analytics endpoints and UI components. | Implemented legacy/local assessment path; partly superseded by Garvey center. | Garvey / Assessment Center | Leadership questions/scoring, DB | Archetypes, member dashboard | Consolidate with Garvey catalog; reduce duplicate routes. |
| Garvey integration | Assessment catalog, archetypes, transfer token, results, callbacks, growth profile. | Implemented backend integration boundary. | Garvey | Auth, HMAC/callback config, LeadershipAssessment, GarveySyncEvent | Assessment Center, Member Home, Simba | External Garvey production contract documentation. |
| Characteristics | Developmental traits interpreted from evidence. | Architecture only; comprehensive framework exists. | Simba | Garvey evidence, participation, learning history | Archetypes, pathways | First read-only profile and member explanations. |
| Archetypes | Community contribution roles. | Architecture + Garvey endpoint exposes assessment archetypes. | Garvey for assessment archetypes; Simba for community archetypes | Assessment evidence, characteristic framework | Pathways, circles | Clear separation between Garvey archetypes and Simba community archetypes. |
| Development Pathways | Growth cycles from evidence to learning/practice/contribution. | Architecture only. | Simba | Characteristics, archetypes, learning history, STAR | Member Home, Community Operations | MVP pathway cards and opt-in goals. |
| Community Circles | Grouping model for practice, trust, and local work. | Architecture only; community circle engine doc exists. | Community Circles | Member lifecycle, archetypes, operations | Community Directory, Operations | Circle creation, roles, facilitator tools. |
| Community Directory | Member/community directory page. | Prototype/frontend surface. | Community Circles / Member Systems | Auth/member data (limited) | Onboarding, circles | Privacy controls and real member search. |
| Community Operations | Registry and framework for operational modules. | Architecture + frontend registry; preparedness is first module. | Community Operations | Participation, preparedness, admin | Member Home, STAR | Reusable operation module template. |
| Preparedness | Household profile, inventory, volunteer readiness and summary. | Implemented API and frontend page; good pilot candidate with polish. | Community Operations / Preparedness | Auth, preparedness models | Community Operations, STAR | Neighborhood readiness maps, mutual aid workflows. |
| Participation Engine | Activities, points, STAR, reputation, verification, rewards, leaderboards, feed. | Implemented backend; UI integration limited. | STAR / Community Operations | Activity models, auth, Discord bridge | Member Home, Preparedness, Admin | Consent-aware contribution feed and verifier UX. |
| STAR | Reward transactions for participation. | Implemented data/API foundation; pilot UX not complete. | STAR | Participation activities, verification | Member Dashboard, rewards | Clear earning rules, anti-gaming review, redemption policy. |
| Marketplace | Future local commerce/cooperative exchange. | Architecture only/planned; no primary route found. | Marketplace / Business Systems | Membership, business systems, STAR, payments | Investment, Publishing | Vendor profiles, mutual-aid exchange, cooperative listings. |
| Business Systems | Membership, billing, applications, business assessment concepts. | Mixed: billing/applications implemented; broader business architecture planned. | Business Systems | Stripe, member data, Garvey business evidence | Marketplace, Investment | Business directory and entrepreneur pathways. |
| Applications | Application cards/page for ecosystem opportunities. | Prototype/frontend surface. | Business Systems / Member Systems | Static applications data | Membership, onboarding | Real application workflow and admin review. |
| PocketPT / Fitness | Health/fitness pages and components. | Prototype/deferred for pilot. | PocketPT / Health | Fitness components, voice/AI utilities | Preparedness, Member Home | Separate health institution with privacy boundary. |
| Investment Platform / Ledger | STAR/ledger V2 components and ledger pages. | Prototype/deferred; no production investment workflow. | Investment Platform | v2-ledger UI, STAR concepts | Marketplace, Business Systems | Community capital, cooperative investment, governance. |
| PAGA/PAGT talent page | Pan-Africa's Got Talent concept. | Deferred/prototype route. | Cultural / Marketplace future | Frontend page only | Publishing, Marketplace | Creator showcase after pilot. |
| Voice / AI Voice | TTS/STT, chat voice, AI voice services, Skill World audio. | Implemented endpoints; external provider/env dependent. | Learning Systems / Knowledge Commons | OpenAI/voice env, static audio files | Chat, languages, audiobooks | Unified voice service contract and quotas. |
| Chat | Chat message, TTS, voice endpoints. | Implemented backend; frontend coupling limited. | Learning Systems / Assistant | Voice/OpenAI utilities | PocketPT, learning | Coach UX after safety and privacy review. |
| Skill World | Audio endpoint and tests for adaptive learning concept. | Prototype/API slice. | Learning Systems | Voice/TTS, tests | Adaptive learning | Full Skill World UI and progress tracking. |
| Discord bridge | Health/diagnostics/test messages, regional posts, daily Black economics facts. | Implemented admin/API bridge; live depends on Discord config. | Community Operations / Notifications | Discord env, black economics data | Participation, daily facts | Event reminders, verification alerts, Circle channels. |
| Notifications | Toasts, notification bot component, Discord messages. | Prototype/mixed; no unified notification service. | Notifications / Community Operations | UI components, Discord bridge | STAR, admin, operations | Central notification preferences and delivery audit. |
| Analytics | Admin overview, roles analytics, activity stream, shares. | Implemented internal analytics endpoints; fragmented. | Admin / Analytics | Assessment data, content shares, activity logs | Admin dashboard, verification | Single analytics model and privacy review. |
| Content share tracking | Share creation/click tracking for audiobooks/content. | Implemented. | Publishing / Analytics | ContentShare model, frontend click tracker | Library, admin shares | Attribution funnel and privacy disclosure. |
| Settings | Auth debug and config surfaces; no full member settings. | Prototype/partial. | Member Systems | Auth, env config | Privacy, notifications | Member preferences, data export, notification settings. |
| Navigation | Global nav and pilot scope control. | Implemented, intentionally constrained. | Member Experience | React routes, pilotScope | All user-facing modules | Role-aware information architecture. |
| Environment/deployment | Render config, env examples, audits, smoke tests. | Implemented documentation/tooling. | Reliability | Backend/frontend configs | System verification | Deployment runbook consolidation. |
| Tests | Backend pytest suite and frontend build/audit scripts. | Strong coverage for many backend contracts. | Reliability | Pytest, npm, scripts | Auth, billing, Garvey, audiobook, participation | Add end-to-end browser smoke tests. |

## Duplicate, Overlapping, or Disconnected Areas

- **Assessment duplication:** Local Leadership Assessment routes and Garvey assessment routes overlap. Recommendation: keep Garvey as the assessment source of truth and treat local leadership endpoints as legacy/compatibility or migrate deliberately.
- **Admin duplication:** `/admin/ai/*` and legacy `/admin/*` compatibility routes serve similar admin data. Recommendation: document canonical admin APIs and retain compatibility only where required.
- **Voice duplication:** `/tts`, `/chat/tts`, `/api/voice/tts`, and audiobook generation all touch speech. Recommendation: define one voice service boundary with module-specific adapters.
- **Page duplication:** Root-level `App.jsx` and `MufasaSessionLauncher.jsx` coexist with `src/App.jsx`; confirm whether root files are legacy scaffolds.
- **Deferred route mismatch:** Earlier pilot lock listed `/study` and `/membership` as deferred, while current route map exposes them. Recommendation: update pilot scope decision explicitly before launch.
- **Prototype islands:** v2-ledger, v2-admin, fitness/PocketPT, Pagt, Express admin route files, and some utility components appear disconnected from the main pilot journey.

## Overall Inventory Conclusion

The repository already contains a broad Community Operating System foundation: membership, authentication, dashboards, learning content, library/publishing primitives, Garvey assessment integration, participation/STAR data models, preparedness operations, billing, admin tools, Discord, and deployment verification. The strongest implemented pilot-ready spine is visitor → auth/member → dashboard → learning/library/languages/timeline → assessment → preparedness/admin verification. The largest gap is not imagination or architecture; it is consolidation, visibility control, UX polish, and clear canonical ownership boundaries.
