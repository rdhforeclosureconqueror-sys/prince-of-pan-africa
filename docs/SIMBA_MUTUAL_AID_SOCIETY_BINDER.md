# Simba Mutual Aid Society Binder

**Version:** 0.1  
**Status:** Standalone planning and operating binder  
**Relationship to main binder:** Companion document to `SIMBA_COOPERATIVE_ECONOMY_BINDER.md` if that binder exists.  
**Important note:** This is an architecture, policy, and operating design document. The final version should be reviewed by appropriate cooperative governance, tax, accounting, privacy, and payments/compliance professionals before public launch.

## Purpose

The Simba Mutual Aid Society exists to turn community participation into organized care. It is a future member-governed community care structure inside Simba that prepares governed community support for urgent destabilizing needs, preparedness, family stability, and community resilience after activation requirements are complete.

## Core Principle

Before commerce features, build the circle. Before money movement, build trust, records, roles, governance, accounting controls, privacy rules, and approval controls.

Safe framing:

> The Mutual Aid Society is a governed community support system. Members may contribute, request support in a later approved phase, nominate others in a later approved phase, and help guide priorities. Aid is reviewed under written policy and distributed based on need, available funds, eligibility, documentation, and approval.

## Relationship to the Simba Platform

The Simba platform is the operating system. The Mutual Aid Society is the community care institution.

The platform may eventually provide member identity, good-standing status, fund visibility, contribution tracking, aid request intake, committee review workflows, decision records, manual disbursement tracking, audit logs, and anonymized impact reports.

The platform must not present mutual aid funds as a personal user balance or imply that members own any portion of the fund.

Required separations:

- STAR remains participation recognition.
- Black Dollars remain separate from Mutual Aid Society support.
- Ownership Contribution Balance remains separate from Mutual Aid Society support.
- Partner reimbursement remains separate from Mutual Aid Society support.
- Wallet behavior must not be changed by this documentation package.

## Recommended Operating Structure

### Launch Model

Start as a governed program connected to Simba. This allows the team to test member needs, request volume, governance process, committee review, fraud controls, reporting, contribution patterns, privacy rules, and accounting controls.

### Mature Model

Long term, the Mutual Aid Society may need its own legal or fiscal structure. Possible paths for professional review include a program inside the cooperative, a nonprofit or foundation, a social welfare entity, or fiscal sponsorship.

Recommended MVP assumption:

> Start as a governed internal program with separate records and policies. Design the software so the Mutual Aid Society can later be separated into its own approved entity without rebuilding everything.

## Activation Rule

The Mutual Aid Society may be visible before launch, but real aid distributions should begin only after activation.

The Society remains **Building Toward Activation** until every activation requirement is satisfied and documented. No mutual aid distributions are authorized before activation.

## $20,000 Threshold

The Mutual Aid Society becomes active only after the designated Mutual Aid / Community Development Fund reaches **$20,000** in available or committed funding and all governance controls are approved.

Before activation, future display-only pages may show purpose, rules, fund progress, contribution sources, coming-soon request process, and governance setup.

After activation and later phase approval, the platform may open member aid requests, nominations, committee review, approved manual support records, and impact reporting.

## Funding Sources

Allowed funding sources may include designated portion of member dues, direct member support, sponsor contributions, grants, partner business contributions, fundraising campaigns, cooperative surplus allocations if approved, and community development allocations.

A common planning rule may be:

> Up to 50% of qualifying member dues may be allocated to the Mutual Aid / Community Development Fund, subject to governance approval, written member terms, and accounting controls.

Each source should be recorded separately with source type, source name, amount, restriction status, restriction notes, received date, payment reference, creator, and audit reference.

## Member Rights and Limits

Members may eventually request aid, nominate another member, contribute funds, view general fund progress, view anonymized impact, and participate in priority-setting if governance allows.

Members may not demand guaranteed aid, sell or transfer aid eligibility, direct fund movement, treat mutual aid as individual property, or use Mutual Aid Society funds as a cash-equivalent member balance.

Safe member language:

> Mutual aid support is not guaranteed. Requests are reviewed based on policy, available funds, urgency, eligibility, documentation, and committee approval.

## Aid Categories

Start with a narrow set of categories.

### Emergency Relief

Examples include rent gap, utility support, food support, urgent transportation, and emergency family needs.

### Education and Preparedness

Examples include training, certifications, books, emergency kits, and tools for resilience.

### Health and Wellness Support

Examples include counseling support, wellness support, recovery support, and community health programs. Avoid presenting this as coverage or guaranteed medical support.

### Community Development

Examples include local gardens, neighborhood projects, youth programs, cultural programs, and community safety initiatives.

### Member Hardship Support

Examples include temporary support for members in good standing, crisis recovery support, and family hardship support.

## Eligibility

Recommended MVP eligibility: a requester must generally be an active member, in good standing, verified in the platform, within request frequency limits, willing to provide required documentation, and not under fraud or suspension review.

Exceptions may be allowed for emergency community cases if approved by the committee or board.

Good standing may include active membership, accepted community terms, no unresolved serious conduct violation, no active fraud flag, and no abuse of previous aid.

Eligibility does not create guaranteed support.

## Governance Model

Use a three-layer governance structure.

### Members

Members can participate through requests, nominations, contributions, surveys, priority feedback, community meetings, and annual reporting review if those actions are approved in later phases.

### Mutual Aid Committee

The Mutual Aid Committee reviews requests and recommends or approves support based on delegated authority. Responsibilities include reviewing applications, requesting more information, checking eligibility, documenting decisions, disclosing conflicts, recommending support method, flagging suspicious activity, and protecting privacy.

### Board or Governance Body

The board or official governance body approves annual budget, fund rules, maximum support limits, emergency authority, appeal process, conflict-of-interest policy, committee appointments, reporting standards, and audits.

## Roles and Permissions

### Member

Can view a future mutual aid overview, submit a request only if a later phase enables it, nominate another member only if enabled, upload documents only if enabled, view own request status only if enabled, and contribute if a later approved payment flow exists.

Cannot view other members' private requests, approve aid, edit fund records, or see sensitive committee notes.

### Committee Reviewer

Can view assigned requests, leave review notes, request information, recommend approval or non-approval, disclose conflicts, and vote or score if enabled.

Cannot alter financial records, pay funds directly unless explicitly authorized, or review conflicted cases.

### Mutual Aid Admin

Can manage requests, assign reviewers, prepare manual support records, update request statuses, manage documentation, and generate reports if a later phase approves those tools.

### Treasurer / Finance Role

Can confirm funds received, confirm manual payments made, reconcile records, export accounting data, and mark manual support records complete if a later phase approves those tools.

### Board / Governance Admin

Can approve policy changes, approve large support requests, appoint committee members, review appeals, and approve annual reports.

## Request Workflow

Recommended future status flow:

```text
draft
  -> submitted
  -> eligibility_check
  -> under_review
  -> more_info_requested
  -> committee_recommended
  -> approved
  -> manual_processing_pending
  -> manually_completed
  -> closed
```

Alternative terminal statuses:

```text
not_approved
withdrawn
expired
flagged
appealed
reversed
```

Future intake fields may include member ID, category, requested amount, urgency level, short explanation, preferred support method, vendor/provider information if applicable, documents if required, consent to review, policy acceptance, and nomination link if nominated by another member.

Future review fields may include reviewer ID, conflict disclosure, eligibility result, recommendation, recommended amount, notes, requested follow-up, and timestamp.

Future decision fields may include decision ID, request ID, decision type, approved amount, support method, conditions, decision maker, decision date, reason code, and appeal eligibility.

## Disbursement Rules

No disbursements occur before activation. After activation, support may move only after approval, documented controls, finance review, and governance-approved procedures. This PR authorizes no payment, payout, reimbursement, or runtime fund movement logic.

Preferred future support order:

1. Pay vendor/provider directly when possible.
2. Use restricted digital support or voucher if appropriate.
3. Provide direct member support only when allowed by policy and documented.
4. Require receipt or closeout confirmation when appropriate.

## Limits and Controls

Recommended MVP controls include maximum request amount, maximum emergency support amount, monthly fund cap, category budget caps, per-member annual review trigger, request frequency limits, documentation thresholds, dual approval above threshold, board approval above threshold, fraud hold status, cooling-off period after large support, and audit log for every status change.

Example starter limits for planning only:

```text
Emergency micro-support: up to $250
Standard support: up to $1,000
Large support: above $1,000 requires board approval
Annual member support review: triggered after $1,500
Monthly fund reserve: do not disburse below 20% reserve
```

These are planning defaults, not final policy.

## Privacy Rules

Mutual aid data is sensitive. The platform should protect request narratives, financial hardship details, identity documents, receipts, health-related details, family information, and committee notes.

Public reporting must be anonymized and must not identify a recipient unless they give explicit written consent.

## Impact Reporting

Member-facing reports may show total fund balance, total raised, total distributed after activation, number of requests approved after activation, categories supported, anonymized stories, and upcoming priorities.

Governance reports may show contributions by source, support by category, non-approved/approved ratio, average response time, fund reserve, large support records, exceptions, conflicts, and audit issues.

Admin reports may show request queue, reviewer activity, pending documents, manual support records, flagged cases, and reconciliation issues if a later phase approves admin tooling.

## Data Model Draft

Planning-only tables may include:

```text
mutual_aid_funds
mutual_aid_contributions
mutual_aid_requests
mutual_aid_request_documents
mutual_aid_reviews
mutual_aid_decisions
mutual_aid_manual_support_records
mutual_aid_policies
mutual_aid_committee_members
mutual_aid_conflict_disclosures
mutual_aid_appeals
mutual_aid_audit_logs
```

No migrations are created in Phase 1.

## Platform Pages

Future member pages may include Mutual Aid overview, fund progress, request aid, nominate someone, my requests, my contributions, rules and eligibility, and impact report.

Future committee pages may include review queue, request detail, conflict disclosure, recommendation form, decision history, and follow-up needed.

Future admin pages may include fund dashboard, contribution records, request management, committee assignment, manual support tracking, policy manager, audit logs, and reports.

No pages are implemented in Phase 1.

## Public Language Guide

Use governed community support, reviewed support, community care, available funds, eligibility, documentation, approval, committee review, impact reporting, community support fund, request support, and anonymized impact.

Avoid language that implies automatic support, guaranteed aid, cash-equivalent member balances, personal ownership of the fund, or financial product behavior.

## Phased Roadmap

1. **Phase 1 — Documentation package.** Create and organize the six documents only.
2. **Phase 2 — Display-only Mutual Aid page.** Future PR only; adds `/mutual-aid` overview page with safe language, activation threshold, coming-soon status, and no request flow.
3. **Phase 3 — Admin/internal planning scaffold.** Future PR only; adds non-public admin planning placeholders if approved. No live requests or payouts.
4. **Phase 4 — Contribution ledger planning/display.** Future PR only; tracks fund progress only if approved. No distributions.
5. **Phase 5 — Request intake pilot.** Future PR only; allowlisted members only. No automatic approval. No automated payouts.
6. **Phase 6 — Committee review pilot.** Future PR only; adds reviewer workflow, conflicts, and decisions.
7. **Phase 7 — Manual disbursement tracking.** Future PR only; records manual payments after governance approval. No automated payments.
8. **Phase 8 — Pilot reporting.** Future PR only; adds anonymized impact and governance reporting.

## Legal and Governance Open Questions

1. Should the Mutual Aid Society remain inside the cooperative at launch?
2. Should it become a standalone or fiscally sponsored structure later?
3. Are member dues being allocated as dues, donations, program fees, or restricted contributions?
4. What tax reporting applies to support recipients?
5. What documentation is needed for different support types?
6. What support methods are allowed?
7. What conflict-of-interest standards apply?
8. Can non-members receive support in emergencies?
9. What state community fundraising rules apply?
10. What privacy policy changes are needed?

## One-Page Summary

The Simba Mutual Aid Society is Building Toward Activation as a governed community support system connected to Simba. It should begin as a controlled program with clear rules, separate records, committee review, privacy protections, support controls, and anonymized impact reporting. The safest next technical step after this documentation package is a display-only page; do not implement live aid payouts until governance, professional review, fund controls, and committee procedures are approved.

## Required Activation and Safety Guardrails

- Mutual Aid Society is currently **Building Toward Activation**.
- The **$20,000 threshold** must be reached before activation.
- Activation also requires approved policy, governance process, accounting controls, privacy rules, and approval controls.
- There are **no mutual aid distributions before activation**.
- There is **no automatic approval**.
- There are **no guaranteed aid promises**.
- There is **no cash-equivalent wallet balance**.
- There is **no runtime fund movement in this PR**.
- There is **no member-facing application flow yet**.
- There is **no payment, payout, or reimbursement logic in this PR**.
- Live payouts are not authorized by this documentation package.
- Support is reviewed under policy and depends on need, available funds, eligibility, documentation, approval, and committee review.

## Related Mutual Aid Documents

- [SIMBA_MUTUAL_AID_DOCS_INDEX.md](SIMBA_MUTUAL_AID_DOCS_INDEX.md)
- [SIMBA_MUTUAL_AID_SOCIETY_BINDER.md](SIMBA_MUTUAL_AID_SOCIETY_BINDER.md)
- [SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md](SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md)
- [SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md](SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md)
- [SIMBA_MUTUAL_AID_LANGUAGE_PACK.md](SIMBA_MUTUAL_AID_LANGUAGE_PACK.md)
- [SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md](SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md)
