# Leadership Assessment Integration

## Frontend framework + routing
- Framework: **React + Vite**
- Router: **react-router-dom** in `src/App.jsx`

## New Routes
- `GET /leadership` — 30-question public assessment form
- `GET /results?userId=<id>` — dynamic results dashboard

## API Configuration
Set your Google Apps Script Web App URL in frontend env:

```bash
VITE_LEADERSHIP_API_URL="https://script.google.com/macros/s/.../exec"
```

If this variable is not set, the app runs in simulation mode so UX can still be validated end-to-end.

## Payload contract used by frontend
### Request
```json
{
  "userId": "string",
  "answers": ["1", "2", "3", "4", "5", "..."]
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
  "coaching": "string"
}
```

## Extensibility notes
- Service layer is centralized in `src/services/leadershipService.js` for easy migration to authenticated storage.
- Results are currently cached in browser localStorage by `userId`; this can later be replaced with user-account persistence.
