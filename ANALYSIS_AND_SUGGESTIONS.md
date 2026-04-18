# API Project Analysis & Suggestions for Improvement

This document is a full review of your **Parking API** (FastAPI + PostgreSQL): what works well, what could be improved, and concrete suggestions.

**Scope:** This note focuses on the **FastAPI + PostgreSQL** service. The **dashboard** (`dashboard/`, Vue) is a separate client; it is not reviewed here.

---

## 1. Project overview

The API manages:

- **Garages** (`parking_config`) – capacity, rates, opening hours
- **Parking spots** – per garage, with `code`, `is_rentable`, `is_active`
- **Vehicle types** – type name and hourly rate
- **Vehicles** – licence plate, type, status
- **Tickets** – entry/exit, fee, state, payment status; optional spot assignment; optional **image** (`image_url` on entry and on `TicketUpdate`)
- **Payments** – linked to closed tickets, with overpayment checks

**Schema changes** go through **Alembic** migrations under `alembic/versions/`.

Notable features: optional API-key auth, CORS configuration (including production checks), configurable fee/payment-status logic (API vs DB triggers), spot allocation with `FOR UPDATE SKIP LOCKED`, solid validation via Pydantic and Literals, **ticket image upload** (`POST` upload route, files under configurable `UPLOAD_DIR`, served as `/uploads/...` — see `docs/TICKET_IMAGE_UPLOAD.md`).

---

## 2. What’s working well

### Architecture

- Clear separation: **routers** (HTTP), **services** (business logic), **schemas** (validation/serialization), **models** (ORM). Easy to navigate and test.
- **Config** is centralized in `app/config.py` with env-based flags (`USE_API_FEE_CALCULATION`, `USE_API_PAYMENT_STATUS`, CORS, upload limits/paths). Good for different deployments (with/without DB triggers).
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

### Uploads and ticket images

- **`app/routers/upload.py`**: Validates JPEG/PNG/WebP, enforces `UPLOAD_TICKET_IMAGE_MAX_BYTES`, writes under `UPLOAD_DIR/tickets/`, returns a path such as `/uploads/tickets/...` for storing on the ticket.
- **Docs**: `docs/TICKET_IMAGE_UPLOAD.md` describes the client flow.

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

Items marked **Addressed** are summarized in the table in §4; details live in README or code comments.

### 3.1 Critical / security

**Hardcoded database URL and password (`app/db.py`)**

- **Current**: `DATABASE_URL` defaults to a URL that contains a literal password. If the repo is shared or deployed, this is a security risk.
- **Suggestion**:
  - Prefer no default with credentials. For example: `DATABASE_URL = os.getenv("DATABASE_URL")` and fail at startup if unset (or only in production).
  - Or keep a default only for local dev (e.g. `postgresql+psycopg2://user:pass@localhost:5432/garaza`) and document that **production must set `DATABASE_URL`** and never commit real credentials.
  You already use `python-dotenv` in config; ensure `db.py` does not override with a default that includes real passwords in production.

**SQL logging (`app/db.py`)** — **Addressed** (see §4: Security / Config / Run entry.)

### 3.2 Consistency and robustness

**Config loading and import order** — **Addressed** (see §4.)

**Run entry point (`app/run.py`)** — **Addressed** (see §4.)

**Vehicle create with `licence_plate is None`**

- **Current**: Uniqueness is checked only when `data.licence_plate is not None`, so multiple vehicles with `licence_plate is None` are allowed. That may be intended (e.g. “unknown” vehicles).
- **Suggestion**: If that is the intended rule, add a short comment in the router or schema. If only one “unknown” vehicle should exist, add a check for an existing row with `licence_plate IS NULL` and return 400 in that case.

### 3.3 API and validation

**Payment method and currency**

- **Current**: `PaymentCreate.method` is a free-form string; `currency` defaults to `"RSD"` and is a string. DB has `method` as `String(20)`, `currency` as `String(3)`.
- **Suggestion**: Optionally restrict `method` and `currency` (e.g. `Literal["CASH", "CARD", "BANK"]` and a small set of currency codes) and/or add `max_length` in Pydantic so validation and OpenAPI stay aligned with the DB and business rules.

**Garage create/update types** — **Addressed** (see §4: Schemas.)

### 3.4 Uploads and operations (ticket images)

- **Current**: Images are stored on local disk under `UPLOAD_DIR`; API returns a relative URL path for `image_url`.
- **Suggestion for production**: Decide whether upload and/or `/uploads` should require the same auth as the rest of the API; plan **backups** for `UPLOAD_DIR` (or move to object storage later). If tickets are exposed with rewritten tokens, keep any URL/token rules aligned with `app/services/rewrite_ticket_tokens.py` and your public ticket flows.

### 3.5 Structure and maintainability

**Pyright and `main.py`**

- **Current**: `# pyright: reportMissingImports=false` at the top of `main.py` disables missing-import checks for the whole file.
- **Suggestion**: Prefer fixing or typing the imports (e.g. `dotenv` in config) and removing the directive, or limit the directive to the few lines that need it so the rest of the file is still checked.

**Optional relationships on models**

- **Current**: `ParkingConfig` has no `relationship` to `ParkingSpot` or `Ticket`. Other models have relationships where needed.
- **Suggestion**: If you often need “all spots for a garage” or “all tickets for a garage”, adding e.g. `spots = relationship("ParkingSpot", back_populates="garage")` (and backrefs on spots) can simplify code and avoid extra queries. Optional and only if it improves readability.

### 3.6 Testing and ops

**Test isolation** — **Addressed** (see §4: Tests.)

**Test coverage** — **Addressed** (see §4: Tests.)

---

## 4. Summary table

| Area | Status / suggestion |
|------|---------------------|
| Architecture | Good separation; keep routers thin and services for logic. |
| Scope | This document = API service only; dashboard is separate. |
| Schema / DB | Alembic migrations for schema evolution. |
| Pagination & route order | In good shape. |
| Auth & CORS | Solid; API key read once at startup from config; CORS config clear. |
| Fee / payment status | Flexible (API vs DB); services used when flags are on. |
| Uploads & ticket images | Implemented (validate size/type, disk storage, docs). For production: auth strategy for upload/static, backups or object storage. |
| Security | **SQL_ECHO** is configurable (**addressed**). **Open:** default `DATABASE_URL` in `db.py` still contains a literal password — require env in production and avoid real credentials in defaults. |
| Config / env | **Addressed:** `.env` only in `app/config.py`; `main` imports config before `db`; documented in code. |
| Run entry point | **Addressed:** `python -m app.run`; README. |
| Schemas | **Addressed:** garages use `Decimal`. **Open:** optional Literals / lengths for payment method and currency. |
| Tests | **Addressed:** transactional rollback in `conftest.py`; broad coverage (health, garages, vehicle types, vehicles, spots, tickets, payments). |
| Type checking | Prefer targeted pyright over disabling for the whole `main.py`. |

---

## 5. Opinion

The project is in good shape: clear structure, sensible API design, and careful handling of entry/exit, payments, and constraints. Ticket images and uploads add a real surface area; the implementation is reasonable for local/single-node use, with production decisions (auth, backups, storage) left to deployment.

**Resolved or stable items** are consolidated in §4 (config order, `run.py`, SQL echo, Decimal garages, tests).

**Main remaining security gap:** the default `DATABASE_URL` in `db.py` with embedded credentials. **Incremental next steps:** stricter payment `method`/`currency` validation if the business needs it; optional SQLAlchemy relationships; tighter Pyright scope on `main.py`.
