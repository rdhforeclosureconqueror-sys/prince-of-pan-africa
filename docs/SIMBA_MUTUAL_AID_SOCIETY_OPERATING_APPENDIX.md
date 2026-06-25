# Simba Mutual Aid Society Operating Appendix

**Version:** 0.1  
**Status:** Human operating rules and templates for Phase 1 documentation only  
**Purpose:** Extend the binder with charters, operating procedures, review templates, control checklists, and launch readiness rules.

## Mutual Aid Society Charter

### Purpose

The Simba Mutual Aid Society exists to organize community care, emergency support, preparedness, and community development through a governed fund connected to the Simba platform.

The Society does not guarantee aid. It reviews requests according to written policy, available funds, member eligibility, documentation, urgency, and committee approval.

### Mission

To help members and community participants meet urgent needs, strengthen household stability, support preparedness, and build community resilience.

### Scope

The Society may support emergency hardship, food and household stability, transportation needs, education and preparedness, wellness and recovery support, family crisis support, community development projects, and youth and cultural programs after activation and approval.

The Society may not operate as a guaranteed support plan, personal savings mechanism, payroll process, lending process, or cash-equivalent wallet.

### Relationship to Simba

The Simba platform may later provide identity, membership records, request intake, committee workflows, fund visibility, audit trails, and reports. The Mutual Aid Society governs the support process. The platform should not automatically approve aid or imply that members own any portion of the fund.

## Mutual Aid Committee Charter

### Committee Purpose

The Mutual Aid Committee reviews aid requests, protects the fund, applies policy fairly, documents decisions, and recommends improvements to the board or governance body.

### Committee Size

Recommended MVP size: minimum 3 members, preferred 5 members, maximum MVP size 7 members. A request should not be approved by only one person except under documented emergency authority.

### Committee Composition

The committee should include at least one governance representative, at least one finance/treasury representative or liaison, trusted community members, and people trained on privacy and conflict-of-interest rules.

### Term Length

Standard term is 12 months. Renewal is allowed by governance approval. Emergency replacement is allowed if a member resigns or is removed.

### Committee Duties

Committee members must review requests respectfully, keep member information private, disclose conflicts, follow written policy, avoid favoritism, document recommendations, protect the fund from abuse, and participate in periodic review meetings.

### Removal

A committee member may be removed for privacy violation, conflict-of-interest abuse, fraud, favoritism, harassment, repeated absence, misuse of platform access, or violation of Simba community rules.

## Conflict-of-Interest Policy

A reviewer has a conflict if the request involves themselves, a family member, romantic partner, close friend, business partner, employer or employee, person they owe money to, person who owes them money, organization they control, or any situation where fairness may reasonably be questioned.

If conflicted, the reviewer must disclose the conflict, leave the review process for that request, not vote, not influence other reviewers, and not access private notes beyond what is allowed.

### Conflict Disclosure Fields

```text
id
request_id
reviewer_id
conflict_type
description
recusal_required
disclosed_at
review_admin_id
status
```

## Aid Request Application Template

### Member Information

Full name, member ID, contact information, membership status, good-standing status, and preferred contact method.

### Request Details

Aid category, requested amount, urgency level, date support is needed by, short summary of need, detailed explanation, prior aid history, and whether the request is connected to another organization or support source.

### Preferred Support Method

Options may include pay vendor/provider directly, pay landlord/utility/company directly, reimbursement after receipt if approved by policy, direct member support if allowed by policy, voucher or restricted support, or other.

### Documentation

Possible documentation includes bill, invoice, lease notice, utility notice, receipt, school/training invoice, transportation estimate, provider letter, emergency explanation, or other supporting proof.

### Member Consent

The member must agree that information may be reviewed by authorized committee/admin users, approval is not guaranteed, false information may lead to non-approval or suspension, support may be paid directly to a vendor/provider, follow-up documentation may be required, and anonymized impact may be reported without identifying them.

## Review Rubric

### Review Criteria

```text
Urgency: 1-5
Need severity: 1-5
Documentation strength: 1-5
Member good-standing status: pass/fail
Prior aid history: low/medium/high concern
Fund availability: pass/fail
Category fit: pass/fail
Fraud concern: low/medium/high
```

### Recommended Decision Logic

Approve if the member is eligible, the request fits an approved category, need is documented or reasonably verified, funds are available, and no unresolved fraud concern exists.

Request more information if the request may be valid but documentation is incomplete, support destination is unclear, or urgency needs confirmation.

Do not approve if the request is outside policy, member is ineligible, documentation is false or insufficient after follow-up, request duplicates recent support beyond limits, or fund balance cannot support the request.

### Reason Codes

```text
approved_emergency_need
approved_standard_need
approved_partial_amount
more_info_needed
not_approved_ineligible_member
not_approved_outside_policy
not_approved_insufficient_documentation
not_approved_fund_unavailable
not_approved_frequency_limit
not_approved_fraud_concern
withdrawn_by_member
```

## Appeals Process

Members should have a fair appeal path. Recommended MVP default: appeal must be submitted within 14 days of non-approval.

Appeal grounds include misunderstood information, newly available documentation, incorrect eligibility status, possible reviewer conflict, or urgency changed after decision.

Appeals should be reviewed by a different reviewer, committee chair, governance admin, or board representative for large or sensitive cases.

Appeal statuses: `appeal_submitted`, `appeal_under_review`, `appeal_more_info_requested`, `appeal_approved`, `appeal_denied`, `appeal_closed`.

## Emergency Aid Procedure

Emergency aid may apply when delay could cause serious harm, such as loss of housing, utility shutoff, food emergency, urgent transportation need, safety-related relocation, or family crisis.

Recommended MVP rule: emergency aid up to $250 may be approved by two authorized reviewers. Emergency aid above $250 follows standard approval unless board emergency authority is triggered.

Emergency aid may be approved with limited documentation, but follow-up should be required. Initial proof is required when possible. Follow-up receipt or confirmation should be required within 14 days.

## Accounting and Fund Controls

The Mutual Aid Fund must be tracked separately from general platform money. Track member dues allocations, restricted donations, unrestricted donations, grants, sponsor funds, partner contributions, support records, reversals, and administrative costs if allowed.

Recommended MVP reserve rule: do not disburse below a 20% reserve unless emergency governance approval is recorded.

Treasurer or finance role should reconcile weekly during launch, monthly after stable operations, quarterly for governance reporting, and annually for full review.

Required records include contribution records, source restrictions, request records, approval decisions, support confirmations, receipts, payment references, audit logs, and policy versions.

## Fraud, Abuse, and Safety Policy

Red flags include duplicate documentation, altered receipts, repeated emergency requests, inconsistent identity information, suspicious vendor/provider, reviewer conflict, pressure on committee members, attempts to sell or transfer aid, and harassment after non-approval.

Fraud statuses: `no_concern`, `monitoring`, `flagged`, `under_investigation`, `cleared`, `restricted`, `suspended`, `referred_to_governance`.

Response options include requesting more documentation, pausing review, not approving request, restricting future requests, suspending mutual aid access, escalating to governance, reversing unpaid support, and documenting incident.

## Policy Versioning

Every request should be tied to the policy version active at submission.

Policy fields: `id`, `policy_name`, `version`, `effective_date`, `approved_by`, `approval_date`, `status`, `summary_of_changes`, `document_url`, `created_at`, `updated_at`.

A request should store `policy_version_id`, `member_policy_acceptance_id`, and `submitted_at` to prevent confusion if policies change later.

## Notifications

Member notifications may be sent when request is submitted, enters review, more information is needed, decision is made, manual support is scheduled, manual support is complete, appeal window is closing, or request is closed.

Committee notifications may be sent when new request is assigned, emergency request arrives, conflict disclosure is needed, review deadline is approaching, more information is uploaded, or appeal is submitted.

Admin notifications may be sent when request is flagged, fund balance is low, reserve threshold is reached, manual support action fails, receipt is overdue, or audit issue appears.

## Service-Level Targets

These are internal goals, not guarantees: emergency first review within 24 hours, standard first review within 5 business days, more-info follow-up within 3 business days, approved manual support scheduling within 3 business days, appeal review within 10 business days, monthly reconciliation by the 10th day of next month, and quarterly impact report within 30 days after quarter end.

## Admin SOP

### New Request SOP

1. Confirm member identity.
2. Confirm active membership.
3. Check good-standing status.
4. Check request frequency limits.
5. Check category fit.
6. Check documentation.
7. Assign reviewers.
8. Create audit log entry.

### Approval SOP

1. Confirm reviewer recommendations.
2. Confirm no unresolved conflict.
3. Confirm funds are available.
4. Confirm reserve rule is not violated.
5. Confirm support method.
6. Record final decision.
7. Notify member.
8. Prepare manual support record if approved by policy.

### Manual Support SOP

1. Confirm approved amount.
2. Confirm recipient/vendor details.
3. Confirm support method.
4. Schedule manual process outside automated product flows.
5. Record reference.
6. Mark complete after confirmation.
7. Request receipt if needed.
8. Close request after confirmation.

## MVP Database Additions

Planning-only additions: `mutual_aid_policy_versions`, `mutual_aid_member_acceptances`, `mutual_aid_request_status_history`, `mutual_aid_notification_events`, `mutual_aid_fraud_reviews`, `mutual_aid_reconciliation_reports`, `mutual_aid_reserve_rules`, `mutual_aid_category_budgets`, `mutual_aid_vendor_recipients`.

No migrations are included in Phase 1.

## MVP Launch Checklist

- [ ] Mutual Aid Society binder approved.
- [ ] Committee charter approved.
- [ ] Conflict-of-interest policy approved.
- [ ] Aid categories approved.
- [ ] Eligibility rules approved.
- [ ] Request limits approved.
- [ ] Emergency aid rule approved.
- [ ] Disbursement rules approved.
- [ ] Privacy language approved.
- [ ] Member consent language approved.
- [ ] Treasurer/reconciliation process approved.
- [ ] Admin SOP approved.
- [ ] Committee members appointed.
- [ ] Committee members trained.
- [ ] Fund records configured in an approved future phase.
- [ ] Policy versioning configured in an approved future phase.
- [ ] Audit logs enabled in an approved future phase.
- [ ] Public language reviewed.
- [ ] Professional review completed before public launch.

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

## Phased Roadmap

1. **Phase 1 — Documentation package.** Create and organize the six documents only.
2. **Phase 2 — Display-only Mutual Aid page.** Future PR only; adds `/mutual-aid` overview page with safe language, activation threshold, coming-soon status, and no request flow.
3. **Phase 3 — Admin/internal planning scaffold.** Future PR only; adds non-public admin planning placeholders if approved. No live requests or payouts.
4. **Phase 4 — Contribution ledger planning/display.** Future PR only; tracks fund progress only if approved. No distributions.
5. **Phase 5 — Request intake pilot.** Future PR only; allowlisted members only. No automatic approval. No automated payouts.
6. **Phase 6 — Committee review pilot.** Future PR only; adds reviewer workflow, conflicts, and decisions.
7. **Phase 7 — Manual disbursement tracking.** Future PR only; records manual payments after governance approval. No automated payments.
8. **Phase 8 — Pilot reporting.** Future PR only; adds anonymized impact and governance reporting.

## Related Mutual Aid Documents

- [SIMBA_MUTUAL_AID_DOCS_INDEX.md](SIMBA_MUTUAL_AID_DOCS_INDEX.md)
- [SIMBA_MUTUAL_AID_SOCIETY_BINDER.md](SIMBA_MUTUAL_AID_SOCIETY_BINDER.md)
- [SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md](SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md)
- [SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md](SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md)
- [SIMBA_MUTUAL_AID_LANGUAGE_PACK.md](SIMBA_MUTUAL_AID_LANGUAGE_PACK.md)
- [SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md](SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md)
