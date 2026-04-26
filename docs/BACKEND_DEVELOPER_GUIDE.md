# Backend Developer Guide

This guide explains how to work on the Python backend in this repository.
It is intended for day-to-day development: understanding structure, adding endpoints, running migrations, and debugging locally.

## 1) Project architecture

The backend follows a layered structure in `app/`:

- `app/main.py`
  - FastAPI app creation, middleware, OpenAPI setup, router registration.
  - Mounts static uploads under `/uploads`.

- `app/routers/`
  - HTTP layer only.
  - Defines endpoints, query/path/body parameters, response models.
  - Handles HTTP-focused concerns (status codes, request validation, error mapping).
  - Should stay thin: delegate business rules to `app/services/`.

- `app/services/`
  - Business/domain logic.
  - Orchestrates model reads/writes and complex workflows (ticket entry/exit, pricing, payment status, spot allocation).
  - Raises domain exceptions that routers convert into API errors.

- `app/schemas.py`
  - Pydantic request/response models.
  - Validation and serialization rules.
  - Shared types (for example: `TicketState`, `PaymentStatus`, paginated responses).

- `app/models.py`
  - SQLAlchemy ORM models mapped to database tables.
  - Database structure and relationships used by the app.

- `app/db.py`
  - Engine/session setup and `get_db()` dependency used by routers/services.

- `app/errors.py` and `app/error_handlers.py`
  - Standardized API error payloads and global exception handling.

- `app/config.py`
  - Environment-based configuration loaded at startup.

Rule of thumb:
- Router = HTTP contract
- Service = domain behavior
- Schema = API data shape
- Model = persistence shape

## 2) Coding conventions

### Typing

- Use Python type hints everywhere (function args/returns, local variables when helpful).
- Keep router signatures explicit (`int | None`, `datetime | None`, etc.).
- Keep schema fields precise (`Decimal` for money, `Literal[...]` for constrained enums).
- Prefer typed exceptions for domain failures in services.

### Error handling

- In services:
  - Raise domain-specific exceptions for expected business failures.
  - Avoid returning mixed success/error tuples.

- In routers:
  - Catch known domain exceptions and map to consistent API errors via `api_error(...)`.
  - Use stable error codes (`TICKET_NOT_FOUND`, `SPOT_OCCUPIED`, etc.).
  - Keep unexpected exceptions for global handlers unless there is a good reason to intercept.

- In API responses:
  - Keep error body structure consistent across endpoints.
  - Prefer explicit status codes (`400`, `401`, `404`, `409`, `500`, `503`) according to failure type.

### Database transactions

- One request should generally use one DB session from `get_db()`.
- For write operations:
  - Perform work in services/routers.
  - `commit()` once after a successful unit of work.
  - On `IntegrityError` or expected DB conflict: `rollback()` and return a clear API error.
- Avoid partial commits in the middle of a multi-step workflow unless intentionally required.

### General style

- Keep routers thin and readable.
- Keep business logic out of schemas.
- Add short comments only when logic is non-obvious.
- Use UTC-aware datetimes consistently.

## 3) Add a new endpoint end-to-end

Use this checklist when implementing new API functionality.

1. Define API contract in `app/schemas.py`
   - Add request model(s) and response model(s).
   - Add validation constraints (`Field`, `Literal`, length/range bounds) as needed.

2. Add or update domain logic in `app/services/`
   - Implement business rules in a focused service function.
   - Use/extend domain exceptions for expected failure states.

3. Add endpoint in the appropriate router (`app/routers/*.py`)
   - Add route decorator, params, and `response_model`.
   - Call the service function.
   - Map service exceptions to API errors.
   - Keep endpoint body short and HTTP-oriented.

4. Register router if it is new
   - Include it in `app/main.py` with `app.include_router(...)`.

5. Verify OpenAPI docs
   - Start server and inspect `/docs`.
   - Confirm request/response schema shape and examples are clear.

6. Add tests in `tests/`
   - Happy path test.
   - Validation failure test(s).
   - Domain/conflict/error test(s).
   - List/filter/pagination checks if applicable.

7. Update documentation
   - Update `README.md` or feature-specific docs in `docs/` if behavior is user-visible.
   - Update `POSTMAN.md` when endpoint impacts API usage examples.

## 4) Migration workflow (Alembic)

This project uses Alembic for schema evolution in `alembic/versions/`.

### When to run migrations

- New environment setup.
- Pulling changes that include new migration revisions.
- Before running backend tests against a fresh database.

### Typical workflow

1. Ensure target PostgreSQL database exists.
2. Set `sqlalchemy.url` in `alembic.ini` to the same DB used by app `DATABASE_URL`.
3. Apply all migrations:

```bash
alembic upgrade head
```

4. Verify revision state:

```bash
alembic current
alembic history
```

### Creating a new migration (when model/schema changes require DB change)

```bash
alembic revision -m "describe_change"
```

Then implement `upgrade()`/`downgrade()` in the new revision file and run `alembic upgrade head` locally.

Tip: keep migrations small and focused, one logical schema change per revision when possible.

## 5) Test strategy

Current tests are integration-style and live in `tests/`.

- Tests call real API routes and use a real database connection.
- Test isolation is transaction-based (each test is rolled back).
- Focus areas already covered include:
  - health/auth
  - garages/vehicle types/vehicles
  - spots
  - ticket flow (entry/exit)
  - payments

Recommended additions for new features:

- At least one happy path and one failure path.
- Boundary-value tests for validation constraints.
- Authorization tests when endpoint is protected.
- Regression tests for previously fixed bugs.

Run tests:

```bash
pytest -v
```

Run specific module:

```bash
pytest tests/test_health.py -v
```

## 6) Local debugging tips

### Start backend in dev mode

From project root:

```bash
python -m app.run
```

Alternative:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful URLs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

### Environment and auth checks

- Confirm `.env` values are set correctly (`DATABASE_URL`, auth values, feature flags).
- If `API_KEY` is set, send either `X-API-Key` or Bearer JWT on protected routes.
- Use `POST /auth/login` to quickly verify login/JWT flow.

### Database and migrations

- If app starts but endpoints fail with DB errors, verify:
  - DB is running.
  - `DATABASE_URL` is correct.
  - Alembic migrations are up to date.

### CORS and frontend integration

- For dashboard/API local integration, ensure backend CORS allows frontend origin (for example `http://localhost:5173`).
- Restart services after changing `.env` values.

### Quick troubleshooting checklist

- `401 Unauthorized`: wrong/missing API key or expired/invalid JWT.
- `409 Conflict`: business rule conflict (already occupied spot, invalid state transition, overpayment, etc.).
- `503` on `/health`: database not reachable.
- Upload issues: verify writable `static/uploads/` and file size/type limits.

## 7) Practical contributor checklist

Before opening a PR:

- Run migrations (if schema changed).
- Run tests (`pytest -v`).
- Verify endpoint behavior in `/docs`.
- Update relevant docs (`README.md`, `docs/*`, `POSTMAN.md`).
- Keep router/service/schema/model responsibilities separated.
