# Mutual Aid Society System Design Draft

**Status:** Documentation-only draft
**Activation status:** Building Toward Activation
**Runtime status:** No mutual aid runtime flows are implemented by this document
**Primary sources:** `SIMBA_COOPERATIVE_ECONOMY_BINDER.md` and the mutual aid society book principles provided for this task

This document translates the mutual aid principles into a future Simba system design. It is not legal, tax, accounting, insurance, banking, charitable solicitation, money-transmission, securities, or cooperative governance advice. It does not authorize launch.

---

## 1. Purpose

The purpose of the Mutual Aid Society system design is to define how Simba can eventually support a member-governed mutual aid structure without confusing it with STAR, Black Dollars, ownership contributions, partner reimbursement, wallet balances, payments, payouts, or automated entitlements.

This document is documentation only. It does not implement mutual aid request forms, fund distribution logic, payment logic, payout logic, reimbursement logic, database migrations, wallet behavior, Black Dollar logic, ownership contribution logic, partner reimbursement logic, or any runtime fund movement.

The Mutual Aid Society is currently **Building Toward Activation**. The $20,000 threshold must be reached before activation. Activation also requires approved policy, governance process, accounting controls, privacy rules, and approval controls.

---

## 2. Source Principles From the Book

The book principles translate into Simba system language as follows:

- **Before the storefront, build the circle.** The system should help members see that relationships, trust, and shared discipline come before commerce features.
- **Before the bank, build the trust.** The future fund must be preceded by governance, records, roles, transparency, and member confidence.
- **Mutual aid is not charity; it is shared obligation.** Future support should be framed as members caring for one another through agreed rules, not as one-directional giving.
- **Community is infrastructure.** Simba should treat meetings, dues, records, roles, and accountability as infrastructure, not side activities.
- **Trust becomes relationships. Relationships become mutual aid. Mutual aid becomes organization. Organization becomes institutions. Institutions support businesses.** The future economy should grow in that order.
- **Ten serious people can begin the circle.** A small committed group can establish the habits, records, and roles that later scale.
- **Meetings, dues, records, and roles make care dependable.** Dependable care requires repeatable governance practices.
- **Transparency protects trust.** Members should be able to understand status, rules, and aggregate fund progress without exposing private hardship details.
- **The first job is to stop emergencies from destroying families.** The future program should prioritize urgent destabilizing needs before discretionary benefits.
- **Survival is the floor, not the ceiling.** Emergency support should stabilize members while the broader cooperative economy builds toward education, ownership, business support, and institution-building.

---

## 3. Core Operating Idea

The Mutual Aid Society is a future member-governed support circle inside the Simba cooperative economy. Its purpose is to build shared community capacity before emergencies happen, then distribute limited support under approved rules after activation.

The system concept is:

1. Members join and strengthen the Simba ecosystem.
2. A designated mutual aid/community development fund is tracked as a collective goal.
3. The community reaches the required activation threshold.
4. Governance approves operating policy, roles, accounting controls, privacy rules, and approval controls.
5. Only after activation may a future member request and review process be launched.

No aid should be described as guaranteed. No request should be automatically approved. No member should see a cash-equivalent wallet balance. No runtime fund movement is authorized in this PR.

---

## 4. Activation Status

Current status: **Building Toward Activation**.

The Mutual Aid Society must not launch until all activation conditions are satisfied:

- The designated fund reaches the $20,000 threshold.
- Mutual aid policy is approved by governance.
- A governance process is approved and documented.
- Accounting controls are approved and operationally ready.
- Privacy rules are approved.
- Approval controls are approved.
- Conflict-of-interest rules are approved.
- Member-facing language is reviewed.
- Legal, tax, accounting, and governance review is complete.

There must be **no mutual aid distributions before activation**.

---

## 5. Member-Facing Language

Approved future-facing language should be careful, non-promissory, and clear:

> Community Mutual Aid Society is Building Toward Activation. Member dues may help build a shared community mutual aid and development fund. The Mutual Aid Society activates only after the community reaches $20,000 and after approved policy, governance process, accounting controls, privacy rules, and approval controls are in place.

Member-facing language must not say or imply:

- aid is guaranteed;
- requests are automatically approved;
- every hardship qualifies;
- members have a cash-equivalent balance;
- members can withdraw mutual aid funds;
- mutual aid is a wallet, bank account, insurance product, investment, or entitlement;
- mutual aid is active before governance approval.

---

## 6. Mutual Aid Society Structure

The future Mutual Aid Society should be structured as a governed support circle with clear separation from other Simba value lanes.

Required structural separations:

- STAR remains participation recognition.
- Black Dollars remain member-only community benefit credits inside the approved partner network.
- Ownership Contribution Balance remains progress toward owner-member eligibility.
- Partner Reimbursement remains controlled settlement to approved businesses under partner agreements.
- Mutual Aid / Community Development Fund remains a shared community fund subject to separate policy and controls.

The Mutual Aid Society should have documented roles, meeting cadence, recordkeeping rules, review procedures, privacy rules, recusal rules, and escalation paths before launch.

---

## 7. Ten Serious People Model

The first operational model should assume that ten serious people can begin the circle. In system design terms, this means Simba should not begin by maximizing automation. It should begin by supporting disciplined human governance.

A future pilot group may include:

- a chair or facilitator;
- a secretary or records keeper;
- a treasurer or finance reviewer;
- a privacy steward;
- a request intake reviewer;
- an approval committee;
- a conflict-of-interest reviewer;
- member educators;
- community accountability witnesses;
- governance liaison or board representative.

The system should help this group document decisions, not replace their judgment.

---

## 8. Dues, Contributions, and Shared Fund Concept

The binder states that 50% of member dues may be allocated toward the Community Development / Mutual Aid Fund if approved by governance and documented in member terms. The fund should be visible as a collective community goal, not as individual cash available to members.

Required design language:

- Mutual Aid Society is currently **Building Toward Activation**.
- The $20,000 threshold must be reached before activation.
- Activation also requires approved policy, governance process, accounting controls, privacy rules, and approval controls.
- No mutual aid distributions before activation.
- No cash-equivalent wallet balance.

The future fund display should show aggregate progress only unless governance later approves a more detailed reporting approach.

---

## 9. Meetings, Records, and Roles

Meetings, dues, records, and roles make care dependable. The future system should support the human practices that make mutual aid trustworthy.

Future records may include:

- meeting dates;
- attendance records;
- approved minutes;
- policy versions;
- role assignments;
- fund balance snapshots;
- request category summaries;
- anonymized decision summaries;
- recusals and conflicts of interest;
- accounting review confirmations;
- audit notes.

These records should be retained according to an approved retention schedule and reviewed by governance before any member-facing request flow launches.

---

## 10. Trust, Transparency, and Accountability

Transparency protects trust, but transparency must not expose private member hardship. The system should separate public or member-visible aggregate status from confidential request details.

Member-visible transparency may include:

- activation status;
- fund threshold progress;
- policy status;
- governance readiness checklist;
- aggregate number of reviewed requests after activation;
- aggregate category reporting after activation;
- aggregate distributions after activation if approved by counsel and governance.

Confidential information must be limited to authorized reviewers and protected by approved privacy rules.

---

## 11. What Member Home Can Show Now

Member Home may show documentation-only, non-runtime mutual aid status language:

- **Community Mutual Aid Society**
- **Status: Building Toward Activation**
- progress toward the $20,000 fund threshold if reliable source data is already approved for display;
- explanation that activation also requires policy, governance process, accounting controls, privacy rules, and approval controls;
- explanation that no member-facing application flow exists yet;
- explanation that there are no mutual aid distributions before activation.

Member Home must not show request forms, approval buttons, payout controls, wallet balances, cash-equivalent values, guaranteed aid promises, or individual entitlement amounts.

---

## 12. What Must Not Launch Yet

The following must not launch from this documentation draft:

- mutual aid runtime flows;
- mutual aid request forms;
- member-facing application flow;
- automatic approval;
- guaranteed aid promises;
- fund distribution logic;
- payment, payout, or reimbursement logic;
- runtime fund movement;
- database migrations;
- wallet behavior changes;
- Black Dollar logic changes;
- ownership contribution logic changes;
- partner reimbursement logic changes;
- cash-equivalent mutual aid balances;
- member withdrawals;
- public hardship stories tied to identifiable members.

---

## 13. Future Member Request Flow

A future request flow may be designed only after activation requirements are satisfied. It should be dignified, minimal, privacy-conscious, and non-shaming.

A future request flow may include:

1. member reviews eligibility and non-guarantee language;
2. member selects an emergency support category;
3. member submits a private request with minimum necessary information;
4. system confirms receipt without promising approval;
5. request is routed to authorized reviewers;
6. member receives status updates using respectful language;
7. approved requests proceed only through approved accounting and payment controls.

Every screen must make clear that submitting a request does not guarantee aid.

---

## 14. Future Review and Approval Flow

A future review and approval flow should be human-governed, documented, and auditable.

Required approval principles:

- no automatic approval;
- no single-person unchecked approval for distributions;
- recusal required for conflicts of interest;
- approval limits defined by policy;
- emergency procedures defined in advance;
- denial and appeal language reviewed for dignity;
- reviewer actions logged;
- accounting controls completed before funds move;
- governance reporting performed in aggregate.

The system should support reviewers, but reviewers remain responsible for applying approved policy.

---

## 15. Future Ledger Requirements

A future mutual aid ledger must be separate from STAR, Black Dollars, ownership contributions, partner reimbursements, and wallet behavior.

Future ledger requirements should include:

- designated fund balance tracking;
- contribution source classification;
- restricted/unrestricted status if applicable;
- approved allocation records;
- request reference IDs;
- approval references;
- disbursement references only after payment controls are approved;
- reversal or correction entries;
- audit trail;
- accounting export or reconciliation support;
- role-based access controls;
- privacy-safe reporting.

The ledger must not create a member cash-equivalent wallet balance.

---

## 16. Privacy, Dignity, and Non-Shame Rules

Mutual aid must protect member dignity. The future system should assume hardship details are sensitive.

Rules:

- collect the minimum necessary information;
- avoid public exposure of hardship details;
- use respectful language in all statuses;
- prohibit shame-based rankings or public request feeds;
- avoid requiring members to perform their hardship for approval;
- restrict reviewer access by role;
- provide clear confidentiality expectations;
- avoid unnecessary document retention;
- review denial language carefully;
- make appeals or reconsideration processes respectful if approved.

---

## 17. Conflict-of-Interest Rules

Conflict-of-interest controls are required before activation. A reviewer should not decide on a request when personal, family, business, financial, romantic, supervisory, or close organizational ties could affect judgment.

Future system support should include:

- conflict disclosure prompts;
- mandatory recusal logging;
- reassignment to alternate reviewers;
- audit trail for recusals;
- governance review of repeated conflicts;
- prohibition on self-approval;
- prohibition on approving requests in exchange for favors, votes, purchases, or membership actions.

---

## 18. Emergency Support Categories

The first job is to stop emergencies from destroying families. Future support categories should focus on urgent stabilizing needs and should be narrowed by approved policy.

Potential categories for review:

- housing stabilization;
- utility shutoff prevention;
- emergency food support;
- transportation crisis support;
- urgent medical access support;
- family safety relocation support;
- funeral or bereavement emergency support;
- childcare emergency support;
- disaster response support;
- other hardship categories approved by governance.

Categories should not become guaranteed benefits. Each category requires eligibility rules, documentation rules, approval limits, privacy handling, and accounting treatment before launch.

---

## 19. Legal, Tax, Accounting, and Governance Review Required

Before activation, the Mutual Aid Society must receive review from appropriate professionals and governance bodies.

Required review areas:

- legal structure;
- cooperative governance authority;
- charitable solicitation implications;
- tax treatment;
- accounting controls;
- fund restrictions;
- insurance implications;
- privacy and data retention;
- payments and money movement;
- member terms;
- denial, appeal, and complaint process;
- conflicts of interest;
- audit process;
- public language.

No launch should occur until these reviews are complete and documented.

---

## 20. Phased Build Order

Recommended phased build order:

1. **Documentation and policy drafting.** Define principles, guardrails, roles, and non-launch language.
2. **Member Home status display.** Show Building Toward Activation status and threshold language only.
3. **Governance packet.** Draft policy, role matrix, conflict rules, privacy rules, and approval procedures.
4. **Accounting design.** Define separate ledger, reconciliation needs, audit trail, and reporting controls.
5. **Legal/tax/accounting review.** Confirm structure, language, and operational requirements.
6. **Reviewer tools prototype.** Build non-payment request review tools only after policy approval.
7. **Member request prototype.** Build private application flow only after activation readiness is approved.
8. **Payment controls integration.** Add payment/payout capabilities only after accounting, legal, and governance approval.
9. **Limited pilot after activation.** Launch with caps, manual review, audit logging, and governance reporting.
10. **Ongoing audit and improvement.** Review outcomes, conflicts, privacy incidents, and member trust indicators.

---

## 21. Final Guardrails

Final guardrails for this design:

- Mutual Aid Society is currently **Building Toward Activation**.
- The $20,000 threshold must be reached before activation.
- Activation also requires approved policy, governance process, accounting controls, privacy rules, and approval controls.
- No mutual aid distributions before activation.
- No automatic approval.
- No guaranteed aid promises.
- No cash-equivalent wallet balance.
- No runtime fund movement in this PR.
- No member-facing application flow yet.
- No payment, payout, or reimbursement logic.
- No mutual aid request forms in this PR.
- No fund distribution logic in this PR.
- No database migrations in this PR.
- No wallet, Black Dollar, ownership contribution, or partner reimbursement behavior changes in this PR.

The correct order is circle, trust, relationship, mutual aid, organization, institution, and then business support. Simba should build the circle before it builds the storefront, and build the trust before it builds anything that resembles a bank.
