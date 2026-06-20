# Community Operations Framework

## Why this framework exists

Simba is becoming a Community Operating System. Learning, assessment, membership, and STAR participation help members grow, but Community Operations is where members practice unity through coordinated action.

Preparedness is the first proof: members can review resources, accept roles, track readiness, and build practical capacity together. The framework exists so future applications do not duplicate the same activity, role, resource, progress, dashboard, and STAR-instruction patterns.

## Preparedness as the first module

Community Preparedness is registered as the first live operations module. Its public route is `/community/preparedness`; `/preparedness` is preserved as a redirect for backward compatibility. Preparedness remains a working member-facing application and should not be treated as a disposable prototype.

## Reusable operational concepts

Each operations module should define:

- `key`
- `title`
- `description`
- `route`
- `status`
- `category`
- `icon` or visual marker
- member-facing CTA
- optional admin notes
- optional progress label
- optional STAR instruction hook

Shared concepts are intentionally small:

1. **Activity feed** — module key, activity type, actor/member, text, created date, visibility/privacy level, and metadata. Existing preparedness activity should be mapped into this shape rather than destructively renamed.
2. **Role / volunteer assignment** — role title, description, status, and assigned member or volunteer-needed state.
3. **Resource / inventory tracking** — resource name, current level/status, need state, and module-specific metadata.
4. **Progress / readiness** — a generic progress panel can display readiness, completion, fulfillment, growth, activation, or other module-specific progress. It must not create a new scoring engine.
5. **STAR instruction hook** — modules may declare an instruction hook that connects to the existing participation system. They must not create independent reward calculations.

## Future reserved modules

The registry reserves these modules as coming soon unless explicitly implemented:

- Community Projects
- Mutual Aid
- Volunteer Center
- Community Gardens
- Food Distribution
- Transportation Support
- Elder Care
- Emergency Response
- Community Chapters
- Community Funding

## Data boundaries

Do not destroy, rename, or migrate preparedness data in a way that breaks existing behavior. If generic tables or APIs are added later, compatibility mapping should allow preparedness-specific records to continue working until a safe migration exists.

Avoid risky migrations when the current system lacks a clean migration path. Prefer incremental adapters, typed registry objects, compatibility mappers, and module-specific services that can later move behind generic interfaces.

## STAR boundaries

Community Operations may trigger instructions or participation prompts for the existing STAR system. It must not change STAR reward calculations, duplicate-protection rules, verification behavior, or rank logic. New operation modules should use existing participation APIs and request explicit review before adding new STAR-awarding activity types.

## Garvey boundaries

Garvey observes and interprets business, personality, and assessment patterns. Simba organizes people into cooperative action. Community Operations is where members practice unity.

Do not place Community Operations logic inside Garvey. Do not make Garvey assign operations roles, readiness scores, or permanent member labels. Garvey can remain an observation engine; Simba remains the coordination system.

## Privacy principles

Operations activity should default to the least visibility required for coordination. Activity feed records should carry explicit visibility such as private, team, community, or admin. Health, household, elder-care, emergency, and location-sensitive data should be treated as sensitive and should not be exposed in broad community feeds by default.

## How to add a future module

1. Add a module definition to the operations registry.
2. Decide whether the module is `Available` or `Coming Soon`.
3. If live, add a route and page that uses shared operation components where they fit.
4. Map module activity into the shared activity feed shape.
5. Define roles and resources locally first; extract only when a second live module needs the same behavior.
6. Use the progress panel as display infrastructure only. Keep module scoring/fulfillment logic separate and explicit.
7. Declare a STAR instruction hook only if the existing participation system supports the action.
8. Document data, privacy, and compatibility assumptions before introducing backend migrations.

## What not to do

- Do not rewrite Preparedness as a different feature.
- Do not remove the current Preparedness page.
- Do not break `/preparedness` compatibility.
- Do not modify Garvey.
- Do not modify assessment scoring.
- Do not modify Community Archetype logic.
- Do not modify STAR calculations.
- Do not modify authentication or membership logic.
- Do not create fake live workflows for reserved modules.
- Do not over-componentize before at least two real modules need the same abstraction.
