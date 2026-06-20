# Simba Architecture Decision Framework

## Purpose

This document defines the architectural review process for every future feature proposed for the Simba wa Ujamaa ecosystem.

It is a planning and governance document. It does not create production code, runtime behavior, APIs, database tables, permissions, migrations, or user-facing features.

The framework exists to prevent Simba from becoming a platform that simply accumulates features. Every addition must make members, families, institutions, and communities more capable, more cooperative, and more self-sufficient than they were before.

Future developers, architects, AI assistants, and contributors should use this document before implementation begins. A feature proposal is not ready for engineering until it can satisfy the review questions, placement guidance, ethical review, technical review, and developer checklist below.

---

## Mission Alignment

Features are not added because they are interesting, fashionable, technically impressive, or easy to build.

Features are added because they strengthen the mission.

Every proposed feature must clearly strengthen one or more of these Simba pillars:

* Learning
* Character
* Cooperation
* Community
* Health
* Economic Opportunity
* Ownership
* Legacy

If a proposal cannot explain which pillar it strengthens, how it strengthens that pillar, and why Simba is the right place for it, the proposal should be paused, redesigned, moved to another platform, or rejected.

### Mission alignment test

A future feature proposal should answer:

1. What community need does this serve?
2. Which Simba pillar does it strengthen?
3. Which member lifecycle stage does it support?
4. How does it help members grow in capability rather than passive consumption?
5. How does it help communities become more cooperative or self-sufficient?
6. What would be weakened if this feature did not exist?
7. Could the same outcome be achieved through an existing Simba system?
8. Does this feature reinforce the Constitution, Operating Philosophy, Ecosystem Architecture, Member Lifecycle Architecture, Community Characteristics Framework, Community Archetypes, Development Pathways, Circle Engine, and Community Operations Framework?

---

## Feature Review Questions

Every proposed feature should include written answers to the following questions before implementation begins.

### Reason for existence

* Why does this feature exist?
* What member problem does it solve?
* What community problem does it solve?
* Is the problem recurring, mission-critical, and worth maintaining over time?
* Does the feature serve a real need or only create novelty?

### Lifecycle placement

* Which member lifecycle stage does this support?
* Does it help a visitor become a member?
* Does it help a member learn, contribute, lead, mentor, organize, build wealth, preserve culture, improve health, or leave a legacy?
* Does it create a clear next step in the member journey?
* Does it duplicate an existing pathway, dashboard, recommendation, activity feed, or STAR participation pattern?

### Cooperation and capacity

* Does it increase cooperation between members?
* Does it strengthen community capacity?
* Does it encourage contribution instead of isolated consumption?
* Does it create shared work, shared learning, shared accountability, or shared ownership?
* Does it strengthen families, circles, chapters, institutions, or community operations?

### Agency, privacy, and dignity

* Does it preserve member agency?
* Does it make recommendations without forcing decisions?
* Does it respect privacy and minimize data collection?
* Does it avoid permanent labels, hidden scoring, or manipulative nudges?
* Does it allow human review where judgment, sensitivity, or consequences are involved?

### Platform fit

* Does it require Garvey?
* Does it belong in Simba?
* Does it belong in PocketPT, Publishing, Investment Platform, Community Operations, Marketplace, or another platform?
* Can it be built from existing systems?
* Does it introduce a new engine that should instead be a module, adapter, view, or extension of an existing engine?
* Will it still make sense in twenty years?

---

## Architectural Placement

Architectural placement determines where a feature belongs, which system owns it, and which systems should only consume or display its outputs.

The first placement question is always:

> What is the feature's primary responsibility?

### Garvey

Place a feature in Garvey only when its primary responsibility is observation, assessment, interpretation of assessment evidence, or production of evidence for other systems.

Garvey may support:

* Assessments
* Assessment results
* Behavioral or business evidence
* Pattern observation
* Voice or input interpretation
* Evidence summaries that Simba can consume

Garvey should not own:

* Community operations workflows
* Member rewards
* STAR calculations
* Permanent identity labels
* Operations role assignment
* Community readiness scoring
* Marketplace transactions
* Social feeds
* Feature experiences whose primary job is coordination rather than observation

### Simba

Place a feature in Simba when its primary responsibility is member development, community coordination, lifecycle progression, recommendations, contribution pathways, community dashboards, or mission-aligned member experience.

Simba may support:

* Member lifecycle experiences
* Community characteristics
* Community archetypes as contribution models
* Development pathways
* Learning and contribution recommendations
* Community opportunities
* Circle participation
* Community dashboards
* STAR participation prompts through existing reward systems

Simba should not duplicate Garvey assessment logic, create independent reward engines, or become a container for unrelated feature ideas.

### PocketPT

Place a feature in PocketPT when its primary responsibility is health, fitness, wellness coaching, physical training, habit support, or health-related member guidance.

PocketPT features should still satisfy Simba ethical standards when connected to Simba, especially around privacy, consent, accessibility, recommendation clarity, and sensitive health information.

### Publishing

Place a feature in Publishing when its primary responsibility is books, essays, curricula, cultural material, educational media, authorship, editorial workflows, or distribution of knowledge products.

Publishing integrations may surface learning materials inside Simba, but the publishing system should own editorial and distribution workflows.

### Investment Platform

Place a feature in the Investment Platform when its primary responsibility is capital formation, investing, member ownership, financial participation, asset stewardship, or long-term economic opportunity.

Investment-related features require heightened review for fairness, transparency, legal compliance, financial risk, member understanding, and long-term stewardship.

### Community Operations

Place a feature in Community Operations when its primary responsibility is coordinated action: preparedness, mutual aid, volunteer work, roles, resources, operational readiness, local projects, elder care, emergency response, food distribution, transportation support, gardens, chapters, or other shared community work.

Community Operations should reuse shared operational concepts such as activity feeds, roles, resources, progress panels, readiness displays, and STAR instruction hooks rather than creating separate systems for each module.

### Marketplace

Place a feature in Marketplace when its primary responsibility is exchange: goods, services, listings, offers, member businesses, cooperative commerce, fulfillment, discovery, or economic matching.

Marketplace features should strengthen economic opportunity and ownership without weakening trust, fairness, privacy, or member agency.

### Separate platform

Create or use a separate platform when the proposed feature:

* Has a mission adjacent to Simba but not central to member development or community coordination.
* Requires a different legal, privacy, operational, financial, or technical model.
* Would overload Simba with unrelated workflows.
* Serves external users whose primary relationship is not the Simba community.
* Needs independent governance, branding, data boundaries, or risk controls.

When in doubt, document the placement decision, rejected alternatives, and the reason Simba is or is not the correct owner.

---

## Reuse First Principles

Future development should prioritize reuse before creating new systems.

### Reuse before invention

Before proposing a new component, API, database table, dashboard, feed, reward mechanism, or workflow, identify whether the outcome can be achieved using:

* Existing services
* Existing components
* Existing APIs
* Existing reward systems
* Existing dashboards
* Existing activity feeds
* Existing lifecycle stages
* Existing community characteristics
* Existing archetypes
* Existing development pathways
* Existing Community Operations concepts
* Existing documentation patterns

### Avoid duplicate systems

A feature should not create a duplicate system for:

* Rewards or STAR calculations
* Member identity or profile data
* Assessment scoring
* Community archetypes
* Lifecycle stages
* Activity feeds
* Operational roles
* Resource tracking
* Learning recommendations
* Dashboards
* Notifications or prompts
* Privacy visibility rules

Duplication is allowed only when there is a documented reason the existing system cannot meet the mission, privacy, technical, or governance requirement.

### Extract slowly

Do not over-generalize too early. Prefer module-specific implementation first when only one module needs a concept. Extract shared abstractions only after multiple real modules prove the same shape is needed.

---

## Member Impact

Every feature proposal must describe impact across four time horizons and beneficiary groups.

### Members

Explain how members benefit.

A strong proposal should show how the feature helps members:

* Learn something useful
* Build character
* Practice cooperation
* Improve health or stability
* Find economic opportunity
* Contribute to others
* Gain ownership or agency
* Progress through a meaningful lifecycle stage

### Communities

Explain how communities benefit.

A strong proposal should show how the feature helps communities:

* Coordinate action
* Build trust
* Increase participation
* Strengthen institutions
* Preserve culture
* Improve readiness
* Develop leaders
* Become less dependent on outside systems

### Institutions

Explain how institutions benefit.

A strong proposal should show how the feature helps schools, churches, chapters, local organizations, cooperatives, businesses, or civic institutions:

* Understand community needs
* Coordinate volunteers or resources
* Support member development
* Improve accountability
* Reduce duplicated effort
* Build durable operating capacity

### Future generations

Explain how future generations benefit.

A strong proposal should show how the feature contributes to:

* Transferable knowledge
* Intergenerational leadership
* Cultural preservation
* Durable ownership
* Stronger local institutions
* Long-term self-sufficiency
* A record of what the community built and learned

---

## Community Impact

Future features should be evaluated by how they affect trust, cooperation, capacity, contribution, and institutions.

### Community review questions

* Does this strengthen trust?
* Does this strengthen cooperation?
* Does this create dependency or capability?
* Does this encourage contribution?
* Does this strengthen institutions?
* Does this help members organize around shared work?
* Does this reduce fragmentation or create another isolated workflow?
* Does this make community progress visible without exposing sensitive information?
* Does this support circles, chapters, families, teams, or institutions in a practical way?
* Does this build the habit of shared responsibility?

### Dependency versus capability

A feature weakens the mission if it makes members dependent on the platform for things the community should learn to do itself.

A feature strengthens the mission if it teaches, coordinates, documents, or supports work in a way that leaves the community more capable even if the software changes later.

---

## Ethical Review

Every feature proposal must include an ethical review proportional to its risk.

### Consent

* What data or actions require consent?
* Is consent explicit, informed, and revocable where appropriate?
* Are members told what the feature does before they use it?

### Transparency

* Can members understand why they are seeing a recommendation, prompt, role, opportunity, or result?
* Are limitations clearly explained?
* Are automated outputs distinguishable from human judgment?

### Privacy

* What personal, household, health, financial, location, or sensitive community data is involved?
* Is the minimum necessary data collected?
* Who can see the data?
* What visibility levels are required?
* What should remain private, team-only, community-only, or admin-only?

### Fairness

* Could this feature exclude, disadvantage, mislabel, or overburden certain members?
* Does it work for members with different ages, abilities, income levels, literacy levels, technical access, and cultural contexts?
* Are appeal, correction, or human review paths needed?

### Accessibility

* Can members with disabilities use the feature?
* Can members with limited bandwidth or older devices participate?
* Is the language clear enough for non-technical members?

### Human review

* Does the feature affect opportunity, reputation, access, rewards, assessment interpretation, financial participation, health guidance, or sensitive community decisions?
* If so, where is human review required?

### Recommendation clarity

* Are recommendations presented as guidance rather than destiny?
* Are members free to disagree, choose another path, or request help?
* Are confidence, limitations, and sources made clear when appropriate?

### Data minimization

* Can the feature work with less data?
* Can data be aggregated, anonymized, summarized, or stored for a shorter period?
* Is every data element necessary for the mission outcome?

### Member dignity

* Does the feature avoid shame, surveillance, manipulation, or permanent negative labels?
* Does it respect members as whole people rather than data points?
* Does it encourage growth and contribution?

### Long-term stewardship

* What happens to the data, workflows, and community records in five, ten, or twenty years?
* Who is responsible for maintaining, correcting, archiving, or retiring them?
* Could future misuse harm members or communities?

---

## Technical Review

Technical review begins only after mission, placement, reuse, member impact, community impact, and ethical review are complete.

A feature proposal should identify:

* Existing reusable components
* Existing reusable services
* Existing reusable APIs
* Existing reward or STAR participation paths
* Existing dashboards or activity feeds
* Required integrations
* Data ownership boundaries
* Potential architectural conflicts
* Backward compatibility requirements
* Migration needs, if any
* Privacy and visibility requirements
* Testing strategy
* Documentation updates
* Rollback strategy
* Operational monitoring needs
* Support and maintenance ownership

### Architectural conflict review

Document whether the feature conflicts with:

* Garvey's role as observation engine
* Simba's role as development and coordination engine
* STAR reward boundaries
* Member lifecycle stages
* Community archetype boundaries
* Community Operations module patterns
* Existing privacy assumptions
* Existing dashboard or feed models
* Existing platform ownership boundaries

If a conflict exists, resolve it in planning before implementation.

---

## Developer Checklist

Before implementation, every feature proposal should include a completed checklist.

* Mission alignment
* Supported Simba pillar or pillars
* Member problem statement
* Community problem statement
* Lifecycle placement
* Platform ownership
* Garvey boundary review
* Simba boundary review
* STAR boundary review
* Privacy review
* Consent review
* Fairness and accessibility review
* Human review requirement, if any
* Reuse review
* Integration review
* Data ownership review
* Backward compatibility review
* Migration plan, if needed
* Testing plan
* Rollback strategy
* Documentation plan
* Support and maintenance owner
* Future extensibility notes
* Twenty-year relevance statement

A proposal that cannot complete this checklist is not ready for production implementation.

---

## Future-Proofing Guidelines

Simba is intended to support long-term community development, not short-term feature accumulation.

Future features should be designed so they can still make sense as members, families, chapters, institutions, and technologies change.

### Twenty-year review

Ask:

* Will this still support the mission in twenty years?
* Does it preserve knowledge for future members?
* Does it make the community more capable without requiring the original builders to explain it?
* Does it use language and concepts that can outlast current trends?
* Can it evolve without rewriting foundational architecture?
* Can it be retired without damaging member records, trust, or institutional memory?

### Extensibility principles

* Prefer clear ownership over hidden coupling.
* Prefer documented boundaries over implicit assumptions.
* Prefer adapters and compatibility layers over disruptive rewrites.
* Prefer member-understandable models over opaque automation.
* Prefer small, mission-aligned modules over broad, unfocused engines.
* Prefer evidence-based iteration over speculative abstraction.

---

## Implementation Guardrails

This document does not authorize implementation.

For this framework and for future proposals that use it, the following guardrails apply unless a later approved implementation plan explicitly changes them:

* Planning only until implementation is separately approved.
* No production code from this document alone.
* No runtime behavior from this document alone.
* No APIs from this document alone.
* No permissions from this document alone.
* No database tables from this document alone.
* No migrations from this document alone.
* No Garvey changes from this document alone.
* No Simba runtime changes from this document alone.
* No STAR changes from this document alone.
* No reward calculation changes from this document alone.
* No assessment scoring changes from this document alone.
* No member data collection changes from this document alone.

Future implementation proposals must explicitly state which guardrails remain in force, which systems are affected, and which approvals are required before engineering begins.

---

## Required Feature Proposal Format

Future proposals should use this repeatable format:

1. Feature name
2. One-paragraph summary
3. Mission pillar or pillars strengthened
4. Member problem solved
5. Community problem solved
6. Lifecycle stage supported
7. Platform placement decision
8. Systems reused
9. New systems requested, if any
10. Member impact
11. Community impact
12. Institutional impact
13. Future-generation impact
14. Ethical review
15. Technical review
16. Data and privacy review
17. Testing plan
18. Rollback plan
19. Documentation plan
20. Twenty-year relevance statement
21. Decision: approve for implementation planning, revise, move to another platform, or reject

---

## Final Principle

Simba should never become a platform that simply accumulates features.

Every addition should make the community more capable, more cooperative, and more self-sufficient than it was before.
