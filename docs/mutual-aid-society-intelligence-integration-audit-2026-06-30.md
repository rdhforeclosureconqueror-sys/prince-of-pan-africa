# Mutual Aid Society + Archetype Intelligence Integration Audit

Date: 2026-06-30  
Scope: repo-wide static inspection of Mutual Aid Society, Society Builder, First 100 Days, handbook, role-fit intelligence, assessment, Garvey, treasury, meeting/task, member-profile, dashboard, and admin surfaces.

## Executive summary

The repository already contains two partly separate Mutual Aid tracks:

1. **Mutual Aid fund/runtime operations**: request intake, admin review, decisions, appeals, disbursement tracking, financial controls, notifications, analytics, observability, launch-readiness and documentation endpoints.
2. **Mutual Aid Society/Society Builder operations**: society creation, chapter registration, member home, institutional profiles, society directory, blueprint audit, First Ten, purpose, covenant, First 100 Days container, trust board tasks, handbook reader references, and role assignment workflow.

The new archetype/role-fit layer is present, but split between:

- frontend static intelligence datasets and screens (`mutualAidRoleBlueprints`, `memberBehavioralProfiles`, `roleInterpretationEngine`, role blueprint library, role review page), and
- backend Society Builder role-assignment tables and APIs that compute candidate fit from First Ten behavioral scores and manual completed-assessment labels.

The strongest existing connection is **First Ten -> role opening -> candidate review -> appointment history**. The largest gap is that role-fit intelligence is not yet connected to persisted Garvey/assessment results, institutional member profiles, active society dashboards, trust-board tasks, treasury setup, meeting/recordkeeping workflows, care teams, recommitment, Next Phase Planner, or Day 100 report generation.

No feature implementation was done in this task. This report and the JSON inventory are documentation-only deliverables.

## Inspection commands used

- `find .. -name AGENTS.md -print`
- `rg -n -i "Mutual Aid Society|Society Builder|Start a Society|100-Day Planner|100 Day|Handbook|First Ten|Purpose Builder|Covenant Builder|Treasury|Ledger|Needs Map|Skills and Assets|Care Teams|Rules Builder|Meeting Builder|First Action|Day 100|Recommitment|Next Phase Planner|Role Blueprint|Behavioral Profile|Role Interpretation|Role Assignment|Garvey|Archetype|Assessment|committee|committees|members|roles" . --glob '!node_modules' --glob '!vendor' --glob '!dist' --glob '!build' --glob '!coverage' --glob '!*.lock' --glob '!package-lock.json'`
- `rg --files | rg -i 'societ|mutual|archetype|role|assessment|garvey|treasury|ledger|planner|handbook|meeting|care|skill|asset|need|member|committee|covenant|purpose|rules|report'`
- `rg -n "class .*Society|society_|mutual_aid|RoleAssignment|role_assignment|assessment|Garvey|role_blueprint|behavioral" backend/app backend/migrations src/pages src/api src/data App.jsx --glob '!*.gdoc'`
- `rg -n "@router\.|def .*role|role_assign|100|first_ten|purpose|covenant|handbook|meeting|treasury|ledger|needs|skills|care|report|recommit|stage|member" backend/app/routes/society_builder.py src/pages/SocietyBuilderPage.jsx src/pages/SocietyHomePage.jsx src/pages/SocietyMemberHomePage.jsx src/pages/MutualAidRoleReviewPage.jsx src/pages/MutualAidRoleBlueprintLibraryPage.jsx src/data/memberBehavioralProfiles.js src/data/roleInterpretationEngine.js src/data/mutualAidRoleBlueprints.js App.jsx`

## Existing Mutual Aid Society capability map

### Backend models and tables

| Capability | Existing model/table | Status | Notes |
|---|---|---|---|
| Society registry | `Society` / `societies` | Implemented | Stores slug, name, type, focus, visibility, lifecycle, chapter/hub fields, geography, founder, parent/root society. |
| Society membership | `SocietyMembership` / `society_memberships` | Implemented | User-to-society relationship with role and status. Separate from First Ten and app RBAC roles. |
| Institutional member profile | `SocietyInstitutionalProfile` / `society_institutional_profiles` | Implemented | Contribution, availability, goals, needs, privacy, projects, impact summary. This is the closest existing Needs Map / Skills & Assets Map substrate. |
| Blueprint audit | `SocietyBlueprintAudit` / `society_blueprint_audits` | Implemented | Trust/relationships/mutual aid/organization/institutions/businesses/property/community wealth/political power scores. |
| First Ten | `SocietyFirstTenMember` / `society_first_ten_members` | Implemented | Name/contact/status/role plus behavioral scores and notes. May optionally link to `users.id`. |
| Purpose Builder | `SocietyPurpose` / `society_purposes` | Implemented | Structured purpose inputs plus generated purpose statement and refinement prompt. |
| Covenant Builder | `SocietyCovenant` / `society_covenants` | Implemented | Covenant text, commitments, conflict practices, review rhythm, version/status. |
| First 100 Days container | `SocietyContainer`, `SocietyContainerMilestone`, `SocietyTrustTask` | Implemented MVP | Active container, milestones, trust-board tasks, handbook/chapter references, progress fields. |
| Role assignment workflow | `SocietyRoleOpening`, `SocietyRoleCandidateReview`, `SocietyRoleDiscussionNote`, `SocietyRoleAppointmentHistory` | Implemented MVP | Stores openings, fit review evidence, decision/development plan, discussion notes, appointments. |
| Mutual Aid fund runtime | `MutualAidFund`, contributions, requests, documents, reviews, decisions, disbursements, notifications, policy acceptances, audit logs, committees, conflicts, appeals, fraud reviews, reconciliation, budgets, vendors | Implemented operational foundation | This is a fund/request workflow, not society-specific yet. |
| App assessment storage | `LeadershipAssessment` | Implemented | Stores leadership assessment result records. New role workflow does not query this table. |
| App RBAC roles | `Role`, `UserRole`, `RolePermission`, plus `User.role` / `MemberProfile.role` elsewhere | Implemented | Separate from society roles and First Ten role labels. |

### Backend routes/APIs

- `/society-builder/societies` creates societies; `/society-builder/societies/me` lists user societies; `/society-builder/societies/main-hub` exposes the Simba main hub.
- `/society-builder/societies/{id}` reads/updates a society.
- `/society-builder/societies/{id}/apply-chapter` supports chapter application.
- `/society-builder/societies/{id}/blueprint-audit` and `/latest` persist and retrieve blueprint audit.
- `/society-builder/societies/{id}/first-ten` supports add/update/delete First Ten members.
- `/society-builder/societies/{id}/purpose` and `/covenant` save purpose/covenant records.
- `/society-builder/societies/{id}/advance-stage` changes lifecycle stage after eligibility checks.
- `/society-builder/societies/{id}/containers/first-100-days/activate` creates the First 100 Days container and tasks.
- `/society-builder/societies/{id}/containers/active`, `/trust-board`, `/trust-board/tasks`, `/trust-board/tasks/{id}`, and `/reader-reference` expose planner/task/handbook references.
- `/society-builder/societies/{id}/institutional-profile/me`, `/member-home`, and `/directory` support member home/profile/directory surfaces.
- `/society-builder/societies/{id}/role-assignment/...` supports dashboard, open roles, candidate suggestions, reviews, notes, decisions, and appointment history.
- `/society-builder/admin/...` supports chapter review, lifecycle override, and institutional-profile admin reads.
- `/mutual-aid/...` exposes fund request workflow, admin review, decision, appeal, disbursement, financial controls, analytics, readiness, security, documentation, and observability endpoints.

### Existing data flow

1. A user creates a society through the frontend formation page.
2. Backend creates `Society` and a founder `SocietyMembership`.
3. The society home can save blueprint audit, First Ten entries, purpose, covenant, and activate the First 100 Days container.
4. Activation creates a `SocietyContainer`, milestones, and `SocietyTrustTask` records.
5. Trust Board displays tasks grouped by lane/status and can update task status/owner fields.
6. Role assignment currently starts from manually-created `SocietyRoleOpening` records and First Ten member behavioral fields.
7. Candidate suggestions write `SocietyRoleCandidateReview` records.
8. Review decisions may write `SocietyRoleAppointmentHistory` and mark role openings appointed.

### Existing permissions

Society Builder routes are guarded by `society_builder:read_self`, `society_builder:update_self`, `society_builder:review_chapters`, `society_builder:override_stage`, or `admin:read_dashboard` depending on endpoint. The Mutual Aid fund runtime uses `mutual_aid:*` permissions such as request creation, admin review, decisions, disbursements, financial controls, analytics, security, compliance, and documentation.

### Existing progress/task/meeting systems

- Progress exists for the First 100 Days container through `current_day`, `current_week`, `percent_complete`, milestones, and trust-board task counts.
- Task records exist in `SocietyTrustTask` and have owner, lane, linked role/module/handbook fields.
- No dedicated Meeting Builder tables were found. Meeting concepts appear as handbook/role responsibilities and trust-board tasks, but not as persisted meeting agendas, minutes, attendance, decisions, or notes outside role discussion notes.
- No separate Rules Builder table was found beyond `SocietyCovenant` and handbook/governance documentation.
- No persisted Day 100 Report, Recommitment, or Next Phase Planner table/route was found.

## Existing archetype / role-fit intelligence capability map

| Capability | Existing files | Status | Notes |
|---|---|---|---|
| Role Blueprint Library | `src/data/mutualAidRoleBlueprints.js`, `src/pages/MutualAidRoleBlueprintLibraryPage.jsx`, `scripts/validateMutualAidRoleBlueprints.mjs` | Implemented frontend/static | Defines many society roles, purpose, responsibilities, archetypes, combined archetypes, traits, handbook connection points, recommended assessments. |
| Member Behavioral Profiles | `src/data/memberBehavioralProfiles.js` | Implemented frontend/static/sample | Provides named member examples with archetype evidence, behavioral confidence, completed assessments and traits. Not persisted. |
| Role Interpretation Engine | `src/data/roleInterpretationEngine.js` | Implemented frontend/static | Compares a profile to a role blueprint; returns alignment, confidence, evidence, missing assessments, growth path, mentor/team complements. |
| Role review screen | `src/pages/MutualAidRoleReviewPage.jsx` | Implemented admin preview/static | Lets admin select blueprint/profile and see interpretation. Not wired to real society role workflow. |
| Backend role assignment workflow | `backend/app/routes/society_builder.py`, `backend/app/models.py`, migration `20260630_role_assignment_workflow.sql` | Implemented persisted MVP | Candidate fit from First Ten scores/notes and role opening recommended assessments, then appointments/history. |
| Assessment Center API | `src/api/assessments.js`, `backend/app/routes/member.py`, `backend/app/routes/assessment.py`, `backend/app/routes/garvey.py` | Implemented elsewhere | Garvey/member assessment APIs exist, but role assignment does not integrate them directly. |
| Assessment result storage | `LeadershipAssessment` | Implemented for leadership assessment | Not normalized into role-fit evidence or First Ten candidate profiles. |

## Integration matrix

| Existing Feature | Existing Files | Current Status | Related New Intelligence Feature | Connection Status | Gap | Recommended Action |
|---|---|---|---|---|---|---|
| Start a Society / Society Builder | `src/pages/SocietyBuilderPage.jsx`, `src/pages/SocietyFormationPage.jsx`, `backend/app/routes/society_builder.py` | Implemented | Role Blueprint Library | Not connected at creation | Society type/focus does not propose starter role blueprint set. | Add post-create suggested role openings seeded from blueprint library by society type/focus. |
| Society Dashboard/Home | `src/pages/SocietyHomePage.jsx`, `backend/app/routes/society_builder.py` | Implemented | Role Assignment Workflow | Partial/not visible in main home | Role coverage/vacancies are not surfaced on society home. | Add role coverage card with vacancies, reviews, appointments, next review dates. |
| Name Your First Ten | `SocietyFirstTenMember`, First Ten routes/UI | Implemented | Member Behavioral Profiles, Role Interpretation | Partial | Backend uses behavioral scores, but not static profile schema, archetype evidence, or real assessment results. | Extend First Ten with optional linked user assessment snapshot and role-fit readiness indicators. |
| Treasurer Selection | Role blueprints + backend role openings | Partial | Treasurer blueprint and candidate review | Backend can review if role opening created manually | Not connected to treasury/fund setup or financial controls. | Seed Treasurer role opening and route appointment to treasury setup/financial controls permissions/checklist. |
| Care Team Lead Selection | Care Coordinator blueprint | Static/partial | Role Blueprint + candidate review | Not connected | No care-team table/workflow; needs are private in institutional profiles only. | Build care team entity after role coverage; connect Care Coordinator to private needs queue. |
| Facilitator Selection | Facilitator blueprint | Static/partial | Role Blueprint + candidate review | Not connected to meetings | No Meeting Builder. | Create meeting workflow or meeting task templates; require facilitator/recordkeeper assignment for recurring meetings. |
| Recordkeeper Selection | Recordkeeper blueprint | Static/partial | Role Blueprint + candidate review | Not connected to records/minutes | No meeting records/decision logs beyond tasks and role notes. | Add recordkeeping/minutes model or link role appointment to trust-board documentation lane. |
| Purpose Builder | `SocietyPurpose`, route `/purpose` | Implemented | Founder/Admin, Facilitator blueprints | Not connected | Purpose completion does not trigger role requirements. | Add purpose completion event/checklist recommending founder/admin/facilitator/recordkeeper review. |
| Covenant Builder / Rules | `SocietyCovenant`, route `/covenant` | Implemented | Conflict Mediator, Recordkeeper, Facilitator roles | Not connected | Covenant conflict practices not linked to role coverage or training. | Use covenant commitments to seed conflict mediator/facilitator role openings and training tasks. |
| 100-Day Planner / First 100 Days Container | `SocietyContainer`, `SocietyContainerMilestone`, `SocietyTrustTask`, `SocietyTrustBoardPage.jsx` | Implemented MVP | Role Assignment Workflow | Partial through task `linked_role` field only | No automatic role opening/review from task linked roles. | Generate/associate role openings from trust-board linked roles and use role coverage to unblock tasks. |
| Handbook reader | `First100DaysChapterReaderPage.jsx`, `src/data/societyContainerGuide.js`, `src/data/containers/first100DaysHandbookSource.js` | Implemented | Role blueprint handbook references | Partial/static | Blueprint handbook connections are frontend-only and not joined to active container tasks. | Normalize handbook chapter keys and link blueprint references to trust-board reader references. |
| Treasury / Ledger | `backend/app/routes/mutual_aid.py`, Mutual Aid fund models, `src/pages/MutualAidFinancialControlsPage.jsx`, `src/pages/LedgerPage.jsx`, `src/v2-ledger/*` | Implemented in separate systems | Treasurer/Assistant Treasurer | Not connected | Society roles do not grant or request mutual aid treasurer permissions; ledger not society-scoped. | Define society treasury setup workflow and map appointed treasurers to fund roles/RBAC with approval. |
| Needs Map | `SocietyInstitutionalProfile.needs_json`, profile/member home pages | Partial | Care Coordinator, Care Team roles | Not connected | Needs are stored per profile but no aggregate map, care-team queue, permissions, or role assignment link. | Build private needs map for care coordinators after permission model is hardened. |
| Skills & Assets Map | `SocietyInstitutionalProfile.contribution_categories_json`, `primary_contribution`, `skills_to_learn_json` | Partial | Role fit and mentor/team complements | Not connected | Directory groups categories but does not feed candidate review. | Feed institutional profile contributions/skills into role-fit evidence and complementary teammate suggestions. |
| Care Teams | Static references in roles/docs | Missing persisted workflow | Care Coordinator | Not connected | No model/routes/UI found for care teams. | Build after Needs Map and permissions. |
| Rules Builder | `SocietyCovenant` | Partial | Conflict/Facilitator/Recordkeeper | Not connected | Covenant stores rules-like content but no rules versioning/workflow separate from covenant. | Keep as covenant for now; add explicit rule sections before separate builder. |
| Meeting Builder | Static references/tasks only | Missing persisted workflow | Facilitator/Recordkeeper | Not connected | No meeting model/routes/UI. | Add meetings/minutes/actions module and connect roles. |
| First Action | First 100 Days task templates | Partial | Project Manager/Volunteer Coordinator | Weak | No explicit first-action report/completion object. | Tag a trust-board task/milestone as first action and require owner/role coverage. |
| Day 100 Report | Handbook/role references | Missing persisted workflow | Role coverage/reporting roles | Not connected | No report model/API/UI found. | Add Day 100 report generated from purpose, covenant, tasks, membership, role coverage, treasury summary. |
| Recommitment | Role blueprint mentions membership coordinator tracking recommitments | Missing | Membership Coordinator | Not connected | No recommitment route/table/UI. | Add after Day 100 report; use role history/vacancies to drive recommitment. |
| Next Phase Planner | Handbook references | Missing | Society Coordinator/Project Manager | Not connected | No next-phase model/UI. | Add after Day 100 report/recommitment. |
| Admin Review | `SocietyChapterAdminPage`, Mutual Aid admin review pages | Implemented in separate contexts | Role Assignment Workflow | Partial | Chapter review/admin mutual aid review separate from role review static preview. | Add admin society role coverage/readiness view; remove/rename static preview when real workflow UI exists. |
| Garvey assessment integration | `backend/app/routes/garvey.py`, `src/api/assessments.js`, member assessment endpoints | Existing elsewhere | Role Interpretation Engine | Not connected | Role fit uses manual completed labels/static profiles, not Garvey result contracts. | Define assessment evidence contract and mapper from Garvey/member results to role-fit evidence. |

## Duplicate / overlap findings

| Overlap | Files / Concepts | Recommendation | Rationale |
|---|---|---|---|
| App RBAC roles vs society roles vs First Ten role labels vs role openings | `Role`, `UserRole`, `SocietyMembership.role`, `SocietyFirstTenMember.role`, `SocietyRoleOpening.title`, `SocietyRoleAppointmentHistory.role_title` | Leave separate but document boundaries now; merge only where permission-granting is explicit | RBAC controls app permissions; society roles are local operating responsibilities; First Ten role is an early label. Do not collapse them, but create a glossary and crosswalk. |
| Static role-fit preview vs persisted backend role assignment | `MutualAidRoleReviewPage.jsx`, `roleInterpretationEngine.js`, backend role-assignment endpoints | Merge over time | Keep static preview as admin/design reference until real UI consumes backend workflow and real assessment evidence. Then deprecate static sample profile review. |
| Member Behavioral Profiles vs Society Institutional Profiles vs MemberProfile | `memberBehavioralProfiles.js`, `SocietyInstitutionalProfile`, `MemberProfile` | Merge evidence model, leave personal/profile surfaces separate | Static behavioral profiles should become an adapter/evidence view, not another member profile store. |
| Mutual Aid fund runtime vs Society Builder | `/mutual-aid/*` models/routes and `/society-builder/*` models/routes | Leave separate but integrate through society/fund association | Fund workflow is financial/request operations; Society Builder is local institution formation. Add optional `society_id`/fund association when ready. |
| Blueprint audit vs First 100 Days progress | `SocietyBlueprintAudit`, `SocietyContainer.percent_complete`, task counts | Merge at dashboard/reporting layer | Audit is institutional maturity; task progress is execution. Day 100 report should combine both. |
| Needs Map vs institutional profile needs | `needs_json`, `needs_privacy_level` | Keep existing profile fields; build care-team queue on top | Avoid duplicating needs storage before privacy/permissions are hardened. |
| Skills/assets map vs directory contribution categories | `contribution_categories_json`, directory groups | Keep and extend | Existing fields are a good seed for a skills/assets map. |
| Meeting notes vs role discussion notes vs trust-board task notes | `SocietyRoleDiscussionNote`, `SocietyTrustTask.completion_notes` | Leave separate; add meeting module | Role review notes and task completion notes should not become general meeting minutes. |
| Admin preview pages vs live admin pages | `MutualAidPilotPreviews.jsx`, Mutual Aid admin pages, role review static page | Deprecate later | Preview pages explicitly say not active and are useful for pilot messaging, but should be removed or hidden once live flows exist. |
| Ledger v1/v2 vs Mutual Aid treasury | `LedgerPage.jsx`, `src/v2-ledger/*`, Mutual Aid financial controls | Leave separate until product boundary is defined | STAR/member ledger appears separate from mutual aid fund accounting. Do not mix without accounting design. |

## Missing connections and missing features

### Missing connections

1. Role blueprint library is not used to seed backend `SocietyRoleOpening` records.
2. Static role interpretation is not used by persisted candidate reviews.
3. Backend role assignment does not query Garvey/member assessment result storage.
4. First Ten entries only optionally link to users; no onboarding flow invites linked users to complete assessments.
5. Institutional profile contribution/need/skill fields do not feed role-fit recommendations.
6. Society home does not surface role vacancies, role coverage, appointment history, or upcoming reviews.
7. Trust-board tasks have `linked_role`, but role vacancies do not block/unblock task readiness.
8. Treasurer appointments do not connect to Mutual Aid financial controls, fund permissions, budgets, reconciliation, or ledger surfaces.
9. Care Coordinator appointments do not connect to needs privacy, care teams, or care queues.
10. Facilitator/Recordkeeper appointments do not connect to a meeting/minutes workflow.
11. Role coverage is not included in Day 100 reporting because no Day 100 report exists yet.
12. Recommitment and Next Phase Planner are not persisted.
13. Admin chapter review and admin role-readiness review are separate.
14. Mutual Aid fund runtime is not society-scoped or linked to local society membership/roles.

### Missing features

- Dedicated Meeting Builder: agendas, attendance, minutes, motions/decisions, action items.
- Care Teams: team membership, private needs queue, assignments, follow-up, escalation.
- Needs Map and Skills/Assets Map as dedicated aggregate views with privacy controls.
- Day 100 Report persisted model/API/UI.
- Recommitment workflow.
- Next Phase Planner workflow.
- Treasury setup for societies, distinct from global Mutual Aid fund runtime.
- Role vacancy/coverage dashboard for society members and admins.
- Assessment evidence mapper from Garvey/member assessment results into role-fit evidence.
- Permission hardening for role-driven access changes, especially treasury and care.
- Role-assignment frontend consuming persisted backend workflow.

## Recommended next implementation phases

### Phase 1 — Connect role-fit review to Society Builder foundation

- Seed starter `SocietyRoleOpening` records from `mutualAidRoleBlueprints` for First Ten roles: Founder/Admin, Facilitator, Treasurer, Recordkeeper, Care Coordinator, Membership Coordinator.
- Add role coverage card to `SocietyHomePage` and a persisted Role Assignment UI route under `/societies/:societyId/role-assignment`.
- Map blueprint keys/titles/handbook chapters/recommended assessments into backend role openings.
- Keep all role recommendations non-deterministic and review-based.

Files/routes likely to modify next:

- `src/data/mutualAidRoleBlueprints.js`
- `src/api/societyBuilder.js`
- `src/pages/SocietyHomePage.jsx`
- new or existing role-assignment page under `src/pages/`
- `backend/app/routes/society_builder.py`
- `backend/app/services/society_builder.py`

### Phase 2 — Connect First Ten and assessments

- Link First Ten entries to registered users where possible.
- Add candidate evidence adapter that reads member/Garvey assessment results and produces role-fit evidence labels.
- Add missing-assessment CTAs in role candidate review and member onboarding.
- Preserve privacy: assessment results should be summarized, consented, and limited to role-review context.

Files/routes likely to modify next:

- `backend/app/routes/member.py`
- `backend/app/routes/assessment.py`
- `backend/app/routes/garvey.py`
- `backend/app/routes/society_builder.py`
- `src/api/assessments.js`
- `src/api/societyBuilder.js`

### Phase 3 — Connect role coverage to 100-Day Planner and handbook

- Use `SocietyTrustTask.linked_role` and blueprint handbook references to show “role coverage needed” on tasks.
- Add task templates for role-review moments: First Ten review, treasurer review before treasury setup, facilitator/recordkeeper before meetings, care coordinator before needs map.
- Normalize handbook chapter keys between role blueprints and First 100 Days guide entries.

Files/routes likely to modify next:

- `src/pages/SocietyTrustBoardPage.jsx`
- `src/data/societyContainerGuide.js`
- `src/data/containers/first100DaysHandbookSource.js`
- `backend/app/services/society_builder.py`
- `backend/app/routes/society_builder.py`

### Phase 4 — Connect Treasurer to treasury/fund setup

- Define society treasury setup separate from global Mutual Aid fund runtime, or add explicit `society_id` association to fund records after data design.
- Connect appointed Treasurer/Assistant Treasurer to financial controls checklist without automatically granting sensitive permissions.
- Add dual-control review and audit trail before permission changes.

Files/routes likely to modify next:

- `backend/app/models.py`
- `backend/app/routes/mutual_aid.py`
- `backend/app/routes/society_builder.py`
- `src/pages/MutualAidFinancialControlsPage.jsx`
- `src/pages/SocietyHomePage.jsx`

### Phase 5 — Build Meeting Builder and connect Facilitator/Recordkeeper

- Add meeting models/routes/UI for agenda, attendance, minutes, decisions, action items, and linked trust-board tasks.
- Require or recommend Facilitator and Recordkeeper coverage before recurring meetings.
- Feed meeting decisions into Day 100 report.

### Phase 6 — Build Needs Map/Care Teams and connect Care Coordinator

- Start from `SocietyInstitutionalProfile.needs_json` and `needs_privacy_level`.
- Add care-team membership, private needs queue, assignments, follow-ups, and escalation.
- Restrict access through explicit care-team roles/permissions and audit logs.

### Phase 7 — Day 100 Report, Recommitment, and Next Phase Planner

- Generate a persisted Day 100 Report from purpose, covenant, First Ten, membership/profile counts, task completion, role coverage, treasury readiness, care/needs readiness, and first action completion.
- Add recommitment workflow for members and role appointments.
- Add Next Phase Planner that turns gaps/vacancies into the next 90/100-day container.

### Phase 8 — Deprecate duplicates and harden permissions

- Replace static role review preview with live role-assignment review UI.
- Keep static blueprint library as a source/reference until backend blueprint catalog exists.
- Document role vocabulary boundaries and permission implications.
- Harden admin/member permissions for society-scoped private profiles, care needs, treasury controls, role review notes, and assessment summaries.

## Specific files/routes/models to modify next

### Backend

- `backend/app/models.py`: add or extend models for blueprint catalog, assessment evidence snapshots, meeting records, care teams, Day 100 report, recommitment, next phase planner, optional society-fund association.
- `backend/app/routes/society_builder.py`: add role-seeding, role dashboard, assessment evidence adapter, role coverage in society summary, task-role integration, Day 100 endpoints.
- `backend/app/services/society_builder.py`: centralize First 100 Days templates, stage eligibility, role-coverage checks, report generation.
- `backend/app/routes/member.py`, `backend/app/routes/assessment.py`, `backend/app/routes/garvey.py`: expose consented assessment summaries for role-fit review.
- `backend/app/routes/mutual_aid.py`: later connect treasury roles/funds only after society-fund boundary is designed.
- New migrations after design approval for any added persisted workflows.

### Frontend

- `src/pages/SocietyHomePage.jsx`: role coverage/vacancy/next review cards.
- `src/pages/SocietyTrustBoardPage.jsx`: show linked role readiness and connect role review CTAs.
- New `src/pages/SocietyRoleAssignmentPage.jsx` or extension of existing role review components to consume persisted backend APIs.
- `src/pages/SocietyMemberHomePage.jsx` and `src/pages/SocietyInstitutionalProfilePage.jsx`: show opt-in role readiness and assessment completion CTAs.
- `src/pages/MutualAidRoleBlueprintLibraryPage.jsx`: keep as reference; optionally add “seed this role” for admins/society founders.
- `src/pages/MutualAidRoleReviewPage.jsx`: deprecate or convert from static sample review to backend-driven review.
- `src/api/societyBuilder.js`: add missing role-assignment API client functions.
- `src/api/assessments.js`: add role-fit evidence summary calls after backend exists.

## Appendix: high-value source files inspected

- `backend/app/models.py`
- `backend/app/routes/society_builder.py`
- `backend/app/services/society_builder.py`
- `backend/app/routes/mutual_aid.py`
- `backend/app/routes/member.py`
- `backend/app/routes/assessment.py`
- `backend/app/routes/garvey.py`
- `backend/migrations/20260628_society_builder_foundation.sql`
- `backend/migrations/20260629_society_first_container.sql`
- `backend/migrations/20260630_role_assignment_workflow.sql`
- `src/api/societyBuilder.js`
- `src/api/assessments.js`
- `src/pages/SocietyBuilderPage.jsx`
- `src/pages/SocietyFormationPage.jsx`
- `src/pages/MySocietiesPage.jsx`
- `src/pages/SocietyHomePage.jsx`
- `src/pages/SocietyMemberHomePage.jsx`
- `src/pages/SocietyInstitutionalProfilePage.jsx`
- `src/pages/SocietyDirectoryPage.jsx`
- `src/pages/SocietyTrustBoardPage.jsx`
- `src/pages/First100DaysChapterReaderPage.jsx`
- `src/pages/MutualAidRoleBlueprintLibraryPage.jsx`
- `src/pages/MutualAidRoleReviewPage.jsx`
- `src/data/mutualAidRoleBlueprints.js`
- `src/data/memberBehavioralProfiles.js`
- `src/data/roleInterpretationEngine.js`
- `src/data/societyContainerGuide.js`
- `src/data/containers/first100DaysHandbookSource.js`
- `src/App.jsx`
