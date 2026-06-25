# STAR System Audit

## Summary

The current STAR system is partially real and partially presentation-layer. A backend participation engine exists with persistent `activities`, `participation_points`, `star_transactions`, verification records, activity history, reward events, and audit logs. Member-facing dashboard widgets and several learning/activity pages call real participation APIs and can create persistent STAR activity.

However, the system is not yet production-hardened against the cooperative economy binder. STAR values are embedded in backend defaults, most activity types are auto-verified, reward “redemption” is only an unlock calculation, and there is no complete admin reversal/appeal flow. The dedicated STAR Rewards route/page requested by the binder does not exist; the application card links to `/dashboard#star-rewards`, but the dashboard does not expose a matching `id`, so that route fragment is effectively broken.

No Black Dollar, ownership contribution, partner reimbursement, or mutual aid runtime implementation was added or changed in this audit.

## Files Reviewed

### Binder / policy reference

- `SIMBA_COOPERATIVE_ECONOMY_BINDER.md`

### Frontend routes, pages, and navigation

- `src/App.jsx`
- `src/components/GlobalNav.jsx`
- `src/components/NavBar.jsx`
- `src/layouts/MufasaShell.jsx`
- `src/pages/MemberDashboard.jsx`
- `src/pages/ApplicationsPage.jsx`
- `src/data/applications.js`
- `src/pages/StudyPage.jsx`
- `src/pages/LanguagePage.jsx`
- `src/pages/LanguagesHub.jsx`
- `src/pages/BrainTraining.jsx`
- `src/pages/PortalDecolonize.jsx`
- `src/pages/CommunityPreparednessPage.jsx`
- `src/pages/CommunityDirectoryPage.jsx`
- `src/pages/BuilderOnboardingPage.jsx`
- `src/pages/CommunityOnboardingPage.jsx`
- `src/pages/Home.jsx`

### Frontend API/service/client support

- `src/api/participation.js`
- `src/api/api.js`
- `src/hooks/useMvpActions.js`
- `src/ai/movementModel.js`
- `src/onboarding/memberOnboardingConfig.js`
- `src/onboarding/memberOnboardingStorage.js`
- `src/services/leadershipService.js`

### Frontend styling related to STAR/dashboard/rewards

- `src/styles/dashboard.css`
- `src/styles/member-home.css`
- `src/styles/applications.css`

### Backend routes and services

- `backend/app/routes/participation.py`
- `backend/app/services/participation.py`
- `backend/app/routes/member.py`
- `backend/app/routes/auth.py`
- `backend/app/routes/garvey.py`
- `backend/app/routes/preparedness.py`
- `backend/app/routes/discord.py`

### Backend models, database, and seed/demo references

- `backend/app/models.py`
- `backend/app/database.py`
- `backend/app/init_db.py`
- `backend/app/seed_demo.py`
- `backend/app/demo_seed.py`
- `backend/app/seed_builder.py`
- `backend/seed_demo.py`

### Tests / verification references found

- `backend/tests/test_participation.py`
- `backend/tests/test_auth_member.py`
- `backend/tests/test_member_routes.py`
- `backend/tests/test_community_operations.py`
- `backend/tests/test_garvey.py`

## Current Routes and Pages

| Route / Page | File path | Works? | Linked in navigation? | Real data or mocked/static? | Visible issues |
|---|---|---:|---:|---|---|
| `/dashboard` member view | `src/App.jsx`, `src/pages/MemberDashboard.jsx` | Yes for authenticated non-admin users | Yes: `GlobalNav`, `NavBar`, `MufasaShell`, home CTAs | Mixed: real `/member/overview`, `/member/activity`, `/participation/experience`, `/participation/community-*`; some fallback/default card text and local onboarding state | STAR widgets are embedded in a large dashboard, not a dedicated STAR page. Repeated audiobook activity is grouped in frontend only. Some counters can fall back to zero/default copy. |
| `/dashboard` admin view | `src/App.jsx`, `src/pages/AdminOperationsDashboard.jsx` | Yes for admin users | Yes via dashboard link, but route branches by auth/admin | Mostly backend/admin API driven | Not a STAR admin review/reversal workspace. |
| `/applications` | `src/App.jsx`, `src/pages/ApplicationsPage.jsx`, `src/data/applications.js` | Yes | Yes in `GlobalNav` | Static application metadata | STAR Rewards card routes to `/dashboard#star-rewards`, but the dashboard has no matching `id="star-rewards"`; link lands on dashboard without scrolling to a STAR section. |
| `/dashboard#star-rewards` | `src/data/applications.js`, `src/pages/MemberDashboard.jsx` | Partially / broken fragment | Yes via STAR Rewards application card | Uses dashboard data if user is authenticated | No dedicated route or anchor target exists. This is the clearest binder mismatch for “Fix broken STAR route” and “Add STAR page.” |
| `/study` | `src/App.jsx`, `src/pages/StudyPage.jsx` | Yes | Yes via Learning card / app routing | Real library/study API plus STAR calls when chapter/listening actions occur | STAR recording errors are logged but do not block study. Needs validation of duplicate scopes per book/chapter/listen event. |
| `/languages` | `src/App.jsx`, `src/pages/LanguagesHub.jsx`, `src/pages/LanguagePage.jsx` | Yes | Yes via app card/global app flow | Mixed: language lesson UI/data plus real STAR API call from `LanguagePage` | The hub/page relationship should be verified manually; lesson completion can award STAR through frontend button. |
| `/brain-training` | `src/App.jsx`, `src/pages/BrainTraining.jsx` | Yes | Indirect via Learning/dashboard prompts, not top-level global nav | Real STAR API call; game stats appear frontend-local | Session completion award depends on frontend button. No backend score validation. |
| `/portal/decolonize` | `src/App.jsx`, `src/pages/PortalDecolonize.jsx` | Yes | Linked from library/decolonization flows | Static lesson data plus real STAR API call | Lesson completion award depends on frontend button/client metadata. |
| `/community/preparedness` and `/preparedness` redirect | `src/App.jsx`, `src/pages/CommunityPreparednessPage.jsx`, `backend/app/routes/preparedness.py` | Yes | Yes via app card and redirect | Real preparedness APIs; some dashboard metrics default to zero; STAR instruction hook is informational | Page explicitly says it exposes a STAR hook without changing STAR calculations, but backend preparedness actions can submit participation activity. |
| `/community/directory` | `src/App.jsx`, `src/pages/CommunityDirectoryPage.jsx` | Yes | Yes via Community app card | Mostly static/demo member cards unless backend integration exists elsewhere | Displays `starRank` on demo data; not an authoritative STAR profile. |
| `/builder/onboarding` | `src/App.jsx`, `src/pages/BuilderOnboardingPage.jsx` | Yes for intended users | Linked from billing/dashboard builder flow | Real builder profile/onboarding APIs; recognition language is mostly profile state, not STAR ledger | Says “recognized as an activated Builder through participation tracking,” but no direct STAR award is visible in this component. |
| `/community/onboarding` | `src/App.jsx`, `src/pages/CommunityOnboardingPage.jsx` | Yes | Linked from member lifecycle/dashboard | Real/local onboarding state depending on implementation | Onboarding config references earning STAR as a task, but onboarding progress itself appears separate from STAR ledger. |
| `/member/overview` API consumer | `src/pages/MemberDashboard.jsx`, `backend/app/routes/member.py` | Yes | Not a page; used by dashboard | Real member and participation summary data | Summary depends on `participation_summary`, which sums `Activity.star_award` directly. |
| `/participation/*` APIs | `src/api/participation.js`, `backend/app/routes/participation.py` | Yes | Not direct pages; used by dashboard/activity pages | Real persistent backend data where DB is configured | APIs expose STAR summary/history/rewards/opportunities/leaderboards, but not a full policy/admin reversal flow. |

## Current Components

| Component / module | File path | Purpose | Data source | Real, mocked, static, or unclear |
|---|---|---|---|---|
| Member dashboard STAR summary, journey ring, achievement gallery, rewards/opportunities/history sections | `src/pages/MemberDashboard.jsx` | Displays STAR balance, rank, recent activity, rewards, badges, community feed, onboarding prompts | `/member/overview`, `/member/activity`, `/participation/experience`, `/participation/community-*`, assessment data, local onboarding storage | Mixed: real API data plus static/default messaging and frontend grouping |
| STAR client API wrapper | `src/api/participation.js` | Fetch STAR experience and record participation activity with guest session headers | Backend `/participation/*` endpoints | Real client wrapper |
| STAR Rewards application card | `src/data/applications.js` | Exposes STAR Rewards as an available app | Static metadata route `/dashboard#star-rewards` | Static; route fragment is broken/missing target |
| Applications page cards | `src/pages/ApplicationsPage.jsx` | Renders STAR Rewards app card and launch link | `SIMBA_APPLICATIONS` static list | Static navigation shell |
| Language lesson completion UI | `src/pages/LanguagePage.jsx` | Records Swahili/Yoruba lesson completion and displays STAR notice | `recordParticipationActivity` | Real API call triggered by frontend button |
| Brain training completion UI | `src/pages/BrainTraining.jsx` | Records completed brain game session and displays STAR notice | `recordParticipationActivity` | Real API call, but score/session validation is frontend-local/unclear |
| Study chapter/listening STAR hooks | `src/pages/StudyPage.jsx` | Attempts to record chapter/read/listen participation | `recordParticipationActivity` | Real API call; failure is non-blocking |
| Decolonization lesson completion UI | `src/pages/PortalDecolonize.jsx` | Records decolonization lesson completion and displays STAR notice | `recordParticipationActivity` | Real API call with static lesson content |
| Preparedness STAR instruction panel | `src/pages/CommunityPreparednessPage.jsx` | Communicates STAR instruction hook for preparedness module | Preparedness module registry and API data | Mostly informational/static; backend can submit real preparedness activities |
| Community directory STAR rank display | `src/pages/CommunityDirectoryPage.jsx` | Displays member `starRank` in directory cards | Local/static member-like data | Mocked/static unless later wired elsewhere |
| Onboarding STAR task config | `src/onboarding/memberOnboardingConfig.js` | Includes “Earn STAR through one approved action” as onboarding task | Static config/local onboarding state | Static/task guidance, not a ledger event |
| Legacy MVP reward hook | `src/hooks/useMvpActions.js` | Stores `lastReward` from MVP action responses | API response from MVP endpoints | Unclear/legacy; not clearly connected to STAR ledger |
| Movement model STAR SQL | `src/ai/movementModel.js` | Contains Node-style SQL insert into `star_transactions` | Direct SQL pseudo/service code | Risky/unclear; schema fields do not match current SQLAlchemy `StarTransaction` fields (`member_id`, `delta` vs `user_id`, `amount`) |

## Current Backend/API Support

| Item | File path | Purpose | Persistent data? | Safe to use for pilot? |
|---|---|---|---:|---|
| `ActivityType` model | `backend/app/models.py` | Defines activity type defaults, points, STAR, verification required flag | Yes | Partially. Useful for pilot, but policy values are embedded and auto-created, not governed by admin policy. |
| `Activity` model | `backend/app/models.py` | Primary participation event record with `participation_points` and `star_award` | Yes | Partially. Real event table exists, but direct `star_award` balance summing lacks reversal semantics. |
| `ParticipationPoint` model | `backend/app/models.py` | Records points for activities | Yes | Partially. Redundant with `Activity.participation_points`; needs reconciliation policy. |
| `StarTransaction` model | `backend/app/models.py` | Records STAR transaction amount/type/reason tied to activity | Yes | Partially. Exists, but `participation_summary` sums `Activity.star_award`, not `StarTransaction.amount`, so the transaction table is not the authoritative balance source. |
| `Badge` model | `backend/app/models.py` | Stores badge definitions | Yes | Not enough by itself; dashboard badges also come from growth profile and reward unlock calculations. |
| `RewardEvent` model | `backend/app/models.py` | Stores reward event/status/cost metadata | Yes | Unclear. Available rewards are calculated from static list; no visible redemption workflow reviewed. |
| `VerificationRecord` model | `backend/app/models.py` | Stores activity verification state and verifier | Yes | Partially. Supports community verification, but most default STAR events are auto-verified. |
| `ActivityAuditLog` model | `backend/app/models.py` | Stores audit action before/after metadata | Yes | Good foundation, but no complete admin reversal/appeal UI/API found. |
| `POST /participation/activity` | `backend/app/routes/participation.py` | Records activity and returns STAR award/summary | Yes, via service | Pilot-safe only for low-risk participation; needs stricter policy controls before high-value use. |
| `GET /participation/summary` | `backend/app/routes/participation.py` | Returns participation score, STAR, rank, streak | Reads DB | Useful, but balance should eventually come from ledger transactions/reversals. |
| `GET /participation/experience` | `backend/app/routes/participation.py` | Returns summary, opportunities, history, rewards, leaderboard | Reads DB + static lists | Useful for pilot display with caveats. |
| `GET /participation/opportunities` | `backend/app/routes/participation.py` | Returns static STAR opportunities | No write; static service list | Safe as informational if values are approved. |
| `GET /participation/history` | `backend/app/routes/participation.py` | Returns recent activity records | Reads DB | Useful. |
| `GET /participation/rewards` | `backend/app/routes/participation.py` | Returns static reward unlock status based on STAR | Reads summary + static rewards | Risky wording: “cost”/unlock should not imply redemption value without terms. |
| `GET /participation/leaderboards` | `backend/app/routes/participation.py` | Returns community leaderboards | Reads DB | Potential privacy/gamification concern; needs policy review. |
| Verification request APIs | `backend/app/routes/participation.py`, `backend/app/services/participation.py` | Creates/validates community verification requests and verifier STAR | Yes | Needs policy/admin controls before high-value contribution awards. |
| Participation service defaults | `backend/app/services/participation.py` | Defines activity defaults, ranks, opportunities, rewards, duplicate detection, summaries | Writes/reads DB | Good foundation, but not policy-externalized and most awards auto-verify. |
| Member overview/activity APIs | `backend/app/routes/member.py` | Include STAR summary and activity rows in member dashboard data | Reads DB | Useful for pilot display. |
| Auth guest merge | `backend/app/routes/auth.py`, `backend/app/services/participation.py` | Merges guest participation into user account on signup/login | Updates DB | Useful, but duplicate/merge reconciliation should be tested. |
| Garvey assessment completion STAR | `backend/app/routes/garvey.py` | Optional STAR award for eligible assessment completion | Writes DB when eligible | Needs review: cross-system assessment rewards should be policy-controlled. |
| Preparedness route STAR submissions | `backend/app/routes/preparedness.py` | Preparedness actions can submit participation activities | Writes DB | Needs review of verification/anti-spam per preparedness action. |

## Current Data Model

- STAR does have persistent database representation through `activities.star_award` and `star_transactions.amount`.
- There is no standalone “STAR balance” table reviewed. Balances are calculated at read time by summing `Activity.star_award` in `participation_summary`.
- STAR is not stored on `users` or `member_profiles` as a direct profile balance in the reviewed models. Member profile/dashboard responses include STAR by calling the participation summary service.
- STAR events exist as `Activity` rows, with supporting `ParticipationPoint`, `StarTransaction`, `ActivityHistory`, `VerificationRecord`, and `ActivityAuditLog` rows.
- The current effective balance is directly stored per activity (`Activity.star_award`) and summed, while `StarTransaction` exists as a ledger-like companion table but is not the source of truth for summary calculation.
- Reversal support is incomplete. The model has `StarTransaction.transaction_type`, `ActivityAuditLog`, and verification/audit tables, but no reviewed admin reversal API/UI or policy-driven reversal flow that creates a reversing ledger event and excludes/reconciles the original award from the balance.
- Duplicate protection exists in the service before awarding. It compares identity, activity type, source module, and a metadata-derived duplicate scope over recent candidate activities.
- Most standard activity types are auto-created as non-verification-required and auto-verified. High-value review exists only through the community verification request path, not as a general policy enforcement layer for all high-value actions.
- Frontend-only STAR display logic exists in the dashboard: grouping audiobook activity, deriving achievements from current STAR, and fallback community goal displays. These displays do not create the balance but can shape member perception.

## Real vs Mocked STAR Events

| Event / Action | Source File | Real or Mocked | Current STAR Amount | Verification Needed | Notes |
|---|---|---|---:|---|---|
| `book_read` | `backend/app/services/participation.py` | Real backend default | 10 | Yes, policy validation needed | Default activity type; source integration not fully verified in this audit. |
| `chapter_read` | `backend/app/services/participation.py`, `src/pages/StudyPage.jsx` | Real API path | 10 | Duplicate scope and completion validation | Study page attempts STAR recording; frontend-driven. |
| `audiobook_listen` | `backend/app/services/participation.py`, `src/pages/StudyPage.jsx` | Real API path | 8 | Duplicate scope/listen completion validation | Dashboard groups repeated audiobook activity in frontend. |
| `language_lesson` | `backend/app/services/participation.py` | Real backend default | 7 | Source integration validation | Generic default; specific language events also exist. |
| `swahili_lesson_completed` | `backend/app/services/participation.py`, `src/pages/LanguagePage.jsx` | Real API path | 7 | Lesson identity duplicate validation | Frontend button awards through API. |
| `yoruba_lesson_completed` | `backend/app/services/participation.py`, `src/pages/LanguagePage.jsx` | Real API path | 7 | Lesson identity duplicate validation | Frontend button awards through API. |
| `language_match_completed` | `backend/app/services/participation.py` | Real backend default | 5 | Source integration validation | No specific frontend source confirmed in this audit. |
| `quiz_completed` | `backend/app/services/participation.py` | Real backend default | 5 | Quiz validation | No specific frontend source confirmed in this audit. |
| `decolonization_lesson_completed` | `backend/app/services/participation.py`, `src/pages/PortalDecolonize.jsx` | Real API path | 9 | Lesson identity duplicate validation | Static lesson content; frontend button triggers award. |
| `brain_game_played` | `backend/app/services/participation.py`, `src/pages/BrainTraining.jsx` | Real API path | 6 | Session/score validation | Frontend-triggered; backend does not validate actual game completion. |
| `content_shared` | `backend/app/services/participation.py` | Real backend default | 4 | Share event validation | Share tracking exists elsewhere, but direct STAR source needs verification. |
| `daily_history_read` | `backend/app/services/participation.py` | Real backend default | 3 | Source integration validation | No direct call confirmed in this audit. |
| `word_of_day_viewed` | `backend/app/services/participation.py` | Real backend default | 3 | Source integration validation | No direct call confirmed in this audit. |
| `member_referred` | `backend/app/services/participation.py` | Real backend default | 20 | High-value review recommended | Referral fraud/spam controls needed. |
| `volunteer_task_completed` | `backend/app/services/participation.py` | Real backend default | 15 | Review recommended | High-ish value; should not be purely self-attested. |
| `event_attended` | `backend/app/services/participation.py` | Real backend default | 12 | Attendance verification | Needs event check-in/proof path. |
| `community_help` | `backend/app/services/participation.py` | Real backend default | 12 | Review recommended | Broad label; needs policy definition. |
| `community_onboarding_completed` | `backend/app/services/participation.py`, `src/onboarding/memberOnboardingConfig.js` | Backend real default; frontend config static | 20 | Completion source validation | Onboarding task mentions STAR but direct award source should be confirmed. |
| `builder_onboarding_completed` | `backend/app/services/participation.py`, `src/pages/BuilderOnboardingPage.jsx` | Backend real default; page recognition unclear | 20 | Completion source validation | Builder page shows activation state but no clear STAR call in component. |
| `share_verified` | `backend/app/services/participation.py`, `backend/app/routes/participation.py` | Real verification path | 12 after verification | Yes; 3 confirmations | Community verification request path can defer award until verified. |
| `community_verification` | `backend/app/services/participation.py` | Real verification reward | 3 default; first verifier 3, follow-ups 1 | Abuse/conflict review | Service mutates verifier award from default based on slot. |
| Preparedness profile completed | `backend/app/services/participation.py`, `backend/app/routes/preparedness.py`, `src/pages/CommunityPreparednessPage.jsx` | Real backend default/path | 12 | Duplicate and proof policy | Preparedness page is a real module with STAR instruction copy. |
| Preparedness volunteer joined | `backend/app/services/participation.py`, `backend/app/routes/preparedness.py` | Real backend default/path | 15 | Review recommended | Volunteer status should not be self-awarded without controls. |
| Preparedness supplies logged | `backend/app/services/participation.py`, `backend/app/routes/preparedness.py` | Real backend default/path | 10 | Duplicate/proof policy | Household supply claims may need privacy-conscious verification. |
| Preparedness training attended | `backend/app/services/participation.py`, `backend/app/routes/preparedness.py` | Real backend default/path | 12 | Attendance verification | Needs training attendance proof. |
| Preparedness household supported | `backend/app/services/participation.py`, `backend/app/routes/preparedness.py` | Real backend default/path | 12 | Review recommended | Service/contribution claim should use verification controls. |
| STAR Rewards application card | `src/data/applications.js` | Static navigation/display | N/A | Route fix needed | Links to missing dashboard anchor instead of a STAR page. |
| Community directory `starRank` | `src/pages/CommunityDirectoryPage.jsx` | Mocked/static display | N/A | Replace with real/permissioned data | Demo rank can imply member status without authoritative source. |
| Achievement “STAR Collector” | `src/pages/MemberDashboard.jsx` | Frontend-derived display | Based on current balance | Messaging review | Derived from balance, not a persistent badge event. |
| Static reward unlocks | `backend/app/services/participation.py`, `src/pages/MemberDashboard.jsx` | Calculated/static | Thresholds at 25, 50, 75, 100, 150, 250 | Policy review | Uses `star_cost`/unlock language; not a real redemption ledger. |

## Broken or Risky Items

- Broken/missing STAR route: `src/data/applications.js` advertises STAR Rewards at `/dashboard#star-rewards`, but `src/pages/MemberDashboard.jsx` does not define a matching anchor or standalone STAR page.
- STAR does not yet have the binder-requested member-facing page with rules, categories, recent activity, milestones, badges, integrity language, and community STAR progress.
- Balance calculation uses `Activity.star_award` rather than `StarTransaction` ledger events, despite the presence of `star_transactions`.
- No complete reversal flow was found. Fraudulent/duplicate STAR cannot be cleanly reversed in the reviewed user/admin flows.
- No member appeal flow for disputed STAR decisions was found.
- Most activity types are auto-verified by default. This conflicts with the binder’s expectation that high-value actions may require review.
- Activity type values are hardcoded in `DEFAULT_ACTIVITY_TYPES`, `STAR_OPPORTUNITIES`, `RANK_THRESHOLDS`, and `STAR_REWARDS`, rather than policy/admin controlled.
- Unknown/unconfigured activity types default to 5 STAR, which may allow accidental awards for typoed or unauthorized actions.
- Frontend-triggered actions can award STAR without strong backend proof of completion for some experiences, such as brain training sessions and lesson buttons.
- Community directory includes a static/demo `starRank`, which could be mistaken for authoritative member reputation.
- Reward list uses `star_cost` naming even though no redemption/cash value should be implied; this should be renamed or explained before public pilot.
- Leaderboards and public/community feed can create ranking/privacy/gamification concerns if member identity handling is not policy-reviewed.
- `src/ai/movementModel.js` appears incompatible with the current backend model (`star_transactions(member_id, delta, reason)` vs SQLAlchemy `user_id`, `amount`, `transaction_type`) and should be treated as stale/unsafe until verified.
- Duplicate detection exists but depends on metadata scopes. Integrations must consistently send stable metadata such as book/chapter/lesson IDs.
- Guest STAR merge exists, but reconciliation and duplicate behavior during signup/login should be regression-tested.

## Binder Alignment

| Binder rule | Current implementation follows? | Notes |
|---|---:|---|
| STAR is participation recognition only. | Mostly | UI and service position STAR as participation recognition, but rewards/leaderboard language should be reviewed to avoid over-gamification or implied benefits. |
| STAR is not money. | Mostly | No cash-out or money conversion found in STAR runtime. Reward `star_cost` wording could confuse users. |
| STAR is not ownership. | Yes in reviewed STAR code | No automatic ownership conversion found. |
| STAR cannot be purchased. | Yes in reviewed STAR code | No STAR purchase/payment flow found. |
| STAR cannot be cashed out. | Yes in reviewed STAR code | No cash-out flow found. |
| STAR cannot be transferred. | Yes in reviewed STAR code | No person-to-person STAR transfer flow found. |
| STAR does not automatically create ownership. | Yes in reviewed STAR code | No ownership automation tied to STAR found. |
| High-value STAR actions may require review. | Partially / not broadly | Community verification path exists, but most default activities are auto-verified and high-value defaults are not centrally policy-gated. |
| Duplicate/spam actions should be reversible. | Duplicate prevention partially; reversal no | Duplicate detection exists, but no complete admin reversal/appeal flow was found. |
| STAR should be auditable. | Partially | Activity, transaction, history, verification, and audit log tables exist; summary does not use ledger as source of truth and reversal workflow is missing. |
| STAR point values should be policy-based, not scattered through frontend code. | Partially | Values are mostly backend constants/static service lists, not frontend, but still hardcoded rather than policy/admin controlled. |

## Recommended Minimal Next PRs

### 1. Safe now

1. Add a documentation-only STAR policy/terminology pass for UI copy: clarify that STAR is participation recognition, not money, not ownership, not transferable, not purchasable, and not cash redeemable.
2. Add or repair a dedicated member-facing STAR route/page shell without changing awarding logic. It should read existing `/participation/experience` data and include binder-aligned rules/integrity copy.
3. Fix the broken `/dashboard#star-rewards` anchor or redirect it to the new STAR page.
4. Rename or explain `star_cost` display language in the UI so rewards appear as recognition milestones/unlocks, not purchases or redemption value.
5. Add tests around duplicate detection metadata scopes for chapter, lesson, brain game, preparedness, and share events.
6. Add a backend test proving unknown activity types do not accidentally create unauthorized STAR once policy is tightened.
7. Add a technical note that `StarTransaction` is not currently the balance source of truth and define the future ledger-backed migration plan.

### 2. Needs policy/admin controls

1. Add admin STAR review/reversal APIs that create reversal events instead of deleting original records.
2. Add member-facing disputed STAR/appeal status after policy approval.
3. Move STAR earning rules to policy-managed configuration or database records with role-protected admin controls.
4. Require verification for high-value or proof-based events such as referrals, volunteer tasks, event attendance, builder contributions, business support, and service contributions.
5. Add anti-spam/rate-limit controls for frontend-triggered STAR events.
6. Add privacy controls for leaderboards/community feeds.
7. Reconcile `Activity.star_award` and `StarTransaction.amount` so one ledger source drives balances, history, reversals, and audit exports.

### 3. Do not build yet

1. Do not implement Black Dollars issuance, balance, wallet spending, partner acceptance, or member transfer flows.
2. Do not implement runtime wallet logic that combines STAR, Black Dollars, ownership contribution, mutual aid, or reimbursement balances.
3. Do not implement ownership contribution payments, dues allocation toward ownership, service credits, founder credits, or automatic owner eligibility.
4. Do not implement partner reimbursement or settlement logic.
5. Do not implement mutual aid application, approval, or distribution runtime flows.
6. Do not change database schemas or add migrations until the STAR hardening design is approved.
7. Do not change partner portal behavior.

## Testing Performed

- `rg -n "\bSTAR\b|star|reward|badge|activity|contribution|member home|dashboard|profile" -S --glob '!node_modules/**' --glob '!dist/**' --glob '!build/**' --glob '!coverage/**'`
- `rg -n "participation|STAR|star_award|star_transactions|current_rank|reward|badge" backend src --glob '!node_modules/**'`
- `rg -n "STAR|Black Dollars|ownership|cash|transfer|purchas|revers|review|participation" SIMBA_COOPERATIVE_ECONOMY_BINDER.md`
- `npm run build`
## Follow-up Notes

- Follow-up PR completed: dedicated STAR Rewards page and navigation repair.
- Follow-up PR completed: Member Home / Dashboard STAR visibility and navigation cleanup.

## Follow-up Note — STAR Activity Display Cleanup

- Member Home now shows a compact recent STAR participation activity feed inside the STAR recognition card. Repeated low-risk activity from the same day and source is grouped in the frontend so members do not see long runs of duplicate lesson/listening rows, while higher-value, service, support, referral, review, appeal, and verification-related actions remain individually visible.
- The `/star-rewards` page uses the same display safety approach for recent STAR activity: noisy same-day actions are summarized, and the card copy states that STAR is participation recognition only, not money, cash, ownership, transferable value, or cash-redemption value.
- Empty states now explain that members can earn STAR through approved learning, reflection, preparedness, sharing, service, building, and support actions. These empty states also repeat that STAR does not automatically create owner-member status.
- This cleanup is display-only. It does not add Black Dollars, ownership contribution logic, mutual aid runtime flows, partner reimbursement logic, schema changes, migrations, payments, or STAR earning-rule changes.
- Some Member Home and STAR Rewards content remains presentation-layer or fallback copy, including static categories, opportunity messaging, badge/milestone presentation, and frontend grouping. These displays are not authoritative policy or ledger records.
- STAR balances are still read from existing participation/activity summary data (`/participation/experience`, `/member/overview`, `/member/activity`) and are still effectively derived from existing participation activity data rather than a ledger-backed source of truth.
- Before STAR becomes ledger-backed, Simba should make `star_transactions` the authoritative balance source, add reversal/appeal/admin review flows, externalize earning policy and high-value verification rules, reconcile historical `Activity.star_award` rows into ledger events, and add tests proving duplicate, reversal, merge, and verification behavior.
