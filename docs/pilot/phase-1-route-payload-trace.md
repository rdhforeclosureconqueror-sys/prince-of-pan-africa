# Phase 1 — Route & Payload Trace (Pilot Stabilization)

Date: 2026-04-21
Scope: static trace only (no core logic changes)

## 1) Backend route inventory (FastAPI)

### Core + diagnostics
- `GET /` → service metadata/status.
- `GET /health` → basic health.
- `GET /info` → metadata + registered route list.

### Auth
- `GET /auth/me` → current user payload (`user` object expected by frontend callers).

### Member dashboard
- `GET /member/overview` → returns:
  - `status`
  - `user` `{ id, email, created_at }`
  - `member_profile` `{ id, role, attributes }`
  - `summary_stats` `{ assessment_count, activity_count }`
- `GET /member/activity?limit=10` → returns:
  - `status`
  - `user_id`
  - `activity[]` entries `{ id, action, timestamp }`

### Leadership assessment
- `POST /assessment/submit`
  - Request: `{ userId?: string, responses: (string|number)[] }` with exactly 30 entries.
  - Response: `{ userId, percentages, roles, insights, coaching, rolesIncluded, version }`.
- `GET /assessment/results/{user_id}`
  - Response: `{ userId, responses, percentages, roles, insights, coaching, version, createdAt }`.
- `GET /assessment/analytics/roles`
  - Response: assessment counts and averages keyed by role.

### Chat / voice / portals / admin / system (registered)
- Chat (router prefix `/chat`): `/ping`, `/message`, `/tts`, `/voice`.
- Voice (router prefix `/api/voice`): `/tts`, `/stt`, `/health`.
- Portals (router prefix `/portal`): `/list`, `/start`, `/continue`, `/create_image`.
- System diagnostics: `/system/verification`, `/system/verification/full`, and test/database diagnostic routes.
- Admin: `/admin/overview`, `/admin/members`, `/admin/profiles`.

## 2) Frontend route usage trace

### Confirmed aligned usages
- Leadership service uses:
  - `POST /assessment/submit`
  - `GET /assessment/results/{userId}`
- Dashboard page uses:
  - `GET /member/overview`
  - `GET /member/activity`

### High-risk mismatches found (for Phase 2+)
1. **Member dashboard shape mismatch**
   - UI expects top-level fields like `reading_minutes`, `workouts_completed`, `shares`, `streak_days`.
   - API actually returns nested `summary_stats` and profile/user metadata.
2. **Activity field mismatch**
   - UI reads `title/type/detail/description`.
   - API returns `action` and `timestamp` only.
3. **Disconnected API calls in MVP helper**
   - Frontend helper calls `/fitness/log`, `/study/journal`, `/study/share`, `/language/practice`, `/forms/submit`, `/ai/session`.
   - No matching FastAPI routes in current backend tree.
4. **Game interaction endpoint mismatch**
   - `PagtPage` posts to `/pagt/vote`.
   - No backend `/pagt/*` route currently registered.

## 3) Payload contract snapshot (current observed canonical shape)

### `GET /member/overview`
```json
{
  "status": "ok",
  "user": { "id": 1, "email": "member@example.com", "created_at": "..." },
  "member_profile": { "id": 1, "role": "member", "attributes": {} },
  "summary_stats": { "assessment_count": 2, "activity_count": 5 }
}
```

### `GET /member/activity`
```json
{
  "status": "ok",
  "user_id": 1,
  "activity": [
    { "id": 9, "action": "assessment_submitted", "timestamp": "..." }
  ]
}
```

### `POST /assessment/submit`
```json
{
  "userId": "1",
  "percentages": { "architect": 63 },
  "roles": { "primary": "Architect", "secondary": "Operator", "growth": "Educator", "shadow": "Nurturer" },
  "insights": { "primary": "...", "growth": "...", "shadow": "..." },
  "coaching": "...",
  "rolesIncluded": ["architect", "operator", "..."],
  "version": "v1"
}
```

## 4) Phase-1 stabilization notes
- No feature logic was changed.
- This trace is additive documentation and provides reversible, audit-friendly input for Phase 2 API contract normalization.
