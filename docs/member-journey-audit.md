# Full Member Journey Audit

Date: 2026-06-15
Scope: Community Member and Builder journeys from landing page through membership selection, Stripe checkout, onboarding/activation, and dashboard command center.

## Executive Summary

The current experience has the right major building blocks: public landing, membership pages, Stripe checkout, billing return pages, onboarding flows, and a dashboard command center. The main cohesion gap is that the journey does not consistently route the member to the correct next step after payment or after partial onboarding.

The ecosystem feels strongest once the member reaches the dashboard, but several earlier handoffs create uncertainty:

- Community checkout success returns members to the dashboard instead of Community Onboarding.
- Builder checkout success attempts to route to Builder Activation, but Community Onboarding is not part of the Builder path even though builders inherit community participation.
- Landing page CTAs emphasize library, assessment, and account creation but do not clearly drive unauthenticated visitors into membership selection.
- Onboarding selections are stored and partially surfaced, but the selected learning path and selected builder lane do not yet change the dashboard's next recommended action.
- Discord is framed as pending/prepared rather than a clear join path, invitation expectation, or checklist.
- Dashboard daily actions are read-only and fixed at 0/4, which can make the command center feel like a dead end after the member asks, “What do I do next?”

## Current Journey Map

### Community Member Journey

1. Landing page
   - Public hero introduces the mission and links to Library, Dashboard for signed-in users, and Leadership Assessment.
   - Account panel lets a visitor create a free member account or sign in.
2. Membership selection
   - Membership overview explains Community and Builder plans and links to individual plan pages.
   - Community page has Stripe checkout, Community Onboarding preview, and Builder comparison links.
3. Stripe checkout
   - Checkout requires authentication; unauthenticated users are redirected to `/?auth=join`.
   - Backend creates Stripe Checkout with `/billing/success` and `/billing/cancel` return URLs.
4. Community onboarding
   - Community onboarding captures interests, first learning path, Discord preparedness, and first daily mission completion.
5. Dashboard command center
   - Dashboard shows daily actions, Swahili, history, community challenge, impact, learning path, feed, community onboarding summary, command updates, and builder participation if applicable.

### Builder Journey

1. Landing page
   - Same landing page as Community journey; Builder-specific path is not directly highlighted in the hero.
2. Membership selection
   - Builder page explains the role, benefits, participation examples, and Stripe checkout.
3. Stripe checkout
   - Billing success detects builder tier and auto-navigates to Builder Activation.
4. Builder activation
   - Builder activation captures introduction, interests, team, first community challenge, and first contribution.
5. Dashboard command center
   - Dashboard surfaces builder activation state, selected lane, interests, contribution history, feedback participation, and testing opportunities.

## Audit Findings

### 1. Dead Ends

#### Critical

- Community paid members are not routed into Community Onboarding after successful checkout. Billing success sends non-builder active members to `/dashboard`, where onboarding is shown only as a lower-page section. A new paying Community member may see many dashboard cards before the first required start path.
- The dashboard’s “Today’s Four Actions” checklist is read-only and always shows `Daily Progress: 0/4`. This creates a perceived dead end because the command center gives tasks but no way to complete or record them.
- The Community Challenge CTA says “Prepare Community Share” and anchors to an in-page feed, but there is no text box, copy action, Discord join, or submit action in the feed section.
- The Builder completion screen says to return to the dashboard to keep contributing, but the Builder dashboard card says activation is recorded and lists generic opportunities. It does not translate the selected team into a concrete next task.

#### Recommended

- Community onboarding preview on the Community membership page routes unauthenticated or unpaid visitors directly to `/community/onboarding`, which then redirects back to `/membership/community`. The label says “Preview,” but the route is gated like the real onboarding flow.
- Billing success inactive state says to refresh after Stripe finishes processing, but offers only “Check Dashboard.” If the webhook is delayed, the member may land in a free dashboard state without plan-specific guidance.

### 2. Missing Links

#### Critical

- Landing page lacks an obvious “Choose Membership” CTA in the hero/account flow. The homepage CTA row links to Library, Dashboard, and Leadership Assessment, but not to `/membership` or the two plan pages.
- Builder membership page does not link to Builder Activation as a preview or explain that paid builders will be taken there after checkout.
- Dashboard does not provide a clear Discord join/prep link or expected next state even though Discord appears in onboarding and command updates.

#### Recommended

- Global navigation for signed-out visitors only shows “Sign In.” It should include Membership or Join options so visitors are not forced to infer the path from the homepage account panel.
- Dashboard learning path card links only to `/library`, not to a path-specific destination aligned with the onboarding selection.

### 3. Missing Next-Step Guidance

#### Critical

- After account creation, the homepage sets status to “Member account created” but does not tell the user to choose a paid plan, start checkout, or go to membership selection.
- Community onboarding completion says “keep using the dashboard,” but the dashboard does not clearly prioritize the member’s selected path as the next action.
- Builder activation asks for a first contribution and optionally whether it has already been delivered. After completion, the dashboard does not say whether to complete, submit, or report that contribution.

#### Recommended

- Membership plan pages describe benefits but do not show a “Then what happens?” sequence: sign in/create account → Stripe checkout → onboarding/activation → dashboard daily mission → Discord/community participation.
- Billing cancel page gives a restart path but does not preserve which plan was canceled.

### 4. Duplicate Onboarding Questions

#### Recommended

- Community onboarding captures learning interests, while Builder activation captures builder interests. Builders therefore may answer a mission-interest question twice if they also complete Community Onboarding.
- Builder first community challenge overlaps with Community onboarding’s first daily mission and dashboard’s community challenge. The language differs, but the mental task is similar: do a first public/community action.

### 5. Dashboard Sections That Do Not Connect to Onboarding Choices

#### Critical

- Community selected learning path is surfaced only in the Community Onboarding summary, while the main “Today’s Learning Path” uses a date-rotating static list instead of the saved selection.
- Community selected interests are summarized but do not filter dashboard cards, feed prompts, or next recommended actions.
- Builder selected team is displayed as a raw team id, but testing opportunities remain generic and do not change by team.

#### Recommended

- Builder interests are displayed under Selected Builder Lane but do not affect the testing opportunities, contribution history prompt, or dashboard section order.
- Discord preparedness is saved in Community Onboarding but not surfaced on the dashboard as a status, invitation checklist, or pending join step.

### 6. Learning-Path Selections Not Surfaced Later

#### Critical

- The selected learning path from Community Onboarding is saved and returned by the backend, but the dashboard’s primary learning-path card ignores it and instead selects from a separate static rotation.
- Learning path ids (`foundations`, `history`, `language`, `economics`) do not map to concrete dashboard destinations. Members who picked “Swahili Foundations” should see the Swahili card prioritized and a direct practice link; members who picked “Community Economics” need a visible economics next step.

### 7. Builder Team Selections Not Surfaced Later

#### Critical

- Builder team selection is stored in `builder_activation.team` and shown on the dashboard, but as an id without a role-specific next action.
- Builder testing opportunities are the same for every builder and do not correspond to Learning Path Team, Community Welcome Team, Testing & Feedback Team, or Outreach Team.

### 8. Missing Discord Preparation / Join Flow

#### Critical

- Discord status exists in the backend overview as `discord_status`, but Community Onboarding only stores `discord_prepared`, and the dashboard does not show either as an actionable member-facing flow.
- Copy says Discord integration is pending/planned in multiple places. This is honest, but it should still tell members exactly what to do now: create Discord account, use same email, wait for invite, watch dashboard status, and prepare first post.

#### Recommended

- Builder page promises “Builder-focused discussions and channels,” but the activation and dashboard do not include channel preparation, invitation timing, or what to post first.

### 9. “What Do I Do Next?” Risk Points

Highest-risk moments:

1. After creating a free account on the landing page.
2. After unauthenticated checkout attempt redirects to account creation.
3. After successful Community checkout.
4. After inactive/delayed Stripe billing success.
5. After Community Onboarding completion.
6. After Builder Activation completion.
7. On the dashboard after seeing read-only daily actions and static feed placeholders.
8. After choosing a learning path or builder team but seeing no tailored next task.
9. When Discord is referenced but no invite/join path exists.

## Critical Fixes

1. Route successful Community checkout to Community Onboarding, not generic dashboard.
2. Add a homepage membership CTA and make the unauthenticated journey explicitly: create account → choose membership → checkout → onboarding.
3. Replace read-only dashboard daily checkboxes with either actionable links or copy that says exactly how to complete each action in the current release.
4. Make the dashboard primary learning-path card use the saved Community Onboarding learning path before falling back to date rotation.
5. Map builder team ids to human labels and team-specific next actions in the Builder Participation dashboard card.
6. Add a Discord preparation/status card on the dashboard using `discord_status` and `discord_prepared`.
7. Add a post-checkout delayed-payment fallback that returns the user to billing status or plan-specific onboarding once active.

## Recommended Fixes

1. Add a “What happens next?” section to both membership plan pages.
2. Change “Preview Community Onboarding” to either a true ungated preview or a clearer paid-member label.
3. Consolidate Community interests and Builder interests for builders, or prefill Builder Activation from Community Onboarding selections.
4. Clarify the difference between Community first daily mission, Builder first community challenge, and dashboard community challenge.
5. Add a dashboard “Next Best Step” banner that changes based on membership state:
   - free account: choose membership
   - paid Community, not onboarded: start Community Onboarding
   - paid Community, onboarded: continue selected path
   - paid Builder, not activated: start Builder Activation
   - activated Builder: complete team-specific contribution
6. Add plan context to billing cancel/success pages so restart CTAs go back to the same selected plan when possible.
7. Add route-level guidance when onboarding routes reject the user for missing membership, explaining that checkout is required.

## Nice-to-Have Improvements

1. Add a journey progress strip across membership, billing success, onboarding, and dashboard.
2. Add “copy my first Discord post” templates based on the selected learning path or builder team.
3. Add dashboard card ordering based on onboarding choices.
4. Add a small “Why this card?” explanation for each dashboard section tied to selected interests.
5. Add a member-facing activity history that distinguishes saved onboarding, completed onboarding, challenge prepared, and challenge submitted.
6. Add builder lane badges instead of raw team ids.
7. Add a “resume where you left off” deep link for partial Community Onboarding and Builder Activation.

## One Connected Ecosystem Recommendation

Treat every journey step as part of one state machine:

- Visitor: learn mission, create account, choose plan.
- Free member: select membership or continue public resources.
- Paid Community member: complete Community Onboarding.
- Onboarded Community member: follow selected learning path and daily mission.
- Paid Builder member: complete Builder Activation.
- Activated Builder: follow team-specific contribution path.
- Discord pending: prepare account and first post.
- Discord connected: join community space and share daily/weekly participation.

The immediate product goal should not be new systems. It should be clearer routing, labels, and state-aware dashboard guidance so every screen answers: “Here is where you are, here is what you already chose, and here is the next useful action.”
