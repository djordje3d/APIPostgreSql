# Garage Manage Workspace

This repository is organized in two primary areas:

- `api/` - FastAPI + PostgreSQL backend
- `frontend/` - Vue 3 + Tailwind dashboard

The uploaded ticket images directory stays at `fileserver/storage/` (intentionally outside `api/`).

## Quick Start

### 1) Backend API

See backend-only commands and setup in `api/README.md`.

Most common command from workspace root:

```bash
python -m api.app.run
```

API URLs:

- Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health: <http://localhost:8000/health>

### 2) Frontend

See `frontend/README.md` for frontend setup.

Typical local run:

```bash
cd frontend
npm install
npm run dev
```

## Layout

- `api/` - backend source, migrations, tests, backend docs, backend scripts
- `frontend/` - Vue application
- `fileserver/storage/` - uploaded ticket images storage (unchanged)
- `POSTMAN.md` - Postman usage notes

## Notes

- Root `.env` is still used by the backend (`api/app/config.py` loads from workspace root).
- Keep `fileserver/storage/` as-is; only API/frontend code moved under `api/` and `frontend/`.
