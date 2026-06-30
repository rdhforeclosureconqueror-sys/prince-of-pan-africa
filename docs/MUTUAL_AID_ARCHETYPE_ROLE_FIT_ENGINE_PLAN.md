# Mutual Aid Society Archetype and Role-Fit Engine Implementation Plan

## 1. Intent and Boundary

The Mutual Aid Society Archetype and Role-Fit Engine helps a Simba society interpret Garvey assessment evidence into role-fit guidance, growth pathways, and balanced team recommendations. The engine supports the existing 100-Day Mutual Aid Society Handbook; it does not redesign the handbook, rename its chapters, replace its sequence, or automatically appoint anyone to a role.

The engine follows this pipeline:

1. Assessment data from Garvey and existing Simba participation signals.
2. Unified archetype and behavioral member profile.
3. Role-fit comparison against Mutual Aid Society role blueprints.
4. Missing-assessment prompts and confidence guidance.
5. Growth pathway recommendations.
6. Complementary teammate and team-balance recommendations.

All language must remain developmental and empowering. Assessments are mirrors of current patterns, not permanent identity. The engine must never say a member is a bad fit, not qualified, unable to lead, or the wrong personality. It should say the member currently shows certain patterns, may naturally align with certain responsibilities, would benefit from strengthening specific practices, may need additional assessment evidence, or may be better supported with complementary teammates.

## 2. Source Systems and Garvey Assessment Inventory Integration

The engine should use Garvey as the assessment observation source and Simba as the interpretation and development layer. The current repository already stores Garvey callbacks with assessment identifiers, result IDs, scores, strengths, growth edges, primary results, archetype payloads, recommendations, result URLs, and completion timestamps. The first implementation should consume those stored Garvey results instead of changing Garvey scoring.

Official Garvey assessment domains to normalize into the engine:

| Garvey assessment | Engine use |
| --- | --- |
| Business Owner Assessment | Initiative, planning, resource management, entrepreneurship, strategic thinking, treasury/business liaison signals. |
| Customer / Voice of Customer | Listening, service, communication, empathy, connector, liaison, care, and communications signals. |
| Love Archetype Engine | Care, empathy, trust repair, conflict approach, care coordination, youth/elder support signals. |
| Leadership Archetype Engine | Leadership, organization, initiative, strategic thinking, execution, facilitation, coordination signals. |
| Loyalty Archetype Engine | Trust, reliability, commitment, consistency, protection, treasury and governance support signals. |
| Youth Rite of Passage / Gates | Mentorship, youth development, responsibility, cultural orientation, learning-guide signals. |
| K-6 Assessment MVP | Youth learning needs, teaching support, mentorship, learning-guide signals. |

Existing Simba-side evidence that can be added after the first Garvey-only pass:

- Legacy local leadership assessment role percentages.
- Participation / Community Labor Exchange verification records.
- Trust score, consistency streaks, verified contributions, and verification accuracy.
- Mutual-aid request fulfillment history.

## 3. Data Model Changes

### 3.1 Tables

Create these backend tables through additive migrations:

| Table | Purpose | Key columns |
| --- | --- | --- |
| `mutual_aid_role_blueprints` | Versioned role definitions for handbook and extended roles. | `id`, `role_key`, `role_name`, `role_group`, `purpose`, `responsibilities_json`, `best_fit_archetypes_json`, `helpful_combinations_json`, `trait_requirements_json`, `need_profile_json`, `recommended_assessments_json`, `missing_prompt_templates_json`, `growth_pathway_json`, `complementary_teammates_json`, `active`, `version`, `created_at`, `updated_at`. |
| `member_archetype_profiles` | Cached interpretation of a member's latest assessment evidence. | `id`, `user_id`, `society_id`, `completed_assessments_json`, `missing_assessments_json`, `primary_archetypes_json`, `secondary_archetypes_json`, `strongest_traits_json`, `growth_areas_json`, `style_profile_json`, `reliability_indicators_json`, `role_suggestions_json`, `roles_to_grow_into_json`, `evidence_snapshot_json`, `confidence_score`, `generated_at`, `expires_at`. |
| `member_role_fit_reviews` | Point-in-time role-fit report for a member and role. | `id`, `society_id`, `user_id`, `role_key`, `requested_by_user_id`, `overall_alignment`, `alignment_score`, `confidence_score`, `supporting_archetypes_json`, `strong_traits_json`, `development_traits_json`, `missing_assessments_json`, `suggested_assessments_json`, `suggested_training_json`, `practice_tasks_json`, `mentor_type_json`, `complementary_teammates_json`, `community_decision_note`, `created_at`. |
| `team_balance_reviews` | Group-level archetype and role-coverage report. | `id`, `society_id`, `team_type`, `team_name`, `member_ids_json`, `role_coverage_json`, `archetype_distribution_json`, `risks_json`, `strengths_json`, `recommendations_json`, `created_by_user_id`, `created_at`. |
| `assessment_interpretation_rules` | Configurable assessment-to-trait/archetype mapping. | `id`, `assessment_key`, `trait_weights_json`, `archetype_weights_json`, `role_relevance_json`, `minimum_confidence_rules_json`, `active`, `version`. |

### 3.2 Future Passport Placeholder

Do not implement the full Member Development Passport in this phase. Leave a `passport_ready_context_json` or equivalent reserved field in profile/review serialization only if needed, with no UI that presents a passport as complete.

### 3.3 Relationship to Current Garvey Storage

The engine should not duplicate raw Garvey results as authoritative records. It should read the existing assessment result history, normalize it into a temporary evidence snapshot, and cache only the interpreted profile and review outputs for speed, auditability, and role-discussion history.

## 4. Role Blueprint Structure

Each role blueprint should be data-driven and editable through migration seed data first, with admin editing later. Required blueprint shape:

```json
{
  "role_key": "treasurer",
  "role_name": "Treasurer",
  "role_group": "handbook_core",
  "purpose": "Protect and steward society funds with transparency, care, and disciplined recordkeeping.",
  "responsibilities": [],
  "best_fit_archetypes": [],
  "helpful_archetype_combinations": [],
  "required_behavioral_traits": [],
  "needs": {
    "trust": [],
    "reliability": [],
    "communication": [],
    "conflict": [],
    "documentation": [],
    "decision_making": [],
    "stress_tolerance": []
  },
  "recommended_assessments": [],
  "missing_assessment_prompts": [],
  "growth_pathway": [],
  "complementary_teammate_types": []
}
```

### 4.1 Core Handbook Roles

| Role | Purpose | Best-fit archetypes | Recommended assessments |
| --- | --- | --- | --- |
| Founder/Admin | Hold the early container, coordinate setup, maintain governance integrity. | Community Organizer, Safety Steward, Resource Steward, Connector. | Leadership, Loyalty, Voice of Customer, Business Owner. |
| Facilitator | Guide meetings, surface voices, maintain rhythm and clarity. | Diplomat, Community Organizer, Connector, Learning Guide. | Leadership, Voice of Customer, Love, Loyalty. |
| Treasurer | Steward funds, protect financial transparency, maintain controls. | Resource Steward, Safety Steward, Economic Builder, Operator. | Loyalty, Business Owner, Leadership, Voice of Customer. |
| Assistant Treasurer | Support treasury continuity, double-check records, share financial workload. | Resource Steward, Operator, Safety Steward. | Loyalty, Business Owner, Leadership. |
| Recordkeeper | Preserve decisions, attendance, minutes, tasks, and institutional memory. | Knowledge Keeper, Archivist, Operator, Documentation Lead. | Leadership, Voice of Customer, Loyalty. |
| Care Coordinator | Coordinate mutual-aid needs, care teams, follow-through, and member support. | Mutual Aid Coordinator, Health Steward, Nurturer, Connector. | Love, Loyalty, Voice of Customer, Leadership. |
| Business Liaison | Connect society members to business owners, co-ops, local commerce, and opportunity. | Economic Builder, Connector, Resource Steward. | Business Owner, Voice of Customer, Leadership. |
| Property Liaison | Track property needs, land/building possibilities, maintenance, and stewardship. | Infrastructure Builder, Resource Steward, Safety Steward. | Business Owner, Leadership, Loyalty. |
| Youth Liaison | Connect youth needs, learning supports, mentorship, and rite-of-passage work. | Youth Mentor, Learning Guide, Cultural Guardian, Health Steward. | Youth/Gates, K-6, Love, Leadership. |
| Preparedness Lead | Coordinate readiness, emergency planning, supplies, safety, and response drills. | Safety Steward, Mutual Aid Coordinator, Infrastructure Builder. | Loyalty, Leadership, Business Owner, Voice of Customer. |
| Elder Liaison | Protect elder voice, needs, care, dignity, and knowledge transfer. | Health Steward, Knowledge Keeper, Cultural Guardian, Connector. | Love, Voice of Customer, Loyalty. |
| Member | Participate, contribute, learn, and carry commitments at an honest capacity. | Any archetype with reliability and service evidence. | At least one core Garvey assessment plus recommended next assessment. |
| Supporter | Help with limited or flexible capacity while staying connected. | Connector, Nurturer, Knowledge Keeper, Builder. | Any relevant assessment; prompts should be optional and invitational. |

### 4.2 Extended 100-Day Process Roles

Seed extended role blueprints for Society Coordinator, Membership Coordinator, Conflict Mediator, Volunteer Coordinator, Project Manager, Community Organizer, Communications Lead, Technology Lead, Historian, Archivist, Teacher, Mentor, Health and Wellness Leader, Event Coordinator, Fundraising Lead, Transportation Coordinator, Food Distribution Coordinator, Emergency Response Coordinator, Neighborhood Captain, Committee Chair, Documentation Lead, Training Facilitator, and Assessment Facilitator.

These should follow the same schema. Extended roles can share archetype defaults:

- Coordination roles: Community Organizer, Operator, Connector, Resource Steward.
- Mediation roles: Diplomat, Health Steward, Safety Steward, Connector.
- Documentation/history roles: Knowledge Keeper, Cultural Guardian, Archivist, Operator.
- Teaching/training roles: Learning Guide, Youth Mentor, Knowledge Keeper, Cultural Guardian.
- Logistics/emergency roles: Safety Steward, Mutual Aid Coordinator, Infrastructure Builder, Resource Steward.
- Technology roles: Technology Steward, Infrastructure Builder, Learning Guide, Operator.
- Fundraising/business roles: Economic Builder, Resource Steward, Connector, Communications Lead.

## 5. Member Profile Structure

A generated member profile should include:

```json
{
  "member_id": "uuid-or-int",
  "society_id": "optional",
  "completed_assessments": [],
  "missing_assessments": [],
  "primary_archetypes": [],
  "secondary_archetypes": [],
  "strongest_traits": [],
  "current_growth_areas": [],
  "leadership_style": "...",
  "trust_style": "...",
  "loyalty_style": "...",
  "collaboration_style": "...",
  "communication_style": "...",
  "conflict_style": "...",
  "service_style": "...",
  "reliability_indicators": [],
  "role_suggestions": [],
  "roles_they_may_grow_into": [],
  "confidence_score": 0.0,
  "evidence_note": "This profile reflects current assessment evidence and can change as the member grows."
}
```

Style fields should be derived from the strongest assessment-backed traits and archetypes. If evidence is incomplete, say that additional assessment evidence would help the society understand the member's current patterns with more confidence.

## 6. Role-Fit Scoring Logic

Role-fit scoring should be explainable and confidence-aware.

### 6.1 Inputs

- Latest completed Garvey assessments by assessment key.
- Normalized archetype labels from Garvey and Simba community archetype mapping.
- Strengths, growth edges, primary results, recommendations, and scores.
- Optional Simba participation signals in a later phase.
- Target role blueprint.

### 6.2 Score Components

| Component | Weight | Description |
| --- | ---: | --- |
| Trait match | 35% | Match between member strongest traits and role required traits. |
| Archetype match | 25% | Match between member primary/secondary archetypes and role best-fit/helpful archetypes. |
| Assessment coverage | 20% | Whether recommended assessments for that role are completed. |
| Reliability/trust indicators | 10% | Loyalty, trust, consistency, verified contribution signals where available. |
| Growth-edge compatibility | 10% | Whether current growth areas are manageable for the role or need support. |

### 6.3 Alignment Labels

Use labels that inform without appointing:

- `strong_current_alignment`: Currently shows strong alignment for this responsibility.
- `promising_alignment_with_support`: May naturally align and would be better supported with complementary teammates or mentoring.
- `growth_pathway_alignment`: May grow into this role by strengthening named traits and completing specific practice tasks.
- `additional_evidence_needed`: Additional assessment needed before making a stronger role-fit recommendation.

Never use rejection labels.

### 6.4 Confidence Rules

- High confidence requires at least 75% of role-recommended assessments completed or strong equivalent evidence.
- Medium confidence requires at least 50% of role-recommended assessments completed.
- Low confidence means the engine can provide possibilities, but must foreground missing-assessment prompts.
- Sensitive roles like Treasurer, Founder/Admin, Preparedness Lead, and Conflict Mediator should require trust/reliability evidence before showing high confidence.

## 7. Missing-Assessment Prompt Logic

When a member is considered for a role and important evidence is missing, show:

> To better understand your fit for this responsibility, complete these assessments.

Each prompt must explain why the assessment matters. Examples:

- Treasurer: Trust/Loyalty helps the society understand reliability, commitment, and financial stewardship patterns; Business Owner helps assess resource-management and planning instincts; Leadership helps assess decision-making; Voice of Customer helps assess transparent communication.
- Care Coordinator: Love helps assess care, empathy, and relational repair patterns; Loyalty helps assess follow-through and trust; Voice of Customer helps assess listening and service; Leadership helps assess coordination under responsibility.
- Conflict Mediator: Love, Voice of Customer, Loyalty, and Leadership together help assess empathy, listening, trust repair, steadiness, and group guidance.

Prompt rules:

1. Only ask for assessments relevant to the role.
2. Prioritize missing assessments by role criticality.
3. If a member has already completed a closely related assessment, reduce urgency rather than duplicating pressure.
4. Use invitational language and explain the value to the member and community.

## 8. Growth Pathway Logic

Growth pathways translate role requirements into next practices. Every pathway should include:

- Traits to strengthen.
- Suggested training modules or handbook chapters.
- Practice tasks that can be done in low-risk settings.
- Suggested mentor type.
- Complementary teammate types.
- Reassessment or reflection moment.

Example for a member growing toward Treasurer:

1. Complete Loyalty and Business Owner assessments if missing.
2. Shadow the Treasurer for two reporting cycles.
3. Practice entering transactions in a sandbox ledger.
4. Review financial controls and conflict-of-interest norms.
5. Pair with a Recordkeeper or Assistant Treasurer for documentation support.
6. Revisit role-fit after the practice cycle.

## 9. Team Balance Logic

The team balance engine should analyze a society, board, committee, care team, or first-ten founding group.

### 9.1 Inputs

- Team member profiles.
- Assigned or proposed roles.
- Role blueprint coverage requirements.
- Archetype distribution.
- Missing assessment coverage.

### 9.2 Outputs

- Strong role coverage.
- Missing role coverage.
- Too many similar archetypes.
- Missing stabilizers.
- Missing documenters.
- Missing mediators.
- Missing executors.
- Missing connectors.
- Strong care culture.
- Weak follow-through risk.
- Strong vision but weak structure risk.

### 9.3 Risk Detection Examples

| Pattern | Interpretation | Recommendation |
| --- | --- | --- |
| Many vision/connector archetypes, few operators/documenters | Strong energy, possible weak structure risk. | Add Recordkeeper, Documentation Lead, Project Manager, or Operator-aligned teammate. |
| Many nurturers, low treasurer/resource evidence | Strong care culture, possible resource-control gap. | Add Resource Steward or Treasurer-aligned support. |
| Strong leaders, low mediators | High initiative, possible conflict strain. | Add Conflict Mediator or Diplomat-aligned teammate. |
| Strong emergency/safety roles, low connectors | Preparedness capacity, possible member engagement gap. | Add Membership Coordinator or Communications Lead. |

## 10. API Plan

Add endpoints under `/api/mutual-aid/archetype-engine` or equivalent:

| Method | Endpoint | Purpose | Permission |
| --- | --- | --- | --- |
| `GET` | `/role-blueprints` | List active role blueprints. | Society member or admin. |
| `GET` | `/role-blueprints/{role_key}` | View one role blueprint. | Society member or admin. |
| `POST` | `/members/{member_id}/profile/generate` | Generate or refresh member archetype profile. | Self, society coordinator, authorized admin. |
| `GET` | `/members/{member_id}/profile` | Read profile summary. | Self or authorized society leadership; respect privacy settings. |
| `POST` | `/members/{member_id}/role-fit/{role_key}` | Generate role-fit review. | Authorized role-selection group. |
| `GET` | `/members/{member_id}/role-fit` | List role-fit reviews visible to requester. | Self or authorized society leadership. |
| `POST` | `/teams/balance-review` | Analyze proposed team balance. | Society coordinator/admin/committee chair. |
| `GET` | `/societies/{society_id}/role-coverage` | Summarize current role coverage and assessment completion. | Society coordinator/admin. |
| `GET` | `/handbook-integration/{chapter}` | Return engine prompts for 100-day chapter integration. | Society member with chapter access. |

All generated reports should include `community_decision_note`: "This engine informs the society's discernment. The community makes the decision."

## 11. UI Plan

### 11.1 Member-Facing UI

- Assessment profile card: completed assessments, suggested next assessments, current archetype mirrors, strongest traits, growth areas.
- Role pathways card: roles the member may naturally align with and roles they may grow into.
- Growth pathway panel: practice tasks, mentor type, training suggestions.
- Privacy controls: member can see what is shared with role-selection groups.

### 11.2 Society Leadership UI

- Role blueprint browser for all core and extended roles.
- Candidate comparison view for a selected role.
- Missing-assessment prompt generator.
- Role-fit explanation drawer with strengths, growth areas, confidence, and complementary teammates.
- Team balance dashboard for first ten, board, committee, care team, or project team.
- Day 100 role coverage summary.

### 11.3 Handbook Integration UI

Do not edit the handbook content. Add contextual side panels, callouts, or optional widgets beside chapter workflows:

- "Use Archetype Engine" action.
- "Suggested member types" card.
- "Missing assessment evidence" card.
- "Team balance check" card.

## 12. 100-Day Integration Points

| Handbook point | Engine support |
| --- | --- |
| Chapter 5 — Name Your First Ten | Compare assessment profiles against early society needs; identify founders, documenters, care carriers, treasurers, connectors, and stabilizers. |
| Chapter 8 — Set the Treasury | Compare candidates against Treasurer and Assistant Treasurer blueprints; emphasize trust, reliability, documentation, and resource-management evidence. |
| Chapter 11 — Create Care Teams | Suggest members aligned with care coordination, empathy, follow-through, communication, and reliability. |
| Chapter 13 — Hold the First Meeting | Suggest Facilitator and Recordkeeper candidates based on meeting guidance, communication, documentation, and steadiness. |
| Chapters 14–15 — 100-Day Planner | For weekly tasks, show best-fit archetypes, recommended member types, missing role supports, and complementary teammates. |
| Chapter 21 — Day 100 Report | Include optional role coverage, team balance, missing roles, missing stabilizers, missing documenters, missing mediators, and assessment completion summary. |
| Chapter 22 — Recommitment | Use role-fit and growth data to help members recommit honestly to core, supporter, pausing, or new role pathways. |
| Chapter 23 — Next Phase Planner | Recommend role coverage needed for the selected next-phase goal and identify assessment gaps before scaling. |

## 13. Privacy and Permission Rules

1. Members can always view their own assessment-derived profile.
2. Society leaders can view only the minimum role-fit information needed for role discernment.
3. Raw Garvey result details should remain more restricted than interpreted summaries.
4. Sensitive assessment evidence should not be exposed to the whole society by default.
5. Role-fit reports should be visible to the member and authorized role-selection group.
6. Team balance reports should aggregate where possible and avoid exposing private growth edges unnecessarily.
7. Reports must carry the note that assessments are current mirrors, not permanent labels.
8. Members should have a way to refresh the profile after new assessments or growth work.
9. Audit who generated role-fit and team-balance reports.
10. Never automatically appoint, demote, remove, or reject a member based on the engine.

## 14. Phased Build Plan

### Phase 1 — Planning and Seed Data

- Add role blueprint seed data for all core handbook roles and extended 100-day process roles.
- Add assessment interpretation rules for current Garvey inventory.
- Add migrations for blueprints, cached profiles, role-fit reviews, and team-balance reviews.
- Add unit tests for blueprint validation and missing required fields.

### Phase 2 — Member Profile Generator

- Build service that reads Garvey assessment results and emits the member profile structure.
- Normalize completed and missing assessments.
- Map Garvey evidence into primary/secondary archetypes, strongest traits, growth areas, and style fields.
- Add self-view API and UI card.

### Phase 3 — Role-Fit Review Engine

- Implement role-fit scoring and confidence logic.
- Generate role-fit explanations, missing-assessment prompts, training, practice tasks, mentor types, and complementary teammate suggestions.
- Add candidate review UI for authorized society leaders.
- Add tests for empowering language guardrails.

### Phase 4 — 100-Day Handbook Side Panels

- Add optional widgets beside the relevant handbook chapters without rewriting handbook content.
- Add chapter-specific suggested member types and role coverage prompts.
- Add treasury, care team, first meeting, Day 100, recommitment, and next-phase planner integrations.

### Phase 5 — Team Balance Engine

- Build team-balance review API and dashboard.
- Detect missing stabilizers, documenters, mediators, executors, connectors, care capacity, follow-through risk, and vision-without-structure risk.
- Add first-ten and committee analysis flows.

### Phase 6 — Participation Evidence and Admin Tools

- Add optional Simba participation evidence into confidence and reliability scoring.
- Add admin tools for updating role blueprints and interpretation rules.
- Add audit exports and privacy review workflows.

## 15. Acceptance Criteria

- The system can generate a member archetype profile from completed Garvey assessments.
- The system can show missing assessments with role-specific explanations.
- The system can compare a member against all required core and extended role blueprints.
- The system can generate empowering role-fit explanations with growth pathways and complementary teammates.
- The system can analyze a team for role coverage and balance risks.
- The 100-day handbook remains unchanged, with only optional engine support added around the relevant chapters.
- No output automatically appoints or rejects a member.
- The architecture leaves room for a future Member Development Passport without building it in this phase.
