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
- `SESSION_COOKIE_SAMESITE` (defaults to `lax`; set to `none` for the current cross-site Render fallback)
- `SESSION_COOKIE_DOMAIN` (optional; leave unset/empty while the browser-facing backend is `prince-of-pan-africa-backend.onrender.com`; use `.simbawaujamaa.com` only after the API is served from a live `api.simbawaujamaa.com`)

## Production API host note

Current frontend production fallback should use `https://prince-of-pan-africa-backend.onrender.com`. Do not point production to `https://api.simbawaujamaa.com` until Render has attached that custom domain to `prince-of-pan-africa-backend`, TLS is active, `GET /health` returns the backend response, and the suspended-service page is gone.

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
