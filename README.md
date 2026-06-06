# Garage Manage Workspace

Parking garage management: FastAPI + PostgreSQL backend and a Vue 3 dashboard for live status, tickets, payments, and analytics.

## Repository layout

| Path | Role |
|------|------|
| `api_python/` | FastAPI backend, Alembic migrations, tests, backend docs |
| `frontend_vue/` | Vue 3 + TypeScript + Tailwind dashboard |
| `fileserver/storage/` | Uploaded ticket images (intentionally outside `api_python/`) |

## Prerequisites

- **Python 3.10+** and **PostgreSQL** (backend)
- **Node.js 18+** (frontend and ticket image file server)

## Local development

Run these from the **workspace root** unless noted.

### 1. Backend setup (once)

```bash
pip install -r api_python/requirements.txt
```

Configure `api_python/.env` (preferred; legacy fallback to root `.env` is supported). At minimum you need `DATABASE_URL` and login credentials (`AUTH_USERNAME` / `AUTH_PASSWORD` or `AUTH_PASSWORD_HASH`). See [api_python/README.md](api_python/README.md) for details.

Apply migrations:

```bash
alembic -c api_python/alembic.ini upgrade head
```

### 2. Start services

| Service | Command | URL |
|---------|---------|-----|
| **API** | `python -m api_python.app.run` | http://localhost:8000 |
| **Swagger / ReDoc** | (with API running) | http://localhost:8000/docs · http://localhost:8000/redoc |
| **Health** | (with API running) | http://localhost:8000/health |
| **Ticket images** | `cd fileserver/storage && npm install && npm run dev` | http://localhost:9009 |
| **Dashboard** | `cd frontend_vue && npm install && npm run dev` | http://localhost:5173 |

Start the API first. For ticket images in the UI, run the file server. Ensure backend `CORS_ORIGINS` includes `http://localhost:5173` when using the dashboard locally.

Optional: copy `frontend_vue/env.example` to `frontend_vue/.env` to override `VITE_API_URL` or `VITE_FILESERVER_URL`.

### 3. Authentication

- The **dashboard** requires JWT sign-in (`/login`) for all routes except login itself.
- The **API** optionally enforces `X-API-Key` or `Authorization: Bearer <jwt>` when `API_KEY` is set in `api_python/.env`. After login, the dashboard sends the JWT.

More detail: [frontend_vue/README.md](frontend_vue/README.md#authentication).

## Tests

```bash
pytest api_python/tests -v
```

## Further reading

- [api_python/README.md](api_python/README.md) — backend setup, migrations, tests
- [api_python/docs/BACKEND_DEVELOPER_GUIDE.md](api_python/docs/BACKEND_DEVELOPER_GUIDE.md) — backend architecture and conventions
- [api_python/docs/TICKET_IMAGE_UPLOAD.md](api_python/docs/TICKET_IMAGE_UPLOAD.md) — ticket image upload flow
- [frontend_vue/README.md](frontend_vue/README.md) — dashboard setup, auth, i18n, troubleshooting
- [POSTMAN.md](POSTMAN.md) — Postman collection setup

## Notes

- Backend env is loaded from `api_python/.env` first, with legacy fallback to root `.env`.
- Keep `fileserver/storage/` at the workspace root; only application code lives under `api_python/` and `frontend_vue/`.
