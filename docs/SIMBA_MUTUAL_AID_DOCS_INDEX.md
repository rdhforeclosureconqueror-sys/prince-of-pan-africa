# Simba Mutual Aid Docs Index

**Version:** 0.1  
**Status:** Documentation map and source-of-truth guide  
**Purpose:** Explain the Mutual Aid Society documentation package, what each file controls, and which document should be edited for each type of change.

## Mutual Aid Documentation Package

The Mutual Aid Society package includes these six controlling documents, created in this order:

1. `docs/SIMBA_MUTUAL_AID_DOCS_INDEX.md`
2. `docs/SIMBA_MUTUAL_AID_SOCIETY_BINDER.md`
3. `docs/SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md`
4. `docs/SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md`
5. `docs/SIMBA_MUTUAL_AID_LANGUAGE_PACK.md`
6. `docs/SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md`

## Source-of-Truth Rules

### Binder

`SIMBA_MUTUAL_AID_SOCIETY_BINDER.md` controls purpose, core principles, relationship to platform, activation rule, funding sources, aid categories, eligibility, governance model, member rights and limits, and high-level implementation phases.

Use the binder when asking:

- What is the Mutual Aid Society?
- What is it allowed to do?
- What should it never be described as?
- What does activation require?

### Operating Appendix

`SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md` controls the committee charter, conflict-of-interest policy, application template, review rubric, appeals, emergency aid procedure, accounting controls, fraud and abuse process, notification events, admin SOP, MVP database additions, and launch checklist.

Use the operating appendix when asking:

- How do humans operate the Mutual Aid Society?
- Who reviews requests?
- How are conflicts handled?
- How are appeals handled?
- What must be complete before launch?

### Technical Spec

`SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md` controls feature flags, module boundaries, roles and permissions, route plan, API plan, database draft, status machines, business rules, audit requirements, privacy rules, first MVP build scope, testing requirements, and PlantUML workflow.

Use the technical spec when asking:

- How should developers build the module in future phases?
- What should the database look like if a later phase approves it?
- What routes and APIs are planned but not yet implemented?
- What must stay behind feature flags?

### Language Pack

`SIMBA_MUTUAL_AID_LANGUAGE_PACK.md` controls member-facing copy, public words, words to avoid, notifications, status labels, approval notices, not-approved notices, appeal copy, FAQ, and empty states.

Use the language pack when asking:

- What should the platform say to members?
- What language is safe?
- What words are forbidden or reserved only for avoidance lists?
- How should a decision be explained respectfully?

### Pilot Launch Plan

`SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md` controls pilot access, pilot participants, pilot scope, manual processes, success criteria, stop conditions, go/no-go rules, timeline, and post-pilot review.

Use the pilot launch plan when asking:

- Who gets access first?
- What can be tested?
- What must stay manual?
- When do we stop the pilot?

## Editing Rules

### Do Not Mix Document Purposes

Do not put:

- technical route details inside the language pack;
- member-facing copy inside the database spec;
- committee operating rules inside the pilot plan;
- pilot timeline inside the core binder;
- legal/entity strategy inside UI copy.

Each document has one job. Cross-reference instead of duplicating full sections.

### Documentation Before Runtime

Before any Mutual Aid runtime code is built, this docs package should be accepted.

Runtime code means request forms, request routes, database migrations, review queues, admin dashboards, disbursement records, payment connections, notifications, impact reports, feature flag runtime logic, wallet changes, or integrations.

The first safe runtime build is only a display-only Mutual Aid overview page with safe language, activation threshold, coming-soon message, links to rules, and a feature flag guard if a later phase approves it.

## Required Cross-References

Each Mutual Aid document must link to the other five Mutual Aid documents and to this index in a **Related Mutual Aid Documents** section.

If `docs/SIMBA_COOPERATIVE_ECONOMY_BINDER.md` exists, it should contain only this short pointer:

> For the full Mutual Aid Society operating model, see docs/SIMBA_MUTUAL_AID_DOCS_INDEX.md.

The main cooperative economy binder must not absorb the full Mutual Aid Society content.

## PR Rules

### Docs-Only PRs

A docs-only PR may add or update markdown files, cross-references, checklists, diagrams inside docs, language clarifications, and guardrails.

A docs-only PR may not add runtime routes, UI pages, database migrations, API endpoints, payment logic, request workflow logic, admin dashboards, auth permission changes, feature flag runtime logic, or connections to STAR, Black Dollars, ownership contribution, partner reimbursement, wallets, payouts, or reimbursement behavior.

### First Runtime PR Limits

The first runtime PR may only add a display-only `/mutual-aid` page if explicitly approved later. It may include safe overview copy from the language pack, activation threshold display, coming-soon request message, docs links if appropriate, and tests proving no request or payout flow exists.

It may not add request submission, document uploads, committee review, disbursement records, payment processing, member fund balances, or automatic eligibility decisions.

## Guardrail Summary

Use governed community support, reviewed support, community care, available funds, eligibility, documentation, approval, committee review, and impact reporting.

Avoid describing Mutual Aid Society with terms listed in the language pack's avoidance section. Aid is reviewed under policy and depends on eligibility, need, documentation, approval, committee review, and available funds. Actual money movement stays manual until separately approved.

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
