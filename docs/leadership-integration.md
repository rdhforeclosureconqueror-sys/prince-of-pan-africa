# Leadership Assessment Integration

## Frontend framework + routing
- Framework: **React + Vite**
- Router: **react-router-dom** in `src/App.jsx`

## New Routes
- `GET /leadership` — 30-question public assessment form
- `GET /results?userId=<id>` — dynamic results dashboard

## Backend API Endpoints
- `POST /assessment/submit`
- `GET /assessment/results/{userId}`
- `GET /assessment/analytics/roles`

## API Configuration
Set your backend base URL in frontend env:

```bash
VITE_API_BASE_URL="https://mufasa-knowledge-bank.onrender.com"
```

If this variable is not set or the API call fails, the app falls back to simulation mode so UX can still be validated end-to-end.

## Payload contract used by frontend
### Request
```json
{
  "userId": "string",
  "responses": ["1", "2", "3", "4", "5", "..."]
}
```

### Expected Response
```json
{
  "userId": "string",
  "percentages": {
    "architect": 0,
    "operator": 0,
    "steward": 0,
    "builder": 0,
    "connector": 0,
    "protector": 0,
    "nurturer": 0,
    "educator": 0,
    "resourceGenerator": 0
  },
  "roles": {
    "primary": "Architect",
    "secondary": "Operator",
    "growth": "Educator",
    "shadow": "Nurturer"
  },
  "coaching": "string",
  "insights": {
    "primary": "string",
    "growth": "string",
    "shadow": "string"
  },
  "version": "v1"
}
```

## Extensibility notes
- Service layer is centralized in `src/services/leadershipService.js` for easy migration to authenticated storage.
- Results are currently cached in browser localStorage by `userId`; this can later be replaced with user-account persistence.
