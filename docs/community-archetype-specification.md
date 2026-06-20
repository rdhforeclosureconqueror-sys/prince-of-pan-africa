# Community Archetype Specification

## Purpose and Boundary

This planning document defines how Simba should eventually interpret Garvey assessment evidence into Community Archetypes, contribution pathways, and growth recommendations. It does **not** implement the Community Contribution Engine, change Garvey scoring, change Garvey archetypes, or modify assessment logic.

Garvey remains the Observation Engine: it runs assessments, identifies assessment archetypes, and emits normalized evidence. Simba becomes the Interpretation and Development Engine: it combines evidence across assessments, identifies functional community alignment, and guides member development.

## Research Basis

The model extends the current Garvey-to-Simba integration already present in the repository and borrows community-role coverage from two stable community-development frameworks:

- Community Capitals Framework: resilient communities need balanced natural, cultural, human, social, political, financial, and built capital.
- Asset-Based Community Development: community growth begins with resident gifts, relationships, local associations, institutions, and connectors.

Those frameworks support expanding the initial archetype list beyond individual talents into a balanced community capacity map.

## Existing Garvey Evidence Inventory

Simba should start only from measurements already available or implied by current Garvey payloads and the existing leadership assessment data model.

### Active Assessment Sources

| Source | Current evidence available to Simba | Notes |
| --- | --- | --- |
| Garvey completion callback | assessment id/type/name, overall score, percentile, strengths, growth edges, primary result, archetype payload, recommendations, result URL, completion timestamp | Stored as `GarveySyncEvent.payload` and summarized into `MemberProfile.attributes.growth_profile` by the callback flow. |
| Official Garvey assessment catalog | Business Owner, Customer / Voice of Customer, Love Archetype, Leadership Archetype, Loyalty Archetype, Youth Rite of Passage / Gates, K-6 Assessment MVP | Simba filters remote catalog data to this official list before display. |
| Legacy local Leadership Assessment | role percentages, primary/secondary/growth/shadow roles, insights, coaching | This is an existing Simba-side assessment record and should be treated as legacy leadership evidence, not a new Garvey scoring change. |
| Participation / Community Labor Exchange | verified contributions, verifications completed, verification accuracy, trust score, leadership level, consistency streak | Use later as Simba-side contribution evidence, separate from Garvey assessment evidence. |

### Measurable Characteristics Already Available or Derivable

| Characteristic | Evidence source | Current status |
| --- | --- | --- |
| Leadership | Leadership Archetype Engine; local Leadership Assessment roles | Direct / existing |
| Initiative | Business Owner Assessment; Leadership Archetype Engine; strengths text | Inferred from existing assessment domains |
| Organization | Leadership Archetype Engine; Operator role | Direct / role-derived |
| Consistency | Loyalty Archetype Engine; Participation reputation consistency streak | Direct / existing Simba reputation field |
| Communication | Voice of Customer; Love Archetype Engine; Connector role | Direct / domain-derived |
| Empathy | Love Archetype Engine; Nurturer role | Direct / role-derived |
| Trust | Loyalty Archetype Engine; Participation trust score | Direct |
| Reliability | Loyalty Archetype Engine; Participation verified-contribution history | Direct / behavioral |
| Creativity | Builder role; Business Owner Assessment; strengths text | Role/domain-derived |
| Strategic Thinking | Architect role; Business Owner Assessment; Leadership Archetype Engine | Role/domain-derived |
| Resource Management | Business Owner Assessment; ResourceGenerator role | Domain/role-derived |
| Conflict Resolution | Love Archetype Engine; Voice of Customer; Protector/Connector roles | Domain/role-derived |
| Adaptability | Growth edges, recommendations, retake history, Builder/Operator roles | Inferred from existing evidence |
| Learning Agility | Youth Rite of Passage / Gates; K-6 Assessment MVP; assessment completion history | Domain/behavior-derived |
| Community Orientation | Connector, Steward, Nurturer, Educator roles; Participation labor | Role/behavior-derived |
| Planning | Business Owner Assessment; Architect/Operator roles | Domain/role-derived |
| Entrepreneurship | Business Owner Assessment; ResourceGenerator/Builder roles | Domain/role-derived |
| Listening | Voice of Customer; Love Archetype Engine | Domain-derived |
| Service | Voice of Customer; Participation labor | Domain/behavior-derived |
| Commitment | Loyalty Archetype Engine; consistency streak | Direct / behavior-derived |
| Protection | Protector role; Loyalty Archetype Engine | Role-derived |
| Teaching | Educator role; Youth/K-6 domains | Role/domain-derived |
| Caregiving | Nurturer role; Love Archetype Engine; Health-aligned strengths text | Role/domain-derived |
| Network Building | Connector role; Voice of Customer; Participation verification | Role/behavior-derived |
| Execution | Operator role; Builder role; Business Owner Assessment | Role/domain-derived |

## Deliverable 1: Community Archetype Catalog

Community Archetypes are functional contribution roles, not personality labels. A member can align with multiple archetypes, and Simba should present top alignments plus growth paths rather than assigning a permanent identity.

| Archetype | Community function | Community capital coverage |
| --- | --- | --- |
| Economic Builder | Creates businesses, jobs, investments, cooperative ventures, and sustainable wealth. | Financial, human, social |
| Knowledge Keeper | Preserves, teaches, researches, publishes, and shares knowledge. | Cultural, human |
| Community Organizer | Coordinates people, projects, volunteers, events, and mutual-aid activity. | Social, political, human |
| Agricultural Steward | Supports food systems, land care, sustainability, gardening, and environmental resilience. | Natural, built, cultural |
| Infrastructure Builder | Designs, builds, maintains, and improves physical or digital infrastructure. | Built, human, financial |
| Health Steward | Promotes physical, mental, family, and community wellness. | Human, social |
| Youth Mentor | Develops children, future leaders, rite-of-passage pathways, and educational systems. | Human, cultural, social |
| Cultural Guardian | Protects language, history, traditions, stories, arts, and identity. | Cultural, social |
| Diplomat | Strengthens communication, mediation, conflict resolution, and cooperation. | Social, political |
| Resource Steward | Manages finances, supplies, logistics, cooperative resources, and operational accountability. | Financial, built, social |
| Connector | Builds relationships between members, associations, partners, and opportunities. | Social, political |
| Safety Steward | Protects people, norms, spaces, data, and community trust. | Social, built, political |
| Learning Guide | Helps members choose lessons, assessments, practice plans, and reflection loops. | Human, cultural |
| Technology Steward | Maintains digital tools, data integrity, automation, accessibility, and member support systems. | Built, human |
| Mutual Aid Coordinator | Mobilizes support during member needs, crises, care gaps, and local emergencies. | Social, human, financial |

## Deliverable 2: Characteristic Library

| Characteristic | Definition | Evidence interpretation rule |
| --- | --- | --- |
| Leadership | Ability to guide people toward shared outcomes. | Use leadership score, leadership strengths, and leadership role percentages. |
| Initiative | Tendency to start needed work without waiting for direction. | Use business, builder, resource-generator, and strengths evidence. |
| Organization | Ability to structure work, people, time, and information. | Use Operator, planning, and business evidence. |
| Consistency | Ability to repeat useful behavior over time. | Use loyalty evidence, assessment history, and participation streaks. |
| Communication | Ability to express, listen, clarify, and coordinate. | Use Voice of Customer, Love, Connector, and Diplomat-related evidence. |
| Empathy | Ability to understand and respond to others' needs. | Use Love, Nurturer, Voice of Customer, and service evidence. |
| Trust | Evidence that others can rely on the member's word and conduct. | Use Loyalty and reputation evidence. |
| Reliability | Ability to complete commitments dependably. | Use Loyalty, verified contributions, and Operator evidence. |
| Creativity | Ability to generate useful new ideas or expressions. | Use Builder, Knowledge Keeper, Cultural Guardian, and business evidence. |
| Strategic Thinking | Ability to see systems, timing, risks, and long-range direction. | Use Architect, Leadership, and Business evidence. |
| Resource Management | Ability to manage money, supplies, assets, time, and logistics. | Use Business Owner, ResourceGenerator, Operator, and Resource Steward evidence. |
| Conflict Resolution | Ability to reduce tension and restore productive cooperation. | Use Love, Voice of Customer, Connector, Protector, and Diplomat evidence. |
| Adaptability | Ability to adjust when conditions change. | Use growth-edge closure over time, Builder, Operator, and recommendation completion. |
| Learning Agility | Ability to learn, apply, and improve. | Use assessment progression, Youth/K-6 domains where relevant, and Learning Guide evidence. |
| Community Orientation | Preference for contribution, mutual responsibility, and collective benefit. | Use Steward, Connector, Nurturer, Educator, Participation labor, and service evidence. |

## Deliverable 3: Characteristic-to-Archetype Matrix

| Archetype | Required characteristics | Supporting characteristics | Optional characteristics |
| --- | --- | --- | --- |
| Economic Builder | Initiative, Resource Management, Strategic Thinking | Leadership, Reliability, Communication | Creativity, Adaptability |
| Knowledge Keeper | Learning Agility, Teaching, Organization | Communication, Strategic Thinking, Consistency | Creativity, Cultural Stewardship |
| Community Organizer | Organization, Communication, Leadership | Reliability, Community Orientation, Conflict Resolution | Adaptability, Network Building |
| Agricultural Steward | Consistency, Resource Management, Community Orientation | Learning Agility, Reliability, Planning | Teaching, Adaptability |
| Infrastructure Builder | Execution, Organization, Reliability | Strategic Thinking, Resource Management, Adaptability | Creativity, Leadership |
| Health Steward | Empathy, Reliability, Communication | Community Orientation, Conflict Resolution, Consistency | Teaching, Learning Agility |
| Youth Mentor | Empathy, Teaching, Reliability | Leadership, Communication, Community Orientation | Cultural Stewardship, Creativity |
| Cultural Guardian | Cultural Stewardship, Teaching, Consistency | Communication, Creativity, Community Orientation | Strategic Thinking, Leadership |
| Diplomat | Communication, Conflict Resolution, Trust | Empathy, Listening, Strategic Thinking | Leadership, Adaptability |
| Resource Steward | Resource Management, Organization, Trust | Reliability, Strategic Thinking, Communication | Leadership, Consistency |
| Connector | Communication, Network Building, Listening | Empathy, Community Orientation, Trust | Service, Adaptability |
| Safety Steward | Trust, Reliability, Protection | Conflict Resolution, Organization, Leadership | Communication, Strategic Thinking |
| Learning Guide | Teaching, Learning Agility, Communication | Empathy, Organization, Consistency | Creativity, Youth Mentorship |
| Technology Steward | Execution, Organization, Learning Agility | Reliability, Strategic Thinking, Service | Creativity, Communication |
| Mutual Aid Coordinator | Empathy, Community Orientation, Organization | Reliability, Communication, Resource Management | Conflict Resolution, Adaptability |

## Deliverable 4: Assessment Evidence Matrix

Weights are planning placeholders for Simba interpretation only. They do not change Garvey scoring.

| Assessment / evidence source | Strongest characteristics evidenced | Archetypes most informed |
| --- | --- | --- |
| Business Owner Assessment | Initiative, Resource Management, Planning, Entrepreneurship, Strategic Thinking | Economic Builder, Resource Steward, Infrastructure Builder, Technology Steward |
| Customer / Voice of Customer | Listening, Service, Communication, Empathy, Conflict Resolution | Connector, Diplomat, Health Steward, Community Organizer, Mutual Aid Coordinator |
| Love Archetype Engine | Empathy, Communication, Conflict Resolution, Caregiving, Trust | Health Steward, Youth Mentor, Diplomat, Connector, Mutual Aid Coordinator |
| Leadership Archetype Engine | Leadership, Organization, Initiative, Strategic Thinking, Execution | Community Organizer, Economic Builder, Safety Steward, Infrastructure Builder, Resource Steward |
| Loyalty Archetype Engine | Trust, Reliability, Commitment, Consistency, Protection | Safety Steward, Resource Steward, Diplomat, Community Organizer, Mutual Aid Coordinator |
| Youth Rite of Passage / Gates | Learning Agility, Leadership, Responsibility, Cultural Orientation, Mentorship readiness | Youth Mentor, Learning Guide, Cultural Guardian, Community Organizer |
| K-6 Assessment MVP | Learning Agility, youth learning needs, foundational education signals | Youth Mentor, Learning Guide, Knowledge Keeper |
| Local Leadership Assessment roles | Architect, Operator, Steward, Builder, Connector, Protector, Nurturer, Educator, ResourceGenerator | All archetypes as secondary Simba-side evidence |
| Participation reputation | Consistency, Reliability, Trust, Service, Community Orientation | Community Organizer, Mutual Aid Coordinator, Connector, Safety Steward |

### Archetype Evidence Coverage Matrix

| Archetype | Primary assessment evidence | Secondary assessment evidence | Simba behavioral evidence |
| --- | --- | --- | --- |
| Economic Builder | Business Owner; Leadership | Loyalty; Voice of Customer | Builder Labor, Growth Labor |
| Knowledge Keeper | Leadership; Youth/K-6 | Voice of Customer; Love | Learning Labor, educational uploads |
| Community Organizer | Leadership; Voice of Customer; Loyalty | Love | Community Labor, verifications |
| Agricultural Steward | Business Owner; Leadership | Loyalty | Community projects, sustainability volunteer proof |
| Infrastructure Builder | Leadership; Business Owner | Loyalty | Builder Labor, bug reports, platform tests |
| Health Steward | Love; Voice of Customer | Loyalty | Mutual-aid and support contributions |
| Youth Mentor | Youth Rite of Passage; K-6; Love | Leadership; Loyalty | Mentorship and educational service proof |
| Cultural Guardian | Youth Rite of Passage; Leadership | Voice of Customer | Cultural uploads, study facilitation |
| Diplomat | Love; Voice of Customer; Loyalty | Leadership | Moderation, mediation, verification accuracy |
| Resource Steward | Business Owner; Loyalty; Leadership | Voice of Customer | Logistics, treasury, supply, and verification records |
| Connector | Voice of Customer; Love | Leadership; Loyalty | Welcomes, referrals, partner introductions |
| Safety Steward | Loyalty; Leadership | Love; Voice of Customer | Moderation, trust, verification accuracy |
| Learning Guide | Youth/K-6; Leadership | Love; Voice of Customer | Lesson completion support and study facilitation |
| Technology Steward | Leadership; Business Owner | Voice of Customer; Loyalty | Builder Labor, technical contribution proof |
| Mutual Aid Coordinator | Love; Voice of Customer; Loyalty | Leadership; Business Owner | Community Labor and crisis-support proof |

## Deliverable 5: Community Alignment Scoring Proposal

### Inputs

- `assessment_score`: normalized 0-100 score from Garvey where present.
- `characteristic_evidence`: normalized characteristic score derived from assessment-specific evidence.
- `confidence`: confidence based on source recency, number of assessments, directness of evidence, and agreement across sources.
- `behavioral_evidence`: optional Simba participation evidence; not a replacement for Garvey assessment evidence.

### Characteristic Score

For each characteristic:

1. Collect all evidence items mapped to that characteristic.
2. Normalize each evidence item to 0-100.
3. Apply source directness:
   - Direct Garvey metric or explicit strength: 1.0
   - Garvey domain inference: 0.75
   - Legacy leadership role evidence: 0.65
   - Simba participation behavior: 0.50
4. Apply recency decay after 180 days unless the assessment is intentionally long-lived.
5. Calculate weighted average and confidence.

### Archetype Alignment

For each archetype:

- Required characteristics: 60% of score.
- Supporting characteristics: 30% of score.
- Optional characteristics: 10% of score.
- Confidence modifier: display separately; do not hide low-confidence matches, but label them.

Example output:

```json
{
  "community_archetype": "Economic Builder",
  "current_alignment": 72,
  "confidence": 0.78,
  "strongest_traits": ["Leadership", "Initiative", "Strategic Thinking"],
  "growth_opportunities": ["Financial Systems", "Delegation", "Communication"],
  "evidence_count": 6,
  "last_updated": "2026-06-20T00:00:00Z"
}
```

### Current, Target, and Growth Needed

| Metric | Meaning |
| --- | --- |
| Current Alignment | Evidence-backed fit for an archetype today. |
| Target Alignment | Member-selected aspiration or Simba-recommended development target. |
| Growth Needed | Difference between target requirements and current characteristic evidence. |
| Contribution Readiness | Whether the member should be invited to observe, assist, lead with support, or lead independently. |

## Deliverable 6: Growth Pathway Framework

Each archetype pathway should include recommendations without hard-coding a single curriculum.

| Pathway section | Recommendation rule |
| --- | --- |
| Books | Map to archetype function and growth characteristics. |
| Audiobooks | Prefer accessibility and on-the-go study versions of the same topics. |
| Language lessons | Recommend languages or vocabulary tied to culture, diplomacy, business, agriculture, health, or youth education. |
| Courses | Select internal lessons first, then approved external courses. |
| Community groups | Recommend Simba groups or partner circles aligned with the archetype. |
| Volunteer opportunities | Match readiness level and local/online availability. |
| Next Garvey assessment | Use Garvey's own `recommended_next_assessment` when present; otherwise choose the next official assessment that closes the largest evidence gap. |

### Example Pathways

| Archetype | Books/audiobooks | Language lessons | Courses | Groups / volunteer opportunities | Next assessment rule |
| --- | --- | --- | --- | --- | --- |
| Economic Builder | Cooperative economics, entrepreneurship, accounting | Business Swahili, financial vocabulary | Business planning, cooperative finance | business circle, vendor directory, grant team | Business Owner or Leadership |
| Knowledge Keeper | history, research methods, publishing | archival terms, African language basics | documentation, oral history | library team, study circle | Leadership, Youth/K-6, or Voice of Customer |
| Community Organizer | organizing, facilitation, project management | meeting facilitation vocabulary | event coordination, volunteer management | welcome team, verification team | Leadership or Voice of Customer |
| Health Steward | wellness, trauma-informed care, nutrition | health vocabulary | mental health first aid, community wellness | care circle, wellness check-ins | Love or Voice of Customer |
| Diplomat | mediation, negotiation, communication | diplomacy vocabulary | conflict resolution | moderation team, partner liaison | Love, Loyalty, or Voice of Customer |
| Technology Steward | accessibility, secure systems, user support | technical vocabulary | platform testing, data stewardship | bug triage, documentation, support desk | Leadership or Voice of Customer |

## Deliverable 7: Community Contribution Engine Data Model

This is a future model proposal only.

### Entities

| Entity | Purpose | Key fields |
| --- | --- | --- |
| `assessment_evidence` | Immutable normalized evidence from Garvey callbacks. | id, user_id, source_event_id, assessment_id, assessment_name, completed_at, normalized_score, percentile, strengths, growth_edges, primary_result, archetype_payload, raw_payload_hash |
| `characteristic_score` | Current characteristic rollup. | id, user_id, characteristic_key, score, confidence, evidence_count, last_evidence_at, calculation_version |
| `community_archetype` | Static catalog of functional roles. | key, title, description, required_characteristics, supporting_characteristics, optional_characteristics, active |
| `member_archetype_alignment` | Current and historical alignment snapshots. | id, user_id, archetype_key, current_alignment, target_alignment, confidence, readiness_level, strongest_traits, growth_opportunities, calculated_at, calculation_version |
| `growth_pathway` | Recommendation bundle for an archetype/characteristic gap. | id, archetype_key, characteristic_key, books, audiobooks, languages, courses, groups, volunteer_opportunities, next_assessment_rule |
| `member_growth_plan` | Member-facing development plan. | id, user_id, target_archetype_key, selected_goals, recommended_actions, status, started_at, completed_at |
| `contribution_profile` | Combined view of assessment alignment and verified contribution behavior. | user_id, top_archetypes, contribution_history_summary, complementary_member_tags, updated_at |

### Data Principles

- Preserve raw Garvey payloads for auditability.
- Store normalized evidence separately from calculated Simba interpretations.
- Version every calculation so future scoring changes can be replayed safely.
- Keep Garvey archetypes and Community Archetypes separate fields.
- Allow multiple target archetypes per member over time.
- Never overwrite historical alignment snapshots; append new snapshots.

## Deliverable 8: Future API Contract Between Garvey and Simba

### Garvey to Simba Completion Event

```json
{
  "event": "assessment.completed",
  "issuer": "simba_wajuma",
  "member_id": "123",
  "member_email": "member@example.com",
  "assessment_id": "leadership-archetype-engine",
  "assessment_type": "leadership",
  "assessment_name": "Leadership Archetype Engine",
  "result_id": "garvey-result-123",
  "completion_status": "completed",
  "overall_score": 82,
  "percentile": 73,
  "strengths": ["decision making", "organization"],
  "opportunities_for_growth": ["delegation"],
  "primary_result": {"label": "Architect"},
  "archetype": {"name": "Architect", "strengths": ["systems thinking"]},
  "recommended_next_assessment": {
    "assessment_name": "Voice of Customer",
    "reason": "Improve communication evidence"
  },
  "recommendation_confidence": 0.88,
  "result_url": "https://garvey.example/results/garvey-result-123",
  "completed_at": "2026-06-20T00:00:00Z"
}
```

### Simba Response

```json
{
  "ok": true,
  "stored": {
    "assessment_id": "leadership-archetype-engine",
    "result_id": "garvey-result-123",
    "overall_score": 82
  },
  "interpretation_status": "queued"
}
```

### Future Simba Read APIs

| Endpoint | Purpose |
| --- | --- |
| `GET /member/community-archetypes` | Returns current top archetype alignments and confidence. |
| `GET /member/community-archetypes/{key}` | Returns evidence, strengths, gaps, and pathway for one archetype. |
| `POST /member/community-archetypes/target` | Lets a member select target archetype(s). |
| `GET /member/contribution-profile` | Returns alignment plus verified contribution behavior. |
| `GET /admin/community-intelligence/coverage` | Shows aggregate community capacity gaps without exposing private member details. |

## Implementation Guardrails for Later Phases

- Do not let Garvey assign Community Archetypes.
- Do not modify Garvey scoring, archetype names, or assessment logic.
- Do not use a single assessment to permanently label a member.
- Always display evidence and confidence with archetype recommendations.
- Prefer member agency: show “you may contribute as...” rather than “you are...”.
- Separate current contribution readiness from long-term aspiration.
- Keep sensitive youth and health evidence protected with stricter access controls.
