# Simba Mutual Aid Pilot Launch Plan

**Version:** 0.1  
**Status:** Controlled pilot planning document  
**Important:** This pilot launch plan does not authorize public launch, live payouts, automated disbursements, unsafe benefit promises, or guaranteed aid. It defines a controlled internal pilot for a future approved phase.

## Pilot Purpose

The purpose of the Mutual Aid pilot is to test whether Simba can safely support a governed community care process before live public launch.

The pilot should validate member understanding, safe language, fund visibility, request intake readiness, committee review process, privacy controls, admin workflow, manual support tracking, impact reporting, fraud controls, and governance decision-making.

The pilot is not meant to maximize volume. It is meant to prove the process is safe, clear, and governable.

## Pilot Scope

### In Scope

For the first pilot, allow Mutual Aid overview page, activation threshold display, rules and eligibility page, fund progress display, test contribution records, internal request intake, committee review testing, admin status updates, manual decision records, manual support records, and anonymized impact report draft.

### Out of Scope

Do not include public aid request access, automated payouts, payment processor payouts, member cash balances, Black Dollar conversion, STAR-to-aid conversion, ownership contribution conversion, partner reimbursement automation, or guaranteed support promises.

## Participants

### Internal Pilot Group

Recommended starting group: 5 to 10 trusted internal members, 2 to 3 admins, 3 to 5 committee reviewers, 1 treasurer or finance role, and 1 governance approver.

### Expansion Group

After the first internal test: 25 to 50 verified members, same committee structure, limited aid categories, and manual support tracking only.

### Public Launch

Public launch should not happen until professional review is complete, privacy review is complete, committee is trained, fund controls are approved, appeal process is tested, audit reports work, safe language is reviewed, and manual reconciliation is tested.

## Access Rules

Only approved pilot participants should access live request flows. Access should be controlled by feature flags, member allowlist, role permissions, good-standing status, admin approval, and policy acceptance.

Recommended pilot access flags:

```text
MUTUAL_AID_DISPLAY_ENABLED=true
MUTUAL_AID_REQUESTS_ENABLED=true only for allowlisted members
MUTUAL_AID_COMMITTEE_REVIEW_ENABLED=true only for assigned reviewers
MUTUAL_AID_DISBURSEMENT_TRACKING_ENABLED=true only for admins/treasurer
MUTUAL_AID_PAYMENTS_ENABLED=false
```

Hard rule: no automated payment movement in pilot.

## Pilot Aid Categories

Start with only three categories: Emergency Relief, Education and Preparedness, and Member Hardship Support.

Defer Health and Wellness Support, Community Development grants, large project funding, partner-funded aid, public nominations, and non-member requests.

## Pilot Limits

Recommended pilot limits:

```text
Maximum request amount: $250
Maximum approved amount: $250
Maximum requests per member: 1 during pilot
Emergency review window: 24 to 48 hours
Standard review window: 5 business days
Minimum reserve: 20%
Manual approval required for every request
Treasurer confirmation required for every manual support record
```

No single reviewer should approve alone. At least 2 authorized reviewers must recommend approval before admin final decision.

## Pilot Workflow

### Display Phase

1. Member views Mutual Aid page.
2. Member reads rules and eligibility.
3. Member sees activation/fund progress.
4. Member sees support is not guaranteed.

### Request Phase

1. Allowlisted member submits request.
2. System checks membership and policy acceptance.
3. Admin checks eligibility.
4. Admin assigns reviewers.
5. Reviewers disclose conflicts.
6. Reviewers recommend approve, not approve, or more info.
7. Admin records decision.
8. Treasurer records manual support status if approved.
9. Member receives notice.
10. Request closes after follow-up.

### Reporting Phase

1. Admin reviews closed requests.
2. Treasurer reconciles records.
3. Governance reviews exceptions.
4. Platform generates anonymized impact report.
5. Team reviews lessons learned.

## Manual Processes During Pilot

Keep actual money movement, bank transfers, payment processor payouts, tax classification, large exception approval, recipient verification, vendor/provider confirmation, receipt validation, restriction review, and accounting reconciliation manual.

The platform may record these actions in a future approved phase, but should not automate them yet.

## Data to Collect

Collect number of page visits, request starts, submitted requests, approved requests, not-approved requests, requests needing more information, average review time, average approved amount, category distribution, documentation issues, member confusion points, reviewer confusion points, admin workload, privacy incidents, appeals, fraud flags, and reconciliation issues.

Also collect qualitative feedback: Did members understand support was not guaranteed? Was the request process respectful? Was the review process clear? Did reviewers know what to do? Were admin controls enough? Was any language confusing?

## Success Criteria

Pilot is successful if members understand mutual aid is reviewed support, no UI shows personal fund balances, no unsafe financial language appears, requests can be reviewed without privacy leaks, reviewers can disclose conflicts, admins can record decisions clearly, treasurer can reconcile manual support records, impact report can be anonymized, audit trail captures major actions, and committee can explain every decision.

Pilot is not successful if members think they are owed aid, think they can access personal money, reviewers approve without policy, private request details are exposed, support records are not reconciled, audit logs are missing, or committee decisions are inconsistent.

## Stop Conditions

Pause the pilot immediately if private hardship details are exposed, money is moved without authorization, reviewers approve conflicted cases, members are promised guaranteed support, fund records do not reconcile, fraud patterns appear, committee cannot explain decisions, professional review concern is raised, platform permissions fail, or members can see other members' requests.

## Roles and Responsibilities

### Pilot Lead

Responsible for pilot readiness, timeline, team coordination, issue escalation, and final go/no-go recommendation.

### Admin Lead

Responsible for request queue, reviewer assignment, status updates, member notices, and documentation checks.

### Committee Chair

Responsible for review discipline, conflict disclosures, recommendation consistency, reviewer training, and committee meetings.

### Treasurer

Responsible for fund records, manual support confirmation, receipt tracking, reconciliation, and finance reporting.

### Governance Approver

Responsible for policy compliance, exceptions, appeals, large concerns, and pilot expansion approval.

## Pilot Timeline

Recommended timeline:

```text
Week 1: Docs, policy, training, and feature flag setup
Week 2: Display-only page test
Week 3: Internal request workflow test with sample requests
Week 4: Real allowlisted pilot requests, manual tracking only
Week 5: Review results, fix issues, prepare expansion decision
```

Do not expand until stop conditions are cleared.

## Pre-Pilot Checklist

- [ ] Binder approved.
- [ ] Operating appendix approved.
- [ ] Technical spec approved.
- [ ] Language pack approved.
- [ ] Pilot launch plan approved.
- [ ] Professional review scheduled or completed.
- [ ] Committee appointed.
- [ ] Committee trained.
- [ ] Conflict-of-interest policy accepted.
- [ ] Privacy policy reviewed.
- [ ] Feature flags configured in a future approved phase.
- [ ] Allowlist configured in a future approved phase.
- [ ] Admin permissions tested.
- [ ] Reviewer permissions tested.
- [ ] Treasurer permissions tested.
- [ ] Test request completed.
- [ ] Audit logs verified.
- [ ] Safe language reviewed.
- [ ] Stop conditions accepted.

## Go/No-Go Rules

Proceed only if all pre-pilot checklist items are complete, no critical privacy or permission issue exists, committee is trained, manual support process is understood, safe language is confirmed, and feature flags are working.

Do not proceed if payout process is unclear, permissions are not tested, committee is not trained, fund accounting is unclear, members may misunderstand the fund, docs conflict with platform UI, or professional review issues are unresolved for public launch.

## Post-Pilot Review

After the pilot, produce a report covering what worked, what confused members, what confused reviewers, average review time, request outcomes, policy exceptions, privacy issues, fraud or abuse concerns, reconciliation results, language changes needed, technical bugs, governance changes needed, and recommended next phase.

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
