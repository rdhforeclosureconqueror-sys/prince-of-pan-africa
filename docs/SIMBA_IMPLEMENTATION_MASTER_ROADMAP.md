# Simba Implementation Master Roadmap

_Date: 2026-06-20_

## Planning-Only Status

This document is the execution roadmap for the Simba ecosystem. It translates the completed architectural planning set into implementation phases, sequencing guidance, readiness criteria, and long-term release philosophy.

This document does **not** implement production behavior, routes, APIs, database changes, migrations, permissions, Garvey logic, Simba runtime logic, STAR behavior, Marketplace behavior, Investment behavior, or any user-facing feature. It is documentation only.

---

## 1. Purpose

The roadmap answers one practical question:

> What do we build next, in what order, and why?

It is not a replacement for the architecture documents. It is the implementation guide that future work should consult before beginning any major Simba feature. The roadmap organizes development by dependency, member value, institutional value, pilot readiness, and long-term sustainability.

---

## 2. Source Architecture References

Future implementation should keep this roadmap aligned with the planning documents below rather than rewriting them here:

| Reference | Role in this roadmap |
| --- | --- |
| `SIMBA_COMMUNITY_CONSTITUTION.md` | Highest governing reference for dignity, agency, consent, mission, and institutional purpose. |
| `SIMBA_OPERATING_PHILOSOPHY.md` | North star for member development, community usefulness, and the Garvey/Simba boundary. |
| `SIMBA_ECOSYSTEM_ARCHITECTURE.md` | Master map of institutions and system boundaries. |
| `SIMBA_ARCHITECTURE_DECISION_FRAMEWORK.md` | Required feature review process before implementation begins. |
| `MEMBER_LIFECYCLE_ARCHITECTURE.md` | Guides where features belong in the lifelong member journey. |
| `SIMBA_KNOWLEDGE_COMMONS_ARCHITECTURE.md` | Defines learning, reflection, study, teach-back, mentorship, and knowledge preservation. |
| `community-characteristics-framework.md` or related characteristic planning | Guides future characteristic interpretation without reducing members to scores. |
| `community-archetype-specification.md` | Defines community archetype interpretation and its boundary from Garvey assessment output. |
| `development-pathways-architecture.md` or related pathway planning | Guides how evidence becomes opt-in learning, practice, and contribution pathways. |
| `COMMUNITY_CIRCLE_ENGINE.md` | Defines Circle formation, facilitation, roles, trust-building, and support. |
| `COMMUNITY_OPERATIONS_FRAMEWORK.md` | Defines projects, operations, preparedness, volunteer coordination, and community work. |
| Preparedness architecture and readiness docs | Provide the first operational proof-of-concept for real-world resilience. |
| `SIMBA_ECOSYSTEM_ATLAS.md` | Explains current and future institutional surfaces across the ecosystem. |
| `SIMBA_ECOSYSTEM_CAPABILITY_INVENTORY.md` | Identifies existing capabilities, prototypes, gaps, and ownership boundaries. |
| `SIMBA_CAPABILITY_MATRIX.md` | Compares capability maturity, readiness, dependencies, and institutional ownership. |
| `SIMBA_INSTITUTION_DEPENDENCY_MAP.md` | Establishes build order, upstream/downstream dependencies, and risk boundaries. |
| `SIMBA_PILOT_READINESS_REPORT.md` | Establishes current launch readiness and pilot-safe vs future capabilities. |
| `SIMBA_USER_JOURNEY_BLUEPRINT.md` | Defines the full member journey from visitor to legacy. |
| `SIMBA_INSTITUTION_STEWARDSHIP_ARCHITECTURE.md` | Guides institutional health, maintenance, stewardship, and sustainability. |
| `SIMBA_DIGITAL_CIVILIZATION_REFERENCE_MODEL.md` | Frames Simba as cooperating institutions rather than accumulated features. |

If a planned feature conflicts with these documents, pause implementation and run the Architecture Decision Framework before building.

---

## 3. Overall Implementation Strategy

### 3.1 Build from trust outward

Simba should first stabilize the experience members touch immediately: orientation, authentication, dashboard, assessment access, learning surfaces, preparedness pilot, and operator visibility. Only after trust is established should Simba expose more complex systems such as Circles, Marketplace, Investment, or Leadership pipelines.

### 3.2 Convert architecture into institutions gradually

The repository already contains a strong institutional blueprint. Implementation should avoid creating isolated feature islands. Every shipped capability should strengthen an institution:

1. Member Experience
2. Knowledge Commons
3. Garvey Assessment Integration
4. Community Characteristics / Archetypes / Pathways
5. Community Circles
6. Community Operations and Preparedness
7. STAR participation recognition
8. Marketplace and Business Systems
9. Publishing and Legacy
10. Investment and Ownership
11. Stewardship and Governance

### 3.3 Prefer pilot coherence over feature breadth

The pilot should feel small, honest, and reliable. A limited guided journey is better than a broad interface full of unfinished promises. Hide or soften future-facing systems until their privacy, consent, operational support, and institutional boundaries are ready.

### 3.4 Use the member lifecycle as the sequencing spine

Build in the order members naturally need support:

```text
Visitor clarity
  → Member onboarding
  → Learning and assessment
  → Interpretation and reflection
  → Pathway recommendations
  → Small-group trust
  → Community work
  → Recognition
  → Economic participation
  → Ownership
  → Leadership
  → Legacy
```

### 3.5 Preserve boundaries between institutions

Garvey observes. Simba interprets and develops. STAR recognizes participation. Community Operations coordinates work. Marketplace circulates opportunity. Investment handles ownership. Publishing preserves knowledge. These boundaries should not collapse for convenience.

---

## 4. Recommended Sequencing Summary

| Sequence | Build focus | Why now |
| --- | --- | --- |
| 1 | Pilot stabilization | Public trust depends on reliable, truthful, low-friction basics. |
| 2 | Community Operations | Preparedness and projects create immediate community value beyond content consumption. |
| 3 | Community Circles | Circles require stable member identity, onboarding, and operational support. |
| 4 | Knowledge Commons expansion | Learning pathways become more meaningful once members can connect study to Circles and service. |
| 5 | Marketplace integration | Commerce should wait until trust, identity, operations, and business boundaries are clearer. |
| 6 | Investment platform | Ownership requires mature business systems, compliance, trust, and education. |
| 7 | Leadership and legacy | Leadership pipelines should emerge from proven participation, mentorship, and stewardship patterns. |

---

## 5. Phase-by-Phase Roadmap

## Phase 1 – Pilot Stabilization

### Objective

Make the current pilot coherent, reliable, honest, and supportable for a guided cohort.

### Build next

- Public landing and CTA polish.
- Pilot onboarding path and expectation copy.
- Authentication/session smoke-test runbook.
- Member dashboard refinement around current, not future, capabilities.
- Assessment Center polish: catalog, empty states, result navigation, Garvey callback expectations.
- Knowledge Commons MVP framing: Library, Timeline/History, Languages, and selected learning surfaces.
- Preparedness MVP positioning as limited guided pilot capability.
- Admin/operator dashboard refinement for launch monitoring.
- Voice/copy improvements to ensure mission, dignity, and agency are clear.
- Documentation cleanup: canonical route list, operator runbook, feature flag list, and pilot support checklist.
- Bug fixes and UX consistency across pilot-critical routes.

### Dependencies

- Stable auth and membership state.
- Known Garvey integration contract and environment configuration.
- Clear pilot feature flags and hidden-future-feature plan.
- Admin ability to monitor signups, assessments, and readiness checks.

### Success criteria

- A pilot member can understand what Simba is, join/sign in, reach the dashboard, access learning, launch or review assessments, and understand what is currently available.
- Operators can run pre-launch smoke checks and respond to pilot issues.
- Future systems are not over-promised in the UI.
- Documentation identifies what is pilot-ready, prototype-only, hidden, or future.

---

## Phase 2 – Community Operations

### Objective

Turn Simba from a learning portal into a coordinated community action platform through preparedness, volunteer coordination, and project operations.

### Build next

- Preparedness Command Center for household/community readiness summaries.
- Volunteer coordination: roles, availability, skills, and consent-aware contact workflow.
- Community project records: needs, tasks, owners, status, and outcomes.
- Operations dashboard for admins/stewards.
- Project participation verification path, integrated carefully with STAR later.
- Incident/event readiness templates for drills, mutual aid, and local response.
- Operator runbooks for project creation, volunteer outreach, and privacy handling.

### Dependencies

- Phase 1 stable member identity and admin operations.
- Privacy and consent rules for household, preparedness, and volunteer data.
- Clear ownership by Community Operations, not Member Dashboard or STAR.
- Initial STAR event vocabulary if recognition will be recorded.

### Success criteria

- A steward can create and manage a small community project.
- Members can volunteer or respond to needs without exposing sensitive data unnecessarily.
- Preparedness data remains private by default and is aggregated only where appropriate.
- The platform demonstrates real-world value beyond content consumption.

---

## Phase 3 – Community Circles

### Objective

Create small-group structures where members practice trust, study, accountability, service, and mutual support.

### Build next

- Circle creation workflow.
- Circle invitation and consent model.
- Facilitator tools: agenda, check-ins, notes, commitments, and escalation guidance.
- Circle dashboard for members and facilitators.
- Circle-to-project connection so Circles can serve Community Operations.
- Circle study mode connected to Knowledge Commons resources.
- Basic health indicators for participation, not ranking.

### Dependencies

- Stable member accounts and onboarding.
- Clear privacy rules for group membership, notes, and commitments.
- Community Operations path for Circles to take meaningful action.
- Knowledge Commons resources suitable for group study.
- Facilitator training and manual support process.

### Success criteria

- A steward can form a pilot Circle and invite members.
- Facilitators have enough tools to run recurring sessions.
- Members understand Circle expectations and can opt in or out.
- Circle activity strengthens learning and service rather than becoming another chat surface.

---

## Phase 4 – Knowledge Commons Expansion

### Objective

Develop the Knowledge Commons from a set of learning surfaces into a guided institution for study, reflection, teach-back, mentorship, and pathway growth.

### Build next

- Reading journeys and curated learning tracks.
- Study groups connected to Circles.
- Reflection prompts and member-controlled notes.
- Teach-back workflow for members to summarize and share lessons.
- Mentorship matching concept and manual pilot tools.
- Learning pathways connected to assessments, archetypes, and service opportunities.
- Publishing pipeline definition for preserving community knowledge.

### Dependencies

- Phase 1 learning surfaces stable.
- Phase 3 Circle structure available for group learning.
- Clear member-controlled privacy for reflections and notes.
- Garvey/Simba evidence boundary understood.
- Content stewardship and review process.

### Success criteria

- Members can move from reading/listening/viewing to reflection and practice.
- Study groups and Circles can use shared materials.
- Teach-back creates reusable community knowledge.
- Recommendations remain invitations, not forced advancement.

---

## Phase 5 – Marketplace Integration

### Objective

Introduce cooperative economic participation only after trust, identity, operations, and business boundaries are mature enough to support it.

### Build next

- Garvey business hub orientation for business-capable members.
- Business profile and discovery MVP.
- Marketplace listing model for goods, services, opportunities, and mutual aid.
- Community purchasing workflows.
- Trust and reputation display rules that do not expose unrelated assessment or private data.
- Business steward dashboard.
- Marketplace policy, dispute, and quality guidelines.

### Dependencies

- Stable membership and business systems.
- Clear separation of commerce, assessment, STAR, and personal development data.
- Payment/compliance review where transactions are involved.
- Community Operations and Circles ready to supply real needs and trusted relationships.

### Success criteria

- Members can discover trusted businesses or services without confusing marketplace participation with personal worth.
- Business owners can maintain accurate profiles.
- Community purchasing strengthens local/cooperative economics.
- Marketplace does not launch before privacy, policy, and support are ready.

---

## Phase 6 – Investment Platform

### Objective

Create pathways from financial education and cooperative participation toward ownership opportunities, while respecting compliance, risk, and member protection.

### Build next

- Ownership education and readiness content.
- Community investment opportunity architecture.
- Real estate integration planning.
- Investment interest workflow with explicit disclaimers and eligibility boundaries.
- Compliance review, audit trails, reporting, and risk controls.
- Investment steward dashboard.
- Separation of investment data from general member, assessment, health, and marketplace data.

### Dependencies

- Mature Marketplace/Business Systems.
- Legal/compliance review before any live investment offering.
- Strong member identity and role controls.
- Transparent education-first onboarding.
- Institutional stewardship process for evaluating community benefit and risk.

### Success criteria

- Members receive education before opportunities.
- No investment capability ships without compliance approval.
- Ownership systems support community benefit rather than speculation.
- Data boundaries and consent are explicit.

---

## Phase 7 – Leadership & Legacy

### Objective

Develop durable leadership, mentorship, stewardship, and legacy preservation systems grounded in demonstrated service and community trust.

### Build next

- Mentor systems and mentor profiles.
- Leadership pathways based on service, learning, facilitation, and stewardship readiness.
- Institutional stewardship dashboards and health reviews.
- Legacy preservation workflows: stories, lessons, publications, archives, lineage, and handoff notes.
- Elder/advisor participation paths.
- Succession and continuity planning for institutions.

### Dependencies

- Working Knowledge Commons, Circles, Operations, and recognition patterns.
- Consent-aware publishing and archive policies.
- Clear separation between leadership readiness and member identity/worth.
- Stewardship review practices.

### Success criteria

- Members can grow into responsibility through service and mentorship.
- Institutions preserve knowledge across transitions.
- Legacy systems honor dignity, consent, and continuity.
- Leadership is treated as stewardship, not status.

---

## 6. Priority Matrix

Priority scale: **P0** = must-have before public pilot; **P1** = early post-pilot; **P2** = version 1.x/2.0; **P3** = long-term; **P4** = future/conditional.

| Feature / Capability | Priority | Institution owner | Dependencies | Member impact | Community impact | Complexity | Pilot relevance | Future scalability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Landing/CTA polish | P0 | Member Experience | Content review | Clear entry and expectations | Better conversion and trust | Low | High | Medium |
| Auth/session launch smoke tests | P0 | Business Systems / Auth | Deployment env | Reliable access | Reduces support burden | Medium | High | High |
| Pilot onboarding | P0 | Member Experience | Auth, dashboard | Reduces confusion | Sets shared expectations | Low | High | High |
| Member dashboard refinement | P0 | Member Experience | Auth, feature visibility | Clear next steps | Better activation | Medium | High | High |
| Assessment Center polish | P0 | Assessment Center / Garvey Integration | Garvey contract | Development insight | Better member guidance | Medium | High | High |
| Garvey result UX and empty states | P0 | Assessment Center | Garvey data | Less friction | More usable evidence | Medium | High | High |
| Knowledge Commons MVP framing | P0 | Knowledge Commons | Existing library/languages/timeline | Immediate learning value | Shared educational base | Low | High | High |
| Admin/operator launch dashboard | P0 | Admin Operations | Auth/RBAC, system checks | Faster support | Safer pilot operations | Medium | High | High |
| Pilot docs/runbooks | P0 | Stewardship / Operations | Current routes/env | Clear support path | Lower launch risk | Low | High | High |
| Hide future systems | P0 | Product Stewardship | Feature flags/nav review | Honest expectations | Protects trust | Low | High | High |
| Preparedness MVP polish | P1 | Community Operations | Privacy model, auth | Practical readiness | Immediate resilience value | Medium | High | High |
| Preparedness Command Center | P1 | Community Operations | Preparedness data | Clarity of readiness | Better local response | High | Medium | High |
| Volunteer coordination | P1 | Community Operations | Consent, member profiles | Meaningful service | Mobilizes capacity | High | Medium | High |
| Community project records | P1 | Community Operations | Admin tools, roles | Contribution opportunities | Converts plans into action | Medium | Medium | High |
| Operations dashboard | P1 | Community Operations | Project data | Support visibility | Institutional coordination | Medium | Medium | High |
| STAR internal event vocabulary | P1 | STAR / Participation | Operations events | Recognition clarity | Trustworthy participation history | Medium | Medium | High |
| Circle creation | P2 | Community Circles | Member identity, privacy | Belonging and practice | Trust formation | High | Low/medium | High |
| Facilitator tools | P2 | Community Circles | Circle model, training | Better group experience | Sustained cooperation | High | Low | High |
| Circle invitations | P2 | Community Circles | Consent, notification | Opt-in participation | Safer group formation | Medium | Low | High |
| Circle dashboards | P2 | Community Circles | Circle data | Clear commitments | Better continuity | High | Low | High |
| Reading journeys | P2 | Knowledge Commons | Content curation | Guided learning | Shared knowledge base | Medium | Medium | High |
| Study groups | P2 | Knowledge Commons / Circles | Circles, resources | Peer learning | Stronger relationships | Medium | Low/medium | High |
| Teach-back workflow | P2 | Knowledge Commons / Publishing | Reflection/publishing policy | Deeper learning | Preserved wisdom | Medium | Low | High |
| Mentorship MVP | P2 | Knowledge Commons / Legacy | Profiles, consent | Guided growth | Intergenerational transfer | High | Low | High |
| Development pathways | P2 | Simba Development Engine | Garvey evidence, Commons, Operations | Personalized growth | Better contribution fit | High | Low | High |
| Community characteristics | P2 | Simba Development Engine | Garvey evidence, privacy rules | More useful self-understanding | Better role alignment | High | Low | High |
| Community archetypes | P2 | Simba Development Engine | Characteristics, consent | Contribution clarity | Balanced capacity map | High | Low | High |
| Business profiles | P3 | Marketplace / Business Systems | Membership, policy | Economic visibility | Local business support | Medium | Low | High |
| Business discovery | P3 | Marketplace | Business profiles | Find trusted providers | Circulates dollars | Medium | Low | High |
| Marketplace listings | P3 | Marketplace | Policy, support, payments optional | Opportunity access | Cooperative exchange | High | Low | High |
| Community purchasing | P3 | Marketplace | Marketplace trust/policy | Group buying power | Economic coordination | High | Low | High |
| Publishing pipeline | P3 | Publishing / Knowledge Commons | Creator policy, storage | Preserve work | Institutional memory | High | Low | High |
| Ownership education | P3 | Investment / Knowledge Commons | Financial curriculum | Better readiness | Responsible capital culture | Medium | Low | High |
| Investment interest workflow | P4 | Investment Platform | Compliance, identity | Access to ownership path | Capital formation | Very high | Hidden | High |
| Real estate integration | P4 | Investment Platform | Legal/compliance, partners | Ownership opportunity | Community asset building | Very high | Hidden | High |
| Leadership pathways | P4 | Leadership / Stewardship | Operations, Circles, mentorship | Growth into responsibility | Sustained institutions | High | Hidden | High |
| Institutional stewardship dashboard | P4 | Stewardship | Institution metrics | Transparency | Healthier institutions | High | Hidden | High |
| Legacy preservation | P4 | Legacy / Publishing | Consent, archive policy | Dignified continuity | Intergenerational memory | High | Hidden | High |

---

## 7. Dependency Graph

```text
Constitution + Operating Philosophy
  ↓
Ecosystem Architecture + Decision Framework
  ↓
Pilot Stabilization
  ├─ Auth / Membership / RBAC
  ├─ Member Dashboard
  ├─ Assessment Center ↔ Garvey Integration
  ├─ Knowledge Commons MVP
  └─ Admin / System Verification
      ↓
Community Operations Foundation
  ├─ Preparedness MVP
  ├─ Volunteer Coordination
  ├─ Community Projects
  └─ Operator Dashboards
      ↓
STAR Participation Recognition
  └─ Event vocabulary, verification, transparent recognition rules
      ↓
Community Circles
  ├─ Circle creation
  ├─ Facilitator tools
  ├─ Study/service connection
  └─ Circle dashboards
      ↓
Knowledge Commons Expansion
  ├─ Reading journeys
  ├─ Study groups
  ├─ Teach-back
  ├─ Mentorship
  └─ Development pathways
      ↓
Marketplace / Business Systems
  ├─ Business profiles
  ├─ Discovery
  ├─ Listings
  └─ Community purchasing
      ↓
Investment / Ownership Platform
  ├─ Education
  ├─ Compliance
  ├─ Opportunity workflow
  └─ Real estate integration
      ↓
Leadership / Stewardship / Legacy
  ├─ Mentor systems
  ├─ Leadership pathways
  ├─ Institutional health reviews
  └─ Legacy preservation
```

### Critical path

1. Pilot trust must precede expansion.
2. Operations must precede recognition and Circles because real service gives groups and STAR meaningful substance.
3. Circles and Knowledge Commons expansion should precede Marketplace because commerce depends on trust and shared norms.
4. Marketplace and business systems must precede Investment because ownership requires mature economic infrastructure.
5. Leadership and Legacy should emerge from demonstrated learning, service, mentorship, and stewardship.

---

## 8. Pilot Readiness

### Must exist before public launch

- Clear landing page and pilot expectation language.
- Working sign-in/join/member dashboard flow.
- Auth/session smoke test in target deployment environment.
- Assessment Center with clear catalog, launch behavior, result states, and failure/empty states.
- Garvey integration contract documented for required environment variables and callback behavior.
- Knowledge Commons MVP surfaces validated and presented honestly.
- Admin/operator launch dashboard and system verification route.
- Pilot support runbook with recovery steps.
- Feature visibility audit: future systems hidden or clearly labeled.
- Privacy guidance for preparedness and any member-submitted sensitive data.
- Manual onboarding and support process for the first cohort.

### Can wait until after launch

- Automated development pathways.
- Community characteristics and community archetype interpretation.
- Circle productization beyond manual cohort structure.
- Full study group workflow.
- Teach-back publishing pipeline.
- Marketplace listings and purchasing.
- Investment workflows.
- Full STAR rewards/reputation UX.
- Institutional stewardship dashboards.
- Legacy preservation workflows.

### Should remain hidden during pilot

- Investment platform.
- Real estate investment surfaces.
- Marketplace transaction flows.
- Unfinished community directory experiences.
- Incomplete Circle creation tools.
- Any STAR leaderboard or reward mechanic without transparent rules.
- Any characteristic/archetype scoring that is not fully consent-aware and explained.
- Prototype publishing workflows not ready for creator rights and content ownership.
- Health or PocketPT surfaces that imply protected wellness data workflows without privacy controls.

### Should be invite-only

- Preparedness pilot.
- Builder/creator audiobook or organizer workflows.
- Community Operations project management tools.
- Admin and steward dashboards.
- Circle facilitator trials.
- Business owner profile tests.
- Mentorship experiments.
- Any Discord/notification integration that could expose member or operations data.

---

## 9. Pilot Launch Checklist

### Product readiness

- [ ] Landing page explains Simba as a Community Operating System in simple language.
- [ ] Primary CTA path is clear for pilot members.
- [ ] Dashboard shows only current reliable capabilities or clearly marked future invitations.
- [ ] Assessment Center works for the intended cohort.
- [ ] Knowledge Commons MVP links are valid and content is reviewed.
- [ ] Preparedness pilot path is either polished for invite-only use or hidden.
- [ ] Unsupported systems are hidden from navigation.

### Technical readiness

- [ ] Production/staging environment variables verified.
- [ ] Auth/session smoke test passes in target environment.
- [ ] Garvey callback/config smoke test passes or has a documented manual fallback.
- [ ] System verification route/API passes.
- [ ] Admin can view pilot health indicators.
- [ ] Error states and empty states are understandable.
- [ ] Feature flags match the pilot scope.

### Operations readiness

- [ ] Pilot owner named.
- [ ] Support contact and escalation path documented.
- [ ] Manual onboarding script prepared.
- [ ] Known limitations documented for members.
- [ ] Privacy expectations documented for preparedness and assessments.
- [ ] Daily/weekly pilot review cadence established.
- [ ] Feedback capture process created.

### Governance readiness

- [ ] Architecture Decision Framework required for new major features.
- [ ] Constitution and Operating Philosophy referenced for contributors.
- [ ] Data sensitivity and consent boundaries reviewed.
- [ ] No future capability is marketed as currently available.

---

## 10. Post-Pilot Roadmap

### Immediately after pilot

- Review member feedback by journey stage.
- Fix onboarding, auth, dashboard, and assessment friction first.
- Confirm which learning surfaces produced real engagement and reflection.
- Decide whether preparedness should become the first public Community Operations module.
- Document pilot lessons in an institutional memory note.

### Version 1.0 candidate

- Stable public member journey.
- Reliable Knowledge Commons MVP.
- Assessment Center and Garvey result experience polished.
- Preparedness MVP either public or clearly invite-only.
- Admin/operator runbooks maintained.
- Future systems still hidden unless production-ready.

### Version 1.x / 2.0 candidate

- Community Operations projects.
- Volunteer coordination.
- Initial STAR recognition rules.
- Circle MVP.
- Reading journeys and study groups.
- Manual mentorship pilot.
- Development pathway prototype.

### Version 3.0 candidate

- Marketplace and business discovery.
- Community purchasing.
- Publishing/teach-back pipeline.
- Mature STAR participation recognition.
- Stewardship reporting.

### Long-term vision

- Investment and ownership platform.
- Real estate/community asset integration.
- Leadership pipelines.
- Legacy preservation.
- Institutional stewardship as a continuous health system.

---

## 11. Technical Debt and Integration Risks

### Known duplicates and overlap

- Legacy leadership assessment overlaps with Garvey assessment direction.
- Assessment archetypes and planned community archetypes can be confused unless clearly separated.
- Learning surfaces exist across Library, Timeline, Languages, Brain Training, Audiobooks, and Study without a unified Knowledge Commons experience.
- Publishing concepts overlap with audiobook and organizer prototypes but are not yet one coherent institution.

### Disconnected systems

- Knowledge Commons, assessments, pathways, Circles, and Operations are architecturally connected but not yet fully connected in product flow.
- Preparedness exists as the strongest operations proof-of-concept but needs clearer relationship to broader Community Operations.
- STAR has foundations but needs transparent recognition rules and member-facing explanation before becoming prominent.
- Marketplace, Investment, and Legacy are largely future architecture and should not appear as active promises.

### Legacy and prototype code risk

- Legacy leadership assessment should be treated as compatibility until a consolidation plan exists.
- Brain Training and Study surfaces may need pilot decision: polish, reposition, or hide.
- Audiobook and organizer workflows should stay guided or invite-only until creator UX, quotas, rights, and storage behavior are fully supportable.

### Documentation gaps

- Canonical route and feature flag inventory for pilot scope.
- Operator runbook for admin dashboards and support workflows.
- Garvey integration contract and environment setup.
- Privacy/consent notes for preparedness, Circles, reflections, and future characteristics.
- STAR policy explaining recognition without social-credit dynamics.
- Marketplace, investment, publishing, and legacy policies before implementation.

### UX improvements

- Make the member dashboard a current-state guide, not a future-feature catalog.
- Add clear empty states wherever data may not exist yet.
- Improve language around assessments as developmental evidence, not identity labels.
- Clarify what is public, private, invite-only, and future.
- Reduce navigation clutter during pilot.

---

## 12. Release Philosophy

1. **Ship small.** Release narrow, reliable slices that members can understand and operators can support.
2. **Keep institutions coherent.** Add capabilities to existing institutions before creating new ones.
3. **Avoid feature creep.** Do not build a feature because it is interesting; build it because it strengthens the mission.
4. **Prefer extending existing systems.** Reuse established routes, data boundaries, roles, and UI patterns where appropriate.
5. **Preserve architectural boundaries.** Garvey, Simba, STAR, Operations, Marketplace, Publishing, Investment, and Legacy must retain distinct responsibilities.
6. **Mission before features.** A technically impressive feature that weakens dignity, trust, consent, or community value should not ship.
7. **Invite before automate.** Early pathway, Circle, mentorship, and leadership systems should begin with human-guided pilots before automation.
8. **Privacy by default.** Sensitive household, assessment, reflection, health, finance, and Circle data should be minimized, consent-aware, and role-protected.
9. **Recognition without reduction.** STAR and participation records should recognize contribution without defining a member's worth.
10. **Document decisions.** Every major release should leave behind institutional memory for future stewards.

---

## 13. Executive Timeline

| Horizon | Main goal | Expected scope |
| --- | --- | --- |
| Pilot | Prove a guided member journey can work reliably and honestly. | Stabilized onboarding, dashboard, assessments, Knowledge Commons MVP, admin visibility, selected invite-only preparedness. |
| Version 1.0 | Establish a trustworthy public foundation. | Reliable member experience, polished learning/assessment flow, supportable operations, clear docs, hidden future systems. |
| Version 2.0 | Move from learning into coordinated community practice. | Community Operations, preparedness expansion, volunteer coordination, project workflows, Circle MVP, study groups, initial recognition. |
| Version 3.0 | Connect trust and participation to cooperative economics. | Marketplace, business discovery, community purchasing, publishing pipeline, mature pathways and mentorship. |
| Long-term vision | Build durable institutions for ownership, leadership, and legacy. | Investment platform, real estate integration, leadership pathways, stewardship dashboards, legacy preservation, intergenerational knowledge systems. |

---

## 14. Implementation Recommendations

1. Treat this roadmap as the default feature sequencing reference.
2. Require every new major feature proposal to cite its phase, institution owner, dependencies, and success criteria.
3. Before Phase 2 work, complete pilot route, feature flag, and admin runbook documentation.
4. Before Circle implementation, define consent and privacy rules for invitations, membership, notes, commitments, and facilitator visibility.
5. Before pathway implementation, clarify Garvey evidence vs Simba interpretation vs member choice.
6. Before STAR expansion, publish transparent earning, verification, and non-punitive recognition rules.
7. Before Marketplace implementation, complete commerce policy, business profile boundaries, and data separation rules.
8. Before Investment implementation, complete legal/compliance review and education-first onboarding.
9. Before Leadership and Legacy implementation, complete mentorship, consent, publishing, and archive policies.
10. After every release, update the Capability Inventory, Capability Matrix, Dependency Map, and this roadmap.

---

## 15. Confirmation of No Production Behavior Change

This roadmap is documentation only. Creating this file does not change production behavior, runtime code, APIs, database schemas, migrations, Garvey integrations, Simba runtime behavior, STAR behavior, permissions, Marketplace behavior, Investment behavior, or user-facing functionality.
