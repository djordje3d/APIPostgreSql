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

   Set the following environment variables (or create a `.env` file in the project root and load it with e.g. `python-dotenv`; do not commit `.env`).

   | Variable       | Description                                                                 | Example |
   |----------------|-----------------------------------------------------------------------------|---------|
   | `DATABASE_URL` | PostgreSQL connection URL (required in production; optional for local dev) | `postgresql+psycopg2://user:password@localhost:5432/garaza` |
   | `SQL_ECHO`     | Set to `true` to log SQL statements (default: off)                         | `false` |

   If `DATABASE_URL` is not set, the app falls back to a default URL (see `app/db.py`). **Do not rely on the default in production;** set `DATABASE_URL` explicitly.

## How to run

From the project root:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **`--reload`** — restart the server when code changes (development only).
- **`--host 0.0.0.0`** — listen on all interfaces (optional; omit to bind to localhost only).
- **`--port 8000`** — port number (default is 8000).

Alternatively, run the app as a module:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- **API docs (Swagger):** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  
- **Health check:** http://localhost:8000/health (returns 200 when app and DB are OK, 503 if the database is unavailable)

## Running tests

Integration tests call the real API and database. Ensure PostgreSQL is running and `DATABASE_URL` (or the default in `app/db.py`) points to a database you can use for testing.

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

## Project layout

- `app/main.py` — FastAPI app and route registration
- `app/db.py` — database engine, session, and `get_db` dependency
- `app/models.py` — SQLAlchemy models
- `app/schemas.py` — Pydantic request/response schemas
- `app/routers/` — API route handlers (garages, vehicle-types, vehicles, tickets, payments, spots)
- `app/services/` — business logic (e.g. spot allocation)
- `tests/` — API integration tests (pytest)
