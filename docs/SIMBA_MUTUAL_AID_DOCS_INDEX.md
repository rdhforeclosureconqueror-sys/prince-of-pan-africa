# Simba Mutual Aid Documentation Index

**Status:** Phase 1 documentation package only  
**Activation status:** Building Toward Activation  
**Runtime status:** No routes, APIs, migrations, dashboards, request forms, payment flows, ledgers, integrations, wallet changes, or fund movement are authorized here.

## Documentation Map

- `SIMBA_MUTUAL_AID_DOCS_INDEX.md` controls the documentation map, editing rules, cross-reference rules, PR limits, and phase guardrails.
- `SIMBA_MUTUAL_AID_SOCIETY_BINDER.md` controls the core policy model, public operating concept, governance model, member rights and limits, and one-page summary.
- `SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md` controls human operating procedures, committee practice, review templates, accounting controls, versioning, service targets, and launch checklists.
- `SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md` controls developer planning only, including future module boundaries, future route/API/table drafts, status machines, audit requirements, and test expectations.
- `SIMBA_MUTUAL_AID_LANGUAGE_PACK.md` controls member-facing and public language.
- `SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md` controls pilot readiness, pilot limits, stop conditions, go/no-go rules, and post-pilot review.

## Editing Rules

- Keep Mutual Aid Society documentation separate from the main cooperative economy binder.
- Update the specific document that controls the subject being changed.
- Do not create a new giant source-of-truth document.
- Keep policy, operations, technical planning, public language, and pilot launch details in their assigned files.
- Do not add runtime behavior from documentation-only changes.
- Treat all technical sections as planning drafts until a later phase explicitly approves implementation.

## Cross-Reference Rules

- Each Mutual Aid document must include the full **Related Mutual Aid Documents** list.
- Cross-references should point to the controlling document rather than duplicating full content.
- If a rule appears in more than one document, the document map above determines which file controls future edits.
- Short summaries may be repeated where helpful, but detailed procedure should live in the controlling file.

## Docs-Only PR Rules

- Documentation-only PRs may edit markdown planning files.
- Documentation-only PRs must not add routes, UI pages, API endpoints, database migrations, seed data, admin dashboards, request forms, review queues, notification systems, payment flows, ledger logic, feature flag runtime logic, STAR integrations, Black Dollar integrations, ownership contribution integrations, partner reimbursement integrations, wallet behavior changes, payout logic, or reimbursement logic.
- Documentation-only PRs must clearly state that live payouts are not authorized.
- Documentation-only PRs must clearly state that support is reviewed and not guaranteed.

## First Runtime PR Limits

The first future runtime PR, if approved, should be limited to Phase 2: a display-only Mutual Aid overview page. It should show safe language, Building Toward Activation status, the $20,000 threshold, and coming-soon status. It must not include request intake, approvals, payment movement, reimbursement movement, dashboards, or member balances.


## Required Activation Guardrails

- Mutual Aid Society is currently **Building Toward Activation**.
- The **$20,000 threshold** must be reached before activation.
- Activation also requires approved policy, governance process, accounting controls, privacy rules, and approval controls.
- There are **no mutual aid distributions before activation**.
- Support is reviewed support, not guaranteed support.
- There is no automatic approval.
- There is no cash-equivalent member balance.
- There is no runtime fund movement in this Phase 1 documentation PR.
- There is no member-facing application flow yet.
- There is no payment, payout, or reimbursement logic in this PR.


## Phased Roadmap

1. **Phase 1 — Documentation package.** Create and organize the six documents only.
2. **Phase 2 — Display-only Mutual Aid page.** Future PR only; adds `/mutual-aid` overview page with safe language, activation threshold, coming-soon status, and no request flow.
3. **Phase 3 — Admin/internal planning scaffold.** Future PR only; adds non-public admin planning placeholders if approved, with no live requests or payouts.
4. **Phase 4 — Contribution ledger planning/display.** Future PR only; tracks fund progress only if approved, with no distributions.
5. **Phase 5 — Request intake pilot.** Future PR only; allowlisted members only, no automatic approval, and no automated payouts.
6. **Phase 6 — Committee review pilot.** Future PR only; adds reviewer workflow, conflicts, and decisions.
7. **Phase 7 — Manual disbursement tracking.** Future PR only; records manual payments after governance approval, with no automated payments.
8. **Phase 8 — Pilot reporting.** Future PR only; adds anonymized impact and governance reporting.

## Summary Guardrails

Build the circle before building runtime tools. Build trust, roles, records, accounting controls, privacy rules, and approval controls before any reviewed support process opens. Keep STAR, Black Dollars, ownership contribution progress, partner reimbursements, wallets, and Mutual Aid Society records separate unless a later approved phase explicitly defines a safe integration.

## Related Mutual Aid Documents

- [SIMBA_MUTUAL_AID_DOCS_INDEX.md](SIMBA_MUTUAL_AID_DOCS_INDEX.md)
- [SIMBA_MUTUAL_AID_SOCIETY_BINDER.md](SIMBA_MUTUAL_AID_SOCIETY_BINDER.md)
- [SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md](SIMBA_MUTUAL_AID_SOCIETY_OPERATING_APPENDIX.md)
- [SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md](SIMBA_MUTUAL_AID_SOCIETY_TECHNICAL_SPEC.md)
- [SIMBA_MUTUAL_AID_LANGUAGE_PACK.md](SIMBA_MUTUAL_AID_LANGUAGE_PACK.md)
- [SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md](SIMBA_MUTUAL_AID_PILOT_LAUNCH_PLAN.md)
