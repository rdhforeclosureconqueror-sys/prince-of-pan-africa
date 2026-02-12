# Repository Consolidation Notes

This repository now contains both:
- Existing Prince of Pan-Africa frontend (current root structure kept intact to avoid breaking live builds).
- New Mufasa Knowledge Bank backend under `backend/`.

## Logical structure
- `backend/` → FastAPI service for Mufasa Knowledge Bank.
- `frontend/` → frontend documentation and maintenance notes.
- `config/` → monorepo deployment and environment templates.
- `docs/` → integration docs and system notes.

## Why frontend files were not physically moved
Live behavior is preserved by leaving existing frontend build paths unchanged (`src`, `public`, `package.json`, `vite.config.js`).
A future migration can move frontend files into `frontend/` once deployment paths are updated.
