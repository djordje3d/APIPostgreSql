# Parking API (FastAPI + PostgreSQL)

API for managing parking garages, spots, vehicles, tickets, and payments. Supports entry/exit flow, spot allocation, and payment recording for closed tickets.

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
   | `API_KEY`                    | Optional. If set, all requests (except `GET /health`) must include header `X-API-Key: <value>`. Omit for local dev with no auth. | `your-secret-key` |
   | `SQL_ECHO`                   | Set to `true` to log SQL statements (default: off)                         | `false` |
   | `USE_API_FEE_CALCULATION`     | Set to `true` if the DB has no trigger for ticket fee/state on exit; the API will compute fee and set ticket_state to CLOSED. Default: `false` (expect DB trigger). | `false` |
   | `USE_API_PAYMENT_STATUS`     | Set to `true` if the DB has no trigger to update ticket payment_status after payments; the API will recalc and update it. Default: `false` (expect DB trigger). | `false` |
   | `CORS_ORIGINS`              | Optional. Comma-separated origins allowed for browser requests (CORS). If unset, defaults to localhost variants. **In production** (when `ENVIRONMENT` or `ENV` is production), must be set if CORS is enabled. | `http://localhost:3000,https://myapp.com` |
   | `CORS_DISABLED`            | Optional. Set to `true` to disable CORS (no CORSMiddleware). Use for server-only or same-origin deployments. Default: `false`. | `false` |
   | `CORS_MAX_AGE`              | Optional. How long (seconds) browsers may cache preflight (OPTIONS) responses. Default: `600`. | `600` |

   If `DATABASE_URL` is not set, the app falls back to a default URL (see `app/db.py`). **Do not rely on the default in production;** set `DATABASE_URL` explicitly.

   **CORS:** The API allows credentials (cookies, `X-API-Key`). Allowed methods are GET, POST, PUT, PATCH, DELETE; allowed headers include `Content-Type`, `Accept`, `Authorization`, `X-API-Key`. Each origin in `CORS_ORIGINS` must start with `http://` or `https://` and have no path (invalid entries are skipped with a log warning). With `ENVIRONMENT=production` or `ENV=production`, invalid or missing `CORS_ORIGINS` cause startup to fail unless `CORS_DISABLED=true`. Set `CORS_DISABLED=true` when the API is only used server-to-server or same-origin (no browser CORS needed).

   **Database with or without triggers:** If your database has triggers that set ticket `fee`/`ticket_state` on exit and `payment_status` after payments, leave `USE_API_FEE_CALCULATION` and `USE_API_PAYMENT_STATUS` unset or `false`. If you use a database without those triggers (e.g. a fresh schema or another DB), set both to `true` so the API performs fee calculation and payment-status updates itself.

   **API key and .env:**
   - **If `API_KEY` is not set** (missing or empty in `.env`): the middleware does nothing; **all requests are allowed** and no key is required. This is why Postman (or curl) may work without sending `X-API-Key`.
   - **If `API_KEY` is set**: every request except `GET /health` must send the header `X-API-Key` with the same value, or the API returns **401 Unauthorized**. Add `API_KEY=your-secret-key` to `.env` in the project root, start the server from the project root (e.g. `python -m app.run`), and **restart the server** after changing `.env` so the new value is picked up.

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

### Postman (and other clients)

When using the API from Postman (or any HTTP client), keep the following in mind:

1. **API key (when `API_KEY` is set in `.env`)**  
   Every request except `GET /health` must include the header **`X-API-Key`** with the same value as in your `.env`.  
   - **Per request:** In the request’s **Headers** tab, add: Key `X-API-Key`, Value `your-secret-key` (or your actual key).  
   - **For all requests:** In the **Collection** → **Authorization** tab, set Type to **API Key**, Key = `X-API-Key`, Value = your key, and Add to **Header**.  
   If the key is missing or wrong, the API returns **401 Unauthorized**.

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

- `app/main.py` — FastAPI app and route registration (imports `app.config` first so `.env` is loaded before the DB engine is created)
- `app/config.py` — environment variables and flags; loads `.env` via `python-dotenv`; `API_KEY` read once at startup
- `app/auth.py` — API key middleware (uses `API_KEY` from config)
- `app/db.py` — database engine, session, and `get_db` dependency (expects env already loaded by config)
- `app/models.py` — SQLAlchemy models
- `app/schemas.py` — Pydantic request/response schemas
- `app/routers/` — API route handlers (garages, vehicle-types, vehicles, tickets, payments, spots)
- `app/services/` — business logic (e.g. spot allocation, pricing, payment status)
- `tests/` — API integration tests (pytest, transactional rollback isolation)
