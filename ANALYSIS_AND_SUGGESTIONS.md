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

- **API key**: Optional `X-API-Key` when `API_KEY` is set; `/health` is excluded. OpenAPI schema includes the security scheme so Swagger can send the key.
- **CORS**: Configurable origins, methods, headers, max_age; production mode requires explicit `CORS_ORIGINS` (or `CORS_DISABLED=true`). Validation rejects invalid origins.
- **Health**: `/health` runs `SELECT 1` and returns 503 if the DB is unavailable — good for load balancers.

### Code quality

- **Datetime**: `datetime.now(timezone.utc)` is used (no deprecated `utcnow()`).
- **Pydantic v2**: `model_config = ConfigDict(from_attributes=True)` and `model_dump(exclude_unset=True)` for partial updates.
- **Tests**: Integration tests for health, garages, vehicle types, and ticket entry flow; `TestClient` against the real app and DB.
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

**SQL logging always on (`app/db.py`)**

- **Current**: `create_engine(DATABASE_URL, echo=True)` — every SQL statement is logged. Noisy and can leak sensitive data in production.
- **Suggestion**: Make it configurable, e.g. `echo=os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "yes")`. Your README already mentions `SQL_ECHO`; wiring it in `db.py` keeps behavior consistent with docs.

### 3.2 Consistency and robustness

**Config loading in `db.py`**

- **Current**: `db.py` reads `DATABASE_URL` via `os.getenv()` but does not call `load_dotenv()`. If the app is started without loading `.env` first (e.g. if only `config` is imported before `db`), the fallback URL might be used even when `.env` is present.
- **Suggestion**: Either call `load_dotenv()` at the top of `db.py` (like `config.py`), or document that `config` (or `main`) must be imported first so that `load_dotenv()` runs before any code that uses `DATABASE_URL`. Prefer one clear place (e.g. `main.py` or `config.py`) that loads env and then import `db` after.

**Empty `app/run.py`**

- **Current**: File is empty. Run command is `uvicorn app.main:app ...`.
- **Suggestion**: Either remove `run.py` or use it as the entry point, e.g.:

  ```python
  import uvicorn
  if __name__ == "__main__":
      uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
  ```

  Then you can run with `python -m app.run` and keep README in sync.

**Vehicle create with `licence_plate is None`**

- **Current**: Uniqueness is checked only when `data.licence_plate is not None`, so multiple vehicles with `licence_plate is None` are allowed. That may be intended (e.g. “unknown” vehicles).
- **Suggestion**: If that is the intended rule, add a short comment in the router or schema. If only one “unknown” vehicle should exist, add a check for an existing row with `licence_plate IS NULL` and return 400 in that case.

### 3.3 API and validation

**Payment method and currency**

- **Current**: `PaymentCreate.method` is a free-form string; `currency` defaults to `"RSD"` and is a string. DB has `method` as `String(20)`, `currency` as `String(3)`.
- **Suggestion**: Optionally restrict `method` and `currency` (e.g. `Literal["CASH", "CARD", "BANK"]` and a small set of currency codes) and/or add `max_length` in Pydantic so validation and OpenAPI stay aligned with the DB and business rules.

**Garage create/update types**

- **Current**: `GarageCreate` / `GarageUpdate` use `float` for rates; DB and responses use `Decimal`. FastAPI/Pydantic will coerce, but using `Decimal` in schemas would match the domain and avoid float rounding in validation.
- **Suggestion**: Use `Decimal` (or `condecimal`) for monetary and rate fields in create/update schemas for consistency with `GarageResponse` and the DB.

### 3.4 Structure and maintainability

**Pyright and `main.py`**

- **Current**: `# pyright: reportMissingImports=false` at the top of `main.py` disables missing-import checks for the whole file.
- **Suggestion**: Prefer fixing or typing the imports (e.g. `dotenv` in config) and removing the directive, or limit the directive to the few lines that need it so the rest of the file is still checked.

**Optional relationships on models**

- **Current**: `ParkingConfig` has no `relationship` to `ParkingSpot` or `Ticket`. Other models have relationships where needed.
- **Suggestion**: If you often need “all spots for a garage” or “all tickets for a garage”, adding e.g. `spots = relationship("ParkingSpot", back_populates="garage")` (and backrefs on spots) can simplify code and avoid extra queries. Optional and only if it improves readability.

### 3.5 Testing and ops

**Test isolation**

- **Current**: Integration tests hit the real database; test_garages and test_tickets_flow create real rows (garages, spots, vehicles, tickets).
- **Suggestion**: For stability and parallel runs, consider: (a) a dedicated test DB and cleaning key tables in `conftest.py` (e.g. in a fixture with `yield`), or (b) using transactions/rollback so each test runs in an isolated transaction. That reduces interference and makes tests more predictable.

**More coverage**

- **Current**: Health, garages, vehicle types, and one ticket flow are covered.
- **Suggestion**: Add tests for: payments (create for closed ticket, overpayment rejected, list by ticket); spots (create, filter by garage/active/free, deactivate); vehicles (create, get by plate, 404); tickets (exit, list filters). Even a few tests per resource will catch regressions.

---

## 4. Summary table

| Area                    | Status / suggestion |
|-------------------------|---------------------|
| Architecture            | Good separation; keep routers thin and services for logic. |
| Pagination & route order| In good shape. |
| Auth & CORS             | Solid; API key and CORS config are clear. |
| Fee / payment status    | Flexible (API vs DB); services used when flags are on. |
| Security                | Remove or restrict default DB URL with credentials; make `echo` configurable. |
| Config / env            | Ensure `.env` is loaded before `db` uses `DATABASE_URL`. |
| Run entry point         | Use or remove `run.py` and document. |
| Schemas                 | Consider `Decimal` for money/rates; optional Literals for payment method/currency. |
| Tests                   | Add payment/spot/vehicle/ticket tests; improve isolation. |
| Type checking           | Prefer targeted pyright over disabling for whole file. |

---

## 5. Opinion

The project is in good shape: clear structure, sensible API design, and careful handling of entry/exit, payments, and constraints. The main gaps are **security and config** (default DB URL with password, SQL echo always on, env loading order) and **test coverage/isolation**. Addressing the security and config points will make it safe and predictable in production; improving tests will make refactors and new features safer. The rest are incremental improvements (types, schemas, optional relationships) that you can adopt as you go.

Implementing the two critical items (no hardcoded credentials in default URL for production, and `SQL_ECHO`-driven `echo` in `db.py`) plus either using or removing `run.py` would already be a strong next step.
