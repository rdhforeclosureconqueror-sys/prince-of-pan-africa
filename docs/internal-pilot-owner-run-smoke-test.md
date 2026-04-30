# Internal Pilot Owner-Run Smoke Test

Use this from your local machine (or any network that can reach Render) to verify live deployment readiness.

## Script
- `scripts/smoke_test_internal_pilot.sh`

## Required environment variables
- `BASE_URL` (required)
  - Example: `https://mufasa-knowledge-bank.onrender.com`
- `ADMIN_EMAIL` (recommended for admin checks)
- `ADMIN_PASSWORD` (recommended for admin checks)
- `MEMBER_EMAIL` (optional, enables member checks)
- `MEMBER_PASSWORD` (optional, enables member checks)

> Do not commit or hardcode credentials. Export them in your shell/session only.

## Checks included
1. `GET /health` returns HTTP 200 and `status` of `ok` or `degraded`.
2. Unauthenticated `GET /admin/overview` returns `401`.
3. If admin credentials are provided:
   - `POST /auth/login` succeeds (`200`)
   - session cookie is issued
   - authenticated `GET /admin/overview` returns `200`
4. `GET /system/verification` is permission-gated (expects `401` or `403` unauthenticated).
5. If member credentials are provided:
   - `POST /auth/login` succeeds (`200`)
   - session cookie is issued
   - authenticated `GET /member/overview` returns `200`

## Example usage
```bash
BASE_URL="https://mufasa-knowledge-bank.onrender.com" \
ADMIN_EMAIL="your-admin@example.com" \
ADMIN_PASSWORD='your-admin-password' \
MEMBER_EMAIL="your-member@example.com" \
MEMBER_PASSWORD='your-member-password' \
bash scripts/smoke_test_internal_pilot.sh
```

## Output format
The script prints `PASS`, `FAIL`, or `WARN` for each check and exits non-zero if any required check fails.
