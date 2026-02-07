# API Project Analysis & Suggestions for Improvement

This document is a full review of your **Parking API** (FastAPI + PostgreSQL): what works well, what could be improved, and concrete suggestions.

---

## 1. Project overview

The API manages:

- **Garages** (`parking_config`) – capacity, rates, opening hours
- **Parking spots** – per garage, with `code`, `is_rentable`, `is_active`
- **Vehicle types** – type name and hourly rate
- **Vehicles** – licence plate, type, status
- **Tickets** – entry/exit, fee, state, payment status; optional spot assignment
- **Payments** – linked to closed tickets, with overpayment checks

Notable features: optional API-key auth, CORS configuration (including production checks), configurable fee/payment-status logic (API vs DB triggers), spot allocation with `FOR UPDATE SKIP LOCKED`, and solid validation via Pydantic and Literals.

---

## 2. What’s working well

### Architecture

- Clear separation: **routers** (HTTP), **services** (business logic), **schemas** (validation/serialization), **models** (ORM). Easy to navigate and test.
- **Config** is centralized in `app/config.py` with env-based flags (`USE_API_FEE_CALCULATION`, `USE_API_PAYMENT_STATUS`, CORS). Good for different deployments (with/without DB triggers).
- **Dependencies**: `get_db()` used consistently; routers stay thin.

### API design

- **REST-style** resources and methods: list (GET), create (POST), get by id (GET), full replace (PUT) where needed, partial update (PATCH) for garages, vehicles, spots, tickets; delete (DELETE) with integrity handling.
- **Paginated lists** with `limit`/`offset` and `PaginatedResponse[T]` for garages, vehicle types, vehicles, tickets, spots, and payments-by-ticket.
- **Route order**: e.g. `GET /payments/by-ticket/{ticket_id}` is registered before `GET /payments/{payment_id}` — no “by-ticket” path eaten by id.
- **Literals** for `TicketState`, `PaymentStatus`, `OperationalStatus` in schemas and query params give clear validation and docs.

### Business logic

- **Ticket entry**: Validates vehicle, garage, optional spot (same garage, active, not occupied); otherwise allocates a free spot via `allocate_free_spot()` with `FOR UPDATE SKIP LOCKED` to avoid races.
- **Ticket exit**: Only for OPEN tickets; when `USE_API_FEE_CALCULATION` is true, fee and `ticket_state=CLOSED` are set in the API; otherwise DB trigger can do it.
- **Payments**: Only for CLOSED tickets; overpayment rejected (total paid + new amount ≤ ticket fee); when `USE_API_PAYMENT_STATUS` is true, payment status is recalculated after create/update/delete.
- **Deletes**: Garages, vehicle types, vehicles, tickets, payments, and spots handle `IntegrityError` and return clear 400 messages. Spot “delete” is implemented as deactivation (and activation endpoint exists).

### Security & config

- **API key**: Optional `X-API-Key` when `API_KEY` is set in config (read once at startup; no per-request env lookup); `/health` is excluded. OpenAPI schema includes the security scheme so Swagger can send the key.
- **CORS**: Configurable origins, methods, headers, max_age; production mode requires explicit `CORS_ORIGINS` (or `CORS_DISABLED=true`). Validation rejects invalid origins.
- **Health**: `/health` runs `SELECT 1` and returns 503 if the DB is unavailable — good for load balancers.
- **Env loading**: `.env` is loaded only in `app/config.py`; `app/main.py` imports config before db so `DATABASE_URL` is available when the engine is created; `app/db.py` documents this order.

### Code quality

- **Datetime**: `datetime.now(timezone.utc)` is used (no deprecated `utcnow()`).
- **Pydantic v2**: `model_config = ConfigDict(from_attributes=True)` and `model_dump(exclude_unset=True)` for partial updates.
- **Tests**: Integration tests with transactional rollback isolation (`conftest.py`). Coverage includes health, garages, vehicle types, vehicles (create, get by id/plate, 404, PATCH, delete with tickets), spots (create, duplicate code, list by garage_id/only_free, deactivate/activate), tickets (entry/exit, list filters), and payments (create for closed ticket, overpayment rejected, list by ticket).
- **Docs**: README and POSTMAN.md explain setup, env vars, and usage.

---

## 3. Suggestions for improvement

### 3.1 Critical / security

**Hardcoded database URL and password (`app/db.py`)**

- **Current**: `DATABASE_URL` defaults to a URL that contains a literal password. If the repo is shared or deployed, this is a security risk.
- **Suggestion**:  
  - Prefer no default with credentials. For example: `DATABASE_URL = os.getenv("DATABASE_URL")` and fail at startup if unset (or only in production).  
  - Or keep a default only for local dev (e.g. `postgresql+psycopg2://user:pass@localhost:5432/garaza`) and document that **production must set `DATABASE_URL`** and never commit real credentials.  
  You already use `python-dotenv` in config; ensure `db.py` does not override with a default that includes real passwords in production.

**SQL logging (`app/db.py`)** — **Addressed**

- **Current**: `db.py` uses `echo=os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "yes")`; SQL is logged only when `SQL_ECHO` is set. README documents `SQL_ECHO`.

### 3.2 Consistency and robustness

**Config loading and import order** — **Addressed**

- **Current**: `.env` is loaded only in `app/config.py`. `app/main.py` imports `app.config` before `app.db` (documented in a comment in `main.py`). `app/db.py` does not call `load_dotenv()` and documents that the entry point must import config first so `DATABASE_URL` is available when the engine is created.

**Run entry point (`app/run.py`)** — **Addressed**

- **Current**: `run.py` is the uvicorn entry point (`python -m app.run`); it reads `HOST`, `PORT`, `RELOAD` from env and runs `uvicorn.run("app.main:app", ...)`. README documents this.

**Vehicle create with `licence_plate is None`**

- **Current**: Uniqueness is checked only when `data.licence_plate is not None`, so multiple vehicles with `licence_plate is None` are allowed. That may be intended (e.g. “unknown” vehicles).
- **Suggestion**: If that is the intended rule, add a short comment in the router or schema. If only one “unknown” vehicle should exist, add a check for an existing row with `licence_plate IS NULL` and return 400 in that case.

### 3.3 API and validation

**Payment method and currency**

- **Current**: `PaymentCreate.method` is a free-form string; `currency` defaults to `"RSD"` and is a string. DB has `method` as `String(20)`, `currency` as `String(3)`.
- **Suggestion**: Optionally restrict `method` and `currency` (e.g. `Literal["CASH", "CARD", "BANK"]` and a small set of currency codes) and/or add `max_length` in Pydantic so validation and OpenAPI stay aligned with the DB and business rules.

**Garage create/update types** — **Addressed**

- **Current**: `GarageCreate` and `GarageUpdate` use `Decimal` for rates and monetary fields; consistent with `GarageResponse` and the DB.

### 3.4 Structure and maintainability

**Pyright and `main.py`**

- **Current**: `# pyright: reportMissingImports=false` at the top of `main.py` disables missing-import checks for the whole file.
- **Suggestion**: Prefer fixing or typing the imports (e.g. `dotenv` in config) and removing the directive, or limit the directive to the few lines that need it so the rest of the file is still checked.

**Optional relationships on models**

- **Current**: `ParkingConfig` has no `relationship` to `ParkingSpot` or `Ticket`. Other models have relationships where needed.
- **Suggestion**: If you often need “all spots for a garage” or “all tickets for a garage”, adding e.g. `spots = relationship("ParkingSpot", back_populates="garage")` (and backrefs on spots) can simplify code and avoid extra queries. Optional and only if it improves readability.

### 3.5 Testing and ops

**Test isolation** — **Addressed**

- **Current**: `conftest.py` runs each test in a transaction that is rolled back; the app’s `get_db` is overridden so `commit()` only flushes. The database is not modified by tests; sequences are reset once per run so IDs remain valid after rollbacks.

**Test coverage** — **Addressed**

- **Current**: Tests cover health; garages (list, create, get, 404); vehicle types (list, create, etc.); vehicles (create, get by id, get by plate, 404, PATCH, delete with tickets → 400); spots (list, create, duplicate code → 400, filter by garage_id, only_free, deactivate, activate, 404); tickets (list, entry, exit, filters by state/payment_status/garage_id, 404); payments (create for closed ticket, open ticket → 400, overpayment → 400, list by ticket, 404).

---

## 4. Summary table

| Area                    | Status / suggestion |
|-------------------------|---------------------|
| Architecture            | Good separation; keep routers thin and services for logic. |
| Pagination & route order| In good shape. |
| Auth & CORS             | Solid; API key read once at startup from config; CORS config clear. |
| Fee / payment status    | Flexible (API vs DB); services used when flags are on. |
| Security                | **SQL_ECHO** is configurable (addressed). Consider removing or restricting default DB URL with credentials for production. |
| Config / env            | Addressed: `.env` loaded only in config; main imports config before db; documented. |
| Run entry point         | Addressed: `run.py` is the uvicorn entry point; documented. |
| Schemas                 | Garages use `Decimal`; optional Literals for payment method/currency. |
| Tests                   | Addressed: transactional rollback isolation; coverage for health, garages, vehicle types, vehicles, spots, tickets, payments. |
| Type checking           | Prefer targeted pyright over disabling for whole file. |

---

## 5. Opinion

The project is in good shape: clear structure, sensible API design, and careful handling of entry/exit, payments, and constraints. **Already addressed**: env loading (single place in config, import order documented), run entry point (`run.py`), SQL logging (`SQL_ECHO`), API key (read once at startup), and test coverage/isolation (transactional rollback, tests for all main resources). The main remaining gap is **security**: the default `DATABASE_URL` in `db.py` still contains a literal password; for production, require `DATABASE_URL` to be set and avoid a default with real credentials. The rest are incremental improvements (schemas, optional model relationships, type checking) that you can adopt as you go.
