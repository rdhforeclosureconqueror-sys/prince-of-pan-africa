# Phase 1 — Member Intelligence Read Model

## Clear scope

Phase 1 adds a read-only/generated Member Intelligence service. It summarizes a member inside a society from existing records only. It does not expose new public APIs, create appointments, assign roles, calculate reputation, or change Society Builder workflows.

## Files changed

- `backend/app/services/member_intelligence.py` — generated read-model service.
- `backend/tests/test_member_intelligence_phase1.py` — backend coverage for empty, partial, First Ten, review, and appointment-history evidence.
- `src/data/memberBehavioralProfiles.js` — marks static sample behavioral profiles as deprecated fallback-only.

## Migration needs

No database migration is required. The read model queries existing tables and returns generated data without persisting new rows.

## Backend tests

Run:

```bash
PYTHONPATH=backend pytest backend/tests/test_member_intelligence_phase1.py -q
```

The tests cover:

- generation with no assessment data,
- generation with partial assessment data,
- missing assessment prompts,
- confidence changes based on available evidence,
- First Ten role consideration evidence,
- role candidate review evidence,
- role assignment history evidence,
- no automatic appointment creation.

## Frontend checks

No frontend runtime behavior is changed in this phase. Static sample behavioral profiles are marked deprecated and fallback-only so future wiring can prefer live Member Intelligence when available.

## Admin manual test steps

1. Create or open a society with an active member.
2. Confirm the member has a `SocietyMembership` record.
3. Generate Member Intelligence through the backend service in a shell or test harness.
4. Confirm the response includes `member_id`, `society_id`, `completed_assessments`, `missing_assessments`, `current_roles`, `evidence_sources`, `warnings`, and `confidence_level`.
5. Add or link a First Ten entry for the same user and regenerate.
6. Confirm `considered_roles` and First Ten evidence appear.
7. Add a role candidate review or appointment history row and regenerate.
8. Confirm role evidence appears without creating any new appointment rows.

## Rollback notes

Remove `backend/app/services/member_intelligence.py`, remove `backend/tests/test_member_intelligence_phase1.py`, and remove the deprecation export/comment from `src/data/memberBehavioralProfiles.js`. No data rollback is required because the service is read-only and has no migration.

## Acceptance criteria

- Member Intelligence can be generated from existing data.
- Missing data produces warnings instead of failures.
- Missing assessments are surfaced.
- Confidence changes as evidence increases.
- First Ten, role candidate review, and role assignment history evidence are included when present.
- Static sample behavioral profiles are no longer presented as the preferred future source.
- No automatic decisions or appointments are made.
