# Unified Intelligence Layer — Goal-Oriented Repo Integration Plan

Date: 2026-06-30  
Status: architecture alignment only; no runtime behavior, schema, route, or UI implementation changes.  
Scope: repo-wide inspection of Society Builder, Mutual Aid fund operations, First 100 Days container/trust board, role-fit intelligence, Garvey/member assessments, member profiles, governance/admin dashboards, and related community operating-system surfaces.

## 1. Executive summary

The repo already contains most of the raw parts needed for a unified Mutual Aid Society intelligence layer, but the parts are not yet connected into one operating loop.

The most important finding is that **Society Builder should be the integration spine**. It already knows the society, founder/member relationships, lifecycle stage, First Ten, purpose, covenant, First 100 Days container, trust-board tasks, member institutional profiles, chapter status, and the persisted role assignment workflow. The new intelligence layer should attach to those existing records instead of creating a separate intelligence island.

The second most important finding is that **Garvey/member assessment evidence already has a canonical storage path**: Garvey callback payloads are recorded as sync events and summarized into `MemberProfile.attributes.growth_profile` plus `garvey_assessment_completions`. That evidence should feed a live member behavioral profile adapter. The static `memberBehavioralProfiles.js` examples should remain preview/demo data only until replaced by live consented evidence.

The third finding is that **role interpretation already exists in two forms**:

1. a static frontend role interpretation engine using sample behavioral profiles and role blueprints, and
2. a persisted backend Society Builder role assignment workflow using First Ten scores/notes and role openings.

The next implementation work should converge these two paths without changing the community-governance philosophy: the software may recommend, summarize, and preserve evidence, but it must not appoint, rank, badge, punish, or turn assessment results into permanent identity.

## 2. Philosophy and hard boundaries

The integration plan should preserve these product rules:

- The system recommends; the community decides; the member grows.
- Assessments are mirrors of current patterns, not permanent identity.
- Role-fit outputs should use non-final language such as “current evidence suggests,” “could support,” “recommended next practice,” and “review with the member/community.”
- Avoid fixed-label, negative-label, reputation, passport, badge, automatic appointment, and automatic task assignment patterns.
- Garvey remains the observation engine. Simba/Society Builder remains the development and coordination engine.
- Keep sensitive evidence scoped, consented, summarized, and auditable.
- Preserve current Society Builder behavior; add integration surfaces around it.
- Do not build adaptive Kanban yet. First connect live evidence, roles, tasks, and dashboards to the existing Trust Board.

## 3. Existing systems discovered

| System | Main files/routes/models | Current role in platform | Integration stance |
|---|---|---|---|
| Society Builder | `backend/app/routes/society_builder.py`, `backend/app/services/society_builder.py`, `src/api/societyBuilder.js`, `src/pages/SocietyBuilderPage.jsx`, `src/pages/SocietyFormationPage.jsx` | Creates societies/chapters and stores the institutional spine. | Make this the source of truth for society context. |
| My Societies / Society Home | `src/pages/MySocietiesPage.jsx`, `src/pages/SocietyHomePage.jsx` | Member/founder entry to existing societies, foundation status, First Ten, purpose, covenant, container activation. | Add intelligence summaries here, not a new standalone hub. |
| Society membership | `SocietyMembership` | User-to-society membership with local role/status. | Source of truth for which society a user belongs to. |
| First Ten | `SocietyFirstTenMember`, First Ten routes and Society Home UI | Early founding member list with manual behavior scores and possible user links. | Source of truth for pre/full-member role-review candidates until all are linked users. |
| Institutional profile | `SocietyInstitutionalProfile`, profile/member-home/directory pages | Stores contribution, availability, goals, needs, skills-to-learn, projects, impact, visibility/privacy. | Source of truth for member-stated contribution/growth/needs inside a society. |
| Blueprint Audit | `SocietyBlueprintAudit`, Society Home UI | Foundation maturity snapshot across trust, relationships, mutual aid, organization, institutions, etc. | Source of truth for society-level readiness gaps. |
| Purpose Builder | `SocietyPurpose` | Stores structured purpose and Day 100 goal. | Source of truth for society mission and Day 100 target. |
| Covenant Builder | `SocietyCovenant` | Stores operating promises, money/privacy/conflict practices, review rhythm. | Source of truth for society rules/covenant until a separate rules module exists. |
| First 100 Days Container | `SocietyContainer`, `SocietyContainerMilestone`, activation route, active-container route | Tracks active 100-day container day/week/progress/milestones. | Source of truth for container/stage context. |
| Trust Board | `SocietyTrustTask`, `src/pages/SocietyTrustBoardPage.jsx` | Kanban-style board grouped by status and lane, with handbook links and task owner fields. | Source of truth for existing society work; intelligence should annotate it before adapting it. |
| Handbook / reader references | `src/data/societyContainerGuide.js`, `src/data/containers/first100DaysHandbookSource.js`, `First100DaysChapterReaderPage.jsx`, trust-task reader endpoint | Provides First 100 Days guidance and task/chapter references. | Source of truth for learning/practice content that supports roles. |
| Role Blueprint Library | `src/data/mutualAidRoleBlueprints.js`, `MutualAidRoleBlueprintLibraryPage.jsx`, validation script | Static catalog of mutual aid roles, traits, responsibilities, assessment recommendations, handbook links. | Should become canonical seed data for role openings, either imported to backend or duplicated through a migration/catalog. |
| Member Behavioral Profiles | `src/data/memberBehavioralProfiles.js` | Static sample profiles for preview. | Replace with live profile adapter fed by Garvey, member profile, First Ten, and optional participation evidence. |
| Role Interpretation Engine | `src/data/roleInterpretationEngine.js` | Static frontend comparison of sample member profile to role blueprint. | Reuse logic concepts, but move live interpretation to backend service or shared deterministic module. |
| Persisted role assignment workflow | `SocietyRoleOpening`, `SocietyRoleCandidateReview`, `SocietyRoleDiscussionNote`, `SocietyRoleAppointmentHistory`, `/role-assignment/*` backend routes | Stores real role openings, candidate reviews, discussion notes, appointment history. | Source of truth for society role review/appointments; needs frontend API client/page wiring. |
| Garvey Assessment Center | `backend/app/routes/garvey.py`, `src/api/assessments.js`, `src/pages/AssessmentCenter.jsx` | Catalog, archetypes, transfer tokens, results, growth profile, callbacks. | Source of truth for external assessment evidence and recommended next assessment. |
| Local Leadership Assessment | `LeadershipAssessment`, `backend/app/routes/assessment.py`, `components/leadership/*` | Local/legacy leadership scoring and dashboard. | Treat as compatibility evidence; do not make it the primary assessment source. |
| Member dashboard | `src/pages/MemberDashboard.jsx`, `backend/app/routes/member.py` | Shows membership/onboarding/growth/assessment/community progress. | Should display society-specific next steps only after Society Builder evidence adapter exists. |
| Mutual Aid Fund runtime | `backend/app/routes/mutual_aid.py`, MutualAid* models/pages | Request intake, review, decisions, appeals, disbursement, financial controls, analytics, observability. | Keep separate from Society Builder until explicit society-fund association is designed. |
| Governance/Executive/Operations dashboards | `MutualAidGovernanceCenter.jsx`, `MutualAidExecutiveDashboard.jsx`, `MutualAidOperationsDashboard.jsx`, analytics/readiness/security/documentation pages | Mostly admin planning/readiness/observability surfaces. | Consume society intelligence summaries later; do not become the source of truth. |
| Aid allowlist / pilot preview pages | `MutualAidAllowlistPreviewPage.jsx`, `MutualAidPilotPreviews.jsx` | Static preview/pilot access shells. | Defer/deprecate after live flows exist. |
| Applications registry / global navigation | `src/data/applications.js`, `src/components/GlobalNav.jsx`, `src/App.jsx` | Routes users into Society Builder, Mutual Aid, assessments, preparedness, etc. | Add links to live role assignment only after backend/frontend integration exists. |
| Community operations registry | `src/operations/communityOperationsRegistry.js` | Lists operations modules such as mutual aid. | Later target for society-level operational summaries. |
| Participation/STAR | `backend/app/services/participation.py`, MemberDashboard, v2 ledger | Tracks activity/STAR/community contribution. | Defer role-fit use until consent/privacy rules are established; do not use as reputation. |

## 4. Current models, routes, pages, services, and data flows

### 4.1 Society Builder data flow today

1. A user enters `/society-builder`, `/societies/start`, or `/societies/register-chapter`.
2. The frontend uses `src/api/societyBuilder.js` to call `/society-builder/societies`.
3. Backend creates a `Society` and a founder/admin `SocietyMembership`.
4. Society Home can save Blueprint Audit, First Ten members, Purpose, Covenant, chapter application, and activate the First 100 Days container.
5. First 100 Days activation creates the active `SocietyContainer`, milestones, and `SocietyTrustTask` records.
6. Trust Board reads container/tasks and lets authorized members move/update tasks.
7. Member Home/Profile/Directory read/write `SocietyInstitutionalProfile` and display contribution/need/skill/profile data.
8. Role assignment backend can create openings, suggest candidates, record review notes/decisions, and create appointment history, but no live frontend API client/page is wired for this workflow yet.

### 4.2 Garvey/member assessment data flow today

1. Assessment Center calls `/member/assessments/catalog`, `/archetypes`, `/transfer-token`, `/results`, and `/growth-profile`.
2. Garvey callbacks accept assessment completion payloads.
3. Callback processing stores `GarveySyncEvent` rows and updates `MemberProfile.attributes` with:
   - `growth_profile`
   - `garvey_assessment_completions`
   - strengths, growth edges, scores, result links, recommended next assessment, and timeline summary.
4. Member Dashboard reads member overview/growth data and displays completed assessments and recommended next assessment.
5. Society Builder role assignment currently does not read this evidence.

### 4.3 Role-fit data flow today

Static preview path:

1. `memberBehavioralProfiles.js` provides sample member profiles.
2. `mutualAidRoleBlueprints.js` provides static role blueprints.
3. `roleInterpretationEngine.js` compares sample profile evidence to blueprint needs.
4. `MutualAidRoleReviewPage.jsx` displays a preview report.

Persisted Society Builder path:

1. Society role openings are created through backend `/role-assignment/open-roles` endpoints.
2. Candidate suggestions iterate `SocietyFirstTenMember` rows.
3. `_candidate_fit` uses First Ten manual scores, role required behavior text, member notes, and role recommended assessments to populate `SocietyRoleCandidateReview`.
4. Review decisions can create `SocietyRoleAppointmentHistory`.
5. This persisted path is real, but it is not yet exposed through `src/api/societyBuilder.js` and is not connected to Garvey assessment completions or the static blueprint catalog.

## 5. Source-of-truth decisions

| Concept | Source of truth now | Do not use as source of truth | Why |
|---|---|---|---|
| Which society a member belongs to | `SocietyMembership` | Global app role, sample profile list | Society context is local and relational. |
| Society creation/chapter status | `Society` | Mutual Aid preview pages | Society Builder already owns this lifecycle. |
| Container/stage context | `SocietyContainer` + milestones/tasks | Static handbook alone | The container is the active operating record. |
| Trust-board work | `SocietyTrustTask` | New adaptive Kanban model | Preserve current board; annotate before adapting. |
| Member-stated contributions/goals/needs | `SocietyInstitutionalProfile` | Static sample behavioral profiles | It is already society-scoped and privacy-aware. |
| First founding candidate list | `SocietyFirstTenMember` | `SocietyMembership` alone | First Ten can include people not yet linked to users. |
| Role openings/reviews/appointments | `SocietyRoleOpening`, `SocietyRoleCandidateReview`, `SocietyRoleAppointmentHistory` | Static role review preview | Persisted workflow is the real community decision trail. |
| Role blueprint definitions | `src/data/mutualAidRoleBlueprints.js` for now | Free-text role names | Existing catalog is coherent; make it seed/catalog data next. |
| External assessment evidence | `GarveySyncEvent` + `MemberProfile.attributes.growth_profile` / `garvey_assessment_completions` | Static sample completed assessments | This is live member evidence. |
| Local leadership assessment | `LeadershipAssessment` | Garvey replacement | Compatibility evidence only. |
| Mutual Aid fund requests/disbursements | MutualAid* models/routes | Society role assignment tables | Fund workflow has its own controls and permissions. |
| Society governance docs | `SocietyCovenant`, governance docs/pages | Role review notes | Covenant owns rules; role notes should not become policy. |

## 6. Systems that already connect

- Society creation connects to society membership creation and My Societies.
- Society Home connects Blueprint Audit, First Ten, Purpose, Covenant, chapter application, and active container launch.
- First 100 Days activation connects Society Builder to container/milestone/task records.
- Trust Board connects tasks to lanes, statuses, handbook guide entries, and reader references.
- Society Member Home/Profile/Directory connect society membership to institutional profile contributions, goals, needs, and directory grouping.
- Garvey callbacks connect external assessment completion to `MemberProfile.attributes.growth_profile` and Member Dashboard display.
- Static role review connects static behavioral profiles to static role blueprints.
- Backend role assignment connects First Ten members to role openings, candidate reviews, discussion notes, decisions, and appointment history.
- Mutual Aid fund runtime connects requests, reviews, decisions, appeals, disbursement tracking, financial controls, notifications, analytics, security, and observability.

## 7. Systems that are disconnected

- Static role blueprints are not used to seed backend role openings.
- Static role interpretation is not used by backend role assignment.
- Backend role assignment is not exposed through the frontend API client or society routes.
- Garvey `growth_profile` and `garvey_assessment_completions` do not feed First Ten, behavioral profiles, candidate reviews, Trust Board, or Society Home.
- `SocietyInstitutionalProfile` does not feed role-fit interpretation or teammate/mentor suggestions.
- First Ten linked `user_id` is not used to pull live member assessment evidence.
- Trust-board `linked_role`/`linked_module` fields do not create role openings or role coverage warnings.
- Role appointment history is not surfaced on Society Home, Member Home, Trust Board, governance pages, or dashboards.
- Treasurer/Assistant Treasurer appointments do not connect to Mutual Aid financial controls or treasury setup.
- Care Coordinator appointments do not connect to needs privacy, needs map, or care teams.
- Facilitator/Recordkeeper appointments do not connect to meeting agendas, minutes, attendance, decision logs, or action items.
- Day 100 Report, Recommitment, and Next Phase Planner are not persisted yet.
- Governance/Executive/Operations dashboards are mostly planning/readiness/admin surfaces rather than live society intelligence dashboards.
- Mutual Aid Fund runtime is not society-scoped and should not be assumed to represent a local society treasury yet.

## 8. Overlaps and duplicates to resolve carefully

| Overlap | Current state | Recommendation |
|---|---|---|
| Role concepts | App RBAC roles, `SocietyMembership.role`, `SocietyFirstTenMember.role`, `SocietyRoleOpening.title`, static role blueprints, Mutual Aid committee roles. | Keep separate but document boundaries. Only RBAC grants app permissions; society roles are local responsibilities; committee roles are fund governance roles. |
| Member profile concepts | `MemberProfile.attributes`, `SocietyInstitutionalProfile`, static `memberBehavioralProfiles.js`. | Use `MemberProfile` for platform-level assessment/onboarding evidence, `SocietyInstitutionalProfile` for society-scoped contribution/needs/goals, static profiles for preview only. |
| Assessment paths | Garvey Assessment Center and local `LeadershipAssessment`. | Make Garvey/member growth profile primary; treat local leadership assessment as legacy/compatibility evidence. |
| Role interpretation paths | Static frontend interpreter and backend `_candidate_fit`. | Converge into a live backend/shared interpretation service that writes `SocietyRoleCandidateReview`; keep preview until live UI is ready. |
| Kanban/task systems | Trust Board tasks, role development plans, future adaptive Kanban, possible meeting action items. | Trust Board remains canonical for 100-day tasks. Role development plans and meetings should link to tasks, not replace them. |
| Treasury/ledger concepts | Mutual Aid fund runtime, financial controls, Ledger pages/v2 ledger, Treasurer blueprint. | Keep separate until a society treasury source-of-truth design is approved. Do not grant treasury permissions from role fit. |
| Governance/admin pages | Governance Center, Executive Dashboard, Operations Dashboard, role review preview, chapter admin. | Leave planning/admin pages separate, but feed them live summary cards later. Deprecate static previews after live equivalents exist. |
| Needs/care concepts | Institutional profile needs, Care Coordinator role, missing Care Teams. | Institutional profile needs are the seed; Care Teams should be new workflow later with strict permissions. |

## 9. How Garvey evidence should feed live member behavioral profiles

### 9.1 Do not create a new profile table first

The first integration should be an adapter/read model, not a new source-of-truth table. A live behavioral profile can be assembled from existing sources:

- `MemberProfile.attributes.growth_profile`
- `MemberProfile.attributes.garvey_assessment_completions`
- local `LeadershipAssessment` rows as legacy evidence
- `SocietyInstitutionalProfile` contribution/goals/skills/needs fields
- `SocietyFirstTenMember` scores/notes where a First Ten member is linked to `user_id`
- later, carefully consented participation evidence from STAR/participation systems

### 9.2 Suggested live behavioral profile shape

A live profile should be a generated summary with provenance, not a permanent identity record:

```json
{
  "user_id": 123,
  "society_id": 45,
  "generated_at": "2026-06-30T00:00:00Z",
  "evidence_window": "current_and_recent",
  "completed_assessments": [],
  "current_patterns": [],
  "member_stated_growth_interests": [],
  "member_stated_contributions": [],
  "society_context": {},
  "privacy_scope": "role_review_summary",
  "limitations": ["Not a permanent label", "Requires community review"]
}
```

### 9.3 Evidence mapping rules

- Map Garvey assessment names/IDs to recommended-assessment names used by role blueprints.
- Preserve raw Garvey payloads in existing sync events/member attributes; expose only summarized role-review evidence.
- Include strengths and growth edges as evidence statements, not scores for public ranking.
- Include recommended next assessment as a growth step.
- If no consent or no linked user exists, role review should fall back to First Ten community observations and say evidence is limited.

## 10. How behavioral profiles should feed role interpretation

Role interpretation should become a service that accepts:

- a society context (`Society`, active container, stage, purpose/covenant, blueprint audit),
- a candidate context (`SocietyFirstTenMember` and/or linked `User`/`SocietyMembership`),
- live behavioral profile summary,
- role blueprint/opening requirements,
- trust-board/handbook context for practice opportunities.

It should produce:

- current alignment narrative,
- evidence statements with sources,
- missing evidence/assessments,
- member-stated growth interests,
- suggested practice opportunities,
- relevant handbook chapters,
- mentor/complementary teammate suggestions,
- clear limitation/reminder that community decides.

It should write or update `SocietyRoleCandidateReview`, because that is already the persisted review trail.

It should not produce:

- automatic appointment,
- ranking leaderboard,
- negative member score,
- public badge/passport,
- automatic task assignment,
- permanent archetype identity.

## 11. How role interpretation should feed existing Society Builder systems

| Target system | Feed from role interpretation | Smallest safe integration |
|---|---|---|
| Society Home | Role coverage, open roles, pending reviews, next assessment prompts, appointment history summary. | Add a role coverage card backed by `/role-assignment/dashboard`. |
| First Ten | Candidate readiness for critical roles, missing evidence, linked-user assessment prompts. | Add “review for role” actions for First Ten members; no auto-sorting. |
| Role openings | Seed openings from role blueprints and society stage/tasks. | Add blueprint-to-opening seed action for founders/admins. |
| Trust Board | Show task-linked role needs, practice opportunities, handbook chapters. | Annotate tasks with role coverage/missing role notices; no adaptive Kanban. |
| 100-Day Container | Show role coverage by milestone/stage and missing foundation responsibilities. | Add summary only; do not redesign container. |
| Governance | Show role review policy, covenant alignment, upcoming reviews, open governance roles. | Admin/member summary card later. |
| Member Home/Profile | Show opt-in “responsibilities I carry / want to grow into” and suggested next assessment. | Add after live behavioral profile adapter. |
| Dashboards | Aggregate society health: coverage, vacancies, assessment evidence completion, task blockers. | Use aggregate counts, not individual labels, for admin dashboards. |
| Mutual Aid Fund | Treasurer readiness and controls checklist only after society-fund boundary is designed. | Defer direct permission/workflow connection. |

## 12. What integration work should happen before adaptive Kanban

Adaptive Kanban should wait until the evidence path is stable. Required prior work:

1. Expose backend role assignment through `src/api/societyBuilder.js`.
2. Add a live society role assignment UI under Society Builder.
3. Seed role openings from the existing role blueprint library.
4. Build a live behavioral profile adapter from Garvey/member profile/First Ten/institutional profile evidence.
5. Map Garvey assessment names/results to role blueprint recommended assessments.
6. Write role interpretation into `SocietyRoleCandidateReview`.
7. Surface role coverage on Society Home.
8. Annotate Trust Board tasks with existing `linked_role` coverage and role-review CTAs.
9. Preserve handbook links and current task lanes/statuses unchanged.
10. Add privacy/consent copy and permission checks before exposing assessment-derived evidence.

Only after those steps should the platform consider adaptive Kanban suggestions, and even then suggestions should be reviewable and opt-in.

## 13. Explicit deferrals

Defer these until after the unified evidence -> profile -> role review -> task annotation loop exists:

- Adaptive Kanban.
- Automatic task assignment.
- Automatic role appointment.
- Passport, badges, member reputation labels, negative scores, or permanent identity tags.
- A new general intelligence database that duplicates existing Society Builder records.
- Full Meeting Builder.
- Full Care Teams / private needs workflow.
- Day 100 Report generation.
- Recommitment workflow.
- Next Phase Planner.
- Society-scoped treasury/fund accounting integration.
- Role-driven RBAC permission grants.
- Participation/STAR evidence in role-fit review, except as a later opt-in summary with safeguards.

## 14. Recommended phase roadmap

### Phase 0 — Document and freeze source-of-truth boundaries

Goal: prevent duplicate intelligence islands.

- Adopt this source-of-truth map.
- Name Society Builder as the integration spine.
- Keep static role review screens explicitly marked as preview until live data replaces them.
- Add developer documentation for roles vs RBAC vs First Ten vs committee roles.

### Phase 1 — Wire persisted role assignment into frontend Society Builder

Goal: make the existing backend role assignment workflow usable before adding new intelligence.

Small changes:

- Add API client methods in `src/api/societyBuilder.js` for role assignment endpoints.
- Add `/societies/:societyId/role-assignment` page or section.
- Add a Society Home role coverage card using `/role-assignment/dashboard`.
- Show open roles, filled roles, vacant roles, roles under review, and appointment history.

Do not add new models.

### Phase 2 — Seed role openings from Role Blueprint Library

Goal: reuse static blueprints as starter data for real role openings.

Small changes:

- Create a safe blueprint seed endpoint/service or frontend-assisted seed action.
- Start with critical First Ten roles: Founder/Admin, Facilitator, Treasurer, Assistant Treasurer, Recordkeeper, Care Coordinator, Membership Coordinator.
- Map blueprint purpose/responsibilities/traits/handbook/recommended assessments into `SocietyRoleOpening`.
- Avoid automatic candidate selection.

### Phase 3 — Live behavioral profile adapter

Goal: replace sample behavioral profiles with live summarized evidence.

Small changes:

- Add a backend read-only adapter that composes live profile summaries from existing tables/JSON attributes.
- Include Garvey completions/growth profile, local leadership assessment compatibility evidence, institutional profile contributions/goals/skills, and First Ten observations.
- Add clear source provenance and limitations.
- Gate sensitive evidence by society membership, role-review permission, and member consent policy.

### Phase 4 — Connect Garvey evidence to role interpretation

Goal: make recommended assessments and completed evidence real.

Small changes:

- Add assessment-name mapping between Garvey official assessments and blueprint recommended assessments.
- Add role-review evidence summaries to candidate reviews.
- Populate missing-assessment prompts from live completion data.
- Keep raw scores private; prefer narrative strengths/growth edges.

### Phase 5 — Connect role interpretation to First Ten and role openings

Goal: help founders review people for responsibilities without ranking them.

Small changes:

- Add “review candidate for role” from a First Ten row.
- Update `SocietyRoleCandidateReview` with live evidence summary, growth path, handbook references, and complementary teammate suggestions.
- Preserve reviewer notes and community decision step.

### Phase 6 — Connect role coverage to Trust Board and 100-Day Container

Goal: connect intelligence to the existing container before adaptive Kanban.

Small changes:

- Use `SocietyTrustTask.linked_role` and `linked_handbook_chapter` to show role coverage status on task cards.
- Add non-blocking “this task may need a Treasurer/Recordkeeper/etc.” notices.
- Add links from tasks to role openings/reviews and handbook chapters.
- Add aggregate role coverage to active container summary.

### Phase 7 — Governance and dashboard summaries

Goal: give admins and members a society-level picture without exposing sensitive individual details.

Small changes:

- Add aggregate counts to governance/executive/operations surfaces: vacancies, under-review roles, missing assessments count, task blockers by role, upcoming review dates.
- Avoid individual assessment labels on broad admin dashboards unless permission and purpose are explicit.

### Phase 8 — Later operating modules

Goal: build missing workflows only after the intelligence spine is working.

Later modules:

- Meeting Builder connected to Facilitator/Recordkeeper.
- Needs Map/Care Teams connected to Care Coordinator and privacy rules.
- Day 100 Report from purpose/covenant/tasks/role coverage/treasury readiness.
- Recommitment and Next Phase Planner.
- Society treasury/fund association and dual-control permission workflows.
- Optional adaptive Kanban recommendations.

## 15. Specific files/routes/models likely to modify next

### Immediate next backend files

- `backend/app/routes/society_builder.py`
  - expose or refine role assignment endpoints for frontend consumption;
  - add role blueprint seeding endpoint/service call;
  - add live behavioral profile evidence endpoint;
  - return role coverage in society summary only after endpoint is stable.
- `backend/app/services/society_builder.py`
  - centralize role coverage, blueprint seeding, stage/task role requirements, and live interpretation helper functions.
- `backend/app/routes/garvey.py`
  - add reusable evidence extraction/mapping helpers or a new service imported by Society Builder.
- `backend/app/routes/member.py`
  - expose consented/summarized member assessment profile data if needed.
- `backend/app/models.py`
  - avoid new models in Phases 1–4 if possible; existing role assignment tables are enough.

### Immediate next frontend files

- `src/api/societyBuilder.js`
  - add role assignment API client methods.
- `src/pages/SocietyHomePage.jsx`
  - add role coverage card and link to role assignment workflow.
- New or existing `src/pages/SocietyRoleAssignmentPage.jsx`
  - consume persisted backend role assignment workflow.
- `src/pages/SocietyTrustBoardPage.jsx`
  - later add linked-role coverage annotations.
- `src/pages/MutualAidRoleReviewPage.jsx`
  - convert from static preview to live review or deprecate after live page exists.
- `src/data/mutualAidRoleBlueprints.js`
  - keep as source seed data until backend catalog/migration exists.
- `src/data/memberBehavioralProfiles.js`
  - keep as sample-only; remove from production role review once live adapter exists.
- `src/data/roleInterpretationEngine.js`
  - reuse language/rules or migrate logic server-side for live persisted reviews.
- `src/App.jsx`
  - add live Society Builder role assignment route only when page/API exist.

### Later backend models/routes

Only after Phases 1–6:

- Meeting models/routes for agendas, attendance, minutes, decisions, action items.
- Care Team models/routes for private needs queue, assignments, follow-up, escalation.
- Day 100 Report model/route.
- Recommitment model/route.
- Next Phase Planner model/route.
- Optional `society_id` association for Mutual Aid funds after treasury design.

## 16. Success criteria for the next build phase

The next build phase is successful if:

- A founder can open an existing society and see role coverage from real persisted role assignment data.
- A founder can seed or create role openings from existing role blueprints.
- A First Ten member can be reviewed for a role without automatic appointment.
- The review can show completed/missing assessment evidence from live Garvey/member profile data when available.
- The review can show handbook/practice suggestions connected to the existing First 100 Days container.
- Trust Board remains operational exactly as before, with optional role context added only as annotation.
- No new reputation, passport, badge, or automatic assignment behavior is introduced.

## 17. Inspection commands used

- `find .. -name AGENTS.md -print`
- `rg -n "Society|society|mutual_aid|Mutual Aid|assessment|Assessment|Garvey|archetype|Archetype|role-assignment|Role Assignment|trust-board|Trust Board|container|Container|Blueprint Audit|Purpose|Covenant|First Ten|Governance|Executive|Operations Dashboard|allowlist|Allowlist|member profile|MemberProfile|Member Profile|kanban|task" backend/app src docs --glob '!node_modules' --glob '!*.gdoc' --glob '!src/data/containers/what_cameBeforeBlackWallstreet'`
- `sed -n '1,140p' docs/community-archetype-specification.md`
- `sed -n '1,220p' backend/app/routes/garvey.py`
- `sed -n '1,140p' backend/app/routes/member.py`
- `sed -n '1,180p' backend/app/models.py`
- `rg -n "class Garvey|GarveySync|growth_profile|attributes|assessment" backend/app/models.py backend/app/routes/garvey.py backend/app/routes/member.py backend/app/services -g'*.py'`
- `sed -n '1,220p' backend/app/services/society_builder.py`
- `sed -n '1,120p' src/pages/SocietyHomePage.jsx`
- `sed -n '1,140p' src/pages/SocietyTrustBoardPage.jsx`
- `sed -n '1,140p' src/pages/MutualAidRoleReviewPage.jsx`
- `sed -n '1,160p' src/data/roleInterpretationEngine.js`
- `sed -n '1,130p' src/data/memberBehavioralProfiles.js`
- `sed -n '1,120p' src/api/societyBuilder.js`
