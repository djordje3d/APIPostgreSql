# Garage Manage Workspace

This repository is organized in two primary areas:

- `api_python/` - FastAPI + PostgreSQL backend
- `frontend/` - Vue 3 + Tailwind dashboard

The uploaded ticket images directory stays at `fileserver/storage/` (intentionally outside `api_python/`).

## Quick Start

### 1) Backend API

See backend-only commands and setup in `api_python/README.md`.

Most common command from workspace root:

```bash
python -m api_python.app.run
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

- `api_python/` - backend source, migrations, tests, backend docs, backend scripts
- `frontend/` - Vue application
- `fileserver/storage/` - uploaded ticket images storage (unchanged)
- `POSTMAN.md` - Postman usage notes

## Notes

- Backend env is loaded from `api_python/.env` (preferred), with legacy fallback to root `.env`.
- Keep `fileserver/storage/` as-is; only API/frontend code moved under `api_python/` and `frontend/`.

