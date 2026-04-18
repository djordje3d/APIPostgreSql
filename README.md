# Parking API (FastAPI + PostgreSQL)

API for managing parking garages, spots, vehicles, tickets, and payments. Supports entry/exit flow, spot allocation, payment recording for closed tickets, and optional ticket image uploads served under `/uploads`. A Vue 3 dashboard lives in `dashboard/` (see [Frontend](#frontend-optional) below).

## Requirements

- Python 3.10+
- PostgreSQL database

## Setup

1. **Create a virtual environment (recommended):**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**

   Set the following environment variables (or create a `.env` file in the project root). Copy `.env.example` to `.env` as a starting point. The app loads `.env` once at startup from the **project root** (parent of `app/`) via `python-dotenv` in `app/config.py`, so the file is found regardless of the directory you start the server from. Do not commit `.env`.

   | Variable                     | Description                                                                 | Example |
   |------------------------------|-----------------------------------------------------------------------------|---------|
   | `DATABASE_URL`               | PostgreSQL connection URL (required in production; optional for local dev) | `postgresql+psycopg2://user:password@localhost:5432/garaza` |
   | `API_KEY`                    | Optional. If set, protected routes require either `X-API-Key` or `Authorization: Bearer <jwt>`. Omit for local dev with no auth. | `your-secret-key` |
   | `JWT_SECRET_KEY`             | Secret used to sign JWTs (default: change-me-in-production). Set in production. | `your-jwt-secret` |
   | `JWT_ALGORITHM`              | JWT algorithm (default: `HS256`). | `HS256` |
   | `JWT_EXPIRE_MINUTES`         | Access token lifetime in minutes (default: 1440 = 24 hours). Set to `2` to test 2-minute expiry; the dashboard will auto-logout when the token expires. | `1440` |
   | `AUTH_USERNAME`              | Single-user login: username for `POST /auth/login`. When set with `AUTH_PASSWORD` (or `AUTH_PASSWORD_HASH`), login is enabled. | `admin` |
   | `AUTH_PASSWORD`              | Single-user login: plain password. Omit if using `AUTH_PASSWORD_HASH`. | `secret` |
   | `AUTH_PASSWORD_HASH`         | Single-user login: bcrypt-hashed password. When set, `AUTH_PASSWORD` is ignored. | `$2b$12$...` |
   | `AUTH_PREFERRED_LANGUAGE`   | Optional. Preferred language code for login responses (default: `en`). | `en` |
   | `SQL_ECHO`                   | Set to `true` to log SQL statements (default: off)                         | `false` |
   | `USE_API_FEE_CALCULATION`     | Set to `true` if the DB has no trigger for ticket fee/state on exit; the API will compute fee and set ticket_state to CLOSED. Default: `false` (expect DB trigger). | `false` |
   | `USE_API_PAYMENT_STATUS`     | Set to `true` if the DB has no trigger to update ticket payment_status after payments; the API will recalc and update it. Default: `false` (expect DB trigger). | `false` |
   | `CORS_ORIGINS`              | Optional. Comma-separated origins allowed for browser requests (CORS). If unset, defaults to localhost variants. **In production** (when `ENVIRONMENT` or `ENV` is production), must be set if CORS is enabled. | `http://localhost:3000,https://myapp.com` |
   | `CORS_DISABLED`            | Optional. Set to `true` to disable CORS (no CORSMiddleware). Use for server-only or same-origin deployments. Default: `false`. | `false` |
   | `CORS_MAX_AGE`              | Optional. How long (seconds) browsers may cache preflight (OPTIONS) responses. Default: `600`. | `600` |
   | `UPLOAD_TICKET_IMAGE_MAX_BYTES` | Optional. Maximum body size in bytes for ticket image uploads (default: 5 MB). Clients should resize before upload. | `5242880` |

   If `DATABASE_URL` is not set, the app falls back to a default URL (see `app/db.py`). **Do not rely on the default in production;** set `DATABASE_URL` explicitly.

   **Ticket images:** Uploaded files are stored under `static/uploads/` at the project root (see `UPLOAD_DIR` in `app/config.py`) and exposed by the app at **`/uploads/...`** via `StaticFiles`. Upload handling is in `app/routers/upload.py`. For flow and API details, see **[docs/TICKET_IMAGE_UPLOAD.md](docs/TICKET_IMAGE_UPLOAD.md)**.

   **CORS:** The API allows credentials (cookies, `X-API-Key`). Allowed methods are GET, POST, PUT, PATCH, DELETE; allowed headers include `Content-Type`, `Accept`, `Authorization`, `X-API-Key`. Each origin in `CORS_ORIGINS` must start with `http://` or `https://` and have no path (invalid entries are skipped with a log warning). With `ENVIRONMENT=production` or `ENV=production`, invalid or missing `CORS_ORIGINS` cause startup to fail unless `CORS_DISABLED=true`. Set `CORS_DISABLED=true` when the API is only used server-to-server or same-origin (no browser CORS needed).

   **Database with or without triggers:** If your database has triggers that set ticket `fee`/`ticket_state` on exit and `payment_status` after payments, leave `USE_API_FEE_CALCULATION` and `USE_API_PAYMENT_STATUS` unset or `false`. If you use a database without those triggers (e.g. a fresh schema or another DB), set both to `true` so the API performs fee calculation and payment-status updates itself.

   **Authentication (API key and JWT):**
   - **If `API_KEY` is not set**: the middleware does not require auth; all requests are allowed (e.g. local dev).
   - **If `API_KEY` is set**: every request except `GET /`, `GET /health`, `POST /auth/login`, and **`GET` requests under `/uploads/`** (static ticket images) must send either **`X-API-Key`** with the same value **or** **`Authorization: Bearer <token>`** (JWT from `POST /auth/login`). Otherwise the API returns **401 Unauthorized**.
   - **Login:** Set `AUTH_USERNAME` and `AUTH_PASSWORD` (or `AUTH_PASSWORD_HASH`) in `.env` to enable `POST /auth/login`. The dashboard can then log in and use the returned JWT. Set `JWT_SECRET_KEY` in production.

## Database migrations (Alembic)

Schema changes live under `alembic/versions/`. Apply migrations when you point the API at a **new** database, or after pulling commits that add revisions.

1. Ensure PostgreSQL is running and the target database exists (create an empty DB if needed).
2. **URL for Alembic:** `alembic/env.py` reads the database URL from **`sqlalchemy.url` in `alembic.ini`** at the project root. It does **not** read `.env`. Set `sqlalchemy.url` to the same database as **`DATABASE_URL`** so migrations and the running app stay in sync (use the same driver form, e.g. `postgresql+psycopg2://...`).
3. From the **project root** (next to `alembic.ini`), with your venv activated and dependencies installed (see [Setup](#setup); [Alembic](https://alembic.sqlalchemy.org/) is included in `requirements.txt`):

   ```bash
   alembic upgrade head
   ```

   To see the current revision: `alembic current`. To list revisions: `alembic history`.

## How to run

From the project root:

**Option 1 — entry point (recommended):**

```bash
python -m app.run
```

Uses `app/run.py` as the uvicorn entry point. Optional env: `HOST` (default `0.0.0.0`), `PORT` (default `8000`), `RELOAD` (default `true`).

**Option 2 — uvicorn directly:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **`--reload`** — restart the server when code changes (development only).
- **`--host 0.0.0.0`** — listen on all interfaces (optional; omit to bind to localhost only).
- **`--port 8000`** — port number (default is 8000).

- **API docs (Swagger):** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  
- **Health check:** http://localhost:8000/health (returns 200 when app and DB are OK, 503 if the database is unavailable)

## Frontend (optional)

The repo includes a **Vue 3 + Tailwind** garage dashboard in `dashboard/`. Install dependencies, run the dev server, and point it at this API (CORS already allows `http://localhost:5173` by default). Full steps: **[dashboard/README.md](dashboard/README.md)**.

### Postman (and other clients)

When using the API from Postman (or any HTTP client), keep the following in mind:

1. **Authentication (when `API_KEY` is set)**  
   Every request except `GET /`, `GET /health`, `POST /auth/login`, and **`GET /uploads/...`** must include either **`X-API-Key`** or **`Authorization: Bearer <token>`** (get token from `POST /auth/login` with body `{"username":"...","password":"..."}`).  
   - **API key:** In the request’s **Headers** tab, add: Key `X-API-Key`, **Headers** add `X-API-Key`, or in **Collection** → **Authorization** set Type = API Key, Key = `X-API-Key`, Add to = Header.  
   - **Bearer token:** Call `POST /auth/login`, copy `access_token`, then in **Authorization** set Type = Bearer Token and paste it.
   If both are missing or invalid, the API returns **401 Unauthorized**.

2. **Garages – partial vs full update**  
   - **`PATCH /garages/{id}`** — partial update: send only the fields you want to change (e.g. `{"name": "New name"}` or `{"default_rate": 120}`).  
   - **`PUT /garages/{id}`** — full replace: send all garage fields in the body (same as POST create).

See **[POSTMAN.md](POSTMAN.md)** for step-by-step Postman setup and what to show in screenshots (e.g. Headers with `X-API-Key`, PATCH garage example).

## Running tests

Integration tests call the real API and database. Each test runs in a transaction that is rolled back, so the database is not modified. Ensure PostgreSQL is running and `DATABASE_URL` (or the default in `app/db.py`) points to a database you can use for testing.

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_health.py -v
```

Test modules: `test_health`, `test_auth`, `test_garages`, `test_vehicle_types`, `test_vehicles`, `test_spots`, `test_tickets_flow`, `test_payments`.

## Project layout

- `app/main.py` — FastAPI app and route registration (imports `app.config` first so `.env` is loaded before the DB engine is created); mounts `/uploads` for static ticket images
- `app/config.py` — environment variables and flags; loads `.env` via `python-dotenv`; `API_KEY` read once at startup; `UPLOAD_DIR` / upload size limits
- `app/auth.py` — API key and JWT middleware (accepts `X-API-Key` or `Authorization: Bearer <jwt>`)
- `app/auth_jwt.py` — JWT create/verify and FastAPI dependencies
- `app/routers/auth.py` — `POST /auth/login` (returns JWT when `AUTH_USERNAME`/`AUTH_PASSWORD` set)
- `app/routers/upload.py` — ticket image upload endpoints
- `app/routers/dashboard.py` — aggregated dashboard metrics for the UI
- `app/db.py` — database engine, session, and `get_db` dependency (expects env already loaded by config)
- `app/models.py` — SQLAlchemy models
- `app/schemas.py` — Pydantic request/response schemas
- `app/routers/` — API route handlers (garages, vehicle-types, vehicles, tickets, payments, spots, upload, dashboard)
- `app/services/` — business logic (e.g. spot allocation, pricing, payment status)
- `alembic/` — Alembic migration scripts (`alembic upgrade head` from project root)
- `alembic.ini` — Alembic config; `sqlalchemy.url` must point at the database you migrate
- `static/uploads/` — on-disk storage for uploaded ticket images (served under `/uploads`)
- `dashboard/` — Vue 3 frontend (see [dashboard/README.md](dashboard/README.md))
- `docs/` — additional documentation (e.g. [TICKET_IMAGE_UPLOAD.md](docs/TICKET_IMAGE_UPLOAD.md))
- `scripts/` — utility scripts (e.g. presentation builder)
- `tests/` — API integration tests (pytest, transactional rollback isolation)
