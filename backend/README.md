# 🦁 Mufasa Knowledge Bank

**Purpose:** Core backend for the Prince of Pan-Africa platform.  
Coordinates OpenAI GPT and OpenVoice APIs for text, speech, and structured portal-based learning.

## Endpoints
| Endpoint | Description |
|-----------|--------------|
| `/chat/ask` | General chat with context |
| `/portal/list` | List all portal codes |
| `/portal/start` | Start a 30-day portal |
| `/portal/continue` | Continue a portal with RESUME_CODE |
| `/health` | Health check |

---

## Environment Variables
- `OPENAI_API_KEY`
- `OPENVOICE_URL` (default: https://ffmpeg-9xhs.onrender.com)
- `ALLOWED_ORIGINS` (comma-separated list of frontend URLs for CORS)
- `SESSION_SECRET` (required outside local/test environments)
- `SESSION_COOKIE_SAMESITE` (defaults to `lax`; production same-site auth uses `lax`)
- `SESSION_COOKIE_DOMAIN` (production same-site auth uses `.simbawaujamaa.com` after `api.simbawaujamaa.com` is verified on the active backend)

## Production API host note

Production frontend builds should use `https://api.simbawaujamaa.com` after Render verifies DNS and issues the certificate for the `prince-of-pan-africa-backend` custom domain. Keep `https://prince-of-pan-africa-backend.onrender.com` documented as the fallback backend URL only.

## Paid subscriber access audit/migration

Use `backend/scripts/paid_subscriber_access.py` when paid customers from an external billing export need to be checked against application RBAC. The script is dry-run by default and expects an authoritative paid-user source because the application database does not currently store billing records.

Create a CSV with an `email` column from the payment system, then audit:

```bash
PYTHONPATH=backend DATABASE_URL=postgresql://... python backend/scripts/paid_subscriber_access.py \
  --paid-users-csv paid_users.csv
```

After reviewing the table of `email`, `users.role`, `user_roles`, and missing subscriber access, assign subscriber access by adding `subscriber` rows to `user_roles`:

```bash
PYTHONPATH=backend DATABASE_URL=postgresql://... python backend/scripts/paid_subscriber_access.py \
  --paid-users-csv paid_users.csv \
  --apply \
  --confirm ASSIGN_SUBSCRIBER
```

If production operations require updating the legacy `users.role` column instead, add `--assignment-mode users-role` to the apply command.
