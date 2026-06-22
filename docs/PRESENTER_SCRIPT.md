# Garage Management System
## Technical Walkthrough — Presenter Script (55 minutes)

**Audience:** Developers new to the codebase  
**Format:** Live demo + IDE code walkthrough  
**Repository:** `APIPostgreSql` (FastAPI + PostgreSQL + Vue 3)

---

## Document control

| Field | Value |
|-------|-------|
| Duration | 55 minutes (+ 10 min setup) |
| Demo plate | Use a fresh plate each run, e.g. `DEMO99` |
| Services | API `:8000` · Dashboard `:5173` · File server `:9009` |

---

## Table of contents

1. [Pre-session checklist](#pre-session-checklist)
2. [Act 1 — The story (0:00–5:00)](#act-1--the-story-000500)
3. [Act 2 — Architecture (5:00–8:00)](#act-2--architecture-500800)
4. [Act 3 — Login & security (8:00–12:00)](#act-3--login--security-8001200)
5. [Act 4 — Dashboard tour (12:00–17:00)](#act-4--dashboard-tour-12001700)
6. [Act 5 — Golden path: new vehicle entry (17:00–32:00)](#act-5--golden-path-new-vehicle-entry-17003200)
7. [Act 6 — Garage detail view (32:00–36:00)](#act-6--garage-detail-view-32003600)
8. [Act 7 — Exit ticket (36:00–43:00)](#act-7--exit-ticket-36004300)
9. [Act 8 — Payment (43:00–49:00)](#act-8--payment-43004900)
10. [Act 9 — Supporting systems (49:00–53:00)](#act-9--supporting-systems-49005300)
11. [Act 10 — Wrap-up & Q&A (53:00–55:00)](#act-10--wrap-up--qa-53005500)
12. [Quick-reference click map](#quick-reference-click-map)
13. [Troubleshooting](#troubleshooting)

---

<div style="page-break-after: always;"></div>

## Pre-session checklist

### Start services (in order)

| # | Terminal | Command | URL |
|---|----------|---------|-----|
| 1 | Workspace root | `python -m api_python.app.run` | http://localhost:8000 |
| 2 | `fileserver/storage` | `npm run dev` | http://localhost:9009 |
| 3 | `frontend_vue` | `npm run dev` | http://localhost:5173 |

### Screen layout

- **Left:** Browser (dashboard)
- **Right:** IDE (VS Code / Cursor)
- **Optional tab:** Swagger at http://localhost:8000/docs

### Demo data

- [ ] At least one garage exists in the database
- [ ] Vehicle types exist (Car, Van, etc.)
- [ ] `api_python/.env` has `AUTH_USERNAME` / `AUTH_PASSWORD` — know the values
- [ ] A small JPEG or PNG on disk for ticket image upload
- [ ] DevTools open: **F12 → Network → Preserve log ✓**

### IDE tabs to pre-open

1. `api_python/app/models.py`
2. `api_python/app/routers/tickets.py`
3. `api_python/app/services/tickets.py`
4. `frontend_vue/src/services/createParkingEntry.ts`
5. `frontend_vue/src/components/dashboard/NewVehicleEntryModal.vue`

---

<div style="page-break-after: always;"></div>

## Act 1 — The story (0:00–5:00)

### What to say

> This is a parking garage operations system. Operators monitor occupancy, register vehicle entry, close tickets on exit, and record payments. Three runtime pieces: FastAPI + PostgreSQL backend, Vue dashboard, and a separate file server for ticket photos.

### What to show

Open root `README.md` — repository layout table.

### What to say (continued)

> The domain revolves around one entity: **Ticket**. Everything else — garage, spot, vehicle, payment — supports the ticket lifecycle: OPEN → CLOSED → PAID.

### What to show

Open `api_python/app/models.py`, scroll to the `Ticket` class (lines 67–88).

**Point out:** `ticket_state`, `payment_status`, `spot_id`, `image_url`.

---

## Act 2 — Architecture (5:00–8:00)

### What to say

> Backend is layered: router = HTTP, service = business rules, schema = validation, model = database.

### What to show

Open `api_python/docs/BACKEND_DEVELOPER_GUIDE.md` — section 1 (Project architecture).

### Architecture diagram

```
Vue UI  →  API routers  →  services  →  PostgreSQL
Vue UI  →  file server (image)  →  image URL back to API
```

### What to say (continued)

> Frontend mirrors that split: views compose widgets, `api/*.ts` is the HTTP client, `services/` orchestrates multi-step flows.

### What to show

Expand in IDE:

- `frontend_vue/src/views/`
- `frontend_vue/src/api/`
- `frontend_vue/src/services/`

---

<div style="page-break-after: always;"></div>

## Act 3 — Login & security (8:00–12:00)

### Demo clicks

| Time | Action |
|------|--------|
| 8:00 | Browser → http://localhost:5173 |
| 8:10 | Land on `/login` (router guard) |
| 8:20 | Type username + password from `api_python/.env` |
| 8:30 | **Click** Sign in (`#signInBtn`) |
| 8:40 | Redirect to `/dashboard` |

### Code walk

| Time | File | What to say |
|------|------|-------------|
| 9:00 | `frontend_vue/src/router/index.ts` | Every route except `/login` requires JWT. |
| 9:30 | `frontend_vue/src/views/LoginView.vue` | Form calls `login()` from `api/auth.ts`. |
| 10:00 | `api_python/app/routers/auth.py` | `POST /auth/login` returns JWT. |
| 10:30 | `api_python/app/main.py` | Middleware enforces Bearer token on protected routes. |

### Network tab (optional)

| Time | Action |
|------|--------|
| 11:00 | DevTools → Network → find `POST .../auth/login` |
| 11:15 | Show response body with token |
| 11:30 | Show next request has `Authorization: Bearer ...` |

### What to say

> Auth is the front door. After this, every dashboard action is an authenticated API call.

---

## Act 4 — Dashboard tour (12:00–17:00)

### Demo clicks

| Time | Action |
|------|--------|
| 12:00 | Point at **Status cards** (free / occupied / open tickets) |
| 12:30 | Point at **Garage dropdown** (middle card) |
| 13:00 | Point at **Revenue summary** (today / month / outstanding) |
| 13:30 | **Click** tab **Overview** — `GarageOverviewTable` |
| 14:00 | **Click** tab **Tickets** — `TicketActivity` table |
| 14:30 | **Click** tab **Timeline** — chart |
| 15:00 | Header: point at **countdown ring** (auto-refresh every 10s) |
| 15:20 | **Click** green **refresh spinner** icon — manual refresh |
| 15:40 | Point at **New vehicle entry** button (`#newVehicleEntryBtn`) |

### Code walk

| Time | File | What to say |
|------|------|-------------|
| 16:00 | `frontend_vue/src/views/DashboardView.vue` | Composes widgets; tabs switch overview / tickets / timeline. |
| 16:30 | `api_python/app/routers/dashboard.py` | Aggregated metrics — fewer round-trips. |
| 16:50 | `frontend_vue/src/App.vue` | Global shell: header, polling, refresh-all, new-entry modal. |

### What to say

> This is an operations console, not a static CRUD app. It polls every 10 seconds and refreshes after writes.

---

<div style="page-break-after: always;"></div>

## Act 5 — Golden path: new vehicle entry (17:00–32:00)

*This is the core of the presentation. Do it live, then trace the code.*

### Part A — Live demo (17:00–22:00)

| Time | Click / type |
|------|----------------|
| 17:00 | **Click** header → **New vehicle entry** |
| 17:10 | Modal opens (`NewVehicleEntryModal`) |
| 17:20 | **Type** licence plate: `DEMO99` |
| 17:30 | **Click** Vehicle type dropdown → select e.g. **Car** |
| 17:40 | **Click** Garage dropdown → select a garage |
| 17:50 | **Click** Spot dropdown → leave **Auto-assign** (or pick a free spot) |
| 18:00 | **Click** **Choose file** → pick a JPEG/PNG |
| 18:10 | Wait for “image ready” text (client-side resize) |
| 18:20 | **Click** **Create entry** (`#createEntryBtn`) |
| 18:30 | Watch success message; modal closes |
| 18:40 | **Click** green refresh icon OR wait for auto-refresh |
| 19:00 | Status cards: occupied +1, open tickets +1 |
| 19:10 | **Click** **Tickets** tab |
| 19:20 | Find row with plate `DEMO99` |

**Say while waiting:**

> Three API calls happen in sequence: resolve vehicle, upload image, create ticket entry.

### Part B — Network tab (19:30–21:00)

| Time | Action |
|------|--------|
| 19:30 | DevTools → Network — filter Fetch/XHR |
| 19:40 | **Click** `GET /vehicles/by-plate/DEMO99` (or `POST /vehicles` if 404) |
| 19:50 | **Click** `POST /upload/ticket-image` |
| 20:00 | **Click** `POST /tickets/entry` |
| 20:15 | Payload: `vehicle_id`, `garage_id`, `spot_id`, `image_url` |
| 20:30 | Response: `ticket_state: "OPEN"`, `ticket_token`, `spot_id` |

### Part C — Frontend code trace (21:00–25:00)

| Time | File | Focus | Say |
|------|------|-------|-----|
| 21:00 | `NewVehicleEntryModal.vue` | form, `submit()` | UI collects plate, type, garage, spot, image. |
| 21:45 | `createParkingEntry.ts` | full file | Orchestration layer — not in the component. |
| 22:30 | `api/vehicles.ts` | `getVehicleByPlate` | Lookup by plate; create if missing. |
| 23:00 | `api/upload.ts` | `uploadTicketImage` | Image to file server; URL returned. |
| 23:30 | `api/tickets.ts` | `ticketEntry` | Final call: `POST /tickets/entry`. |

**Key code path:**

```
createParkingEntry()
  → getVehicleByPlate() or createVehicle()
  → uploadTicketImage()
  → ticketEntry({ vehicle_id, garage_id, spot_id, image_url })
```

### Part D — Backend code trace (25:00–31:00)

| Time | File | Focus | Say |
|------|------|-------|-----|
| 25:00 | `routers/tickets.py` | `POST /entry` ~line 197 | Router is thin — maps errors to HTTP. |
| 25:45 | `services/tickets.py` | `create_ticket_entry` ~line 93 | Business logic lives here. |
| 26:30 | same file | `_resolve_spot_id` ~line 59 | Manual spot or auto-allocate. |
| 27:00 | `services/spots.py` | `allocate_free_spot` | Finds first free active spot. |
| 27:30 | `services/tokens.py` | `generate_ticket_token` | Unique scannable token per ticket. |
| 28:00 | `models.py` | `Ticket` | Persisted with OPEN, NOT_APPLICABLE payment. |

**Say at `create_ticket_entry`:**

> On success: generate token, assign spot, set state OPEN, commit once. Token collision retries up to 5 times.

### Part E — Swagger (optional, 31:00–32:00)

| Time | Action |
|------|--------|
| 31:00 | Tab → http://localhost:8000/docs |
| 31:10 | Expand **Tickets** → `POST /tickets/entry` |
| 31:20 | Show request schema + response model |
| 31:40 | Point at errors: `SPOT_OCCUPIED`, `NO_FREE_SPOTS_AVAILABLE` |

---

<div style="page-break-after: always;"></div>

## Act 6 — Garage detail view (32:00–36:00)

### Demo clicks

| Time | Action |
|------|--------|
| 32:00 | Dashboard → **Overview** tab |
| 32:10 | **Click** any row in **Garage overview** table |
| 32:20 | Navigates to `/garage/:id` |
| 32:30 | Point at garage header card (name, capacity, rates) |
| 32:45 | Scroll to **Open tickets** table |
| 33:00 | Confirm `DEMO99` appears |
| 33:15 | **Click** header **Dashboard** link → back to `/dashboard` |

### Code walk

| Time | File | Say |
|------|------|-----|
| 34:00 | `router/index.ts` | Three routes: login, dashboard, garage detail. |
| 34:30 | `GarageDetailView.vue` | Single-garage drill-down: spots, open tickets, revenue. |
| 35:00 | `composables/useGarageSpots.ts` etc. | Composable per concern — reusable fetch logic. |
| 35:30 | `GarageOverviewTable.vue` ~line 95 | Row click pushes `garage-detail` route. |

---

## Act 7 — Exit ticket (36:00–43:00)

### Part A — Live demo (36:00–39:00)

| Time | Action |
|------|--------|
| 36:00 | Dashboard → **Tickets** tab |
| 36:10 | Find `DEMO99` row |
| 36:20 | **Click** barcode icon → **Ticket detail modal** |
| 36:35 | Point at: plate, spot, entry time, image, Code39 barcode |
| 36:50 | **Click** Close on modal |
| 37:00 | **Click** exit icon on row (`icon-exit`, “Close ticket”) |
| 37:10 | Row updates: CLOSED, exit time, fee |
| 37:30 | **Click** green refresh — revenue / outstanding update |

### Part B — Network + code (39:00–43:00)

| Time | Action |
|------|--------|
| 39:00 | Network → `POST /tickets/{id}/exit` |
| 39:15 | Response: `ticket_state: "CLOSED"`, `fee`, `exit_time` |

| Time | File | Say |
|------|------|-----|
| 39:45 | `TicketActivity.vue` | `closeTicket()` calls `ticketExit(id)`. |
| 40:15 | `api/tickets.ts` | `POST /tickets/{id}/exit`. |
| 40:45 | `routers/tickets.py` | `ticket_exit` ~line 239. |
| 41:15 | `services/tickets.py` | `close_ticket` function. |
| 41:45 | `services/pricing.py` | Fee calculated on exit from rates + duration. |
| 42:30 | `TicketRow.vue` lines 79–88 | Exit button only when `ticket_state === 'OPEN'`. |

### What to say

> Closing a ticket is a state transition. The service calculates fee, sets exit time, updates payment status — then the dashboard reflects it.

---

<div style="page-break-after: always;"></div>

## Act 8 — Payment (43:00–49:00)

### Part A — Live demo (43:00–46:00)

| Time | Action |
|------|--------|
| 43:00 | Tickets tab → closed `DEMO99` |
| 43:10 | **Click** credit-card icon OR barcode → **Go to payment** |
| 43:25 | **Payment modal** — total fee + rest to pay |
| 43:35 | **Type** amount (full fee) |
| 43:45 | **Click** Payment method → e.g. **Cash** |
| 43:55 | **Click** **Submit payment** (`#submitPaymentBtn`) |
| 44:10 | Modal closes; table refreshes |
| 44:25 | Row shows PAID |
| 44:40 | **Click** barcode icon → **Evidence of payments** in detail modal |

### Part B — Code trace (46:00–49:00)

| Time | File | Say |
|------|------|-----|
| 46:00 | `PaymentModal.vue` | Amount + method; validates against rest to pay. |
| 46:30 | `api/payments.ts` | `createPayment`, `getPaymentsByTicket`. |
| 47:00 | `routers/payments.py` | `POST /payments`. |
| 47:30 | `services/payments.py` | Updates ticket payment_status when fully paid. |
| 48:00 | `TicketDetailModal.vue` | Payment history + barcode. |
| 48:30 | `App.vue` | Payment done triggers dashboard-wide refresh. |

---

## Act 9 — Supporting systems (49:00–53:00)

One minute each — fast tour.

| Time | Topic | Show |
|------|-------|------|
| 49:00 | Errors | `errors.py`, `error_handlers.py` — codes like `SPOT_OCCUPIED` |
| 50:00 | Migrations | `alembic/versions/` — schema evolves with Alembic |
| 51:00 | Tests | `tests/test_vehicle_types.py` — pytest pattern |
| 52:00 | i18n | `i18n.ts` + header language switcher — EN/SR |

### What to say

> These show the project is production-shaped: migrations, tests, consistent errors, localization.

---

## Act 10 — Wrap-up & Q&A (53:00–55:00)

### What to say

> We followed one ticket end to end: login → new entry (vehicle + image + spot) → live dashboard → exit with fee → payment. Frontend orchestrates; backend enforces rules; PostgreSQL is source of truth.

**Leave on screen:** Tickets tab with `DEMO99` — CLOSED + PAID.

### Q&A prompts

- **Garage full?** → `NO_FREE_SPOTS_AVAILABLE`
- **Why separate image upload?** → file server + smaller API payloads
- **Why dashboard analytics endpoint?** → one call vs many widget round-trips

---

<div style="page-break-after: always;"></div>

## Quick-reference click map

| User action | UI click path | API call |
|-------------|---------------|----------|
| Login | `/login` → Sign in | `POST /auth/login` |
| New entry | Header → New vehicle entry → Create entry | `GET/POST /vehicles`, `POST /upload/ticket-image`, `POST /tickets/entry` |
| View ticket | Tickets tab → barcode icon | `GET /tickets/dashboard` + payments in modal |
| Close ticket | Tickets tab → exit icon | `POST /tickets/{id}/exit` |
| Pay | Tickets tab → credit card → Submit | `POST /payments` |
| Garage detail | Overview tab → click garage row | `GET /garages/{id}`, spots, open tickets |
| Manual refresh | Header → green spinner | multiple dashboard GETs |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Login fails | Check `AUTH_USERNAME` / `AUTH_PASSWORD` in `api_python/.env`; restart API |
| Image upload fails | Start file server on port 9009 |
| CORS error | Ensure `CORS_ORIGINS` includes `http://localhost:5173` |
| Create entry disabled | All fields + image required; wait for resize to finish |
| No garages in dropdown | Run migrations; seed data if needed |
| Ticket not in list | Tickets tab; check garage filter; click refresh |

---

## Export to PDF

From VS Code / Cursor: open this file → **Markdown: Export (PDF)** (if extension installed), or:

```bash
# With pandoc (from repo root)
pandoc docs/PRESENTER_SCRIPT.md -o docs/PRESENTER_SCRIPT.pdf --pdf-engine=xelatex -V geometry:margin=1in
```

Or print from browser: open the rendered Markdown preview → **Print** → **Save as PDF**.

---

*Garage Manage — Presenter Script v1.0*
