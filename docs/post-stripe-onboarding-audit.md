# Post-Stripe Onboarding Audit

Status: Recommended roadmap before adding new platform features.

## Journey reviewed

1. Landing Page
2. Membership Selection
3. Checkout
4. Account Creation
5. Dashboard
6. Discord Access
7. Community Participation

## Current-state observations

### Landing Page

- The landing page explains the platform as a home for member onboarding, admin operations, learning, and leadership training.
- The primary calls to action point users toward the library, leadership assessment, dashboard when authenticated, and the inline account form.
- There is no clear first-time member path that says: choose a membership, complete checkout, create an account, complete orientation, join Discord, and make a first contribution.

### Membership Selection

- The membership overview presents Community and Builder plans with mission framing, benefits, and plan detail pages.
- Community and Builder plan pages can start Stripe checkout.
- The plan pages describe orientation materials, Builder participation, discussions, testing, feedback, outreach, and community development, but they do not show a concrete post-payment sequence.

### Checkout

- Checkout redirects authenticated users to Stripe through the billing checkout endpoint.
- If checkout receives a 401, the user is sent to the landing page account form with `auth=join`.
- The current flow requires account creation before checkout, but this dependency is implied by behavior rather than explained before the user clicks a paid membership button.

### Account Creation

- Account creation lives on the landing page as a simple email/password join form.
- After account creation, the user remains on the landing page with a success status and has to decide where to go next.
- There is no account-created welcome screen, membership selection recovery step, or checkout resume prompt.

### Billing Return

- The billing success page verifies subscription status and sends active users to the dashboard.
- The billing cancel page sends users back to membership options.
- The success page does not explain the onboarding sequence after payment, Discord access, orientation, Builder activation, contribution tracking, or support/retry steps.

### Dashboard

- The member dashboard shows membership status, membership type, orientation status, Discord status, community updates, activity, and Builder participation blocks.
- Orientation and Discord are status labels only. There is no action to begin orientation, connect Discord, claim a role, or request help.
- Builder Members can see testing opportunities, contribution history, and feedback participation, but there is no activation checklist, task claim flow, feedback form, contribution submission flow, or contribution ledger entry point.

### Discord Access

- Discord integration is documented as planning only and explicitly not implemented in the current phase.
- Planned future dashboard features include a Connect Discord action, Discord connection status, role status, and channel access instructions.
- Because the dashboard displays Discord status today, members may expect a working Discord join path that is not available yet.

### Community Participation

- Community participation is described in the membership pages as discussions, updates, learning paths, support for the mission, and Builder participation.
- The live dashboard does not give new Community Members a first community action.
- The live dashboard does not give new Builder Members a guided first Builder action.
- Activity tracking exists for logged backend activity, but the empty state points to starting a lesson, sharing a post, or logging a workout without providing clear buttons to do those actions.

## Missing onboarding steps

1. **Pre-checkout account requirement explanation**
   - Users need to know whether they should create an account before paying.
   - Add a short “How joining works” sequence to membership pages: create account, choose plan, pay with Stripe, land on dashboard, finish orientation, join Discord.

2. **Checkout recovery path**
   - If a visitor clicks a membership checkout button before signing in, the redirect to account creation should preserve the selected plan.
   - After account creation, prompt the user to continue the selected plan checkout.

3. **Post-payment onboarding page**
   - The billing success route should not only verify access. It should introduce the next steps and send the user into orientation.

4. **Member onboarding checklist**
   - Dashboard should show a persistent checklist until completed:
     - Verify membership status.
     - Complete welcome/orientation.
     - Join Discord or request Discord invite.
     - Open foundational learning path.
     - Make first community action.
     - For Builders: choose first Builder track.

5. **Support and failure states**
   - Add clear support actions when billing status is pending, Discord is not connected, role sync fails, or dashboard access is denied.

## Missing welcome flow

Recommended welcome flow:

1. **Welcome screen after account creation**
   - Message: “Your account is ready. Choose your membership to activate access.”
   - Actions: Community checkout, Builder checkout, compare plans, sign out.

2. **Welcome screen after successful billing**
   - Message: “Membership active. Start orientation.”
   - Show membership type and explain what unlocks now.
   - Actions: Start orientation, open dashboard, join Discord once available.

3. **Welcome email**
   - Send plan-specific welcome email after Stripe webhook confirms active subscription.
   - Include dashboard link, orientation link, Discord instructions, and support contact.

4. **In-dashboard welcome card**
   - Display for new members until orientation is complete.
   - Explain what to do in the first 10 minutes, first day, and first week.

## Missing orientation flow

Recommended orientation flow:

1. **Orientation route**
   - Add `/onboarding` or `/orientation` for authenticated members.
   - Gate it by membership status and display progress.

2. **Orientation modules**
   - Mission and expectations.
   - Membership type overview.
   - How to use the dashboard.
   - Foundational library starting point.
   - Discord/community conduct.
   - Builder track selection for Builder Members.

3. **Completion tracking**
   - Store orientation status as `not_started`, `in_progress`, or `completed`.
   - Update dashboard status and unlock the next suggested action.

4. **First-session success moment**
   - After completion, show a clear next action:
     - Community Member: introduce yourself in Discord or start foundational text.
     - Builder Member: choose a Builder track and submit first feedback/test interest.

## Missing Discord join flow

Recommended Discord join flow:

1. **Before Discord automation is ready**
   - Replace passive `not_connected` status with a “Discord access coming soon” or “Request invite” card.
   - Avoid implying live Discord access if bot/OAuth and role sync are not implemented.

2. **Minimum viable Discord flow**
   - Dashboard button: Connect Discord.
   - OAuth callback or invite-code confirmation.
   - Store Discord user ID and sync status.
   - Show assigned role and channel instructions.

3. **Stripe-to-Discord role sync**
   - Community subscription assigns Community role.
   - Builder subscription assigns Builder role plus baseline Community access.
   - Failed sync creates a retry state and support/admin action.

4. **Discord onboarding content**
   - Show rules, channel map, introduction prompt, and first community action.
   - Provide a non-Discord fallback for members who do not use Discord.

## Missing Builder activation flow

Recommended Builder activation flow:

1. **Builder welcome card**
   - Show only to Builder Members.
   - Explain that Builder status is a participation role, not only a content tier.

2. **Builder track selection**
   - Let Builders choose one or more tracks:
     - Onboarding tester.
     - Library/foundational text reviewer.
     - Discord/community organization feedback.
     - Outreach support.
     - Product feedback.
     - Local needs and opportunities.

3. **First Builder task**
   - Provide a small starter task that can be completed in under 10 minutes.
   - Examples: review onboarding, submit one issue, vote on Discord channel structure, test a learning path.

4. **Builder contribution submission**
   - Add entry points to submit feedback, report a bug, propose a community need, or log outreach.

5. **Recognition and history**
   - Populate contribution history from submitted Builder actions.
   - Show what was submitted, current status, and impact.

## Missing contribution tracking entry points

Recommended entry points:

1. **Dashboard quick actions**
   - Submit feedback.
   - Report onboarding issue.
   - Log community introduction.
   - Log learning milestone.
   - Log outreach/referral.
   - Claim Builder task.

2. **Contextual activity capture**
   - Library: mark foundational text started/completed.
   - Orientation: mark modules complete.
   - Discord: mark introduction complete.
   - Builder: submit test result or feedback.

3. **Activity model expansion**
   - Add typed actions such as `orientation_completed`, `discord_connected`, `introduction_posted`, `builder_task_claimed`, `builder_feedback_submitted`, and `learning_path_started`.

4. **Member-visible ledger**
   - Show a contribution timeline that explains what counts and what the member should do next.

## Confusion and drop-off risks

1. **Landing page does not route first-time paid members clearly**
   - A new user may create an account and not understand that membership payment is still required.

2. **Membership checkout requires auth without pre-explaining it**
   - Clicking checkout while signed out sends the user to the join form, but the selected plan context is lost.

3. **Billing success sends users straight to dashboard without orientation**
   - Users may see status cards but no guided next step.

4. **Orientation and Discord statuses look incomplete but unactionable**
   - `not_started` and `not_connected` can create anxiety if no action is available.

5. **Discord is planned only, but dashboard exposes Discord status**
   - This can make members expect an invite or role sync that does not exist yet.

6. **Builder benefits imply participation, but there is no participation workflow**
   - Builder Members may pay more and then find no task board, feedback form, Discord channel, or contribution path.

7. **Contribution history starts empty with no way to contribute**
   - Empty contribution history should include a call to action.

8. **Activity empty state mentions actions without direct links**
   - New members are told to start a lesson, share a post, or log a workout, but those entry points are not directly available from the dashboard.

## Recommended onboarding roadmap before new platform features

### Phase 1: Clarify the join-to-checkout path

- Add a “How joining works” section to the membership overview and plan pages.
- Preserve intended plan when signed-out users are redirected to account creation.
- After account creation, show a continue-checkout prompt for the selected plan.
- Update checkout error states with support and retry guidance.

### Phase 2: Add post-payment welcome and onboarding checklist

- Convert billing success into a welcome handoff when subscription is active.
- Add dashboard onboarding checklist with completion states.
- Add welcome card for first-session members.
- Add clear pending states when Stripe has not fully confirmed access.

### Phase 3: Build orientation foundation

- Create `/orientation` route for authenticated members.
- Add core orientation modules and completion tracking.
- Update dashboard orientation status through real backend state.
- Add first-session completion event to activity history.

### Phase 4: Implement safe Discord access path

- If Discord is not ready, label it as coming soon or request-only.
- Build Discord connect/request-invite flow.
- Store Discord connection and sync state.
- Add role/channel instructions after connection.
- Add admin retry/support path for failed sync.

### Phase 5: Activate Builder participation

- Add Builder activation card and track selection.
- Add first Builder task flow.
- Add Builder feedback and issue submission forms.
- Populate Builder contribution history from submitted actions.
- Add Builder-specific Discord/channel instructions when available.

### Phase 6: Add contribution tracking and community participation loops

- Add quick actions to dashboard and relevant content pages.
- Expand activity types for onboarding, Discord, learning, and Builder actions.
- Show member-visible contribution timeline.
- Add weekly next-step recommendations based on membership type and completed actions.

## Recommended priority order

1. Fix account creation to checkout continuity.
2. Add billing success welcome handoff.
3. Add dashboard onboarding checklist.
4. Add orientation route and completion tracking.
5. Make Discord status honest and actionable.
6. Add Builder activation and contribution submission.
7. Add richer contribution tracking and recognition.

## Definition of done for onboarding readiness

The platform is ready for new feature expansion when a new paid member can:

1. Understand the join sequence before checkout.
2. Create an account without losing selected plan context.
3. Complete Stripe checkout and receive a clear welcome.
4. Start and finish orientation.
5. Know exactly how to access Discord or why it is not available yet.
6. Complete one first community action.
7. If Builder, choose a Builder track and submit a first contribution.
8. See progress reflected in dashboard status and activity history.
